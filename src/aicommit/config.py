"""Load and resolve configuration: defaults, environment, and CLI flags."""

from __future__ import annotations

import os
from dataclasses import dataclass

DEFAULT_MODEL = "claude-opus-4-8"
DEFAULT_MAX_DIFF_BYTES = 100_000


@dataclass(frozen=True)
class Config:
    """Resolved, immutable configuration for a single run."""

    model: str = DEFAULT_MODEL
    commit_type: str | None = None
    scope: str | None = None
    max_diff_bytes: int = DEFAULT_MAX_DIFF_BYTES


def load_config(
    *,
    model: str | None = None,
    commit_type: str | None = None,
    scope: str | None = None,
) -> Config:
    """Resolve a `Config` from defaults, the environment, and CLI flags.

    Precedence for `model` (lowest to highest): built-in default <
    `AICOMMIT_MODEL` < `--model`. `commit_type`/`scope` currently come only
    from CLI flags (config-file layering arrives in a later phase).
    """
    resolved_model = model or os.environ.get("AICOMMIT_MODEL") or DEFAULT_MODEL
    return Config(model=resolved_model, commit_type=commit_type, scope=scope)
