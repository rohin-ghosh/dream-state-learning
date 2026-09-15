import json
from pathlib import Path
import tempfile
import unittest

from gpu.orch_l2_rich_math_audit import candidate_dispositions, held_failure_category, provider_evidence, verify_manifest, verify_sleep, sha


class RichMathAuditTests(unittest.TestCase):
    def outer(self, turns):
        return dict(num_turns=turns, modelUsage={'claude-sonnet-5[1m]': {}, 'claude-haiku-4-5': {}},
                    usage={'iterations': [{}]}, is_error=False)

    def test_one_turn_still_does_not_prove_exact_call_count(self):
        receipt = provider_evidence(self.outer(1))
        self.assertEqual(receipt['accounted_call_lower_bound'], 2)
        self.assertFalse(receipt['exact_call_count_known'])
        self.assertIsNone(receipt['actual_provider_calls'])

    def test_two_and_four_turns_exceed_two_reserved_slots(self):
        for turns, expected in ((2, 3), (4, 5)):
            with self.subTest(turns=turns):
                receipt = provider_evidence(self.outer(turns))
                self.assertEqual(receipt['accounted_call_lower_bound'], expected)
                self.assertEqual(receipt['usage_iteration_entries'], 1)

    def test_failed_invocations_still_count(self):
        outer = self.outer(4)
        outer['is_error'] = True
        self.assertEqual(provider_evidence(outer)['accounted_call_lower_bound'], 5)

    def test_missing_or_unknown_usage_is_not_two_calls(self):
        for outer in ({}, {'num_turns': 1}, {'num_turns': True},
                      dict(num_turns=1, modelUsage={'unknown': {}})):
            receipt = provider_evidence(outer)
            self.assertFalse(receipt['accounting_evidence_complete'])
            self.assertIsNone(receipt['accounted_call_lower_bound'])

    def test_native_turn_distribution_reconciles_to_151_not_142(self):
        rows = [provider_evidence(self.outer(turns)) for turns in [1] * 64 + [2] * 6 + [4]]
        self.assertEqual(sum(row['reported_main_turns'] for row in rows), 80)
        self.assertEqual(sum(row['accounted_call_lower_bound'] for row in rows), 151)

    def test_sleep_requires_actual_persisted_losses(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            previous = {'state': 'before'}
            receipt = dict(input_adapter=previous, output_adapter={'state': 'after'}, updates=2, fits=1)
            with self.assertRaisesRegex(ValueError, 'sleep_loss_count_mismatch'):
                verify_sleep(directory, receipt, previous, False)
            (directory / 'LOSSES.jsonl').write_text('\n'.join(json.dumps(dict(update=update, loss=0.5)) for update in (1, 2)))
            self.assertEqual(verify_sleep(directory, receipt, previous, False), 2)
            with self.assertRaisesRegex(ValueError, 'zero_or_frozen_sleep_changed_state'):
                verify_sleep(directory, receipt, previous, True)

    def test_zero_yield_keeps_exact_identity(self):
        with tempfile.TemporaryDirectory() as temporary:
            previous = {'state': 'before'}
            receipt = dict(input_adapter=previous, output_adapter=previous, updates=0, fits=0)
            self.assertEqual(verify_sleep(Path(temporary), receipt, previous, False), 0)
            receipt['output_adapter'] = {'state': 'after'}
            with self.assertRaisesRegex(ValueError, 'zero_or_frozen_sleep_changed_state'):
                verify_sleep(Path(temporary), receipt, previous, False)

    def test_manifest_detects_changed_bytes_and_unlisted_files(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            root = directory / 'native'
            root.mkdir()
            artifact = root / 'COMPLETE.json'
            artifact.write_text('{}')
            manifest = directory / 'manifest'
            manifest.write_text(sha(artifact) + '  ./COMPLETE.json\n')
            self.assertEqual(verify_manifest(root, manifest), 1)
            (root / 'extra.json').write_text('{}')
            with self.assertRaisesRegex(ValueError, 'native_manifest_file_set_mismatch'):
                verify_manifest(root, manifest)
            artifact.write_text('{"modified":true}')
            with self.assertRaisesRegex(ValueError, 'native_file_digest_mismatch'):
                verify_manifest(root, manifest)

    def test_prefilter_and_invalid_review_are_not_semantic_fail(self):
        rows = [dict(index=0, candidate=False, admitted=False, semantic_status='UNREVIEWED'),
                dict(index=1, candidate=True, admitted=False, semantic_status='UNREVIEWED'),
                dict(index=2, candidate=True, admitted=False, semantic_status='FAIL'),
                dict(index=3, candidate=True, admitted=True, semantic_status='PASS')]
        receipt = candidate_dispositions(rows, {1: 'PARENT_RESPONSE_REJECTED'})
        self.assertEqual(receipt['eligible_candidates'], 3)
        self.assertEqual(receipt['prefiltered'], 1)
        self.assertEqual(receipt['semantic_fail'], 1)
        self.assertEqual(receipt['no_valid_review'], 1)
        self.assertEqual(receipt['admitted'], 1)
        self.assertEqual(receipt['no_valid_review_reasons'], {'PARENT_RESPONSE_REJECTED': 1})

    def test_zero_candidate_cycle_has_no_semantic_failures(self):
        rows = [dict(index=0, candidate=False, admitted=False, semantic_status='UNREVIEWED')]
        receipt = candidate_dispositions(rows, {})
        self.assertEqual(receipt['eligible_candidates'], 0)
        self.assertEqual(receipt['semantic_fail'], 0)
        self.assertEqual(receipt['no_valid_review'], 0)

    def test_unknown_candidate_disposition_fails_closed(self):
        rows = [dict(index=0, candidate=True, admitted=False, semantic_status='OTHER')]
        with self.assertRaisesRegex(ValueError, 'unclassified_candidate_disposition'):
            candidate_dispositions(rows, {})

    def test_missing_registered_final_does_not_infer_answer_from_prose(self):
        held = dict(correct=False, answer=None)
        response = dict(terminal=True, truncated=False, raw='Both conditions are satisfied. FINAL: 8', content_tokens=498)
        self.assertEqual(held_failure_category(held, response), 'missing_exact_FINAL')
        self.assertIsNone(held['answer'])
        self.assertFalse(held['correct'])

    def test_truncation_precedes_null_or_wrong_registered_answer(self):
        for answer in (None, '999'):
            held = dict(correct=False, answer=answer)
            response = dict(terminal=False, truncated=True)
            self.assertEqual(held_failure_category(held, response), 'truncation')

    def test_partition_preserves_registered_success_wrong_and_nonterminal(self):
        response = dict(terminal=True, truncated=False)
        self.assertEqual(held_failure_category(dict(correct=True, answer='8'), response), 'registered_correct')
        self.assertEqual(held_failure_category(dict(correct=False, answer='999'), response), 'parsed_wrong')
        response['terminal'] = False
        self.assertEqual(held_failure_category(dict(correct=False, answer=None), response), 'nonterminal_other')
        with self.assertRaisesRegex(ValueError, 'registered_correct_with_invalid_completion'):
            held_failure_category(dict(correct=True, answer='8'), response)


if __name__ == '__main__':
    unittest.main()
