"""Load and resolve configuration: defaults, config file, environment, flags."""

from __future__ import annotations

import os
import sys
from dataclasses import dataclass
from pathlib import Path

if sys.version_info >= (3, 11):
    import tomllib
else:  # pragma: no cover - exercised by the 3.10 CI job
    import tomli as tomllib

from aicommit.errors import ConfigError

DEFAULT_MODEL = "claude-opus-5-5"
DEFAULT_MAX_DIFF_BYTES = 100_000
CONFIG_FILENAME = ".aicommit.toml"


@dataclass(frozen=True)
class Config:
    """Resolved, immutable configuration for a single run."""

    model: str = DEFAULT_MODEL
    commit_type: str | None = None
    scope: str | None = None
    max_diff_bytes: int = DEFAULT_MAX_DIFF_BYTES


def _config_file_path() -> Path | None:
    """Return the first config file found: project-local, then XDG."""
    local = Path(CONFIG_FILENAME)
    if local.is_file():
        return local
    xdg_home = os.environ.get("XDG_CONFIG_HOME")
    base = Path(xdg_home) if xdg_home else Path.home() / ".config"
    candidate = base / "aicommit" / "config.toml"
    return candidate if candidate.is_file() else None


def _load_config_file() -> dict:
    """Return the parsed config file, or `{}` if none exists.

    Raises `ConfigError` (exit 1) if a config file exists but is malformed.
    """
    path = _config_file_path()
    if path is None:
        return {}
    try:
        with path.open("rb") as config_file:
            return tomllib.load(config_file)
    except (tomllib.TOMLDecodeError, OSError) as error:
        raise ConfigError(str(path), detail=str(error)) from error


def load_config(
    *,
    model: str | None = None,
    commit_type: str | None = None,
    scope: str | None = None,
) -> Config:
    """Resolve a `Config` from defaults, an optional config file, the
    environment, and CLI flags.

    Precedence (lowest to highest):
    - `model`: built-in default < config file `model` < `AICOMMIT_MODEL` <
      `--model`.
    - `commit_type`/`scope`: built-in default (`None`) < config file
      (`type`/`scope`) < `--type`/`--scope`.
    - `max_diff_bytes`: built-in default < config file.
    """
    file_data = _load_config_file()
    resolved_model = (
        model
        or os.environ.get("AICOMMIT_MODEL")
        or file_data.get("model")
        or DEFAULT_MODEL
    )
    resolved_commit_type = commit_type or file_data.get("type")
    resolved_scope = scope or file_data.get("scope")
    resolved_max_diff_bytes = file_data.get("max_diff_bytes", DEFAULT_MAX_DIFF_BYTES)
    return Config(
        model=resolved_model,
        commit_type=resolved_commit_type,
        scope=resolved_scope,
        max_diff_bytes=resolved_max_diff_bytes,
    )
