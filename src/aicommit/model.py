"""Anthropic client wrapper: draft a commit message from a diff."""

from __future__ import annotations

import os
from collections.abc import Callable

import anthropic

from aicommit.config import Config
from aicommit.errors import ApiError, AuthError
from aicommit.prompt import SYSTEM_PROMPT, build_prompt

ClientFactory = Callable[[], anthropic.Anthropic]


def draft_message(
    diff: str,
    config: Config,
    *,
    client_factory: ClientFactory = anthropic.Anthropic,
) -> str:
    """Call the Claude API and return the drafted commit message text.

    Maps SDK errors to the app's typed errors: auth failures -> `AuthError`
    (exit 5), network/rate-limit/server failures -> `ApiError` (exit 6).
    """
    if client_factory is anthropic.Anthropic and not os.environ.get(
        "ANTHROPIC_API_KEY"
    ):
        raise AuthError(detail="ANTHROPIC_API_KEY is not set")
    client = client_factory()
    try:
        response = client.messages.create(
            model=config.model,
            max_tokens=1024,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": build_prompt(diff)}],
        )
    except (anthropic.AuthenticationError, anthropic.PermissionDeniedError) as error:
        raise AuthError(detail=str(error)) from error
    except anthropic.RateLimitError as error:
        raise ApiError(
            "Rate limited by the Anthropic API. Wait a moment and retry.",
            detail=str(error),
        ) from error
    except (anthropic.APIConnectionError, anthropic.APITimeoutError) as error:
        raise ApiError(
            "Could not reach the Anthropic API. Check your connection and retry.",
            detail=str(error),
        ) from error
    except anthropic.APIStatusError as error:
        if error.status_code >= 500:
            raise ApiError(
                "Anthropic API error (server). Try again shortly.",
                detail=str(error),
            ) from error
        raise
    return "".join(block.text for block in response.content if block.type == "text")
