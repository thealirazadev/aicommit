"""Subprocess wrappers around the git executable."""

from __future__ import annotations

import subprocess


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
