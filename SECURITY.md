# Security policy

## Supported versions

Only the latest release (0.1.0, the version in `pyproject.toml`) on `main` receives security
fixes.

## Reporting a vulnerability

Please do not open a public issue. Use GitHub's private vulnerability reporting
(Security tab, "Report a vulnerability") or email thealirazadev@gmail.com with the
steps to reproduce. You should get a reply within 72 hours.

## How aicommit protects your key and your code

- The Anthropic API key is read only from the `ANTHROPIC_API_KEY` environment variable. The
  tool exits with a clear error when it is missing or invalid.
- The staged diff is sent to the Anthropic API to draft the message, so that content leaves
  your machine. Do not run it on changes you are not allowed to send to that service.
- Oversized diffs are cut to `max_diff_bytes` (100,000 bytes by default) before they are sent,
  which bounds how much of a change is transmitted in one request.
- Nothing is committed until you accept a draft, or pass `--yes` to accept the first one.
  `--dry-run` prints the draft and never creates a commit.
- Logging is structured and quiet by default; `--verbose` adds debug detail on stderr.
