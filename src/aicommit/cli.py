"""Click command, flags, top-level orchestration and exit codes."""

from __future__ import annotations

import click
from rich.console import Console

from aicommit import __version__, git
from aicommit.config import load_config
from aicommit.errors import AicommitError

_console = Console(stderr=True)


@click.command()
@click.option(
    "--model",
    "-m",
    "model",
    default=None,
    help="Override the model id for this run.",
)
@click.version_option(
    version=__version__, prog_name="aicommit", message="%(prog)s %(version)s"
)
def main(model: str | None) -> None:
    """Draft a Conventional Commit message from the staged git diff."""
    try:
        load_config(model=model)
        git.require_staged_diff()
    except AicommitError as error:
        _console.print(f"Error: {error.message}", style="red")
        raise SystemExit(error.exit_code) from None
    except KeyboardInterrupt:
        _console.print("Aborted.", style="red")
        raise SystemExit(130) from None
    raise SystemExit(0)
