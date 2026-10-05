import unittest
from datetime import UTC, datetime, timedelta

from gmail_cleaner.analysis import (
    MessageObservation,
    age_bucket,
    analyze_observations,
    categories_from_labels,
    gmail_internal_date_to_datetime,
    normalize_sender,
)


class AnalysisTests(unittest.TestCase):
    NOW = datetime(2026, 10, 5, 12, tzinfo=UTC)

    def make_message(
        self,
        *,
        message_id="m1",
        sender_email="news@example.com",
        age_days=200,
        label_ids=("CATEGORY_PROMOTIONS",),
        subject="Example subject",
    ):
        return MessageObservation(
            message_id=message_id,
            thread_id=f"t-{message_id}",
            sender_name="Example",
            sender_email=sender_email,
            subject=subject,
            internal_date=self.NOW - timedelta(days=age_days),
            label_ids=tuple(label_ids),
        )

    def test_normalize_sender(self):
        self.assertEqual(
            normalize_sender("Example News <NEWS@Example.com>"),
            ("Example News", "news@example.com"),
        )

    def test_normalize_sender_without_name(self):
        self.assertEqual(
            normalize_sender("NEWS@Example.com"),
            ("NEWS@Example.com", "news@example.com"),
        )

    def test_normalize_sender_without_address(self):
        self.assertEqual(
            normalize_sender("Unknown Sender"),
            ("Unknown Sender", "(unknown)"),
        )

    def test_categories_extract_known_labels_only(self):
        self.assertEqual(
            categories_from_labels(("INBOX", "CATEGORY_SOCIAL", "CATEGORY_PROMOTIONS")),
            ("social", "promotions"),
        )

    def test_age_bucket_uses_aware_datetimes(self):
        self.assertEqual(
            age_bucket(self.NOW - timedelta(days=10), self.NOW),
            "7-30d",
        )
        self.assertEqual(
            age_bucket(self.NOW - timedelta(days=400), self.NOW),
            "365d+",
        )

    def test_age_bucket_rejects_naive_datetime(self):
        with self.assertRaises(ValueError):
            age_bucket(datetime.fromisoformat("2026-01-01T00:00:00"), self.NOW)

    def test_gmail_internal_date_conversion(self):
        dt = gmail_internal_date_to_datetime("0")
        self.assertEqual(dt, datetime(1970, 1, 1, tzinfo=UTC))

    def test_analysis_is_deterministic_and_structured(self):
        observations = [
            self.make_message(message_id="m1", age_days=200),
            self.make_message(
                message_id="m2",
                sender_email="other@example.com",
                age_days=20,
                label_ids=("CATEGORY_PRIMARY",),
            ),
            self.make_message(
                message_id="m3",
                sender_email="news@example.com",
                age_days=400,
                label_ids=("CATEGORY_PROMOTIONS",),
            ),
        ]

        result = analyze_observations(
            observations,
            now=self.NOW,
            candidate_older_than_days=180,
        )

        self.assertEqual(result.total_messages, 3)
        self.assertEqual(result.sender_counts["news@example.com"], 2)
        self.assertEqual(result.category_counts["promotions"], 2)
        self.assertEqual(result.category_counts["primary"], 1)
        self.assertEqual(result.age_bucket_counts["180-365d"], 1)
        self.assertEqual(result.age_bucket_counts["365d+"], 1)
        self.assertEqual(
            [candidate.message_id for candidate in result.candidates],
            ["m1", "m3"],
        )
        self.assertEqual(
            result.candidates[0].reasons,
            ("age:180d+", "category:promotions"),
        )
        self.assertEqual(
            result.candidates[0].sender_email,
            "news@example.com",
        )
        self.assertEqual(
            result.candidates[0].subject,
            "Example subject",
        )
        self.assertEqual(result.candidates[0].age_days, 200)
        self.assertEqual(result.candidates[0].categories, ("promotions",))
        self.assertEqual(
            result.to_dict()["candidates"],
            [
                {
                    "age_days": 200,
                    "categories": ["promotions"],
                    "message_id": "m1",
                    "reasons": ["age:180d+", "category:promotions"],
                    "sender_email": "news@example.com",
                    "subject": "Example subject",
                },
                {
                    "age_days": 400,
                    "categories": ["promotions"],
                    "message_id": "m3",
                    "reasons": ["age:180d+", "category:promotions"],
                    "sender_email": "news@example.com",
                    "subject": "Example subject",
                },
            ],
        )

    def test_candidate_is_excluded_when_only_age_matches(self):
        result = analyze_observations(
            [self.make_message(label_ids=("CATEGORY_PRIMARY",), age_days=500)],
            now=self.NOW,
            candidate_older_than_days=180,
        )
        self.assertEqual(result.candidates, ())

    def test_candidate_matches_exact_age_boundary(self):
        result = analyze_observations(
            [self.make_message(age_days=180)],
            now=self.NOW,
            candidate_older_than_days=180,
        )
        self.assertEqual([item.message_id for item in result.candidates], ["m1"])

    def test_analysis_supports_empty_input(self):
        result = analyze_observations([], now=self.NOW)
        self.assertEqual(result.total_messages, 0)
        self.assertEqual(result.sender_counts, {})
        self.assertEqual(result.candidates, ())

    def test_analysis_rejects_invalid_candidate_age(self):
        with self.assertRaises(ValueError):
            analyze_observations(
                [],
                now=self.NOW,
                candidate_older_than_days=-1,
            )


if __name__ == "__main__":
    unittest.main()
