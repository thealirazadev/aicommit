"""Tests for configuration resolution precedence."""

from aicommit.config import DEFAULT_MODEL, load_config


def test_default_model(monkeypatch) -> None:
    monkeypatch.delenv("AICOMMIT_MODEL", raising=False)
    config = load_config()
    assert config.model == DEFAULT_MODEL


def test_env_overrides_default(monkeypatch) -> None:
    monkeypatch.setenv("AICOMMIT_MODEL", "claude-sonnet-5")
    config = load_config()
    assert config.model == "claude-sonnet-5"


def test_flag_overrides_env(monkeypatch) -> None:
    monkeypatch.setenv("AICOMMIT_MODEL", "claude-sonnet-5")
    config = load_config(model="claude-opus-4-8")
    assert config.model == "claude-opus-4-8"
