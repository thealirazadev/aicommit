"""Tests for git subprocess wrappers: repo detection and diff reading."""

import pytest

from aicommit import git
from aicommit.errors import NoStagedChangesError, NotAGitRepoError


def test_is_inside_git_repo_true(temp_git_repo) -> None:
    assert git.is_inside_git_repo() is True


def test_is_inside_git_repo_false(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    assert git.is_inside_git_repo() is False


def test_read_staged_diff_returns_diff_text(temp_git_repo) -> None:
    diff = git.read_staged_diff()
    assert "example.txt" in diff


def test_read_staged_diff_empty_when_nothing_staged(empty_git_repo) -> None:
    diff = git.read_staged_diff()
    assert diff.strip() == ""


def test_require_staged_diff_returns_diff_text(temp_git_repo) -> None:
    diff = git.require_staged_diff()
    assert "example.txt" in diff


def test_require_staged_diff_raises_when_nothing_staged(empty_git_repo) -> None:
    with pytest.raises(NoStagedChangesError):
        git.require_staged_diff()


def test_require_staged_diff_raises_outside_git_repo(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    with pytest.raises(NotAGitRepoError):
        git.require_staged_diff()
