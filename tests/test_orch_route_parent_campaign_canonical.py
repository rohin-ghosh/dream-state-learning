from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace
import os
import tempfile
import unittest
from unittest.mock import patch

from gpu import orch_route_parent_campaign_canonical as canonical
from gpu import orch_route_parent_campaign_canonical_parent as parent
from gpu import orch_guided_native as native
from organism_v6 import orch_guided_bridge as bridge
from organism_v6 import orch_route_parent_campaign_canonical as policy
from organism_v6.experienced_event_goal_replay_layout import GoalReplayLayout


class CanonicalTests(unittest.TestCase):
    def test_broker_matches_new_arms_and_rejects_history_or_budget_overrun(self):
        payload = dict(kind='coach', turn=0, task={}, public_messages=[], prior_parent_messages=[], learner={})
        for identity in ('0000_GUIDED_C1', '0127_NO_LORA_C8'):
            request = dict(id=identity, payload=policy.parent_payload(payload))
            self.assertEqual(parent.validated_request(identity + '.request.json', request)['cell'], policy.CELL)
        for identity in ('0000_FROZEN_C1', '0128_GUIDED_C1', '0000_NO_LORA_C9'):
            with self.assertRaises(ValueError):
                parent.validated_request(identity + '.request.json', dict(id=identity, payload={}))

    def test_prospective_matched_two_episode_schedule(self):
        cohort = policy.cohort(set())
        self.assertEqual(cohort, policy.cohort(set()))
        self.assertEqual(len(cohort['train']), 8)
        self.assertEqual(len(cohort['held']), 9)
        for group in cohort['train'] + cohort['held']:
            self.assertEqual(sum(len(policy.shared.tasks(world)) for world in group), 2)
        masters = [world['master'] for group in cohort['train'] + cohort['held'] for world in group]
        self.assertEqual(len(set(masters)), 17)
        self.assertEqual(cohort['presentations_by_cycle'], [4] + [16] * 7)
        self.assertNotIn('FROZEN', policy.ARMS)
        self.assertEqual(policy.SOURCE_ARM, 'GUIDED')

    def test_exclusions_and_strict_dose(self):
        world = policy.cohort(set())['held'][0][0]
        identifier = next(iter(world['edges'][0].values()))
        with self.assertRaises(ValueError):
            policy.cohort({identifier})
        for cycle in (0, 9, True):
            with self.assertRaises(ValueError):
                policy.presentations_for_cycle(cycle)
        self.assertEqual(sum(GoalReplayLayout(2, policy.presentations_for_cycle(cycle)).updates
                             for cycle in range(1, 9)), 812)

    def test_base_identity_cannot_masquerade_as_adapter(self):
        base = canonical.BaseIdentity('a' * 64).verify()
        self.assertEqual(canonical.BaseIdentity.from_document(base.document()), base)
        for key, value in (('path', '/tmp/adapter'), ('kind', 'FROZEN'), ('files', [['adapter', 'a'*64]])):
            with self.assertRaises(ValueError):
                canonical.BaseIdentity.from_document(dict(base.document(), **{key: value}))
        with self.assertRaises(ValueError):
            canonical.BaseIdentity('bad').verify()

    def test_same_life_continuation_and_no_update(self):
        initial = canonical.BaseIdentity('a' * 64).document()
        prior = dict(arm='NO_LORA', cycle=1, phase='sleep', status='COMPLETE',
                     updates=0, fits=0, output_adapter=initial)
        self.assertEqual(policy.next_identity(initial, 'NO_LORA', 2, prior), initial)
        for change in (dict(updates=1), dict(fits=1), dict(arm='GUIDED'), dict(cycle=2),
                       dict(output_adapter=canonical.BaseIdentity('b' * 64).document())):
            with self.assertRaises(ValueError):
                policy.next_identity(initial, 'NO_LORA', 2, dict(prior, **change))

    def test_parent_projection_blind_and_actual_strong(self):
        payload = dict(kind='coach', turn=0, task={}, public_messages=[],
                       prior_parent_messages=[], learner={})
        self.assertEqual(policy.parent_payload(payload)['cell']['provider'], 'openai/openai/gpt-6-astra')
        for forbidden in ('sealed_score', 'HELD', '/tmp/private'):
            with self.assertRaises(ValueError):
                policy.parent_payload(dict(payload, learner=dict(data=forbidden)))

    def test_thinking_counters_have_explicit_denominators(self):
        episode = dict(captures=[dict(command='ROUTE a'), dict(command='ROUTE a', error='invalid')], routes=['a'])
        call = dict(started_unix=10, finished_unix=12,
                    response=dict(prompt_tokens=7, token_ids=[1, 2], terminal=True, truncated=False))
        metrics = policy.thinking_metrics([episode], [call], [dict(admitted=False)])
        self.assertEqual(metrics['episodes'], 1)
        self.assertEqual(metrics['action_attempts'], 2)
        self.assertEqual(metrics['rejected_action_attempts'], 1)
        self.assertEqual(metrics['repeated_action_strings'], 1)
        self.assertEqual(metrics['adjacent_repeated_actions'], 1)
        self.assertEqual(metrics['generation_wall_seconds'], 2)
        self.assertEqual(metrics['coherence_proxies']['reflection_admissions'], 0)
        self.assertFalse(metrics['parent_visible'])
        self.assertNotIn('successes', metrics)

    def test_base_only_mount_rejects_lora_trainability_and_hash_drift(self):
        base = canonical.BaseIdentity('a' * 64)
        parameter = SimpleNamespace(requires_grad=False)
        model = SimpleNamespace(named_parameters=lambda: [('weight', parameter)],
                                state_dict=lambda **unused: dict(weight=parameter))
        engine = SimpleNamespace(model=model, verify_base=lambda: None)
        with patch.object(native, 'state_hash', return_value=base.base_sha256):
            self.assertEqual(canonical.observe_base(engine, base), base)
            parameter.requires_grad = True
            with self.assertRaises(ValueError):
                canonical.observe_base(engine, base)
            parameter.requires_grad = False
            model.peft_config = {'default': object()}
            with self.assertRaises(ValueError):
                canonical.observe_base(engine, base)
            del model.peft_config
            model.named_parameters = lambda: [('layer.lora_A.default.weight', parameter)]
            with self.assertRaises(ValueError):
                canonical.observe_base(engine, base)
            model.named_parameters = lambda: [('weight', parameter)]
        with patch.object(native, 'state_hash', return_value='b' * 64):
            with self.assertRaises(ValueError):
                canonical.observe_base(engine, base)

    def test_base_loader_no_adapter_and_clean_fresh_readout(self):
        identity = canonical.BaseIdentity('a' * 64)
        binding = bridge.StageBinding('canonical', 'NO_LORA', 1, 'sealed_readout', identity,
                                      False, True, 'b' * 64)
        process = ('boot', os.getpid(), 2)
        observed_options = []
        def factory(options, tokenizer, check):
            observed_options.append(options)
            return SimpleNamespace()
        with tempfile.TemporaryDirectory() as directory, patch.dict(os.environ, CUDA_VISIBLE_DEVICES='GPU-test'), \
             patch.object(native, '_USED_PROCESSES', set()), \
             patch.object(native, 'process_identity', return_value=process), \
             patch.object(canonical, 'observe_base', return_value=identity):
            options = dict(model_dir=directory, device='cuda:0', gpu_uuid='GPU-test',
                           context=native.StageContext(), check=lambda label: None,
                           predecessor_processes=(('boot', 1, 1),), engine_factory=factory,
                           tokenizer_loader=lambda directory: object())
            loaded = canonical.load_stage(binding, **options)
            self.assertIsNone(observed_options[0].adapter_dir)
            self.assertEqual(observed_options[0].phase, 'readout')
            self.assertEqual(loaded.observed, identity)
            with self.assertRaises(ValueError):
                canonical.load_stage(binding, **options)
            with self.assertRaises(ValueError):
                canonical.load_stage(replace(binding, phase='training'), **options)
            with self.assertRaises(ValueError):
                canonical.load_stage(binding, **dict(options, context=native.StageContext(private_guidance=('teacher',))))


if __name__ == '__main__':
    unittest.main()
