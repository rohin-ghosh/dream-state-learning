"""Readmission is restricted to a never-launched identity-drift denial."""

import importlib.util
from pathlib import Path
import tempfile
import unittest


HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location("r179_readmission", HERE / "readmit_node1.py")
READMIT = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(READMIT)


class ReadmissionTests(unittest.TestCase):
    def test_only_privileged_drift_denial_qualifies(self):
        self.assertEqual(READMIT.drift_pids(dict(clear=False, scanner_euid=0,
            blocking_reasons=["process_identity_drift:123"])), [123])

    def test_actual_device_holder_never_qualifies(self):
        with self.assertRaisesRegex(ValueError, "only_actual_privileged"):
            READMIT.drift_pids(dict(clear=False, scanner_euid=0,
                blocking_reasons=["process_identity_drift:123", "active_compute_pid:789"]))

    def test_clear_or_unprivileged_reports_do_not_qualify(self):
        for clear, uid in ((True, 0), (False, 1395)):
            with self.subTest(clear=clear, uid=uid), self.assertRaises(ValueError):
                READMIT.drift_pids(dict(clear=clear, scanner_euid=uid,
                    blocking_reasons=["process_identity_drift:123"]))

    def test_any_launch_evidence_prevents_readmission(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            READMIT.no_native_launch(root)
            for name in ("LAUNCH.json", "NATIVE.log", "CONTAINMENT_VERIFIED.json", "ADMISSION_TIME.json", "EXIT.json"):
                with self.subTest(name=name):
                    (root / name).write_text("fixture")
                    with self.assertRaisesRegex(ValueError, "before_any_native"):
                        READMIT.no_native_launch(root)
                    (root / name).unlink()


if __name__ == "__main__":
    unittest.main()
