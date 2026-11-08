# Rules — aicommit

These rules are binding for anyone implementing aicommit. When something here conflicts with a habit or a shortcut, follow the rule.

## Conventions

### Preferred libraries and patterns

- **CLI:** `click`. Use `click.command`, options, `click.prompt`/`click.confirm`, `click.edit`, and `CliRunner` in tests. Do not add Typer, argparse, or a second CLI layer.
- **Output:** all user-facing output goes through a single `rich.Console` instance (create it in `logging.py` or `cli.py` and pass it down). Never mix bare `print()` with rich output.
- **HTTP/model access:** the official `anthropic` SDK only. Do not hand-roll `requests`/`httpx` calls to the API. Do not add any other model provider.
- **Git access:** every git invocation goes through helpers in `git.py` using `subprocess.run([...], capture_output=True, text=True)` with an explicit argument list. Never build shell command strings; never pass `shell=True`.
- **Config:** parse TOML with the standard-library `tomllib` (Python 3.11+) or `tomli` on 3.10. Resolve config once at startup into an immutable `Config` (a frozen dataclass). Do not read env vars scattered throughout the code.
- **Errors:** raise typed exceptions from `errors.py`; catch them once at the top level in `cli.py`.

### What to avoid

- No global mutable state. Pass `Config` and `Console` explicitly.
- No `shell=True`, no string-interpolated shell commands, no `os.system`.
- No network calls anywhere except through `model.py`. Tests must never touch the network.
- No new runtime dependency without approval (see Boundaries).
- No clever metaprogramming; prefer plain functions and small modules.
- No printing of the API key, the full diff, or raw tracebacks by default.

### Naming

- **Modules:** `snake_case`, one responsibility each (`git.py`, `prompt.py`, `model.py`, `message.py`, `config.py`, `errors.py`, `logging.py`, `cli.py`). PEP 8.
- **Functions:** `snake_case`, verb-first, action-describing: `read_staged_diff`, `build_prompt`, `draft_message`, `present_and_choose`, `create_commit`, `load_config`.
- **Variables:** `snake_case`, descriptive (`staged_diff`, `draft`, `commit_type`, `exit_code`). Avoid one-letter names except short loop indices.
- **Constants:** `UPPER_SNAKE_CASE` (`DEFAULT_MODEL = "claude-opus-5-5"`, `SYSTEM_PROMPT`).
- **Classes/exceptions:** `PascalCase` (`Config`, `AicommitError`, `NoStagedChangesError`).

### Commit format (for building this tool)

- **Conventional Commits** with a short, imperative subject: `type(scope): summary`. Types: `feat`, `fix`, `docs`, `style`, `refactor`, `perf`, `test`, `build`, `ci`, `chore`, `revert`.
- Keep the subject under ~72 characters. Add a body only when it adds information.
- **ONE COMMIT PER FEATURE/TASK.** Each phase's "Commits" list in `docs/phases.md` is the intended order — do not batch multiple features into one commit, and do not split one feature across many noise commits.
- Commit messages must carry **no authorship attribution** — no "Generated with", no "Co-Authored-By", no assistant mention. This applies both to commits you make while building the tool and to the messages the tool itself produces.

### Dependencies and lockfile

- **Pin exact versions.** `pyproject.toml` `dependencies` use `==` pins, not ranges. Suggested starting pins (verify each exists on PyPI at build time and adjust if a pin is unavailable):
  - `anthropic==0.116.0`
  - `click==8.1.7`
  - `rich==13.9.4`
  - dev: `pytest==8.3.4`, `ruff==0.8.4`, `black==24.10.0`, and `tomli==2.0.2` only if targeting Python 3.10.
- **Commit the lockfile.** Use `uv` and commit `uv.lock` (`uv lock` to generate, `uv sync` to install). If `uv` is unavailable, generate and commit `requirements.lock` with `pip-compile` (pip-tools) instead. Exactly one lockfile is committed and kept in sync with `pyproject.toml`.
- Changing or adding a dependency requires approval (see Boundaries) and its own commit.

## Error handling and logging

Handle failures of both subsystems: the `git` subprocess and the Claude API. Users see one friendly line; details are available with `--verbose`; raw tracebacks are never shown by default.

### Failure classes, messages, and exit codes

| Situation                        | Detect                                                        | User-facing message (one line)                                             | Exit |
| -------------------------------- | ------------------------------------------------------------ | -------------------------------------------------------------------------- | ---- |
| Not a git repository             | `git rev-parse --is-inside-work-tree` fails / non-zero        | `Not a git repository. Run aicommit from inside a git repo.`               | 4    |
| No staged changes                | `git diff --cached` output is empty                          | `No staged changes. Stage files with 'git add' first.`                     | 3    |
| Missing/invalid API key          | `anthropic.AuthenticationError` / `PermissionDeniedError`; or key unset | `Anthropic API key missing or invalid. Set ANTHROPIC_API_KEY.`             | 5    |
| Network error                    | `anthropic.APIConnectionError` / `APITimeoutError`           | `Could not reach the Anthropic API. Check your connection and retry.`      | 6    |
| Rate limited                     | `anthropic.RateLimitError`                                    | `Rate limited by the Anthropic API. Wait a moment and retry.`             | 6    |
| API server error                 | `anthropic.APIStatusError` with status >= 500                | `Anthropic API error (server). Try again shortly.`                         | 6    |
| Oversized diff                   | diff bytes > `max_diff_bytes`                                | `Diff is large; sending a summary. Use a smaller staged change for detail.`| n/a (warn, continue) |
| git commit failed                | `git commit` non-zero exit                                   | `git commit failed: <first line of git stderr>`                            | 7    |
| Empty edited message             | edited message is blank after editing                        | `Commit message is empty; nothing committed.`                              | 1    |
| User quit at prompt / Ctrl-C     | user chose quit, or `KeyboardInterrupt`                      | `Aborted.`                                                                  | 130  |
| Bad CLI flags                    | click usage error                                            | click's own usage message                                                  | 2    |
| Any other unexpected error       | uncaught in inner code                                        | `Unexpected error. Re-run with --verbose for details.`                     | 1    |

