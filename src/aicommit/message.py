"""Present the drafted message via rich and prompt for accept/quit."""

from __future__ import annotations

from typing import IO

from rich.console import Console
from rich.panel import Panel


def present_message(console: Console, message: str) -> None:
    """Render the drafted message in a bordered panel."""
    console.print(Panel(message, title="Proposed commit message"))


def prompt_choice(console: Console, *, stream: IO[str] | None = None) -> str:
    """Prompt for accept/quit; accepts letters or words, case-insensitive.

    Blank input defaults to accept ("a"). Invalid input re-prompts.
    """
    while True:
        raw = console.input("[a]ccept  [q]uit > ", stream=stream).strip().lower()
        if raw in ("", "a", "accept"):
            return "a"
        if raw in ("q", "quit"):
            return "q"
        console.print("Please enter 'a' or 'q'.", style="yellow")
