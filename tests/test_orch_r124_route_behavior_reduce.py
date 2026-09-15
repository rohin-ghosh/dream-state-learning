from copy import deepcopy
import unittest

from gpu import orch_r124_route_behavior_reduce as reduce


class ReductionTests(unittest.TestCase):
    def conditions(self):
        row = dict(messages_sha256='same', style='MINIMAL', context='INITIAL',
            response=dict(raw='ROUTE P1'), metrics=dict(action='ROUTE P1', generated_tokens=4,
            rationale_tokens=0, truncated=False, terminal=True, repeated_fourgram_fraction=0))
        return {condition: {'task': deepcopy(row)} for condition in reduce.probe.CONDITIONS}

    def test_identical_output_is_not_invented_change(self):
        rows = reduce.paired_rows(self.conditions())
        self.assertFalse(rows[0]['output_changed'])
        self.assertEqual(rows[0]['generated_token_delta'], 0)
        summary = reduce.summarize(rows)[0]
        self.assertEqual(summary['outputs_changed'], 0)
        self.assertEqual(summary['after']['responses_with_rationale'], 0)

    def test_changed_prose_distinct_from_changed_action(self):
        conditions = self.conditions()
        conditions['AFTER']['task']['response']['raw'] = 'The record supports this.\nROUTE P1'
        conditions['AFTER']['task']['metrics'].update(generated_tokens=10, rationale_tokens=5)
        rows = reduce.paired_rows(conditions)
        self.assertTrue(rows[0]['output_changed'])
        self.assertFalse(rows[0]['action_changed'])
        self.assertEqual(rows[0]['rationale_token_delta'], 5)

    def test_changed_prompts_cannot_claim_matched_response_change(self):
        conditions = self.conditions()
        conditions['AFTER']['task']['messages_sha256'] = 'different'
        with self.assertRaisesRegex(ValueError, 'same_prompt'):
            reduce.paired_rows(conditions)

    def test_missing_control_cannot_be_inferred(self):
        conditions = self.conditions()
        del conditions['AFTER_LORA_OFF']
        with self.assertRaisesRegex(ValueError, 'three_actual'):
            reduce.paired_rows(conditions)


if __name__ == '__main__':
    unittest.main()
