from copy import deepcopy
import unittest

from gpu import orch_continual_exhaustion_keyed_runtime_v2 as version
from tests import test_orch_continual_exhaustion_keyed_runtime as previous


class EvidenceV2Tests(unittest.TestCase):
    def fixture(self):
        packet, result = previous.KeyedContinuationTests().fixture()
        target = ('I add 2+3=5.\nI consider subtraction instead of addition.\n'
            'I reject subtraction because the problem asks for a sum.\n'
            'I verify 5-3=2.\nI multiply the sum by 2: 5*2=10.\nFINAL: 10')
        packet[0].update(target_source_lines=version.transport.old.policy.source_lines(target),
            target_sha256=version.transport.old.policy.text_sha(target), gold='10',
            question='What is (2+3)*2?', student_prefix=[dict(role='user', content='What is (2+3)*2?')])
        review = result['reviews'][0]
        for field in ('has_meaningful_branch', 'branching_alternative', 'branch_rejection_reason'):
            review.pop(field, None)
        review.update(independent_answer='10', legacy_considered_and_rejected=False,
            legacy_alternative_line_ids=[], legacy_rejection_line_ids=[],
            branch_metrics=dict(measurement_status='UNKNOWN', semantic_distinct_approaches_considered=None,
                semantic_distinct_approaches_pursued=None, repetition_failure=None, repetition_reason='',
                repetition_line_ids=[], approaches=[]),
            r106=dict(measurement_status='MEASURED', departures_and_returns=[dict(
                main_line_ids=[1], departure_line_ids=[4], return_line_ids=[5], kind='CHECK',
                return_phase='MID_SOLUTION', return_to_main_computation=True,
                reason='The inverse check returns to multiplication of the computed sum.')],
                error=dict(status='UNKNOWN', evidence_line_ids=[], reason='Separate error measurement not asserted by this fixture.'),
                coherence=dict(status='UNKNOWN', evidence_line_ids=[], reason='Separate coherence measurement not asserted by this fixture.')))
        return packet, result

    def validate(self, packet, result):
        return version.validate_result(packet, result, version.digest(packet))

    def test_valid_check_positive_r106_without_rejected_path(self):
        packet, result = self.fixture()
        resolved = self.validate(packet, result)[0]
        self.assertFalse(resolved['has_meaningful_branch'])
        self.assertFalse(resolved['legacy_considered_and_rejected'])
        self.assertEqual(resolved['branching_alternative'], '')
        self.assertEqual(resolved['r106']['author_counts']['mid_solution'], 1)
        self.assertEqual(resolved['status'], 'PASS')

    def test_explicit_positive_legacy_claim_remains_positive(self):
        packet, result = self.fixture()
        result['reviews'][0].update(legacy_considered_and_rejected=True,
            legacy_alternative_line_ids=[2], legacy_rejection_line_ids=[3])
        resolved = self.validate(packet, result)[0]
        self.assertTrue(resolved['has_meaningful_branch'])
        self.assertEqual(resolved['branching_alternative'], packet[0]['target_source_lines'][1]['text'])
        self.assertEqual(resolved['branch_rejection_reason'], packet[0]['target_source_lines'][2]['text'])

    def test_missing_positive_legacy_evidence_fails_not_coerced_false(self):
        packet, result = self.fixture()
        for alternative, rejection in [([], []), ([2], []), ([], [3])]:
            changed = deepcopy(result)
            changed['reviews'][0].update(legacy_considered_and_rejected=True,
                legacy_alternative_line_ids=alternative, legacy_rejection_line_ids=rejection)
            before = deepcopy(changed)
            with self.assertRaises(ValueError):
                self.validate(packet, changed)
            self.assertEqual(changed, before)

    def test_negative_claim_cannot_silently_discard_evidence(self):
        packet, result = self.fixture()
        result['reviews'][0]['legacy_alternative_line_ids'] = [2]
        with self.assertRaisesRegex(ValueError, 'cannot_discard_evidence'):
            self.validate(packet, result)

    def test_sparse_selected_ids_form_declared_exact_inclusive_interval(self):
        packet, result = self.fixture()
        result['reviews'][0].update(legacy_considered_and_rejected=True,
            legacy_alternative_line_ids=[1, 3], legacy_rejection_line_ids=[3])
        resolved = self.validate(packet, result)[0]
        self.assertEqual(resolved['branching_alternative'], ''.join(item['text'] for item in packet[0]['target_source_lines'][:3]))
        self.assertEqual(resolved['legacy_alternative_line_ids'], [1, 3])

    def test_historical_retyped_fields_and_hashes_rejected(self):
        packet, result = self.fixture()
        for field, value in [('has_meaningful_branch', True), ('branching_alternative', 'paraphrase'),
                             ('branch_rejection_reason', 'paraphrase'), ('target_sha256', packet[0]['target_sha256'])]:
            changed = deepcopy(result)
            changed['reviews'][0][field] = value
            with self.assertRaisesRegex(ValueError, 'no_legacy_strings_hashes_or_rehydration'):
                self.validate(packet, changed)

    def test_terminal_final_not_mid_solution(self):
        packet, result = self.fixture()
        branch = result['reviews'][0]['r106']['departures_and_returns'][0]
        branch['return_line_ids'] = [6]
        with self.assertRaisesRegex(ValueError, 'terminal_final_is_not_mid_solution'):
            self.validate(packet, result)
        branch.update(return_phase='TERMINAL_CHECK_OR_ASIDE', return_to_main_computation=False)
        resolved = self.validate(packet, result)[0]['r106']
        self.assertEqual(resolved['author_counts'], dict(departures_and_returns=1, mid_solution=0, terminal_check_or_aside=1))

    def test_phase_cannot_claim_mid_without_resumed_computation(self):
        packet, result = self.fixture()
        result['reviews'][0]['r106']['departures_and_returns'][0]['return_to_main_computation'] = False
        with self.assertRaisesRegex(ValueError, 'return_phase_consistency'):
            self.validate(packet, result)

    def test_order_out_of_range_missing_and_duplicate_evidence_rejected(self):
        packet, result = self.fixture()
        for key, ids in [('main_line_ids', [5]), ('departure_line_ids', []), ('return_line_ids', [999]),
                         ('departure_line_ids', [4, 4]), ('main_line_ids', [True])]:
            changed = deepcopy(result)
            changed['reviews'][0]['r106']['departures_and_returns'][0][key] = ids
            with self.assertRaises(ValueError):
                self.validate(packet, changed)
        branch = result['reviews'][0]['r106']['departures_and_returns'][0]
        result['reviews'][0]['r106']['departures_and_returns'] = [deepcopy(branch), deepcopy(branch)]
        with self.assertRaisesRegex(ValueError, 'duplicate_departure_evidence'):
            self.validate(packet, result)

    def test_unknown_does_not_become_zero_or_positive_certificate(self):
        packet, result = self.fixture()
        result['reviews'][0]['r106']['measurement_status'] = 'UNKNOWN'
        with self.assertRaisesRegex(ValueError, 'unknown_r106_not_positive'):
            self.validate(packet, result)
        result['reviews'][0]['r106']['departures_and_returns'] = []
        counts = self.validate(packet, result)[0]['r106']['author_counts']
        self.assertTrue(all(value is None for value in counts.values()))

    def test_error_coherence_and_repetition_are_separate(self):
        packet, result = self.fixture()
        result['reviews'][0]['r106']['error'] = dict(status='ERROR_OBSERVED', evidence_line_ids=[2], reason='Separate descriptive fixture.')
        resolved = self.validate(packet, result)[0]
        self.assertEqual(resolved['r106']['error']['source_evidence_spans'], [packet[0]['target_source_lines'][1]['text']])
        self.assertEqual(resolved['r106']['coherence']['status'], 'UNKNOWN')
        self.assertIsNone(resolved['branch_metrics']['repetition_failure'])

    def test_frozen_gold_and_quality_checks_still_reject_false_PASS(self):
        packet, result = self.fixture()
        for change in (dict(grounded_operations=False), dict(independent_answer='11'), dict(full_text_read=False), dict(evidence_line_ids=[999])):
            changed = deepcopy(result)
            changed['reviews'][0].update(change)
            with self.assertRaises(ValueError):
                self.validate(packet, changed)

    def test_numeric_answer_is_not_repaired_or_coerced(self):
        packet, result = self.fixture()
        for answer in (10, '10 ', '+10', '1e1'):
            changed = deepcopy(result)
            changed['reviews'][0]['independent_answer'] = answer
            with self.assertRaisesRegex(ValueError, 'canonical_numeric_string_required'):
                self.validate(packet, changed)

    def test_schema_has_source_ids_not_retyped_strings_or_legacy_flag(self):
        properties = version.response_schema(6)['properties']['reviews']['items']['properties']
        self.assertNotIn('has_meaningful_branch', properties)
        self.assertNotIn('branching_alternative', properties)
        self.assertNotIn('branch_rejection_reason', properties)
        for key in ('legacy_considered_and_rejected', 'legacy_alternative_line_ids', 'legacy_rejection_line_ids', 'r106'):
            self.assertIn(key, properties)

    def test_builder_delegation_preserves_historical_criteria_and_bounds(self):
        config, allocation = previous.KeyedContinuationTests().config_allocation()
        allocation.update(serialization_contract=version.SCHEMA, maximum_additional_review_calls=118,
            approved_by='BUILDER_USER_DELEGATED', delegated_authority=version.BUILDER_AUTHORITY,
            historical_acceptance_unchanged=True, r107_selection_enabled=False)
        version.validate_allocation(allocation, config, 'a' * 64, version.transport.CUTOFF - 1)
        self.assertEqual(allocation['approved_by'], 'BUILDER_USER_DELEGATED')
        for change in (dict(delegated_authority=''), dict(historical_acceptance_unchanged=False),
                       dict(r107_selection_enabled=True), dict(maximum_additional_review_calls=128),
                       dict(deadline_unix=version.transport.DEADLINE + 60)):
            with self.assertRaises(ValueError):
                version.validate_allocation(dict(allocation, **change), config, 'a' * 64, version.transport.CUTOFF - 1)

    def test_main_must_allocate_v2_with_118_or_lower_additional_cap(self):
        config, allocation = previous.KeyedContinuationTests().config_allocation()
        allocation.update(serialization_contract=version.SCHEMA, maximum_additional_review_calls=118)
        version.validate_allocation(allocation, config, 'a' * 64, version.transport.CUTOFF - 1)
        for change in (dict(serialization_contract='V1'), dict(maximum_additional_review_calls=128),
                       dict(maximum_additional_review_calls=119), dict(maximum_additional_review_calls=True)):
            with self.assertRaises(ValueError):
                version.validate_allocation(dict(allocation, **change), config, 'a' * 64, version.transport.CUTOFF - 1)


if __name__ == '__main__':
    unittest.main()
