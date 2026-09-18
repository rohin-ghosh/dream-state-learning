from copy import deepcopy
from pathlib import Path
import unittest

import recovery
from recovery_runtime import entrypoint, CAPTIONS, MATH


class RecoveryTests(unittest.TestCase):
    def test_offline_replay_preserves_confined_inbox_namespace(self):
        self.assertEqual(recovery.offline_inbox(dict(root='/original/confined/life')),
            Path('/original/confined/life/stream/inbox'))

    def test_exact_eight_devices(self):
        for name, device in dict(CAPTIONS, **MATH).items():
            self.assertIn(entrypoint(dict(source_root='/owned/' + name + '/source_new', physical=device)),
                ('gpu.r227_caption_runtime', 'gpu.r226_math_runtime'))
            with self.assertRaises(ValueError):
                entrypoint(dict(source_root='/owned/' + name + '/source_new', physical=(device + 1) % 8))

    def test_retired_aliases_forbidden(self):
        for name in ('conversational', 'p32', 'peer_math', 'r213_siege_envoy_fork', 'frozen_c2'):
            with self.assertRaises(ValueError):
                entrypoint(dict(source_root='/owned/' + name + '/source_new', physical=0))

    def test_wall_obeys_existing_lease_and_reservation(self):
        plan = dict(lease_end_unix=100000)
        self.assertEqual(recovery.checked_deadline(plan, dict(next_reserved_unix=99999), 1000), 44200)
        self.assertEqual(recovery.checked_deadline(plan, dict(next_reserved_unix=5000), 1000), 4880)
        with self.assertRaises(ValueError):
            recovery.checked_deadline(plan, dict(next_reserved_unix=2000), 1000)
        with self.assertRaises(ValueError):
            recovery.checked_deadline(plan, dict(next_reserved_unix=99999), 1000, 999999)

    def test_plan_changes_only_location_and_wall(self):
        original = dict(source_root='/owned/r213_math_a/source_old', physical=1, hard_end_unix=10,
            root='/namespace/original', new_presentations=16,
            startup_context=dict(path='/owned/r213_math_a/source_old/context/start.md', sha256='fixed'),
            think_act_learn=dict(prose_target_filter='unchanged', environment_facts='unchanged'),
            birth_prompt='unchanged')
        snapshot = deepcopy(original)
        changed = recovery.relocated_plan(original, Path('/owned/r213_math_a/source_new'), 20)
        self.assertEqual(original, snapshot)
        self.assertEqual(changed['root'], original['root'])
        self.assertEqual(changed['think_act_learn'], original['think_act_learn'])
        self.assertEqual(changed['birth_prompt'], original['birth_prompt'])
        self.assertEqual(changed['startup_context']['sha256'], 'fixed')
        self.assertEqual(changed['hard_end_unix'], 20)
        self.assertEqual(changed['new_presentations'], 16)

    def test_no_overlapping_recovery_protocols(self):
        for field in ('preupdate_recovery', 'authorized_wall_extension'):
            with self.assertRaises(ValueError):
                recovery.relocated_plan(dict(source_root='/owned/r213_math_a/old', physical=1,
                    **{field: {}}), Path('/owned/r213_math_a/new'), 20)


if __name__ == '__main__':
    unittest.main()
