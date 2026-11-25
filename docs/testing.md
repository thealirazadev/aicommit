# Testing: aicommit

## Strategy

The automated suite is `pytest` and never touches the network:

- The Anthropic API is always mocked. The suite must never make a real network call or require `ANTHROPIC_API_KEY`. `model.draft_message` takes a `client_factory`, and the CLI tests monkeypatch `aicommit.cli.draft_message`, so no real `anthropic.Anthropic()` is used.
- Git is exercised against real temporary repositories created in a tmp dir (git is fast and deterministic).

Test modules:

- `test_git.py`: repo detection, staged-diff reading (empty vs non-empty), the diffstat, oversized-diff summarizing, binary files not being inlined, commit creation with the exact message, and git-failure handling. Uses a real temp repo via a fixture.
- `test_prompt.py`: the prompt builder includes the diff and honors `--type`/`--scope`; the system prompt forbids attribution.
- `test_model.py`: `draft_message` with a fake Anthropic client: returns text on success and sends the configured model, diff and constraints; maps `AuthenticationError`/`PermissionDeniedError` and a missing key to `AuthError` (exit 5), `RateLimitError`/`APIConnectionError`/`APITimeoutError`/`APIStatusError(>=500)` to `ApiError` (exit 6), and re-raises other status errors.
- `test_config.py`: precedence (default < file < env < flag), local file over the XDG file, and a malformed config file raising a friendly error.
- `test_message.py`: choice parsing (a/e/r/q and words, case-insensitive, blank default, invalid re-prompt), the prompt showing every choice letter, and the edit cases (edited text, unchanged editor, blank save).
- `test_cli.py`: end to end through click's `CliRunner` with drafting mocked: dry-run, `--yes`, accept, quit (130), edit, regenerate (a second draft call), `--edit`, spinner on and off a TTY, `--quiet`, `--verbose` without the key, color and `NO_COLOR`, oversized diffs, and the exit codes for every unhappy path.
- `test_package.py`: the version is defined and the CLI runs.

Real editor interaction, the live spinner in a terminal and a run against the real API are checked by hand; they are not part of the automated suite.

### Mocking the API

- `conftest.py` provides a fake Anthropic client whose `messages.create` records its keyword arguments and returns a canned response shaped like the SDK's (`.content` is a list of blocks with `.type == "text"` and `.text`).
- To test error mapping, the fake `messages.create` raises the relevant `anthropic` exception class.
- Tests assert on the request where it matters (the model id, that the diff is present, that type/scope constraints are passed).

### Fixtures

- `sample.diff` under `tests/fixtures/`: a representative staged diff.
- `temp_git_repo` `git init`s a tmp dir, configures a throwaway user, stages a file and changes into it; `empty_git_repo` does the same with nothing staged.

## Exact commands

Development install:

```sh
uv sync --all-extras          # or: pip install -e ".[dev]"
```

Run tests:

```sh
uv run pytest                 # or: pytest
uv run pytest -q              # quiet
uv run pytest tests/test_cli.py::test_accept_creates_commit   # a single test
```

`pytest` is configured in `pyproject.toml` to run with `--cov=aicommit`, and coverage fails under 90 percent (`[tool.coverage.report] fail_under = 90`).

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

## CI

`.github/workflows/ci.yml` runs on every push and pull request to `main`, on Python 3.10 and 3.13:

1. `uv sync --frozen --all-extras` (installs from the committed `uv.lock`; fails if it is out of date).
2. `uv run ruff check .`
3. `uv run black --check .`
4. `uv run pytest` (with the 90 percent coverage gate).

Run the same three checks locally before pushing.
