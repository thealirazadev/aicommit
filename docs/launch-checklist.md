# Launch checklist — aicommit

Work top to bottom before the first public release. Leave items unchecked until they are genuinely done.

## Packaging and versioning

- [ ] Dependency versions are pinned exactly (`==`) in `pyproject.toml`.
- [ ] The lockfile (`uv.lock`, or `requirements.lock`) is committed and in sync with `pyproject.toml`.
- [ ] `__version__` is defined once and matches the `pyproject.toml` version.
- [ ] Python version floor (`>=3.10`) is declared and correct.
- [ ] Entry point works after install: `pipx install .` (or `pip install .`) then `aicommit --version` runs from a clean shell.
- [ ] `aicommit` is runnable both as the console script and as `python -m aicommit`.

## Functionality

- [ ] Happy path: stage a change, run `aicommit`, accept -> a commit with the exact message is created.
- [ ] `--dry-run`, `--yes`, `--edit`, `--type`, `--scope`, `--model` all behave per `docs/design.md`.
- [ ] Accept / edit / regenerate / quit flow works end to end.
- [ ] Multi-line commit bodies are preserved into the actual commit.

## Errors and robustness

- [ ] API errors are handled gracefully: missing/invalid key (exit 5), network/timeout/rate-limit/5xx (exit 6) — each a friendly one-line message, no raw traceback by default.
- [ ] No staged changes (exit 3) and not-a-git-repo (exit 4) are handled with clear messages.
- [ ] git commit failure exits 7 with the git error's first line.
- [ ] Oversized diffs fall back to a summary with a `Warning:`; binary content is never inlined.
- [ ] All exit codes match `docs/design.md`.

## Output and accessibility

- [ ] `NO_COLOR` is respected; `--no-color` produces output with no ANSI escape codes.
- [ ] `--quiet` and `--verbose` behave per `docs/design.md`; verbose logs are structured and never include the API key or full diff.
- [ ] Non-TTY / piped output falls back to plain text automatically (no spinner, no color).
- [ ] No color-only meaning: success/warning/error carry text labels.

## Security

- [ ] The API key is read only from the environment; it is never hardcoded, logged, or written to disk.
- [ ] Only the diff (or its summary) plus `--type`/`--scope` is sent to the API; documented in the README.
- [ ] `.env` is gitignored; only `.env.example` (dummy values) is committed.
- [ ] Generated commit messages contain no authorship attribution (no "Generated with", no "Co-Authored-By").

## Docs and help

- [ ] `aicommit --help` text is complete and lists every flag with a clear description.
- [ ] README install/usage/test steps are accurate against the shipped CLI.
- [ ] `docs/` reflects the final behavior (no stale claims).
- [ ] LICENSE file present (MIT) and referenced.

## Quality gates

- [ ] `pytest` passes with the API mocked and no network access.
- [ ] `ruff check .` and `black --check .` pass.
- [ ] Manual QA checklists in `docs/phases.md` completed for all phases.

## Publish to PyPI

- [ ] `pyproject.toml` metadata is complete: name, version, description, authors, license, `readme`, `requires-python`, classifiers, project URLs.
- [ ] Package name `aicommit` is available on PyPI (or an alternative is chosen and reflected everywhere).
- [ ] `uv build` (or `python -m build`) produces a clean sdist and wheel.
- [ ] `twine check dist/*` passes.
- [ ] Test install from TestPyPI in a clean environment; `aicommit --version` works.
- [ ] Tag the release (matching `__version__`) and publish to PyPI.
- [ ] Verify `pipx install aicommit` from PyPI works end to end.
