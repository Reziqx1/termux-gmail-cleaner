"""Dry-run-first Gmail cleanup CLI for Termux."""

from __future__ import annotations

import argparse
import os
import re
import sys
from collections.abc import Iterable, Sequence
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from google.auth.exceptions import GoogleAuthError
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from . import __version__
from .analysis import analyze_observations
from .mutation import move_to_trash_detailed
from .observer import fetch_observations
from .reporting import (
    build_analysis_report,
    build_cleanup_report,
    render_analysis_human,
    render_cleanup_human,
    render_json,
)
from .presets import DEFAULT_PRESET_DIR, list_presets, load_preset, preset_to_toml
from .verifier import verify_trashed

SCOPES = ["https://www.googleapis.com/auth/gmail.modify"]
DEFAULT_MAX_RESULTS = 50
DEFAULT_PREVIEW = 20
BATCH_SIZE = 100
BROAD_QUERY_PATTERN = re.compile(
    r"(?<!\S)(?:in:anywhere|in:all|label:all)(?!\S)",
    re.IGNORECASE,
)


class GmailMutationError(RuntimeError):
    """Raised when a Trash mutation fails after zero or more successful batches."""


def find_broad_query_terms(query: str) -> list[str]:
    """Return broad Gmail selectors that deserve extra scrutiny before applying."""
    return sorted(
        {match.group(0).lower() for match in BROAD_QUERY_PATTERN.finditer(query)}
    )


def chunked(items: Sequence[str], size: int) -> Iterable[list[str]]:
    """Yield fixed-size chunks and reject invalid chunk sizes."""
    if size <= 0:
        raise ValueError("chunk size must be greater than zero")

    for start in range(0, len(items), size):
        yield list(items[start : start + size])


def _secure_permissions(path: Path) -> None:
    """Apply owner-only permissions when the filesystem supports them."""
    try:
        path.chmod(0o600)
    except OSError:
        # Some filesystems do not support Unix permission changes.
        pass


