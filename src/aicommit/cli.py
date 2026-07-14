"""Click command, flags, top-level orchestration and exit codes."""

import click


@click.command()
def main() -> None:
    """Draft a Conventional Commit message from the staged git diff."""
    raise SystemExit(0)
