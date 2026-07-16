"""Tests for presenting the draft and parsing the accept/edit/regenerate/quit choice."""

import io

from rich.console import Console

from aicommit.message import edit_message, present_message, prompt_choice


def _console() -> tuple[Console, io.StringIO]:
    buffer = io.StringIO()
    console = Console(file=buffer, force_terminal=False, width=80)
    return console, buffer


def test_present_message_shows_text() -> None:
    console, buffer = _console()
    present_message(console, "feat: add example\n\nBody text.")
    output = buffer.getvalue()
    assert "Proposed commit message" in output
    assert "feat: add example" in output
    assert "Body text." in output


def test_prompt_choice_blank_defaults_to_accept() -> None:
    console, _ = _console()
    choice = prompt_choice(console, stream=io.StringIO("\n"))
    assert choice == "a"


def test_prompt_choice_accepts_letter_and_word() -> None:
    console, _ = _console()
    assert prompt_choice(console, stream=io.StringIO("a\n")) == "a"
    console, _ = _console()
    assert prompt_choice(console, stream=io.StringIO("accept\n")) == "a"


def test_prompt_choice_quit_letter_and_word() -> None:
    console, _ = _console()
    assert prompt_choice(console, stream=io.StringIO("q\n")) == "q"
    console, _ = _console()
    assert prompt_choice(console, stream=io.StringIO("quit\n")) == "q"


def test_prompt_choice_case_insensitive() -> None:
    console, _ = _console()
    assert prompt_choice(console, stream=io.StringIO("QUIT\n")) == "q"


def test_prompt_choice_reprompts_on_invalid() -> None:
    console, buffer = _console()
    choice = prompt_choice(console, stream=io.StringIO("nope\na\n"))
    assert choice == "a"
    assert "Please enter" in buffer.getvalue()


def test_prompt_choice_edit_letter_and_word() -> None:
    console, _ = _console()
    assert prompt_choice(console, stream=io.StringIO("e\n")) == "e"
    console, _ = _console()
    assert prompt_choice(console, stream=io.StringIO("edit\n")) == "e"


def test_prompt_choice_regenerate_letter_and_word() -> None:
    console, _ = _console()
    assert prompt_choice(console, stream=io.StringIO("r\n")) == "r"
    console, _ = _console()
    assert prompt_choice(console, stream=io.StringIO("regenerate\n")) == "r"


def test_edit_message_returns_edited_text(monkeypatch) -> None:
    monkeypatch.setattr("aicommit.message.click.edit", lambda text: "fix: edited\n")
    assert edit_message("feat: original") == "fix: edited"


def test_edit_message_falls_back_when_editor_reports_no_change(monkeypatch) -> None:
    monkeypatch.setattr("aicommit.message.click.edit", lambda text: None)
    assert edit_message("feat: original") == "feat: original"
