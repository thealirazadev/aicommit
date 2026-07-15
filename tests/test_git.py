"""Tests for git subprocess wrappers: repo detection and diff reading."""

from aicommit import git


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
