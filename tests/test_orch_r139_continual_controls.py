"""CPU-only R139 controls: fabricated models, mailbox events and readout tasks."""

from contextlib import contextmanager
from copy import deepcopy
import json
from pathlib import Path
import random
import signal
import sys
import time
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from gpu import orch_r139_continual_controls as controls
from gpu import orch_r125_continual_native as native
from gpu.orch_r125_stream_journal import StreamJournal
from organism_v6.orch_r125_continual_stream import digest


ADAPTER_HASH = 'a' * 64


def fixture_plan(tmp_path, monkeypatch, *, mode=controls.MODES[1], adapter=None, max_readouts=2):
    source = tmp_path / 'source'
    source.mkdir(exist_ok=True)
    startup = source / 'startup.txt'
    startup.write_text('Fixture R127 startup: continue your inquiry.')
    reference = dict(schema=native.SCHEMA, base_sha256=native.BASE_SHA256,
        system_prompt=native.SYSTEM, birth_prompt=startup.read_text(),
        startup_context=dict(version='R127_STARTUP_V1', path=str(startup), sha256=native.sha(startup)),
        compaction_invitation=native.COMPACTION_INVITATION,
        new_presentations=16, rehearsal_presentations=1, anchor_lambda=0.25, seed=37,
        segments_per_sleep=2, segment_tokens=16, context_limit=8192, max_sleeps=None,
        physical=0, gpu_uuid='GPU-fixture', hard_end_unix=time.time() + 600,
        lease_end_unix=time.time() + 1000,
        decoder=dict(temperature=0.7, top_p=0.95, repetition_penalty=1.05, no_repeat_ngram_size=16),
        root=str(tmp_path / 'life'), model_dir=str(tmp_path / 'model'),
        anchors=str(tmp_path / 'anchors'), source_root=str(source))
    monkeypatch.setattr(controls, 'source_inventory', lambda root: {name: 'b' * 64 for name in controls.SOURCE_FILES})
    return controls.make_plan(reference, mode=mode, adapter=adapter, max_readouts=max_readouts)


def fixture_adapter(tmp_path):
    from gpu.astra_pchain2_native import TARGET_MODULES
    directory = tmp_path / 'actual_adapter'
    directory.mkdir()
    (directory / 'adapter_config.json').write_text(json.dumps(dict(peft_type='LORA', r=8, lora_alpha=16,
        lora_dropout=0.05, bias='none', task_type='CAUSAL_LM', target_modules=list(TARGET_MODULES))))
    (directory / 'adapter_model.safetensors').write_bytes(b'fixture only; never loaded by real PEFT')
    return dict(initialization='pretrained_rank8', path=str(directory),
                files=controls.adapter_files(directory), state_sha256=ADAPTER_HASH)


def test_plan_preserves_seed_prompts_context_and_decoder(tmp_path, monkeypatch):
    plan = fixture_plan(tmp_path, monkeypatch)
    assert controls.validate_plan(plan) is plan
    assert plan['seed'] == plan['control']['sampling_rng']['seed'] == 37
    assert plan['system_prompt'] == native.SYSTEM
    assert plan['birth_prompt'] == Path(plan['startup_context']['path']).read_text()
    assert plan['decoder'] == dict(temperature=0.7, top_p=0.95, repetition_penalty=1.05,
                                   no_repeat_ngram_size=16)
    assert plan['control']['readout_schedule']['reference_presleep_extra_segments'] == 1
    before = deepcopy(plan)
    controls.validate_plan(plan)
    assert plan == before


@pytest.mark.parametrize('field,value,error', [
    ('mode', 'learning', 'explicit_control_mode'),
    ('learning_steps', 1, 'no_learning_sleep_or_compaction'),
    ('learning_steps', False, 'no_learning_sleep_or_compaction'),
    ('optimizer_steps', 1, 'no_learning_sleep_or_compaction'),
    ('sleep_enabled', True, 'no_learning_sleep_or_compaction'),
    ('compaction_at_sleep', True, 'no_learning_sleep_or_compaction'),
    ('adapter', {'initialization': 'seeded_rank8'}, 'base_control_has_no_adapter'),
])
def test_control_contract_rejections(tmp_path, monkeypatch, field, value, error):
    plan = fixture_plan(tmp_path, monkeypatch)
    plan['control'][field] = value
    with pytest.raises(ValueError, match=error):
        controls.validate_plan(plan)


