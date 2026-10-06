# Changelog

## [Unreleased]

### Added

- Add versioned analysis reports with deterministic JSON and human-readable output.
- Add structured Trash mutation outcomes with per-batch success/failure reporting.
- Add read-only Trash verification with explicit verification states.
- Add local, credential-free TOML cleanup presets with strict validation and CLI precedence.
- Add centralized portable configuration, credential, token, and preset path resolution.

### Changed

- Apply now produces a final cleanup report and verifies successfully processed messages without introducing a second mutation path.
- Preserve the existing dry-run, explicit `--apply`, exact `TRASH` confirmation, and broad-query safety boundaries.
- Keep analysis metadata-only and permanent deletion unsupported.

### Validation

- GitHub Actions test and security workflows pass for the complete v0.3 implementation slices.
- Real Android/Termux + Gmail validation remains the final release gate in issue #25.

## [0.2.0] - 2026-10-06

### Added

- Add a read-only Gmail metadata observer and deterministic mailbox analysis primitives.
- Add a JSON-producing `--analyze` CLI mode with explicit review-candidate criteria.
- Add evidence-first sender, category, and age distributions for queried messages.

### Changed

- Enrich review-candidate output with sender, subject, age, category, and explicit reasons for operator review.
- Deduplicate candidate reasons and add exact-age-boundary coverage to the analysis test suite.
- Document the v0.2 analysis boundary, validation evidence, and repository-maintainer guidance.
- Improve package metadata and local build-artifact handling.
- Harden interactive apply so a zero-item preview cannot be confirmed accidentally.
- Apply owner-only permissions to existing OAuth credential files before loading them where supported.

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
