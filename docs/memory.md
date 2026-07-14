# Memory — aicommit

Running log for the implementation. Keep it short. Update it as work progresses so any agent can pick up where the last left off.

## Completed

- Planning documentation created (README, PRD, architecture, rules, design, phases, testing, memory, launch-checklist, .env.example).

## In progress

_Nothing yet. Record the current task, the approach, and anything half-finished here. If a bug resists two fix attempts, stop and write what was tried and the current theory (see `docs/rules.md` — Boundaries)._

## Decisions log

_Record notable decisions and any deviation flags here, newest first. Do not change `docs/PRD.md` or `docs/architecture.md` without flagging it here first._

- Default model is `claude-opus-4-8`; overridable via `--model` and `AICOMMIT_MODEL`.
- CLI framework: `click` (not Typer), to keep the dependency surface small and behavior explicit.
- Commit creation uses `git commit -F <tmpfile>` so multi-line bodies survive intact.
- Package uses a `src/` layout; lockfile is `uv.lock` (fallback `requirements.lock` via pip-tools if `uv` is unavailable).
