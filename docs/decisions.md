# Design decisions

This page records the main engineering choices in aicommit and the reasons behind them,
including the bugs and edge cases that shaped the current code.

## 1. One command, built on click

aicommit is a single `aicommit` command with flags and no subcommands. It is built on
`click` rather than Typer or argparse: click gives `click.edit` for `$EDITOR` support,
`UsageError` for flag conflicts, and `CliRunner` for end-to-end tests, with a small
dependency surface. `--dry-run` and `--yes` together is rejected as a usage error (exit 2)
because one promises never to commit and the other commits immediately.

## 2. All git access goes through subprocess wrappers in `git.py`

The tool shells out to the `git` binary instead of using libgit2 bindings, so there is
nothing native to build or ship. Every call goes through `_run_git`, which passes an explicit
argument list to `subprocess.run` and never uses `shell=True`, so file names and messages are
never interpreted by a shell. Keeping every git call in one module also keeps the error
handling in one place and lets the tests run against real throwaway repositories.

## 3. Commits are created with `git commit -F <tmpfile>`

The accepted message is written to a temporary file and passed with `-F` instead of `-m`.
This preserves multi-line bodies, blank lines and special characters exactly, so
`git log -1 --pretty=%B` matches what the user accepted. The temp file is removed in a
`finally` block even when the commit fails, and a failed commit raises `GitCommitError`
(exit 7) with the first line of git's stderr, falling back to stdout when stderr is empty.

## 4. Typed errors with fixed exit codes, caught once

Inner modules raise subclasses of `AicommitError`, each carrying a one-line user message, an
exit code and optional detail. `cli.py` catches them in a single place, prints `Error: ...`
to stderr and exits with the error's code. The codes are stable so the tool is scriptable:
3 nothing staged, 4 not a repository, 5 API key missing or invalid, 6 network, rate limit or
server error, 7 git commit failed, 1 an empty edited message, a malformed config file or any
unexpected error, and 130 for quit or Ctrl-C. Unexpected exceptions are logged with their
traceback at debug level only, so a raw traceback never reaches the user by default.

## 5. The API key is checked before the SDK client is built

When `ANTHROPIC_API_KEY` is completely unset, the Anthropic SDK raises a plain `TypeError`
rather than `AuthenticationError`. That fell through to the generic "Unexpected error" path
and exited 1 instead of 5. `draft_message` now checks the variable up front and raises
`AuthError`, but only when the real `anthropic.Anthropic` factory is in use, so tests that
inject a fake client do not need a key in the environment. The key is never stored on
`Config` or logged; the SDK reads it from the environment itself.

## 6. One non-streaming model call per draft, with explicit error mapping

Each draft or regenerate is one `messages.create` call with `max_tokens=1024`. A commit
message is short, so streaming would add complexity without any timeout benefit. The tool
adds no retry loop of its own because the SDK already retries rate limits and server errors.
SDK exceptions are mapped most specific first: authentication and permission errors become
`AuthError` (exit 5); rate limits, connection errors and timeouts become `ApiError` (exit 6);
other status errors become `ApiError` only for 5xx. A non-auth 4xx is deliberately re-raised
rather than reported as a network problem, since it points to a bad request, not a transient
failure.

## 7. Configuration is resolved once into a frozen dataclass

`load_config` merges built-in defaults, an optional TOML file, the environment and CLI flags
into an immutable `Config` at startup, and that object is passed down explicitly instead of
reading the environment throughout the code. For the model the precedence is `--model`, then
`AICOMMIT_MODEL`, then the config file, then the default `claude-opus-5-5`. Type and scope
come from flags or the file; `max_diff_bytes` comes only from the file. The file is
`./.aicommit.toml` if present, otherwise `$XDG_CONFIG_HOME/aicommit/config.toml` (falling back
to `~/.config`). A file that exists but fails to parse is a `ConfigError` (exit 1) naming the
path, not a crash. TOML is read with `tomllib` on 3.11+ and the `tomli` backport on 3.10,
declared as a conditional dependency.

## 8. Oversized diffs are summarized and truncated, never sent whole

Only the staged diff, or its summary, plus any type and scope hints leave the machine. Above
`max_diff_bytes` (100,000 by default) the payload becomes the `git diff --cached --stat`
summary followed by the diff cut to that many bytes, and the user sees a `Warning:` line
before drafting continues. The cut happens on the encoded bytes and is decoded with
`errors="ignore"`, so a multi-byte character split at the boundary is dropped instead of
raising. Binary files need no special handling: `git diff --cached` emits only a
`Binary files ... differ` marker, which a test checks.

## 9. Two consoles, and no escape codes when color is off

The draft, prompts and success line go to a stdout `rich.Console`; errors, warnings and
"Aborted." go to a stderr console, so `--dry-run` output can be piped cleanly. `--no-color` or
any `NO_COLOR` value disables color on both consoles. The spinner is shown only on a TTY,
outside `--quiet`, and also not under no-color, because its cursor-control sequences are
themselves ANSI escapes. Every colored signal also carries a word (`Committed`, `Warning:`,
`Error:`), so nothing depends on color alone.

## 10. The choice prompt escapes rich markup

The prompt `[a]ccept [e]dit [r]egenerate [q]uit` first rendered as `ccept dit egenerate uit`,
because rich parsed `[a]`, `[e]`, `[r]` and `[q]` as style tags and dropped them. The
brackets are now escaped, and a test asserts every choice letter is visible. Input is
case-insensitive, accepts letters or full words, treats blank input as accept and re-prompts
on anything else.

## 11. Editing keeps the draft when the editor reports no change

`click.edit` returns `None` when the user closes the editor without saving a change; in that
case the original draft is kept. A message that is blank after stripping raises
`EmptyMessageError` (exit 1) and nothing is committed, so an accidental empty save never
creates an empty commit. `--edit` opens the editor once right after the first draft, and
combined with `--yes` it commits the edited text without prompting.

## 12. Structured logs behind `--verbose`, never containing secrets

Logging uses the standard library on stderr. The default level is WARNING, `--quiet` sets
ERROR, and `--verbose` sets DEBUG and wins if both are given, since more information is the
safer resolution than an error. Debug records are `event=... key=value` lines with the model
id, diff size in bytes, request duration, the chosen action and the exit code. The key, the
diff contents and the model output are never passed as fields, and a test checks that the API
key does not appear in verbose output.

## 13. `.env` is read from the repository root, for two keys only

The README has always offered a `.env` file as an alternative to exporting the key, so the
CLI loads `<repo root>/.env` before resolving configuration. It uses a small stdlib parser
instead of adding `python-dotenv`. Because the file belongs to whatever repository you are
committing in, possibly one you just cloned, only `ANTHROPIC_API_KEY` and `AICOMMIT_MODEL`
are taken from it: a repository's `.env` must not be able to set `ANTHROPIC_BASE_URL` and
send your real key to another host. A variable already set in the environment always wins.

## 14. Model output is cleaned before it is shown or committed

The prompt asks for the bare message, but a model sometimes wraps it in a Markdown code
fence anyway, and committed as is the fence line becomes the subject. `clean_message` trims
whitespace and removes a fence that wraps the whole message; a fence inside the body is kept.
An empty result is an `ApiError` (exit 6) rather than an empty commit. The draft is printed as
`rich.text.Text`, never as a markup string, so brackets such as `[x]` in a message show in the
preview and in `--dry-run` output exactly as they will be committed. The diff itself is read
with `--no-color --no-ext-diff`, so a `color.ui = always` or `diff.external` setting in the
user's git config cannot put escape codes or another tool's output into the prompt.
