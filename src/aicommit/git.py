"""Subprocess wrappers around the git executable."""

from __future__ import annotations

import os
import subprocess
import tempfile
from pathlib import Path

from aicommit.errors import GitCommitError, NoStagedChangesError, NotAGitRepoError


def _run_git(args: list[str]) -> subprocess.CompletedProcess[str]:
    """Run a git subcommand with an explicit argument list and capture output."""
    return subprocess.run(["git", *args], capture_output=True, text=True)


def is_inside_git_repo() -> bool:
    """Return True if the current directory is inside a git working tree."""
    result = _run_git(["rev-parse", "--is-inside-work-tree"])
    return result.returncode == 0 and result.stdout.strip() == "true"


def repo_root() -> Path | None:
    """Return the top-level directory of the current work tree, or None."""
    result = _run_git(["rev-parse", "--show-toplevel"])
    top = result.stdout.strip()
    if result.returncode != 0 or not top:
        return None
    return Path(top)


# Plain diff text regardless of the user's git config: `color.ui = always` would put
# ANSI codes in the prompt, and `diff.external` would run another program instead.
_PLAIN_DIFF_FLAGS = ["--no-color", "--no-ext-diff"]


def read_staged_diff() -> str:
    """Return the staged diff produced by `git diff --cached`."""
    result = _run_git(["diff", "--cached", *_PLAIN_DIFF_FLAGS])
    return result.stdout


def read_staged_diffstat() -> str:
    """Return the diffstat summary produced by `git diff --cached --stat`."""
    result = _run_git(["diff", "--cached", "--stat", *_PLAIN_DIFF_FLAGS])
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
        if result.returncode != 0:
            lines = (result.stderr or result.stdout).strip().splitlines()
            raise GitCommitError(lines[0] if lines else "unknown error")
    finally:
        os.unlink(tmp_path)
    return _run_git(["rev-parse", "--short", "HEAD"]).stdout.strip()
