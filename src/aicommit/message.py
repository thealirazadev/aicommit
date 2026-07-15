"""Present the drafted message via rich and prompt for the next action."""

from __future__ import annotations

from typing import IO

from rich.console import Console
from rich.panel import Panel

_WORDS = {"a": "accept", "e": "edit", "r": "regenerate", "q": "quit"}


def present_message(console: Console, message: str) -> None:
    """Render the drafted message in a bordered panel."""
    console.print(Panel(message, title="Proposed commit message"))


def prompt_choice(console: Console, *, stream: IO[str] | None = None) -> str:
    """Prompt for accept/edit/regenerate/quit; accepts letters or words.

    Case-insensitive. Blank input defaults to accept ("a"). Invalid input
    re-prompts instead of raising.
    """
    while True:
        raw = (
            console.input("[a]ccept  [e]dit  [r]egenerate  [q]uit > ", stream=stream)
            .strip()
            .lower()
        )
        if raw == "":
            return "a"
        if raw in _WORDS:
            return raw
        for letter, word in _WORDS.items():
            if raw == word:
                return letter
        console.print("Please enter a, e, r, or q.", style="yellow")
