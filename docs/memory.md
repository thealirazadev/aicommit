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

- Python 3.10 support: the config loader uses `tomllib` on 3.11+ and the `tomli` backport on
  3.10 (a conditional dependency, as `docs/rules.md` specifies). CI runs the suite on 3.10 and 3.13.
- Bug found and fixed during Phase 3 verification (not a scope change, a correctness fix to
  already-shipped Phase 1 behavior): `draft_message` called `anthropic.Anthropic()` and
  `messages.create` without ever checking `ANTHROPIC_API_KEY` up front. When the key is
  completely unset, the SDK raises a plain `TypeError` (not `AuthenticationError`), which fell
  through to the generic "Unexpected error" exit 1 instead of the documented exit 5. Fixed by
  checking `ANTHROPIC_API_KEY` before constructing the client, but only when the default
  `client_factory` (`anthropic.Anthropic`) is in use, so mocked tests with an injected fake
  client are unaffected. Verified manually: unset key now exits 5 with the documented message.
- Default model is `claude-opus-5-5` (was `claude-opus-4-8` until 2026-11-09); overridable via `--model` and `AICOMMIT_MODEL`.
- CLI framework: `click` (not Typer), to keep the dependency surface small and behavior explicit.
- Commit creation uses `git commit -F <tmpfile>` so multi-line bodies survive intact.
- Package uses a `src/` layout; lockfile is `uv.lock` (fallback `requirements.lock` via pip-tools if `uv` is unavailable).

## Real-model manual run (2026-11-09)

- Ran the phase 1 and phase 3 manual checklists in a scratch repo against Claude Opus 5.5 via a
  local Anthropic-Messages shim (calls the Claude Code CLI; outside the repo). The staged diff
  (a new `divide` with a zero guard) produced `feat(calc): add divide function with
  zero-division guard` plus a body; accept committed the exact message, quit exited 130 with no
  commit, `--yes` committed, `--dry-run --yes` exited 2; exit codes 3 (nothing staged), 4
  (outside repo), 5 (unset key, and a wrong key against the real API), 6 (unreachable base URL,
  no traceback).
- Fixed: the interactive prompt rendered as `ccept  dit  egenerate  uit` because rich read
  `[a]`, `[e]`, `[r]`, `[q]` as style tags; the brackets are now escaped, with a test.
- **Flagged architecture.md/rules.md change:** default model `claude-opus-4-8` ->
  `claude-opus-5-5` (the id only).
