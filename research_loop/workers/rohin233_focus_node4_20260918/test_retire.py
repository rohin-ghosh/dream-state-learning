import unittest
from pathlib import Path
from unittest.mock import patch

import retire


class RetirementScopeTests(unittest.TestCase):
    def binding(self, physical):
        root = retire.BASE / ('MATH_C' if physical == 6 else f'SCALE_physical{physical}') / 'life'
        return dict(physical=physical, root=str(root), backing_root=str(root))

    def test_named_roots_only(self):
        for physical in (0, 1, 2, 5):
            self.assertEqual(retire.scope(self.binding(physical)).name, 'life')

    def test_P3_P7_kernel4_never_selected(self):
        for physical in (3, 4, 7):
            with self.assertRaises(ValueError):
                retire.scope(self.binding(physical))

    def test_root_substitution_rejected(self):
        binding = self.binding(2)
        binding['root'] = self.binding(3)['root']
        with self.assertRaises(ValueError):
            retire.scope(binding)

    def test_math_C_requires_explicit_no_route_disposition(self):
        binding = self.binding(6)
        with self.assertRaises(ValueError):
            retire.scope(binding)
        binding['classroom_disposition'] = 'NO_PROVEN_CROSS_NODE_THINK_ROUTE_RETIRE'
        self.assertEqual(retire.scope(binding).parent.name, 'MATH_C')

    def test_start_tick_reuse_rejected(self):
        expected = {key: 'bound' for key in retire.IDENTITY_FIELDS}
        actual = dict(expected, start_ticks='reused')
        with patch.object(retire, 'identity', return_value=actual):
            self.assertFalse(retire.same_process(expected))

    def test_no_pause_or_KILL_signal(self):
        source = Path(retire.__file__).read_text()
        self.assertNotIn('signal.SIGSTOP', source)
        self.assertNotIn('signal.SIGKILL', source)
        self.assertNotIn('killpg(', source)


if __name__ == '__main__':
    unittest.main()
