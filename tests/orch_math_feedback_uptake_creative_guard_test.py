import json
from pathlib import Path
import subprocess
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import Mock

from gpu import orch_math_feedback_uptake_creative_guard as guard


class CreativeGuardTests(unittest.TestCase):
    def report(self, **updates):
        report = dict(gpu=dict(index=7, uuid=guard.UUID), host_sha256=guard.HOST_SHA,
            device_minor=7, scanner_euid=0, clear=True, blocking_reasons=[])
        report.update(updates)
        return report

    def test_scanner_exception_then_full_clean_scan(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            error = subprocess.CalledProcessError(1, ['scanner'], stderr='snapshot raced')
            common = SimpleNamespace(scan=Mock(side_effect=[error, self.report()]))
            guard.admit(common, root, root, 'C7_readout', 100, clock=lambda: 0, wait=lambda seconds: None)
            self.assertEqual(common.scan.call_count, 2)
            self.assertEqual(json.loads((root / 'ADMISSION_C7_readout_0.json').read_text())['status'], 'SCANNER_ERROR_BLOCKED')

    def test_blocking_owner_never_waived(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            common = SimpleNamespace(scan=Mock(return_value=self.report(clear=False, blocking_reasons=['owner_present'])))
            clock = Mock(side_effect=[0, 0, 181])
            with self.assertRaises(TimeoutError):
                guard.admit(common, root, root, 'C7', 500, clock=clock, wait=lambda seconds: None)
            self.assertEqual(common.scan.call_count, 1)

    def test_root_and_clear_not_enough_when_uuid_wrong(self):
        with self.assertRaisesRegex(AssertionError, 'pinned'):
            guard.checked_report(self.report(gpu=dict(index=7, uuid='wrong')))

    def test_host_mismatch_fails_closed(self):
        with self.assertRaisesRegex(AssertionError, 'host_minor'):
            guard.checked_report(self.report(host_sha256='wrong'))

    def test_unprivileged_scanner_not_admitted(self):
        self.assertFalse(guard.checked_report(self.report(scanner_euid=1395)))

    def test_existing_artifact_not_overwritten(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / 'receipt.json'
            guard.write(path, {'old': True})
            with self.assertRaises(FileExistsError):
                guard.write(path, {'new': True})

    def fixture(self, root):
        for cycle in range(1, 8):
            for phase in ('experience', 'readout'):
                if cycle == 7 and phase == 'readout':
                    continue
                output = root / 'GUIDED_SLEEP' / f'cycle{cycle}' / phase
                output.mkdir(parents=True)
                complete = dict(status='COMPLETE', process=['boot', 1, 2], output_adapter={'sha': 'same'})
                guard.write(output / 'COMPLETE.json', complete)
                guard.write(output / 'AFTER.json', dict(complete, actual_mounted_identity_verified=True, frozen_base_verified=True))
                guard.write(output / 'REQUEST.json', {})
                if phase == 'experience':
                    guard.write(output / 'ROWS.json', [])
                for index in range(4 if phase == 'experience' else 8):
                    guard.write(output / f'CALL_{index:03d}.json', {})

    def test_exact_completed_prefix(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self.fixture(root)
            self.assertTrue(guard.completed_prefix(root))
            self.assertEqual(guard.REMAINING, ((7, 'readout'), (8, 'experience'), (8, 'readout')))

    def test_even_empty_entered_phase_is_not_retried(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self.fixture(root)
            (root / 'GUIDED_SLEEP/cycle7/readout').mkdir()
            with self.assertRaisesRegex(AssertionError, 'entered_phase'):
                guard.completed_prefix(root)

    def test_prior_dispatch_blocks_retry(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self.fixture(root)
            guard.write(root / 'LAUNCH_C7_readout.json', {})
            with self.assertRaisesRegex(AssertionError, 'prior_dispatch'):
                guard.completed_prefix(root)

    def test_incomplete_prefix_blocks(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self.fixture(root)
            (root / 'GUIDED_SLEEP/cycle7/experience/FAILED.json').write_text('{}')
            with self.assertRaisesRegex(AssertionError, 'prefix_failure'):
                guard.completed_prefix(root)


if __name__ == '__main__':
    unittest.main()
