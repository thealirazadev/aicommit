"""Load and resolve configuration: defaults, environment, and CLI flags."""

from __future__ import annotations

import os
from dataclasses import dataclass

DEFAULT_MODEL = "claude-opus-4-8"


@dataclass(frozen=True)
class Config:
    """Resolved, immutable configuration for a single run."""

    model: str = DEFAULT_MODEL


def load_config(*, model: str | None = None) -> Config:
    """Resolve a `Config` from defaults, the environment, and CLI flags.

    Precedence for `model` (lowest to highest): built-in default <
    `AICOMMIT_MODEL` < `--model`.
    """
    resolved_model = model or os.environ.get("AICOMMIT_MODEL") or DEFAULT_MODEL
    return Config(model=resolved_model)
