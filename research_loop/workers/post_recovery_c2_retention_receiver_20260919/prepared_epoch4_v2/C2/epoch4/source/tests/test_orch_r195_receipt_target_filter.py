"""Synthetic provenance and conservative receipt exclusions; no live execution."""

from copy import deepcopy
import hashlib
import json
import unittest

from organism_v6.orch_r195_receipt_target_filter import receipt_exclusions, unsupported_claims
from tests.test_orch_r197_correction_ledger import RAW, receipt


def rows(target, *, raw=RAW, returncode=0, stdout='', stderr=''):
    outcome = receipt(raw, returncode=returncode, stderr=stderr)
    outcome['result']['stdout'] = stdout
    outcome['result_sha256'] = hashlib.sha256(json.dumps(
        outcome['result'], sort_keys=True, indent=2).encode()).hexdigest()
    attempt = dict(source_sha256='d' * 64, segment=10, target=raw)
    review = dict(source_sha256='e' * 64, segment=11, target=target,
        learn_review_evidence=[dict(act_source_sha256=attempt['source_sha256'],
            response_origin=dict(record_sha256='a' * 64), outcome=outcome)])
    return [attempt, review]


class ReceiptFilterTests(unittest.TestCase):
    def test_empty_output_numerical_claim_is_quarantined_not_declared_false(self):
        batch = rows('The solution for V is [29].')
        before = deepcopy(batch)
        proof = receipt_exclusions(batch)
        self.assertEqual(len(proof['excluded']), 1)
        exclusion = proof['excluded'][0]
        self.assertEqual(exclusion['source_sha256'], batch[1]['source_sha256'])
        self.assertEqual(exclusion['reason'], 'numeric_result_claim_after_empty_output')
        self.assertFalse(exclusion['semantic_falsehood_claimed'])
        self.assertEqual(batch, before)

    def test_actual_stdout_or_cautious_language_is_not_quarantined(self):
        self.assertEqual(receipt_exclusions(rows('The result was 29.', stdout='29\n'))['excluded'], [])
        for target in ('No result was observed; 29 is unverified.',
                       'The solution might be 29.', 'I expect the result is 29.',
                       'No result obtained.', '> The result was 29.'):
            with self.subTest(target=target):
                self.assertEqual(receipt_exclusions(rows(target))['excluded'], [])

    def test_prose_without_an_execution_is_not_treated_as_a_failed_tool_claim(self):
        batch = rows('My hand calculation gives 3.')
        batch[1]['learn_review_evidence'][0]['outcome'] = dict(
            status='LANGUAGE_RESPONSE_UNVERIFIED', executed=False)
        self.assertEqual(receipt_exclusions(batch)['excluded'], [])

    def test_absent_import_requires_actual_joined_error_receipt(self):
        error = "Traceback (most recent call last):\n  fixture\nModuleNotFoundError: No module named 'absent_fixture'\n"
        batch = rows('I will revise the attempt.', raw='```python\nimport absent_fixture\n```',
            returncode=1, stderr=error)
        proof = receipt_exclusions(batch)
        self.assertEqual(proof['excluded'][0]['source_sha256'], batch[0]['source_sha256'])
        self.assertEqual(proof['excluded'][0]['reason'], 'actual_receipt_import_error')
        batch[1]['learn_review_evidence'][0]['response_origin']['record_sha256'] = 'f' * 64
        self.assertEqual(receipt_exclusions(batch)['excluded'], [])

    def test_no_module_inventory_is_invented(self):
        batch = rows('No result obtained.', raw='```python\nimport sympy\n```')
        self.assertEqual(receipt_exclusions(batch)['excluded'], [])

    def test_out_of_batch_or_future_attempt_cannot_be_excluded(self):
        batch = rows('The result was 29.')
        batch[0]['segment'] = 12
        self.assertEqual(receipt_exclusions(batch)['excluded'], [])
        batch[1]['learn_review_evidence'][0]['act_source_sha256'] = 'f' * 64
        self.assertEqual(receipt_exclusions(batch)['excluded'], [])

    def test_non_numeric_language_is_explicitly_outside_claim_filter(self):
        self.assertEqual(unsupported_claims('The scene is funny.'), [])


if __name__ == '__main__':
    unittest.main()