Exit code 0 is reserved for success: a commit was created, or `--dry-run` printed a message.

### Style of error handling

- Define an `AicommitError` base exception in `errors.py` carrying `message`, `exit_code`, and optional `detail`. Subclasses: `NotAGitRepoError` (4), `NoStagedChangesError` (3), `AuthError` (5), `ApiError` (6), `GitCommitError` (7). One consistent style everywhere.
- Raise these from the inner modules (`git.py`, `model.py`, `message.py`). Do not `sys.exit` from inner code.
- `cli.py` has exactly one `try/except AicommitError` around the workflow. It prints `error.message` to stderr (in red, unless color is disabled), logs `error.detail` at debug level, and exits with `error.exit_code`.
- Catch `KeyboardInterrupt` at the same top level and exit 130 with `Aborted.`.
- Never let a raw traceback reach the user by default. With `--verbose`, log the traceback via the logger (to stderr) but still print the friendly line.

### Logging

- Use the standard-library `logging`, configured in `logging.py`. Default level `WARNING`; `--verbose` sets `DEBUG`; `--quiet` sets `ERROR` and suppresses non-essential info output.
- Logs go to **stderr**; the drafted commit message and normal prompts go to the console (stdout for machine-readable output such as `--dry-run`).
- **Structured logging behind a flag:** when `--verbose` is set, emit structured log records (e.g. key=value fields: `event`, `model`, `diff_bytes`, `duration_ms`, `exit_code`) so a run can be traced. Default (non-verbose) logging is quiet and human-friendly.
- Log the model id, byte sizes, and timings. **Never** log the API key, the full diff contents, or full model output at info level.

## Security

- **Never hardcode the API key.** It is read from the environment (`ANTHROPIC_API_KEY`) by the SDK. Support an optional `.env` in the working directory for convenience, but the key still lives only in the environment/`.env`, never in source.
- **Never log the key.** No debug line, no error `detail`, no structured field may include it. If you echo the environment for debugging, redact anything matching a key pattern.
- **Do not send secrets or large binary diffs to the API.** Binary changes appear in `git diff --cached` as `Binary files ... differ` with no content — that is acceptable to send (no payload). Do not read and inline binary file contents. Cap the diff at `max_diff_bytes`; above the cap, send `git diff --cached --stat` (a diffstat summary) plus a truncated diff, and warn the user.
- **Be careful what leaves the machine.** Only the diff text (or its summary), plus optional type/scope hints, is sent to the API. Document this plainly for users (see below). Do not send file paths outside the repo, environment variables, or unrelated context.
- **What data is sent to the API (document in README/help):** the staged diff produced by `git diff --cached` (or, for large diffs, a `--stat` summary and a truncated diff), and any `--type`/`--scope` you pass. Nothing else. The message is drafted by Anthropic's Claude API; treat staged content accordingly and do not stage secrets you would not want sent.

## Simplicity / YAGNI - KISS

- Build only what a phase requires. No speculative abstractions, plugin systems, provider interfaces, or caching layers.
- Prefer a plain function over a class; a module over a package; a dataclass over a config framework.
- One model call per draft. No retry/backoff logic beyond what the SDK already does (the SDK retries 429/5xx automatically). Do not add your own retry loop unless a phase asks for it.
- Do not add features that are in Non-goals (see `docs/PRD.md`).

## Code style

- **PEP 8**, enforced by `ruff` and `black`. Run both before every commit.
- **Sparse comments.** Comment *why*, not *what*. No commented-out code.
- **Concise docstrings.** One-line docstrings on public functions describing intent and return; longer only when the contract is subtle.
- **No emoji** anywhere in code, output, comments, or docs.
- **No authorship attribution** in code headers, docstrings, or commit messages — no "generated by", no "co-authored by", no assistant mention.
- **Conventional Commits** for every commit (see Conventions).
- Type-hint public functions. Keep functions small and single-purpose.

## Boundaries

- **No wholesale delete/rewrite.** Do not delete or rewrite whole modules to "clean up". Make the smallest change that satisfies the task.
- **Do not change PRD or architecture silently.** If implementation reveals that `docs/PRD.md` or `docs/architecture.md` is wrong or incomplete, stop and flag it in `docs/memory.md` (Decisions log) and to the requester before diverging. Do not quietly implement something different.
- **No new dependency without approval.** Adding, removing, or version-bumping a dependency requires explicit approval and its own commit; update `pyproject.toml` and the lockfile together.
- **Ask when ambiguous.** If a requirement is unclear or two designs are both defensible, ask rather than guess.
- **Stop after two failed fix attempts.** If a bug resists two genuine fix attempts, stop, write what you tried and the current theory in `docs/memory.md` (In progress), and ask for direction instead of thrashing.
- **Scope every change.** Classify each proposed change as: *current phase* (do it now), *new phase* (belongs in a later phase — add it to `docs/phases.md`), or *backlog* (record it in the Backlog section). Do not silently pull backlog work into the current phase.
