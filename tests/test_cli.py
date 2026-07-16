"""End-to-end CLI tests via click's CliRunner. The API is always mocked."""

import re
import subprocess

from click.testing import CliRunner

from aicommit import cli
from aicommit.cli import main
from aicommit.config import Config
from aicommit.errors import ApiError, AuthError, GitCommitError

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


def test_dry_run_prints_without_committing(temp_git_repo, monkeypatch) -> None:
    monkeypatch.setattr(
        "aicommit.cli.draft_message",
        lambda diff, config: "fix(cli): handle empty diff",
    )
    runner = CliRunner()
    result = runner.invoke(main, ["--dry-run"])
    assert result.exit_code == 0
    assert "fix(cli): handle empty diff" in result.output
    head = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=temp_git_repo,
        capture_output=True,
        text=True,
    )
    assert head.returncode != 0


def test_yes_commits_first_draft_without_prompting(temp_git_repo, monkeypatch) -> None:
    monkeypatch.setattr(
        "aicommit.cli.draft_message",
        lambda diff, config: "fix(cli): handle empty diff",
    )
    runner = CliRunner()
    result = runner.invoke(main, ["--yes"])
    assert result.exit_code == 0
    assert "Committed" in result.output
    subject = _commit_log(temp_git_repo).strip()
    assert SUBJECT_RE.match(subject)


def test_edit_then_accept_commits_edited_message(temp_git_repo, monkeypatch) -> None:
    monkeypatch.setattr(
        "aicommit.cli.draft_message",
        lambda diff, config: "fix(cli): handle empty diff",
    )
    monkeypatch.setattr(
        "aicommit.message.click.edit", lambda text: "feat(cli): edited message"
    )
    runner = CliRunner()
    result = runner.invoke(main, [], input="e\na\n")
    assert result.exit_code == 0
    assert "Committed" in result.output
    subject = _commit_log(temp_git_repo).strip()
    assert subject == "feat(cli): edited message"


def test_edit_empty_save_exits_1_no_commit(temp_git_repo, monkeypatch) -> None:
    monkeypatch.setattr(
        "aicommit.cli.draft_message",
        lambda diff, config: "fix(cli): handle empty diff",
    )
    monkeypatch.setattr("aicommit.message.click.edit", lambda text: "   \n")
    runner = CliRunner()
    result = runner.invoke(main, [], input="e\n")
    assert result.exit_code == 1
    assert "Commit message is empty; nothing committed." in result.output
    head = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=temp_git_repo,
        capture_output=True,
        text=True,
    )
    assert head.returncode != 0


def test_regenerate_makes_second_api_call(temp_git_repo, monkeypatch) -> None:
    drafts = iter(["fix(cli): first draft", "feat(cli): second draft"])
    calls: list[str] = []

    def _draft(diff, config):
        calls.append(diff)
        return next(drafts)

    monkeypatch.setattr("aicommit.cli.draft_message", _draft)
    runner = CliRunner()
    result = runner.invoke(main, [], input="r\na\n")
    assert result.exit_code == 0
    assert len(calls) == 2
    subject = _commit_log(temp_git_repo).strip()
    assert subject == "feat(cli): second draft"


def test_edit_flag_opens_editor_before_prompt(temp_git_repo, monkeypatch) -> None:
    monkeypatch.setattr(
        "aicommit.cli.draft_message",
        lambda diff, config: "fix(cli): handle empty diff",
    )
    monkeypatch.setattr(
        "aicommit.message.click.edit", lambda text: "feat(cli): pre-edited"
    )
    runner = CliRunner()
    result = runner.invoke(main, ["--edit"], input="a\n")
    assert result.exit_code == 0
    subject = _commit_log(temp_git_repo).strip()
    assert subject == "feat(cli): pre-edited"


def test_edit_flag_with_yes_commits_edited_message_without_prompt(
    temp_git_repo, monkeypatch
) -> None:
    monkeypatch.setattr(
        "aicommit.cli.draft_message",
        lambda diff, config: "fix(cli): handle empty diff",
    )
    monkeypatch.setattr(
        "aicommit.message.click.edit", lambda text: "feat(cli): pre-edited"
    )
    runner = CliRunner()
    result = runner.invoke(main, ["--edit", "--yes"])
    assert result.exit_code == 0
    subject = _commit_log(temp_git_repo).strip()
    assert subject == "feat(cli): pre-edited"


class _FakeStatus:
    """Records the spinner text and acts as a no-op context manager."""

    def __init__(self, texts: list[str]) -> None:
        self._texts = texts

    def __call__(self, text: str) -> "_FakeStatus":
        self._texts.append(text)
        return self

    def __enter__(self) -> "_FakeStatus":
        return self

    def __exit__(self, *exc_info: object) -> None:
        return None


def test_spinner_shown_on_tty_for_draft_and_regenerate(
    temp_git_repo, monkeypatch
) -> None:
    monkeypatch.setattr(
        "aicommit.cli.draft_message",
        lambda diff, config: "fix(cli): handle empty diff",
    )
    monkeypatch.setattr(cli._stdout, "_force_terminal", True)
    texts: list[str] = []
    monkeypatch.setattr(cli._stdout, "status", _FakeStatus(texts))
    runner = CliRunner()
    result = runner.invoke(main, [], input="r\na\n")
    assert result.exit_code == 0
    assert texts == ["Drafting commit message...", "Regenerating..."]


