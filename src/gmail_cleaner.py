#!/usr/bin/env python3
"""Dry-run-first Gmail cleanup CLI for Termux.

The tool uses Gmail search syntax and moves matching messages to Trash only
when --apply is explicitly supplied. It never performs permanent deletion.
"""

from __future__ import annotations

import argparse
import os
from pathlib import Path
from typing import Iterable

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES = ["https://www.googleapis.com/auth/gmail.modify"]
DEFAULT_MAX_RESULTS = 50
BATCH_SIZE = 100


def chunked(items: list[str], size: int) -> Iterable[list[str]]:
    """Yield a list in fixed-size chunks."""
    for start in range(0, len(items), size):
        yield items[start : start + size]


def get_credentials(credentials_path: Path, token_path: Path) -> Credentials:
    """Load, refresh or create Gmail OAuth credentials."""
    creds: Credentials | None = None

    if token_path.exists():
        creds = Credentials.from_authorized_user_file(str(token_path), SCOPES)

    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
    elif not creds or not creds.valid:
        if not credentials_path.exists():
            raise FileNotFoundError(
                f"OAuth client file not found: {credentials_path}. "
                "Create credentials.json from Google Cloud and keep it private."
            )
        flow = InstalledAppFlow.from_client_secrets_file(
            str(credentials_path), SCOPES
        )
        creds = flow.run_local_server(port=0)

    token_path.write_text(creds.to_json(), encoding="utf-8")
    return creds


def build_service(credentials_path: Path, token_path: Path):
    """Create an authenticated Gmail API service."""
    creds = get_credentials(credentials_path, token_path)
    return build("gmail", "v1", credentials=creds)


def search_message_ids(service, query: str, max_results: int) -> list[str]:
    """Return Gmail message IDs matching a search query."""
    ids: list[str] = []
    page_token: str | None = None

    while len(ids) < max_results:
        response = (
            service.users()
            .messages()
            .list(
                userId="me",
                q=query,
                maxResults=min(100, max_results - len(ids)),
                pageToken=page_token,
            )
            .execute()
        )
        ids.extend(item["id"] for item in response.get("messages", []))

        page_token = response.get("nextPageToken")
        if not page_token:
            break

    return ids[:max_results]


def fetch_metadata(service, message_id: str) -> tuple[str, str]:
    """Fetch a compact subject/from summary for preview output."""
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

    headers = {
        item["name"].lower(): item["value"]
        for item in response.get("payload", {}).get("headers", [])
    }
    return headers.get("subject", "(no subject)"), headers.get("from", "(unknown sender)")


def move_to_trash(service, message_ids: list[str]) -> None:
    """Move messages to Gmail Trash in bounded batches."""
    for batch in chunked(message_ids, BATCH_SIZE):
        service.users().messages().batchModify(
            userId="me",
            body={"ids": batch, "addLabelIds": ["TRASH"]},
        ).execute()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Preview or trash Gmail messages matching a search query."
    )
    parser.add_argument(
        "--query",
        required=True,
        help="Gmail search query, e.g. 'category:promotions older_than:1y'",
    )
    parser.add_argument(
        "--max-results",
        type=int,
        default=DEFAULT_MAX_RESULTS,
        help=f"Maximum messages to inspect (default: {DEFAULT_MAX_RESULTS}).",
    )
    parser.add_argument(
        "--credentials",
        type=Path,
        default=Path(os.environ.get("GMAIL_CREDENTIALS", "credentials.json")),
        help="OAuth client JSON path.",
    )
    parser.add_argument(
        "--token",
        type=Path,
        default=Path(os.environ.get("GMAIL_TOKEN", "token.json")),
        help="OAuth token JSON path.",
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Actually move matching messages to Trash. Without this flag the run is read-only.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    if args.max_results <= 0:
        raise SystemExit("--max-results must be greater than zero.")

    if not args.query.strip():
        raise SystemExit("--query cannot be empty.")

    service = build_service(args.credentials, args.token)
    message_ids = search_message_ids(service, args.query, args.max_results)

    print(f"Query: {args.query}")
    print(f"Matched: {len(message_ids)} message(s)")
    print(f"Mode: {'APPLY (move to Trash)' if args.apply else 'DRY RUN (no changes)'}")

    for message_id in message_ids[:20]:
        subject, sender = fetch_metadata(service, message_id)
        print(f"- {subject} | {sender}")

    if len(message_ids) > 20:
        print(f"- ... and {len(message_ids) - 20} more")

    if not message_ids:
        return 0

    if args.apply:
        move_to_trash(service, message_ids)
        print(f"Moved {len(message_ids)} message(s) to Gmail Trash.")
    else:
        print("No changes made. Re-run with --apply to move these messages to Trash.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
