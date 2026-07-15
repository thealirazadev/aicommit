"""Tests for git subprocess wrappers: repo detection and diff reading."""

import subprocess

import pytest

from aicommit import git
from aicommit.errors import GitCommitError, NoStagedChangesError, NotAGitRepoError


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


def test_create_commit_writes_exact_message(temp_git_repo) -> None:
    message = "feat: add example\n\nBody line one.\nBody line two.\n"
    git.create_commit(message)
    result = subprocess.run(
        ["git", "log", "-1", "--pretty=%B"],
        cwd=temp_git_repo,
        capture_output=True,
        text=True,
        check=True,
    )
    # git normalizes the trailing newline on commit; compare content, not that.
    assert result.stdout.rstrip("\n") == message.rstrip("\n")


def test_create_commit_returns_short_sha(temp_git_repo) -> None:
    sha = git.create_commit("feat: add example\n")
    assert sha
    result = subprocess.run(
        ["git", "rev-parse", "--short", "HEAD"],
        cwd=temp_git_repo,
        capture_output=True,
        text=True,
        check=True,
    )
    assert sha == result.stdout.strip()


def test_create_commit_raises_on_failure(temp_git_repo) -> None:
    git.create_commit("feat: add example\n")
    with pytest.raises(GitCommitError):
        git.create_commit("feat: add example again\n")
