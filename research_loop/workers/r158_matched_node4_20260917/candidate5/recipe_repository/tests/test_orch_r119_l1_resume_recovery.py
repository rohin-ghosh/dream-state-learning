import subprocess
import unittest
from unittest.mock import Mock

from gpu.orch_r119_l1_resume_recovery import guarded_scan


class ScannerRecoveryTests(unittest.TestCase):
    def test_success_and_blocked_reports_preserved_exactly(self):
        for clear in (True,False):
            report=dict(clear=clear,scanner_euid=0,gpu=dict(uuid='actual'),blocking_reasons=[])
            self.assertIs(guarded_scan(Mock(return_value=report),1,'service'),report)

    def test_scanner_execution_errors_never_admit(self):
        errors=[subprocess.CalledProcessError(1,['scanner']),subprocess.TimeoutExpired(['scanner'],90)]
        for error in errors:
            report=guarded_scan(Mock(side_effect=error),1,'service')
            self.assertFalse(report['clear'])
            self.assertIsNone(report['scanner_euid'])
            self.assertTrue(report['ownership_not_verified'])
            self.assertTrue(report['no_gpu_launch'])

    def test_other_provenance_errors_not_suppressed(self):
        with self.assertRaises(ValueError):
            guarded_scan(Mock(side_effect=ValueError('wrong_uuid')),1,'service')


if __name__=='__main__':
    unittest.main()
