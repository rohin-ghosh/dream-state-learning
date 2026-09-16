from contextlib import contextmanager
from copy import deepcopy
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time
from types import SimpleNamespace

import pytest

from gpu import orch_guided_native as weights
from gpu import orch_r125_continual_native as native
from gpu import orch_r125_continual_readout as runner
from organism_v6 import orch_r107_capability as policy


RAW = '<think>Raw reasoning is retained verbatim.</think>\nanswer\n'
ADAPTER_SHA256 = 'a' * 64


def test_bare_CUuuid_preserves_exact_bound_device(monkeypatch):
    expected = 'GPU-d62ba12e-ff08-9e5e-ba35-14c723f6e05b'
    monkeypatch.setenv('CUDA_VISIBLE_DEVICES', expected)
    engine = Engine(expected)
    engine.device_uuid = expected.removeprefix('GPU-')
    assert runner._verify_device(engine, {'gpu_uuid': expected}) == expected
    engine.device_uuid = 'd62ba12e-ff08-9e5e-ba35-14c723f6e05c'
    with pytest.raises(ValueError, match='CUDA_UUID_mismatch'):
        runner._verify_device(engine, {'gpu_uuid': expected})


class Model:
    def __init__(self):
        self.parameter = SimpleNamespace(requires_grad=False)
        self.training = False
        self.disable_adapters = False
        self.lora_A, self.lora_B = {}, {}
        self.disable_calls = 0
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
        self.disable_calls += 1
        self.disable_adapters = True
        try:
            yield
        finally:
            self.disable_adapters = False
            self.parameter.requires_grad = True


class Engine:
    def __init__(self, gpu_uuid):
        self.model = Model()
        self.tokenizer = SimpleNamespace(eos_token_id=99)
        self.device_uuid = gpu_uuid
        self.device_count = 1
        self.torch = SimpleNamespace(cuda=SimpleNamespace(device_count=lambda: self.device_count,
            get_device_properties=lambda index: SimpleNamespace(uuid=self.device_uuid)))
        self.calls = []
        self.base_checks = 0
        self.fail_at = None
        self.base_fail_at = None
        self.after_generate = lambda response: None

    def verify_base(self):
        self.base_checks += 1
        if self.base_checks == self.base_fail_at:
            raise ValueError('frozen_base_changed')

    def generate(self, messages, *, max_new_tokens):
        assert not self.model.parameter.requires_grad
        assert max_new_tokens == 512
        self.calls.append((deepcopy(messages), self.model.disable_adapters))
        if len(self.calls) == self.fail_at:
            raise RuntimeError('synthetic_generation_failure')
        response = dict(raw=RAW, messages=deepcopy(messages), token_ids=[7, 99],
            prompt_tokens=20, terminal=True, truncated=False)
        self.after_generate(response)
        return response


