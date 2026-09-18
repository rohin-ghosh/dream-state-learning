import unittest

from r188_node1 import prefix_name, suffix_counts


class LossTests(unittest.TestCase):
    def test_preserves_record_and_intent_pairs(self):
        self.assertTrue(prefix_name('00000000000000000042.json', 42))
        self.assertTrue(prefix_name('00000000000000000042.intent.json', 42))
        self.assertFalse(prefix_name('00000000000000000043.json', 42))
        self.assertFalse(prefix_name('00000000000000000043.intent.json', 42))
        with self.assertRaises(ValueError):
            prefix_name('00000000000000000043.partial', 42)

    def test_only_logged_consecutive_updates_count(self):
        complete = dict(index=4, kind='SLEEP_COMPLETE', document=dict(total_optimizer_steps=20))
        updates = [dict(index=index + 5, kind='UPDATE', document=dict(optimizer_step=step))
                   for index, step in enumerate((21, 22))]
        result = suffix_counts([complete] + updates, complete)
        self.assertEqual(result['logged_discarded_updates'], 2)
        self.assertEqual(result['unknown_inflight_update'], 'UNKNOWN_NOT_COUNTED')
        updates[-1]['document']['optimizer_step'] = 24
        with self.assertRaises(ValueError):
            suffix_counts([complete] + updates, complete)

    def test_newer_complete_forbids_rollback(self):
        complete = dict(index=4, kind='SLEEP_COMPLETE', document=dict(total_optimizer_steps=20))
        with self.assertRaises(ValueError):
            suffix_counts([complete, dict(complete, index=5)], complete)


if __name__ == '__main__':
    unittest.main()
