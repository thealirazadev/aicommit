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
