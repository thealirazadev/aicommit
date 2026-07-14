"""Smoke tests for the package scaffold and console entry point."""

from click.testing import CliRunner

import aicommit
from aicommit.cli import main


def test_version_is_defined() -> None:
    assert isinstance(aicommit.__version__, str)
    assert aicommit.__version__


def test_cli_runs() -> None:
    runner = CliRunner()
    result = runner.invoke(main, [])
    assert result.exit_code == 0
