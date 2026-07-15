"""Subprocess wrappers around the git executable."""

from __future__ import annotations

import os
import subprocess
import tempfile

from aicommit.errors import GitCommitError, NoStagedChangesError, NotAGitRepoError


def _run_git(args: list[str]) -> subprocess.CompletedProcess[str]:
    """Run a git subcommand with an explicit argument list and capture output."""
    return subprocess.run(["git", *args], capture_output=True, text=True)


def is_inside_git_repo() -> bool:
    """Return True if the current directory is inside a git working tree."""
    result = _run_git(["rev-parse", "--is-inside-work-tree"])
    return result.returncode == 0 and result.stdout.strip() == "true"


def read_staged_diff() -> str:
    """Return the staged diff produced by `git diff --cached`."""
    result = _run_git(["diff", "--cached"])
    return result.stdout


def require_staged_diff() -> str:
    """Return the staged diff, raising if not in a repo or nothing is staged."""
    if not is_inside_git_repo():
        raise NotAGitRepoError()
    diff = read_staged_diff()
    if not diff.strip():
        raise NoStagedChangesError()
    return diff


def create_commit(message: str) -> str:
    """Create a commit via `git commit -F <tmpfile>`; return the short SHA."""
    fd, tmp_path = tempfile.mkstemp(suffix=".txt")
    try:
        with os.fdopen(fd, "w") as tmp_file:
            tmp_file.write(message)
        result = _run_git(["commit", "-F", tmp_path])
        if result.returncode != 0:
            lines = (result.stderr or result.stdout).strip().splitlines()
            raise GitCommitError(lines[0] if lines else "unknown error")
    finally:
        os.unlink(tmp_path)
    return _run_git(["rev-parse", "--short", "HEAD"]).stdout.strip()
