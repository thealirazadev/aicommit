"""Tests for `draft_message`, with the Anthropic API fully mocked."""

from aicommit.config import Config
from aicommit.model import draft_message


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
