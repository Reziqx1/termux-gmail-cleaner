import unittest
from unittest.mock import MagicMock

from googleapiclient.errors import HttpError
from httplib2 import Response

from gmail_cleaner.verifier import verify_trashed


class VerifierTests(unittest.TestCase):
    def test_verifies_messages_with_trash_label(self):
        service = MagicMock()
        service.users.return_value.messages.return_value.get.return_value.execute.return_value = {
            "id": "m1",
            "labelIds": ["INBOX", "TRASH"],
        }

        result = verify_trashed(service, ["m1"])

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].state, "verified")
        self.assertIsNone(result[0].detail)

    def test_marks_missing_trash_label(self):
        service = MagicMock()
        service.users.return_value.messages.return_value.get.return_value.execute.return_value = {
            "id": "m1",
            "labelIds": ["INBOX"],
        }

        result = verify_trashed(service, ["m1"])

        self.assertEqual(result[0].state, "not-verified")
        self.assertEqual(result[0].detail, "TRASH label is absent")

    def test_reports_verification_http_error(self):
        service = MagicMock()
        service.users.return_value.messages.return_value.get.return_value.execute.side_effect = HttpError(
            Response({"status": "404"}),
            b"not found",
        )

        result = verify_trashed(service, ["m1"])

        self.assertEqual(result[0].state, "verification-error")
        self.assertIn("HttpError", result[0].detail or "")

    def test_empty_input_is_no_op(self):
        service = MagicMock()

        result = verify_trashed(service, [])

        self.assertEqual(result, ())
        service.users.return_value.messages.return_value.get.assert_not_called()


if __name__ == "__main__":
    unittest.main()
