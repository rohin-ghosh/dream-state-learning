import unittest

from gpu import orch_r109_l1_public_feedback as pilot
from organism_v6 import orch_persist_code as ledger


class PublicFeedbackTests(unittest.TestCase):
    def setUp(self):
        self.task = ledger.build_tasks()[0]

    def test_public_probe_exposes_no_private_inputs(self):
        task = dict(self.task, inputs=None)
        result = pilot.execute_public(task, '{"expression":"sum(values)"}')
        self.assertEqual(result['input'], pilot.public_probe(task))
        self.assertFalse(result['hidden_tests_exposed'])

    def test_actual_invalid_identifier_is_not_rewritten(self):
        result = pilot.execute_public(self.task, '{"expression":"sum(xs)"}')
        self.assertIn('unknown identifier', result['error'])
        self.assertEqual(result['expression'], 'sum(xs)')

    def test_no_feedback_control_does_not_receive_execution(self):
        feedback = pilot.execute_public(self.task, '{"expression":"sum(xs)"}')
        prefix = pilot.messages(self.task, 'CHILD_NO_FEEDBACK', 'prior', feedback)
        self.assertNotIn('unknown identifier', prefix[-1]['content'])

    def test_treatment_receives_actual_error(self):
        feedback = pilot.execute_public(self.task, '{"expression":"sum(xs)"}')
        prefix = pilot.messages(self.task, 'CHILD_PUBLIC_FEEDBACK', 'prior', feedback)
        self.assertIn('unknown identifier', prefix[-1]['content'])
        self.assertEqual(prefix[-2], dict(role='assistant', content='prior'))

    def test_base_and_child_treatment_prompts_match(self):
        feedback = pilot.execute_public(self.task, '{"expression":"sum(xs)"}')
        self.assertEqual(pilot.messages(self.task, 'CHILD_PUBLIC_FEEDBACK', 'prior', feedback),
                         pilot.messages(self.task, 'BASE_PUBLIC_FEEDBACK', 'prior', feedback))

    def test_real_operation_order_error_public_obstacle(self):
        task = ledger.build_tasks()[0]
        wrong = '{"expression":"sum(values)"}'
        result = pilot.execute_public(task, wrong)
        self.assertNotEqual(result['observed'], ledger.expected(task, result['input']))
        self.assertNotIn('error', result)

    def test_feedback_has_no_gold_or_verdict(self):
        result = pilot.execute_public(self.task, '{"expression":"sum(values)"}')
        self.assertLessEqual(set(result), pilot.PUBLIC_KEYS)
        self.assertTrue({'expected', 'success', 'correct', 'verifier', 'gold'}.isdisjoint(result))

    def test_verifier_fields_are_rejected_not_silently_forwarded(self):
        result = pilot.execute_public(self.task, '{"expression":"sum(values)"}')
        for key in ('expected', 'success', 'correct', 'gold', 'hidden_inputs'):
            with self.assertRaises(ValueError):
                pilot.messages(self.task, 'CHILD_PUBLIC_FEEDBACK', 'previous', dict(result, **{key: 1}))

    def test_interface_fix_is_not_metacognition(self):
        result = pilot.correction(dict(success=False), dict(success=True),
                                  dict(error='ValueError: unknown identifier'), 'old', 'new')
        self.assertTrue(result['interface_repair_candidate'])
        self.assertFalse(result['behavior_repair_candidate'])
        self.assertFalse(result['metacognition_claim'])
        self.assertFalse(result['functional_admission'])

    def test_already_correct_is_not_correction(self):
        result = pilot.correction(dict(success=True), dict(success=True), {}, 'old', 'new')
        self.assertFalse(result['verified_failed_to_passed_candidate'])

    def test_failed_again_is_not_correction(self):
        result = pilot.correction(dict(success=False), dict(success=False), {}, 'old', 'new')
        self.assertFalse(result['verified_failed_to_passed_candidate'])

    def test_deadline_and_no_fit(self):
        plan = dict(source_label=pilot.SOURCE, physical=7, uuid=pilot.UUID, max_responses=96,
                    task_count=16, max_new_tokens=8192, native_end_unix=pilot.NATIVE_END,
                    external_end_unix=pilot.EXTERNAL_END, parents=0, optimizer_steps=0, fit_allowed=0)
        pilot.validate_plan(plan, pilot.NATIVE_END - 1)
        with self.assertRaises(ValueError):
            pilot.validate_plan(plan, pilot.NATIVE_END)
        with self.assertRaises(ValueError):
            pilot.validate_plan(dict(plan, fit_allowed=1), pilot.NATIVE_END - 1)


if __name__ == '__main__':
    unittest.main()
