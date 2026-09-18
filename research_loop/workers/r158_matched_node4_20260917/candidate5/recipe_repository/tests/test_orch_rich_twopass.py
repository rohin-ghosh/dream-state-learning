from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from gpu import orch_rich_twopass_run as run
from organism_v6 import orch_rich_twopass as policy


class TwoPassTests(unittest.TestCase):
    def setUp(self):
        self.task = dict(id='synthetic-task', family='group_accounting', question='A synthetic arithmetic question.', gold='87654321')

    def response(self, tokens=200, prompt_tokens=2200):
        return dict(raw='I retain the actual preceding draft and give my answer.\nFINAL: 87654321',
                    token_ids=[7] * tokens + [8], terminal=True, truncated=False, prompt_tokens=prompt_tokens)

    def test_common_draft_is_exact_old_prompt_and_contains_no_gold_hint(self):
        actual, neutral = policy.prompt(self.task, 'draft')
        self.assertEqual((actual, neutral), policy.original.prompt(self.task, 'rich'))
        self.assertNotIn(self.task['gold'], str(actual))

    def test_conditions_share_truthful_neutral_draft_and_equal_caps(self):
        first_actual, first_neutral = policy.prompt(self.task, 'final', 'BRANCH', 'my exact draft')
        second_actual, second_neutral = policy.prompt(self.task, 'final', 'CONTINUE', 'my exact draft')
        self.assertEqual(first_neutral, second_neutral)
        self.assertEqual(first_neutral[1]['content'], 'my exact draft')
        self.assertNotEqual(first_actual, second_actual)
        for text in (policy.BRANCH_GUIDANCE, policy.CONTINUE_GUIDANCE, policy.FINAL_SYSTEM):
            self.assertNotIn(text, str(first_neutral))
        self.assertEqual(policy.CAPS, dict(draft=512, final=1536, record=512))

    def test_future_branch_guidance_requires_rejection_evidence_when_relevant(self):
        self.assertIn('Before the FINAL line', policy.BRANCH_GUIDANCE)
        self.assertIn('alternative you considered', policy.BRANCH_GUIDANCE)
        self.assertIn('made you reject it, when relevant', policy.BRANCH_GUIDANCE)
        self.assertIn('Do not manufacture disagreement', policy.BRANCH_GUIDANCE)
        self.assertNotIn('alternative you considered', policy.CONTINUE_GUIDANCE)

    def test_NEW_record_preserves_draft_and_final_without_branch_guidance(self):
        actual, neutral = policy.prompt(self.task, 'record', 'BRANCH', 'draft unchanged', 'final unchanged')
        self.assertEqual(actual[-1]['content'], policy.record.NEW_RECORD)
        self.assertEqual(neutral[1]['content'], 'draft unchanged')
        self.assertEqual(neutral[3]['content'], 'final unchanged')
        self.assertNotIn(policy.BRANCH_GUIDANCE, str(neutral))
        self.assertNotIn(policy.record.NEW_RECORD, str(neutral))
        self.assertEqual(len(neutral), 5)

    def test_long_source_is_never_cropped_or_automatically_admitted(self):
        response = self.response(tokens=1000)
        row = policy.capture(self.task, 'final', 'BRANCH', response, [], 'a' * 64)
        self.assertFalse(row['candidate'])
        self.assertFalse(row['admitted'])
        self.assertTrue(row['long_source'])
        self.assertEqual(row['target'], response['raw'])
        self.assertEqual(row['call']['token_ids'], response['token_ids'])

    def test_RAW85_context_changes_only_this_arm_and_target_bounds_remain(self):
        response = self.response()
        old = policy.original.capture(self.task, 'rich', response, [])
        current = policy.capture(self.task, 'final', 'CONTINUE', response, [])
        self.assertFalse(old['token_contract_pass'])
        self.assertTrue(current['token_contract_pass'])
        for tokens in (149, 401):
            self.assertFalse(policy.capture(self.task, 'record', 'BRANCH', self.response(tokens=tokens), [])['candidate'])
        self.assertFalse(policy.capture(self.task, 'record', 'BRANCH', self.response(prompt_tokens=4097), [])['candidate'])

    def test_shared_draft_never_becomes_a_condition_target(self):
        row = policy.capture(self.task, 'draft', 'SHARED', self.response(), [])
        self.assertFalse(row['candidate'])
        with self.assertRaisesRegex(ValueError, 'shared_draft_is_source'):
            policy.admit(row, {}, {})

    def test_record_depends_only_on_completed_final_outcome(self):
        self.assertTrue(policy.record_allowed(dict(status='OK', outcome_pass=True, candidate=False)))
        self.assertFalse(policy.record_allowed(dict(status='OK', outcome_pass=False)))
        self.assertFalse(policy.record_allowed(dict(status='ERROR', outcome_pass=True)))

    def test_admission_delegates_unchanged_support_and_gold_gate(self):
        row = dict(stage='record')
        with patch.object(policy.admission, 'admit', return_value={'admitted': False}) as admit:
            self.assertEqual(policy.admit(row, {'status': 'UNRESOLVED'}, {'status': 'AMBIGUOUS'}), {'admitted': False})
            admit.assert_called_once_with(row, {'status': 'UNRESOLVED'}, {'status': 'AMBIGUOUS'})

    def test_reservations_precede_calls_prevent_repeats_and_enforce_lifetime_cap(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with patch.object(policy, 'MAX_CALLS', 2):
                self.assertEqual(run.reserve(root, 0, 'draft', 'SHARED'), 0)
                with self.assertRaises(FileExistsError):
                    run.reserve(root, 0, 'draft', 'SHARED')
                self.assertEqual(run.reserve(root, 0, 'final', 'BRANCH'), 1)
                with self.assertRaises(AssertionError):
                    run.reserve(root, 0, 'record', 'BRANCH')
            self.assertEqual(len((root / 'CALLS.jsonl').read_text().splitlines()), 2)


if __name__ == '__main__':
    unittest.main()
