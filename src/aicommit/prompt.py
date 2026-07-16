"""Build the system + user prompt sent to the Claude API."""

from __future__ import annotations

SYSTEM_PROMPT = """You are a git commit message assistant. Given a staged git diff, \
draft a single Conventional Commit message.

Rules:
- The first line is the subject: `type(scope): summary`, where type is one of \
feat, fix, docs, style, refactor, perf, test, build, ci, chore, revert. Scope is \
optional and in parentheses.
- Keep the subject under about 72 characters, imperative mood, no trailing period.
- Add a body only if it adds real information beyond the subject; separate it from \
the subject with one blank line.
- Never include authorship attribution, such as "Generated with" or \
"Co-Authored-By", or any mention of an AI assistant.
- Output only the commit message text, nothing else."""


def build_prompt(
    diff: str, *, commit_type: str | None = None, scope: str | None = None
) -> str:
    """Return the user-turn prompt embedding the staged diff.

    `commit_type`/`scope`, when given, are passed as hard constraints on the
    subject line.
    """
    constraints = []
    if commit_type:
        constraints.append(f'Use "{commit_type}" as the commit type.')
    if scope:
        constraints.append(f'Use "{scope}" as the scope, in parentheses.')
    constraint_text = ("\n" + "\n".join(constraints)) if constraints else ""
    return (
        f"Here is the staged git diff:\n\n{diff}\n\n"
        f"Draft the commit message.{constraint_text}"
    )
