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
- Python 3.10 is supported through the `tomli` backport.
- Choice letters in the accept, edit, regenerate, and quit prompt are no longer swallowed as
  rich markup.
- Upgraded black and certifi to resolve security advisories.

## 0.1.0

Drafts a Conventional Commit message from the staged diff with the Claude API, with accept,
edit, regenerate, and quit before anything is committed, plus `--dry-run` and `--yes` modes.
