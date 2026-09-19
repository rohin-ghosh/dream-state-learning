import unittest

import status


class StatusTests(unittest.TestCase):
    def test_backoff_status_without_document_timestamp(self):
        value = status.policy_status(dict(status='PROVIDER_BACKOFF', not_before_unix=200), 150, 100)
        self.assertTrue(value['belongs_to_post_reboot_parent'])
        self.assertEqual(value['timestamp_basis'], 'status_file_mtime')
        self.assertEqual(value['not_before_unix'], 200)

    def test_historical_document_is_never_fresh_from_file_mtime(self):
        value = status.policy_status(dict(status='AWAITING_RENDER', observed_unix=50), 150, 100)
        self.assertFalse(value['belongs_to_post_reboot_parent'])
        self.assertEqual(value['timestamp_basis'], 'document')


if __name__ == '__main__':
    unittest.main()
