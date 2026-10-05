# Architecture

## v0.1 architecture

The project intentionally keeps the runtime path small:

```text
CLI arguments
     │
     ▼
argument validation
     │
     ▼
OAuth credential layer
     │
     ▼
Gmail API service
     │
     ▼
message search
     │
     ├── metadata preview
     │
     └── apply safety gate
              │
              ▼
       batchModify(TRASH)
```

### Boundaries

**CLI layer** owns argument parsing, operator-facing output, and the apply gate.

**OAuth layer** loads, refreshes, and creates credentials. Tokens are stored locally and are never committed.

**Search layer** returns message IDs from Gmail using the operator's query.

**Preview layer** requests only lightweight metadata needed for the operator's decision.

**Mutation layer** adds Gmail's `TRASH` label in bounded batches. Permanent deletion is outside the project scope.

## Safety properties

The important properties are:

1. No mutation during normal dry-run execution.
2. Mutation requires `--apply`.
3. Interactive mutation requires the exact word `TRASH`.
4. Broad selectors receive additional scrutiny.
5. Non-interactive broad cleanup requires an explicit override.
6. Mutation progress is reported when later batches fail.

These properties are tested with unit tests and have also been exercised against a real Gmail account on Android/Termux.

## v0.2 boundary

v0.2 should introduce a separate **analysis layer** rather than embedding classification logic inside the mutation path.

Planned flow:

```text
Gmail API
   │
   ▼
lightweight observation
   │
   ▼
normalization
   │
   ▼
analysis
   │
   ├── sender groups
   ├── categories
   ├── age distribution
   └── cleanup candidates
   │
   ▼
report
   │
   ▼
operator decision
   │
   ▼
existing safety + mutation layer
```

The analysis layer should produce evidence and recommendations, not silently delete or trash messages.

## Threat model

The primary risks are operator mistakes, credential leakage, overly broad queries, and partial API failure.

The design responds by minimizing collected data, excluding secrets from Git, keeping mutation explicit, limiting operations to Trash, guarding broad non-interactive queries, and reporting partial progress.
