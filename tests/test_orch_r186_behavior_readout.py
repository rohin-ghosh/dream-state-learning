"""Synthetic CPU contracts only: no model, checkpoint from a life, or GPU."""

from contextlib import contextmanager
from copy import deepcopy
import json
import os
from pathlib import Path
import random
import stat
import sys
import tempfile
import time
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from gpu import orch_guided_native as weights
from gpu import orch_r125_continual_native as native
from gpu import orch_r186_behavior_readout as runner
from organism_v6 import orch_r107_capability as policy


ADAPTER_SHA256 = 'a' * 64
RAW = '<think>Synthetic diagnostic only.</think>\nanswer\n'


class State:
    def __init__(self, value):
        self.value = value

    def clone(self):
        return State(self.value)


class Torch:
    def __init__(self, gpu_uuid):
        self.cpu, self.device = 11, 22
        self.initialized = False
        self.syncs = 0
        self.cuda = SimpleNamespace(is_initialized=lambda: self.initialized,
            device_count=lambda: 1, get_device_properties=lambda index: SimpleNamespace(uuid=gpu_uuid),
            get_rng_state_all=self.cuda_states, set_rng_state_all=self.set_cuda_states,
            synchronize=self.synchronize)

    def cuda_states(self):
        if not self.initialized:
            raise AssertionError('CUDA RNG accessed before loader')
        return [State(self.device)]

    def set_cuda_states(self, states):
        self.device = states[0].value

    def synchronize(self):
        self.syncs += 1

    def get_rng_state(self):
        return State(self.cpu)

    def set_rng_state(self, state):
        self.cpu = state.value

    @staticmethod
    def equal(actual, expected):
        return actual.value == expected.value


class Model:
    def __init__(self):
        self.parameter = SimpleNamespace(requires_grad=False)
        self.training = False
        self.disable_adapters = False
        self.lora_A, self.lora_B = {}, {}
        self.adapter_sha256 = ADAPTER_SHA256

    def parameters(self):
        return [self.parameter]

    def named_parameters(self):
        return [('model.lora_A.default.weight', self.parameter)]

    def modules(self):
        return [self]

    def requires_grad_(self, value):
        self.parameter.requires_grad = value

    @contextmanager
    def disable_adapter(self):
        self.disable_adapters = True
        try:
            yield
        finally:
            self.disable_adapters = False
            self.parameter.requires_grad = True


class Tokenizer:
    eos_token_id = 99

    def decode(self, tokens, *, skip_special_tokens, clean_up_tokenization_spaces):
        if skip_special_tokens or clean_up_tokenization_spaces:
            raise AssertionError('exact decoder options required')
        return RAW if tokens else ''


class Engine:
    def __init__(self, torch):
        self.torch = torch
        self.model = Model()
        self.tokenizer = Tokenizer()
        self.calls, self.random_draws = [], []
        self.base_checks = 0
        self.base_bad = False
        self.fail_at = None
        self.after_generate = lambda response, supplied: None

    def verify_base(self):
        self.base_checks += 1
        if self.base_bad:
            raise ValueError('frozen_base_changed')

    def generate(self, supplied, *, max_new_tokens):
        if max_new_tokens != 512 or self.model.parameter.requires_grad:
            raise AssertionError('read-only fixed decoder cap')
        self.calls.append((deepcopy(supplied), self.model.disable_adapters))
        self.random_draws.append((random.random(), self.torch.cpu, self.torch.device))
        self.torch.cpu += 1
        self.torch.device += 1
        if len(self.calls) == self.fail_at:
            raise RuntimeError('synthetic_generation_failure')
        response = dict(raw=RAW, messages=deepcopy(supplied), token_ids=[7, 99],
            prompt_tokens=20, terminal=True, truncated=False)
        self.after_generate(response, supplied)
        return response


