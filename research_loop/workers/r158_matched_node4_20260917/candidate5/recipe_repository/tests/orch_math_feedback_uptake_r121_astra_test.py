from copy import deepcopy
import inspect
import unittest

from gpu import orch_math_feedback_uptake_r121_astra as subject


class FastAstraTests(unittest.TestCase):
    def test_low_effort_without_provider_or_model_change(self):
        document = 'model = "'+subject.delivery.STRONG+'"\nmodel_reasoning_effort = "high"\n'
        result = subject.low_settings(document)
        self.assertEqual(result['model'], subject.delivery.STRONG)
        self.assertEqual(result['model_reasoning_effort'], 'low')

    def test_unknown_model_rejected(self):
        with self.assertRaisesRegex(ValueError, 'existing_strong'):
            subject.low_settings('model = "other"')

    def test_config_preserves_original_identity_and_budget(self):
        original = dict(remote_root='/old', deadline_unix=1, max_parent_calls=384,
            max_output_tokens=8192, max_budget_usd=12, life_id='unchanged')
        plan = dict(branch='A2', index=5, original_root='/old', bounds={'train_end_unix':2},
            prospective_capacity={'parent':100000}, contract={'parent_wait_seconds':0})
        config = dict(original, deadline_unix=2, max_parent_calls=100000, max_output_tokens=1024)
        before = deepcopy(original)
        subject.validate_delta(config, original, plan)
        self.assertEqual(original, before)
        config['max_budget_usd'] = 100
        with self.assertRaisesRegex(ValueError, 'only_prospective'):
            subject.validate_delta(config, original, plan)

    def test_existing_once_archival_path_reused(self):
        self.assertIn('delivery.astra_evaluate.__code__', inspect.getsource(subject.evaluate))
        self.assertIn("fork/'BROKER_LEDGER_CONFIG.json'", inspect.getsource(subject.namespace))
        self.assertIn("actual_single_lane_lock_acquired=True", inspect.getsource(subject.namespace))


if __name__ == '__main__':
    unittest.main()
