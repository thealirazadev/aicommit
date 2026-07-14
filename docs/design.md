# Design — aicommit (CLI UX)

This document specifies the command-line user experience: the command, its flags, output, the interactive flow, exit codes, and accessibility. Implement the behavior here exactly; `docs/architecture.md` covers the internals.

## Command

A single command, `aicommit`, invoked inside a git repository with staged changes. There are no subcommands. The console entry point is `aicommit = "aicommit.cli:main"` in `pyproject.toml`.

```
aicommit [OPTIONS]
```

Running `aicommit` with staged changes drafts a Conventional Commit message, shows it, and prompts for what to do next.

## Flags

| Flag              | Short | Type   | Default | Behavior                                                                                 |
| ----------------- | ----- | ------ | ------- | ---------------------------------------------------------------------------------------- |
| `--type`          | `-t`  | text   | none    | Force the Conventional Commit type (e.g. `feat`, `fix`). Passed to the model as a constraint. |
| `--scope`         | `-s`  | text   | none    | Force the commit scope; appears as `type(scope): ...`.                                    |
| `--model`         | `-m`  | text   | config  | Override the model id for this run.                                                       |
| `--dry-run`       | `-n`  | flag   | off     | Draft and print the message to stdout, then exit 0. No prompt, no commit.                 |
| `--yes`           | `-y`  | flag   | off     | Accept the first draft and commit without prompting. Mutually exclusive with `--dry-run`.|
| `--edit`          | `-e`  | flag   | off     | After drafting, open the message in `$EDITOR` before the accept step.                     |
| `--quiet`         | `-q`  | flag   | off     | Suppress non-essential output (spinner text, hints). Errors still print.                 |
| `--verbose`       | `-v`  | flag   | off     | Detailed, structured logs on stderr. Prints a friendly line too; still no raw traceback unless it is the logged detail. |
| `--no-color`      |       | flag   | off     | Disable ANSI color. Also disabled automatically when `NO_COLOR` is set.                   |
| `--version`       |       | flag   | -       | Print `aicommit <version>` and exit 0.                                                    |
| `--help`          |       | flag   | -       | Print help and exit 0.                                                                    |

Notes:
- `--dry-run` and `--yes` together is a usage error (exit 2): one prints, the other commits.
- `--quiet` and `--verbose` together resolves to `--verbose` (more information wins); do not error.
- Unknown flags produce click's usage error (exit 2).

## Colored output

- All output is routed through one `rich.Console`. Color is enabled only when attached to a TTY and neither `--no-color` nor `NO_COLOR` is set.
- Palette (semantic, not decorative):
  - Success (commit created): green.
  - Warning (large diff, fell back to summary): yellow.
  - Error: red, on stderr.
  - The drafted message: shown inside a bordered `rich.Panel` titled "Proposed commit message".
- Color is never the only signal — see Accessibility.

## Spinner during the API call

- While waiting on the Claude API (initial draft and each regenerate), show a `rich` status spinner with the text `Drafting commit message...` (regenerate: `Regenerating...`).
- The spinner is shown only when stdout is a TTY and `--quiet` is off. In non-interactive or quiet mode, print nothing (or a single plain line) instead of animating.
- The spinner stops before any prompt, error, or the panel is rendered.

## How the proposed message is displayed

- After a successful draft, render a bordered panel:

```
+-- Proposed commit message --------------------------------+
| fix(parser): handle empty staged diff without crashing    |
|                                                           |
| Return a friendly error and exit code 3 when the staged   |
| diff is empty instead of raising.                         |
+-----------------------------------------------------------+
```

- The subject line is on the first line; a blank line separates the optional body. Long bodies wrap to the console width.
- Below the panel (unless `--quiet`), show the prompt line described next.

## Accept / edit / regenerate flow

After the panel, prompt:

```
[a]ccept  [e]dit  [r]egenerate  [q]uit >
```

- Accept the letters `a`/`e`/`r`/`q` and their full words (`accept`, `edit`, `regenerate`, `quit`), case-insensitive. Enter with no input defaults to `accept`.
- An unrecognized answer re-prompts (does not crash, does not commit).

Actions:
- **accept** — write the current message to a temp file and run `git commit -F <tmpfile>`. On success, print a green confirmation with the short SHA (`Committed a1b2c3d`) and exit 0. On git failure, print the git error and exit 7.
- **edit** — open the current message in `$EDITOR` (via `click.edit`, which falls back to a sensible default editor). If the edited text is non-empty, replace the draft and re-display the panel + prompt. If it is empty/blank, print `Commit message is empty; nothing committed.` and exit 1.
- **regenerate** — call the API again (spinner), replace the draft with the new one, re-display the panel + prompt. A short optional nudge ("provide a different message") may be appended to the request.
- **quit** — print `Aborted.` and exit 130. No commit.

`--edit` combined with the flow: when `--edit` is passed, open the editor immediately after the first draft (before showing the prompt), then present the panel + prompt as usual. `--yes` skips the prompt entirely and commits the first draft (still honoring `--edit` if both are set: edit once, then commit).

## Exit codes

| Code | Meaning                                                        |
| ---- | ------------------------------------------------------------- |
| 0    | Success — commit created, or `--dry-run` printed a message.  |
| 1    | Unexpected/internal error, or empty edited message.          |
| 2    | CLI usage error (bad flags; click default).                  |
| 3    | Nothing staged.                                              |
| 4    | Not inside a git repository.                                 |
| 5    | Authentication error — API key missing or invalid.           |
| 6    | API / network error (connection, timeout, rate limit, 5xx). |
| 7    | git commit failed.                                           |
| 130  | Aborted by the user (quit at the prompt or Ctrl-C).          |

These are the single source of truth for exit codes and must match `docs/rules.md`.

## --quiet / --verbose

- **Default:** the spinner, the panel, the prompt, and a one-line success/error message.
- **--quiet:** no spinner animation, no hints. In interactive mode still show the panel and prompt (the user must decide); suppress decorative lines. In `--dry-run`/`--yes` mode, print only the essential output (the message or the success line) and errors.
- **--verbose:** everything default shows, plus structured debug logs on stderr (model id, diff bytes, request duration, chosen action, exit code). Never prints the API key or the full diff.

## NO_COLOR support

- If the `NO_COLOR` environment variable is set to any value, or `--no-color` is passed, disable all ANSI color and styling. Construct the `rich.Console` accordingly (`no_color=True` / `force_terminal=False` as appropriate) and verify output contains no escape codes.
- Detection is checked once at startup and applied to the single shared console.

## Accessibility (no meaning by color alone)

- Every colored signal carries a text label or symbol, so meaning survives with color off or for color-blind users:
  - Success: `Committed a1b2c3d` (word "Committed"), not just green text.
  - Warning: prefixed `Warning:` (word), not just yellow.
  - Error: prefixed `Error:` on stderr, not just red.
- The accept/edit/regenerate options are labeled with letters and words, never distinguished only by color.
- Do not rely on the spinner as the only indication of progress; the following panel or error confirms the outcome.
- Respect `NO_COLOR` and non-TTY environments (pipes, CI): fall back to plain text automatically.
