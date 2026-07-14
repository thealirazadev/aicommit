# Phases — aicommit

Build in the order below. Each phase is independently shippable and leaves the tool working. Do one commit per feature/task, in the listed order, using Conventional Commits (see `docs/rules.md`). Do not start a later phase's work early; if you discover something that belongs later, record it in Backlog or as a new phase.

---

## Phase 1 — Draft and print

Lay the foundation and get a drafted message out of the tool. At the end of this phase `aicommit` reads the staged diff, drafts a Conventional Commit message via the Claude API, and prints it to stdout. It does not commit yet.

### Definition of done

- The package installs and exposes the `aicommit` console command (`pip install -e .` / `uv sync`, then `aicommit --version` works).
- `pyproject.toml` declares the entry point, exact-pinned dependencies, and Python 3.10+; the lockfile is committed.
- With staged changes, `aicommit` prints a Conventional Commit message whose subject matches `^(feat|fix|docs|style|refactor|perf|test|build|ci|chore|revert)(\(.+\))?!?: .+` and contains no attribution lines.
- The model id resolves from `--model` > `AICOMMIT_MODEL` > built-in default (`claude-opus-4-8`). (Config file support is deferred to Phase 4.)
- These errors work with the documented exit codes and one-line messages: no staged changes (3), not a git repo (4), missing/invalid API key (5), network/rate-limit/5xx (6).
- No raw traceback is printed by default.
- `pytest`, `ruff check .`, and `black --check .` pass. The API is mocked in tests.

### Manual test checklist

- [ ] In a git repo with staged changes, run `aicommit`; a plausible message prints.
- [ ] `aicommit --version` prints the version; `aicommit --help` prints help.
- [ ] `aicommit --model claude-opus-4-8` targets that model (verify via `--verbose` log or a mocked assertion).
- [ ] With nothing staged, exit code is 3 and the message names `git add`.
- [ ] Outside any git repo, exit code is 4.
- [ ] With `ANTHROPIC_API_KEY` unset or wrong, exit code is 5.
- [ ] With the network unreachable, exit code is 6 and no traceback appears.

### Commits

1. `chore: scaffold package with pyproject and aicommit entry point`
2. `chore: pin dependencies and commit lockfile`
3. `feat: add version and help output`
4. `feat: resolve model config from flag, env, and default`
5. `feat: read staged diff via git subprocess`
6. `feat: detect missing repo and empty staged diff`
7. `feat: build conventional-commit prompt from the diff`
8. `feat: draft a commit message via the anthropic api`
9. `feat: map api auth and network failures to friendly errors`
10. `feat: print the drafted message to stdout`

---

## Phase 2 — Commit with confirmation

Turn the printer into a committer. Present the draft and let the user accept or quit; on accept, create the commit.

### Definition of done

- After drafting, `aicommit` shows the message in a panel and prompts `[a]ccept` / `[q]uit` (edit/regenerate arrive in Phase 3).
- Accept creates the commit via `git commit -F <tmpfile>`; `git log -1 --pretty=%B` equals the accepted message exactly (multi-line preserved). Exit 0, with a `Committed <sha>` confirmation.
- A failed `git commit` exits 7 with the git error's first line.
- Quit and Ctrl-C exit 130 with `Aborted.` and create no commit.
- `--dry-run` prints the message and exits 0 without prompting or committing.
- `--yes` accepts the first draft and commits without prompting; `--dry-run` + `--yes` is a usage error (exit 2).
- Tests cover accept-commits, quit-no-commit, dry-run, and `--yes`.

### Manual test checklist

- [ ] Run `aicommit`, choose accept; the commit exists with the exact message.
- [ ] Run `aicommit`, choose quit; no commit is created, exit 130.
- [ ] `aicommit --dry-run` prints and does not commit.
- [ ] `aicommit --yes` commits the first draft with no prompt.
- [ ] `aicommit --dry-run --yes` exits 2 with a usage error.
- [ ] A multi-line body survives into `git log -1 --pretty=%B` unchanged.

### Commits

1. `feat: create commit from message via git commit -F`
2. `feat: present the draft in a panel with an accept/quit prompt`
3. `feat: wire accept to commit and quit to exit 130`
4. `feat: report git commit failures with exit code 7`
5. `feat: add --dry-run to print without committing`
6. `feat: add --yes to accept the first draft`

---

## Phase 3 — Edit and regenerate

Complete the interactive loop.

### Definition of done

