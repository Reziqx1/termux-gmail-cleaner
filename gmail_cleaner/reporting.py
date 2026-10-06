"""Operator-facing report construction and rendering for v0.3."""

from __future__ import annotations

import json
from collections.abc import Mapping
from typing import Any

from .analysis import MailboxAnalysis

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
            f"  - {name}: {count}"
            for name, count in sorted(age_bucket_counts.items())
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