@pytest.mark.parametrize('mutation,error', [
    (lambda plan: plan.update(seed=1), 'exact_reference_plan_binding'),
    (lambda plan: plan['control']['sampling_rng'].update(seed=1), 'exact_sampling_seed_initialization'),
    (lambda plan: plan['control']['readout_schedule'].update(every_segments=3), 'explicit_matched_readout_frontiers'),
    (lambda plan: plan['control']['readout_schedule'].update(max_readouts=True), 'explicit_control_smoke_limit'),
    (lambda plan: plan['control']['readout_schedule'].update(reference_presleep_extra_segments=0),
        'explicit_matched_readout_frontiers'),
])
def test_sampling_and_cadence_drift_rejected(tmp_path, monkeypatch, mutation, error):
    plan = fixture_plan(tmp_path, monkeypatch)
    mutation(plan)
    with pytest.raises(ValueError, match=error):
        controls.validate_plan(plan)


def test_real_pretrained_required_and_hash_bound(tmp_path, monkeypatch):
    adapter = fixture_adapter(tmp_path)
    plan = fixture_plan(tmp_path, monkeypatch, mode=controls.MODES[0], adapter=adapter)
    assert controls.validate_plan(plan) is plan
    (Path(adapter['path']) / 'adapter_model.safetensors').write_bytes(b'changed fixture')
    with pytest.raises(ValueError, match='pretrained_adapter_files_binding'):
        controls.validate_plan(plan)
    plan['control']['adapter']['path'] = str(tmp_path / 'missing')
    with pytest.raises(ValueError, match='real_adapter_directory_required'):
        controls.validate_plan(plan)
    plan['control']['adapter'] = None
    with pytest.raises(ValueError, match='explicit_real_adapter_initialization'):
        controls.validate_plan(plan)


def test_wrong_rank_and_symlink_rejected(tmp_path):
    adapter = fixture_adapter(tmp_path)
    directory = Path(adapter['path'])
    config = native.read(directory / 'adapter_config.json')
    config['r'] = 16
    (directory / 'adapter_config.json').write_text(json.dumps(config))
    with pytest.raises(ValueError, match='exact_native_rank8_recipe'):
        controls.adapter_files(directory)
    link = tmp_path / 'link'
    link.symlink_to(directory, target_is_directory=True)
    with pytest.raises(ValueError, match='real_adapter_directory_required'):
        controls.adapter_files(link)


class Model:
    def __init__(self, adapter=False):
        self.adapter = adapter
        self.parameter = SimpleNamespace(requires_grad=False, dtype='float32')
        self.training = False
        self.config = SimpleNamespace(max_position_embeddings=32768)
        self.moves = []

    def parameters(self):
        return [self.parameter]

    def named_parameters(self):
        return [('model.lora_A.weight' if self.adapter else 'model.base.weight', self.parameter)]

    def requires_grad_(self, value):
        self.parameter.requires_grad = value

    def eval(self):
        self.training = False

    def to(self, device):
        self.moves.append(device)
        return self


