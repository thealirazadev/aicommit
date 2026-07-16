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


def test_build_prompt_honors_type_constraint() -> None:
    prompt = build_prompt("diff --git a/f b/f\n", commit_type="fix")
    assert '"fix"' in prompt


def test_build_prompt_honors_scope_constraint() -> None:
    prompt = build_prompt("diff --git a/f b/f\n", scope="api")
    assert '"api"' in prompt


def test_build_prompt_without_constraints_omits_them() -> None:
    prompt = build_prompt("diff --git a/f b/f\n")
    assert "commit type" not in prompt
    assert "scope" not in prompt
