import unittest
from unittest.mock import MagicMock

from googleapiclient.errors import HttpError
from httplib2 import Response

from gmail_cleaner.mutation import move_to_trash_detailed


class MutationTests(unittest.TestCase):
    def test_batches_successfully(self):
        service = MagicMock()
        execute = service.users.return_value.messages.return_value.batchModify.return_value.execute
        execute.return_value = {}

        result = move_to_trash_detailed(
            service,
            ["m1", "m2", "m3"],
            batch_size=2,
        )

        self.assertFalse(result.failed)
        self.assertEqual(result.moved_ids, ("m1", "m2", "m3"))
        self.assertEqual(result.moved_count, 3)
        self.assertEqual(len(result.batches), 2)
        self.assertTrue(all(batch.succeeded for batch in result.batches))

    def test_partial_failure_preserves_successful_batches(self):
        service = MagicMock()
        execute = service.users.return_value.messages.return_value.batchModify.return_value.execute
        execute.side_effect = [
            {},
            HttpError(Response({"status": "500"}), b"server error"),
        ]

        result = move_to_trash_detailed(
            service,
            ["m1", "m2", "m3", "m4"],
            batch_size=2,
        )

        self.assertTrue(result.failed)
        self.assertEqual(result.moved_ids, ("m1", "m2"))
        self.assertEqual(result.moved_count, 2)
        self.assertEqual(len(result.batches), 2)
        self.assertTrue(result.batches[0].succeeded)
        self.assertFalse(result.batches[1].succeeded)
        self.assertIsNotNone(result.batches[1].error)

    def test_empty_input_is_no_op(self):
        service = MagicMock()

        result = move_to_trash_detailed(service, [])

        self.assertFalse(result.failed)
        self.assertEqual(result.moved_ids, ())
        self.assertEqual(result.batches, ())
        service.users.return_value.messages.return_value.batchModify.assert_not_called()

    def test_invalid_batch_size_is_rejected(self):
        with self.assertRaises(ValueError):
            move_to_trash_detailed(MagicMock(), ["m1"], batch_size=0)


if __name__ == "__main__":
    unittest.main()
