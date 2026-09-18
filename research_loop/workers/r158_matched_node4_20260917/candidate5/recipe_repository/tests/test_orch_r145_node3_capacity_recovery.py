import ast
from contextlib import nullcontext
from copy import deepcopy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import tempfile
import time
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from gpu import orch_r145_node3_capacity_recovery as repair


def sample(prefix=5, target=3, suffix=0):
    inputs = tuple(range(10, 10 + prefix + target + suffix))
    targets = inputs[prefix:prefix + target]
    return SimpleNamespace(input_ids=inputs, labels=(-100,) * prefix + targets + (-100,) * suffix,
                           target_ids=targets)


def anchors(suffix=2):
    return {family: [dict(split='TRAIN', encoded=sample(prefix=3, target=2, suffix=suffix))]
            for family in ('code', 'math', 'simulated_tools', 'concise_answer')}


def minimal_native():
    return ("class NativeChild:\n"
            "    def generate(self, messages):\n        return messages\n"
            "    def sleep(self, new_rows, old_rows, anchors, record):\n"
            + repair.OLD_ENCODING
            + "        for label, sample, weight in batch:\n"
              "            if True:\n                if True:\n                    if True:\n"
            + repair.OLD_FORWARD
            + "    def checkpoint(self, path):\n        return path\n")


class EncodedContractTests(unittest.TestCase):
    def test_child_window_keeps_preceding_ignored_label(self):
        for prefix, target in ((1, 1), (13, 4), (16300, 64)):
            with self.subTest(prefix=prefix, target=target):
                row = sample(prefix, target)
                previous = deepcopy(row)
                window = repair.child_window(row)
                self.assertEqual(window, dict(logits_to_keep=target + 1, labels=(-100,) + row.target_ids))
                self.assertEqual(row, previous)

    def test_same_child_window_as_unmodified_Main_helper(self):
        from gpu.orch_r145_suffix_loss import loss_window
        for prefix, target in ((1, 1), (28, 5), (100, 11), (16000, 128)):
            row = sample(prefix=prefix, target=target)
            self.assertEqual(repair.child_window(row), loss_window(row))

    def test_anchor_masked_suffix_is_valid_and_unchanged(self):
        row = sample(suffix=3)
        original = deepcopy(row)
        layout = repair.encoded_contract(row, anchor=True)
        self.assertEqual(layout['masked_suffix_tokens'], 3)
        self.assertEqual(row, original)
        with self.assertRaisesRegex(ValueError, 'child_target_must_end_sequence'):
            repair.child_window(row)

    def test_anchor_without_suffix_is_also_valid(self):
        self.assertEqual(repair.encoded_contract(sample(), anchor=True)['masked_suffix_tokens'], 0)

    def test_invalid_children_fail_instead_of_trimming(self):
        bad = [sample(prefix=0), sample(target=0), sample(suffix=1)]
        bad.extend([
            SimpleNamespace(input_ids=(1, 2, 3), labels=(-100, 2, -100), target_ids=(2, 3)),
            SimpleNamespace(input_ids=(1, 2, 3), labels=(-100, 2, 9), target_ids=(2, 9)),
            SimpleNamespace(input_ids=(1, 2), labels=(-100, True), target_ids=(2,)),
            SimpleNamespace(input_ids=(1, -1), labels=(-100, -1), target_ids=(-1,)),
            SimpleNamespace(input_ids=(1, 2, 3), labels=(-100, 3), target_ids=(3,)),
            SimpleNamespace(input_ids=(1, 2, 3, 4), labels=(-100, 2, -100, 4), target_ids=(2, 4)),
        ])
        for row in bad:
            with self.subTest(row=row), self.assertRaises(ValueError):
                repair.child_window(row)

    def test_all_child_and_anchor_rows_are_validated(self):
        child_rows = {'new': sample(), 'rehearsal': sample(prefix=50)}
        inventory = anchors()
        proof = repair.validate_rows(child_rows, inventory, 100)
        self.assertEqual((proof['child_count'], proof['anchor_count']), (2, 4))
        self.assertEqual(proof['max_anchor_tokens'], 7)
        child_rows['rehearsal'] = sample(suffix=1)
        with self.assertRaises(ValueError):
            repair.validate_rows(child_rows, inventory, 100)

    def test_anchor_context_overflow_is_rejected_not_rewritten(self):
        inventory = anchors()
        inventory['code'].append(dict(split='TRAIN', encoded=sample(prefix=100)))
        with self.assertRaisesRegex(ValueError, 'no_context_truncation'):
            repair.validate_rows({'new': sample()}, inventory, 50)

    def test_held_anchor_is_rejected(self):
        inventory = anchors()
        inventory['code'][0]['split'] = 'TEST'
        with self.assertRaisesRegex(ValueError, 'TRAIN_anchors_only'):
            repair.validate_rows({'new': sample()}, inventory, 100)

    def test_unknown_anchor_family_rejected(self):
        inventory = anchors()
        inventory['other'] = inventory.pop('code')
        with self.assertRaises(ValueError):
            repair.validate_rows({'new': sample()}, inventory, 100)


