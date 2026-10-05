# Termux Gmail Cleaner

> A safety-first Gmail cleanup CLI for Android/Termux.

[![Tests](https://github.com/Reziqx1/termux-gmail-cleaner/actions/workflows/tests.yml/badge.svg)](https://github.com/Reziqx1/termux-gmail-cleaner/actions/workflows/tests.yml)
[![Security audit](https://github.com/Reziqx1/termux-gmail-cleaner/actions/workflows/security.yml/badge.svg)](https://github.com/Reziqx1/termux-gmail-cleaner/actions/workflows/security.yml)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

Termux Gmail Cleaner searches Gmail using Gmail's own query syntax and lets you review matches before moving them to **Trash**. It never implements permanent deletion.

## Why it exists

This project started as a personal Android/Termux automation experiment. It is intentionally small and readable so the behavior can be inspected instead of hidden behind a large framework.

The design principle is:

**observe → preview → explicitly confirm → change → verify**

## Features

- Gmail API with OAuth 2.0
- Designed for Android + Termux
- Read-only dry run by default
- Explicit `--apply` plus a `TRASH` confirmation before mutation
- Optional `--yes` for intentional non-interactive use
- Configurable Gmail search query
- Preview of matching message subjects/senders
- Batched move-to-Trash operation
- Credential files excluded from Git and written with owner-only permissions where supported
- Unit tests and GitHub Actions CI
- Dependency security auditing

## Requirements

- Android + Termux
- Python 3.10+
- A Google Cloud OAuth client for a desktop application
- Gmail API enabled for the account/project

Install:

```bash
pkg update
pkg install python
python -m pip install -e .
```

## Authentication

Download your Google OAuth client JSON and save it locally as:

```text
credentials.json
```

Keep it private. The first run starts an OAuth loopback flow and prints the authorization URL so it can be opened manually in the Android browser.

The resulting token is stored at `token.json` by default and is also ignored by Git.

You can override both locations:

```bash
export GMAIL_CREDENTIALS="$HOME/.config/gmail-cleaner/credentials.json"
export GMAIL_TOKEN="$HOME/.config/gmail-cleaner/token.json"
```

## Usage

### 1. Preview first

```bash
python -m gmail_cleaner --query 'category:promotions older_than:1y'
```

This mode makes **no Gmail changes**.

### 2. Apply after reviewing

```bash
python -m gmail_cleaner --query 'category:promotions older_than:1y' --apply
```

The CLI then asks you to type `TRASH`.

For deliberate automation where you already trust the exact query:

```bash
python -m gmail_cleaner --query 'from:example.com' --apply --yes
```

### 3. Control result volume

```bash
python -m gmail_cleaner --query 'from:example.com' --max-results 100 --preview 25
```

## Gmail query examples

Gmail query syntax is passed through unchanged:

```text
older_than:1y
category:promotions older_than:6m
from:example.com
has:attachment larger:10M
```

Start narrow. Use dry-run output to verify what the query selects.

## Security model

This project intentionally does **not** support permanent deletion.

The required Gmail scope is `gmail.modify`, used to search messages and add the `TRASH` label.

Never commit credentials, refresh tokens, exported mail or personal message data. See [SECURITY.md](SECURITY.md).

## Development

Run tests:

```bash
python -m unittest discover -s tests -v
```

Run lint/format checks:

```bash
ruff check .
ruff format --check .
```

Audit dependencies:

```bash
pip-audit
```

The CI runs tests and security checks automatically.

## Project status

**Unreleased v0.1.0 — early-stage personal project.**

The core cleanup flow is implemented, but the project has not yet been published as a packaged release. Real-device validation should be performed with a test Gmail account or carefully scoped queries before broad use.

## Roadmap

- [ ] Add safer batch verification/reporting
- [ ] Add optional structured output for scripts
- [ ] Add more unit tests around OAuth and failure paths
- [ ] Validate the CLI on current Termux/Python versions
- [ ] Publish a first tagged release after real-device validation

## License

MIT