def test_no_spinner_off_a_tty(temp_git_repo, monkeypatch) -> None:
    monkeypatch.setattr(
        "aicommit.cli.draft_message",
        lambda diff, config: "fix(cli): handle empty diff",
    )
    monkeypatch.setattr(cli._stdout, "_force_terminal", False)
    texts: list[str] = []
    monkeypatch.setattr(cli._stdout, "status", _FakeStatus(texts))
    runner = CliRunner()
    result = runner.invoke(main, [], input="a\n")
    assert result.exit_code == 0
    assert texts == []


def test_quiet_suppresses_spinner(temp_git_repo, monkeypatch) -> None:
    monkeypatch.setattr(
        "aicommit.cli.draft_message",
        lambda diff, config: "fix(cli): handle empty diff",
    )
    monkeypatch.setattr(cli._stdout, "_force_terminal", True)
    texts: list[str] = []
    monkeypatch.setattr(cli._stdout, "status", _FakeStatus(texts))
    runner = CliRunner()
    result = runner.invoke(main, ["--quiet"], input="a\n")
    assert result.exit_code == 0
    assert texts == []


def test_verbose_emits_structured_logs_without_key_or_diff(
    temp_git_repo, monkeypatch
) -> None:
    monkeypatch.setattr(
        "aicommit.cli.draft_message",
        lambda diff, config: "fix(cli): handle empty diff",
    )
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-super-secret-value")
    runner = CliRunner()
    result = runner.invoke(main, ["--verbose", "--yes"])
    assert result.exit_code == 0
    assert "event=draft" in result.output
    assert "model=" in result.output
    assert "sk-super-secret-value" not in result.output


def test_color_present_by_default_on_a_forced_terminal(
    temp_git_repo, monkeypatch
) -> None:
    monkeypatch.setattr(
        "aicommit.cli.draft_message",
        lambda diff, config: "fix(cli): handle empty diff",
    )
    monkeypatch.setattr(cli._stdout, "_force_terminal", True)
    monkeypatch.delenv("NO_COLOR", raising=False)
    runner = CliRunner()
    result = runner.invoke(main, ["--yes"])
    assert "\x1b[" in result.output


def test_no_color_flag_strips_ansi(temp_git_repo, monkeypatch) -> None:
    monkeypatch.setattr(
        "aicommit.cli.draft_message",
        lambda diff, config: "fix(cli): handle empty diff",
    )
    monkeypatch.setattr(cli._stdout, "_force_terminal", True)
    monkeypatch.delenv("NO_COLOR", raising=False)
    runner = CliRunner()
    result = runner.invoke(main, ["--yes", "--no-color"])
    assert "\x1b[" not in result.output


def test_no_color_env_var_strips_ansi(temp_git_repo, monkeypatch) -> None:
    monkeypatch.setattr(
        "aicommit.cli.draft_message",
        lambda diff, config: "fix(cli): handle empty diff",
    )
    monkeypatch.setattr(cli._stdout, "_force_terminal", True)
    monkeypatch.setenv("NO_COLOR", "1")
    runner = CliRunner()
    result = runner.invoke(main, ["--yes"])
    assert "\x1b[" not in result.output


def test_oversized_diff_warns_and_still_drafts(temp_git_repo, monkeypatch) -> None:
    (temp_git_repo / "example.txt").write_text("x" * 500 + "\n")
    subprocess.run(["git", "add", "example.txt"], cwd=temp_git_repo, check=True)
    monkeypatch.setattr(
        "aicommit.cli.load_config", lambda **kwargs: Config(max_diff_bytes=50)
    )
    monkeypatch.setattr(
        "aicommit.cli.draft_message",
        lambda diff, config: "fix(cli): handle large diff",
    )
    runner = CliRunner()
    result = runner.invoke(main, ["--yes"])
    assert result.exit_code == 0
    assert "Warning:" in result.output
    assert "Committed" in result.output


def test_type_and_scope_flags_reach_config(temp_git_repo, monkeypatch) -> None:
    seen: dict = {}

    def _draft(diff, config):
        seen["commit_type"] = config.commit_type
        seen["scope"] = config.scope
        return "fix(api): handle empty diff"

    monkeypatch.setattr("aicommit.cli.draft_message", _draft)
    runner = CliRunner()
    result = runner.invoke(main, ["--type", "fix", "--scope", "api", "--yes"])
    assert result.exit_code == 0
    assert seen == {"commit_type": "fix", "scope": "api"}


def test_dry_run_and_yes_together_is_usage_error(temp_git_repo) -> None:
    runner = CliRunner()
    result = runner.invoke(main, ["--dry-run", "--yes"])
    assert result.exit_code == 2


def test_git_commit_failure_exits_7(temp_git_repo, monkeypatch) -> None:
    monkeypatch.setattr(
        "aicommit.cli.draft_message",
        lambda diff, config: "fix(cli): handle empty diff",
    )

    def _raise(message):
        raise GitCommitError("fatal: unable to write new index file")

    monkeypatch.setattr("aicommit.git.create_commit", _raise)
    runner = CliRunner()
    result = runner.invoke(main, [], input="a\n")
    assert result.exit_code == 7
    assert "fatal: unable to write new index file" in result.output


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
