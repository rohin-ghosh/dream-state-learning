import unittest

from organism_v6 import orch_rich_hot_node3_fill12 as policy


class FillerTests(unittest.TestCase):
    def test_exact_ownership_and_unsteered_control(self):
        for index in (0,3,4,5,6,7):
            with self.assertRaises(ValueError):
                policy.condition(index)
        control=policy.messages(dict(question='Q',gold='SEALED'),1)
        steered=policy.messages(dict(question='Q',gold='SEALED'),2)
        self.assertNotIn('SEALED',str(control))
        self.assertNotIn(policy.exhaustion.STEERING,str(control))
        self.assertIn(policy.exhaustion.STEERING,str(steered))

    def test_absolute_deadlines_and_no_reset(self):
        self.assertTrue(policy.can_dispatch(policy.DISPATCH_CUTOFF-1,0,0))
        self.assertFalse(policy.can_dispatch(policy.DISPATCH_CUTOFF,0,0))
        self.assertEqual(policy.HARD_END-policy.DISPATCH_CUTOFF,300)
        self.assertEqual(policy.protocol()['new_aggregate_ceiling'],3280)
        self.assertFalse(policy.protocol()['quota_reset'])

    def test_slot_global_and_early_release_limits(self):
        self.assertFalse(policy.can_dispatch(0,256,256))
        self.assertFalse(policy.can_dispatch(0,1,512))
        self.assertFalse(policy.can_dispatch(0,0,0,True))
        self.assertTrue(policy.can_dispatch(0,255,511))

    def test_context_oracle_and_self_report_contract(self):
        self.assertEqual(policy.exhaustion.token_budget(500),16384)
        self.assertEqual(policy.exhaustion.token_budget(32000),768)
        self.assertIs(policy.exhaustion.outcome,policy.exhaustion.previous.outcome)
        result=policy.exhaustion.assess(dict(raw='WORKED_APPROACH_COUNT: 2\nREJECTED_APPROACH: NONE'))
        self.assertIsNone(result['semantic_verified_worked_approach_count'])
        self.assertFalse(result['admission'])
