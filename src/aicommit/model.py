"""Anthropic client wrapper: draft a commit message from a diff."""

from __future__ import annotations

from collections.abc import Callable

import anthropic

from aicommit.config import Config
from aicommit.prompt import SYSTEM_PROMPT, build_prompt

ClientFactory = Callable[[], anthropic.Anthropic]


def draft_message(
    diff: str,
    config: Config,
    *,
    client_factory: ClientFactory = anthropic.Anthropic,
) -> str:
    """Call the Claude API and return the drafted commit message text."""
    client = client_factory()
    response = client.messages.create(
        model=config.model,
        max_tokens=1024,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": build_prompt(diff)}],
    )
    return "".join(block.text for block in response.content if block.type == "text")
