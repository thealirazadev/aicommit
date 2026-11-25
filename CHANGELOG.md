# Changelog

## Unreleased

### Added
- Optional config file for settings such as the model and the diff size limit.
- Oversized staged diffs are cut to a size limit before they are sent to the model.
- `--quiet` and `--verbose` flags with structured logging, and `NO_COLOR` and `--no-color`
  support.
- `--type` and `--scope` constraints for the drafted message.
- CI runs lint, the format check, and tests on every push, with a 90 percent coverage gate.

### Fixed
- A `.env` file at the repository root is now actually loaded, as the README described (only
  `ANTHROPIC_API_KEY` and `AICOMMIT_MODEL`, never overriding the environment).
- A code fence wrapped around the model's output is removed instead of becoming the commit
  subject, and an empty draft is reported instead of committed.
- Brackets in a drafted message are shown verbatim in the preview and in `--dry-run` output.
- The staged diff is read without color or external diff tools, whatever the git config says.
- A config file value of the wrong type is a friendly error instead of an unexpected crash.
- Python 3.10 is supported through the `tomli` backport.
- Choice letters in the accept, edit, regenerate, and quit prompt are no longer swallowed as
  rich markup.
- Upgraded black and certifi to resolve security advisories.

## 0.1.0

Drafts a Conventional Commit message from the staged diff with the Claude API, with accept,
edit, regenerate, and quit before anything is committed, plus `--dry-run` and `--yes` modes.