@pytest.fixture
def setup(tmp_path, monkeypatch):
    root = tmp_path / 'life'
    checkpoint_dir = root / 'checkpoints' / 'sleep_0001'
    adapter_dir = checkpoint_dir / 'adapter'
    adapter_dir.mkdir(parents=True)
    (adapter_dir / 'adapter_model.safetensors').write_bytes(b'checkpoint adapter')
    optimizer_path = checkpoint_dir / 'optimizer_rng.pt'
    optimizer_path.write_bytes(b'hashed but never deserialized optimizer and RNG')
    adapter_files = {'adapter_model.safetensors': native.sha(adapter_dir / 'adapter_model.safetensors')}
    checkpoint = dict(schema=native.SCHEMA, base_sha256=native.BASE_SHA256,
        adapter_path=str(adapter_dir), adapter_files=adapter_files,
        adapter_state_sha256=ADAPTER_SHA256, optimizer_rng_path=str(optimizer_path),
        checkpoint_sha256=dict(adapter=policy.digest(adapter_files),
            optimizer=native.sha(optimizer_path), rng=native.sha(optimizer_path)), optimizer_steps=16)
    commit_path = checkpoint_dir / 'COMMIT.json'
    native.write_once(commit_path, checkpoint)
    now = time.time()
    plan = dict(schema=native.SCHEMA, base_sha256=native.BASE_SHA256,
        system_prompt=native.SYSTEM, birth_prompt=native.BIRTH,
        compaction_invitation=native.COMPACTION_INVITATION,
        new_presentations=16, rehearsal_presentations=1, anchor_lambda=0.25,
        seed=0, segments_per_sleep=2, segment_tokens=512, context_limit=4096,
        max_sleeps=1, physical=0, gpu_uuid='GPU-test-bound-device',
        hard_end_unix=now + 3600, lease_end_unix=now + 7200,
        decoder=dict(temperature=0.7, top_p=0.95, repetition_penalty=1.05, no_repeat_ngram_size=16),
        root=str(root), model_dir=str(tmp_path / 'model'), anchors=str(tmp_path / 'anchors'),
        source_root=str(tmp_path / 'source'), history=[{'secret': 'must not reach model'}],
        parent_messages=['must not reach model'])
    plan_path = root / 'PLAN.json'
    native.write_once(plan_path, plan)
    monkeypatch.setenv('R125_ADMISSION_PLAN_SHA256', native.sha(plan_path))
    monkeypatch.setenv('CUDA_VISIBLE_DEVICES', plan['gpu_uuid'])
    engine = Engine(plan['gpu_uuid'])
    loads = []

    def load(actual_plan, actual_checkpoint, check):
        loads.append((actual_plan, actual_checkpoint))
        check('load')
        return engine

    monkeypatch.setattr(runner, '_load_engine', load)
    monkeypatch.setattr(weights, 'state_hash', lambda parameters: engine.model.adapter_sha256)
    output = root / 'readouts' / 'sleep_0001'
    return SimpleNamespace(root=root, plan=plan, plan_path=plan_path, checkpoint=checkpoint,
        checkpoint_dir=checkpoint_dir, commit_path=commit_path, output=output, engine=engine, loads=loads)


def execute(setup):
    return runner.run(setup.plan_path, setup.checkpoint_dir, setup.output)


def test_full_fixed_suite_public_projection_actual_off_and_no_history(setup, monkeypatch):
    monkeypatch.setattr(runner.socket, 'gethostname', lambda: 'private-node-name')
    original = native.NativeChild.verify_checkpoint
    verifications = []

    def verify(document):
        verifications.append(deepcopy(document))
        original(document)

    monkeypatch.setattr(native.NativeChild, 'verify_checkpoint', staticmethod(verify))
    monkeypatch.setattr(native.NativeChild, '__init__', lambda *args, **kwargs: pytest.fail('native child loaded'))
    stream = setup.root / 'stream'
    stream.mkdir()
    (stream / 'history.json').write_text('private TRAIN history; never read or modify')
    result = execute(setup)
    assert result == native.read(setup.output / 'COMPLETE.json')
    assert result['pid'] == os.getpid()
    assert 'hostname' not in result
    assert result['host_sha256'] == hashlib.sha256(b'private-node-name').hexdigest()
    assert all('private-node-name' not in path.read_text() for path in setup.output.rglob('*.json'))
    assert result['checkpoint_commit_sha256'] == native.sha(setup.commit_path)
    assert result['suite_sha256'] == policy.digest(policy.tasks()) == runner.SUITE_SHA256
    assert result['before_after_verified'] and result['calls'] == 64 and result['task_count'] == 32
    assert result['paired_scores']['recorded_cells'] == 64
    assert result['paired_scores']['all_pairs_complete']
    assert result['paired_scores']['overall']['pairs']['counts']['both_fail'] == 32
    assert result['training_updates'] == 0 and not result['train_ingestion']
    assert not result['history_present'] and not result['parent_present']
    assert len(verifications) == 3 and setup.engine.base_checks == 2
    assert setup.engine.model.disable_calls == 32
    assert not setup.engine.model.disable_adapters and not setup.engine.model.parameter.requires_grad
    assert (stream / 'history.json').read_text() == 'private TRAIN history; never read or modify'
    captures = []
    for position, task in enumerate(policy.tasks()):
        for offset, off in enumerate((False, True) if position % 2 == 0 else (True, False)):
            index = position * 2 + offset
            assert setup.engine.calls[index] == (policy.messages(task), off)
            name = f'CALL_{index:03d}.json'
            receipt = native.read(setup.output / name)
            assert receipt['messages'] == policy.messages(task)
            assert receipt['response']['raw'] == RAW
            assert receipt['response']['max_new_tokens'] == 512
            assert receipt['capture']['lora_enabled'] is not off
            assert receipt['pid'] == result['pid']
            assert result['call_files'][name] == native.sha(setup.output / name)
            assert native.read(setup.output / 'reservations' / name)['status'] == 'RESERVED'
            captures.append(receipt['capture'])
    assert result['paired_scores'] == policy.reduce_paired(captures,
        checkpoint_sha256=ADAPTER_SHA256, base_sha256=native.BASE_SHA256, max_new_tokens=512)
    with pytest.raises(FileExistsError):
        execute(setup)
    assert len(setup.loads) == 1


