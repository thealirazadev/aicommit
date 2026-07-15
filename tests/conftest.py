"""Shared pytest fixtures: temp git repos and a fake Anthropic client."""

from __future__ import annotations

import subprocess

import pytest


def _git(*args: str, cwd) -> None:
    subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True, text=True)


@pytest.fixture
def temp_git_repo(tmp_path, monkeypatch):
    """Create a throwaway git repo with one staged file; chdir into it."""
    repo = tmp_path / "repo"
    repo.mkdir()
    _git("init", cwd=repo)
    _git("config", "user.email", "test@example.com", cwd=repo)
    _git("config", "user.name", "Test User", cwd=repo)
    (repo / "example.txt").write_text("hello\n")
    _git("add", "example.txt", cwd=repo)
    monkeypatch.chdir(repo)
    return repo


@pytest.fixture
def empty_git_repo(tmp_path, monkeypatch):
    """Create a throwaway git repo with no staged changes; chdir into it."""
    repo = tmp_path / "empty-repo"
    repo.mkdir()
    _git("init", cwd=repo)
    _git("config", "user.email", "test@example.com", cwd=repo)
    _git("config", "user.name", "Test User", cwd=repo)
    monkeypatch.chdir(repo)
    return repo


class _FakeTextBlock:
    def __init__(self, text: str) -> None:
        self.type = "text"
        self.text = text


class _FakeResponse:
    def __init__(self, text: str) -> None:
        self.content = [_FakeTextBlock(text)]


class FakeAnthropicClient:
    """Stand-in for `anthropic.Anthropic`; records calls, never touches the network."""

    def __init__(self, text: str = "feat: add example feature") -> None:
        self.calls: list[dict] = []
        self._text = text
        self.messages = self

    def create(self, **kwargs):
        self.calls.append(kwargs)
        return _FakeResponse(self._text)


@pytest.fixture
def fake_anthropic_client():
    return FakeAnthropicClient()
