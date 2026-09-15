import inspect
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from gpu.orch_rich_hot_node3_base107_engine import Engine, assert_no_adapter, assert_original_rope
from organism_v6 import orch_rich_hot_node3_base107 as policy


class FakeBase:
    def __init__(self, names=('weight',), trainable=False):
        self.entries = [(name, SimpleNamespace(requires_grad=trainable)) for name in names]

    def named_parameters(self):
        return iter(self.entries)

    def parameters(self):
        return (parameter for name, parameter in self.entries)

    def modules(self):
        return iter([self])


class GenuineBaseTests(unittest.TestCase):
    def test_default_rope_normalization_is_not_scaling(self):
        original = dict(max_position_embeddings=32768, rope_theta=1000000.0)
        config = SimpleNamespace(max_position_embeddings=32768,
            rope_scaling=dict(rope_theta=1000000.0, rope_type='default'))
        assert_original_rope(config, original)
        for scaling in (dict(rope_theta=1000000.0, rope_type='linear', factor=2),
                        dict(rope_theta=10000.0, rope_type='default')):
            config.rope_scaling = scaling
            with self.assertRaises(AssertionError):
                assert_original_rope(config, original)

    def test_direct_loader_has_no_adapter_load(self):
        source = inspect.getsource(Engine)
        self.assertIn('AutoModelForCausalLM.from_pretrained', source)
        self.assertNotIn('PeftModel', source)
        self.assertNotIn('read_bundle', source)
        self.assertNotIn('disable_adapter', source)
        self.assertNotIn('import peft', source)

    def test_no_adapter_and_frozen_assertions(self):
        self.assertEqual(assert_no_adapter(FakeBase())['peft_wrapper_count'], 0)
        for model in (FakeBase(('layer.lora_A.weight',)), FakeBase(trainable=True)):
            with self.assertRaises(ValueError):
                assert_no_adapter(model)
        model = FakeBase()
        model._hf_peft_config_loaded = True
        with self.assertRaises(ValueError):
            assert_no_adapter(model)

    def test_main_slot_and_foreign_slots_rejected(self):
        for index in (0, 1, 2, 3, 6, 7):
            with self.assertRaises(ValueError):
                policy.arm(index)

    def test_reasoning_permission_and_functional_not_form(self):
        self.assertIn('ordinary prose BEFORE', policy.guidance(4))
        self.assertIn('affect the action', policy.guidance(4))
        self.assertIn('change the next reasoning step', policy.guidance(5))
        self.assertIn('No prescribed branch count', policy.guidance(5))
        self.assertTrue(policy.SYSTEM.startswith('Reason through'))
        self.assertNotEqual(policy.SYSTEM, policy.original.SYSTEM)

    def test_prose_then_final_action_keeps_gym_semantics(self):
        world = dict(edges=[dict(node='start', port='p1', outcome='mid', receipt='r1'),
                            dict(node='mid', port='p2', outcome='goal', receipt='r2')])
        task = dict(node='start', goal='goal', ports=['p1'], events=['e1'],
                    display_variant='GOAL_FIRST_PUBLIC_FIELDS_V1')
        outputs = iter(['Reasoning before a committed action.\nROUTE p1',
                        'The actual receipt changes the current node.\nROUTE p2'])
        messages = []
        def generate(prompt):
            messages.append(prompt)
            return dict(raw=next(outputs), terminal=True, truncated=False)
        record = policy.episode(world, task, generate, {}, 4)
        self.assertTrue(record['correct'])
        self.assertEqual(len(record['routes']), 2)
        self.assertTrue(messages[0][0]['content'].startswith(policy.SYSTEM))

    def test_trailing_text_after_action_is_rejected(self):
        world = dict(edges=[])
        task = dict(node='start', goal='goal', ports=['p1'], events=['e1'],
                    display_variant='GOAL_FIRST_PUBLIC_FIELDS_V1')
        record = policy.episode(world, task, lambda prompt: dict(raw='ROUTE p1\nextra',
            terminal=True, truncated=False), {}, 5)
        self.assertEqual(record['terminal_reason'], 'invalid_final_action')
        self.assertEqual(record['routes'], [])

    def test_bare_commands_are_never_qualified(self):
        row = policy.assess(dict(raw='READ EVENT opaque-address'))
        self.assertTrue(row['raw_command_only'])
        self.assertFalse(row['qualified_action_changing_reasoning'])
        self.assertIsNone(row['qualified_functional_count'])
        self.assertFalse(row['trainingAllowed'])

    def test_prose_is_not_automatically_functional(self):
        row = policy.assess(dict(raw='I should investigate uncertainty.\nREAD EVENT opaque-address'))
        self.assertFalse(row['raw_command_only'])
        self.assertIsNone(row['qualified_action_changing_reasoning'])
        self.assertIsNone(row['functional_metarealisation_to_changed_continuation'])

    def test_paired_prior_cohort_preserved(self):
        cohort = dict(tasks=[dict(index=4, arm='prior', task_id='fixed')], phase_version='prior')
        with patch.object(policy.previous, 'roster', return_value=cohort):
            result = policy.roster({})
        self.assertEqual(result['tasks'][0]['task_id'], 'fixed')
        self.assertTrue(result['paired_prior_task_ids'])

    def test_driver_cannot_touch_main_slot(self):
        from gpu import orch_rich_hot_node3_base107_run as runner
        with patch.object(runner, 'bind_host') as bind:
            with self.assertRaises(ValueError):
                runner.watch(Path('/unused'), 3)
        bind.assert_not_called()


if __name__ == '__main__':
    unittest.main()
