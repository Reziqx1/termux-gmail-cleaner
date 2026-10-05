import unittest

from src.gmail_cleaner import chunked


class ChunkedTests(unittest.TestCase):
    def test_chunks_list(self):
        self.assertEqual(
            list(chunked(["a", "b", "c", "d", "e"], 2)),
            [["a", "b"], ["c", "d"], ["e"]],
        )

    def test_empty_list(self):
        self.assertEqual(list(chunked([], 100)), [])

    def test_single_chunk(self):
        self.assertEqual(list(chunked(["a", "b"], 100)), [["a", "b"]])


if __name__ == "__main__":
    unittest.main()
