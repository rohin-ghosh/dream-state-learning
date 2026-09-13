"""CPU fixtures only; actual pinned encoder/scorer, mocked tokenizer/model/processes."""
from collections import UserDict
import copy
from dataclasses import asdict
import importlib.util
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import time
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch
import zlib

sys.dont_write_bytecode = True
SOURCE = Path("/data/home/rohing/dream-state")
PATH = Path("/tmp/astra_level1_real_record_run_20260913.py")
spec = importlib.util.spec_from_file_location("real_record_runtime_test", PATH)
runtime = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runtime)

class TokenizerFixture:
    chat_template = "CPU_QWEN_SHAPED_FULL_ASSISTANT_TEMPLATE"
    eos_token = "<|im_end|>"
    eos_token_id = 1
    pad_token_id = 0
    as_mapping = True
    trailer = "\n"

    def encode(self, text, add_special_tokens=False):
        assert add_special_tokens is False
        words = re.findall(r"<\|im_start\|>|<\|im_end\|>|[A-Za-z_]+|[0-9]+|[^\w\s]|\s+", text)
        assert "".join(words) == text
        return [1 if word == self.eos_token else 2 if word == "<|im_start|>" else zlib.crc32(word.encode()) + 3 for word in words]

    def apply_chat_template(self, messages, tokenize, add_generation_prompt):
        messages = copy.deepcopy(messages)
        if messages[0]["role"] != "system":
            messages.insert(0, {"role": "system", "content": "Fixture generic system."})
        text = "".join(f"<|im_start|>{message['role']}\n{message['content']}<|im_end|>\n" for message in messages)
        if add_generation_prompt:
            text += "<|im_start|>assistant\n"
        elif self.trailer != "\n":
            text = text[:-1] + self.trailer
        if not tokenize:
            return text
        ids = self.encode(text, add_special_tokens=False)
        return UserDict(input_ids=ids) if self.as_mapping else ids


class NativeFixture:
    instances = []
    mode = 'valid'

    def __init__(self, plan, probe, route):
        self.tokenizer = TokenizerFixture()
        self.route = route
        self.seen = []
        self.closed = False
        self.instances.append(self)

    def generate(self, request):
        self.seen.append(copy.deepcopy(request))
        if self.mode == 'error':
            raise RuntimeError('CPU simulated native failure')
        core_request = request['core_request']
        if core_request['kind'] == 'wake':
            raw = f"PREDICT: F\nACT: TRY {core_request['tick']},{core_request['tick'] + 3},-2"
            if self.mode == 'invalid':
                raw = 'I decline to issue an action.'
        else:
            prompt = core_request['input_messages'][0]['content']
            facts = json.loads(re.findall(r'^Observed fields: (.*)$', prompt, re.MULTILINE)[-1])
            predicted, observed = facts['predicted'], facts['observed']
            relation = 'unavailable' if predicted is None else 'matched' if predicted == observed else 'mismatched'
            raw = json.dumps(dict(try_value=facts['values'], observed=observed, predicted=predicted, relation=relation),
                             sort_keys=True, separators=(',', ':')).replace('"try_value"', '"try"')
            if self.mode == 'fenced':
                raw = '```json\n' + raw + '\n```'
        tokens = self.tokenizer.encode(raw)
        finish = 'stop'
        if self.mode == 'length':
            tokens = [3] * request['params']['max_tokens']
            finish = 'length'
        if self.mode == 'over_budget':
            tokens = [3] * (request['params']['max_tokens'] + 1)
        route = dict(name='wrong', id=1, path='/CPU_ONLY') if self.mode == 'bad_route' else self.route
        return dict(**request['native'], text=raw, decoded_output=raw, output_token_ids=tokens,
                    actual_prompt_token_ids=request['native']['prompt_token_ids'], finish_reason=finish,
                    stop_reason=1, started=1.0, ended=2.0, lora_request=route)

    def close(self):
        self.closed = True


class RuntimeTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix='real_record_cpu_', dir='/tmp')
        self.addCleanup(temporary.cleanup)
        self.home = Path(temporary.name)
        self.root = self.home / 'formation'
        self.source = self.home / 'source'
        for name in ('__init__.py', 'birth_skill_corpus.py', 'rulegame_parenting_diagnostic.py', 'train_adapter_v3.py',
                     'birth_reflection_probe.py', 'rulegame.py'):
            path = self.source / 'organism_v6' / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes((SOURCE / 'organism_v6' / name).read_bytes())
        self.model = self.home / 'model'
        self.model.mkdir()
        self.model_files = {'CPU_fixture.safetensors': 'a' * 64}
        self.environment = {'CPU_only': True}
        self.helper = runtime.load_module(self.record('/tmp/astra_level1_skill_run_20260913.py'), 'helper_fixture')
        self.probe = runtime.load_module(self.record('/tmp/astra_birth_skill_probe_run_20260913.py'), 'probe_fixture')
        self.patch(self.helper, 'environment', return_value=self.environment)
        self.patch(self.probe, 'model_hashes', return_value=self.model_files)
        self.patch(self.probe, 'native_environment', return_value=self.environment)
        self.patch(self.probe, 'native_tokenizer', return_value=TokenizerFixture())
        self.patch(self.probe, 'gpu_state', side_effect=AssertionError('GPU forbidden'))
        self.patch(runtime.subprocess, 'Popen', side_effect=AssertionError('native subprocess forbidden'))
        original_loader = runtime.load_module
        def loader(record, name):
            runtime.pinned(record)
            if name == 'level1':
                return self.helper
            if name == 'public':
                return self.probe
            return original_loader(record, name)
        self.patch(runtime, 'load_module', side_effect=loader)
        env = patch.dict(os.environ, {}, clear=False)
        env.start()
        self.addCleanup(env.stop)
        protocol = self.home / 'protocol.md'
        protocol.write_text('CPU formation protocol fixture,96/192, no launch permission')
        self.material = self.home / 'old_material.py'
        self.material.write_text('CPU upstream provenance fixture')
        self.binding = dict(schema=1, scope=self.probe.SCOPE, visibility='model-only-public', approved_by='Main',
                            model_name=self.probe.MODEL_NAME, revision=self.probe.REVISION, model_files=self.model_files,
                            native_environment=self.environment,
                            source_files={name: runtime.digest(self.source / name) for name in self.probe.SOURCE_NAMES})
        binding_path = self.home / 'binding.json'
        runtime.write(binding_path, self.binding)
        self.specification = dict(runner_sha256=runtime.digest(PATH), source=str(self.source), source_files=runtime.tree(self.source),
                    model=str(self.model), core=self.record('/tmp/astra_level1_real_record_core_20260913.py'),
                    level1_runtime=self.record('/tmp/astra_level1_skill_run_20260913.py'),
                    public=self.record('/tmp/astra_birth_skill_probe_run_20260913.py'), protocol=self.record(protocol),
                    binding=self.record(binding_path), gpu_index=0, gpu_uuid='GPU-CPU-FIXTURE-ONLY', lease_end=time.time()+30000)
        self.specification['upstream'] = [self.make_upstream(seed) for seed in range(3)]
        self.spec_path = self.home / 'spec.json'
        NativeFixture.instances = []
        NativeFixture.mode = 'valid'

    def record(self, path):
        return dict(path=str(path), sha256=runtime.digest(path))

    def patch(self, target, name, **kwargs):
        patcher = patch.object(target, name, **kwargs)
        result = patcher.start()
        self.addCleanup(patcher.stop)
        return result

    def make_upstream(self, seed):
        root = self.home / f'upstream_seed{seed}'
        adapter = root / 'run/fit/adapter'
        adapter.mkdir(parents=True)
        config = dict(target_modules=['q_proj'])
        runtime.write(adapter / 'adapter_config.json', dict(r=8, lora_alpha=16, lora_dropout=.05, bias='none', target_modules=['q_proj']))
        (adapter / 'adapter_model.safetensors').write_text('CPU dummy LoRA ' + str(seed))
        (adapter / 'DONE').write_text('CPU DONE')
        runtime.write(adapter / 'train_manifest.json', dict(steps=320))
        files = runtime.tree(adapter)
        runtime.write(root / 'run/fit/fit.json', dict(adapter=str(adapter), adapter_files=files, updates=320, presentations=1280))
        old_spec = dict(runner_sha256=runtime.LEVEL1_SHA256, skill='perception', learner_seed=seed,
                        source_files=self.specification['source_files'], material=self.record(self.material), protocol=self.specification['protocol'])
        plan = dict(root=str(root), scope=self.helper.SCOPE, self_sha256=runtime.LEVEL1_SHA256, skill='perception',
                    learner_seed=seed, model=str(self.model), model_files=self.model_files, config=config, specification=old_spec)
        runtime.write(root / 'plan.json', plan)
        pin = runtime.digest(root / 'plan.json')
        complete = dict(plan_sha256=pin, calls=120, scored=False, stages=dict(OFF={}, fit=runtime.tree(root / 'run/fit'), post={}))
        runtime.write(root / 'capture_complete.json', complete)
        completion_pin = runtime.digest(root / 'capture_complete.json')
        collection = self.home / f'upstream_seed{seed}_collected'
        collection.mkdir()
        runtime.write(collection / 'scores.json', dict(CPU_fixture_never_inspect_score_values=True))
        runtime.write(collection / 'collection.json', dict(completion_sha256=completion_pin, scores_sha256=runtime.digest(collection / 'scores.json')))
        runtime.write(root.with_name(root.name + '.collection_claim.json'), dict(plan_sha256=pin, out=str(collection), retry=False))
        return dict(seed=seed, root=str(root), plan_sha256=pin, completion_sha256=completion_pin,
                    collection=self.record(collection / 'collection.json'), adapter_files=files)

    def prepare(self):
        runtime.write(self.spec_path, self.specification)
        result = runtime.prepare(self.root, self.spec_path, runtime.digest(self.spec_path), allow_native=True)
        self.pin = result['plan_sha256']
        self.plan, self.core, self.dependencies, _ = runtime.verify(self.root, self.pin)
        return result

    def fake_state(self, plan, pin, state, deadline, probe):
        directory = self.root / 'run' / state
        directory.mkdir()
        pid = 90000 + runtime.STATES.index(state)
        identity = dict(pid=pid, pgid=pid, state=state, plan_sha256=pin)
        runtime.write(directory / 'launch.json', identity)
        runtime.write(directory / 'started.json', identity)
        with patch.object(runtime, 'Native', NativeFixture):
            runtime.capture_state(plan, state, self.core, self.dependencies, probe)
        runtime.write(directory / 'released.json', dict(pid=pid, pgid=pid))

    def complete(self):
        self.prepare()
        with patch.object(runtime, 'run_state', self.fake_state):
            result = runtime.controller(self.root, self.pin, allow_gpu=True)
        self.completion = result['completion_sha256']

    def test_prepare_native_tokenizer_only_exact_contract_and_upstream(self):
        result = self.prepare()
        self.assertIn('NOT_GPU_APPROVAL', result['status'])
        self.assertEqual(self.plan['core_contract']['max_output_tokens'], dict(wake=96, record=192))
        self.assertEqual(len(self.plan['episode_ids']), 8)
        self.assertEqual(list(self.plan['upstream']), list(runtime.STATES[1:]))
        self.assertEqual(self.plan['budget']['controller'], 1800)
        self.assertEqual(len(runtime.read(self.root / 'initial_prompts.json')), 8)
        self.assertFalse((self.root / 'run').exists())

    def test_four_fresh_states_full128calls_sequential_source_joins_and_collection(self):
        self.complete()
        self.assertEqual(len(NativeFixture.instances), 4)
        for instance in NativeFixture.instances:
            self.assertTrue(instance.closed)
            self.assertEqual(len(instance.seen), 32)
            self.assertEqual([request['core_request']['kind'] for request in instance.seen], ['wake', 'record'] * 16)
            second_wake = instance.seen[2]['messages'][0]['content']
            self.assertIn('Earlier actual transcript', second_wake)
            self.assertIn('record_raw', second_wake)
        self.assertIsNone(NativeFixture.instances[0].route)
        self.assertEqual(len({instance.route['path'] for instance in NativeFixture.instances[1:]}), 3)
        before = runtime.tree(self.root)
        out = self.home / 'collection'
        runtime.collect(self.root, self.pin, self.completion, out)
        report = runtime.read(out / 'formation_report.json')
        self.assertEqual(sum(state['calls'] for state in report['costs'].values()), 128)
        self.assertEqual(report['comparison']['missing_states'], [])
        self.assertFalse(report['automatic_pass'])
        self.assertIsNone(report['scientific_pass'])
        self.assertFalse(report['comparison']['native_identity_verified'])
        self.assertEqual(runtime.tree(self.root), before)
        with self.assertRaises(FileExistsError):
            runtime.collect(self.root, self.pin, self.completion, self.home / 'retry')

    def test_invalid_wakes_no_fabricated_records_actual64calls(self):
        NativeFixture.mode = 'invalid'
        self.complete()
        complete = runtime.read(self.root / 'capture_complete.json')
        self.assertEqual(complete['calls'], 64)
        for state in runtime.STATES:
            capture = runtime.read(self.root / 'run' / state / 'formation.json')
            self.assertEqual(capture['summary']['world_executions'], 0)
            self.assertEqual(capture['summary']['missing_records'], 16)
            self.assertEqual(capture['summary']['possible_records'], 16)

    def test_actual96token_length_wake_is_preserved_not_executed(self):
        NativeFixture.mode = 'length'
        self.complete()
        capture = runtime.read(self.root / 'run/OFF/formation.json')
        self.assertEqual(capture['summary']['world_executions'], 0)
        self.assertEqual(len(runtime.read(self.root / 'run/OFF/00.response.json')['output_token_ids']), 96)

    def test_fenced_native_record_never_rewritten_for_production(self):
        NativeFixture.mode = 'fenced'
        self.complete()
        capture = runtime.read(self.root / 'run/OFF/formation.json')
        self.assertEqual(capture['summary']['content_correct'], 16)
        self.assertEqual(capture['summary']['production_eligible'], 0)
        self.assertTrue(capture['episodes'][0]['turns'][0]['record']['response']['raw'].startswith('```json'))

    def test_backend_failure_aborts_instead_of_core_silent_refusal(self):
        self.prepare()
        NativeFixture.mode = 'error'
        with patch.object(runtime, 'run_state', self.fake_state):
            with self.assertRaises(runtime.NativeCaptureFailure):
                runtime.controller(self.root, self.pin, allow_gpu=True)
        self.assertTrue((self.root / 'controller_failure.json').exists())
        self.assertFalse((self.root / 'capture_complete.json').exists())
        self.assertTrue(NativeFixture.instances[0].closed)
        out = self.home / 'failed_collection'
        with self.assertRaisesRegex(ValueError, 'failed or unbound'):
            runtime.collect(self.root, self.pin, '0' * 64, out)
        self.assertFalse((out / 'formation_report.json').exists())

    def test_wrong_route_overbudget_dynamic_context_fail_closed(self):
        self.prepare()
        directory = self.root / 'run/OFF'
        for mode in ('bad_route', 'over_budget'):
            with self.subTest(mode=mode):
                target = self.home / mode
                target.mkdir()
                plan = dict(self.plan, root=str(target))
                (target / 'run/OFF').mkdir(parents=True)
                NativeFixture.mode = mode
                with patch.object(runtime, 'Native', NativeFixture):
                    with self.assertRaises(runtime.NativeCaptureFailure):
                        runtime.capture_state(plan, 'OFF', self.core, self.dependencies, self.probe)
        directory.mkdir(parents=True)
        NativeFixture.mode = 'valid'
        with patch.object(runtime, 'Native', NativeFixture), patch.dict(runtime.ENGINE, max_model_len=10):
            with self.assertRaises(runtime.NativeCaptureFailure):
                runtime.capture_state(self.plan, 'OFF', self.core, self.dependencies, self.probe)

    def test_upstream_adapter_collection_and_duplicate_seed_rejected(self):
        duplicate = copy.deepcopy(self.specification)
        duplicate['upstream'][1]['seed'] = 0
        with self.assertRaisesRegex(ValueError, 'three distinct'):
            runtime.upstream_bindings(duplicate, self.helper, self.binding)
        scores = Path(self.specification['upstream'][0]['collection']['path']).parent / 'scores.json'
        original = scores.read_bytes()
        scores.write_text('changed')
        with self.assertRaisesRegex(ValueError, 'collected bytes'):
            runtime.upstream_bindings(self.specification, self.helper, self.binding)
        scores.write_bytes(original)
        adapter = Path(self.specification['upstream'][0]['root']) / 'run/fit/adapter/adapter_model.safetensors'
        adapter.write_text('changed')
        with self.assertRaisesRegex(ValueError, 'adapter files'):
            runtime.upstream_bindings(self.specification, self.helper, self.binding)

    def test_raw_capture_tamper_and_reused_worker_pid_rejected(self):
        self.complete()
        response_path = self.root / 'run/OFF/00.response.json'
        original = response_path.read_bytes()
        response_path.write_text('{}')
        with self.assertRaisesRegex(ValueError, 'capture bytes'):
            runtime.validate_completed(self.plan, self.pin, self.core, self.dependencies)
        response_path.write_bytes(original)
        receipt = self.root / 'run/perception_seed0/released.json'
        receipt.write_text(json.dumps(dict(pid=90000, pgid=90000)))
        with self.assertRaisesRegex(ValueError, 'process receipts'):
            runtime.validate_completed(self.plan, self.pin, self.core, self.dependencies)

    def test_plan_protocol_source_pins_and_fresh_root(self):
        self.prepare()
        with self.assertRaisesRegex(ValueError, 'plan pin'):
            runtime.verify(self.root, '0' * 64)
        with self.assertRaisesRegex(ValueError, 'fresh formation root'):
            runtime.prepare(self.root, self.spec_path, runtime.digest(self.spec_path), allow_native=True)
        protocol = Path(self.specification['protocol']['path'])
        protocol.write_text('drift')
        with self.assertRaisesRegex(ValueError, 'input file pin'):
            runtime.verify(self.root, self.pin)

    def test_owned_timeout_cleanup_and_no_foreign_kill(self):
        self.prepare()
        (self.root / 'run').mkdir()
        process = Mock(pid=98765)
        process.wait.side_effect = subprocess.TimeoutExpired('CPU worker', 1)
        with patch.object(self.probe, 'gpu_state', return_value=True), patch.object(runtime.subprocess, 'Popen', return_value=process), \
             patch.object(self.probe, 'cleanup') as cleanup, patch.object(self.probe, 'group_alive', return_value=False):
            with self.assertRaises(subprocess.TimeoutExpired):
                runtime.run_state(self.plan, self.pin, 'OFF', time.monotonic()+1000, self.probe)
            cleanup.assert_called_once_with(process)
            self.assertLessEqual(process.wait.call_args.kwargs['timeout'], 900)
        with patch.object(self.probe, 'gpu_state', return_value=False), patch.object(self.probe, 'cleanup') as cleanup:
            with self.assertRaisesRegex(ValueError, 'not vacant'):
                runtime.run_state(self.plan, self.pin, 'perception_seed0', time.monotonic()+1000, self.probe)
            cleanup.assert_not_called()

    def test_upstream_scores_never_interpreted_and_core_budget_drift_rejected(self):
        original_read = runtime.read
        def no_score_read(path):
            self.assertNotEqual(Path(path).name, 'scores.json')
            return original_read(path)
        with patch.object(runtime, 'read', side_effect=no_score_read):
            self.prepare()
        original_loader = runtime.load_module
        def mismatched_core(record, name):
            module = original_loader(record, name)
            if name == 'core':
                module.MAX_OUTPUT_TOKENS = dict(wake=64, record=192)
            return module
        with patch.object(runtime, 'load_module', side_effect=mismatched_core):
            with self.assertRaisesRegex(ValueError, 'token-budget contract'):
                runtime.checked_apis(self.specification)


if __name__ == '__main__':
    unittest.main()
