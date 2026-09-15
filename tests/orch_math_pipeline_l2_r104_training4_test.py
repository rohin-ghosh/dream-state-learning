import copy
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import Mock

from gpu import orch_math_pipeline_l2_r102_policy as policy
from gpu import orch_math_pipeline_l2_r104_broker as broker
from gpu import orch_math_pipeline_l2_r104_native as native
from gpu import orch_math_pipeline_l2_r104_run as runner


class Training4Test(unittest.TestCase):
    def test_exact_two_episode_strong_training_wheels_context(self):
        previous = policy.PARENTING
        try:
            policy.PARENTING = runner.CONFIG['parenting']
            episodes = [dict(task=task, trace='An incorrect past answer.',
                outcome=dict(status='INCORRECT', correct=False)) for task in policy.original.cohort()['train'][0][:2]]
            payload = policy.parent_payload(episodes, 1)
            with broker.training_context():
                broker.previous.transport.parent.policy.validate_parent_payload(payload)
                self.assertIn('Training-wheels/long/supportive', broker.previous.transport.parent.INSTRUCTIONS)
                with self.assertRaises(AssertionError):
                    broker.previous.transport.parent.policy.validate_parent_payload(dict(payload, episodes=payload['episodes']*4))
            self.assertEqual(runner.CONFIG['physical'], 4)
            self.assertEqual(runner.CONFIG['parenting']['strength'], 'openai/openai/gpt-6-astra')
        finally:
            policy.PARENTING = previous

    def test_cohort_excludes_old_and_both_r102_shared_pools(self):
        first = policy.make_cohort(policy.original.cohort())
        next_cohort = policy.make_cohort(first)
        old_hashes = {task['question_sha256'] for group in first['train'] + first['held'] for task in group}
        new_tasks = [task for group in next_cohort['train'] + next_cohort['held'] for task in group]
        self.assertFalse(old_hashes & {task['question_sha256'] for task in new_tasks})
        self.assertEqual(len(new_tasks), 80)
        self.assertEqual(sum(2+2+8+(48 if native.retention_due(cycle) else 0) for cycle in range(1,9)), 144)

    def test_seed_optimizer_state_loaded_without_reset(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            optimizer = root/'saved_optimizer.pt'
            optimizer.write_bytes(b'CPU fixture, not a model')
            (root/'SEED_PROVENANCE.json').write_text(json.dumps(dict(optimizer_path=str(optimizer),
                optimizer_sha256=native.sha(optimizer))))
            state = dict(state={1:dict(step=1194)}, param_groups=[dict(lr=3e-5)])
            loaded = SimpleNamespace(optimizer=Mock(), engine=SimpleNamespace(torch=SimpleNamespace(load=Mock(return_value=state))))
            native.restore_seed_optimizer(loaded, root, root)
            loaded.optimizer.load_state_dict.assert_called_once_with(state)
            loaded.engine.torch.load.assert_called_once_with(optimizer, map_location='cpu', weights_only=True)
            self.assertFalse(json.loads((root/'OPTIMIZER_CONTINUITY.json').read_text())['new_optimizer_reset'])

    def test_imported_row_requires_exact_bound_source(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)/'new'
            prior=Path(directory)/'prior'
            root.mkdir(); prior.mkdir()
            source=prior/'CALL.json'
            source.write_text(json.dumps(dict(task_id='FAILED_TRAIN', response=dict(raw='bad past attempt'))))
            row=dict(source_campaign=str(prior),source_call_path='CALL.json',source_call_sha256=native.sha(source),
                target='bad past attempt',target_sha256=policy.text_sha('bad past attempt'),episode_id='FAILED_TRAIN',outcome='INCORRECT')
            (root/'SEED_PROVENANCE.json').write_text(json.dumps(dict(campaign=str(prior),row_digests=[policy.digest(row)])))
            self.assertEqual(native.source_row(root,row),row)
            changed=copy.deepcopy(row); changed['outcome']='CORRECT'
            with self.assertRaises(AssertionError):
                native.source_row(root,changed)


if __name__ == '__main__':
    unittest.main()