class BehaviorReadoutTest(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix='r186-cpu-')
        self.addCleanup(temporary.cleanup)
        self.base = Path(temporary.name)
        self.root = self.base / 'life'
        self.checkpoint_dir = self.root / 'checkpoints' / 'sleep_0001'
        adapter = self.checkpoint_dir / 'adapter'
        adapter.mkdir(parents=True)
        self.adapter_file = adapter / 'adapter_model.safetensors'
        self.adapter_file.write_bytes(b'synthetic fixture, not saved child weights')
        optimizer = self.checkpoint_dir / 'optimizer_rng.pt'
        optimizer.write_bytes(b'hash only, deliberately not a pickle')
        adapter_files = {self.adapter_file.name: native.sha(self.adapter_file)}
        checkpoint = dict(schema=native.SCHEMA, base_sha256=native.BASE_SHA256,
            adapter_path=str(adapter), adapter_files=adapter_files, adapter_state_sha256=ADAPTER_SHA256,
            optimizer_rng_path=str(optimizer), checkpoint_sha256=dict(adapter=policy.digest(adapter_files),
                optimizer=native.sha(optimizer), rng=native.sha(optimizer)), optimizer_steps=16)
        self.commit = self.checkpoint_dir / 'COMMIT.json'
        native.write_once(self.commit, checkpoint)
        now = time.time()
        self.plan = dict(schema=native.SCHEMA, base_sha256=native.BASE_SHA256,
            system_prompt=native.SYSTEM, birth_prompt=native.BIRTH,
            compaction_invitation=native.COMPACTION_INVITATION,
            new_presentations=16, rehearsal_presentations=1, anchor_lambda=0.25,
            seed=0, segments_per_sleep=2, segment_tokens=512, context_limit=4096,
            max_sleeps=1, physical=0, gpu_uuid='GPU-synthetic-fixture',
            hard_end_unix=now + 3600, lease_end_unix=now + 7200,
            decoder=dict(temperature=0.7, top_p=0.95, repetition_penalty=1.05, no_repeat_ngram_size=16),
            root=str(self.root), model_dir=str(self.base / 'model'), anchors=str(self.base / 'anchors'),
            source_root=str(self.base / 'source'), history=['excluded synthetic history'],
            parent_messages=['excluded synthetic parent'], working_state=['excluded synthetic carry'])
        self.plan_path = self.root / 'PLAN.json'
        native.write_once(self.plan_path, self.plan)
        self.config = dict(schema=runner.SCHEMA, prompts=[dict(id=identifier,
            text='  Synthetic caller prompt: ' + identifier + '\n') for identifier in runner.PROMPT_IDS])
        self.config_path = self.base / 'CONFIG.json'
        native.write_once(self.config_path, self.config)
        self.output = self.root / 'behavior_readouts' / 'sleep_0001'
        self.torch = Torch(self.plan['gpu_uuid'])
        self.engine = Engine(self.torch)
        self.loads = 0
        self.load_failure = False
        self.patch(patch.dict(os.environ, {'R125_ADMISSION_PLAN_SHA256': native.sha(self.plan_path),
            runner.CONFIG_BINDING: native.sha(self.config_path), 'CUDA_VISIBLE_DEVICES': self.plan['gpu_uuid']}))
        self.patch(patch.object(runner, '_torch', return_value=self.torch))
        self.patch(patch.object(runner, '_load_engine', side_effect=self.load))
        self.patch(patch.object(weights, 'state_hash', side_effect=lambda parameters: self.engine.model.adapter_sha256))
        self.patch(patch.object(native.NativeChild, '__init__', side_effect=AssertionError('no live child')))
        self.patch(patch.object(policy, 'tasks', side_effect=AssertionError('no synthetic32 bank')))
        original_rng = random.getstate()
        self.addCleanup(random.setstate, original_rng)

    def patch(self, patcher):
        value = patcher.start()
        self.addCleanup(patcher.stop)
        return value

    def load(self, plan, checkpoint, check):
        self.loads += 1
        check('load')
        random.random()
        self.torch.cpu = 88
        if self.load_failure:
            raise RuntimeError('synthetic_load_failure')
        self.torch.initialized = True
        return self.engine

    def run_readout(self):
        return runner.run(self.plan_path, self.checkpoint_dir, self.config_path, self.output)

    def read(self, name):
        return json.loads((self.output / name).read_bytes())

    def test_six_independent_birth_contexts_actual_off_masks_and_immutable_inputs(self):
        files = [self.plan_path, self.config_path, self.commit, self.adapter_file,
            self.checkpoint_dir / 'optimizer_rng.pt']
        before = {path: path.read_bytes() for path in files}
        result = self.run_readout()
        self.assertEqual(result, self.read('COMPLETE.json'))
        self.assertEqual(result['calls'], 6)
        self.assertTrue(result['before_after_verified'])
        self.assertFalse(result['automatic_scoring'])
        self.assertEqual(result['training_updates'], 0)
        self.assertEqual(result['decoder'], dict(do_sample=False, num_beams=1, use_cache=True, repetition_penalty=1.0))
        self.assertEqual([disabled for _, disabled in self.engine.calls], [False, True, True, False, False, True])
        for position, prompt in enumerate(self.config['prompts']):
            for offset in (0, 1):
                index = 2 * position + offset
                expected = runner.messages(self.plan, prompt)
                self.assertEqual(self.engine.calls[index][0], expected)
                record = self.read(f'CALL_{index:03d}.json')
                self.assertEqual(record['response']['raw'], RAW)
                self.assertEqual(record['mask_receipt']['prefix_labels'], [-100] * 20)
                self.assertEqual(record['mask_receipt']['generated_labels'], [-100, -100])
                self.assertEqual(record['mask_receipt']['target_tokens'], 0)
                self.assertEqual(record['mask_receipt']['generated_tokens'], 2)
                self.assertEqual(record['mask_receipt']['content_tokens'], 1)
                self.assertTrue(record['rng']['restored'])
                self.assertEqual(self.read(f'reservations/CALL_{index:03d}.json')['status'], 'RESERVED')
                self.assertEqual(result['call_files'][f'CALL_{index:03d}.json'], native.sha(self.output / f'CALL_{index:03d}.json'))
        self.assertEqual(before, {path: path.read_bytes() for path in files})
        self.assertEqual(self.torch.syncs, 12)
        self.assertFalse((self.root / 'readouts').exists())
        self.assertFalse((self.root / 'parent_inbox').exists())

    def test_private_exclusive_artifacts(self):
        self.run_readout()
        for path in [self.output, *self.output.rglob('*')]:
            self.assertEqual(stat.S_IMODE(path.stat().st_mode), 0o700 if path.is_dir() else 0o600)
        preserved = self.read('COMPLETE.json')
        with self.assertRaises(FileExistsError):
            self.run_readout()
        self.assertEqual(self.loads, 1)
        self.assertEqual(self.read('COMPLETE.json'), preserved)

    def test_success_rng_is_restored_and_identical_for_each_call(self):
        before = random.getstate()
        self.run_readout()
        self.assertEqual(random.getstate(), before)
        self.assertEqual(self.torch.cpu, 11)
        self.assertEqual(self.torch.device, 22)
        self.assertTrue(self.read('COMPLETE.json')['rng']['restored'])
        self.assertTrue(all(draw == self.engine.random_draws[0] for draw in self.engine.random_draws))

    def test_generation_failure_restores_rng_and_retains_without_retry(self):
        before = random.getstate()
        self.engine.fail_at = 2
        with self.assertRaisesRegex(RuntimeError, 'synthetic_generation_failure'):
            self.run_readout()
        self.assertEqual(random.getstate(), before)
        self.assertEqual((self.torch.cpu, self.torch.device), (11, 22))
        self.assertEqual(len(self.engine.calls), 2)
        self.assertEqual(self.read('FAILED.json')['calls'], 2)
        self.assertTrue(self.read('FAILED.json')['rng']['restored'])
        self.assertEqual(self.read('CALL_000.json')['status'], 'COMPLETE')
        self.assertEqual(self.read('CALL_001.json')['status'], 'FAILED')
        self.assertFalse(self.engine.model.disable_adapters)
        self.assertFalse(self.engine.model.parameter.requires_grad)
        self.assertFalse((self.output / 'COMPLETE.json').exists())

    def test_loader_failure_preserves_cpu_rng(self):
        self.load_failure = True
        before = random.getstate()
        with self.assertRaisesRegex(RuntimeError, 'synthetic_load_failure'):
            self.run_readout()
        self.assertEqual(random.getstate(), before)
        self.assertEqual(self.torch.cpu, 11)
        self.assertEqual(self.read('FAILED.json')['calls'], 0)
        self.assertTrue(self.read('FAILED.json')['rng']['restored'])

    def test_resident_cuda_is_rejected_before_load(self):
        self.torch.initialized = True
        with self.assertRaisesRegex(ValueError, 'fresh_process'):
            self.run_readout()
        self.assertEqual(self.loads, 0)

    def test_admission_binding_and_output_scope_fail_before_load(self):
        for name in ('R125_ADMISSION_PLAN_SHA256', runner.CONFIG_BINDING, 'CUDA_VISIBLE_DEVICES'):
            with self.subTest(name=name), patch.dict(os.environ, {name: 'wrong'}):
                with self.assertRaises(ValueError):
                    self.run_readout()
        for location in ('readouts/probe', 'parent_inbox/probe', 'behavior_readouts'):
            with self.subTest(location=location), self.assertRaisesRegex(ValueError, 'separate_private'):
                runner.run(self.plan_path, self.commit, self.config_path, self.root / location)
        self.assertEqual(self.loads, 0)

    def test_config_contract_rejects_missing_duplicate_empty_and_hidden_inputs(self):
        invalid = [dict(self.config, decoder={}), dict(self.config, prompts=[])]
        for field, value in [('id', 'continue'), ('text', ''), ('text', ' '), ('text', 'x' * 16385), ('answer', 'hidden')]:
            config = deepcopy(self.config)
            config['prompts'][1][field] = value
            invalid.append(config)
        for config in invalid:
            with self.subTest(config=str(config)[:100]), self.assertRaises(ValueError):
                runner.validate_config(config)
        self.assertEqual(runner.validate_config(self.config), self.config)

    def test_checkpoint_file_tampering_rejected_before_load(self):
        self.adapter_file.write_bytes(b'tampered synthetic adapter')
        with self.assertRaisesRegex(ValueError, 'adapter_file_binding'):
            self.run_readout()
        self.assertEqual(self.loads, 0)

    def test_existing_history_workspace_and_other_readouts_are_not_read(self):
        excluded = [self.root / name for name in ('stream', 'workspace', 'readouts', 'parent_inbox')]
        for directory in excluded:
            directory.mkdir()
            (directory / 'synthetic_sentinel.txt').write_text('not a source for this diagnostic')
        read_bytes, read_text = Path.read_bytes, Path.read_text

        def guarded_bytes(path, *args, **kwargs):
            self.assertFalse(any(path.is_relative_to(directory) for directory in excluded))
            return read_bytes(path, *args, **kwargs)

        def guarded_text(path, *args, **kwargs):
            self.assertFalse(any(path.is_relative_to(directory) for directory in excluded))
            return read_text(path, *args, **kwargs)

        with patch.object(Path, 'read_bytes', guarded_bytes), patch.object(Path, 'read_text', guarded_text):
            self.run_readout()

    def test_wrong_cuda_uuid_rejected_before_generation(self):
        self.torch.cuda.get_device_properties = lambda index: SimpleNamespace(uuid='GPU-wrong')
        with self.assertRaisesRegex(ValueError, 'CUDA_UUID_mismatch'):
            self.run_readout()
        self.assertEqual(len(self.engine.calls), 0)

    def test_symlink_cannot_redirect_output_into_existing_readouts(self):
        existing = self.root / 'readouts'
        existing.mkdir()
        (self.root / 'behavior_readouts').symlink_to(existing, target_is_directory=True)
        with self.assertRaisesRegex(ValueError, 'separate_private_behavior_readouts'):
            self.run_readout()
        self.assertEqual(self.loads, 0)

    def test_midrun_input_change_stops_with_first_response_preserved(self):
        self.engine.after_generate = lambda response, supplied: self.config_path.write_text('{}')
        with self.assertRaisesRegex(ValueError, 'behavior_config_SHA256_binding'):
            self.run_readout()
        self.assertEqual(len(self.engine.calls), 1)
        self.assertEqual(self.read('CALL_000.json')['response']['raw'], RAW)
        self.assertEqual(self.read('AFTER.json')['status'], 'FAILED')

    def test_midrun_commit_change_stops_before_next_call(self):
        self.engine.after_generate = lambda response, supplied: self.commit.write_text('{}')
        with self.assertRaisesRegex(ValueError, 'checkpoint_COMMIT_changed'):
            self.run_readout()
        self.assertEqual(len(self.engine.calls), 1)

    def test_source_drift_fails_without_another_generation(self):
        sha = runner._sha

        def changed_sha(path):
            if self.engine.calls and Path(path).name == 'orch_r186_behavior_readout.py':
                return 'c' * 64
            return sha(path)

        with patch.object(runner, '_sha', side_effect=changed_sha):
            with self.assertRaisesRegex(ValueError, 'readout_source_changed'):
                self.run_readout()
        self.assertEqual(len(self.engine.calls), 1)

    def test_adapter_mutation_fails_identity_check_and_stops(self):
        self.engine.after_generate = lambda response, supplied: setattr(self.engine.model, 'adapter_sha256', 'b' * 64)
        with self.assertRaisesRegex(ValueError, 'immutable_checkpoint_adapter'):
            self.run_readout()
        self.assertEqual(len(self.engine.calls), 1)
        self.assertFalse(self.read('FAILED.json')['before_after_verified'])

    def test_base_mutation_fails_identity_check(self):
        self.engine.after_generate = lambda response, supplied: setattr(self.engine, 'base_bad', True)
        with self.assertRaisesRegex(ValueError, 'frozen_base_changed'):
            self.run_readout()
        self.assertEqual(len(self.engine.calls), 1)

    def test_raw_decoder_mismatch_is_not_scored_or_retried(self):
        self.engine.after_generate = lambda response, supplied: response.update(raw='invented cleaned answer')
        with self.assertRaisesRegex(ValueError, 'exact_raw_decoder'):
            self.run_readout()
        self.assertEqual(self.read('CALL_000.json')['response']['raw'], 'invented cleaned answer')
        self.assertEqual(len(self.engine.calls), 1)

    def test_input_context_mutation_is_rejected(self):
        self.engine.after_generate = lambda response, supplied: supplied.append(dict(role='user', content='hidden carry'))
        with self.assertRaisesRegex(ValueError, 'birth_only_messages_mutated'):
            self.run_readout()
        self.assertEqual(len(self.engine.calls), 1)

    def test_response_token_metadata_is_validated(self):
        expected = runner.messages(self.plan, self.config['prompts'][0])
        response = dict(messages=expected, token_ids=[7, 99], raw=RAW, prompt_tokens=20, terminal=True, truncated=False)
        for changes in ({'token_ids': []}, {'token_ids': [True, 99]}, {'token_ids': [7] * 513},
                {'terminal': False}, {'truncated': True}, {'prompt_tokens': 0}, {'max_new_tokens': 256},
                {'messages': []}):
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                runner._validate_response(dict(response, **changes), expected, self.engine.tokenizer)
        terminal_only = dict(response, token_ids=[99], raw='')
        self.assertEqual(runner._validate_response(terminal_only, expected, self.engine.tokenizer)['content_tokens'], 0)
        truncated = dict(response, token_ids=[7] * 512, terminal=False, truncated=True)
        self.assertEqual(runner._validate_response(truncated, expected, self.engine.tokenizer)['generated_tokens'], 512)

    def test_numpy_rng_preserved_if_already_loaded(self):
        state = ['MT19937', [1, 2, 3], 1, 0, 0.0]
        original = deepcopy(state)
        numpy = SimpleNamespace(random=SimpleNamespace(get_state=lambda: tuple(deepcopy(state)),
            set_state=lambda value: state.__setitem__(slice(None), deepcopy(value))),
            array_equal=lambda actual, expected: actual == expected)
        with patch.dict(sys.modules, {'numpy': numpy}):
            with runner._preserve_rng(self.torch):
                state[1][0] = 99
        self.assertEqual(state, original)

    def test_rng_restoration_failure_never_claims_complete(self):
        self.torch.cuda.set_rng_state_all = lambda states: None
        with self.assertRaisesRegex(ValueError, 'CUDA_RNG_restoration'):
            self.run_readout()
        self.assertEqual(len(self.engine.calls), 1)
        self.assertFalse(self.read('CALL_000.json')['rng']['restored'])
        self.assertFalse((self.output / 'COMPLETE.json').exists())

    def test_cli_has_only_explicit_paths(self):
        with patch.object(runner, 'run') as execute:
            runner.main(['--plan', str(self.plan_path), '--checkpoint', str(self.commit),
                '--config', str(self.config_path), '--output', str(self.output)])
        execute.assert_called_once_with(self.plan_path, self.commit, self.config_path, self.output)


if __name__ == '__main__':
    unittest.main()
