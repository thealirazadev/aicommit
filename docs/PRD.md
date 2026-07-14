# PRD — aicommit

## What we're building

A small, fast command-line tool that removes the friction of writing commit messages. It reads the staged git diff, sends it to the Anthropic Claude API, and drafts a Conventional Commit message. The developer stays in control: nothing is committed until they accept the draft, and they can edit it or ask for a fresh draft first.

The tool does one thing well: turn "what I just staged" into a good commit message, then commit it. It is a terminal utility, invoked as `aicommit` in a repository with staged changes.

## Target user

Developers who use git from the terminal and want higher-quality, consistent commit messages without stopping to compose them by hand. They already stage changes deliberately (`git add`, `git add -p`) and want a Conventional Commits-style message that matches the diff. They are comfortable with an API key in their environment and expect the tool to be scriptable (flags, exit codes) as well as interactive.

## Core features (prioritized)

### P0 — must exist for the tool to be useful

1. **Read the staged diff.** Run `git diff --cached` and capture the staged changes. If there are no staged changes, or the current directory is not a git repository, stop with a clear message.
2. **Draft a Conventional Commit message.** Send the diff to the Claude API and receive a `type(scope): summary` subject plus an optional body. The message must never contain authorship attribution (no "Generated with", no "Co-Authored-By").
3. **Present the draft and let the user choose.** Show the message, then prompt: accept, edit, regenerate, or quit. Accept commits it; quit exits without committing.
4. **Create the commit.** On accept, run git to create the commit with the exact drafted (or edited) message.

### P1 — makes it pleasant and controllable

5. **Edit before committing.** Open the draft in `$EDITOR`, then re-present it.
6. **Regenerate.** Ask the model for a different draft without re-running the whole command.
7. **Type/scope overrides.** `--type` and `--scope` constrain the generated message.
8. **Non-interactive modes.** `--dry-run` (print only) and `--yes` (accept first draft) for scripting.
9. **Clear, categorized errors.** Distinct, friendly messages and exit codes for: no staged changes, not a git repo, missing/invalid API key, network/rate-limit error, oversized diff.

### P2 — polish

10. **Output controls.** `--quiet`, `--verbose` (structured logs), `NO_COLOR` / `--no-color`, spinner during the API call.
11. **Configuration file.** Optional config for the default model, type, and scope, layered under environment variables and CLI flags.
12. **Model override.** `--model` and `AICOMMIT_MODEL`.

## Non-goals

- Not a full git wrapper. It does not stage, push, amend, rebase, or manage branches. Staging is the user's job.
- No commit history rewriting, no message linting of existing commits, no changelog generation.
- No hosting of or proxying to any model other than the Anthropic Claude API. No local models, no OpenAI, no fallback providers.
- No persistent server, daemon, database, or telemetry. State is limited to an optional local config file.
- No editor/IDE plugins, no git hook installation. (A git hook is a possible future backlog item, not part of this project.)
- Does not send secrets or large binary blobs to the API (see `docs/rules.md` — Security).

## Success criteria per core feature

1. **Read the staged diff** — In a repo with staged changes, the tool captures the full `git diff --cached` output. With nothing staged it exits with code 3 and the message "No staged changes. Stage files with `git add` first." Outside a git repo it exits with code 4 and says so.
2. **Draft a message** — Given a representative staged diff, the tool returns a subject line matching `^(feat|fix|docs|style|refactor|perf|test|build|ci|chore|revert)(\(.+\))?!?: .+`, with the subject under about 72 characters, and no attribution lines anywhere in the message.
3. **Present and choose** — The draft is displayed; the prompt accepts a/e/r/q (and their word forms). An invalid choice re-prompts rather than crashing. Quit exits without creating a commit.
4. **Create the commit** — On accept, `git log -1 --pretty=%B` equals the accepted message exactly (subject and body preserved, including multi-line bodies). Exit code is 0.
5. **Edit** — Choosing edit opens `$EDITOR` seeded with the draft; saving returns to the presentation with the edited text; an empty edited message is rejected with a message, not a commit.
6. **Regenerate** — Choosing regenerate produces a new draft (a second API call) and returns to the presentation without leaving the command.
7. **Overrides** — `--type fix` forces a `fix` subject; `--scope api` forces `(api)` in the subject.
8. **Non-interactive** — `--dry-run` prints the draft and exits 0 without committing; `--yes` commits the first draft with no prompt.
9. **Errors** — Each failure class produces its documented exit code (see `docs/design.md`) and a one-line friendly message; `--verbose` adds detail; a raw traceback is never printed by default.
10. **Output controls** — With `NO_COLOR` set or `--no-color`, output contains no ANSI color codes; `--quiet` suppresses non-essential output; the spinner appears only while waiting on the API and only when attached to a TTY.
11. **Config file** — A config value for `model` is used when neither `--model` nor `AICOMMIT_MODEL` is set; CLI flag beats env var beats config file beats built-in default.
12. **Model override** — `--model X` and `AICOMMIT_MODEL=X` both cause the request to target model `X`.
