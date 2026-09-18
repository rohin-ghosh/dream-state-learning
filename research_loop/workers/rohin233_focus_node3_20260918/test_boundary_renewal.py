from copy import deepcopy
from pathlib import Path
import unittest

from boundary_renewal import TARGETS, exact_native, extension, selected


class BoundaryRenewalTests(unittest.TestCase):
    def test_only_four_named_early_captions_not_math_or_other_roots(self):
        self.assertEqual(len(TARGETS), 4)
        for name in ('r213_math_a', 'r213_r226_caption_unparented_fork', 'p32', 'conversational'):
            with self.assertRaises(ValueError):
                selected(Path('/owned'), name)

    def test_exact_PID_startticks_command_and_control_required(self):
        expected = dict(pid=12, start_ticks='20', command_sha256='sha', state='R',
            args=['python', 'native', '--config', '/owned/GUARD.json'])
        exact_native(expected, expected, Path('/owned'))
        for value in (dict(expected, start_ticks='21'), dict(expected, command_sha256='other'),
                dict(expected, state='Z'), dict(expected, args=['python', 'native', '/other/GUARD.json'])):
            with self.assertRaises(ValueError):
                exact_native(expected, value, Path('/owned'))

    def test_extension_does_not_change_checkpoint_working_state_or_recipe(self):
        saved = dict(sha256='actual-saved-state', state=dict(deadline_unix=100, rows=['own'], pending=None))
        plan = dict(hard_end_unix=200, lease_end_unix=30000, learning_rate=0.00003)
        before = deepcopy((plan, saved))
        result = extension(plan, saved)
        self.assertEqual(result['authorized_wall_extension']['previous_stream_sha256'], saved['sha256'])
        self.assertEqual((plan, saved), before)
        with self.assertRaises(ValueError):
            extension(dict(plan, hard_end_unix=99), saved)


if __name__ == '__main__':
    unittest.main()