@pytest.mark.parametrize('variable,value,error', [
    ('R125_ADMISSION_PLAN_SHA256', None, 'admission_plan_SHA256_binding'),
    ('R125_ADMISSION_PLAN_SHA256', '0' * 64, 'admission_plan_SHA256_binding'),
    ('CUDA_VISIBLE_DEVICES', '0', 'one_bound_GPU_environment'),
    ('CUDA_VISIBLE_DEVICES', 'GPU-wrong', 'one_bound_GPU_environment'),
])
def test_admission_rejected_before_loading_or_writing(setup, monkeypatch, variable, value, error):
    if value is None:
        monkeypatch.delenv(variable)
    else:
        monkeypatch.setenv(variable, value)
    with pytest.raises(ValueError, match=error):
        execute(setup)
    assert not setup.loads and not setup.output.exists()


@pytest.mark.parametrize('field,value,error', [
    ('schema', 'wrong', 'frozen_native_contract'),
    ('base_sha256', '0' * 64, 'frozen_native_contract'),
    ('system_prompt', 'changed', 'exact_posted_prompts'),
    ('segment_tokens', 2048, 'bounded_native_segment'),
    ('hard_end_unix', 0, 'within_lease_wall'),
])
def test_native_plan_validation_not_replaced(setup, monkeypatch, field, value, error):
    setup.plan[field] = value
    setup.plan_path.write_text(json.dumps(setup.plan))
    monkeypatch.setenv('R125_ADMISSION_PLAN_SHA256', native.sha(setup.plan_path))
    with pytest.raises(ValueError, match=error):
        execute(setup)
    assert not setup.loads and not setup.output.exists()


@pytest.mark.parametrize('artifact,error', [
    ('optimizer_rng.pt', 'optimizer_RNG_file_binding'),
    ('adapter/adapter_model.safetensors', 'adapter_file_binding'),
])
def test_native_checkpoint_hashes_verified_before_load(setup, artifact, error):
    (setup.checkpoint_dir / artifact).write_bytes(b'tampered')
    with pytest.raises(ValueError, match=error):
        execute(setup)
    assert not setup.loads and not setup.output.exists()


@pytest.mark.parametrize('destination', ['stream/diagnostic', 'TRAIN/diagnostic', 'checkpoints/diagnostic', 'readouts'])
def test_output_never_stream_train_checkpoint_or_shared_readouts(setup, destination):
    with pytest.raises(ValueError, match='separate_node_local_readouts'):
        runner.run(setup.plan_path, setup.commit_path, setup.root / destination)
    assert not setup.loads


def test_output_symlink_cannot_escape_readouts(setup):
    setup.output.parent.mkdir()
    (setup.output.parent / 'escape').symlink_to(setup.root, target_is_directory=True)
    with pytest.raises(ValueError, match='separate_node_local_readouts'):
        runner.run(setup.plan_path, setup.commit_path, setup.output.parent / 'escape' / 'leaked')
    assert not setup.loads


@pytest.mark.parametrize('fail_at', [1, 2, 17])
def test_failed_calls_are_durable_no_retry_and_partial_pairs_retained(setup, fail_at):
    setup.engine.fail_at = fail_at
    with pytest.raises(RuntimeError, match='synthetic_generation_failure'):
        execute(setup)
    failed = native.read(setup.output / 'FAILED.json')
    assert failed['calls'] == fail_at and failed['before_after_verified']
    assert failed['paired_scores']['recorded_cells'] == fail_at
    assert not failed['paired_scores']['all_pairs_complete']
    assert native.read(setup.output / f'CALL_{fail_at - 1:03d}.json')['status'] == 'FAILED'
    assert not (setup.output / 'COMPLETE.json').exists()
    assert len(setup.engine.calls) == fail_at
    assert not setup.engine.model.disable_adapters and not setup.engine.model.parameter.requires_grad
    assert setup.engine.base_checks == 2


