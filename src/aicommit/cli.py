"""Click command, flags, top-level orchestration and exit codes."""

import click

from aicommit import __version__


@click.command()
@click.version_option(
    version=__version__, prog_name="aicommit", message="%(prog)s %(version)s"
)
def main() -> None:
    """Draft a Conventional Commit message from the staged git diff."""
    raise SystemExit(0)
