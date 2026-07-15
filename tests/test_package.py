"""Smoke tests for the package scaffold and console entry point."""

from click.testing import CliRunner

import aicommit
from aicommit.cli import main


def test_version_is_defined() -> None:
    assert isinstance(aicommit.__version__, str)
    assert aicommit.__version__


def test_cli_runs(temp_git_repo, monkeypatch) -> None:
    monkeypatch.setattr("aicommit.cli.draft_message", lambda diff, config: "feat: x")
    runner = CliRunner()
    result = runner.invoke(main, [])
    assert result.exit_code == 0


def test_version_flag() -> None:
    runner = CliRunner()
    result = runner.invoke(main, ["--version"])
    assert result.exit_code == 0
    assert result.output.strip() == f"aicommit {aicommit.__version__}"


def test_help_flag() -> None:
    runner = CliRunner()
    result = runner.invoke(main, ["--help"])
    assert result.exit_code == 0
    assert "Usage" in result.output
