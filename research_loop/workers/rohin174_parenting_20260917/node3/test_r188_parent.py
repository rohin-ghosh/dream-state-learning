import unittest

from r188_parent import rebase_snapshot


class RollbackParentTests(unittest.TestCase):
    def test_lifetime_clock_without_rewriting_raw_snapshot(self):
        source = dict(request_count=126, response_count=126, delivered={})
        restored = dict(saved_index=100, counts=dict(discarded_REQUEST=3, discarded_RESPONSE=3))
        result = rebase_snapshot(source, restored)
        self.assertEqual(result['request_count'], 129)
        self.assertEqual(source['request_count'], 126)
        self.assertFalse(result['R188_explicit_rollback']['unbroken_exact_continuation'])

    def test_only_postrollback_deliveries_receive_new_offset(self):
        source = dict(request_count=127, response_count=127, delivered={
            'old': dict(record_index=99, request_count=100),
            'new': dict(record_index=101, request_count=127)})
        restored = dict(saved_index=100, counts=dict(discarded_REQUEST=3, discarded_RESPONSE=3))
        result = rebase_snapshot(source, restored)
        self.assertEqual(result['delivered']['old']['request_count'], 100)
        self.assertEqual(result['delivered']['new']['request_count'], 130)
        self.assertEqual(source['delivered']['new']['request_count'], 127)


if __name__ == '__main__':
    unittest.main()
