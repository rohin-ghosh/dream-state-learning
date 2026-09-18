from copy import deepcopy
from datetime import datetime, timezone
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from gpu import orch_continual_exhaustion_publish as publish
from organism_v6 import orch_continual_batch as policy
from tests import test_orch_continual_batch_remote_feed as fixtures


class ExhaustionPublisherTests(unittest.TestCase):
    def test_exact_deadline(self):
        self.assertEqual(datetime.fromtimestamp(publish.DEADLINE, timezone.utc).isoformat(),
                         '2026-09-15T08:00:00+00:00')

    def test_new_128_not_old_reset(self):
        original = dict(reserved=0, limit=128, old_reserved=96)
        result = publish.reserve_budget(original, publish.DEADLINE, publish.DEADLINE - 1000)
        self.assertEqual(result['reserved'], 2)
        self.assertEqual(original['reserved'], 0)
        self.assertEqual(result['old_reserved'], 96)

    def test_no_65th_review_batch(self):
        state = dict(reserved=0, limit=128, old_reserved=96)
        for number in range(64):
            state = publish.reserve_budget(state, publish.DEADLINE, publish.DEADLINE - 1000)
        self.assertEqual(state['reserved'], 128)
        with self.assertRaises(ValueError):
            publish.reserve_budget(state, publish.DEADLINE, publish.DEADLINE - 1000)

    def test_dispatch_margin_and_deadline_not_extended(self):
        for deadline, now in [(publish.DEADLINE, publish.DEADLINE - 660),
                              (publish.DEADLINE + 1, publish.DEADLINE - 1000)]:
            with self.assertRaises(ValueError):
                publish.reserve_budget(dict(reserved=0, limit=128, old_reserved=96), deadline, now)

    def test_invalid_ledgers_fail(self):
        for reserved, limit, old in [(1, 128, 96), (-2, 128, 96), (0, 256, 96), (0, 128, 0), (False, 128, 96)]:
            with self.assertRaises(ValueError):
                publish.reserve_budget(dict(reserved=reserved, limit=limit, old_reserved=old),
                                       publish.DEADLINE, publish.DEADLINE - 1000)

    def fixture(self):
        row, review = fixtures.NativeFeedTests().branch_fixture()
        for approach in review['branch_metrics']['approaches']:
            approach.update(method_kind='SAME_PREMISE_METHOD', distinctness_reason='Different operation.',
                            worked_line_ids=approach['pursued_line_ids'])
        return row, review

    def test_rejected_method_not_automatic_failure(self):
        row, review = self.fixture()
        result = publish.validate_reviews([row], {'reviews': [review]})
        self.assertEqual(result[0]['status'], 'PASS')
        self.assertEqual(publish.method_measurement(result[0])['same_premise_worked_methods'], 1)

    def test_counterfactual_not_counted_as_worked_method(self):
        row, review = self.fixture()
        review['branch_metrics']['approaches'][1]['method_kind'] = 'COUNTERFACTUAL'
        measured = publish.method_measurement(publish.validate_reviews([row], {'reviews': [review]})[0])
        self.assertEqual(measured['same_premise_worked_methods'], 0)
        self.assertEqual(measured['category_counts']['COUNTERFACTUAL'], 1)

    def test_invalid_worked_line_fails(self):
        row, review = self.fixture()
        review['branch_metrics']['approaches'][1]['worked_line_ids'] = [900]
        with self.assertRaises(ValueError):
            publish.validate_reviews([row], {'reviews': [review]})

    def test_unknown_is_not_positive(self):
        review = dict(target_sha256='target', branch_metrics=dict(measurement_status='UNKNOWN',
            approaches=[], repetition_failure=None))
        self.assertIsNone(publish.method_measurement(review)['same_premise_worked_methods'])

    def candidate(self, degree=0):
        return dict(target='FINAL: 5', target_sha256=policy.text_sha('FINAL: 5'),
            mechanical_pass=True, outcome_pass=True, token_contract_pass=True,
            semantic_status='UNREVIEWED', admitted=False, trainingAllowed=False,
            training_encoding=dict(sequence_length=12), actor=dict(state_sha256='37ec', base_sha256='base'),
            provenance=dict(source_native_path='/native/allowed/shard1/call.json',
                source_purpose='L1_EXTERNAL_GENERATION', parenting_experience=False,
                generator_classification='ORIGINAL37EC_CONTROL', steering_degree=degree,
                instruction_regime='STEERED' if degree else 'EXHAUSTION_ONLY'))

    def registry(self):
        return dict(sources={'/native/allowed': dict(source_purpose='L1_EXTERNAL_GENERATION',
            parenting_experience=False, generator_state_sha256='37ec', generator_base_sha256='base')})

    def test_mixed_steering_same37ec_explicitly_allowed(self):
        first, second = self.candidate(), self.candidate(3)
        second.update(target='FINAL: 6', target_sha256=policy.text_sha('FINAL: 6'))
        publish.validate_candidates([first, second], self.registry())
        self.assertEqual(publish.steering_counts([first, second]), {'0:EXHAUSTION_ONLY': 1, '3:STEERED': 1})

    def test_teacher_checkpoint_parenting_and_wrong_root_rejected(self):
        for field, value in [('generator_classification', 'CHECKPOINT_DERIVED'),
                             ('generator_classification', 'TEACHER_DISTILLATION'),
                             ('parenting_experience', True),
                             ('source_native_path', '/native/allowed_other/call.json')]:
            row = self.candidate()
            row['provenance'][field] = value
            with self.assertRaises(ValueError):
                publish.validate_candidates([row], self.registry())

    def test_wrong_state_and_base_rejected(self):
        for key in ('state_sha256', 'base_sha256'):
            row = self.candidate()
            row['actor'][key] = 'other'
            with self.assertRaises(ValueError):
                publish.validate_candidates([row], self.registry())

    def test_oversize_retained_not_cropped(self):
        row = self.candidate()
        row['training_encoding']['sequence_length'] = 2049
        before = deepcopy(row)
        with self.assertRaises(ValueError):
            publish.validate_candidates([row], self.registry())
        self.assertEqual(row, before)

    def envelope(self):
        return dict(model=publish.MODEL, status='completed', usage=dict(input_tokens=20, output_tokens=15,
            input_tokens_details=dict(cached_tokens=4), output_tokens_details=dict(reasoning_tokens=3)),
            output=[dict(type='message', content=[dict(type='output_text', text='{"reviews": []}')])])

    def test_provider_cap_enforced_request_and_response(self):
        self.assertEqual(publish.provider_payload('packet', 'instructions')['max_output_tokens'], 8192)
        envelope = self.envelope()
        envelope['usage']['output_tokens'] = 8193
        with self.assertRaises(ValueError):
            publish.parse_provider(envelope)

    def test_provider_tools_and_model_drift_rejected(self):
        for kind in ('tool', 'model'):
            envelope = self.envelope()
            if kind == 'tool':
                envelope['output'].append(dict(type='function_call'))
            else:
                envelope['model'] = 'different'
            with self.assertRaises(ValueError):
                publish.parse_provider(envelope)

    def test_provider_usage_components_not_added_twice(self):
        result, usage = publish.parse_provider(self.envelope())
        self.assertEqual(usage['reported_components']['input_tokens'], 20)
        self.assertEqual(usage['reported_components']['cached_input_tokens'], 4)
        self.assertEqual(usage['reported_components']['output_tokens'], 15)

    def test_schema_classifies_methods_separately(self):
        schema = publish.review_schema()
        approach = schema['properties']['reviews']['items']['properties']['branch_metrics']['properties']['approaches']['items']
        self.assertEqual(approach['properties']['method_kind']['enum'], list(publish.METHOD_KINDS))

    def test_source_contains_no_unbounded_retry(self):
        source = Path(publish.__file__).read_text()
        self.assertIn('ThreadPoolExecutor(max_workers=2', source)
        self.assertIn('timeout=310', source)
        self.assertIn("attempts=1, retries=0", source)


if __name__ == '__main__':
    unittest.main()
