"""Tests for prompt construction."""

from aicommit.prompt import SYSTEM_PROMPT, build_prompt


def test_build_prompt_includes_diff() -> None:
    diff = "diff --git a/foo.py b/foo.py\n+print('hi')\n"
    prompt = build_prompt(diff)
    assert diff in prompt


def test_system_prompt_forbids_attribution() -> None:
    lowered = SYSTEM_PROMPT.lower()
    assert "co-authored-by" in lowered
    assert "generated with" in lowered
    assert "never include" in lowered
