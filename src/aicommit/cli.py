"""Click command, flags, top-level orchestration and exit codes."""

from __future__ import annotations

import contextlib
import time

import click
from rich.console import Console

from aicommit import __version__, git
from aicommit.config import load_config
from aicommit.errors import AicommitError
from aicommit.logging import configure_logging, log_event
from aicommit.message import edit_message, present_message, prompt_choice
from aicommit.model import draft_message

_console = Console(stderr=True)
_stdout = Console()


def _drafting_status(text: str, *, quiet: bool):
    """Return a spinner context manager, or a no-op one off a TTY / quiet."""
    if quiet or not _stdout.is_terminal:
        return contextlib.nullcontext()
    return _stdout.status(text)


def _draft_and_log(logger, diff: str, config, *, quiet: bool, event: str, text: str):
    """Draft a message under the spinner, logging timing and size."""
    started = time.perf_counter()
    with _drafting_status(text, quiet=quiet):
        message = draft_message(diff, config)
    duration_ms = round((time.perf_counter() - started) * 1000)
    log_event(
        logger,
        event,
        model=config.model,
        diff_bytes=len(diff.encode()),
        duration_ms=duration_ms,
    )
    return message


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
@click.option(
    "--edit",
    "-e",
    "edit_",
    is_flag=True,
    default=False,
    help="Open the drafted message in $EDITOR before the accept step.",
)
@click.option(
    "--type",
    "-t",
    "commit_type",
    default=None,
    help="Force the Conventional Commit type (e.g. feat, fix).",
)
@click.option(
    "--scope",
    "-s",
    "scope",
    default=None,
    help="Force the commit scope; appears as type(scope): ...",
)
@click.option(
    "--quiet",
    "-q",
    "quiet",
    is_flag=True,
    default=False,
    help="Suppress non-essential output (spinner, hints).",
)
@click.option(
    "--verbose",
    "-v",
    "verbose",
    is_flag=True,
    default=False,
    help="Emit structured debug logs on stderr.",
)
@click.version_option(
    version=__version__, prog_name="aicommit", message="%(prog)s %(version)s"
)
def main(
    model: str | None,
    dry_run: bool,
    yes_: bool,
    edit_: bool,
    commit_type: str | None,
    scope: str | None,
    quiet: bool,
    verbose: bool,
) -> None:
    """Draft a Conventional Commit message from the staged git diff."""
    if dry_run and yes_:
        raise click.UsageError("--dry-run and --yes cannot be used together.")
    logger = configure_logging(quiet=quiet, verbose=verbose)

    def _exit(code: int) -> None:
        log_event(logger, "exit", exit_code=code)
        raise SystemExit(code)

    try:
        config = load_config(model=model, commit_type=commit_type, scope=scope)
        diff = git.require_staged_diff()
        message = _draft_and_log(
            logger,
            diff,
            config,
            quiet=quiet,
            event="draft",
            text="Drafting commit message...",
        )
        if dry_run:
            _stdout.print(message)
            _exit(0)
        if edit_:
            message = edit_message(message)
        if yes_:
            sha = git.create_commit(message)
            _stdout.print(f"Committed {sha}", style="green")
            _exit(0)
        present_message(_stdout, message)
        while True:
            choice = prompt_choice(_stdout)
            log_event(logger, "choice", value=choice)
            if choice == "q":
                _console.print("Aborted.", style="red")
                _exit(130)
            if choice == "e":
                message = edit_message(message)
                present_message(_stdout, message)
                continue
            if choice == "r":
                message = _draft_and_log(
                    logger,
                    diff,
                    config,
                    quiet=quiet,
                    event="regenerate",
                    text="Regenerating...",
                )
                present_message(_stdout, message)
                continue
            break
        sha = git.create_commit(message)
        _stdout.print(f"Committed {sha}", style="green")
    except AicommitError as error:
        _console.print(f"Error: {error.message}", style="red")
        _exit(error.exit_code)
    except KeyboardInterrupt:
        _console.print("Aborted.", style="red")
        _exit(130)
    except Exception:
        logger.debug("event=unexpected_error", exc_info=True)
        _console.print(
            "Error: Unexpected error. Re-run with --verbose for details.",
            style="red",
        )
        _exit(1)
    _exit(0)
