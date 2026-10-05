# Project Quality Checklist

This file records the quality baseline for the repository so future changes can be evaluated against the same standards.

## Confirmed in the repository

- [x] README explains purpose, safety model, setup, authentication, usage, limitations, development, and roadmap.
- [x] MIT license included.
- [x] CONTRIBUTING.md included.
- [x] CODE_OF_CONDUCT.md included.
- [x] SUPPORT.md included.
- [x] SECURITY.md included.
- [x] CITATION.cff included.
- [x] Issue templates for bugs and feature requests.
- [x] Pull request checklist.
- [x] Dependabot configured for pip and GitHub Actions.
- [x] Credential and common local-secret patterns ignored by Git.
- [x] Build/test artifacts ignored.
- [x] Unit tests cover search pagination, metadata parsing, dry-run behavior, confirmation, query guards, batching, partial failures, CLI errors, and OAuth credential paths.
- [x] CI tests Python 3.11–3.14.
- [x] Dependency security audit runs in CI.
- [x] v0.1.0 has a published Git tag and GitHub release.
- [x] Real Android/Termux validation completed.
- [x] Real Gmail OAuth validation completed.
- [x] Real Gmail dry-run validation completed.
- [x] One-message Trash mutation and post-mutation verification completed.
- [x] Permanent deletion is not implemented.
- [x] Interactive apply requires a visible preview item.

## Current engineering boundary

v0.1 is the stable safety-first foundation.

The next feature work belongs behind the existing safety boundary:

**observe → analyze → report → operator decision → apply → verify**

The v0.2 analysis layer should not silently mutate Gmail.

## Maintainer-side GitHub settings to verify

These items are repository-account settings rather than files, so they should be checked in GitHub Settings:

- [ ] CodeQL default setup enabled for the public repository.
- [ ] Secret scanning enabled.
- [ ] Push protection enabled for supported secrets.
- [ ] Dependabot alerts enabled.
- [ ] Dependabot security updates enabled.
- [ ] Main branch protection/rules configured for pull requests and required checks as appropriate.
- [ ] Repository description and topics accurately describe the project.
- [ ] Best repositories are pinned on the maintainer profile.

## Release rule

A release should not be treated as complete unless:

1. automated tests are green,
2. security checks are green,
3. documentation matches the actual behavior,
4. secrets and generated artifacts are excluded,
5. destructive behavior has a narrow, reproducible test,
6. the release version and changelog agree.
