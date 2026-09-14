import json
from pathlib import Path
import unittest
from contextlib import contextmanager

from organism_v6 import orch_base_contract as policy


FREEZE = Path('research_notes/analysis/orch_base_contract_20260914_attempt1/FREEZE.json')


class BaseContractTests(unittest.TestCase):
    def setUp(self):
        self.entries = json.loads(FREEZE.read_text())['entries']

    def result(self, text, tokens=160):
        return dict(raw=text, token_ids=[1] * tokens + [2], terminal=True, truncated=False)

    def test_fixed_selection(self):
        self.assertEqual([entry['task']['id'] for entry in self.entries],
                         [14, 17, 49, 62, 'gsm8k-train-1649', 'gsm8k-train-5724', 'gsm8k-train-3590', 'gsm8k-train-2554'])

    def test_initial_prompt_exact(self):
        for entry in self.entries:
            self.assertEqual(policy.prompt(entry)[0], entry['initial_messages'])
            self.assertNotIn('Be terse.', json.dumps(entry['initial_messages']))

    def test_safe_action_checker(self):
        entry = self.entries[0]
        good = policy.capture(entry, self.result('{"expression":"l*b*h/2"}'), [])
        self.assertTrue(good['outcome_pass'])
        bad = policy.capture(entry, self.result('{"expression":"__import__(\"os\")"}'), [])
        self.assertFalse(bad['outcome_pass'])

    def test_ordered_feedback_matches_original(self):
        entry = self.entries[0]
        row = policy.capture(entry, self.result('{"expression":"l*b*h/2"}'), [])
        self.assertIn('Oracle feedback: {"success": true, "passed": 3, "total": 3}', policy.prompt(entry, row)[0][-1]['content'])

    def test_math_gold_not_injected(self):
        entry = dict(self.entries[4], task=dict(self.entries[4]['task'], gold='SECRET_SENTINEL'))
        self.assertNotIn('SECRET_SENTINEL', json.dumps(policy.prompt(entry)[0]))

    def test_range_boundaries(self):
        for count in (149, 150, 400, 401):
            row = policy.capture(self.entries[4], self.result('FINAL: 25', count), [])
            self.assertEqual(row['token_contract'], 150 <= count <= 400)

    def test_success_is_not_admission(self):
        row = policy.capture(self.entries[4], self.result('FINAL: 25'), [])
        self.assertTrue(row['outcome_pass'])
        self.assertFalse(row['admitted'])

    def test_all_failures_remain_in_denominator(self):
        result = policy.reduce(self.entries, [])
        self.assertEqual(result['states']['BASE']['denominator'], 8)
        self.assertFalse(result['local_suppression_support'])

    def test_full_semantic_not_lexical(self):
        row = policy.capture(self.entries[4], self.result('We calculate 500 * .2 * .25 = 25. FINAL: 25'), [])
        review = dict(target_sha256=row['target_sha256'], status='PASS', reason='fixture',
                      quotes=['We calculate'], ownership=True, grounding=True, checkable=True,
                      truthful=True, no_padding=True, reusable=True)
        self.assertFalse(policy.admission(row, review))
        review['target_sha256'] = 'wrong'
        with self.assertRaises(ValueError):
            policy.admission(row, review)

    def test_peft_restoration_refreezes_without_updates(self):
        class Parameter:
            requires_grad = False
            value = 37

        class Model:
            parameter = Parameter()

            def parameters(self):
                return [self.parameter]

            def requires_grad_(self, flag):
                self.parameter.requires_grad = flag

            @contextmanager
            def disable_adapter(self):
                try:
                    yield
                finally:
                    self.parameter.requires_grad = True

        model = Model()
        for fail in (False, True):
            try:
                with policy.readonly_condition(model, 'BASE'):
                    self.assertFalse(model.parameter.requires_grad)
                    if fail:
                        raise RuntimeError('fixture')
            except RuntimeError:
                pass
            self.assertFalse(model.parameter.requires_grad)
            self.assertEqual(model.parameter.value, 37)

    def test_resume_never_regenerates_completed_states(self):
        rows = [dict(position=0, state='BASE', kind='solution', outcome_pass=True),
                dict(position=0, state='BASE', kind='record', outcome_pass=True),
                dict(position=1, state='ORIGINAL', kind='solution', outcome_pass=False)]
        self.assertEqual(policy.completed_states(rows), {(0, 'BASE'), (1, 'ORIGINAL')})
        with self.assertRaises(AssertionError):
            policy.completed_states(rows[:1])


if __name__ == '__main__':
    unittest.main()
