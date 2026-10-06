import tempfile
import unittest
from pathlib import Path

from gmail_cleaner.cli import parse_args
from gmail_cleaner.presets import (
    list_presets,
    load_preset,
    preset_path,
    write_example_preset,
)


class PresetTests(unittest.TestCase):
    def test_write_and_load_example_preset(self):
        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp)
            path = write_example_preset("old-promotions", preset_dir=directory)

            self.assertEqual(path, preset_path("old-promotions", directory))
            self.assertEqual(
                load_preset("old-promotions", directory)["query"],
                "category:promotions older_than:1y",
            )
            self.assertEqual(list_presets(directory), ["old-promotions"])

    def test_invalid_preset_name_fails_closed(self):
        with (
            tempfile.TemporaryDirectory() as tmp,
            self.assertRaises(ValueError),
        ):
            preset_path("../unsafe", Path(tmp))

    def test_unknown_field_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "bad.toml"
            path.write_text(
                'query = "category:promotions"\n'
                'unexpected = "nope"\n',
                encoding="utf-8",
            )
            with self.assertRaises(ValueError):
                load_preset("bad", Path(tmp))

    def test_missing_query_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "bad.toml"
            path.write_text("preview = 5\n", encoding="utf-8")
            with self.assertRaises(ValueError):
                load_preset("bad", Path(tmp))

    def test_wrong_type_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "bad.toml"
            path.write_text(
                'query = "category:promotions"\n'
                'preview = "five"\n',
                encoding="utf-8",
            )
            with self.assertRaises(TypeError):
                load_preset("bad", Path(tmp))

    def test_cli_loads_preset_values(self):
        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp)
            write_example_preset("old-promotions", preset_dir=directory)

            args = parse_args(
                [
                    "--preset",
                    "old-promotions",
                    "--preset-dir",
                    str(directory),
                ]
            )

            self.assertEqual(args.query, "category:promotions older_than:1y")
            self.assertEqual(args.max_results, 100)
            self.assertEqual(args.preview, 25)
            self.assertEqual(args.candidate_category, ["promotions"])
            self.assertEqual(args.candidate_older_than, 180)
            self.assertEqual(args.report_format, "json")

    def test_cli_explicit_values_override_preset(self):
        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp)
            write_example_preset("old-promotions", preset_dir=directory)

            args = parse_args(
                [
                    "--preset",
                    "old-promotions",
                    "--preset-dir",
                    str(directory),
                    "--max-results",
                    "5",
                    "--preview",
                    "2",
                    "--report-format",
                    "human",
                ]
            )

            self.assertEqual(args.query, "category:promotions older_than:1y")
            self.assertEqual(args.max_results, 5)
            self.assertEqual(args.preview, 2)
            self.assertEqual(args.report_format, "human")

    def test_query_override_works(self):
        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp)
            write_example_preset("old-promotions", preset_dir=directory)

            args = parse_args(
                [
                    "--preset",
                    "old-promotions",
                    "--preset-dir",
                    str(directory),
                    "--query",
                    "from:example.com",
                ]
            )

            self.assertEqual(args.query, "from:example.com")

    def test_preset_does_not_bypass_apply_gate(self):
        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp)
            write_example_preset("old-promotions", preset_dir=directory)

            args = parse_args(
                [
                    "--preset",
                    "old-promotions",
                    "--preset-dir",
                    str(directory),
                ]
            )

            self.assertFalse(args.apply)
            self.assertFalse(args.yes)


if __name__ == "__main__":
    unittest.main()
