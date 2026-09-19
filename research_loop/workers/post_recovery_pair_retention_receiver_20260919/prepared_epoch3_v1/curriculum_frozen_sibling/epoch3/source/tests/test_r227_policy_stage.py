from copy import deepcopy
from pathlib import Path
import unittest

from r227_policy_stage import FILTERS, POLICY, policy_plan


class R227PolicyStageTests(unittest.TestCase):
    def test_explicit_two_level_policy_no_selectors_and_no_original_mutation(self):
        original = dict(source_root='/arm/live', birth_prompt='immutable initial experiment',
            startup_context=dict(path='/arm/live/context/startup.md', sha256='a' * 64),
            think_act_learn=dict(console_reply_policy='R205', pinned_messages_policy='R206',
                **{key: 'historical-selector' for key in FILTERS}),
            **{key: 'historical-selector' for key in FILTERS})
        before = deepcopy(original)
        staged = policy_plan(original, Path('/arm/staged'))
        self.assertEqual(original, before)
        for scope in (staged, staged['think_act_learn']):
            self.assertEqual(scope['learn_row_policy'], POLICY)
            self.assertFalse(set(FILTERS).intersection(scope))
        self.assertEqual(staged['think_act_learn']['console_reply_policy'], 'R205')
        self.assertEqual(staged['think_act_learn']['pinned_messages_policy'], 'R206')
        self.assertEqual(staged['birth_prompt'], original['birth_prompt'])
        self.assertEqual(staged['startup_context']['path'], '/arm/staged/context/startup.md')
        self.assertEqual(staged['startup_context']['sha256'], 'a' * 64)

    def test_receiving_policy_does_not_change_recipes_roots_or_walls(self):
        original = dict(source_root='/arm/live', think_act_learn={}, new_presentations=16,
            rehearsal_presentations=0, root='/arm/raw', physical=7, gpu_uuid='exact-device',
            hard_end_unix=123456, lease_end_unix=234567, plasticity={'learning_rate_multiplier': 0.3})
        staged = policy_plan(original, Path('/arm/staged'))
        for key in ('new_presentations', 'rehearsal_presentations', 'root', 'physical', 'gpu_uuid',
                'hard_end_unix', 'lease_end_unix', 'plasticity'):
            self.assertEqual(staged[key], original[key])


if __name__ == '__main__':
    unittest.main()
