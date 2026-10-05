"""Pure, read-only mailbox analysis primitives for v0.2."""

from collections import Counter
from dataclasses import dataclass
from datetime import UTC, datetime
from email import utils as email_utils


CATEGORY_LABELS = {
    "CATEGORY_PRIMARY": "primary",
    "CATEGORY_SOCIAL": "social",
    "CATEGORY_PROMOTIONS": "promotions",
    "CATEGORY_UPDATES": "updates",
    "CATEGORY_FORUMS": "forums",
}

AGE_BUCKETS = (
    (0, 7, "0-7d"),
    (7, 30, "7-30d"),
    (30, 90, "30-90d"),
    (90, 180, "90-180d"),
    (180, 365, "180-365d"),
)


@dataclass(frozen=True)
class MessageObservation:
    """Normalized metadata required for mailbox analysis."""

    message_id: str
    thread_id: str
    sender_name: str
    sender_email: str
    subject: str
    internal_date: datetime
    label_ids: tuple[str, ...]


@dataclass(frozen=True)
class ReviewCandidate:
    """A review signal, never an instruction to mutate Gmail."""

    message_id: str
    reasons: tuple[str, ...]


@dataclass(frozen=True)
class MailboxAnalysis:
    """Deterministic aggregate analysis result."""

    total_messages: int
    sender_counts: dict[str, int]
    category_counts: dict[str, int]
    age_bucket_counts: dict[str, int]
    candidates: tuple[ReviewCandidate, ...]

    def to_dict(self) -> dict[str, object]:
        """Return a JSON-serializable representation."""
        return {
            "total_messages": self.total_messages,
            "sender_counts": dict(self.sender_counts),
            "category_counts": dict(self.category_counts),
            "age_bucket_counts": dict(self.age_bucket_counts),
            "candidates": [
                {"message_id": item.message_id, "reasons": list(item.reasons)}
                for item in self.candidates
            ],
        }


def normalize_sender(raw_from: str) -> tuple[str, str]:
    """Normalize a Gmail From header into display name and lowercase address."""
    display_name, address = email_utils.parseaddr(raw_from)
    display_name = display_name.strip()
    address = address.strip()

    if "@" in address:
        return display_name or address, address.lower()

    raw_name = raw_from.strip()
    return raw_name or "(unknown sender)", "(unknown)"


def categories_from_labels(label_ids: tuple[str, ...] | list[str]) -> tuple[str, ...]:
    """Return known Gmail categories in stable label order."""
    return tuple(
        CATEGORY_LABELS[label]
        for label in label_ids
        if label in CATEGORY_LABELS
    )


def age_bucket(internal_date: datetime, now: datetime) -> str:
    """Place a message into a deterministic age bucket."""
    if internal_date.tzinfo is None or now.tzinfo is None:
        raise ValueError("internal_date and now must be timezone-aware")

    age_days = max(0, (now - internal_date).total_seconds() / 86400)

    for lower, upper, label in AGE_BUCKETS:
        if lower <= age_days < upper:
            return label

    return "365d+"


def analyze_observations(
    observations: list[MessageObservation] | tuple[MessageObservation, ...],
    *,
    now: datetime,
    candidate_categories: tuple[str, ...] = ("promotions",),
    candidate_older_than_days: int = 180,
) -> MailboxAnalysis:
    """Analyze normalized metadata without performing any network or mutation."""
    if now.tzinfo is None:
        raise ValueError("now must be timezone-aware")
    if candidate_older_than_days < 0:
        raise ValueError("candidate_older_than_days cannot be negative")

    sender_counts = Counter(item.sender_email for item in observations)
    category_counts: Counter[str] = Counter()
    age_counts: Counter[str] = Counter()
    candidates: list[ReviewCandidate] = []
    wanted_categories = set(candidate_categories)

    for item in observations:
        categories = categories_from_labels(item.label_ids)
        if categories:
            category_counts.update(categories)
        else:
            category_counts["uncategorized"] += 1

        age_counts[age_bucket(item.internal_date, now)] += 1

        age_days = max(0, (now - item.internal_date).total_seconds() / 86400)
        reasons: list[str] = []

        for category in categories:
            if category in wanted_categories:
                reasons.append(f"category:{category}")

        if age_days >= candidate_older_than_days:
            reasons.append(f"age:{candidate_older_than_days}d+")

        if len(reasons) >= 2:
            candidates.append(
                ReviewCandidate(
                    message_id=item.message_id,
                    reasons=tuple(sorted(reasons)),
                )
            )

    return MailboxAnalysis(
        total_messages=len(observations),
        sender_counts=dict(sender_counts),
        category_counts=dict(category_counts),
        age_bucket_counts=dict(age_counts),
        candidates=tuple(candidates),
    )


def gmail_internal_date_to_datetime(internal_date_ms: str | int) -> datetime:
    """Convert Gmail's millisecond internal date to an aware UTC datetime."""
    milliseconds = int(internal_date_ms)
    return datetime.fromtimestamp(milliseconds / 1000, tz=UTC)
