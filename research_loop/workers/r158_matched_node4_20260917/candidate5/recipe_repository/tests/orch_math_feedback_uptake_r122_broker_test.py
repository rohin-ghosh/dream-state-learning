import unittest

from gpu import orch_math_feedback_uptake_r122_broker as broker


class BrokerTests(unittest.TestCase):
    def test_train_plan_binding(self):
        plan = dict(index=5, root='owned', native_end=broker.lane.NATIVE, prospective_parent_capacity=100, file_sha256='b' * 64)
        payload = dict(life_id='R122_A100_5', task_id='new_TRAIN', task_provenance=dict(
            split='TRAIN', cohort_sha256=plan['file_sha256'], task_sha256='a' * 64))
        config = broker.config_for(plan, dict(payload=payload))
        self.assertEqual(config['max_output_tokens'], 1024)
        self.assertEqual(config['deadline_unix'], broker.lane.NATIVE)
        for split in ('DEV', 'FINAL'):
            payload['task_provenance']['split'] = split
            with self.assertRaises(ValueError):
                broker.config_for(plan, dict(payload=payload))


if __name__ == '__main__':
    unittest.main()
