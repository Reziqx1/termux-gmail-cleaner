import io
import tempfile
import unittest
from contextlib import redirect_stderr
from pathlib import Path
from unittest.mock import MagicMock, patch

from googleapiclient.errors import HttpError

from gmail_cleaner import __version__
from gmail_cleaner.cli import (
    BATCH_SIZE,
    GmailMutationError,
    _confirm_apply,
    chunked,
    fetch_metadata,
    find_broad_query_terms,
    get_credentials,
    main,
    move_to_trash,
    parse_args,
    search_message_ids,
)


def make_service():
    messages = FakeMessages(
        list_responses=[{"messages": [{"id": "abc"}]}],
        metadata={
            "payload": {
                "headers": [
                    {"name": "Subject", "value": "Test"},
                    {"name": "From", "value": "Example <test@example.com>"},
                ]
            }
        },
    )
    return messages, FakeService(messages)


class ChunkedTests(unittest.TestCase):
    def test_chunks_list(self):
        self.assertEqual(
            list(chunked(["a", "b", "c", "d", "e"], 2)),
            [["a", "b"], ["c", "d"], ["e"]],
        )

    def test_empty_list(self):
        self.assertEqual(list(chunked([], 100)), [])

    def test_invalid_size(self):
        with self.assertRaises(ValueError):
            list(chunked(["a"], 0))


class FakeMessages:
    def __init__(self, list_responses=None, metadata=None, batch_fail_at=None):
        self.list_responses = list(list_responses or [])
        self.metadata = metadata or {}
        self.batch_fail_at = batch_fail_at
        self.list_calls = []
        self.get_calls = []
        self.batch_calls = []

    def list(self, **kwargs):
        self.list_calls.append(kwargs)
        response = self.list_responses.pop(0)
        request = MagicMock()
        request.execute.return_value = response
        return request

    def get(self, **kwargs):
        self.get_calls.append(kwargs)
        request = MagicMock()
        request.execute.return_value = self.metadata
        return request

    def batchModify(self, **kwargs):
        self.batch_calls.append(kwargs)
        request = MagicMock()
        if self.batch_fail_at == len(self.batch_calls):
            response = MagicMock(status=500, reason="test failure")
            request.execute.side_effect = HttpError(response, b"test failure")
        else:
            request.execute.return_value = {}
        return request


class FakeUsers:
    def __init__(self, messages):
        self._messages = messages

    def messages(self):
        return self._messages


class FakeService:
    def __init__(self, messages):
        self._users = FakeUsers(messages)

    def users(self):
        return self._users


