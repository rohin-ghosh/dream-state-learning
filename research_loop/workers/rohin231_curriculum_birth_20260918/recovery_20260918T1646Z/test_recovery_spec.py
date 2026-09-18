from copy import deepcopy
import unittest

from recovery_spec import extend_plan


class RecoverySpecTests(unittest.TestCase):
    def setUp(self):
        self.plan = dict(physical=0, root='/pair/raw', source_root='/old/source',
            startup_context={'path': '/old/source/context/birth.txt'}, hard_end_unix=1000,
            lease_end_unix=24600, learn_row_policy='R227_ALL_AUTHENTIC_CHILD_ROWS_V1',
            think_act_learn={'learn_row_policy': 'R227_ALL_AUTHENTIC_CHILD_ROWS_V1'},
            learning_rate=3e-5, new_presentations=16)
        self.saved = dict(sha256='a' * 64, state=dict(pending=None, sleep_frontier=1,
            rows=[{'original': 'raw'}], deadline_unix=1000,
            sleep_receipts=[{'status': 'COMPLETE'}]))

    def test_exact_only_permitted_plan_changes_and_no_mutation(self):
        previous = deepcopy(self.plan)
        saved = deepcopy(self.saved)
        result = extend_plan(self.plan, self.saved, '/new/source', 3000, 24600)
        self.assertEqual(self.plan, previous)
        self.assertEqual(self.saved, saved)
        self.assertEqual({key for key in result if result[key] != previous.get(key)},
            {'source_root', 'startup_context', 'hard_end_unix', 'authorized_wall_extension'})
        self.assertEqual(result['authorized_wall_extension']['previous_stream_sha256'], 'a' * 64)
        self.assertEqual(result['authorized_wall_extension']['safety_margin_seconds'], 21600)

    def test_reject_pending_or_untrained_state(self):
        for key, value in [('pending', 'inflight'), ('sleep_frontier', 0), ('sleep_receipts', [])]:
            with self.subTest(key=key), self.assertRaises(ValueError):
                changed = deepcopy(self.saved)
                changed['state'][key] = value
                extend_plan(self.plan, changed, '/new/source', 3000, 24600)

    def test_reject_wrong_deadline_or_lease(self):
        for deadline, lease in [(900, 24600), (3001, 24600), (3000, 25000), (24480, 24600)]:
            with self.subTest(deadline=deadline, lease=lease), self.assertRaises(ValueError):
                extend_plan(self.plan, self.saved, '/new/source', deadline, lease)

    def test_scope_and_policy_fail_closed(self):
        for key, value in [('physical', 2), ('learn_row_policy', None)]:
            with self.subTest(key=key), self.assertRaises(ValueError):
                changed = deepcopy(self.plan)
                changed[key] = value
                extend_plan(changed, self.saved, '/new/source', 3000, 24600)

    def test_frozen_device_same_configuration(self):
        self.plan['physical'] = 1
        result = extend_plan(self.plan, self.saved, '/new/source', 3000, 24600)
        self.assertEqual(result['physical'], 1)
        self.assertEqual(result['think_act_learn'], self.plan['think_act_learn'])


if __name__ == '__main__':
    unittest.main()
