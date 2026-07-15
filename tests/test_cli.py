"""End-to-end CLI tests via click's CliRunner."""

from click.testing import CliRunner

from aicommit.cli import main


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
