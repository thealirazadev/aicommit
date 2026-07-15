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


class AuthError(AicommitError):
    """Raised when the Anthropic API key is missing or invalid."""

    def __init__(self, detail: str | None = None) -> None:
        super().__init__(
            "Anthropic API key missing or invalid. Set ANTHROPIC_API_KEY.",
            exit_code=5,
            detail=detail,
        )


class ApiError(AicommitError):
    """Raised for network, rate-limit, or server errors from the Anthropic API."""

    def __init__(self, message: str, detail: str | None = None) -> None:
        super().__init__(message, exit_code=6, detail=detail)


class GitCommitError(AicommitError):
    """Raised when `git commit` exits non-zero."""

    def __init__(self, git_stderr_first_line: str) -> None:
        super().__init__(
            f"git commit failed: {git_stderr_first_line}",
            exit_code=7,
        )