def fake_runtime(plan, monkeypatch):
    from gpu import astra_experienced_event_microloop as source
    from gpu import orch_guided_native as weights
    from gpu import orch_r125_continual_readout as readout
    events = []
    torch = SimpleNamespace(float32='float32', manual_seed=lambda seed: events.append(('cpu_seed', seed)),
        get_rng_state=lambda: 'CPU_STATE', set_rng_state=lambda state: events.append(('cpu_restore', state)),
        cuda=SimpleNamespace(manual_seed_all=lambda seed: events.append(('cuda_seed', seed)),
            synchronize=lambda: None, empty_cache=lambda: None,
            get_rng_state_all=lambda: ['CUDA_STATE'],
            set_rng_state_all=lambda state: events.append(('cuda_restore', state)), is_initialized=lambda: False))
    engines = []

    def engine_factory(options, tokenizer, *, check):
        assert options.phase == 'readout'
        assert options.expected_base_sha256 == native.BASE_SHA256
        events.append(('engine', options.adapter_dir))
        engine = SimpleNamespace(torch=torch, tokenizer=tokenizer, model=Model(bool(options.adapter_dir)),
            verify_base=Mock(), runtime={'fixture': True}, generate=Mock(return_value={'raw': 'fixture'}))
        engines.append(engine)
        return engine

    def initialize(child):
        child.seed_rng()
        events.append(('initialize_rank8', plan['seed']))
        child.engine.model.adapter = True

    monkeypatch.setattr(source, 'Engine', engine_factory)
    monkeypatch.setattr(source.native, 'load_local_tokenizer', lambda path: SimpleNamespace(eos_token_id=2))
    monkeypatch.setattr(native.NativeChild, 'initialize_adapter', initialize)
    monkeypatch.setattr(weights, 'state_hash', lambda parameters: ADAPTER_HASH)
    monkeypatch.setattr(readout, '_verify_device', lambda engine, plan: plan['gpu_uuid'])
    monkeypatch.setattr(controls.random, 'seed', lambda seed: events.append(('python_seed', seed)))
    monkeypatch.setitem(sys.modules, 'torch', torch)
    return events, engines


@pytest.mark.parametrize('mode,initialization', [(controls.MODES[1], None),
    (controls.MODES[0], 'seeded_rank8'), (controls.MODES[0], 'pretrained_rank8')])
def test_no_optimizer_and_exact_seed_order(tmp_path, monkeypatch, mode, initialization):
    adapter = fixture_adapter(tmp_path) if initialization == 'pretrained_rank8' else (
        {'initialization': initialization} if initialization else None)
    plan = fixture_plan(tmp_path, monkeypatch, mode=mode, adapter=adapter)
    events, engines = fake_runtime(plan, monkeypatch)
    child = controls.FrozenChild(plan)
    seeds = [('python_seed', 37), ('cpu_seed', 37), ('cuda_seed', 37)]
    assert events[1:] == (seeds + [('initialize_rank8', 37)] + seeds if initialization == 'seeded_rank8' else seeds)
    assert not hasattr(child, 'optimizer') and not hasattr(child, 'sleep') and not hasattr(child, 'checkpoint')
    assert child.identity['adapter_state_sha256'] == (ADAPTER_HASH if adapter else None)
    assert child.identity['learning_steps'] == child.identity['optimizer_steps'] == 0
    engines[0].verify_base.assert_called()
    assert not child.engine.model.parameter.requires_grad


def test_pretrained_tensor_mismatch_rejected(tmp_path, monkeypatch):
    adapter = fixture_adapter(tmp_path)
    adapter['state_sha256'] = 'd' * 64
    plan = fixture_plan(tmp_path, monkeypatch, mode=controls.MODES[0], adapter=adapter)
    fake_runtime(plan, monkeypatch)
    with pytest.raises(ValueError, match='loaded_pretrained_tensor_identity'):
        controls.FrozenChild(plan)


def test_base_hash_verifier_and_real_device_are_not_skipped(tmp_path, monkeypatch):
    plan = fixture_plan(tmp_path, monkeypatch)
    fake_runtime(plan, monkeypatch)
    child = controls.FrozenChild(plan)
    child.engine.verify_base.side_effect = ValueError('frozen_base_changed')
    with pytest.raises(ValueError, match='frozen_base_changed'):
        child.snapshot()


def test_readout_offload_restores_all_rng_without_optimizer(tmp_path, monkeypatch):
    plan = fixture_plan(tmp_path, monkeypatch)
    events, engines = fake_runtime(plan, monkeypatch)
    child = controls.FrozenChild(plan)
    prior_python_rng = random.getstate()
    state = child.offload_for_readout()
    random.random()
    child.restore_after_readout(state)
    assert random.getstate() == prior_python_rng
    assert ('cpu_restore', 'CPU_STATE') in events
    assert ('cuda_restore', ['CUDA_STATE']) in events
    assert engines[0].model.moves == ['cpu', 'cuda:0']


