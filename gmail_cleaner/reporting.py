"""Operator-facing report construction and rendering for v0.3."""

from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from typing import Any

from .analysis import MailboxAnalysis
from .mutation import MutationExecution
from .verifier import VerificationResult

REPORT_SCHEMA_VERSION = "0.3"


def build_analysis_report(
    *,
    query: str,
    matched: int,
    analysis: MailboxAnalysis,
) -> dict[str, Any]:
    """Build a stable, machine-readable read-only analysis report."""
    return {
        "schema_version": REPORT_SCHEMA_VERSION,
        "report_type": "analysis",
        "query": query,
        "matched": matched,
        "analysis": analysis.to_dict(),
    }


def build_cleanup_report(
    *,
    query: str,
    matched: int,
    execution: MutationExecution,
    verification: Sequence[VerificationResult],
) -> dict[str, Any]:
    """Build a stable report for a Trash mutation and its verification."""
    verification_items = [
        {
            "message_id": item.message_id,
            "state": item.state,
            **({"detail": item.detail} if item.detail else {}),
        }
        for item in verification
    ]

    verified_count = sum(item.state == "verified" for item in verification)
    not_verified_count = sum(item.state == "not-verified" for item in verification)
    error_count = sum(item.state == "verification-error" for item in verification)

    if not execution.moved_ids:
        verification_status = "not-run"
    elif error_count == len(verification):
        verification_status = "verification-error"
    elif verified_count == len(verification):
        verification_status = "verified"
    else:
        verification_status = "incomplete"

    if not execution.batches:
        mutation_status = "no-op"
    elif execution.failed:
        mutation_status = "partial" if execution.moved_count else "failed"
    else:
        mutation_status = "success"

    return {
        "schema_version": REPORT_SCHEMA_VERSION,
        "report_type": "cleanup",
        "query": query,
        "matched": matched,
        "mutation": {
            "status": mutation_status,
            "requested": matched,
            "moved": execution.moved_count,
            "batches": [
                {
                    "batch_index": batch.batch_index,
                    "requested": batch.requested,
                    "succeeded": batch.succeeded,
                    **({"error": batch.error} if batch.error else {}),
                }
                for batch in execution.batches
            ],
        },
        "verification": {
            "status": verification_status,
            "checked": len(verification),
            "verified": verified_count,
            "not_verified": not_verified_count,
            "errors": error_count,
            "results": verification_items,
        },
    }


def render_json(report: Mapping[str, Any]) -> str:
    """Render a report as deterministic, human-readable JSON."""
    return json.dumps(report, indent=2, sort_keys=True)


def render_analysis_human(report: Mapping[str, Any]) -> str:
    """Render an analysis report as a concise operator-facing summary."""
    analysis = report.get("analysis", {})
    candidates = analysis.get("candidates", [])
    category_counts = analysis.get("category_counts", {})
    age_bucket_counts = analysis.get("age_bucket_counts", {})

    lines = [
        f"Report schema: {report.get('schema_version', 'unknown')}",
        f"Report type: {report.get('report_type', 'unknown')}",
        "Mode: READ-ONLY ANALYSIS",
        f"Query: {report.get('query', '')}",
        f"Matched: {report.get('matched', 0)} message(s)",
        f"Candidates: {len(candidates)}",
    ]

    if category_counts:
        lines.append("Categories:")
        lines.extend(
            f"  - {name}: {count}" for name, count in sorted(category_counts.items())
        )

    if age_bucket_counts:
        lines.append("Age distribution:")
        lines.extend(
            f"  - {name}: {count}" for name, count in sorted(age_bucket_counts.items())
        )

    if candidates:
        lines.append("Review candidates:")
        for candidate in candidates:
            reasons = ", ".join(candidate.get("reasons", []))
            lines.append(
                "  - "
                f"{candidate.get('sender_email', '(unknown sender)')} | "
                f"{candidate.get('subject', '(no subject)')} | "
                f"{candidate.get('age_days', 0)}d | {reasons}"
            )
    else:
        lines.append("Review candidates: none")

    return "\n".join(lines)


def render_cleanup_human(report: Mapping[str, Any]) -> str:
    """Render a cleanup mutation and verification report for operators."""
    mutation = report.get("mutation", {})
    verification = report.get("verification", {})

    lines = [
        f"Report schema: {report.get('schema_version', 'unknown')}",
        f"Report type: {report.get('report_type', 'unknown')}",
        "Mode: APPLY",
        f"Query: {report.get('query', '')}",
        f"Matched: {report.get('matched', 0)} message(s)",
        f"Mutation: {mutation.get('status', 'unknown')}",
        f"Moved: {mutation.get('moved', 0)}/{mutation.get('requested', 0)}",
        (
            "Verification: "
            f"{verification.get('status', 'unknown')} "
            f"({verification.get('verified', 0)} verified, "
            f"{verification.get('not_verified', 0)} not verified, "
            f"{verification.get('errors', 0)} errors)"
        ),
    ]

    batches = mutation.get("batches", [])
    if batches:
        lines.append("Batches:")
        for batch in batches:
            status = "OK" if batch.get("succeeded") else "FAILED"
            detail = f" | {batch.get('error')}" if batch.get("error") else ""
            lines.append(
                f"  - #{batch.get('batch_index')}: "
                f"{status} ({batch.get('requested', 0)} message(s)){detail}"
            )

    return "\n".join(lines)
