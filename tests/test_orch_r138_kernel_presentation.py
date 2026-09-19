from copy import deepcopy
from types import SimpleNamespace
import unittest

from gpu.orch_r138_kernel_presentation import verify_recovery_presentation


class RecoveryPresentationTests(unittest.TestCase):
    def setUp(self):
        self.plan = dict(presentation_version='R125_PLAIN_CONTEXT_V1', system_prompt='system',
                         birth_prompt='birth', context_limit=16384)
        self.stream = SimpleNamespace(presentation=dict(version='R125_PLAIN_CONTEXT_V1',
            system_prompt='system', birth_prompt='birth'), context_limit=16384)

    def test_exact_recovery_does_not_modify_state(self):
        before = deepcopy(vars(self.stream))
        verify_recovery_presentation(self.stream, self.plan, True)
        self.assertEqual(vars(self.stream), before)

    def test_recovery_rejects_changes_to_every_presentation_field(self):
        for key in ('system_prompt', 'birth_prompt', 'presentation_version', 'context_limit'):
            changed = dict(self.plan, **{key: 32768 if key == 'context_limit' else 'changed'})
            with self.subTest(key=key), self.assertRaisesRegex(ValueError, 'preserve_existing_presentation'):
                verify_recovery_presentation(self.stream, changed, True)

    def test_non_recovery_leaves_normal_presentation_path_untouched(self):
        verify_recovery_presentation(self.stream, {}, False)


if __name__ == '__main__':
    unittest.main()
