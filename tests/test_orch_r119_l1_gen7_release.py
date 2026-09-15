import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from gpu import orch_r119_l1_gen7_release as release


class OwnedIdentityTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.process = subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(30)',
                                         'supervise', '--root', str(self.root), '--index', '7'])
        self.addCleanup(self.cleanup_process)
        self.expected = release.identity(self.process.pid)

    def cleanup_process(self):
        if self.process.poll() is None:
            self.process.terminate()
        self.process.wait(timeout=5)

    def test_exact_own_identity_and_command_can_open_pidfd_without_signals(self):
        descriptor = release.owned_descriptor(self.expected, self.root, 'supervise', 'fixture_uuid')
        os.close(descriptor)
        self.assertIsNone(self.process.poll())
        self.assertFalse(release.gone(self.expected))

    def test_stale_identity_rejected_before_signal(self):
        expected = dict(self.expected, start_ticks='wrong_start_ticks')
        with self.assertRaises(AssertionError):
            release.owned_descriptor(expected, self.root, 'supervise', 'fixture_uuid')
        self.assertIsNone(self.process.poll())

    def test_wrong_root_or_role_rejected(self):
        for root, role in ((self.root/'foreign', 'supervise'), (self.root, 'generate')):
            with self.assertRaises(AssertionError):
                release.owned_descriptor(self.expected, root, role, 'fixture_uuid')
        self.assertIsNone(self.process.poll())

    def test_immutable_receipt_is_not_overwritten(self):
        path = self.root/'RECEIPT.json'
        release.write(path, dict(status='FIRST'))
        with self.assertRaises(AssertionError):
            release.write(path, dict(status='SECOND'))
        self.assertEqual(release.read(path), dict(status='FIRST'))

    def test_fast_candidate_is_only_preprobe_not_full_acceptance(self):
        release.write(self.root/'PROGRESS.json', dict(calls=2, inherited_calls=0, new_segment_calls=2))
        release.write(self.root/'CALL_000002.json', dict(cumulative_call=2, family='math'))
        release.write(self.root/'FAILED_000001.json', {})
        self.assertTrue(release.candidate_progress(self.root)[0])
        from gpu.orch_r119_l1_gen7_handover import boundary_status
        self.assertFalse(boundary_status(self.root)['candidate'])
        release.write(self.root/'INTENT_000003.json', {})
        self.assertFalse(release.candidate_progress(self.root)[0])


if __name__ == '__main__':
    unittest.main()
