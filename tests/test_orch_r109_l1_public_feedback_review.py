import unittest

from gpu import orch_r109_l1_public_feedback_review as review


class RevisionTests(unittest.TestCase):
    def test_multiline_json_mismatch_is_not_rescored(self):
        result = review.shape('{\n "expression": "sum(values)"\n}')
        self.assertTrue(result['whole_response_json'])
        self.assertTrue(result['original_expression_AST_valid'])

    def test_partial_identifier_change_with_frozen_failure(self):
        frozen = dict(before_success=False, after_success=False, verified_failed_to_passed_candidate=False)
        result = review.revision('{"expression":"sum(xs)"}', '{"expression":"affine(values)"}',
                                 dict(error='unknown identifier'), dict(error='helper arity mismatch'), frozen)
        self.assertEqual(result['unknown_identifiers_removed'], ['xs'])
        self.assertTrue(result['general_values_introduced'])
        self.assertEqual(result['diagnostic_transition'], 'UNKNOWN_IDENTIFIER->ARITY')
        self.assertFalse(result['frozen_success_candidate'])
        self.assertFalse(result['functional_admission'])

    def test_wrong_key_stays_wrong_key(self):
        result = review.shape('{"expr":"sum(values)"}')
        self.assertFalse(result['exact_expression_key'])
        self.assertTrue(result['alternate_expr_key'])

    def test_parse_failure_is_not_identifier_removal(self):
        frozen = dict(before_success=False, after_success=False, verified_failed_to_passed_candidate=False)
        result = review.revision('{"expr":"sum(xs)"}', '{"expr":"sum(xs"}',
                                 dict(error='JSON_SCHEMA'), dict(error='JSON_SCHEMA'), frozen)
        self.assertFalse(result['expression_AST_comparable'])
        self.assertEqual(result['unknown_identifiers_removed'], [])

    def test_parse_failure_is_not_literal_removal(self):
        frozen = dict(before_success=False, after_success=False, verified_failed_to_passed_candidate=False)
        result = review.revision('{"expr":"sum([1, 2])"}', 'not JSON',
                                 dict(error='JSON_SCHEMA'), dict(error='JSONDecodeError'), frozen)
        self.assertFalse(result['list_literal_removed'])

    def test_verification_does_not_run_recovered_expression(self):
        result = review.shape('{"expr":"__import__(42)"}')
        self.assertFalse(result['original_expression_AST_valid'])
        self.assertEqual(result['unknown_identifiers'], ['__import__'])


if __name__ == '__main__':
    unittest.main()