@pytest.mark.parametrize('kind,error', [
    ('adapter', 'immutable_checkpoint_adapter'),
    ('base', 'frozen_base_changed'),
    ('commit', 'checkpoint_COMMIT_changed'),
    ('plan', 'admission_plan_SHA256_binding'),
    ('disk', 'adapter_file_binding'),
])
def test_after_integrity_failures_preserve_raw_without_complete(setup, kind, error):
    def mutate(response):
        if len(setup.engine.calls) != 64:
            return
        if kind == 'adapter':
            setup.engine.model.adapter_sha256 = 'b' * 64
        elif kind == 'base':
            setup.engine.base_fail_at = 2
        elif kind == 'commit':
            setup.commit_path.write_text(setup.commit_path.read_text() + '\n')
        elif kind == 'plan':
            setup.plan_path.write_text(setup.plan_path.read_text() + '\n')
        else:
            (setup.checkpoint_dir / 'adapter/adapter_model.safetensors').write_bytes(b'changed')

    setup.engine.after_generate = mutate
    with pytest.raises(ValueError, match=error):
        execute(setup)
    assert native.read(setup.output / 'AFTER.json')['status'] == 'FAILED'
    assert not native.read(setup.output / 'FAILED.json')['before_after_verified']
    assert native.read(setup.output / 'CALL_063.json')['response']['raw'] == RAW
    assert not (setup.output / 'COMPLETE.json').exists()


@pytest.mark.parametrize('kind', ['uuid', 'count', 'adapter', 'base', 'trainable', 'training'])
def test_loaded_engine_must_be_readonly_and_bound_before_calls(setup, kind):
    if kind == 'uuid':
        setup.engine.device_uuid = 'GPU-other'
    elif kind == 'count':
        setup.engine.device_count = 2
    elif kind == 'adapter':
        setup.engine.model.adapter_sha256 = 'b' * 64
    elif kind == 'base':
        setup.engine.base_fail_at = 1
    elif kind == 'trainable':
        setup.engine.model.parameter.requires_grad = True
    else:
        setup.engine.model.training = True
    with pytest.raises((ValueError, AssertionError)):
        execute(setup)
    assert not setup.engine.calls
    assert (setup.output / 'FAILED.json').exists()
    assert not (setup.output / 'COMPLETE.json').exists()


@pytest.mark.parametrize('kind,error', [
    ('history', 'exact_prompt_mismatch'),
    ('cap', 'fixed_cap512'),
    ('tokens', 'native_cap_violation'),
])
def test_malformed_response_is_failed_and_raw_is_preserved(setup, kind, error):
    def mutate(response):
        if kind == 'history':
            response['messages'].append(dict(role='assistant', content='prior history'))
        elif kind == 'cap':
            response['max_new_tokens'] = 1536
        else:
            response['token_ids'] = [7] * 512 + [99]

    setup.engine.after_generate = mutate
    with pytest.raises(ValueError, match=error):
        execute(setup)
    receipt = native.read(setup.output / 'CALL_000.json')
    assert receipt['status'] == 'FAILED' and receipt['response']['raw'] == RAW
    assert receipt['capture']['result']['completion'] == 'execution_error'
    assert not (setup.output / 'COMPLETE.json').exists()


def test_token_cap_truncation_is_not_promoted_to_a_complete_pair(setup):
    def truncate(response):
        response.update(token_ids=[7] * 512, terminal=False, truncated=True)

    setup.engine.after_generate = truncate
    result = execute(setup)
    assert result['status'] == 'COMPLETE' and result['calls'] == 64
    assert not result['paired_scores']['all_pairs_complete']
    assert result['paired_scores']['overall']['pairs']['counts']['incomplete_pair'] == 32


def test_load_failure_has_terminal_receipt(setup, monkeypatch):
    def fail(*args):
        raise RuntimeError('load_failure')

    monkeypatch.setattr(runner, '_load_engine', fail)
    with pytest.raises(RuntimeError, match='load_failure'):
        execute(setup)
    failed = native.read(setup.output / 'FAILED.json')
    assert failed['calls'] == 0 and not failed['before_after_verified']
    assert failed['paired_scores']['recorded_cells'] == 0


