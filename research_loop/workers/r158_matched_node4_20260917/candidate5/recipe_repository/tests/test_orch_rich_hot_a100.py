import unittest

from organism_v6 import orch_rich_hot_a100 as policy
from gpu import orch_rich_hot_a100_run as runner


class RichHotA100Tests(unittest.TestCase):
    def test_excludes_peer_gpus(self):
        for index in (0, 1, -1, 8):
            with self.assertRaises(ValueError):
                policy.allocation(index)
        self.assertEqual(set(policy.DEVICES), {2, 3, 4, 5, 6, 7})

    def test_disjoint_paired_shards(self):
        for first, second in ((2, 4), (3, 5), (7, 6)):
            self.assertEqual(policy.allocation(first)[0], policy.allocation(second)[0])
            self.assertEqual({policy.allocation(first)[1], policy.allocation(second)[1]}, {0, 1})
        self.assertLessEqual(256 * 2, policy.MAX_CALLS)

    def test_context_no_crop_and_top_cap(self):
        self.assertEqual(policy.budget(512), 8192)
        self.assertEqual(policy.budget(9000), 7384)
        for count in (0, 16384, 20000):
            with self.assertRaises(ValueError):
                policy.budget(count)

    def test_original_numeric_parser_retained(self):
        task = dict(gold='12')
        for text, correct in [('FINAL: 12', True), ('FINAL: 11', False), ('12', False), ('FINAL: 12\nextra', False)]:
            result = policy.outcome(task, dict(raw=text, token_ids=[2, 3], terminal=True, truncated=False))
            self.assertEqual(result['outcome_pass'], correct)
            self.assertFalse(result['admitted'])
            self.assertEqual(result['semantic_status'], 'UNREVIEWED')

    def test_truncated_correct_retains_both_facts(self):
        result = policy.outcome(dict(gold='12'), dict(raw='FINAL: 12', token_ids=[1], terminal=False, truncated=True))
        self.assertTrue(result['outcome_pass'])
        self.assertFalse(result['terminal_correct'])

    def test_conditional_new_unconditional_reconsider(self):
        self.assertFalse(policy.followup_allowed('ORIGINAL_RICH', dict(outcome_pass=False)))
        self.assertTrue(policy.followup_allowed('LIGHT_BRANCH', dict(outcome_pass=True)))
        self.assertTrue(policy.followup_allowed('SELF_EVALUATE', dict(outcome_pass=False)))

    def test_no_gold_in_prompts_and_actual_draft(self):
        task = dict(question='Compute the quantity.', gold='987654321')
        for strategy in ('ORIGINAL_RICH', 'LIGHT_BRANCH', 'SELF_EVALUATE'):
            messages = policy.messages(task, strategy, 'actual native draft')
            self.assertEqual(messages[-2]['content'], 'actual native draft')
            self.assertNotIn(task['gold'], str(messages))
            self.assertNotIn('150–400', str(messages))

    def test_fixed_lifetime_lease_margin(self):
        result = policy.lease_deadline(1000, 100000)
        self.assertEqual(result['hard_deadline_unix'], 44200)
        with self.assertRaises(ValueError):
            policy.lease_deadline(1000, 50000)

    def test_own_engine_not_intensity_caps(self):
        self.assertEqual(runner.Engine.__bases__, (runner.portable.source.Engine,))
        self.assertEqual(policy.CAP, 8192)


if __name__ == '__main__':
    unittest.main()
