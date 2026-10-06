import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from gmail_cleaner.paths import config_dir, credentials_path, preset_dir, token_path


class PathResolutionTests(unittest.TestCase):
    def test_default_config_dir_is_under_home(self):
        with patch.dict(os.environ, {}, clear=True):
            self.assertEqual(
                config_dir(),
                Path.home() / ".config" / "gmail-cleaner",
            )

    def test_config_dir_environment_override_wins(self):
        with patch.dict(
            os.environ,
            {"GMAIL_CLEANER_CONFIG_DIR": "~/custom/gmail-cleaner"},
            clear=True,
        ):
            self.assertEqual(
                config_dir(),
                Path("~/custom/gmail-cleaner").expanduser(),
            )

    def test_credentials_and_token_use_config_defaults(self):
        with patch.dict(os.environ, {}, clear=True):
            self.assertEqual(
                credentials_path(),
                Path.home() / ".config" / "gmail-cleaner" / "credentials.json",
            )
            self.assertEqual(
                token_path(),
                Path.home() / ".config" / "gmail-cleaner" / "token.json",
            )

    def test_specific_environment_paths_override_config_dir(self):
        with patch.dict(
            os.environ,
            {
                "GMAIL_CLEANER_CONFIG_DIR": "~/base",
                "GMAIL_CREDENTIALS": "~/explicit/credentials.json",
                "GMAIL_TOKEN": "~/explicit/token.json",
                "GMAIL_CLEANER_PRESET_DIR": "~/explicit/presets",
            },
            clear=True,
        ):
            self.assertEqual(
                credentials_path(),
                Path("~/explicit/credentials.json").expanduser(),
            )
            self.assertEqual(
                token_path(),
                Path("~/explicit/token.json").expanduser(),
            )
            self.assertEqual(
                preset_dir(),
                Path("~/explicit/presets").expanduser(),
            )

    def test_explicit_cli_path_wins_over_environment(self):
        with patch.dict(
            os.environ,
            {"GMAIL_CREDENTIALS": "~/env/credentials.json"},
            clear=True,
        ):
            self.assertEqual(
                credentials_path(Path("~/cli/credentials.json")),
                Path("~/cli/credentials.json").expanduser(),
            )

    def test_preset_dir_defaults_beneath_config_dir(self):
        with patch.dict(
            os.environ,
            {"GMAIL_CLEANER_CONFIG_DIR": "~/custom"},
            clear=True,
        ):
            self.assertEqual(
                preset_dir(),
                Path("~/custom/presets").expanduser(),
            )

    def test_path_helpers_do_not_create_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            custom = Path(tmp) / "config"
            with patch.dict(
                os.environ,
                {"GMAIL_CLEANER_CONFIG_DIR": str(custom)},
                clear=True,
            ):
                _ = config_dir()
                _ = credentials_path()
                _ = token_path()
                _ = preset_dir()
            self.assertFalse(custom.exists())


if __name__ == "__main__":
    unittest.main()
