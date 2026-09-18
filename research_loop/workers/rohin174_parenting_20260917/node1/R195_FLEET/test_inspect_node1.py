"""Regression for the metadata inspector's existing runtime digest format."""

import hashlib
import json
import unittest

from inspect_node1 import digest


class InspectorDigestTests(unittest.TestCase):
    def test_non_ascii_history_uses_existing_ascii_escaped_canonical_bytes(self):
        document = {"history": "λ，数学", "rows": [], "pending": None}
        expected = hashlib.sha256(json.dumps(document, sort_keys=True,
            separators=(",", ":"), allow_nan=False).encode()).hexdigest()
        self.assertEqual(digest(document), expected)
        utf8_hash = hashlib.sha256(json.dumps(document, sort_keys=True,
            separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode()).hexdigest()
        self.assertNotEqual(digest(document), utf8_hash)


if __name__ == "__main__":
    unittest.main()
