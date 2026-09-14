"""Post-sleep public-evidence selection checks without native imports."""

from copy import deepcopy
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest
from unittest.mock import MagicMock, patch

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

    def test_native_dispatch_does_not_write_cases_twice(self):
        with TemporaryDirectory() as temporary:
            output = Path(temporary) / 'run'
            after = deepcopy(self.after)
            after['arguments'].update(model_dir='model', adapter_dir='adapter')
            cases = self.prepare()
            engine = MagicMock()
            engine.model.named_parameters.return_value = [('layer.lora_A.weight', object())]
            engine.runtime = {}
            engine.generate.side_effect = [dict(raw=cases['sources'][0]['canonical'],
                terminal=True, truncated=False) for case in cases['cases']]
            provenance = dict(expected_actor_state_sha256='updated', adapter_files={}, source_files={})
            tokenizer = MagicMock()
            tokenizer.apply_chat_template.return_value = [1, 2, 3]
            with patch.dict('os.environ', HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1', CUDA_VISIBLE_DEVICES='gpu'), \
                    patch.object(runner, 'load_inputs', return_value=(after, cases, provenance)), \
                    patch.object(runner.source.native, 'load_local_tokenizer', return_value=tokenizer), \
                    patch.object(runner.source, 'Engine', return_value=engine), \
                    patch.dict('sys.modules', {'organism_v6.pcfl_vertical_train':
                        SimpleNamespace(_state_hash=lambda parameters: 'updated')}):
                runner.main(['--after', 'after', '--output', str(output), '--gpu-uuid', 'gpu'])
            self.assertEqual(runner.source.read(output / 'RESULT.json')['status'], 'RESELECTION_CAPTURED_NO_FIT')
            self.assertEqual(engine.generate.call_count, cases['expected_calls'])
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
