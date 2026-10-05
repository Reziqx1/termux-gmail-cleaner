# Termux Gmail Cleaner

[![Release](https://img.shields.io/github/v/release/Reziqx1/termux-gmail-cleaner?display_name=tag&sort=semver)](https://github.com/Reziqx1/termux-gmail-cleaner/releases)
[![Tests](https://github.com/Reziqx1/termux-gmail-cleaner/actions/workflows/tests.yml/badge.svg)](https://github.com/Reziqx1/termux-gmail-cleaner/actions/workflows/tests.yml)
[![Security audit](https://github.com/Reziqx1/termux-gmail-cleaner/actions/workflows/security.yml/badge.svg)](https://github.com/Reziqx1/termux-gmail-cleaner/actions/workflows/security.yml)
[![License](https://img.shields.io/github/license/Reziqx1/termux-gmail-cleaner)](LICENSE)

> A safety-first Gmail cleanup CLI for Android/Termux.

Termux Gmail Cleaner uses Gmail's own search syntax to find messages, show a lightweight preview, and optionally move matches to **Trash**. It deliberately does **not** implement permanent deletion.

**Design principle:** observe → preview → explicitly confirm → change → verify

## Why this project?

Gmail cleanup is easy to automate badly. This project keeps the core operation small, inspectable, and reversible: search first, inspect metadata, require an explicit mutation mode, and only add the Gmail `TRASH` label.

## Safety contract

- **Dry run is the default.** A normal invocation never changes Gmail.
- **Mutation requires `--apply`.**
- **Interactive apply requires the exact confirmation word `TRASH`.**
- **Non-interactive `--yes` is an explicit opt-in.**
- Broad selectors such as `in:anywhere`, `in:all`, and `label:all` trigger an additional warning; `--yes` requires `--allow-broad-query` for those selectors.
- Changes are performed with Gmail's `batchModify` using the `TRASH` label.
- **Permanent deletion is intentionally unsupported.**
- The tool previews only message metadata (`Subject` and `From`); it does not download message bodies or attachments for cleanup.
- OAuth client files and tokens are ignored by Git and written with owner-only permissions where the platform supports them.

## Features

- Gmail API + OAuth 2.0
- Android + Termux friendly
- Gmail query syntax passthrough
- Dry-run-first workflow
- Exact interactive confirmation
- Deliberate non-interactive mode
- Broad-query safety guard
- Metadata-only previews
- Bounded Trash batches of 100 messages
- Partial-batch failure reporting
- Credential handling and refresh
- Unit tests across Python 3.11–3.14
- GitHub Actions test and dependency-audit workflows
- Dependabot for Python and GitHub Actions dependencies

## Requirements

- Android with Termux
- Python 3.11+
- A Google Cloud OAuth client configured as a desktop application
- Gmail API enabled for the Google Cloud project

### Install from source

Clone the repository, then create the Termux environment:

```bash
git clone https://github.com/Reziqx1/termux-gmail-cleaner.git
cd termux-gmail-cleaner
```

For dependencies with native components, prefer Termux's packaged builds:

```bash
pkg update
pkg install python python-cryptography ruff
python -m venv --system-site-packages .venv
source .venv/bin/activate
python -m pip install -e .
```

This is the development setup validated on a real Android/Termux environment.

## Authentication

1. Create/download a Google OAuth client JSON for a desktop application.
2. Save it locally as `credentials.json`.
3. Keep the file private and never commit it.
4. Run the CLI. On first use, it prints an authorization URL that can be opened manually in the Android browser.
5. The resulting token is stored as `token.json` by default.

Optional environment overrides:

```bash
export GMAIL_CREDENTIALS="$HOME/.config/gmail-cleaner/credentials.json"
export GMAIL_TOKEN="$HOME/.config/gmail-cleaner/token.json"
```

For a test-mode Google OAuth application, authorize only an account that is permitted to use the application's configured test audience.

## Quick start

### Preview

```bash
gmail-cleaner --query 'category:promotions older_than:1y'
```

No Gmail changes are made.

### Apply

```bash
gmail-cleaner --query 'category:promotions older_than:1y' --apply
```

Review the preview and type `TRASH` when prompted.

### Automation

```bash
gmail-cleaner --query 'from:example.com' --apply --yes
```

Use `--yes` only when the exact query and result scope are already trusted.

For broad selectors, add the explicit safety override:

```bash
gmail-cleaner --query 'in:anywhere category:promotions' --apply --yes --allow-broad-query
```

### Limit the operation

```bash
gmail-cleaner --query 'from:example.com' --max-results 100 --preview 25
```

The default maximum is 50 messages and the default preview is 20.

## Gmail query examples

The query is passed to Gmail unchanged:

```text
older_than:1y
category:promotions older_than:6m
from:example.com
has:attachment larger:10M
in:anywhere newer_than:7d
```

Start narrow and verify the dry-run output before applying a cleanup.

## What the tool does not do

This project intentionally does not:

- permanently delete messages
- download or export mail bodies for cleanup
- inspect attachments
- infer that a message is junk based on its content
- silently mutate Gmail in dry-run mode
- commit OAuth credentials, tokens, or personal mailbox data

Gmail itself controls the lifecycle of messages after they are moved to Trash.

## Architecture

The current v0.1 architecture is deliberately small:

```text
CLI arguments
     │
     ▼
OAuth credential layer
     │
     ▼
Gmail search
     │
     ▼
message IDs
     │
     ├── metadata preview
     │
     └── apply gate
            │
            ▼
      batchModify(TRASH)
```

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for design boundaries and the planned analysis layer for v0.2.

## Development

Run the tests:

```bash
python -m unittest discover -s tests -v
```

Run static checks:

```bash
ruff check .
ruff format --check .
```

Audit dependencies:

```bash
pip-audit
```

Every pull request should leave the tests and security workflow green.

## Verification

v0.1.0 has been validated on a real Android/Termux environment with:

- OAuth authorization against a real Gmail account
- real Gmail read-only dry runs
- a one-message disposable Trash mutation
- verification that the test message appeared in Trash and disappeared from Inbox
- 21 unit tests passing locally
- CI test matrix passing on Python 3.11–3.14
- dependency security audit passing

These checks establish that the core workflow works; they are not a guarantee that every Gmail query is safe. Query scope remains the operator's responsibility.

## Project status

**v0.1.0 — released.**

The v0.1 series is the stable safety-first foundation. v0.2 will focus on mailbox analysis and reporting before introducing broader automation.

## Roadmap

### v0.2 — Analysis

- [ ] Lightweight mailbox scan
- [ ] Sender/category/age grouping
- [ ] Cleanup candidate reports
- [ ] Structured output for scripts
- [ ] Safer batch verification/reporting

### Later

- [ ] Reusable cleanup presets
- [ ] Better operator-facing reports
- [ ] Additional portability improvements

## Security

See [SECURITY.md](SECURITY.md) for credential handling and vulnerability reporting.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). Safety, reproducibility, tests, and clear behavior come before feature volume.

## License

MIT
