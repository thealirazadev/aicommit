"""Tests for `draft_message`, with the Anthropic API fully mocked."""

import anthropic
import httpx
import pytest

from aicommit.config import Config
from aicommit.errors import ApiError, AuthError
from aicommit.model import draft_message


def _response(status_code: int) -> httpx.Response:
    request = httpx.Request("POST", "https://api.anthropic.com/v1/messages")
    return httpx.Response(status_code, request=request)


class _RaisingClient:
    """Fake client whose `messages.create` raises a given exception."""

    def __init__(self, error: Exception) -> None:
        self._error = error
        self.messages = self

    def create(self, **kwargs):
        raise self._error


def test_draft_message_returns_text(fake_anthropic_client) -> None:
    config = Config(model="claude-opus-4-8")
    result = draft_message(
        "diff --git a/f b/f\n",
        config,
        client_factory=lambda: fake_anthropic_client,
    )
    assert result == "feat: add example feature"


def test_draft_message_sends_configured_model(fake_anthropic_client) -> None:
    config = Config(model="claude-sonnet-5")
    draft_message(
        "diff --git a/f b/f\n",
        config,
        client_factory=lambda: fake_anthropic_client,
    )
    assert fake_anthropic_client.calls[0]["model"] == "claude-sonnet-5"


def test_draft_message_includes_diff_in_request(fake_anthropic_client) -> None:
    config = Config()
    draft_message(
        "diff --git a/f b/f\n+print('hi')\n",
        config,
        client_factory=lambda: fake_anthropic_client,
    )
    sent = fake_anthropic_client.calls[0]["messages"][0]["content"]
    assert "print('hi')" in sent


def test_authentication_error_maps_to_auth_error() -> None:
    error = anthropic.AuthenticationError("bad key", response=_response(401), body=None)
    client = _RaisingClient(error)
    with pytest.raises(AuthError):
        draft_message("diff", Config(), client_factory=lambda: client)


def test_permission_denied_error_maps_to_auth_error() -> None:
    error = anthropic.PermissionDeniedError(
        "forbidden", response=_response(403), body=None
    )
    client = _RaisingClient(error)
    with pytest.raises(AuthError):
        draft_message("diff", Config(), client_factory=lambda: client)


def test_rate_limit_error_maps_to_api_error() -> None:
    error = anthropic.RateLimitError(
        "too many requests", response=_response(429), body=None
    )
    client = _RaisingClient(error)
    with pytest.raises(ApiError):
        draft_message("diff", Config(), client_factory=lambda: client)


def test_connection_error_maps_to_api_error() -> None:
    request = httpx.Request("POST", "https://api.anthropic.com/v1/messages")
    error = anthropic.APIConnectionError(request=request)
    client = _RaisingClient(error)
    with pytest.raises(ApiError):
        draft_message("diff", Config(), client_factory=lambda: client)


def test_timeout_error_maps_to_api_error() -> None:
    request = httpx.Request("POST", "https://api.anthropic.com/v1/messages")
    error = anthropic.APITimeoutError(request=request)
    client = _RaisingClient(error)
    with pytest.raises(ApiError):
        draft_message("diff", Config(), client_factory=lambda: client)


def test_server_status_error_maps_to_api_error() -> None:
    error = anthropic.APIStatusError("server error", response=_response(503), body=None)
    client = _RaisingClient(error)
    with pytest.raises(ApiError):
        draft_message("diff", Config(), client_factory=lambda: client)


def test_client_status_error_is_not_swallowed() -> None:
    error = anthropic.APIStatusError("teapot", response=_response(418), body=None)
    client = _RaisingClient(error)
    with pytest.raises(anthropic.APIStatusError):
        draft_message("diff", Config(), client_factory=lambda: client)
