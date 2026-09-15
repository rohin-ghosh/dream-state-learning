import unittest

from organism_v6 import orch_rich_hot_node1_exhaustion as policy


class ExhaustionTests(unittest.TestCase):
    def test_unsteered_control_and_labelled_other_arms(self):
        task = dict(question='QUESTION_ONLY', gold='HIDDEN_ANSWER')
        only = policy.messages(task, 'ORIGINAL_RICH')
        self.assertIn('EXHAUSTION_ONLY', only[0]['content'])
        self.assertNotIn(policy.STEERING, only[0]['content'])
        self.assertNotIn('HIDDEN_ANSWER', str(only))
        for condition in policy.CONDITIONS[1:]:
            messages = policy.messages(task, condition)
            self.assertIn('EXHAUSTION_PLUS_STEERING', messages[0]['content'])
            self.assertIn(policy.STEERING, messages[0]['content'])

    def test_two_worked_approaches_and_no_fabricated_evidence(self):
        self.assertIn('at least two', policy.EXHAUSTION)
        self.assertIn('hypotheses', policy.EXHAUSTION)
        self.assertIn('specific evidence', policy.EXHAUSTION)
        self.assertIn('Never invent', policy.EXHAUSTION)
        self.assertIn('Repetition is a failure', policy.EXHAUSTION)
        self.assertNotIn('150', policy.EXHAUSTION)
        self.assertNotIn('first-person', policy.EXHAUSTION)

    def test_actual_stage_two_context_remainder(self):
        self.assertEqual(policy.token_budget(600), 16384)
        self.assertEqual(policy.token_budget(17000), 15768)
        self.assertEqual(policy.token_budget(32767), 1)
        with self.assertRaises(ValueError):
            policy.token_budget(32768)

    def test_own_first_pass_truthful_and_oracle_unchanged(self):
        first = 'Actual first pass, not a teacher answer.'
        messages = policy.messages(dict(question='QUESTION'), 'TWO_PASS', first)
        self.assertEqual(messages[2]['content'], first)
        self.assertIn('not an external', messages[3]['content'])
        self.assertIs(policy.outcome, policy.previous.outcome)

    def test_self_reports_are_not_semantic_verified(self):
        assessment = policy.assess(dict(raw='WORKED_APPROACH_COUNT: 2\nREJECTED_APPROACH: guess; violates given 5\nFINAL: 5'))
        self.assertEqual(assessment['self_reported_worked_approach_count'], 2)
        self.assertEqual(assessment['self_reported_rejected_approach_count'], 1)
        self.assertIsNone(assessment['semantic_verified_worked_approach_count'])
        self.assertFalse(assessment['admission'])

    def test_repetition_never_counts_as_branching(self):
        assessment = policy.assess(dict(raw='Repeating exactly the same unsupported claim.\n' * 4))
        self.assertEqual(assessment['repeated_substantive_lines'], 3)
        self.assertTrue(assessment['repetition_failure_signal'])
        self.assertFalse(assessment['repetition_counts_as_useful_branch'])
        self.assertIsNone(assessment['self_reported_worked_approach_count'])
