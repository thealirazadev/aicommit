"""Typed exception hierarchy carrying a user-facing message and exit code."""

from __future__ import annotations


class AicommitError(Exception):
    """Base error for all handled failures; caught once at the top level."""

    def __init__(self, message: str, exit_code: int, detail: str | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.exit_code = exit_code
        self.detail = detail


class NotAGitRepoError(AicommitError):
    """Raised when the current directory is not inside a git work tree."""

    def __init__(self) -> None:
        super().__init__(
            "Not a git repository. Run aicommit from inside a git repo.",
            exit_code=4,
        )


class NoStagedChangesError(AicommitError):
    """Raised when `git diff --cached` has no output."""

    def __init__(self) -> None:
        super().__init__(
            "No staged changes. Stage files with 'git add' first.",
            exit_code=3,
        )
