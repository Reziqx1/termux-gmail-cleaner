import unittest
from datetime import UTC, datetime

from gmail_cleaner.observer import observation_from_resource


class ObserverTests(unittest.TestCase):
    def test_observation_normalizes_required_metadata(self):
        observation = observation_from_resource(
            {
                "id": "m1",
                "threadId": "t1",
                "internalDate": "0",
                "labelIds": ["INBOX", "CATEGORY_PROMOTIONS"],
                "payload": {
                    "headers": [
                        {"name": "Subject", "value": "  Hello  "},
                        {
                            "name": "From",
                            "value": "News <NEWS@Example.com>",
                        },
                    ]
                },
            }
        )

        self.assertEqual(observation.message_id, "m1")
        self.assertEqual(observation.thread_id, "t1")
        self.assertEqual(observation.sender_name, "News")
        self.assertEqual(observation.sender_email, "news@example.com")
        self.assertEqual(observation.subject, "Hello")
        self.assertEqual(observation.internal_date, datetime(1970, 1, 1, tzinfo=UTC))
        self.assertEqual(observation.label_ids, ("INBOX", "CATEGORY_PROMOTIONS"))

    def test_observation_uses_safe_header_fallbacks(self):
        observation = observation_from_resource(
            {
                "id": "m1",
                "threadId": "t1",
                "internalDate": "0",
                "labelIds": [],
                "payload": {"headers": []},
            }
        )

        self.assertEqual(observation.sender_email, "(unknown)")
        self.assertEqual(observation.subject, "(no subject)")

    def test_missing_id_is_rejected(self):
        with self.assertRaises(ValueError):
            observation_from_resource(
                {"threadId": "t1", "internalDate": "0"}
            )

    def test_missing_internal_date_is_rejected(self):
        with self.assertRaises(ValueError):
            observation_from_resource({"id": "m1", "threadId": "t1"})


if __name__ == "__main__":
    unittest.main()
