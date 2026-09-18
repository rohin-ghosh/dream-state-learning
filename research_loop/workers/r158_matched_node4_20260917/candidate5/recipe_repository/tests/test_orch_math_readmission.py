import copy
import hashlib
import unittest

from organism_v6 import orch_math_readmission as policy
from organism_v6 import orch_math_rich as original


class ReadmissionTests(unittest.TestCase):
    def setUp(self):
        target = 'Two plus two is four. FINAL is checked below.\nFINAL: 4'
        self.row = dict(target=target, target_sha256=hashlib.sha256(target.encode()).hexdigest(),
            student_prefix=[dict(role='user', content='What is two plus two?')], task_id='train-1',
            call=dict(raw=target, terminal=True, truncated=False, token_ids=[1] * 101),
            generated_tokens=100, gold='4', outcome_pass=True, admitted=False,
            semantic_status='FAIL', token_contract_pass=False)
        self.review = dict(target_sha256=self.row['target_sha256'],
            student_prefix_sha256=original.digest(self.row['student_prefix']), raw_call_sha256='capture',
            full_text_read=True, reason='Content passes; original failure was register only.',
            evidence_spans=['Two plus two is four.'], status='FAIL', first_person=False,
            prefix_reason='All operations follow from the supplied question.',
            **{axis: True for axis in policy.CONTENT_AXES})
        self.gold = dict(status='VALID', independent_answer='4')

    def reassess(self, **kwargs):
        return policy.reassess(self.row, self.review, self.gold, 'capture', **kwargs)

    def test_register_and_short_length_are_not_gates(self):
        result = self.reassess()
        self.assertTrue(result['eligible'])
        self.assertEqual(result['length_tag'], 'under150')
        self.assertFalse(result['first_person'])

    def test_long_complete_output_is_eligible(self):
        self.row['call']['token_ids'] = [1] * 701
        self.row['generated_tokens'] = 700
        self.assertTrue(self.reassess()['eligible'])

    def test_original_artifacts_are_not_mutated(self):
        before = copy.deepcopy((self.row, self.review, self.gold))
        self.reassess()
        self.assertEqual((self.row, self.review, self.gold), before)

    def test_content_failures_and_unknowns_are_not_waived(self):
        for axis in policy.CONTENT_AXES:
            for value in (False, None):
                with self.subTest(axis=axis, value=value):
                    self.review[axis] = value
                    self.assertFalse(self.reassess()['eligible'])
            self.review[axis] = True

    def test_incorrect_outcome_is_not_waived(self):
        self.row['outcome_pass'] = False
        self.assertFalse(self.reassess()['eligible'])

    def test_gold_uncertainty_is_not_waived(self):
        self.gold['status'] = 'AMBIGUOUS'
        self.assertFalse(self.reassess()['eligible'])

    def test_held_task_is_excluded(self):
        self.assertFalse(self.reassess(excluded_ids={'train-1'})['eligible'])

    def test_truncated_output_is_not_waived(self):
        self.row['call']['truncated'] = True
        self.assertFalse(self.reassess()['eligible'])

    def test_target_tampering_fails(self):
        self.row['target'] += ' changed'
        with self.assertRaisesRegex(ValueError, 'source_target'):
            self.reassess()

    def test_prefix_tampering_fails(self):
        self.row['student_prefix'][0]['content'] = 'Different question'
        with self.assertRaisesRegex(ValueError, 'review_prefix'):
            self.reassess()

    def test_capture_tampering_fails(self):
        self.review['raw_call_sha256'] = 'different'
        with self.assertRaisesRegex(ValueError, 'review_capture'):
            self.reassess()

    def test_branching_is_not_falsely_certified(self):
        self.assertEqual(self.reassess()['branching_status'], 'NOT_ASSESSED_BY_THIS_EXISTING_REVIEW')


if __name__ == '__main__':
    unittest.main()
