"""Configure logging: quiet/verbose levels and structured records on stderr."""

from __future__ import annotations

import logging

LOGGER_NAME = "aicommit"


def configure_logging(*, quiet: bool, verbose: bool) -> logging.Logger:
    """Configure and return the aicommit logger.

    Default level is `WARNING`; `--verbose` sets `DEBUG` (structured records
    become visible); `--quiet` sets `ERROR`. Verbose wins if both are set.
    """
    level = logging.WARNING
    if verbose:
        level = logging.DEBUG
    elif quiet:
        level = logging.ERROR

    logger = logging.getLogger(LOGGER_NAME)
    logger.handlers.clear()
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("%(message)s"))
    logger.addHandler(handler)
    logger.setLevel(level)
    logger.propagate = False
    return logger


def log_event(logger: logging.Logger, event: str, **fields: object) -> None:
    """Emit a structured key=value debug record.

    Never pass the API key, the full diff, or full model output as a field.
    """
    kv = " ".join(f"{key}={value}" for key, value in fields.items())
    logger.debug("event=%s %s", event, kv)
