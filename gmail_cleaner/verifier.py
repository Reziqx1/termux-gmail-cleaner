"""Read-only verification of Gmail Trash state for v0.3."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any

from googleapiclient.errors import HttpError


@dataclass(frozen=True)
class VerificationResult:
    """Verification state for one message after a mutation attempt."""

    message_id: str
    state: str
    detail: str | None = None


def verify_trashed(
    service: Any,
    message_ids: Sequence[str],
) -> tuple[VerificationResult, ...]:
    """Read message label state and confirm which IDs are in Gmail Trash."""
    results: list[VerificationResult] = []

    for message_id in message_ids:
        try:
            response = (
                service.users()
                .messages()
                .get(
                    userId="me",
                    id=message_id,
                    format="minimal",
                )
                .execute()
            )
        except (HttpError, OSError) as exc:
            results.append(
                VerificationResult(
                    message_id=message_id,
                    state="verification-error",
                    detail=f"{type(exc).__name__}: {exc}",
                )
            )
            continue

        labels = tuple(str(label) for label in response.get("labelIds", ()))
        if "TRASH" in labels:
            results.append(
                VerificationResult(
                    message_id=message_id,
                    state="verified",
                )
            )
        else:
            results.append(
                VerificationResult(
                    message_id=message_id,
                    state="not-verified",
                    detail="TRASH label is absent",
                )
            )

    return tuple(results)
