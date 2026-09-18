import unittest
from pathlib import Path
from unittest.mock import patch

from r188_recovery import prefix_file, suffix_counts, terminate


class RollbackAccountingTests(unittest.TestCase):
    def test_prefix_includes_exact_intent_companions_not_suffix(self):
        self.assertTrue(prefix_file('00000000000000000010.json', 10))
        self.assertTrue(prefix_file('00000000000000000010.intent.json', 10))
        self.assertFalse(prefix_file('00000000000000000011.intent.json', 10))
        self.assertFalse(prefix_file('00000000000000000010.json.partial', 10))

    def setUp(self):
        self.saved = dict(index=10, kind='SLEEP_COMPLETE', document=dict(total_optimizer_steps=100))

    def test_logged_loss_and_unknown_are_separate(self):
        records = [self.saved, dict(index=11, kind='RESPONSE', document={}),
            dict(index=12, kind='UPDATE', document=dict(optimizer_step=101))]
        result = suffix_counts(records, self.saved)
        self.assertEqual(result['logged_discarded_updates'], 1)
        self.assertEqual(result['discarded_RESPONSE'], 1)
        self.assertEqual(result['unknown_inflight_update'], 'UNKNOWN_NOT_COUNTED')

    def test_new_complete_must_not_be_discarded(self):
        with self.assertRaisesRegex(ValueError, 'newer_saved_boundary'):
            suffix_counts([self.saved, dict(self.saved, index=11)], self.saved)

    def test_gap_in_update_evidence_rejected(self):
        with self.assertRaisesRegex(ValueError, 'consecutive_logged_discarded_updates'):
            suffix_counts([self.saved, dict(index=11, kind='UPDATE', document=dict(optimizer_step=102))], self.saved)

    def test_zombie_exit_does_not_read_inaccessible_cwd(self):
        fields = ['0'] * 22
        fields[0], fields[19] = 'Z', '123'
        with patch.object(Path, 'read_text', return_value='99 (exited) ' + ' '.join(fields)), \
                patch('r188_recovery.base.exact') as exact:
            terminate(dict(pid=99, ticks='123'))
            exact.assert_not_called()

    def test_exit_between_stat_and_cwd_requires_pidfd_confirmation(self):
        fields = ['0'] * 22
        fields[0], fields[19] = 'R', '123'
        with patch.object(Path, 'read_text', return_value='99 (exiting) ' + ' '.join(fields)), \
                patch('r188_recovery.base.exact', side_effect=PermissionError), \
                patch('r188_recovery.os.pidfd_open', return_value=11), \
                patch('r188_recovery.os.close'), \
                patch('r188_recovery.select.select', side_effect=[([], [], []), ([11], [], [])]), \
                patch('r188_recovery.signal.pidfd_send_signal') as sent:
            terminate(dict(pid=99, ticks='123'))
            sent.assert_not_called()


if __name__ == '__main__':
    unittest.main()
