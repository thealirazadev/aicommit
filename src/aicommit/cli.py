"""Click command, flags, top-level orchestration and exit codes."""

import click

from aicommit import __version__
from aicommit.config import load_config


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
    load_config(model=model)
    raise SystemExit(0)
