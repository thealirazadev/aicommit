# aicommit

aicommit is a command-line tool that reads your staged git diff, asks the Anthropic Claude API to draft a Conventional Commit message, and lets you accept, edit, or regenerate that message before it creates the commit for you.

## Features

- Reads the staged diff (`git diff --cached`) and drafts a Conventional Commit message from it.
- Interactive accept / edit / regenerate / quit flow before anything is committed.
- Conventional Commits output: `type(scope): summary` subject plus an optional body.
- Override the commit `--type` and `--scope`; nudge regenerations without retyping.
- `--dry-run` prints the draft without committing; `--yes` accepts the first draft non-interactively.
- Colored output and a spinner via `rich`; honors `NO_COLOR` and `--no-color`.
- Friendly, specific errors for the common failures: nothing staged, not a git repo, missing/invalid API key, network/rate-limit errors, oversized or binary diffs.
- Configurable model via `--model`, the `AICOMMIT_MODEL` environment variable, or a config file.

## Tech stack

- Python 3.10+ CLI packaged with `pyproject.toml`, exposing a console entry point named `aicommit`.
- [`click`](https://click.palletsprojects.com/) for the command-line interface.
- [`rich`](https://rich.readthedocs.io/) for colored output and the progress spinner.
- [`anthropic`](https://pypi.org/project/anthropic/) SDK targeting the Claude Messages API (default model `claude-opus-4-8`).
- Git access through the `git` executable via `subprocess` (no libgit2 dependency).
- `pytest` for tests, with the Anthropic API mocked (no network in the test suite).
- `ruff` and `black` for linting and formatting.

See `docs/architecture.md` for the full design and `docs/phases.md` for the build order.

## Prerequisites

- Python 3.10 or newer.
- `git` on your `PATH`.
- An Anthropic API key exported as `ANTHROPIC_API_KEY` (see `.env.example`).

## Install

Recommended (isolated, global CLI):

```sh
pipx install aicommit
```

Or into the current environment:

```sh
pip install aicommit
```

From source (development):

```sh
git clone <repo-url>
cd aicommit
uv sync            # or: pip install -e ".[dev]"
```

## Configure

Export your key (or put it in a `.env` file in the project you are committing in):

```sh
export ANTHROPIC_API_KEY="sk-ant-..."
```

Copy `.env.example` to `.env` and fill it in. `AICOMMIT_MODEL` is optional and overrides the default model.

## Usage

Stage some changes, then run:

```sh
git add -p
aicommit
```

You will be shown a drafted message and prompted to accept, edit, regenerate, or quit.

Common flags:

```sh
aicommit --type fix --scope parser   # force the type and scope
aicommit --dry-run                   # print the draft, do not commit
aicommit --yes                       # accept the first draft, commit immediately
aicommit --edit                      # open the draft in $EDITOR before committing
aicommit --model claude-opus-4-8     # override the model
aicommit --verbose                   # detailed logs on stderr
```

See `aicommit --help` for the complete list, and `docs/design.md` for the full UX.

## Test

```sh
uv run pytest            # or: pytest
uv run ruff check .
uv run black --check .
```

The test suite mocks the Anthropic API and never makes network calls. See `docs/testing.md` for the exact commands.

## Project structure

```
aicommit/
  README.md            This file (the only doc at the repository root).
  pyproject.toml       Packaging, dependencies, and the aicommit entry point.
  uv.lock              Pinned, committed lockfile.
  .env.example         Documented environment variables (dummy values).
  docs/                Planning and handoff documentation.
  src/aicommit/        Application source (CLI, git, prompt, model, config).
  tests/               pytest suite with the API mocked.
```

## License: MIT
