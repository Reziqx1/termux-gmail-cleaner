## Summary

Describe what changed and why.

## Validation

- [ ] `python -m unittest discover -s tests -v`
- [ ] `ruff check .`
- [ ] `ruff format --check .`
- [ ] `pip-audit` when dependency-related changes are made
- [ ] Real-device validation performed when Termux/runtime behavior changed

## Safety review

- [ ] Dry-run behavior remains read-only.
- [ ] No credentials, tokens, private Gmail data, or personal secrets are included.
- [ ] Any mutation behavior remains explicit and Trash-only.
- [ ] Security and behavior implications are documented.
