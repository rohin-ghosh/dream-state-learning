import importlib.util
import inspect
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1] / 'research_loop/workers/r143_node5_allocator_20260916t1427z'
SPEC = importlib.util.spec_from_file_location('node5_readmit2_test', ROOT / 'node5_saved_readmit_20260916t1657z.py')
readmit = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(readmit)


class SecondSavedReadmissionTests(unittest.TestCase):
    def test_original_recovery_unchanged_except_prior_preload_proof(self):
        previous = (ROOT / 'node5_saved_readmit_20260916t1652z.py').read_text()
        current = Path(readmit.__file__).read_text()
        current = current.replace('20260916t1657z_readmit2', '20260916t1652z_readmit1')
        current = current.replace(inspect.getsource(readmit.previous_readmission_failed) + '\n\n', '')
        current = current.replace('    previous_readmission_failed(helper)\n', '')
        self.assertEqual(current, previous)

    def test_prior_failed_native_launch_or_live_worker_blocks_recovery(self):
        source = inspect.getsource(readmit.previous_readmission_failed)
        for gate in ('LAUNCH.json', 'NATIVE.log', 'CONTAINMENT_VERIFIED.json', 'RECOVERY_DISPATCHED.json',
                     'previous_readmission_processes_absent', '2470912', '2470915', '2470916'):
            self.assertIn(gate, source)
        self.assertTrue(inspect.getsource(readmit.saved_run1).splitlines()[1].strip().startswith('previous_readmission_failed'))


if __name__ == '__main__':
    unittest.main()
