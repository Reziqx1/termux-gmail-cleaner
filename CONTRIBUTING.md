# Contributing

Thanks for improving Termux Gmail Cleaner.

This project values **correctness, safety, reproducibility, and portability** over feature volume.

## Before submitting changes

1. Keep normal behavior read-only unless the task explicitly concerns mutation behavior.
2. Never add OAuth credentials, tokens, personal Gmail data, message bodies, attachments, or other secrets.
3. Add or update tests for behavior changes.
4. Run:

```bash
python -m unittest discover -s tests -v
ruff check .
ruff format --check .
```

5. Run `pip-audit` for dependency changes.
6. Explain behavior, safety, and compatibility implications in the pull request.

## Design expectations

- Keep operations explicit and inspectable.
- Preserve dry-run behavior.
- Preserve Trash-only mutation semantics.
- Prefer small, testable functions over hidden automation.
- Treat Gmail query scope as user-controlled input.
- Do not introduce permanent deletion.

## Pull requests

Use the pull request template. A good pull request explains:

- what changed
- why it changed
- how it was tested
- what safety or compatibility implications exist

Real-device validation is expected when Android/Termux behavior changes.

## Scope

Please avoid broad automation that permanently deletes mail or hides destructive behavior behind defaults.

See [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md) for community expectations and [SUPPORT.md](SUPPORT.md) for troubleshooting.
