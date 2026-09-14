"""Post-sleep public-evidence selection checks without native imports."""

from copy import deepcopy
import unittest

from gpu import astra_corrective_reselect as runner
from tests.test_experienced_event_corrective_replay import fixture


class ReselectionTests(unittest.TestCase):
    def setUp(self):
        self.collection, self.records, bindings = fixture()
        self.after = dict(bindings['before_result'], schema=runner.driver.SCHEMA,
            phase='readout_corrective', state='AFTER', replay_arm='CHILD_CORRECTIVE',
            frozen_base_unchanged=True, loaded_adapter_state_sha256='updated',
            corrective_training_result_sha256='train-sha',
            arguments=dict(phase='readout_corrective', state='AFTER', replay_arm='CHILD_CORRECTIVE'))
        self.request = deepcopy(self.after)
        self.panels = deepcopy(self.after['panels'])
        self.train = dict(adapter_state_after='updated')

    def prepare(self):
        return runner.prepare_after(self.collection, self.after, self.request, self.panels,
                                    self.records, self.train, 'train-sha')

    def test_original_prompt_recipe_and_actual_error_cases(self):
        cases = self.prepare()
        self.assertEqual(cases['expected_calls'], 2)
        self.assertEqual(cases, runner.selector.prepare_cases(self.collection, self.records))
        self.assertNotIn('HIDDEN_READER_METADATA', str([case['messages'] for case in cases['cases']]))

    def test_ancestor_uniform_or_wrong_receipt_rejected(self):
        for key, value in dict(loaded_adapter_state_sha256='ancestor', replay_arm='UNIFORM_REPLAY',
                corrective_training_result_sha256='wrong', phase='readout', state='BEFORE', fits=1,
                reader_wrapper=8, frozen_base_unchanged=False, status='FAILED').items():
            with self.subTest(key=key):
                original = self.after[key]
                self.after[key] = value
                with self.assertRaises(ValueError):
                    self.prepare()
                self.after[key] = original

    def test_request_panel_and_actual_outcome_drift_rejected(self):
        self.request['arguments']['state'] = 'BEFORE'
        with self.assertRaises(ValueError):
            self.prepare()
        self.request = deepcopy(self.after)
        self.panels['OWN_PARAMETRIC']['denominator'] = 3
        with self.assertRaises(ValueError):
            self.prepare()
        self.panels = deepcopy(self.after['panels'])
        self.records.pop()
        with self.assertRaises(ValueError):
            self.prepare()


if __name__ == '__main__':
    unittest.main()
