import importlib.util
from pathlib import Path
import unittest


class RestoreTests(unittest.TestCase):
    def test_poll_receipt_keeps_references_without_repeating_transcript(self):
        import p7_bounded
        observation = dict(reference={'next_index': 12}, reply=dict(record_index=11,
            record_sha256='a' * 64, text='long child transcript'), publications=[{'message': 'parent text'}])
        compact = p7_bounded.compact_poll(observation)
        self.assertEqual(compact['reply_reference']['record_index'], 11)
        self.assertEqual(compact['publications'], 1)
        self.assertNotIn('long child transcript', str(compact))
        self.assertEqual(observation['reply']['text'], 'long child transcript')

    def test_c2_respects_saved_scope_and_has_gap_notice(self):
        path = Path(__file__).with_name('c2_restore.py')
        spec = importlib.util.spec_from_file_location('c2_restore_test', path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        self.assertIn('operator outage', module.GAP)
        self.assertIn('Check every pair', module.GAP)
        self.assertIn('all authentic child rows still train', module.GAP)
        self.assertNotIn('V = 29', module.GAP)

    def test_no_native_control_in_restart_scripts(self):
        for filename in ('c2_restore.py', 'p7_restore.py'):
            text = Path(__file__).with_name(filename).read_text()
            for forbidden in ('SIGTERM', 'SIGKILL', 'pidfd_send_signal', 'native.run(', 'torch.load'):
                self.assertNotIn(forbidden, text)


if __name__ == '__main__':
    unittest.main()