def fixture_manifest(plan):
    identity = dict(base_sha256=native.BASE_SHA256, base_fingerprint_verified=True,
        adapter_state_sha256=ADAPTER_HASH if plan['control']['adapter'] else None,
        gpu_uuid=plan['gpu_uuid'], mode=plan['control']['mode'], learning_steps=0, optimizer_steps=0)
    return dict(identity=identity, model_state_sha256=digest(identity))


def test_native_stream_continues_and_journal_has_no_sleep(tmp_path, monkeypatch):
    plan = fixture_plan(tmp_path, monkeypatch)
    stream = controls.new_stream(plan, fixture_manifest(plan))
    messages_seen = []

    def generate(messages, **kwargs):
        messages_seen.append(deepcopy(messages))
        assert kwargs == dict(max_new_tokens=16, deadline_unix=plan['hard_end_unix'])
        return dict(raw='Fixture thought.', token_ids=[10, 2], terminal=True, truncated=False)

    child = SimpleNamespace(plan=plan, generate=generate, count_tokens=lambda messages: len(messages))
    root = Path(plan['root'])
    root.mkdir()
    boundaries = []
    with StreamJournal(root / 'stream', create=True) as journal:
        journal.record('COMMITTED', dict(kind='BIRTH', state=stream.checkpoint()))
        native.write_once(journal.inbox / 'parent-fixture.json', dict(schema='R127_ATTRIBUTED_INBOX_V1',
            id='parent-fixture', text='Fixture parent message.', split='TRAIN', actor='parent',
            speaker='Astra', source_receipt=None))
        controls.drive(child, stream, journal, lambda cycle, frontier: boundaries.append((cycle, frontier)))
        assert journal.latest_checkpoint()['document']['state']['sleep_receipts'] == []
    assert boundaries == [(0, 0), (1, 2), (2, 4)]
    assert len(stream.rows) == 4 and stream.sleep_frontier == 0 and stream.sleep_due
    assert all(row['actor'] == 'child' and row['prefix_loss'] is False for row in stream.rows)
    assert all('Fixture parent message.' in str(messages) for messages in messages_seen)
    parents = [event for event in stream.history.events if event.actor == 'parent']
    assert len(parents) == 1 and parents[0].text == 'Astra: Fixture parent message.'
    assert not any(operation['kind'] == 'compaction' for operation in stream.history.operations)
    records = [native.read(path) for path in (root / 'stream/records').glob('[0-9]*.json')
               if not path.name.endswith('.intent.json')]
    assert not any(record['kind'].startswith('SLEEP') for record in records)
    with StreamJournal(root / 'stream') as recovered:
        assert len(recovered.latest_checkpoint()['document']['state']['rows']) == 4
    assert not (root / 'checkpoints').exists()


def test_generation_delegates_native_decoder_and_context(tmp_path, monkeypatch):
    plan = fixture_plan(tmp_path, monkeypatch)
    fake_runtime(plan, monkeypatch)
    child = controls.FrozenChild(plan)
    generate = Mock(return_value=dict(adapter_state_sha256=None, raw='fixture'))
    monkeypatch.setattr(native.NativeChild, 'generate', generate)
    result = child.generate([{'role': 'user', 'content': 'fixture'}], max_new_tokens=16,
                            deadline_unix=plan['hard_end_unix'])
    assert generate.call_args.args[0] is child
    assert generate.call_args.kwargs == dict(max_new_tokens=16, deadline_unix=plan['hard_end_unix'])
    assert result['learning_steps'] == result['optimizer_steps'] == 0


def test_base_manifest_has_no_fictitious_adapter_or_optimizer(tmp_path, monkeypatch):
    plan = fixture_plan(tmp_path, monkeypatch)
    fake_runtime(plan, monkeypatch)
    child = controls.FrozenChild(plan)
    Path(plan['root']).mkdir()
    path, manifest = controls.save_manifest(child, plan)
    assert controls.verify_manifest(plan, path) == manifest
    assert manifest['adapter_path'] is manifest['optimizer_checkpoint'] is None
    assert [entry.name for entry in path.parent.iterdir()] == ['MANIFEST.json']
    manifest['adapter_path'] = '/fixture/fake_adapter'
    path.write_text(json.dumps(manifest))
    with pytest.raises(ValueError, match='no_fake_base_adapter'):
        controls.verify_manifest(plan, path)


