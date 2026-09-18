"""CPU refusal/dispatch/boundary regression; no remote or GPU actions."""

from pathlib import Path
import sys
import unittest
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parent))
import r188_preload_recovery as recovery


class PreloadRecoveryTests(unittest.TestCase):
    def check(self, label='pilot', names=(), present=(), actual='same', expected='same', reasons=None):
        recovery.eligibility(label, dict(reason='original_privileged_clear_admission', retired=True, terminated=True),
            dict(clear=False, scanner_euid=0, blocking_reasons=recovery.SCOPES[label][3] if reasons is None else reasons),
            names, present, actual, expected)

    def test_two_exact_refusals(self):
        for label in recovery.SCOPES:
            self.check(label)

    def test_each_dispatch_marker_blocks(self):
        for marker in recovery.DISPATCH_MARKERS:
            with self.subTest(marker=marker), self.assertRaisesRegex(ValueError, 'prior_native_dispatch'):
                self.check(names=[marker])

    def test_live_owner_blocks(self):
        with self.assertRaisesRegex(ValueError, 'owners_absent'):
            self.check(present=[1])

    def test_suffix_blocks(self):
        with self.assertRaisesRegex(ValueError, 'boundary_no_suffix'):
            self.check(actual='changed')

    def test_other_refusal_blocks(self):
        with self.assertRaisesRegex(ValueError, 'preserved_admission'):
            self.check(reasons=['foreign_GPU_owner'])

    def test_unchanged_supervise_and_no_signals(self):
        source = Path(recovery.__file__).read_text()
        self.assertIn('operator.supervise(output)', source)
        self.assertIn('os.O_RDWR | os.O_NOFOLLOW', source)
        self.assertNotIn('os.kill', source)
        self.assertNotIn('pidfd_send_signal', source)
        self.assertNotIn('WRITER.lock', source)

    def test_reader_uses_original_capsule_unit_contract(self):
        expected = 'orch-r136-native-' + 'a' * 32
        operator = SimpleNamespace(successor_unit_name=lambda output, physical: expected)
        self.assertEqual(recovery.unit_name(operator, Path('/tmp/unused'), 7), expected)
        operator = SimpleNamespace(successor_unit_name=lambda output, physical: output.name)
        with self.assertRaisesRegex(ValueError, 'reader_capsule_unit_contract'):
            recovery.unit_name(operator, Path('/tmp/wrong-unit'), 7)


if __name__ == '__main__':
    unittest.main()
