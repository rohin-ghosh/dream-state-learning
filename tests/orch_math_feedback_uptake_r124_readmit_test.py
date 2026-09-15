import errno
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from gpu import orch_math_feedback_uptake_r124_readmit as repair


class ReadmissionTests(unittest.TestCase):
    def test_only_receipts_redirected(self):
        root = Path('/test/A2')
        for name in ('ADMISSION.json', 'GUARD_STARTED.json'):
            self.assertEqual(repair.receipt_path(root, root / name), root / repair.ATTEMPT / name)
        for name in ('LAUNCH.json', 'COUNTERS.json', 'GUARD_TERMINAL.json', 'native.log'):
            self.assertEqual(repair.receipt_path(root, root / name), root / name)

    def test_actual_esrch_required(self):
        with patch.object(repair.os, 'pidfd_open', side_effect=OSError(errno.ESRCH, 'gone')), patch.object(Path, 'exists', return_value=False):
            self.assertTrue(repair.prove_absent(100)['proc_absent'])
        for error in (errno.EPERM, errno.EMFILE):
            with patch.object(repair.os, 'pidfd_open', side_effect=OSError(error, 'not exit')), self.assertRaises(ValueError):
                repair.prove_absent(100)

    def test_live_reused_pid_rejected(self):
        with patch.object(repair.os, 'pidfd_open', return_value=4), patch.object(repair.os, 'close') as close:
            with self.assertRaises(ValueError):
                repair.prove_absent(100)
            close.assert_called_once_with(4)

    def test_proc_reappearance_rejected(self):
        with patch.object(repair.os, 'pidfd_open', side_effect=OSError(errno.ESRCH, 'gone')), patch.object(Path, 'exists', return_value=True), self.assertRaises(ValueError):
            repair.prove_absent(100)

    def test_model_or_charge_blocks_recovery(self):
        for name in ('LAUNCH.json', 'native.log', 'reservations/0001.json', 'paired_DEV/before/BINDING.json'):
            with tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                (root / 'COUNTERS.json').write_text(json.dumps({'native': 200}))
                repair.no_input(root, {'native': 200})
                target = root / name
                target.parent.mkdir(parents=True, exist_ok=True)
                target.touch()
                with self.assertRaises(ValueError):
                    repair.no_input(root, {'native': 200})

    def test_changed_counter_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'COUNTERS.json').write_text('{"native": 201}')
            with self.assertRaises(ValueError):
                repair.no_input(root, {'native': 200})
