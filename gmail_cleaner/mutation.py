"""Gmail Trash execution results for v0.3 verification/reporting."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any

from googleapiclient.errors import HttpError

BATCH_SIZE = 100


@dataclass(frozen=True)
class BatchOutcome:
    """Outcome of one bounded Gmail Trash mutation batch."""

    batch_index: int
    requested: int
    message_ids: tuple[str, ...]
    succeeded: bool
    error: str | None = None


@dataclass(frozen=True)
class MutationExecution:
    """Structured result of a Trash mutation attempt."""

    batches: tuple[BatchOutcome, ...]

    @property
    def moved_ids(self) -> tuple[str, ...]:
        """Return IDs from batches confirmed by Gmail as successful."""
        return tuple(
            message_id
            for batch in self.batches
            if batch.succeeded
            for message_id in batch.message_ids
        )

    @property
    def moved_count(self) -> int:
        """Return the count of successfully processed message IDs."""
        return len(self.moved_ids)

    @property
    def failed(self) -> bool:
        """Return whether any mutation batch failed."""
        return any(not batch.succeeded for batch in self.batches)


def move_to_trash_detailed(
    service: Any,
    message_ids: Sequence[str],
    *,
    batch_size: int = BATCH_SIZE,
) -> MutationExecution:
    """Move messages to Trash and retain explicit per-batch outcomes."""
    if batch_size <= 0:
        raise ValueError("batch_size must be greater than zero")

    batches = []
    for start in range(0, len(message_ids), batch_size):
        batch_ids = tuple(message_ids[start : start + batch_size])
        index = (start // batch_size) + 1

        try:
            (
                service.users()
                .messages()
                .batchModify(
                    userId="me",
                    body={"ids": list(batch_ids), "addLabelIds": ["TRASH"]},
                )
                .execute()
            )
        except HttpError as exc:
            batches.append(
                BatchOutcome(
                    batch_index=index,
                    requested=len(batch_ids),
                    message_ids=batch_ids,
                    succeeded=False,
                    error=f"HttpError: {exc}",
                )
            )
            break

        batches.append(
            BatchOutcome(
                batch_index=index,
                requested=len(batch_ids),
                message_ids=batch_ids,
                succeeded=True,
            )
        )

    return MutationExecution(tuple(batches))