def _secure_write(path: Path, content: str) -> None:
    """Write a credential file with owner-only permissions when supported."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    _secure_permissions(path)


def get_credentials(credentials_path: Path, token_path: Path) -> Credentials:
    """Load, refresh, or create Gmail OAuth credentials."""
    token_path.parent.mkdir(parents=True, exist_ok=True)
    creds: Credentials | None = None

    if token_path.exists():
        _secure_permissions(token_path)
        try:
            creds = Credentials.from_authorized_user_file(str(token_path), SCOPES)
        except (ValueError, KeyError) as exc:
            raise RuntimeError(
                f"Could not read OAuth token file: {token_path}. "
                "Delete it and authenticate again."
            ) from exc

    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
    elif not creds or not creds.valid:
        if not credentials_path.exists():
            raise FileNotFoundError(
                f"OAuth client file not found: {credentials_path}. "
                "Create an OAuth client for a desktop application and keep it private."
            )

        _secure_permissions(credentials_path)
        flow = InstalledAppFlow.from_client_secrets_file(str(credentials_path), SCOPES)
        # Termux may not have a desktop browser integration; the URL can still
        # be opened manually in the Android browser.
        creds = flow.run_local_server(port=0, open_browser=False)

    _secure_write(token_path, creds.to_json())
    return creds


def build_service(credentials_path: Path, token_path: Path) -> Any:
    """Create an authenticated Gmail API service."""
    creds = get_credentials(credentials_path, token_path)
    return build("gmail", "v1", credentials=creds, cache_discovery=False)


def search_message_ids(service: Any, query: str, max_results: int) -> list[str]:
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
                maxResults=min(BATCH_SIZE, max_results - len(ids)),
                pageToken=page_token,
            )
            .execute()
        )
        ids.extend(item["id"] for item in response.get("messages", []))

        page_token = response.get("nextPageToken")
        if not page_token:
            break

    return ids[:max_results]


def fetch_metadata(service: Any, message_id: str) -> tuple[str, str]:
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
    return (
        headers.get("subject", "(no subject)"),
        headers.get("from", "(unknown sender)"),
    )


def move_to_trash(service: Any, message_ids: Sequence[str]) -> int:
    """Move messages to Gmail Trash in bounded batches and report progress."""
    moved = 0
    batches = list(chunked(message_ids, BATCH_SIZE))

    for index, batch in enumerate(batches, start=1):
        try:
            (
                service.users()
                .messages()
                .batchModify(
                    userId="me",
                    body={"ids": batch, "addLabelIds": ["TRASH"]},
                )
                .execute()
            )
        except HttpError as exc:
            raise GmailMutationError(
                f"Trash operation failed in batch {index}/{len(batches)} "
                f"after successfully moving {moved} message(s)."
            ) from exc
        moved += len(batch)

    return moved


def build_parser() -> argparse.ArgumentParser:
    """Build the command-line interface parser."""
    parser = argparse.ArgumentParser(
        description="Preview or move Gmail messages to Trash using a search query."
    )
    parser.add_argument("--version", action="version", version=__version__)
    parser.add_argument(
        "--query",
        help="Gmail search query, e.g. 'category:promotions older_than:1y'.",
    )
    parser.add_argument(
        "--max-results",
        type=int,
        default=None,
        help=f"Maximum messages to inspect (default: {DEFAULT_MAX_RESULTS}).",
    )
    parser.add_argument(
        "--preview",
        type=int,
        default=None,
        help=f"Maximum message summaries to print (default: {DEFAULT_PREVIEW}).",
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
        help="Move matches to Gmail Trash after an explicit confirmation prompt.",
    )
    parser.add_argument(
        "--yes",
        action="store_true",
        help="Skip the confirmation prompt. Only meaningful with --apply.",
    )
    parser.add_argument(
        "--allow-broad-query",
        action="store_true",
        help=(
            "Allow non-interactive --yes mode for broad selectors such as "
            "in:anywhere. Review the query carefully before using this."
        ),
    )
    parser.add_argument(
        "--analyze",
        action="store_true",
        help="Perform a read-only metadata analysis and print a report.",
    )
    parser.add_argument(
        "--report-format",
        choices=("json", "human"),
        default=None,
        help="Analysis report format (default: json). Only used with --analyze.",
    )
    parser.add_argument(
        "--candidate-category",
        action="append",
        default=None,
        help="Category to consider for review candidates (default: promotions).",
    )
    parser.add_argument(
        "--candidate-older-than",
        type=int,
        default=None,
        help="Minimum age in days for review candidates (default: 180).",
    )
    return parser


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    """Parse, load optional presets, and validate CLI arguments."""
    args = build_parser().parse_args(argv)

    if args.list_presets and (args.preset or args.show_preset):
        raise SystemExit(
            "--list-presets cannot be combined with --preset or --show-preset."
        )
    if args.show_preset and args.preset:
        raise SystemExit("--show-preset cannot be combined with --preset.")
    if args.list_presets or args.show_preset:
        return args

    if args.preset:
        preset = load_preset(args.preset, args.preset_dir)
        if args.query is None:
            args.query = preset["query"]
        if args.max_results is None:
            args.max_results = preset.get("max_results", DEFAULT_MAX_RESULTS)
        if args.preview is None:
            args.preview = preset.get("preview", DEFAULT_PREVIEW)
        if args.report_format is None:
            args.report_format = preset.get("report_format", "json")
        if args.candidate_category is None:
            args.candidate_category = preset.get("candidate_categories")
        if args.candidate_older_than is None:
            args.candidate_older_than = preset.get("candidate_older_than", 180)

    args.max_results = (
        DEFAULT_MAX_RESULTS if args.max_results is None else args.max_results
    )
    args.preview = DEFAULT_PREVIEW if args.preview is None else args.preview
    args.report_format = "json" if args.report_format is None else args.report_format
    args.candidate_older_than = (
        180 if args.candidate_older_than is None else args.candidate_older_than
    )

    if not args.query or not args.query.strip():
        raise SystemExit(
            "--query is required unless --preset, --list-presets, or --show-preset is used."
        )
    if args.max_results <= 0:
        raise SystemExit("--max-results must be greater than zero.")
    if args.preview < 0:
        raise SystemExit("--preview cannot be negative.")
    if args.apply and args.preview == 0 and not args.yes:
        raise SystemExit(
            "--preview 0 with --apply requires --yes. "
            "Interactive apply must show at least one preview item."
        )
    if args.yes and not args.apply:
        raise SystemExit("--yes requires --apply.")
    if args.allow_broad_query and not args.apply:
        raise SystemExit("--allow-broad-query requires --apply.")
    if args.analyze and args.apply:
        raise SystemExit("--analyze cannot be combined with --apply.")
    if args.analyze and args.yes:
        raise SystemExit("--analyze is read-only; --yes is not applicable.")
    if not args.analyze and args.report_format != "json":
        raise SystemExit("--report-format requires --analyze.")
    if args.candidate_older_than < 0:
        raise SystemExit("--candidate-older-than cannot be negative.")

    broad_terms = find_broad_query_terms(args.query)
    if broad_terms and args.yes and not args.allow_broad_query:
        selectors = ", ".join(broad_terms)
        raise SystemExit(
            f"--yes with a broad query ({selectors}) requires --allow-broad-query."
        )

    return args

def _confirm_apply(total: int) -> bool:
    """Require an explicit interactive confirmation before mutating Gmail."""
    try:
        answer = input(
            f"Move {total} matching message(s) to Gmail Trash? Type TRASH to confirm: "
        )
    except EOFError:
        return False
    return answer.strip() == "TRASH"


def run(args: argparse.Namespace) -> int:
    """Execute the requested cleanup operation."""
    if args.list_presets:
        names = list_presets(args.preset_dir)
        if names:
            print("\n".join(names))
        return 0

    if args.show_preset:
        print(preset_to_toml(args.show_preset, args.preset_dir), end="")
        return 0

    service = build_service(args.credentials, args.token)
    message_ids = search_message_ids(service, args.query, args.max_results)

    if args.analyze:
        observations = fetch_observations(service, message_ids)
        result = analyze_observations(
            observations,
            now=datetime.now(UTC),
            candidate_categories=tuple(args.candidate_category or ("promotions",)),
            candidate_older_than_days=args.candidate_older_than,
        )
        report = build_analysis_report(
            query=args.query,
            matched=len(message_ids),
            analysis=result,
        )
        if args.report_format == "human":
            print(render_analysis_human(report))
        else:
            print(render_json(report))
        return 0

    print(f"Query: {args.query}")
    print(f"Matched: {len(message_ids)} message(s)")
    print(f"Mode: {'APPLY' if args.apply else 'DRY RUN'}")

    for message_id in message_ids[: args.preview]:
        subject, sender = fetch_metadata(service, message_id)
        print(f"- {subject} | {sender}")

    remaining = len(message_ids) - args.preview
    if remaining > 0:
        print(f"- ... and {remaining} more")

    if not message_ids:
        return 0

    if not args.apply:
        print("No changes made. Re-run with --apply to move these messages to Trash.")
        return 0

    broad_terms = find_broad_query_terms(args.query)
    if broad_terms:
        selectors = ", ".join(broad_terms)
        print(
            f"WARNING: broad query selector(s) detected: {selectors}. "
            "This can include important mail outside a narrow cleanup target. "
            "Review the preview carefully."
        )

    if not args.yes and not _confirm_apply(len(message_ids)):
        print("Cancelled. No changes made.")
        return 0

    execution = move_to_trash_detailed(service, message_ids)
    verification = verify_trashed(service, execution.moved_ids)
    report = build_cleanup_report(
        query=args.query,
        matched=len(message_ids),
        execution=execution,
        verification=verification,
    )
    print(render_cleanup_human(report))
    if execution.failed or any(item.state != "verified" for item in verification):
        return 1
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    """CLI entry point with user-friendly error handling."""
    try:
        args = parse_args(argv)
        return run(args)
    except FileNotFoundError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    except (RuntimeError, GoogleAuthError, HttpError) as exc:
        print(f"error: Gmail operation failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
