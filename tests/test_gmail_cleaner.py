import unittest
from unittest.mock import MagicMock, patch

from gmail_cleaner.cli import (
    BATCH_SIZE,
    _confirm_apply,
    chunked,
    fetch_metadata,
    move_to_trash,
    parse_args,
    search_message_ids,
)


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
    def __init__(self, list_responses=None, metadata=None):
        self.list_responses = list(list_responses or [])
        self.metadata = metadata or {}
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

        move_to_trash(service, message_ids)

        self.assertEqual(len(messages.batch_calls), 3)
        self.assertEqual(
            [len(call["body"]["ids"]) for call in messages.batch_calls],
            [BATCH_SIZE, BATCH_SIZE, 1],
        )

    def test_confirmation_requires_exact_word(self):
        with patch("builtins.input", return_value="TRASH"):
            self.assertTrue(_confirm_apply(3))
        with patch("builtins.input", return_value="trash"):
            self.assertFalse(_confirm_apply(3))

    def test_parse_args_rejects_yes_without_apply(self):
        with self.assertRaises(SystemExit):
            parse_args(["--query", "from:test@example.com", "--yes"])

    def test_run_dry_run_never_moves_messages(self):
        from unittest.mock import patch

        from gmail_cleaner.cli import run

        messages = FakeMessages(
            metadata={
                "payload": {
                    "headers": [
                        {"name": "Subject", "value": "Test"},
                        {"name": "From", "value": "Example <test@example.com>"},
                    ]
                }
            }
        )
        service = FakeService(messages)

        args = parse_args(["--query", "from:test@example.com"])
        with patch("gmail_cleaner.cli.build_service", return_value=service):
            self.assertEqual(run(args), 0)

        self.assertEqual(messages.batch_calls, [])


if __name__ == "__main__":
    unittest.main()
