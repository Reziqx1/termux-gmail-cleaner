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
        self.assertEqual(args.report_format, "json")

    def test_parser_accepts_human_report_format(self):
        args = parse_args(
            [
                "--query",
                "category:promotions",
                "--analyze",
                "--report-format",
                "human",
            ]
        )
        self.assertEqual(args.report_format, "human")

    def test_parser_rejects_analysis_with_apply(self):
        with self.assertRaises(SystemExit):
            parse_args(["--query", "category:promotions", "--analyze", "--apply"])

    def test_parser_rejects_analysis_with_yes(self):
        with self.assertRaises(SystemExit):
            parse_args(["--query", "category:promotions", "--analyze", "--yes"])

    def test_parser_rejects_human_report_without_analysis(self):
        with self.assertRaises(SystemExit):
            parse_args(
                [
                    "--query",
                    "category:promotions",
                    "--report-format",
                    "human",
                ]
            )

    def build_service(self):
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
        return service

    def test_analysis_command_is_read_only_and_outputs_json(self):
        service = self.build_service()

        stdout = io.StringIO()
        with (
            patch("gmail_cleaner.cli.build_service", return_value=service),
            redirect_stdout(stdout),
        ):
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
        self.assertEqual(report["schema_version"], "0.3")
        self.assertEqual(report["report_type"], "analysis")
        self.assertEqual(report["query"], "category:promotions")
        self.assertEqual(report["matched"], 1)
        self.assertEqual(report["analysis"]["total_messages"], 1)
        self.assertEqual(
            report["analysis"]["sender_counts"],
            {"news@example.com": 1},
        )
        service.users.return_value.messages.return_value.batchModify.assert_not_called()

    def test_analysis_command_can_render_human_report(self):
        service = self.build_service()

        stdout = io.StringIO()
        with (
            patch("gmail_cleaner.cli.build_service", return_value=service),
            redirect_stdout(stdout),
        ):
            self.assertEqual(
                main(
                    [
                        "--query",
                        "category:promotions",
                        "--analyze",
                        "--report-format",
                        "human",
                        "--max-results",
                        "1",
                    ]
                ),
                0,
            )

        output = stdout.getvalue()
        self.assertIn("Mode: READ-ONLY ANALYSIS", output)
        self.assertIn("Matched: 1 message(s)", output)
        self.assertIn("Review candidates: none", output)
        service.users.return_value.messages.return_value.batchModify.assert_not_called()

    def test_parser_loads_preset_values(self):
        import tempfile
        from pathlib import Path

        with tempfile.TemporaryDirectory() as tmp:
            Path(tmp, "old-promotions.toml").write_text(
                'query = "category:promotions older_than:1y"\n'
                "max_results = 100\n"
                "preview = 25\n"
                'candidate_categories = ["promotions"]\n'
                "candidate_older_than = 180\n"
                'report_format = "human"\n',
                encoding="utf-8",
            )
            args = parse_args(
                [
                    "--preset",
                    "old-promotions",
                    "--preset-dir",
                    tmp,
                    "--analyze",
                ]
            )

        self.assertEqual(args.query, "category:promotions older_than:1y")
        self.assertEqual(args.max_results, 100)
        self.assertEqual(args.preview, 25)
        self.assertEqual(args.candidate_category, ["promotions"])
        self.assertEqual(args.candidate_older_than, 180)
        self.assertEqual(args.report_format, "human")

    def test_cli_overrides_preset_values(self):
        import tempfile
        from pathlib import Path

        with tempfile.TemporaryDirectory() as tmp:
            Path(tmp, "preset.toml").write_text(
                'query = "category:promotions"\nmax_results = 100\npreview = 25\n',
                encoding="utf-8",
            )
            args = parse_args(
                [
                    "--preset",
                    "preset",
                    "--preset-dir",
                    tmp,
                    "--query",
                    "from:example.com",
                    "--max-results",
                    "5",
                    "--preview",
                    "2",
                ]
            )

        self.assertEqual(args.query, "from:example.com")
        self.assertEqual(args.max_results, 5)
        self.assertEqual(args.preview, 2)

    def test_list_presets_can_run_without_gmail_service(self):
        import tempfile
        from pathlib import Path

        with tempfile.TemporaryDirectory() as tmp:
            Path(tmp, "zeta.toml").write_text('query = "from:zeta@example.com"\n')
            Path(tmp, "alpha.toml").write_text('query = "from:alpha@example.com"\n')
            stdout = io.StringIO()
            with redirect_stdout(stdout):
                self.assertEqual(
                    main(["--list-presets", "--preset-dir", tmp]),
                    0,
                )

        self.assertEqual(stdout.getvalue().splitlines(), ["alpha", "zeta"])

    def test_show_preset_can_run_without_gmail_service(self):
        import tempfile
        from pathlib import Path

        with tempfile.TemporaryDirectory() as tmp:
            Path(tmp, "preset.toml").write_text('query = "from:example.com"\n')
            stdout = io.StringIO()
            with redirect_stdout(stdout):
                self.assertEqual(
                    main(
                        [
                            "--show-preset",
                            "preset",
                            "--preset-dir",
                            tmp,
                        ]
                    ),
                    0,
                )

        self.assertIn('query = "from:example.com"', stdout.getvalue())


if __name__ == "__main__":
    unittest.main()
