# Security Policy

## Sensitive data

This project handles Gmail OAuth credentials. Never commit:

- OAuth client JSON files
- OAuth access or refresh tokens
- API keys
- exported mail
- message bodies or attachments

The default `.gitignore` covers the common credential filenames.

## Reporting a vulnerability

Do not open a public issue containing credentials, tokens or exploitable details.

For a suspected security problem, contact the repository owner privately through GitHub and include enough information to reproduce the issue without exposing secrets.

## Safety model

The CLI is dry-run by default and only moves messages to Trash when `--apply` is provided. Permanent deletion is intentionally not implemented.

Apply mode warns when broad Gmail selectors such as `in:anywhere` are present. Non-interactive `--yes` mode requires an explicit `--allow-broad-query` opt-in for those selectors.