def test_pair_reducer_failure_still_has_terminal_receipt(setup):
    def mismatch(response):
        response['prompt_tokens'] += int(setup.engine.model.disable_adapters)

    setup.engine.after_generate = mismatch
    with pytest.raises(ValueError, match='paired_prompt_token_mismatch'):
        execute(setup)
    failed = native.read(setup.output / 'FAILED.json')
    assert failed['calls'] == 64 and failed['before_after_verified']
    assert failed['reduction_error']['error'] == 'paired_prompt_token_mismatch'
    assert 'paired_scores' not in failed
    assert not (setup.output / 'COMPLETE.json').exists()


def test_off_must_really_disable_adapter(setup, monkeypatch):
    @contextmanager
    def ineffective_disable():
        yield

    monkeypatch.setattr(setup.engine.model, 'disable_adapter', ineffective_disable)
    with pytest.raises(AssertionError):
        execute(setup)
    assert len(setup.engine.calls) == 1
    assert native.read(setup.output / 'CALL_001.json')['status'] == 'FAILED'
    assert not (setup.output / 'COMPLETE.json').exists()


def test_cli_exact_paths(monkeypatch, tmp_path):
    observed = []
    monkeypatch.setattr(runner, 'run', lambda *args: observed.append(args))
    paths = [tmp_path / name for name in ('plan.json', 'COMMIT.json', 'readouts/sleep_1')]
    runner.main(['--plan', str(paths[0]), '--checkpoint', str(paths[1]), '--output', str(paths[2])])
    assert observed == [tuple(paths)]


@pytest.mark.parametrize('argv', [[], ['--plan', 'plan'],
    ['--plan', 'plan', '--checkpoint', 'checkpoint'],
    ['--plan', 'plan', '--checkpoint', 'checkpoint', '--output', 'output', '--history', 'private']])
def test_cli_requires_all_three_paths_and_rejects_history(argv):
    with pytest.raises(SystemExit) as error:
        runner.main(argv)
    assert error.value.code == 2


def test_cli_help_is_cpu_only_and_does_not_import_native():
    source = """
import sys
from gpu import orch_r125_continual_readout as runner
assert 'torch' not in sys.modules
assert 'gpu.orch_r125_continual_native' not in sys.modules
runner.main(['--help'])
"""
    result = subprocess.run([sys.executable, '-B', '-c', source], cwd=Path(__file__).resolve().parents[1],
        capture_output=True, text=True, check=False)
    assert result.returncode == 0, result.stderr
    assert all(flag in result.stdout for flag in ('--plan', '--checkpoint', '--output'))


def test_real_loader_uses_readout_engine_without_optimizer(setup, monkeypatch):
    from gpu import astra_experienced_event_microloop as source

    observed = []
    monkeypatch.setitem(sys.modules, 'torch', SimpleNamespace(cuda=SimpleNamespace(is_initialized=lambda: False)))
    monkeypatch.setattr(source.native, 'load_local_tokenizer', lambda path: 'local-tokenizer')

    def engine(options, tokenizer, *, check):
        observed.append((vars(options), tokenizer, check))
        return setup.engine

    monkeypatch.setattr(source, 'Engine', engine)
    loader = REAL_LOADER
    check = lambda label: None
    assert loader(setup.plan, setup.checkpoint, check) is setup.engine
    options, tokenizer, actual_check = observed[0]
    assert options['phase'] == 'readout' and options['adapter_dir'] == setup.checkpoint['adapter_path']
    assert options['device'] == 'cuda:0' and options['expected_base_sha256'] == native.BASE_SHA256
    assert tokenizer == 'local-tokenizer' and actual_check is check
    assert 'history' not in options and 'optimizer_rng_path' not in options


def test_real_loader_rejects_resident_cuda(setup, monkeypatch):
    monkeypatch.setitem(sys.modules, 'torch', SimpleNamespace(cuda=SimpleNamespace(is_initialized=lambda: True)))
    with pytest.raises(ValueError, match='fresh_process_without_resident_CUDA'):
        REAL_LOADER(setup.plan, setup.checkpoint, lambda label: None)


REAL_LOADER = runner._load_engine
