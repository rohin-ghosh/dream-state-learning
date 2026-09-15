from pathlib import Path
import tempfile
import unittest

from gpu import orch_math_pipeline_l2_supervise as repair


class RepairTest(unittest.TestCase):
    def test_exact_retention_seam_is_callable(self):
        from gpu import orch_math_pipeline_l2_native_continue as driver
        driver.bind_retention()
        self.assertTrue(callable(driver.orch_full_rich.memory.recall))
        self.assertTrue(callable(driver.orch_full_rich.memory.audit.collect_cases))

    def test_continue_only_unattempted_cycles_and_all_tests(self):
        self.assertEqual(repair.remaining_stages(), [(1, 'experience'), (1, 'readout'),
            (2, 'experience'), (2, 'readout'), (3, 'experience'), (3, 'readout')])

    def test_only_fresh_full_admission_can_accept(self):
        self.assertTrue(repair.transient_admission(dict(blocking_reasons=['process_identity_drift:4583'])))
        for reason in ('reserved_cvd_pid:1', 'unknown_process_visibility:1', 'active_compute_pid:2', 'open_device_pid:3'):
            self.assertFalse(repair.transient_admission(dict(blocking_reasons=[reason, 'process_identity_drift:4583'])))
        self.assertFalse(repair.transient_admission(dict(blocking_reasons=[])))

    def test_adoption_requires_exact_native_completion(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            output = root / 'GUIDED_SLEEP/cycle0/readout'
            identity = dict(pid=10, start_ticks='20', boot_id='boot')
            repair.original.write(output / 'COMPLETE.json', dict(status='COMPLETE', process=['boot', 10, 20]))
            repair.original.write(output / 'AFTER.json', dict(actual_mounted_identity_verified=True))
            repair.completed_phase(root, 'GUIDED_SLEEP', 0, 'readout', identity)
            with self.assertRaises(AssertionError):
                repair.completed_phase(root, 'GUIDED_SLEEP', 0, 'readout', dict(identity, pid=11))
            repair.original.write(output / 'FAILED.json', dict(error='native_failure'))
            with self.assertRaises(AssertionError):
                repair.completed_phase(root, 'GUIDED_SLEEP', 0, 'readout', identity)


if __name__ == '__main__':
    unittest.main()
