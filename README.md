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
- Read-only mailbox analysis with transparent candidate reporting
- Versioned analysis reports with JSON and human-readable output
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

Configuration and credential paths are resolved with this precedence:
**explicit CLI path → environment override → application config directory**.
The default application config directory is `~/.config/gmail-cleaner`. The same portable resolver is used for local presets.

```bash
export GMAIL_CREDENTIALS="$HOME/.config/gmail-cleaner/credentials.json"
export GMAIL_TOKEN="$HOME/.config/gmail-cleaner/token.json"
export GMAIL_CLEANER_CONFIG_DIR="$HOME/.config/gmail-cleaner"
export GMAIL_CLEANER_PRESET_DIR="$HOME/.config/gmail-cleaner/presets"
```

For a test-mode Google OAuth application, authorize only an account that is permitted to use the application's configured test audience.

## Quick start

### Preview

```bash
gmail-cleaner --query 'category:promotions older_than:1y'
```

No Gmail changes are made.

### Analyze (read-only)

v0.2 adds an evidence-first mailbox analysis mode. It never mutates Gmail:

```bash
gmail-cleaner --query 'category:promotions newer_than:1y' --analyze
```

The command prints structured JSON containing sender/category/age distributions and transparent review candidates. By default, a candidate must match the selected category and be at least 180 days old. Change the threshold or category explicitly with `--candidate-older-than` and `--candidate-category`.

Analysis uses lightweight Gmail metadata only; it does not download message bodies or attachments.

### Human-readable analysis report

v0.3 adds a separate operator-facing renderer without changing the analysis logic:

```bash
gmail-cleaner --query 'category:promotions newer_than:1y' --analyze --report-format human
```

Use JSON when another program needs structured data; use human output when reviewing the mailbox interactively. Both modes remain read-only.

### Reusable presets

Save a reviewed cleanup recipe locally as TOML, then load it without putting credentials into the preset:

```text
query = "category:promotions older_than:1y"
max_results = 100
preview = 25
candidate_categories = ["promotions"]
candidate_older_than = 180
report_format = "json"
```

Use the preset management commands:

```bash
gmail-cleaner --list-presets
gmail-cleaner --show-preset old-promotions
gmail-cleaner --preset old-promotions --analyze
```

Explicit CLI values override preset values, and a preset never bypasses `--apply`, confirmation, or broad-query safety gates.

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

The current architecture keeps analysis and mutation deliberately separated:

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
     ├───────────────┐
     │               │
     ▼               ▼
metadata preview   metadata observer
     │               │
     │               ▼
     │          analysis core
     │               │
     │               ▼
     │          report renderers
     │
     └── apply gate ──► batchModify(TRASH)
                              │
                              ▼
                         verification
```

The v0.2 analysis path is read-only and cannot be combined with `--apply`. See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md), [docs/V0.2_ANALYSIS.md](docs/V0.2_ANALYSIS.md), and [docs/V0.3_ROADMAP.md](docs/V0.3_ROADMAP.md) for the design boundaries.

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

The project has been validated on a real Android/Termux environment with:

- OAuth authorization against a real Gmail account
- real Gmail read-only dry runs
- a one-message disposable Trash mutation
- verification that the test message appeared in Trash and disappeared from Inbox
- **44 unit tests passing locally after the v0.2 candidate-reporting refinement**
- deterministic candidate-reporting proof producing the expected candidate structure
- real Gmail `--analyze` runs returning structured JSON without mutations
- CI test matrix passing on Python 3.11–3.14
- dependency security audit passing on the merged v0.2 commit
- GitHub Release **v0.2.0** published from `main` at commit `fe1eca4609393ea2e860ae195cff164c9a2a3c13`

The complete v0.3 implementation is covered by the GitHub Actions test/security workflows. Real Android/Termux + Gmail validation of the v0.3 release candidate is tracked separately in GitHub issue [#25](https://github.com/Reziqx1/termux-gmail-cleaner/issues/25). These checks establish that the core workflow works; they are not a guarantee that every Gmail query is safe. Query scope remains the operator's responsibility.

## Project status

**v0.2.0 — released; v0.3 release candidate.**

The complete v0.3 implementation is merged to `main`: reporting, mutation verification, reusable local presets, and portable configuration paths are in place. The remaining release gate is real Android/Termux + Gmail validation, tracked in issue [#25](https://github.com/Reziqx1/termux-gmail-cleaner/issues/25).

## Roadmap

### v0.2 — Analysis (complete)

- [x] Lightweight mailbox scan
- [x] Sender/category/age grouping
- [x] Cleanup candidate reports
- [x] Structured output for scripts

### v0.3 — Evidence-first cleanup workflow (in progress)

- [x] Versioned analysis report model
- [x] Human-readable analysis renderer
- [x] Safer verification and batch reporting
- [x] Reusable local cleanup presets
- [x] Portable configuration/path handling
- [ ] Real Android/Termux + Gmail validation for the completed workflow
- [ ] v0.3.0 release

See [docs/V0.3_ROADMAP.md](docs/V0.3_ROADMAP.md) and GitHub issue [#17](https://github.com/Reziqx1/termux-gmail-cleaner/issues/17).

### Later

- Additional portability improvements beyond the v0.3 scope
- Broader workflow integrations only if they preserve the safety contract

## Security

See [SECURITY.md](SECURITY.md) for credential handling and vulnerability reporting.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). Safety, reproducibility, tests, and clear behavior come before feature volume.

## License

MIT
