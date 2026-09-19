import unittest

from reconcile import validate_delivery


class ReconciliationTests(unittest.TestCase):
    result = {"inbox_publication": {"id": "published-id"}}

    def test_hash_and_id_bound_delivery(self):
        validate_delivery(self.result, {"result_sha256": "hash", "inbox_id": "published-id", "status": "COMPLETE"}, "hash")

    def test_publication_id_mismatch_fails(self):
        with self.assertRaisesRegex(ValueError, "delivered_publication_id"):
            validate_delivery(self.result, {"result_sha256": "hash", "inbox_id": "different", "status": "COMPLETE"}, "hash")

    def test_result_hash_mismatch_fails(self):
        with self.assertRaisesRegex(ValueError, "delivered_result_hash"):
            validate_delivery(self.result, {"result_sha256": "different", "inbox_id": "published-id", "status": "COMPLETE"}, "hash")

    def test_incomplete_receipt_is_not_delivery(self):
        with self.assertRaisesRegex(ValueError, "delivery_receipt_complete"):
            validate_delivery(self.result, {"result_sha256": "hash", "inbox_id": "published-id", "status": "PUBLISHED"}, "hash")


if __name__ == "__main__":
    unittest.main()
