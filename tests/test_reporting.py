import json
import unittest

from gmail_cleaner.analysis import MailboxAnalysis, ReviewCandidate
from gmail_cleaner.reporting import (
    REPORT_SCHEMA_VERSION,
    build_analysis_report,
    render_analysis_human,
    render_json,
)


class ReportingTests(unittest.TestCase):
    def make_analysis(self):
        return MailboxAnalysis(
            total_messages=2,
            sender_counts={"news@example.com": 2},
            category_counts={"promotions": 2},
            age_bucket_counts={"180-365d": 1, "365d+": 1},
            candidates=(
                ReviewCandidate(
                    message_id="m1",
                    sender_email="news@example.com",
                    subject="Old newsletter",
                    age_days=200,
                    categories=("promotions",),
                    reasons=("age:180d+", "category:promotions"),
                ),
            ),
        )

    def test_analysis_report_has_schema_metadata(self):
        report = build_analysis_report(
            query="category:promotions",
            matched=2,
            analysis=self.make_analysis(),
        )

        self.assertEqual(report["schema_version"], REPORT_SCHEMA_VERSION)
        self.assertEqual(report["report_type"], "analysis")
        self.assertEqual(report["query"], "category:promotions")
        self.assertEqual(report["matched"], 2)
        self.assertEqual(report["analysis"]["total_messages"], 2)

    def test_json_renderer_is_deterministic_json(self):
        report = build_analysis_report(
            query="category:promotions",
            matched=2,
            analysis=self.make_analysis(),
        )

        rendered = render_json(report)
        parsed = json.loads(rendered)

        self.assertEqual(parsed, report)
        self.assertEqual(rendered, render_json(report))

    def test_human_renderer_contains_operator_summary(self):
        report = build_analysis_report(
            query="category:promotions",
            matched=2,
            analysis=self.make_analysis(),
        )

        rendered = render_analysis_human(report)

        self.assertIn("Mode: READ-ONLY ANALYSIS", rendered)
        self.assertIn("Matched: 2 message(s)", rendered)
        self.assertIn("Candidates: 1", rendered)
        self.assertIn("news@example.com | Old newsletter | 200d", rendered)
        self.assertIn("age:180d+, category:promotions", rendered)


if __name__ == "__main__":
    unittest.main()
