# Changelog

## Unreleased

### Changed

- Support Python 3.11 through 3.14 in project metadata and CI.
- Centralize the package version in `gmail_cleaner.__version__`.
- Expand tests for OAuth credential handling, apply behavior and CLI error reporting.

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
