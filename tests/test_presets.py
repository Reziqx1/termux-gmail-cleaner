import tempfile
import unittest
from pathlib import Path

from gmail_cleaner.presets import (
    list_presets,
    load_preset,
    preset_path,
    preset_to_toml,
    validate_preset_name,
)


class PresetTests(unittest.TestCase):
    def write_preset(self, directory, name="old-promotions", text=None):
        path = Path(directory) / f"{name}.toml"
        path.write_text(
            text
            or 'query = "category:promotions older_than:1y"\n'
            "max_results = 100\n"
            "preview = 25\n"
            'candidate_categories = ["promotions"]\n'
            "candidate_older_than = 180\n"
            'report_format = "json"\n',
            encoding="utf-8",
        )
        return path

    def test_validates_safe_name(self):
        self.assertEqual(validate_preset_name("old-promotions.v1"), "old-promotions.v1")
        with self.assertRaises(ValueError):
            validate_preset_name("../secrets")
        with self.assertRaises(ValueError):
            validate_preset_name("")

    def test_loads_and_normalizes_valid_preset(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.write_preset(tmp)
            result = load_preset("old-promotions", Path(tmp))
        self.assertEqual(result["query"], "category:promotions older_than:1y")
        self.assertEqual(result["max_results"], 100)
        self.assertEqual(result["preview"], 25)
        self.assertEqual(result["candidate_categories"], ["promotions"])
        self.assertEqual(result["candidate_older_than"], 180)
        self.assertEqual(result["report_format"], "json")

    def test_rejects_unknown_fields(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.write_preset(
                tmp,
                text='query = "from:example.com"\nsecret = "no"\n',
            )
            with self.assertRaises(ValueError):
                load_preset("old-promotions", Path(tmp))

    def test_rejects_invalid_types(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.write_preset(
                tmp,
                text='query = "from:example.com"\nmax_results = true\n',
            )
            with self.assertRaises(TypeError):
                load_preset("old-promotions", Path(tmp))

    def test_rejects_missing_query(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.write_preset(tmp, text="preview = 10\n")
            with self.assertRaises(ValueError):
                load_preset("old-promotions", Path(tmp))

    def test_lists_deterministically(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.write_preset(tmp, "zeta")
            self.write_preset(tmp, "alpha")
            Path(tmp, "README.txt").write_text("ignore", encoding="utf-8")
            self.assertEqual(list_presets(Path(tmp)), ["alpha", "zeta"])

    def test_missing_preset_has_clear_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(FileNotFoundError) as context:
                load_preset("missing", Path(tmp))
        self.assertIn("Preset not found", str(context.exception))

    def test_preset_path_is_contained_by_directory(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = preset_path("safe-name", Path(tmp))
            self.assertEqual(path, Path(tmp) / "safe-name.toml")

    def test_preset_to_toml_validates_before_returning_content(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.write_preset(tmp)
            content = preset_to_toml("old-promotions", Path(tmp))
        self.assertIn('query = "category:promotions older_than:1y"', content)


if __name__ == "__main__":
    unittest.main()
