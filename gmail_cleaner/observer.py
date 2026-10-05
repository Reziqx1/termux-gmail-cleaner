"""Gmail metadata observation adapter for the v0.2 analysis layer."""

from __future__ import annotations

from typing import Any

from .analysis import (
    MessageObservation,
    gmail_internal_date_to_datetime,
    normalize_sender,
)


def _header_value(message: dict[str, Any], name: str, default: str) -> str:
    """Return one metadata header value or a safe fallback."""
    wanted = name.lower()
    for header in message.get("payload", {}).get("headers", []):
        if header.get("name", "").lower() == wanted:
            return str(header.get("value", "")).strip() or default
    return default


def observation_from_resource(message: dict[str, Any]) -> MessageObservation:
    """Normalize one Gmail message resource into an analysis observation."""
    message_id = str(message.get("id", "")).strip()
    thread_id = str(message.get("threadId", "")).strip()
    internal_date = message.get("internalDate")

    if not message_id:
        raise ValueError("Gmail message resource is missing id")
    if not thread_id:
        raise ValueError(f"Gmail message {message_id} is missing threadId")
    if internal_date is None:
        raise ValueError(f"Gmail message {message_id} is missing internalDate")

    sender_name, sender_email = normalize_sender(
        _header_value(message, "From", "(unknown sender)")
    )

    return MessageObservation(
        message_id=message_id,
        thread_id=thread_id,
        sender_name=sender_name,
        sender_email=sender_email,
        subject=_header_value(message, "Subject", "(no subject)"),
        internal_date=gmail_internal_date_to_datetime(internal_date),
        label_ids=tuple(str(label) for label in message.get("labelIds", [])),
    )


def fetch_observation(service: Any, message_id: str) -> MessageObservation:
    """Fetch the minimal Gmail metadata required for analysis."""
    response = (
        service.users()
        .messages()
        .get(
            userId="me",
            id=message_id,
            format="metadata",
            metadataHeaders=["Subject", "From"],
        )
        .execute()
    )
    return observation_from_resource(response)


def fetch_observations(
    service: Any, message_ids: list[str]
) -> list[MessageObservation]:
    """Fetch observations in message-ID order."""
    return [fetch_observation(service, message_id) for message_id in message_ids]
