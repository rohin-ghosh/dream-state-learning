import ast
from copy import deepcopy
from pathlib import Path
import unittest
from unittest.mock import patch

from gpu import orch_math_feedback_uptake_r119_shared as subject


class MathLeaseSharedTests(unittest.TestCase):
    def test_only_deadlines_change(self):
        before = dict(cycles=43, native_calls=1168, parent_calls=384,
            native_end_unix=1, hard_end_unix=2, morning_unix=3)
        saved = deepcopy(before)
        result = subject.continuation_bounds(before, dict(train_end_unix=4, hard_end_unix=5))
        self.assertEqual(before, saved)
        self.assertEqual(result, dict(before, native_end_unix=4, hard_end_unix=5))

    def test_explicit_common_clock_environment(self):
        with patch.dict(subject.os.environ, {}, clear=True):
            with self.assertRaisesRegex(ValueError, 'Main_clock_environment'):
                subject.configure()

    def test_wrong_backend_rejected_before_state_or_gpu(self):
        with patch.dict(subject.os.environ, {'ORCH_R119_LEASE_CLOCK':subject.CLOCK['path'],
             'ORCH_R119_LEASE_CLOCK_SHA256':subject.CLOCK['sha256']}), \
             patch.object(subject.shared,'sha',return_value='bad'):
            with self.assertRaisesRegex(ValueError,'actual_Main_clock_backend'):
                subject.configure()

    def test_no_final_readout_replay(self):
        with patch.object(subject,'configure'), patch.object(subject.shared,'read',return_value={'stage':'morning_final'}):
            with self.assertRaisesRegex(ValueError,'completed_FINAL_never_repeat'):
                subject.readout(Path('/root'),Path('/binding'))

    def test_source_custody_timers_never_dispatch_final(self):
        source = Path(subject.__file__).with_name('orch_math_feedback_uptake_r119_shared_native.py').read_text()
        self.assertNotIn('final.prepare(service)',source)
        self.assertNotIn("final.MODULE,'schedule'",source)
        self.assertIn("MODULE,'finalcustody'",source)
        self.assertIn('previous.math.HARD - 30',source)
        ast.parse(source)

    def test_original_parent_and_native_caps_not_changed(self):
        source = Path(subject.__file__).read_text()
        self.assertNotIn('policy.NATIVE_CAP =', source)
        self.assertNotIn('policy.PARENT_CAP =', source)
        self.assertNotIn('policy.CYCLES =', source)
        self.assertIn("same_genuine_gen1",source)
        self.assertIn("no_counter_reset",source)

    def test_actual_completed_final_schema(self):
        documents = {'COMPLETE.json':dict(native=8),
            'TERMINAL.json':dict(completed_native=8,charged_native=8,failed_or_partial_native=0,
                unattempted_native=0,status='COMPLETE'), 'LAUNCH.json':dict(identity={'pid':123})}
        with patch.object(subject.shared,'read',side_effect=lambda path:documents[Path(path).name]), \
             patch.object(subject.life,'ref',side_effect=lambda path:dict(path=str(path),sha256='a'*64)), \
             patch.object(subject.life,'alive',return_value=False), patch.object(Path,'exists',return_value=True):
            self.assertFalse(subject.completed_final('F2')['repeat_allowed'])
            documents['TERMINAL.json']['charged_native'] = 7
            with self.assertRaisesRegex(ValueError,'eight_complete'):
                subject.completed_final('F2')


if __name__ == '__main__':
    unittest.main()
