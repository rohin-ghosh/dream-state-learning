from copy import deepcopy
import json
import os
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from gpu import orch_r127_route_transfer as probe


class TransferTests(unittest.TestCase):
    def test_fixed_cohort_and_checkpoint_denominators(self):
        cohort = probe.fresh_cohort(set())
        self.assertEqual(len(cohort['worlds']), 16)
        self.assertEqual(len(cohort['tasks']), 32)
        self.assertEqual(len({row['task_id'] for row in cohort['tasks']}), 32)
        self.assertEqual(probe.TOTAL_CALLS, 1472)
        self.assertEqual(probe.CONDITIONS, ('SEED', 'GUIDED_C2', 'GUIDED_C4', 'GUIDED_C6',
            'UNPARENTED_C2', 'UNPARENTED_C4', 'UNPARENTED_C6'))
        self.assertFalse(cohort['trainingAllowed'])
        self.assertFalse(cohort['final_tasks_used'])

    def test_fresh_cohort_is_reproducible_without_sampling_results(self):
        self.assertEqual(probe.fresh_cohort({'N_prior'}), probe.fresh_cohort({'N_prior'}))

    def test_collision_never_silently_replaces_a_world(self):
        first = probe.fresh_cohort(set())['worlds'][0]
        with self.assertRaisesRegex(ValueError, 'namespace_collision'):
            probe.fresh_cohort(probe.identifiers(first))

    def test_two_task_prompt_contains_public_inputs_not_world_edges(self):
        from organism_v6 import orch_full_rich as rich
        cohort = probe.fresh_cohort(set())
        for row in cohort['tasks']:
            task = row['task']
            messages = [dict(role='system', content=rich.SYSTEM),
                dict(role='user', content=rich.readout.display(task['node'], task, list(task['ports'])))]
            self.assertEqual(probe.digest(messages), row['initial_prompt_sha256'])
            self.assertNotIn('"outcome"', json.dumps(messages))
            self.assertNotIn('"correct"', json.dumps(messages))
            self.assertNotIn(rich.GUIDANCE, messages[0]['content'])

    def test_claim_is_written_before_generation_and_never_overwritten(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            path = probe.reserve(root, 'SOURCE', [{'role': 'user', 'content': 'test'}])
            self.assertTrue(probe.read(path)['no_retry'])
            self.assertFalse(probe.read(path)['trainingAllowed'])
            with self.assertRaises(FileExistsError):
                probe.write(path, {'status': 'fabricated'})

    def test_condition_budget_is_not_reset_by_another_condition(self):
        with tempfile.TemporaryDirectory() as temporary, patch.object(probe, 'SOURCE_CALLS', 1):
            root = Path(temporary)
            probe.reserve(root, 'SOURCE', [])
            probe.reserve(root, 'SEED', [])
            with self.assertRaisesRegex(ValueError, 'condition_budget'):
                probe.reserve(root, 'SOURCE', [])

    def test_missing_charge_is_not_reused(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            probe.write(root / 'claims/CALL_00002.json', {'condition': 'SEED'})
            with self.assertRaisesRegex(ValueError, 'contiguous'):
                probe.reserve(root, 'SEED', [])

    def fixture(self, root):
        bundle = root / 'bundle'
        bundle.mkdir()
        adapter = bundle / 'adapter'
        adapter.mkdir()
        (adapter / 'adapter_model.safetensors').write_bytes(b'CPU fixture, never a real model')
        identity = dict(path='adapter', state_sha256=probe.SEED, base_sha256=probe.BASE,
            files=[['adapter_model.safetensors', probe.sha(adapter / 'adapter_model.safetensors')]])
        cohort = probe.fresh_cohort(set())
        exported = dict(conditions={name: dict(adapter=deepcopy(identity), arm=name, cycle=0, updates=0)
            for name in probe.CONDITIONS})
        plan = dict(bundle=str(bundle), output=str(root / 'run'), uuid='GPU-test', model_dir=str(root),
            hard_end_unix=10**12)
        Path(plan['output']).mkdir()
        path = root / 'PLAN.json'
        probe.write(path, plan)
        return path, plan, exported, cohort

    def test_actual_episode_loop_keeps_invalid_source_and_failed_task_records(self):
        from gpu import orch_guided_native as native
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            path, plan, exported, cohort = self.fixture(root)
            loads = []
            def load(binding, **kwargs):
                self.assertEqual(binding.phase, 'sealed_readout')
                self.assertFalse(binding.parent_present)
                engine = SimpleNamespace(generate=lambda messages, **options: dict(raw='NOT_AN_ACTION',
                    messages=deepcopy(messages), terminal=True, truncated=False, token_ids=[1, 2]))
                actor = SimpleNamespace(optimizer=None, observed=binding.adapter, process=(1, 2, 3),
                    engine=engine, verify_unchanged=Mock())
                loads.append(actor)
                return actor
            environment = dict(CUDA_VISIBLE_DEVICES=plan['uuid'], HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1')
            with patch.object(probe, 'validate', return_value=(plan, exported, cohort)), \
                    patch.object(native, 'load_stage', side_effect=load), patch.dict(os.environ, environment):
                probe.stage(path, 'SOURCE')
                probe.stage(path, 'SEED')
            store = probe.read(Path(plan['output']) / 'SOURCE/STORE.json')
            self.assertEqual(store['accepted_events'], 0)
            self.assertEqual(store['worlds'], 16)
            self.assertEqual(store['store'], {})
            complete = probe.read(Path(plan['output']) / 'SEED/COMPLETE.json')
            self.assertEqual(len(complete['episodes']), 32)
            self.assertEqual(complete['optimizer_steps'], 0)
            self.assertEqual(complete['parent_calls'], 0)
            for reference in complete['episodes']:
                episode = probe.checked(reference)
                self.assertFalse(episode['correct'])
                self.assertEqual(episode['parent_messages'], [])
                self.assertEqual(episode['actor_calls'], 1)
                self.assertEqual(episode['captures'][0]['response']['raw'], 'NOT_AN_ACTION')
                self.assertFalse(episode['trainingAllowed'])
            self.assertEqual(len(loads), 2)
            for actor in loads:
                actor.verify_unchanged.assert_called_once_with()


if __name__ == '__main__':
    unittest.main()