def gate_fixture(plan, tmp_path):
    log = tmp_path / 'cpu-tests.log'
    log.write_text('fixture test receipt')
    line = '[Builder] 2026-09-16 CPU/provenance fixture ' + controls.plan_binding(plan)
    coordination = Path(plan['source_root']) / 'research_loop/COORDINATION.md'
    coordination.parent.mkdir()
    coordination.write_text(line + '\n')
    receipt = dict(schema=controls.GATE_SCHEMA, status='PASS', plan_binding=controls.plan_binding(plan),
        source_files=plan['source_files'], tests_passed=True, test_log_path=str(log),
        test_log_sha256=native.sha(log), coordination_line=line)
    path = tmp_path / 'cpu-gate.json'
    native.write_once(path, receipt)
    plan['cpu_gate'] = dict(path=str(path), sha256=native.sha(path))
    return path


def test_CPU_gate_binds_plan_sources_log_and_coordination(tmp_path, monkeypatch):
    plan = fixture_plan(tmp_path, monkeypatch)
    with pytest.raises(ValueError, match='bound_CPU_gate_required'):
        controls.verify_gate(plan)
    gate_fixture(plan, tmp_path)
    controls.verify_gate(plan)
    plan['control']['sampling_rng']['seed'] = 2
    with pytest.raises(ValueError, match='passing_exact_CPU_provenance_gate'):
        controls.verify_gate(plan)
    plan['control']['sampling_rng']['seed'] = 37
    (tmp_path / 'cpu-tests.log').write_text('changed')
    with pytest.raises(ValueError, match='CPU_test_log_binding'):
        controls.verify_gate(plan)


def test_gate_rejects_source_drift_and_unlogged_Builder_receipt(tmp_path, monkeypatch):
    plan = fixture_plan(tmp_path, monkeypatch)
    gate_fixture(plan, tmp_path)
    monkeypatch.setattr(controls, 'source_inventory', lambda root: {})
    with pytest.raises(ValueError, match='source_provenance_drift'):
        controls.verify_gate(plan)
    monkeypatch.setattr(controls, 'source_inventory', lambda root: plan['source_files'])
    (Path(plan['source_root']) / 'research_loop/COORDINATION.md').write_text('unrelated fixture line\n')
    with pytest.raises(ValueError, match='operator_Builder_coordination_gate'):
        controls.verify_gate(plan)


def test_admission_rejected_before_any_model_load(tmp_path, monkeypatch):
    plan = fixture_plan(tmp_path, monkeypatch)
    path = tmp_path / 'PLAN.json'
    native.write_once(path, plan)
    monkeypatch.delenv('R125_ADMISSION_PLAN_SHA256', raising=False)
    child = Mock()
    monkeypatch.setattr(controls, 'FrozenChild', child)
    with pytest.raises(ValueError, match='admitted_control_plan_environment'):
        controls.run(path)
    child.assert_not_called()


