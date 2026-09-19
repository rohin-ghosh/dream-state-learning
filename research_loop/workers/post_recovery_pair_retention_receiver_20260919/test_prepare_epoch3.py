from pathlib import Path
import unittest

from prepare_epoch3 import CHECKS, EXPECTED_HISTORY, HERE, HISTORY, checksum, history_parity, prepare


class Epoch3Tests(unittest.TestCase):
    def test_exact_both_arm_preimage_overlay_parity_and_no_double_application(self):
        namespace = {'__name__': '_test_frontier_port'}
        exec(compile((CHECKS / 'frontier_port.py').read_bytes(), 'frontier_port', 'exec'), namespace)
        for life in ('curriculum_learner', 'curriculum_frozen_sibling'):
            original = (HERE / 'prepared_epoch2_v2' / life / 'epoch2/source' / HISTORY).read_bytes()
            proposed = namespace['port'](original)
            self.assertEqual(checksum(proposed), EXPECTED_HISTORY)
            self.assertTrue(history_parity(original, proposed)['passed'])
            with self.assertRaises(ValueError):
                namespace['port'](proposed)

    def test_existing_epoch2_and_outside_worker_outputs_refused(self):
        for output in (HERE / 'prepared_epoch2_v2', Path('/tmp/forbidden-epoch3-output')):
            with self.assertRaisesRegex(ValueError, 'new_local_worker_epoch3_output_only'):
                prepare(output)


if __name__ == '__main__':
    unittest.main()
