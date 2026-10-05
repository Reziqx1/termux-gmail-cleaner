# Contributing

This is a small personal project, but contributions are welcome when they improve correctness, safety or portability.

## Before submitting changes

1. Keep the default behavior read-only.
2. Never add credentials, OAuth tokens or personal Gmail data.
3. Add or update tests for behavior changes.
4. Run:

```bash
python -m unittest discover -s tests -v
ruff check .
ruff format --check .
```

5. Explain security or behavior implications in the pull request.

## Scope

Please avoid adding broad automation that permanently deletes mail. Changes should remain explicit, inspectable and easy to reverse where possible.
