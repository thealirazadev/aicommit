"""Click command, flags, top-level orchestration and exit codes."""

from __future__ import annotations

import click
from rich.console import Console

from aicommit import __version__, git
from aicommit.config import load_config
from aicommit.errors import AicommitError
from aicommit.message import present_message, prompt_choice
from aicommit.model import draft_message

_console = Console(stderr=True)
_stdout = Console()


@click.command()
@click.option(
    "--model",
    "-m",
    "model",
    default=None,
    help="Override the model id for this run.",
)
@click.option(
    "--dry-run",
    "-n",
    "dry_run",
    is_flag=True,
    default=False,
    help="Print the drafted message and exit without committing.",
)
@click.option(
    "--yes",
    "-y",
    "yes_",
    is_flag=True,
    default=False,
    help="Accept the first draft and commit without prompting.",
)
@click.version_option(
    version=__version__, prog_name="aicommit", message="%(prog)s %(version)s"
)
def main(model: str | None, dry_run: bool, yes_: bool) -> None:
    """Draft a Conventional Commit message from the staged git diff."""
    if dry_run and yes_:
        raise click.UsageError("--dry-run and --yes cannot be used together.")
    try:
        config = load_config(model=model)
        diff = git.require_staged_diff()
        message = draft_message(diff, config)
        if dry_run:
            _stdout.print(message)
            raise SystemExit(0)
        present_message(_stdout, message)
        choice = "a" if yes_ else prompt_choice(_stdout)
        if choice == "q":
            _console.print("Aborted.", style="red")
            raise SystemExit(130)
        sha = git.create_commit(message)
        _stdout.print(f"Committed {sha}", style="green")
    except AicommitError as error:
        _console.print(f"Error: {error.message}", style="red")
        raise SystemExit(error.exit_code) from None
    except KeyboardInterrupt:
        _console.print("Aborted.", style="red")
        raise SystemExit(130) from None
    except Exception:
        _console.print(
            "Error: Unexpected error. Re-run with --verbose for details.",
            style="red",
        )
        raise SystemExit(1) from None
    raise SystemExit(0)