class GmailApiTests(unittest.TestCase):
    def test_search_paginates_and_caps_results(self):
        messages = FakeMessages(
            list_responses=[
                {
                    "messages": [{"id": str(i)} for i in range(3)],
                    "nextPageToken": "next",
                },
                {"messages": [{"id": str(i)} for i in range(3, 6)]},
            ]
        )
        service = FakeService(messages)

        result = search_message_ids(service, "from:test@example.com", 5)

        self.assertEqual(result, ["0", "1", "2", "3", "4"])
        self.assertEqual(len(messages.list_calls), 2)
        self.assertEqual(messages.list_calls[1]["pageToken"], "next")

    def test_metadata_extracts_subject_and_sender(self):
        messages = FakeMessages(
            metadata={
                "payload": {
                    "headers": [
                        {"name": "Subject", "value": "Hello"},
                        {"name": "From", "value": "Example <test@example.com>"},
                    ]
                }
            }
        )
        service = FakeService(messages)

        self.assertEqual(
            fetch_metadata(service, "abc"),
            ("Hello", "Example <test@example.com>"),
        )

    def test_trash_batches_large_inputs(self):
        message_ids = [str(i) for i in range(BATCH_SIZE * 2 + 1)]
        messages = FakeMessages()
        service = FakeService(messages)

        moved = move_to_trash(service, message_ids)

        self.assertEqual(moved, BATCH_SIZE * 2 + 1)
        self.assertEqual(len(messages.batch_calls), 3)
        self.assertEqual(
            [len(call["body"]["ids"]) for call in messages.batch_calls],
            [BATCH_SIZE, BATCH_SIZE, 1],
        )

    def test_trash_reports_partial_failure(self):
        message_ids = [str(i) for i in range(BATCH_SIZE * 2)]
        messages = FakeMessages(batch_fail_at=2)
        service = FakeService(messages)

        with self.assertRaises(GmailMutationError) as context:
            move_to_trash(service, message_ids)

        self.assertIn(
            "batch 2/2 after successfully moving 100 message(s)",
            str(context.exception),
        )
        self.assertEqual(len(messages.batch_calls), 2)

    def test_find_broad_query_terms(self):
        self.assertEqual(
            find_broad_query_terms("in:anywhere newer_than:1d"),
            ["in:anywhere"],
        )
        self.assertEqual(
            find_broad_query_terms("IN:ALL foo label:all"),
            ["in:all", "label:all"],
        )
        self.assertEqual(
            find_broad_query_terms("category:promotions older_than:1y"), []
        )

    def test_parse_args_rejects_broad_yes_without_override(self):
        with self.assertRaises(SystemExit):
            parse_args(
                [
                    "--query",
                    "in:anywhere newer_than:1d",
                    "--apply",
                    "--yes",
                ]
            )

    def test_parse_args_accepts_broad_yes_with_override(self):
        args = parse_args(
            [
                "--query",
                "in:anywhere newer_than:1d",
                "--apply",
                "--yes",
                "--allow-broad-query",
            ]
        )
        self.assertTrue(args.allow_broad_query)

    def test_parse_args_rejects_broad_override_without_apply(self):
        with self.assertRaises(SystemExit):
            parse_args(
                [
                    "--query",
                    "category:promotions",
                    "--allow-broad-query",
                ]
            )

    def test_confirmation_requires_exact_word(self):
        with patch("builtins.input", return_value="TRASH"):
            self.assertTrue(_confirm_apply(3))
        with patch("builtins.input", return_value="trash"):
            self.assertFalse(_confirm_apply(3))

    def test_parse_args_rejects_yes_without_apply(self):
        with self.assertRaises(SystemExit):
            parse_args(["--query", "from:test@example.com", "--yes"])

    def test_cli_version_comes_from_package(self):
        self.assertEqual(__version__, "0.1.0")
        args = parse_args(["--query", "from:test@example.com"])
        self.assertEqual(args.query, "from:test@example.com")

    def test_run_dry_run_never_moves_messages(self):
        from gmail_cleaner.cli import run

        messages, service = make_service()
        args = parse_args(["--query", "from:test@example.com"])

        with patch("gmail_cleaner.cli.build_service", return_value=service):
            self.assertEqual(run(args), 0)

        self.assertEqual(messages.batch_calls, [])

    def test_run_apply_moves_after_confirmation(self):
        from gmail_cleaner.cli import run

        messages, service = make_service()
        args = parse_args(["--query", "from:test@example.com", "--apply"])

        with (
            patch("gmail_cleaner.cli.build_service", return_value=service),
            patch("gmail_cleaner.cli._confirm_apply", return_value=True),
            patch(
                "gmail_cleaner.cli.move_to_trash", return_value=1
            ) as move_to_trash_mock,
        ):
            self.assertEqual(run(args), 0)

        move_to_trash_mock.assert_called_once_with(service, ["abc"])
        self.assertEqual(messages.batch_calls, [])

    def test_main_reports_runtime_errors(self):
        stderr = io.StringIO()
        with (
            patch(
                "gmail_cleaner.cli.build_service",
                side_effect=RuntimeError("test failure"),
            ),
            redirect_stderr(stderr),
        ):
            self.assertEqual(main(["--query", "from:test@example.com"]), 1)

        self.assertIn("Gmail operation failed: test failure", stderr.getvalue())


class OAuthTests(unittest.TestCase):
    def test_missing_client_file_has_clear_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            token_path = Path(tmp) / "token.json"
            credentials_path = Path(tmp) / "credentials.json"

            with self.assertRaises(FileNotFoundError) as context:
                get_credentials(credentials_path, token_path)

        self.assertIn("OAuth client file not found", str(context.exception))

    def test_malformed_token_has_clear_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            token_path = Path(tmp) / "token.json"
            credentials_path = Path(tmp) / "credentials.json"
            token_path.write_text("not-json", encoding="utf-8")

            with (
                patch(
                    "gmail_cleaner.cli.Credentials.from_authorized_user_file",
                    side_effect=ValueError("bad token"),
                ),
                self.assertRaises(RuntimeError) as context,
            ):
                get_credentials(credentials_path, token_path)

        self.assertIn("Could not read OAuth token file", str(context.exception))

    def test_refreshes_expired_credentials(self):
        with tempfile.TemporaryDirectory() as tmp:
            token_path = Path(tmp) / "token.json"
            credentials_path = Path(tmp) / "credentials.json"
            token_path.write_text("{}", encoding="utf-8")

            creds = MagicMock()
            creds.expired = True
            creds.refresh_token = "refresh-token"
            creds.to_json.return_value = "{}"

            with patch(
                "gmail_cleaner.cli.Credentials.from_authorized_user_file",
                return_value=creds,
            ):
                get_credentials(credentials_path, token_path)

            creds.refresh.assert_called_once()
            self.assertEqual(token_path.read_text(encoding="utf-8"), "{}")

    def test_creates_new_credentials_when_token_is_absent(self):
        with tempfile.TemporaryDirectory() as tmp:
            token_path = Path(tmp) / "token.json"
            credentials_path = Path(tmp) / "credentials.json"
            credentials_path.write_text("{}", encoding="utf-8")

            creds = MagicMock()
            creds.to_json.return_value = "{}"
            flow = MagicMock()
            flow.run_local_server.return_value = creds

            with patch(
                "gmail_cleaner.cli.InstalledAppFlow.from_client_secrets_file",
                return_value=flow,
            ) as factory:
                result = get_credentials(credentials_path, token_path)

        factory.assert_called_once_with(
            str(credentials_path),
            ["https://www.googleapis.com/auth/gmail.modify"],
        )
        flow.run_local_server.assert_called_once_with(port=0, open_browser=False)
        self.assertIs(result, creds)


if __name__ == "__main__":
    unittest.main()
