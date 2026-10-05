# Support

## Before opening an issue

Please check:

1. The README setup and authentication sections.
2. Your Python and Termux environment.
3. The exact Gmail query in a dry run before using `--apply`.

For reproducible bugs, include the command shape, expected behavior, actual behavior, and relevant error output. Do not include OAuth credentials, tokens, message bodies, private email addresses, or exported Gmail data.

## Common checks

### OAuth problems

Confirm that the OAuth client JSON exists at the configured path and that the Google account is permitted to use the OAuth application's test audience when the app is in testing.

### Termux dependency problems

Prefer Termux-native packages for dependencies with native components. See the README for the validated development setup.

### Unexpected matches

Gmail query semantics determine the search result set. Run the same query without `--apply` and inspect the preview before changing anything.

## Security issues

Do not report security vulnerabilities in a public issue. See [SECURITY.md](SECURITY.md).
