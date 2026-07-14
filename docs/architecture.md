# Architecture — aicommit

## Flow

```
git diff --cached
        |
        v
[git.py]  read staged diff  ---- empty? ------> friendly error, exit 3
        |                   ---- not a repo? --> friendly error, exit 4
        v
[prompt.py]  build system + user prompt from the diff (+ optional type/scope)
        |
        v
[model.py]  call Anthropic Messages API (spinner while waiting)
        |          |
        |          +-- auth error -----> friendly error, exit 5
        |          +-- network/429/5xx-> friendly error, exit 6
        v
[message.py]  clean + parse draft, present it
        |
        v
   prompt: [a]ccept / [e]dit / [r]egenerate / [q]uit
        |        |            |             |
     accept    edit        regenerate      quit --> exit 130 (no commit)
        |        |            |
        |     $EDITOR      back to model.py (re-draft)
        |        |            |
        |        +----- re-present ---------+
        v
[git.py]  git commit -F <message>  ---- commit failed? --> friendly error, exit 7
        |
        v
   success, exit 0
```

`--dry-run` stops after presenting and prints the draft (exit 0, no prompt, no commit).
`--yes` skips the prompt and commits the first draft.

## Proposed folder / file tree

```
aicommit/
  README.md
  pyproject.toml            packaging, deps, [project.scripts] aicommit = "aicommit.cli:main"
  uv.lock                   committed lockfile
  .env.example
  .gitignore
  docs/                     this documentation set
  src/
    aicommit/
      __init__.py           __version__ defined here
      __main__.py           enables `python -m aicommit`, calls cli.main
      cli.py                click command, flags, top-level orchestration and exit codes
      config.py             load/merge config (defaults < file < env < flags); Config dataclass
      git.py                subprocess wrappers: repo check, staged diff, diffstat, commit
      prompt.py             build the system + user prompt; the model instructions live here
      model.py              Anthropic client wrapper; draft_message(); maps SDK errors -> app errors
      message.py            clean model output; present via rich; accept/edit/regenerate loop
      errors.py             AicommitError hierarchy carrying (message, exit_code, detail)
      logging.py            configure logging; quiet vs verbose; structured logs behind --verbose
  tests/
    __init__.py
    conftest.py             fixtures: fake Anthropic client, temp git repo, sample diff
    fixtures/
      sample.diff           a representative staged diff used across tests
    test_git.py
    test_prompt.py
    test_model.py           API fully mocked
    test_config.py
    test_message.py
    test_cli.py             end-to-end via click's CliRunner, API mocked
```

Rationale for the `src/` layout: it prevents the tests from importing the package from the working tree by accident, which catches packaging mistakes (a missing module won't be found unless it's actually installed). Standard for distributable CLIs.

## Tech stack with rationale

- **Python 3.10+** — broad availability; 3.10 gives `match`/structural pattern matching and modern typing. Ships everywhere developers already have git.
- **click** — mature, dependency-light CLI framework with a built-in test runner (`CliRunner`), `$EDITOR` integration (`click.edit`), and `click.confirm`/`click.prompt`. Chosen over Typer to keep the dependency surface small and the behavior explicit. Do not mix in Typer.
- **rich** — colored panels for the draft, a status spinner during the API call, and automatic `NO_COLOR` handling. Console output is routed through a single `rich.Console` so color can be disabled globally.
- **anthropic** (official SDK) — calls the Claude Messages API. The message is short, so a single non-streaming `client.messages.create(...)` with a small `max_tokens` is sufficient; streaming is unnecessary and would add complexity.
- **subprocess + the `git` binary** — no native git bindings to build or ship. `git diff --cached` and `git commit` are stable interfaces. Every git call is wrapped in `git.py` so error handling and testing are centralized.
- **pytest** — the API is mocked; tests are unit-level plus click `CliRunner` end-to-end tests. No network in CI.
- **ruff + black** — fast linting and deterministic formatting.

## Model call

Default model: `claude-opus-4-8` (override with `--model` or `AICOMMIT_MODEL`). The request is a single non-streaming Messages API call:

