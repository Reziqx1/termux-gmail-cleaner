import json
import unittest

from gmail_cleaner.analysis import MailboxAnalysis, ReviewCandidate
from gmail_cleaner.mutation import BatchOutcome, MutationExecution
from gmail_cleaner.reporting import (
    REPORT_SCHEMA_VERSION,
    build_analysis_report,
    build_cleanup_report,
    render_analysis_human,
    render_cleanup_human,
    render_json,
)
from gmail_cleaner.verifier import VerificationResult


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

    def test_cleanup_report_marks_success_and_verification(self):
        execution = MutationExecution(
            batches=(
                BatchOutcome(
                    batch_index=1,
                    requested=2,
                    message_ids=("m1", "m2"),
                    succeeded=True,
                ),
            )
        )
        verification = (
            VerificationResult("m1", "verified"),
            VerificationResult("m2", "verified"),
        )

        report = build_cleanup_report(
            query="category:promotions older_than:1y",
            matched=2,
            execution=execution,
            verification=verification,
        )

        self.assertEqual(report["report_type"], "cleanup")
        self.assertEqual(report["mutation"]["status"], "success")
        self.assertEqual(report["mutation"]["moved"], 2)
        self.assertEqual(report["verification"]["status"], "verified")
        self.assertEqual(report["verification"]["verified"], 2)

    def test_cleanup_report_marks_partial_mutation(self):
        execution = MutationExecution(
            batches=(
                BatchOutcome(
                    batch_index=1,
                    requested=2,
                    message_ids=("m1", "m2"),
                    succeeded=True,
                ),
                BatchOutcome(
                    batch_index=2,
                    requested=2,
                    message_ids=("m3", "m4"),
                    succeeded=False,
                    error="HttpError",
                ),
            )
        )
        verification = (
            VerificationResult("m1", "verified"),
            VerificationResult("m2", "not-verified", "TRASH label is absent"),
        )

        report = build_cleanup_report(
            query="category:promotions older_than:1y",
            matched=4,
            execution=execution,
            verification=verification,
        )

        self.assertEqual(report["mutation"]["status"], "partial")
        self.assertEqual(report["mutation"]["moved"], 2)
        self.assertEqual(report["verification"]["status"], "incomplete")
        self.assertEqual(report["verification"]["not_verified"], 1)
        self.assertEqual(report["mutation"]["batches"][1]["succeeded"], False)

    def test_cleanup_human_renderer_explains_batch_and_verification_state(self):
        execution = MutationExecution(
            batches=(
                BatchOutcome(
                    batch_index=1,
                    requested=2,
                    message_ids=("m1", "m2"),
                    succeeded=True,
                ),
            )
        )
        verification = (
            VerificationResult("m1", "verified"),
            VerificationResult("m2", "verified"),
        )
        report = build_cleanup_report(
            query="category:promotions",
            matched=2,
            execution=execution,
            verification=verification,
        )

        rendered = render_cleanup_human(report)

        self.assertIn("Mode: APPLY", rendered)
        self.assertIn("Mutation: success", rendered)
        self.assertIn("Moved: 2/2", rendered)
        self.assertIn("Verification: verified", rendered)
        self.assertIn("#1: OK (2 message(s))", rendered)


if __name__ == "__main__":
    unittest.main()