@pytest.mark.parametrize('adapter_enabled', [False, True])
@pytest.mark.parametrize('failure', [None, 'generation', 'capture', 'already_initialized'])
def test_fresh_readout_uses_only_fixture_policy_and_truthful_arms(tmp_path, monkeypatch, adapter_enabled, failure):
    from organism_v6 import orch_r107_capability as policy
    from gpu import orch_r125_continual_readout as readout
    from gpu import orch_r107_capability_run as runner
    plan = fixture_plan(tmp_path, monkeypatch, mode=controls.MODES[int(not adapter_enabled)],
        adapter={'initialization': 'seeded_rank8'} if adapter_enabled else None)
    fake_runtime(plan, monkeypatch)
    manifest = fixture_manifest(plan)
    manifest.update(adapter_path='/fixture/adapter' if adapter_enabled else None)
    child = controls.FrozenChild(plan)
    assert child.identity == manifest['identity']
    monkeypatch.setattr(controls, 'FrozenChild', lambda actual_plan, actual_manifest: child)
    monkeypatch.setattr(controls, 'admitted_plan', lambda path: deepcopy(plan))
    monkeypatch.setattr(controls, 'verify_manifest', lambda actual_plan, path: deepcopy(manifest))
    tasks = [dict(id=f'fixture-{index}') for index in range(32)]
    monkeypatch.setattr(policy, 'tasks', lambda: deepcopy(tasks))
    monkeypatch.setattr(readout, 'SUITE_SHA256', digest(tasks))
    monkeypatch.setattr(policy, 'messages', lambda task: [{'role': 'user', 'content': task['id']}])
    captures = []

    def capture(task, arm, response, **kwargs):
        assert kwargs['checkpoint_sha256'] == (ADAPTER_HASH if adapter_enabled else native.BASE_SHA256)
        assert kwargs['lora_enabled'] is (arm == 'ON')
        captures.append((task['id'], arm))
        return dict(task_id=task['id'], arm=arm, response=response)

    monkeypatch.setattr(policy, 'capture', capture)
    reducer = Mock(return_value={'fixture_pairs': 32})
    monkeypatch.setattr(policy, 'reduce_paired', reducer)
    conditions = []

    @contextmanager
    def readonly(model, condition):
        conditions.append(condition)
        yield

    monkeypatch.setattr(runner, 'readonly_condition', readonly)
    plan_path, manifest_path = tmp_path / 'PLAN.json', tmp_path / 'MANIFEST.json'
    native.write_once(plan_path, plan)
    native.write_once(manifest_path, manifest)
    output = Path(plan['root']) / 'readouts/control_000000'
    if failure == 'already_initialized':
        child.torch.cuda.is_initialized = lambda: True
        with pytest.raises(ValueError, match='fresh_process_without_resident_CUDA'):
            controls.run_readout(plan_path, manifest_path, output)
        child.engine.generate.assert_not_called()
        assert not output.exists()
        return
    if failure in ('generation', 'capture'):
        if failure == 'generation':
            child.engine.generate.side_effect = RuntimeError('fixture readout failure')
        else:
            monkeypatch.setattr(policy, 'capture', Mock(side_effect=RuntimeError('fixture readout failure')))
        with pytest.raises(RuntimeError, match='fixture readout failure'):
            controls.run_readout(plan_path, manifest_path, output)
        assert child.engine.generate.call_count == 1
        assert not (output / 'COMPLETE.json').exists()
        assert native.read(output / 'FAILED.json')['retry_allowed'] is False
        assert native.read(output / 'AFTER.json')['unchanged'] is True
        assert native.read(output / 'CALL_000.json')['status'] == 'FAILED'
        if failure == 'capture':
            assert native.read(output / 'CALL_000.json')['response'] == {'raw': 'fixture'}
        return
    result = controls.run_readout(plan_path, manifest_path, output)
    assert result['calls'] == (64 if adapter_enabled else 32)
    assert result['actual_arms'] == (['ON', 'OFF'] if adapter_enabled else ['OFF'])
    assert result['parent_present'] is result['history_present'] is result['train_ingestion'] is False
    assert all(call.args[0][0]['content'].startswith('fixture-') for call in child.engine.generate.call_args_list)
    assert all(call.kwargs == {'max_new_tokens': 512} for call in child.engine.generate.call_args_list)
    assert bool(conditions) == adapter_enabled
    assert reducer.called == adapter_enabled
    assert (output / 'COMPLETE.json').exists() and (output / 'AFTER.json').exists()


