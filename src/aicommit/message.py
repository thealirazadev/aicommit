"""Present the drafted message via rich and prompt for the next action."""

from __future__ import annotations

from typing import IO

import click
from rich.console import Console
from rich.panel import Panel

from aicommit.errors import EmptyMessageError

_WORDS = {"a": "accept", "e": "edit", "r": "regenerate", "q": "quit"}


def present_message(console: Console, message: str) -> None:
    """Render the drafted message in a bordered panel."""
    console.print(Panel(message, title="Proposed commit message"))


def edit_message(message: str) -> str:
    """Open the current draft in `$EDITOR`; return the edited, stripped text.

    Falls back to the original message if the editor reports no change
    (`click.edit` returns `None` in that case). Raises `EmptyMessageError`
    if the user explicitly saved a blank message.
    """
    edited = click.edit(message)
    if edited is None:
        return message
    edited = edited.strip()
    if not edited:
        raise EmptyMessageError()
    return edited


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
