# Memory — aicommit

Running log for the implementation. Keep it short. Update it as work progresses so any agent can pick up where the last left off.

## Completed

- Planning documentation created (README, PRD, architecture, rules, design, phases, testing, memory, launch-checklist, .env.example).
- Phase 1 (draft and print) and Phase 2 (commit with confirmation) complete.
- Phase 3 (edit and regenerate) complete, all 5 commits: parse accept/edit/regenerate/quit
  choices, edit in `$EDITOR`, reject an empty edited message, regenerate with a second API
  call, `--edit` flag. Phase verification checklist passed (pytest/ruff/black clean,
  `aicommit --version` runs, no-staged/not-a-repo/missing-key exit codes verified manually).

- Phase 4 (UX and controls polish) complete, all 6 commits: spinner during the API call,
  `--type`/`--scope` constraints, `--quiet`/`--verbose` with structured logging (new
  `logging.py` module), `NO_COLOR`/`--no-color`, oversized-diff summarization (new
  `git.read_staged_diffstat`/`git.build_diff_payload`), and config-file support (new
  `_load_config_file`/`_config_file_path` in `config.py`, `.aicommit.toml` then XDG path).
  Phase verification checklist passed (pytest/ruff/black clean, `aicommit --version` runs,
  manual checks of type/scope, NO_COLOR, quiet+verbose precedence, config file, and exit
  codes all behaved as documented).

## In progress

_Nothing in progress. All four phases in `docs/phases.md` are complete._

## Decisions log

_Record notable decisions and any deviation flags here, newest first. Do not change `docs/PRD.md` or `docs/architecture.md` without flagging it here first._

- **Flag for follow-up (not silently resolved):** the config-file loader uses the standard
  library `tomllib`, which only exists on Python 3.11+. `pyproject.toml` still declares
  `requires-python = ">=3.10"` (per Phase 1 and `docs/rules.md`). On a real Python 3.10
  install, `import tomllib` in `config.py` will fail at import time, breaking the whole CLI,
  since `config.py` is imported unconditionally. `docs/rules.md` anticipates this ("`tomllib`
  (Python 3.11+) or `tomli` on 3.10") but adding `tomli` as a conditional dependency needs
  approval per the dependency-approval boundary, so it was not added here. The dev/test
  environment for this session is Python 3.12, so tests pass, but Python 3.10 users are
  currently broken. Needs a decision: add `tomli` as a conditional dependency for `<3.11`, or
  raise the minimum supported Python to 3.11 in the PRD/architecture (the latter would need
  explicit sign-off since it changes `docs/architecture.md`).
- Bug found and fixed during Phase 3 verification (not a scope change, a correctness fix to
  already-shipped Phase 1 behavior): `draft_message` called `anthropic.Anthropic()` and
  `messages.create` without ever checking `ANTHROPIC_API_KEY` up front. When the key is
  completely unset, the SDK raises a plain `TypeError` (not `AuthenticationError`), which fell
  through to the generic "Unexpected error" exit 1 instead of the documented exit 5. Fixed by
  checking `ANTHROPIC_API_KEY` before constructing the client, but only when the default
  `client_factory` (`anthropic.Anthropic`) is in use, so mocked tests with an injected fake
  client are unaffected. Verified manually: unset key now exits 5 with the documented message.
- Default model is `claude-opus-4-8`; overridable via `--model` and `AICOMMIT_MODEL`.
- CLI framework: `click` (not Typer), to keep the dependency surface small and behavior explicit.
- Commit creation uses `git commit -F <tmpfile>` so multi-line bodies survive intact.
- Package uses a `src/` layout; lockfile is `uv.lock` (fallback `requirements.lock` via pip-tools if `uv` is unavailable).
