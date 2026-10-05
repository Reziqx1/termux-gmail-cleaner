import io
import json
import unittest
from contextlib import redirect_stdout
from unittest.mock import MagicMock, patch

from gmail_cleaner.cli import main, parse_args

class AnalyzeCliTests(unittest.TestCase):
    def test_parser_accepts_analysis_options(self):
        args = parse_args(
            [
                "--query",
                "category:promotions",
                "--analyze",
                "--candidate-category",
                "promotions",
                "--candidate-older-than",
                "90",
            ]
        )
        self.assertTrue(args.analyze)
        self.assertEqual(args.candidate_category, ["promotions"])
        self.assertEqual(args.candidate_older_than, 90)

    def test_parser_rejects_analysis_with_apply(self):
        with self.assertRaises(SystemExit):
            parse_args(
                ["--query", "category:promotions", "--analyze", "--apply"]
            )

    def test_parser_rejects_analysis_with_yes(self):
        with self.assertRaises(SystemExit):
            parse_args(
                ["--query", "category:promotions", "--analyze", "--yes"]
            )

    def test_analysis_command_is_read_only_and_outputs_json(self):
        service = MagicMock()
        service.users.return_value.messages.return_value.list.return_value.execute.return_value = {
            "messages": [{"id": "m1"}]
        }
        service.users.return_value.messages.return_value.get.return_value.execute.return_value = {
            "id": "m1",
            "threadId": "t1",
            "internalDate": "0",
            "labelIds": ["CATEGORY_PRIMARY"],
            "payload": {
                "headers": [
                    {"name": "Subject", "value": "Hello"},
                    {"name": "From", "value": "News <news@example.com>"},
                ]
            },
        }

        stdout = io.StringIO()
        with patch("gmail_cleaner.cli.build_service", return_value=service):
            with redirect_stdout(stdout):
                self.assertEqual(
                    main(
                        [
                            "--query",
                            "category:promotions",
                            "--analyze",
                            "--max-results",
                            "1",
                        ]
                    ),
                    0,
                )

        report = json.loads(stdout.getvalue())
        self.assertEqual(report["query"], "category:promotions")
        self.assertEqual(report["matched"], 1)
        self.assertEqual(report["analysis"]["total_messages"], 1)
        self.assertEqual(report["analysis"]["sender_counts"], {"news@example.com": 1})
        service.users.return_value.messages.return_value.batchModify.assert_not_called()


if __name__ == "__main__":
    unittest.main()
