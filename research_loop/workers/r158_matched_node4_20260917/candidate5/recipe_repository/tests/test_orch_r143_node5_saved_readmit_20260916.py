from copy import deepcopy
import importlib.util
import inspect
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1] / 'research_loop/workers/r143_node5_allocator_20260916t1427z'
SPEC = importlib.util.spec_from_file_location('node5_readmit_test', ROOT / 'node5_saved_readmit_20260916t1652z.py')
readmit = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(readmit)


class SavedReadmissionTests(unittest.TestCase):
    def test_inherits_original_scanner_and_confined_supervise(self):
        original = readmit.inherited()
        source = inspect.getsource(original.supervise)
        self.assertIn("'scan'", source)
        self.assertIn("report['clear']", source)
        self.assertIn('unchanged_fresh_exclusive_admission', source)
        self.assertEqual(original.CONTROLS, readmit.CONTROLS)

    def test_only_attempt_and_unit_change(self):
        original = dict(attempt_dir='/old', resume=True, plan_sha256='same',
                        device_containment=dict(unit='old', minor=2, uid=2524))
        proposed = deepcopy(original)
        proposed['attempt_dir'] = '/new'
        proposed['device_containment']['unit'] = 'new'
        readmit.guard_delta(original, proposed)
        proposed['plan_sha256'] = 'other'
        with self.assertRaises(ValueError):
            readmit.guard_delta(original, proposed)

    def test_exact_failure_and_checkpoint_only(self):
        boundary = dict(cycle=32, optimizer_steps=2754, state_sha256=readmit.STATE_SHA)
        failed = dict(error='unchanged_fresh_exclusive_admission')
        admission = dict(clear=False, blocking_reasons=['process_identity_drift:2404675'])
        readmit.failure_contract(boundary, failed, admission, False)
        for changed in (dict(boundary, cycle=31), dict(boundary, optimizer_steps=2753), dict(boundary, state_sha256='bad')):
            with self.assertRaises(ValueError):
                readmit.failure_contract(changed, failed, admission, False)
        with self.assertRaises(ValueError):
            readmit.failure_contract(boundary, failed, admission, True)
        with self.assertRaises(ValueError):
            readmit.failure_contract(boundary, failed, dict(admission, blocking_reasons=['foreign_fd']), False)

    def test_full_bundle_and_snapshot_still_required(self):
        source = inspect.getsource(readmit.saved_run1)
        for gate in ('saved_evidence', 'verify_snapshot', 'all_run1_saved_state_exact', 'old_and_failed_run1_processes_absent'):
            self.assertIn(gate, source)

    def test_no_new_source_patch_or_child_signals(self):
        source = inspect.getsource(readmit)
        for forbidden in ('pidfd_send_signal', 'SIGTERM', 'patch_source(', 'os.kill('):
            self.assertNotIn(forbidden, source)
        self.assertIn('same_source_plan_allocation_bytes=True', source)


if __name__ == '__main__':
    unittest.main()