class SourceAndOwnershipTests(unittest.TestCase):
    def test_exact_reversible_child_only_patch(self):
        source = minimal_native()
        with patch.object(repair, 'NATIVE_SHA', hashlib.sha256(source.encode()).hexdigest()):
            changed = repair.patch_source(source, 'a' * 64)
        self.assertEqual(repair.without_sleep(source), repair.without_sleep(changed))
        tree = ast.parse(changed)
        branch = next(node for node in ast.walk(tree) if isinstance(node, ast.If)
                      and isinstance(node.test, ast.Call) and isinstance(node.test.func, ast.Attribute)
                      and node.test.func.attr == 'startswith')
        self.assertEqual(branch.test.args[0].value, 'ANCHOR:')
        calls = [node for node in ast.walk(branch.body[0]) if isinstance(node, ast.Call)]
        self.assertFalse(any(keyword.arg == 'logits_to_keep' for call in calls for keyword in call.keywords))
        original = ast.parse(repair.OLD_FORWARD.strip()).body[0]
        self.assertEqual(ast.dump(branch.body[0]), ast.dump(original))
        self.assertIn("labels[:, -window['logits_to_keep']:]", changed)
        self.assertNotIn('orch_r144_sleep_targets', changed)

    def test_unknown_or_live_native_cannot_be_patched(self):
        with self.assertRaisesRegex(ValueError, 'exact_original_frozen_native_required'):
            repair.patch_source(minimal_native(), 'a' * 64)

    def test_runtime_pin_required(self):
        source = minimal_native()
        with patch.object(repair, 'NATIVE_SHA', hashlib.sha256(source.encode()).hexdigest()):
            for value in ('', '0' * 63, 'x' * 64):
                with self.subTest(value=value), self.assertRaises(ValueError):
                    repair.patch_source(source, value)

    def test_original_frozen_native_integration(self):
        path = os.environ.get('R145_ORIGINAL_NATIVE')
        if path is None:
            self.skipTest('set R145_ORIGINAL_NATIVE to the pinned frozen source, never shared current native')
        source = Path(path).read_text()
        changed = repair.patch_source(source, 'a' * 64)
        self.assertEqual(repair.without_sleep(source), repair.without_sleep(changed))
        self.assertEqual(changed.count('logits_to_keep=window'), 1)
        self.assertEqual(changed.count('r145_capacity.prepare_sleep'), 1)

    def test_snapshot_lane_pins_match_actual_compact_evidence(self):
        path = Path('research_loop/workers/r144_node3_targets_20260916t1515z_operator2/EXITED_5_6_SUMMARY.json')
        for lane in json.loads(path.read_text()):
            actual = repair.LANES[lane['physical']]
            for key in ('saved_cycle', 'saved_steps', 'commit_sha256'):
                self.assertEqual(actual[key], lane[key])
            indices = [int(Path(row['path']).stem) for row in lane['suffix']]
            self.assertEqual(indices, list(range(actual['start'], actual['end'])))
            self.assertEqual([int(Path(row['path']).stem) for row in lane['suffix'] if row['kind'] == 'REQUEST'],
                             list(actual['requests']))

    def test_exact_two_lanes_only(self):
        for physical in range(8):
            plan = dict(physical=physical, gpu_uuid=repair.DEVICES.get(physical, 'foreign'),
                        root='/localhome/local-rohing/orch_r133_node3_'
                        + repair.LANES.get(physical, {}).get('name', 'foreign') + '_20260916_attempt1/run1')
            if physical in (5, 6):
                self.assertEqual(repair.owned_plan(plan), repair.LANES[physical])
                with self.assertRaises(ValueError):
                    repair.owned_plan(dict(plan, gpu_uuid='foreign'))
            else:
                with self.assertRaises(ValueError):
                    repair.owned_plan(plan)

    def test_evidence_never_overwritten(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'proof.json'
            repair.save_once(path, {'status': 'FIRST'})
            with self.assertRaises(FileExistsError):
                repair.save_once(path, {'status': 'SECOND'})
            self.assertEqual(json.loads(path.read_text()), {'status': 'FIRST'})


class RuntimeRejectionTests(unittest.TestCase):
    FORWARD = '''def forward(self, input_ids=None, labels=None, logits_to_keep=0):
        outputs = self.model(input_ids=input_ids)
        logits = self.lm_head(outputs[:, -logits_to_keep:, :])
        loss = None
        if labels is not None:
            loss = self.loss_function(logits=logits, labels=labels)
        return loss
    '''

    def test_labels_used_only_for_loss(self):
        repair.forward_contract(self.FORWARD)

    def test_labels_in_transformer_forward_rejected(self):
        changed = self.FORWARD.replace('self.model(input_ids=input_ids)', 'self.model(input_ids=input_ids, labels=labels)')
        with self.assertRaisesRegex(ValueError, 'labels_used_only_in_causal_loss'):
            repair.forward_contract(changed)

    def test_no_explicit_logits_to_keep_rejected(self):
        with self.assertRaises(ValueError):
            repair.forward_contract(self.FORWARD.replace('logits_to_keep=0', '**kwargs'))

    def test_unknown_loss_implementation_rejected(self):
        with self.assertRaises(ValueError):
            repair.forward_contract(self.FORWARD.replace('self.loss_function', 'other_loss'))

    def test_unknown_package_versions_fail_before_importing_model(self):
        with patch('importlib.metadata.version', return_value='unknown'):
            with self.assertRaisesRegex(ValueError, 'unknown_installed_runtime_version'):
                repair.installed_runtime_pins()

    def test_changed_runtime_rejected_before_model_usage(self):
        with patch.object(repair, 'installed_runtime_pins', return_value={'changed': True}):
            with self.assertRaisesRegex(ValueError, 'actual_installed_functions_and_files_match_pins'):
                repair.verify_model(object(), {'expected': True})


class ProbeRestoreTests(unittest.TestCase):
    def test_failed_probe_restores_adapter_optimizer_rng_modes_and_flags(self):
        class Parameter:
            def __init__(self, value):
                self.value, self.requires_grad, self.grad = value, False, None

            def detach(self):
                return self

            def cpu(self):
                return self

            def clone(self):
                return Parameter(self.value)

            def copy_(self, other):
                self.value = other.value

            def requires_grad_(self, enabled):
                self.requires_grad = enabled

        parameter, base = Parameter(12), Parameter(42)

        class Optimizer:
            def __init__(self):
                self.state = {'momentum': 7}

            def state_dict(self):
                return deepcopy(self.state)

            def load_state_dict(self, state):
                self.state = deepcopy(state)

            def zero_grad(self, set_to_none):
                parameter.grad = None

        optimizer = Optimizer()
        model = SimpleNamespace(training=False, parameters=lambda: [parameter, base],
                                named_parameters=lambda: [('lora', parameter), ('base', base)])
        model.modules = lambda: [model]
        torch = SimpleNamespace(Tensor=Parameter, optim=SimpleNamespace(AdamW=Optimizer),
                                cuda=SimpleNamespace(device_count=lambda: 1), no_grad=nullcontext, seed=145)
        child = SimpleNamespace(plan={'gpu_uuid': repair.DEVICES[5], 'hard_end_unix': time.time() + 300,
                                      'context_limit': 100},
                                torch=torch, engine=SimpleNamespace(model=model, verify_base=lambda: None),
                                optimizer=optimizer, parameters={'lora': parameter}, optimizer_steps=752,
                                adapter_hash=lambda: repair.digest(parameter.value), r145_admitted_plan_sha256='plan')

        def fail_after_mutation(label):
            parameter.value = 999
            parameter.grad = 5
            optimizer.state['momentum'] = 8
            torch.seed = 987
            model.training = True
            child.optimizer_steps = 999
            raise RuntimeError('injected_probe_failure')

        child.check = fail_after_mutation
        inventory, encoded = anchors(), {'child': sample()}
        layout = repair.validate_rows(encoded, inventory, 100)
        with tempfile.TemporaryDirectory() as directory, patch.dict(os.environ, {
                'CUDA_VISIBLE_DEVICES': repair.DEVICES[5], 'PYTORCH_CUDA_ALLOC_CONF': 'expandable_segments:True',
                'R125_ADMISSION_PLAN_SHA256': 'plan'}, clear=True), \
                patch.object(repair, 'prepare_sleep', return_value=layout), \
                patch.object(repair, 'rng_state', side_effect=lambda runtime: {'seed': runtime.seed}), \
                patch.object(repair, 'restore_rng', side_effect=lambda runtime, state: setattr(runtime, 'seed', state['seed'])), \
                patch.object(repair, 'rng_fingerprint', side_effect=repair.digest):
            with self.assertRaisesRegex(RuntimeError, 'injected_probe_failure'):
                repair.bounded_train_probe(child, encoded, inventory, 'a' * 64, directory)
            self.assertEqual((parameter.value, parameter.grad, parameter.requires_grad), (12, None, False))
            self.assertEqual((optimizer.state, torch.seed, model.training, child.optimizer_steps),
                             ({'momentum': 7}, 145, False, 752))
            proof = json.loads((Path(directory) / 'TRAIN_PROBE_RESULT.json').read_text())
            self.assertEqual(proof['status'], 'FAIL')
            self.assertTrue(proof['state_restored'])
            self.assertEqual(proof['optimizer_updates'], 0)


@unittest.skipUnless(all(importlib.util.find_spec(name) for name in ('torch', 'transformers', 'peft')),
                     'installed Qwen2/PEFT CPU runtime unavailable; NOT a model-equivalence PASS')
class InstalledQwenChildAnchorTests(unittest.TestCase):
    def test_paired_full_child_context_and_original_masked_anchor_suffix(self):
        import torch
        from peft import LoraConfig, get_peft_model
        from transformers import Qwen2Config, Qwen2ForCausalLM

        torch.set_num_threads(2)
        torch.manual_seed(145)
        model = get_peft_model(Qwen2ForCausalLM(Qwen2Config(vocab_size=128, hidden_size=32,
            intermediate_size=64, num_hidden_layers=2, num_attention_heads=4, num_key_value_heads=2,
            max_position_embeddings=256, attention_dropout=0.0, use_cache=False)),
            LoraConfig(r=8, lora_alpha=16, lora_dropout=0.05,
                       target_modules=['q_proj', 'v_proj'], task_type='CAUSAL_LM'))
        model.gradient_checkpointing_enable(gradient_checkpointing_kwargs={'use_reentrant': False})
        model.enable_input_require_grads()
        model.train()
        with torch.no_grad():
            for name, parameter in model.named_parameters():
                if 'lora_B' in name:
                    parameter.normal_(mean=0.0, std=0.03)
        parameters = {name: parameter for name, parameter in model.named_parameters() if parameter.requires_grad}
        self.assertTrue(parameters)
        self.assertTrue(all('lora_' in name for name in parameters))
        for prefix, target in ((1, 1), (28, 5), (100, 11)):
            child = sample(prefix=prefix, target=target)
            anchor = sample(prefix=4, target=5, suffix=2)
            repair.encoded_contract(anchor, anchor=True)
            initial_rng = torch.get_rng_state()
            results = []
            for optimized in (False, True):
                torch.set_rng_state(initial_rng)
                model.zero_grad(set_to_none=True)
                losses = []
                for kind, row, weight in [('NEW', child, 0.75)] + [('ANCHOR:test', anchor, 0.0625)] * 4:
                    inputs = torch.tensor([row.input_ids], dtype=torch.long)
                    kwargs = dict(input_ids=inputs, labels=torch.tensor([row.labels], dtype=torch.long),
                                  attention_mask=torch.ones_like(inputs), use_cache=False)
                    if optimized and not kind.startswith('ANCHOR:'):
                        window = repair.child_window(row)
                        kwargs.update(labels=torch.tensor([window['labels']], dtype=torch.long),
                                      logits_to_keep=window['logits_to_keep'])
                    loss = model(**kwargs).loss
                    (loss * weight).backward()
                    losses.append(float(loss.detach()))
                results.append((losses, {name: parameter.grad.clone() for name, parameter in parameters.items()},
                                torch.get_rng_state()))
                self.assertTrue(all(torch.count_nonzero(gradient).item() > 0 for gradient in results[-1][1].values()))
                self.assertTrue(all(parameter.grad is None for name, parameter in model.named_parameters()
                                    if name not in parameters))
            torch.testing.assert_close(torch.tensor(results[0][0]), torch.tensor(results[1][0]), atol=1e-6, rtol=1e-6)
            self.assertTrue(torch.equal(results[0][2], results[1][2]))
            for name in parameters:
                torch.testing.assert_close(results[0][1][name], results[1][1][name], atol=1e-6, rtol=1e-5)


if __name__ == '__main__':
    unittest.main()
