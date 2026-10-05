# Changelog

## Unreleased

### Changed

- Polish repository documentation and maintainer guidance.
- Add community health files, issue templates, pull request checks, support guidance, and citation metadata.
- Document the v0.1 architecture, safety boundaries, and v0.2 analysis boundary.
- Improve package metadata and local build-artifact handling.
- Harden interactive apply so a zero-item preview cannot be confirmed accidentally.
- Apply owner-only permissions to existing OAuth credential files before loading them where supported.
- Add a read-only Gmail metadata observer and deterministic mailbox analysis primitives.
- Add a JSON-producing `--analyze` CLI mode with explicit review-candidate criteria.
- Enrich review-candidate output with sender, subject, age, category, and explicit reasons for operator review.
- Deduplicate candidate reasons and add exact-age-boundary coverage to the analysis test suite.

## [0.1.0] - 2026-10-05

### Added

- Gmail search based cleanup CLI
- Dry-run by default
- Explicit confirmation before applying changes
- Batch trash operations
- OAuth credential loading and refresh
- Unit tests for search pagination, metadata parsing, batching and confirmation
- GitHub Actions CI
- Credential-focused security documentation

### Changed

- Support Python 3.11 through 3.14 in project metadata and CI.
- Centralize the package version in `gmail_cleaner.__version__`.
- Expand tests for OAuth credential handling, apply behavior and CLI error reporting.
- Warn on broad Gmail selectors before interactive mutation.
- Require an explicit `--allow-broad-query` opt-in for broad selectors in non-interactive `--yes` mode.
- Report successful mutation progress when a later Trash batch fails.
- Validate the CLI on real Android/Termux with a real Gmail dry run and one-message Trash test.
