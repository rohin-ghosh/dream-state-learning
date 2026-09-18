import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from gpu import orch_r145_node3_readmission as readmission


class BeforeNativeReadmissionTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.control = Path(self.temporary.name)
        self.config = dict(attempt_dir=str(self.control))
        self.manifest = dict(recovery_output=str(self.control / 'recovery'))
        self.write('FAILED.json', dict(error='unchanged_global_exclusive_admission'))
        self.write('ADMISSION.json', dict(clear=False, scanner_euid=0, blocking_reasons=['process_identity_drift:123']))
        self.write('SUPERVISOR_REQUEST.json', dict(pid=999999999))

    def write(self, name, document):
        (self.control / name).write_text(json.dumps(document))

    def validate(self):
        return readmission.validate_denial(self.control, self.config, self.manifest)

    def test_exact_before_native_identity_denial_allowed_for_fresh_scan(self):
        self.assertFalse(self.validate()['clear'])

    def test_every_possible_native_artifact_blocks(self):
        for name in ('CONTAINED_COMMAND.json', 'CONTAINMENT_VERIFIED.json', 'LAUNCH.json', 'NATIVE.log', 'EXIT.json'):
            with self.subTest(name=name):
                self.write(name, {})
                with self.assertRaisesRegex(ValueError, 'possible_native_dispatch'):
                    self.validate()
                (self.control / name).unlink()

    def test_no_retry_of_started_probe_or_oom(self):
        (self.control / 'recovery').mkdir()
        with self.assertRaisesRegex(ValueError, 'recovery_started'):
            self.validate()

    def test_foreign_fd_or_nonroot_or_clear_denials_rejected(self):
        for report in (dict(clear=False, scanner_euid=0, blocking_reasons=['open_device_pid:1']),
                       dict(clear=False, scanner_euid=0, blocking_reasons=[]),
                       dict(clear=False, scanner_euid=2524, blocking_reasons=['process_identity_drift:123']),
                       dict(clear=True, scanner_euid=0, blocking_reasons=['process_identity_drift:123'])):
            with self.subTest(report=report):
                self.write('ADMISSION.json', report)
                with self.assertRaises(ValueError):
                    self.validate()

    def test_other_failure_rejected(self):
        self.write('FAILED.json', dict(error='CUDA OOM'))
        with self.assertRaisesRegex(ValueError, 'only_original_admission_failure'):
            self.validate()

    def test_live_supervisor_rejected(self):
        self.write('SUPERVISOR_REQUEST.json', dict(pid=1))
        with self.assertRaisesRegex(ValueError, 'previous_supervisor'):
            self.validate()


if __name__ == '__main__':
    unittest.main()
