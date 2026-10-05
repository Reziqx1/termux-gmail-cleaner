# Termux Gmail Cleaner

A small, evidence-first Gmail cleanup CLI designed to run in Termux.

The project is intentionally **dry-run first**: it searches Gmail, shows what would be affected, and only moves messages to Trash when the user explicitly passes `--apply`.

## Features

- Gmail API + OAuth 2.0
- Termux-friendly Python CLI
- Dry-run by default
- Configurable Gmail search query
- Preview matching messages before applying changes
- Moves messages to Gmail Trash instead of permanently deleting them
- Keeps OAuth credentials and tokens outside Git
- Simple, inspectable source code

## Requirements

- Android + Termux
- Python 3.10+
- A Google Cloud OAuth client for a desktop application
- A Gmail account with Gmail API access enabled

Install dependencies:

```bash
pkg update
pkg install python
pip install -r requirements.txt
```

Place your OAuth client file at:

```text
credentials.json
```

Do **not** commit it.

## Usage

Preview messages:

```bash
python -m src.gmail_cleaner --query 'category:promotions older_than:1y'
```

Apply the cleanup:

```bash
python -m src.gmail_cleaner --query 'category:promotions older_than:1y' --apply
```

Limit the number of messages processed:

```bash
python -m src.gmail_cleaner --query 'from:example.com' --max-results 100
```

The default behavior never modifies Gmail.

## Configuration

The tool accepts Gmail's normal search syntax through `--query`.

Examples:

```text
older_than:1y
category:promotions older_than:6m
from:example.com
has:attachment larger:10M
```

Start with a narrow query, inspect the dry-run output, then use `--apply`.

## Security

Never commit:

- `credentials.json`
- `token.json`
- API keys
- OAuth client secrets
- personal exports or message data

The repository's `.gitignore` blocks the common credential filenames.

## Project status

Early-stage personal developer project.

The goal is not to hide complexity behind a giant automation script. The project is intentionally small so the behavior can be read, tested and understood.

## Development

Run the test suite with:

```bash
python -m unittest discover -s tests -v
```

## License

MIT