- The prompt now offers `[a]ccept` / `[e]dit` / `[r]egenerate` / `[q]uit`, accepting letters and full words, case-insensitive, defaulting to accept on empty input; unrecognized input re-prompts.
- Edit opens the current draft in `$EDITOR`; a non-empty result replaces the draft and re-presents; an empty result exits 1 with `Commit message is empty; nothing committed.`.
- Regenerate makes a second API call and re-presents the new draft, staying in the loop.
- `--edit` opens the editor once immediately after the first draft, then continues the normal flow (and commits directly if combined with `--yes`).
- Tests cover edit-nonempty, edit-empty, regenerate (asserting a second API call), and the choice parser.

### Manual test checklist

- [ ] Choose edit, change the message, save; the edited text is presented and can be accepted.
- [ ] Choose edit, save an empty message; exit 1, no commit.
- [ ] Choose regenerate; a different draft appears and the loop continues.
- [ ] `aicommit --edit` opens the editor before the first prompt.
- [ ] Entering an unrecognized choice re-prompts instead of crashing.

### Commits

1. `feat: parse accept/edit/regenerate/quit choices`
2. `feat: edit the draft in $EDITOR before committing`
3. `feat: reject an empty edited message`
4. `feat: regenerate the draft with a second api call`
5. `feat: add --edit to open the editor after drafting`

---

## Phase 4 — UX and controls polish

Add the remaining flags, output controls, and robustness.

### Definition of done

- A spinner shows while waiting on the API (initial draft and regenerate), only on a TTY and not under `--quiet`.
- `--type` and `--scope` constrain the drafted subject (`--type fix` yields a `fix` subject; `--scope api` yields `(api)`).
- `--quiet` and `--verbose` behave per `docs/design.md`; `--verbose` emits structured logs (key=value fields) on stderr and never logs the key or full diff.
- `NO_COLOR` and `--no-color` disable all ANSI color; output verified free of escape codes.
- Large diffs (> `max_diff_bytes`) fall back to a `git diff --cached --stat` summary plus a truncated diff, with a `Warning:` line; the tool still drafts a message.
- Binary changes are not inlined (only git's `Binary files ... differ` marker is sent).
- Config file support: `./.aicommit.toml` then `$XDG_CONFIG_HOME/aicommit/config.toml` (`~/.config/...` fallback), layered below env and flags; a malformed file is a friendly error (exit 1).
- Tests cover type/scope constraints, NO_COLOR output, large-diff fallback, and config-file precedence.

### Manual test checklist

- [ ] `aicommit --type fix --scope parser` produces `fix(parser): ...`.
- [ ] `NO_COLOR=1 aicommit --dry-run` output contains no ANSI codes; `--no-color` too.
- [ ] `aicommit --verbose` prints structured logs on stderr; the key never appears.
- [ ] `aicommit --quiet` suppresses the spinner and hints.
- [ ] Stage a very large change; a `Warning:` prints and a message is still drafted from the summary.
- [ ] Stage a binary file; no binary content is sent (check `--verbose` diff bytes / a mocked-request assertion).
- [ ] A `.aicommit.toml` with `model = "..."` is used when no flag/env is set; a flag still overrides it.

### Commits

1. `feat: show a spinner while calling the api`
2. `feat: add --type and --scope constraints`
3. `feat: add --quiet and --verbose with structured logging`
4. `feat: honor NO_COLOR and --no-color`
5. `feat: summarize oversized diffs before sending`
6. `feat: load configuration from an optional config file`

---

## Phase verification

Run after each phase; run the full list before calling a phase done.

- [ ] `uv run pytest` (or `pytest`) passes with the API mocked and no network access.
- [ ] `ruff check .` and `black --check .` pass.
- [ ] `pip install -e .` (or `uv sync`) succeeds and `aicommit --version` runs from a clean shell.
- [ ] Happy path: stage a change, run `aicommit`, and reach the phase's intended outcome (print in Phase 1; commit in Phase 2+).
- [ ] Output check: the drafted subject matches the Conventional Commit pattern and contains no attribution lines.
- [ ] Exit codes match `docs/design.md` for every path exercised.

Unhappy paths (exercise the ones the phase implements):

- [ ] No staged changes -> exit 3, friendly message.
- [ ] Not a git repository -> exit 4.
- [ ] Missing/invalid `ANTHROPIC_API_KEY` -> exit 5, key never printed.
- [ ] Network down (simulate) -> exit 6, no traceback by default.
- [ ] Huge diff -> `Warning:` and a message drafted from the summary (Phase 4).
- [ ] Binary files staged -> no binary content sent; a message is still drafted (Phase 4).
- [ ] Quiet mode: no spinner/hints; only essential output and errors.
- [ ] Verbose mode: structured logs on stderr, still a friendly one-line error, still no raw traceback and no key.

## Backlog

_Empty. Record out-of-scope ideas and deferred work here with a one-line rationale; do not implement without approval._
