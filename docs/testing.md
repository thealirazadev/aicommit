# Testing — aicommit

## Strategy

Two layers, no network:

1. **Unit tests (`pytest`)** — each module tested in isolation. The Anthropic API is **always mocked**; the test suite must never make a real network call or require `ANTHROPIC_API_KEY`. Git is exercised against real temporary repositories created in a tmp dir (git is fast and deterministic), or mocked at the `subprocess` boundary where a real repo is overkill.
   - `test_git.py` — repo detection, staged-diff reading (empty vs non-empty), commit creation, git-failure handling. Uses a real temp repo via a fixture.
   - `test_prompt.py` — the prompt builder includes the diff and honors `--type`/`--scope`; asserts the system prompt forbids attribution.
   - `test_model.py` — `draft_message` with a fake Anthropic client: returns text on success; maps `AuthenticationError` -> `AuthError` (exit 5), `RateLimitError`/`APIConnectionError`/`APITimeoutError`/`APIStatusError(>=500)` -> `ApiError` (exit 6).
   - `test_config.py` — precedence (default < file < env < flag); malformed config file -> friendly error.
   - `test_message.py` — choice parsing (a/e/r/q + words, default, invalid re-prompt); empty-edit rejection; cleaning of model output (strip code fences/attribution if present).
   - `test_cli.py` — end-to-end through click's `CliRunner` with the API mocked: dry-run prints and does not commit; `--yes` commits; accept commits; quit exits 130; exit codes for the unhappy paths.

2. **Manual QA** — the checklists in `docs/phases.md`. These cover real editor interaction (`--edit`), the live spinner, TTY color, `NO_COLOR`, and a genuine end-to-end run against the real API. Manual QA is required before a phase is considered done, but is not part of the automated suite.

### Mocking the API

- Provide a fixture (in `conftest.py`) that supplies a fake Anthropic client whose `messages.create` returns a canned response object shaped like the SDK's (`.content` is a list of blocks with `.type == "text"` and `.text`). Inject it into `model.py` (e.g. via a client factory parameter or `monkeypatch`), so no real `anthropic.Anthropic()` is constructed in tests.
- To test error mapping, have the fake `messages.create` raise the relevant `anthropic` exception class.
- Assert on the request when it matters (e.g. the model id, that the diff is present, that type/scope constraints are passed, that no binary content is inlined).

### Fixtures

- `sample.diff` under `tests/fixtures/` — a representative staged diff reused across tests.
- A `temp_git_repo` fixture that `git init`s a tmp dir, configures a throwaway user, and stages a file, so `test_git.py` and `test_cli.py` run against a real repo without touching the developer's repo.

## Exact commands

Development install:

```sh
uv sync                       # or: pip install -e ".[dev]"
```

Run tests:

```sh
uv run pytest                 # or: pytest
uv run pytest -q              # quiet
uv run pytest tests/test_cli.py::test_accept_commits   # a single test
```

Lint and format:

```sh
uv run ruff check .           # lint
uv run black --check .        # formatting check (no changes)
uv run black .                # apply formatting
```

Build (sanity check the package):

```sh
uv build                      # or: python -m build
pip install -e .              # confirm the aicommit entry point installs
aicommit --version
```

## Gate

**Build and tests must pass before a feature is considered done.** For every commit/feature:

1. `uv run pytest` passes (API mocked, no network).
2. `uv run ruff check .` passes.
3. `uv run black --check .` passes.
4. The package still installs and `aicommit --version` runs.

A feature that breaks any of these is not done. Do not commit red tests or a broken build. Add or update tests in the same commit as the feature they cover.
