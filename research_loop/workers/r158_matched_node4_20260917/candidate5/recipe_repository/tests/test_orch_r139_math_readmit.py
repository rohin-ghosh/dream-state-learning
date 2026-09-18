from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import Mock

from gpu import orch_r139_route_astra_handoff as helper
from gpu.orch_r139_math_readmit import receipt_writer, validate_attempt


class ReadmitTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.root = Path(directory.name)
        helper.write(self.root / 'GUARD_STARTED.json', dict(identity=dict(pid=123)))
        helper.write(self.root / 'ADMISSION.json', dict(clear=False, scanner_euid=0,
            blocking_reasons=['process_identity_drift:456']))

    def test_premodel_only(self):
        validate_attempt(helper, self.root, self.root / 'proc')
        helper.write(self.root / 'LAUNCH.json', {})
        with self.assertRaisesRegex(ValueError, 'no_model_retry'):
            validate_attempt(helper, self.root, self.root / 'proc')

    def test_live_guard_blocks(self):
        (self.root / 'proc' / '123').mkdir(parents=True)
        with self.assertRaisesRegex(ValueError, 'still_present'):
            validate_attempt(helper, self.root, self.root / 'proc')

    def test_other_admission_failures_not_retried(self):
        fake = SimpleNamespace(require=helper.require, read=Mock(side_effect=[dict(identity=dict(pid=123)),
            dict(clear=False,scanner_euid=0,blocking_reasons=['occupied'])]))
        with self.assertRaisesRegex(ValueError, 'transient'):
            validate_attempt(fake, self.root, self.root / 'proc')

    def test_only_prescan_receipts_redirected(self):
        original = Mock()
        attempt = self.root / 'attempt'
        writer = receipt_writer(original, self.root, attempt)
        writer(self.root / 'ADMISSION.json', {})
        original.assert_called_with(attempt / 'ADMISSION.json', {})
        writer(self.root / 'LAUNCH.json', {})
        original.assert_called_with(self.root / 'LAUNCH.json', {})


if __name__ == '__main__':
    unittest.main()
