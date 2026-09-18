from copy import deepcopy
import unittest

from gpu import orch_continual_batch_publish as publisher
from gpu.orch_continual_batch_snapshot_node2 import normalized_call
from organism_v6 import orch_continual_batch as policy


class SerializationTests(unittest.TestCase):
    def test_node2_normalization_preserves_original(self):
        call = dict(stage='final', condition='ORIGINAL_RICH', messages=[{}, {}],
            trainingAllowed=False, outcome=dict(correct=True, admitted=False))
        before = deepcopy(call)
        adapted = normalized_call(call)
        self.assertEqual(call, before)
        self.assertEqual(adapted['stage'], 'source')
        self.assertTrue(adapted['outcome']['outcome_pass'])

    def test_node2_wrong_outcome_not_repaired(self):
        call = dict(stage='final', condition='ORIGINAL_RICH', messages=[{}, {}],
            trainingAllowed=False, outcome=dict(correct=False, admitted=False))
        with self.assertRaisesRegex(ValueError, 'observed_original_oracle'):
            normalized_call(call)

    def test_node2_second_pass_requires_registered_condition(self):
        call = dict(stage='final', condition='OTHER', messages=[{}, {}, {}, {}],
            trainingAllowed=False, outcome=dict(correct=True, admitted=False))
        with self.assertRaisesRegex(ValueError, 'registered_own_second_pass'):
            normalized_call(call)
    def fixture(self):
        target = 'A quoted "check" uses 2+3=5.\r\n\nFINAL: 5'
        row = dict(target=target, target_sha256=policy.text_sha(target), gold='5',
                   provenance=dict(raw_call_sha256='raw'), student_prefix_sha256='prefix')
        review = dict(target_sha256=row['target_sha256'], raw_call_sha256='raw',
            student_prefix_sha256='prefix', evidence_line_ids=[1, 3], independent_answer='5',
            status='PASS', full_text_read=True, reason='Addition is valid.', gold_status='VALID',
            **dict.fromkeys(policy.AXES, True))
        return row, dict(reviews=[review])

    def test_numbered_lines_preserve_all_original_bytes(self):
        row, result = self.fixture()
        before = deepcopy(result)
        resolved = policy.resolve_line_reviews([row], result)
        self.assertEqual(''.join(line['text'] for line in policy.source_lines(row['target'])), row['target'])
        self.assertEqual(resolved['reviews'][0]['evidence_spans'], ['A quoted "check" uses 2+3=5.\r\n', 'FINAL: 5'])
        self.assertEqual(result, before)
        policy.validate_review([row], resolved)

    def test_invalid_line_ids_fail_without_fabricating(self):
        for identifiers in ([], [0], [4], [True], ['1'], [1, 1], None):
            with self.subTest(identifiers=identifiers):
                row, result = self.fixture()
                result['reviews'][0]['evidence_line_ids'] = identifiers
                with self.assertRaises(ValueError):
                    policy.resolve_line_reviews([row], result)

    def test_target_mutation_is_rejected(self):
        row, result = self.fixture()
        row['target'] += ' altered'
        with self.assertRaisesRegex(ValueError, 'immutable_target'):
            policy.resolve_line_reviews([row], result)

    def test_retyped_spans_are_not_silently_replaced(self):
        row, result = self.fixture()
        result['reviews'][0]['evidence_spans'] = ['invented']
        with self.assertRaisesRegex(ValueError, 'not_retype'):
            policy.resolve_line_reviews([row], result)

    def test_numeric_format_is_strict_and_never_repaired(self):
        for answer in ('5 dollars', 'FINAL: 5', ' 5', '+5', '1,000', '5e0', '01', '1/0', 5):
            with self.subTest(answer=answer):
                row, result = self.fixture()
                result['reviews'][0]['independent_answer'] = answer
                with self.assertRaisesRegex(ValueError, 'canonical_numeric'):
                    policy.resolve_line_reviews([row], result)

    def test_lossless_decimal_and_fraction_strings_preserved(self):
        for answer in ('5', '-2', '0.25', '1/3', '5.00'):
            row, result = self.fixture()
            result['reviews'][0]['independent_answer'] = answer
            result['reviews'][0]['gold_status'] = 'INVALID'
            self.assertEqual(policy.resolve_line_reviews([row], result)['reviews'][0]['independent_answer'], answer)

    def test_wrong_answer_is_not_fixed_to_gold(self):
        row, result = self.fixture()
        result['reviews'][0]['independent_answer'] = '6'
        with self.assertRaisesRegex(ValueError, 'unverified_gold_VALID'):
            policy.resolve_line_reviews([row], result)
        self.assertEqual(result['reviews'][0]['independent_answer'], '6')

    def test_valid_gold_must_match_even_on_failed_review(self):
        row, result = self.fixture()
        result['reviews'][0].update(independent_answer='6', status='FAIL')
        with self.assertRaisesRegex(ValueError, 'unverified_gold_VALID'):
            policy.resolve_line_reviews([row], result)

    def test_branch_measurement_cannot_invent_alternative(self):
        row, result = self.fixture()
        result['reviews'][0].update(has_meaningful_branch=True, branching_alternative='imagined branch',
                                   branch_rejection_reason='imagined reason')
        with self.assertRaisesRegex(ValueError, 'branch_measurement'):
            policy.resolve_line_reviews([row], result)

    def test_old_serialization_default_unchanged(self):
        self.assertFalse(publisher.LINE_REVIEWS)
        self.assertIn('evidence_spans', publisher.schema()['properties']['reviews']['items']['properties'])

    def test_future_schema_uses_numbered_lines(self):
        original = publisher.LINE_REVIEWS
        try:
            publisher.LINE_REVIEWS = True
            properties = publisher.schema()['properties']['reviews']['items']['properties']
            self.assertIn('evidence_line_ids', properties)
            self.assertNotIn('evidence_spans', properties)
            self.assertIn('pattern', properties['independent_answer'])
        finally:
            publisher.LINE_REVIEWS = original


if __name__ == '__main__':
    unittest.main()
