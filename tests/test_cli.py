"""End-to-end CLI tests via click's CliRunner. The API is always mocked."""

import re
import subprocess

from click.testing import CliRunner

from aicommit.cli import main
from aicommit.errors import ApiError, AuthError

SUBJECT_RE = re.compile(
    r"^(feat|fix|docs|style|refactor|perf|test|build|ci|chore|revert)(\(.+\))?!?: .+"
)


def _commit_log(repo) -> str:
    result = subprocess.run(
        ["git", "log", "-1", "--pretty=%B"],
        cwd=repo,
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout


def test_no_staged_changes_exits_3(empty_git_repo) -> None:
    runner = CliRunner()
    result = runner.invoke(main, [])
    assert result.exit_code == 3
    assert "git add" in result.output


def test_outside_git_repo_exits_4(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    runner = CliRunner()
    result = runner.invoke(main, [])
    assert result.exit_code == 4


def test_accept_creates_commit(temp_git_repo, monkeypatch) -> None:
    monkeypatch.setattr(
        "aicommit.cli.draft_message",
        lambda diff, config: "fix(cli): handle empty diff",
    )
    runner = CliRunner()
    result = runner.invoke(main, [], input="a\n")
    assert result.exit_code == 0
    assert "Committed" in result.output
    subject = _commit_log(temp_git_repo).strip()
    assert SUBJECT_RE.match(subject)
    assert "Co-Authored-By" not in result.output
    assert "Generated with" not in result.output


def test_quit_creates_no_commit_exits_130(temp_git_repo, monkeypatch) -> None:
    monkeypatch.setattr(
        "aicommit.cli.draft_message",
        lambda diff, config: "fix(cli): handle empty diff",
    )
    runner = CliRunner()
    result = runner.invoke(main, [], input="q\n")
    assert result.exit_code == 130
    assert "Aborted" in result.output
    head = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=temp_git_repo,
        capture_output=True,
        text=True,
    )
    assert head.returncode != 0


def test_blank_input_defaults_to_accept(temp_git_repo, monkeypatch) -> None:
    monkeypatch.setattr(
        "aicommit.cli.draft_message",
        lambda diff, config: "fix(cli): handle empty diff",
    )
    runner = CliRunner()
    result = runner.invoke(main, [], input="\n")
    assert result.exit_code == 0
    assert "Committed" in result.output


def test_auth_error_exits_5(temp_git_repo, monkeypatch) -> None:
    def _raise(diff, config):
        raise AuthError()

    monkeypatch.setattr("aicommit.cli.draft_message", _raise)
    runner = CliRunner()
    result = runner.invoke(main, [])
    assert result.exit_code == 5
    assert "ANTHROPIC_API_KEY" in result.output


def test_api_error_exits_6(temp_git_repo, monkeypatch) -> None:
    def _raise(diff, config):
        raise ApiError(
            "Could not reach the Anthropic API. Check your connection and retry."
        )

    monkeypatch.setattr("aicommit.cli.draft_message", _raise)
    runner = CliRunner()
    result = runner.invoke(main, [])
    assert result.exit_code == 6


def test_unexpected_error_exits_1_without_traceback(temp_git_repo, monkeypatch) -> None:
    def _raise(diff, config):
        raise ValueError("boom")

    monkeypatch.setattr("aicommit.cli.draft_message", _raise)
    runner = CliRunner()
    result = runner.invoke(main, [])
    assert result.exit_code == 1
    assert "Traceback" not in result.output
    assert "boom" not in result.output
