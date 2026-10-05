# Security Policy

## Sensitive data

This project handles Gmail OAuth credentials. Never commit:

- OAuth client JSON files
- OAuth access or refresh tokens
- API keys
- exported mail
- message bodies or attachments
- private logs containing mailbox data

The repository ignores common credential and local-secret patterns. Still verify `git status` and `git diff` before pushing.

## Local credential handling

Keep OAuth client files and tokens in private local storage. The CLI attempts to write token files with owner-only permissions where the underlying filesystem supports them.

If a credential is accidentally exposed, stop using it and revoke/rotate it through the relevant Google account or Cloud project controls. Do not paste credentials or tokens into GitHub issues or chat.

## Safety model

The CLI is dry-run by default.

Mutation requires `--apply`. Interactive mutation requires the exact confirmation word `TRASH`. Non-interactive `--yes` is an explicit opt-in.

Broad Gmail selectors such as `in:anywhere`, `in:all`, and `label:all` receive additional scrutiny. Non-interactive use of those selectors requires `--allow-broad-query`.

The mutation path adds the Gmail `TRASH` label in bounded batches. Permanent deletion is intentionally not implemented.

## Privacy model

Cleanup previews request lightweight message metadata needed for operator review. The project does not download message bodies or attachments as part of its current cleanup flow.

## Reporting a vulnerability

Do not open a public issue containing credentials, tokens, private mailbox data, or exploitable security details.

Contact the repository owner privately through GitHub and provide enough information to reproduce the issue without exposing secrets.