def test_dispatch_fails_closed_records_failure_and_restores(tmp_path, monkeypatch):
    plan = fixture_plan(tmp_path, monkeypatch)
    manifest = tmp_path / 'MANIFEST.json'
    manifest.write_text('{}')
    child = SimpleNamespace(plan=plan, offload_for_readout=Mock(return_value={'fixture': True}),
                            restore_after_readout=Mock())
    process = SimpleNamespace(wait=Mock(return_value=1), poll=lambda: 1)
    launch = Mock(return_value=process)
    monkeypatch.setattr(controls.subprocess, 'Popen', launch)
    controls.fresh_readout(child, tmp_path / 'PLAN.json', manifest, 1, 2)
    child.restore_after_readout.assert_called_once_with({'fixture': True})
    failed = Path(plan['root']) / 'readouts/control_000001_FAILED.json'
    assert native.read(failed)['retry_allowed'] is False
    command = launch.call_args.args[0]
    assert '--readout-manifest' in command and '--checkpoint' not in command
    assert 'stream' not in str(command) and 'inbox' not in str(command)
    assert launch.call_args.kwargs['start_new_session'] is True
    with pytest.raises(FileExistsError):
        controls.fresh_readout(child, tmp_path / 'PLAN.json', manifest, 1, 2)


def test_dispatch_timeout_cleans_only_own_worker_and_restores(tmp_path, monkeypatch):
    plan = fixture_plan(tmp_path, monkeypatch)
    manifest = tmp_path / 'MANIFEST.json'
    manifest.write_text('{}')
    child = SimpleNamespace(plan=plan, offload_for_readout=Mock(return_value='RNG_FIXTURE'),
                            restore_after_readout=Mock())
    timeout = controls.subprocess.TimeoutExpired('fixture worker', 1)
    process = SimpleNamespace(pid=123456789, wait=Mock(side_effect=[timeout, timeout, -9]), poll=lambda: None)
    monkeypatch.setattr(controls.subprocess, 'Popen', Mock(return_value=process))
    kill = Mock()
    monkeypatch.setattr(controls.os, 'killpg', kill)
    controls.fresh_readout(child, tmp_path / 'PLAN.json', manifest, 0, 0)
    assert [call.args for call in kill.call_args_list] == [
        (process.pid, signal.SIGTERM), (process.pid, signal.SIGKILL)]
    child.restore_after_readout.assert_called_once_with('RNG_FIXTURE')


def test_public_run_is_wall_bounded_and_creates_only_frozen_artifacts(tmp_path, monkeypatch):
    plan = fixture_plan(tmp_path, monkeypatch, max_readouts=1)
    fake_runtime(plan, monkeypatch)
    child = controls.FrozenChild(plan)
    child.count_tokens = lambda messages: len(messages)
    child.generate = lambda messages, **kwargs: dict(raw='fixture', token_ids=[3, 2], terminal=True, truncated=False)
    monkeypatch.setattr(controls, 'FrozenChild', lambda actual_plan: child)
    monkeypatch.setattr(controls, 'admitted_plan', lambda path: plan)
    dispatch = Mock()
    monkeypatch.setattr(controls, 'fresh_readout', dispatch)
    path = tmp_path / 'PLAN.json'
    native.write_once(path, plan)
    previous_handler = signal.getsignal(signal.SIGALRM)
    controls.run(path)
    assert signal.getitimer(signal.ITIMER_REAL) == (0.0, 0.0)
    assert signal.getsignal(signal.SIGALRM) == previous_handler
    assert [call.args[-2:] for call in dispatch.call_args_list] == [(0, 0), (1, 2)]
    root = Path(plan['root'])
    assert sorted(entry.name for entry in root.iterdir()) == ['frozen_model', 'stream']
    assert native.read(root / 'frozen_model/MANIFEST.json')['optimizer_checkpoint'] is None
    with pytest.raises(ValueError, match='new_control_no_resume'):
        controls.run(path)


def test_callable_wall_rejects_expired_or_existing_timer(monkeypatch):
    with pytest.raises(ValueError, match='control_wall_expired'):
        with controls.bounded_wall({'hard_end_unix': time.time() - 1}):
            pytest.fail('must not enter expired wall')
    monkeypatch.setattr(controls.signal, 'getitimer', lambda timer: (10.0, 0.0))
    with pytest.raises(ValueError, match='control_requires_unshared_wall_timer'):
        with controls.bounded_wall({'hard_end_unix': time.time() + 600}):
            pytest.fail('must not replace another operator timer')
