import copy
import json
import unittest

from organism_v6 import orch_route_parent_campaign_teacher_exemplar as policy


class TeacherExemplarTests(unittest.TestCase):
    def exemplar(self):
        return dict(source_label=policy.LABEL, methods=[dict(name=name, explanation='A justified educational step. ' * 8)
            for name in ('algebra', 'substitution')], final_answer='12', checks=['equality', 'units'], limitations='No tools executed')

    def envelope(self):
        return dict(model=policy.MODEL, status='completed', usage=dict(output_tokens=100),
            output=[dict(type='message', content=[dict(type='output_text', text=json.dumps(self.exemplar()))])])

    def test_actual_model_and_budget_not_alias(self):
        self.assertEqual(policy.parse_response(self.envelope())['source_label'], policy.LABEL)
        for patch in (dict(model='assumed-astra'), dict(status='incomplete'), dict(usage=dict(output_tokens=8193)),
                      dict(output=[dict(type='function_call')])):
            with self.assertRaises(ValueError):
                policy.parse_response(dict(self.envelope(), **patch))

    def test_teacher_label_and_multiple_methods_required(self):
        for patch in (dict(source_label='SELF_GENERATED_L1'), dict(methods=[]), dict(checks=[])):
            envelope = self.envelope()
            envelope['output'][0]['content'][0]['text'] = json.dumps(dict(self.exemplar(), **patch))
            with self.assertRaises(ValueError):
                policy.parse_response(envelope)

    def test_gold_paths_and_held_rejected_from_prompts(self):
        prompt = dict(source_label=policy.LABEL, split='TRAIN', task_id='EXISTING_TRAIN_1', domain='math',
            problem='Find a quantity.', observed_events=[])
        self.assertEqual(policy.validate_prompt(prompt), prompt)
        for patch in (dict(gold='12'), dict(split='HELD'), dict(source_label='SELF_GENERATED_L1'),
                      dict(problem='HELD canary'), dict(problem='/tmp/private'), dict(problem='sealed_score')):
            with self.assertRaises(ValueError):
                policy.validate_prompt(dict(prompt, **patch))

    def test_numeric_correctness_is_not_ingestion_permission(self):
        check = policy.check_answer(self.exemplar(), dict(domain='math', answer='12'))
        self.assertTrue(check['final_answer_correct'])
        self.assertFalse(check['ingestion_authorized'])
        self.assertEqual(check['method_proofs'], 'NOT_INDEPENDENTLY_VERIFIED')
        self.assertFalse(policy.check_answer(self.exemplar(), dict(domain='math', answer='13'))['final_answer_correct'])

    def test_route_checks_only_observed_edges(self):
        oracle = dict(domain='route', start='start', goal='goal', observed_edges=[
            dict(node='start', port='one', outcome='middle'), dict(node='middle', port='two', outcome='goal')])
        response = dict(self.exemplar(), final_answer='ROUTE one; ROUTE two')
        self.assertTrue(policy.check_answer(response, oracle)['final_answer_correct'])
        self.assertFalse(policy.check_answer(dict(response, final_answer='ROUTE two; ROUTE one'), oracle)['final_answer_correct'])
        missing = copy.deepcopy(oracle)
        missing['observed_edges'].pop()
        self.assertFalse(policy.check_answer(response, missing)['final_answer_correct'])


if __name__ == '__main__':
    unittest.main()
