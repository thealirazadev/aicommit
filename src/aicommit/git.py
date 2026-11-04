"""Subprocess wrappers around the git executable."""

from __future__ import annotations

import os
import subprocess
import tempfile

from aicommit.errors import GitCommitError, NoStagedChangesError, NotAGitRepoError


def _run_git(args: list[str]) -> subprocess.CompletedProcess[str]:
    """Run a git subcommand with an explicit argument list and capture output.

    Output is decoded as UTF-8 with invalid bytes replaced, so a diff that
    touches non-UTF-8 files (or a non-UTF-8 locale) cannot crash the run.
    """
    return subprocess.run(
        ["git", *args],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )


def _raise_on_failure(result: subprocess.CompletedProcess[str]) -> None:
    """Raise GitCommitError with git's first stderr line if git exited non-zero."""
    if result.returncode != 0:
        lines = (result.stderr or result.stdout).strip().splitlines()
        raise GitCommitError(lines[0] if lines else "unknown error")


def is_inside_git_repo() -> bool:
    """Return True if the current directory is inside a git working tree."""
    result = _run_git(["rev-parse", "--is-inside-work-tree"])
    return result.returncode == 0 and result.stdout.strip() == "true"


def read_staged_diff() -> str:
    """Return the staged diff produced by `git diff --cached`."""
    result = _run_git(["diff", "--cached"])
    _raise_on_failure(result)
    return result.stdout


def read_staged_diffstat() -> str:
    """Return the diffstat summary produced by `git diff --cached --stat`."""
    result = _run_git(["diff", "--cached", "--stat"])
    _raise_on_failure(result)
    return result.stdout


def build_diff_payload(diff: str, max_diff_bytes: int) -> tuple[str, bool]:
    """Return the text to send to the model, and whether it was summarized.

    If `diff` fits within `max_diff_bytes`, it is returned unchanged. Above
    the cap, return the diffstat summary plus a byte-truncated diff instead.
    """
    encoded = diff.encode()
    if len(encoded) <= max_diff_bytes:
        return diff, False
    truncated = encoded[:max_diff_bytes].decode(errors="ignore")
    return f"{read_staged_diffstat()}\n{truncated}", True


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
        with os.fdopen(fd, "w", encoding="utf-8") as tmp_file:
            tmp_file.write(message)
        result = _run_git(["commit", "-F", tmp_path])
        _raise_on_failure(result)
    finally:
        os.unlink(tmp_path)
    return _run_git(["rev-parse", "--short", "HEAD"]).stdout.strip()