```python
# model.py (shape, not final code)
import anthropic

client = anthropic.Anthropic()  # reads ANTHROPIC_API_KEY from the environment
response = client.messages.create(
    model=cfg.model,             # default "claude-opus-4-8"
    max_tokens=1024,             # a commit message is small; well within timeout limits
    system=SYSTEM_PROMPT,        # instructions from prompt.py
    messages=[{"role": "user", "content": user_prompt}],
)
text = "".join(b.text for b in response.content if b.type == "text")
```

Notes for the implementer:
- Construct the client with no arguments so it resolves `ANTHROPIC_API_KEY` from the environment. Do not pass the key around in code or log it.
- `max_tokens=1024` is deliberate: output is a short commit message, so non-streaming has no timeout risk (the SDK only requires streaming for very large `max_tokens`).
- Catch `anthropic.AuthenticationError` and `anthropic.PermissionDeniedError` and raise the app's auth error (exit 5). Catch `anthropic.RateLimitError`, `anthropic.APIConnectionError`, `anthropic.APITimeoutError`, and `anthropic.APIStatusError` (>=500) and raise the app's API error (exit 6). Catch most-specific first.
- Regenerate makes another `messages.create` call; optionally append a short "give me a different message" nudge to the user content.

## Data model (config only)

The tool holds no persistent state beyond an optional config file. Configuration is resolved into a single immutable `Config` object at startup.

`Config` fields:

| Field           | Type            | Default            | Source order (lowest first)                 |
| --------------- | --------------- | ------------------ | ------------------------------------------- |
| `model`         | `str`           | `claude-opus-4-8`  | built-in < config file < `AICOMMIT_MODEL` < `--model` |
| `commit_type`   | `str \| None`   | `None`             | built-in < config file < `--type`           |
| `scope`         | `str \| None`   | `None`             | built-in < config file < `--scope`          |
| `max_diff_bytes`| `int`           | `100000`           | built-in < config file                      |
| `no_color`      | `bool`          | `False`            | built-in < `NO_COLOR` env < `--no-color`    |

`ANTHROPIC_API_KEY` is intentionally **not** stored on `Config`; it is read by the SDK from the environment only.

Optional config file (TOML), searched in this order, first found wins:
1. `./.aicommit.toml` (project-local, next to the repo you are committing in)
2. `$XDG_CONFIG_HOME/aicommit/config.toml` (falls back to `~/.config/aicommit/config.toml`)

Example config file:

```toml
model = "claude-opus-4-8"
# type = "feat"
# scope = "cli"
max_diff_bytes = 100000
```

If no config file exists, defaults apply. A malformed config file is a friendly error (exit 1), not a crash.

## Where state lives

- **Runtime, in memory:** the resolved `Config`, the captured diff, and the current draft. Nothing is written to disk except the commit itself.
- **Commit creation:** the accepted message is written to a temporary file and passed to `git commit -F <tmpfile>` so multi-line bodies and special characters survive intact; the temp file is deleted afterward.
- **On disk, optional and user-owned:** the config file above. The tool never writes it automatically.
- **Never stored:** the API key, the diff, or any model output is not persisted or cached.

## External dependencies and required environment variables

Runtime dependencies (pinned exactly in `pyproject.toml` and `uv.lock` — see `docs/rules.md`):

- `anthropic` — Claude Messages API SDK.
- `click` — CLI framework.
- `rich` — terminal output and spinner.

Dev dependencies: `pytest`, `ruff`, `black`.

External systems:

- **Anthropic Claude API** (`https://api.anthropic.com`) via the `anthropic` SDK. Reached over the network on every draft/regenerate.
- **`git` executable** on `PATH`, invoked via `subprocess`.

Environment variables:

| Variable            | Required | Read by            | Purpose                                                        |
| ------------------- | -------- | ------------------ | -------------------------------------------------------------- |
| `ANTHROPIC_API_KEY` | Yes      | anthropic SDK      | Authenticates API calls. Never logged or persisted by aicommit.|
| `AICOMMIT_MODEL`    | No       | config.py          | Overrides the default model id.                                |
| `EDITOR`            | No       | message.py (edit)  | Editor used by `--edit`; falls back to click's default.        |
| `NO_COLOR`          | No       | logging/console    | If set (any value), disables colored output.                   |

A `.env` file in the working directory may be loaded for convenience (document this behavior; keep it optional and do not require a dotenv library if the SDK/shell already provides the variable).
