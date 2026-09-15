from copy import deepcopy
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time
from types import SimpleNamespace

import pytest

from gpu import orch_r111_route_final as final


def put(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value))


@pytest.fixture
def prepared(tmp_path, monkeypatch):
    original = tmp_path / 'original'
    runtime = tmp_path / 'runtime'
    executable = runtime / 'gpu/orch_r111_route_pair_shared.py'
    executable.parent.mkdir(parents=True)
    executable.write_text('fixture_frozen_source = True\n')
    selector = tmp_path / 'selector.py'
    selector.write_text('def validate_selection(root):\n    raise ValueError("fixture_requires_selection")\n')
    plan = dict(root=str(original), physical=0, uuid=final.OWNED['F1'][1],
        schema='R115V4_F1_MATCHED_FRESH_BASE_ROUTE', final_sha256='unread_sealed_hash',
        source_files={str(executable): final.sha(executable)},
        decoder=dict(do_sample=False, num_beams=1, readout_max_new_tokens=2048),
        bounds=dict(native_calls=32768, parent_calls=16384, cycles=512,
                    lease_end_unix=final.END+21600+100, hard_end_unix=final.END+100),
        shared_learner=dict(branch='F1'), parent_prompt_sha256='fixed_prompt')
    put(original / 'PLAN.json', plan)
    put(original / 'COHORT.json', dict(train=['original_training_only']))
    (original / 'RESERVATIONS.jsonl').write_text('{"kind":"NATIVE","number":123}\n')
    control = tmp_path / 'control' / 'CONTROL.json'
    common = tmp_path / 'common'
    put(common / 'CONFIG.json', dict(owner='F1'))
    put(control, dict(routes={'F1': dict(root=str(original), plan=final.ref(original/'PLAN.json'),
        source_root=str(runtime))}, common=str(common),
        immutable={'CONFIG.json': final.ref(common/'CONFIG.json')}))
    cpu = tmp_path/'CPU.json'
    put(cpu, dict(exitcode=0, CUDA_VISIBLE_DEVICES='', model_calls=0, provider_calls=0,
        real_FINAL_reads=0, source_sha256=final.sha(final.__file__), selector_sha256=final.sha(selector)))
    monkeypatch.setattr(final.time, 'time', lambda: final.START-100)
    reference = final.prepare('F1', original, tmp_path/'evaluation', final.ref(control),
                              final.ref(selector), final.ref(cpu))
    return final.read(reference['path']), reference


def test_prepare_never_reads_or_copies_FINAL_and_preserves_old_ledger(prepared):
    config, reference = prepared
    root = Path(config['root'])
    assert not (root/'SEALED_FINAL.json').exists()
    assert not (Path(config['original_root'])/'SEALED_FINAL.json').exists()
    assert (Path(config['original_root'])/'RESERVATIONS.jsonl').read_text() == '{"kind":"NATIVE","number":123}\n'
    plan = final.read(root/'PLAN.json')
    assert plan['bounds']['native_calls'] == 48
    assert plan['bounds']['parent_calls'] == plan['bounds']['cycles'] == 0
    assert 'shared_learner' not in plan
    assert not (root/'RESERVATIONS.jsonl').exists()
    assert final.validate_config(reference) == config


@pytest.mark.parametrize('now', [final.START-1, final.END, final.END+1])
def test_never_runs_before_cut_or_past_bound(prepared, now):
    with pytest.raises(ValueError, match='not_in_FINAL_window'):
        final.window(prepared[0], now)


def test_lease_margin_is_earlier_cut_and_cannot_be_extended(prepared):
    config, reference = prepared
    config = deepcopy(config)
    config['end_unix'] = final.START+300
    final.window(config, final.START+299)
    with pytest.raises(ValueError):
        final.window(config, final.START+300)
    config['end_unix'] = final.END+1
    with pytest.raises(ValueError, match='fixed_evaluation_window'):
        final.window(config, final.START+1)


def test_no_early_materialization_or_morning_inspection(prepared):
    config, unused = prepared
    with pytest.raises(ValueError, match='not_in_FINAL_window'):
        final.materialize(config, final.START-1)
    with pytest.raises(ValueError, match='no_early_FINAL_inspection'):
        final.completed_morning(config['original_root'], final.START-1)


def test_completed_morning_skipped_but_sleep_zero_is_not_morning(prepared):
    config, unused = prepared
    original = Path(config['original_root'])
    put(original/'sealed_final_readouts/readout_0000/COMPLETE.json',
        dict(scope='FINAL', finished_unix=final.START+1))
    assert final.completed_morning(original, final.START+2) is None
    morning = original/'sealed_final_readouts/readout_0007/COMPLETE.json'
    put(morning, dict(scope='FINAL', finished_unix=final.START+1))
    assert final.completed_morning(original, final.START+2) == final.ref(morning)


def test_materialize_exact_original_sealed_eight_at_cut_only(prepared):
    config, unused = prepared
    original = Path(config['original_root'])
    put(original/'SEALED_FINAL.json', dict(tasks=[dict(id=f'FINAL-{index}') for index in range(8)], store={}))
    config['sealed_final'] = final.ref(original/'SEALED_FINAL.json')
    final.materialize(config, final.START)
    root = Path(config['root'])
    assert (root/'SEALED_FINAL.json').resolve() == original/'SEALED_FINAL.json'
    assert final.read(root/'FINAL_INVENTORY_BINDING.json')['inspected_unix'] == final.START
    assert final.read(root/'ROHIN_GO.json')['provider_calls_authorized'] == 0
    assert not (root/'parent_queue').exists()


def test_wrong_sealed_count_and_hash_fail_without_native_calls(prepared):
    config, unused = prepared
    original = Path(config['original_root'])
    put(original/'SEALED_FINAL.json', dict(tasks=[dict(id='only_one')], store={}))
    config['sealed_final'] = final.ref(original/'SEALED_FINAL.json')
    with pytest.raises(ValueError, match='exact_sealed_eight'):
        final.materialize(config, final.START)
    config['sealed_final']['sha256'] = 'wrong'
    with pytest.raises(ValueError, match='original_sealed_inventory'):
        final.materialize(config, final.START)
    assert not (Path(config['root'])/'RESERVATIONS.jsonl').exists()


def test_command_can_only_use_fresh_FINAL_not_training_or_baseline(prepared, monkeypatch):
    config, unused = prepared
    command = final.command(config, dict(path='/selected/checkpoint.json'))
    assert command[-2:] == ['--scope', 'final']
    assert command[command.index('--sleep-index')+1] == '1'
    assert 'readout' in command and 'run' not in command and 'supervise' not in command
    monkeypatch.setenv('PARENT_BROKER', 'must_not_inherit')
    monkeypatch.setenv('ANTHROPIC_API_KEY', 'fixture_not_real')
    monkeypatch.setenv('OPENAI_API_KEY', 'fixture_not_real')
    environment = final.environment(config)
    assert not any(key.startswith(('PARENT_', 'ANTHROPIC_', 'OPENAI_')) for key in environment)
    assert environment['CUDA_VISIBLE_DEVICES'] == config['uuid']
    assert environment['PYTHONPATH'] == config['runtime_source']


def test_no_dispatch_without_actual_cutoff_completion(prepared, monkeypatch):
    config, unused = prepared
    control = final.bound(config['cutoff'])
    control.update(source=dict(path='unused'), directory=str(Path(config['root'])/'absent_control'))
    monkeypatch.setattr(final, 'bound', lambda reference: control)
    monkeypatch.setattr(final, 'module_from', lambda *args: SimpleNamespace(validate=lambda control: None))
    with pytest.raises(ValueError, match='actual_cutoff_completion_required'):
        final.release_evidence(config)
    assert not (Path(config['root'])/'ATTEMPT.json').exists()


@pytest.mark.parametrize('live,status', [(True, 'RELEASED'), (False, 'EXIT_UNCONFIRMED')])
def test_release_never_accepts_live_or_unconfirmed_predecessors(prepared, monkeypatch, live, status):
    config, unused = prepared
    directory = Path(config['root'])/'cutoff'
    put(directory/'COMPLETED.json', {})
    put(directory/'F1/DISPOSITION.json', dict(status=status))
    control = dict(source={}, directory=str(directory), routes={'F1': dict(supervisor={}, initial_actor={})})
    monkeypatch.setattr(final, 'bound', lambda reference: control)
    monkeypatch.setattr(final, 'module_from', lambda *args: SimpleNamespace(
        validate=lambda control: None, alive=lambda identity: live))
    with pytest.raises(ValueError, match='owned_predecessors_absent|confirmed_route_release'):
        final.release_evidence(config)


def test_real_pidfd_timeout_kills_only_new_evaluation_child():
    child = subprocess.Popen([sys.executable, '-c',
        'import signal,time; signal.signal(signal.SIGTERM,signal.SIG_IGN); print("ready",flush=True); time.sleep(60)'],
        stdout=subprocess.PIPE, text=True)
    sentinel = subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(60)'])
    assert child.stdout.readline().strip() == 'ready'
    descriptor = os.pidfd_open(child.pid)
    try:
        code, signals = final.finish_child(child, descriptor, time.time()+.15, grace_seconds=.1)
        assert code == -signal.SIGKILL
        assert signals == ['SIGTERM', 'SIGKILL_AT_BOUND']
        assert sentinel.poll() is None
    finally:
        os.close(descriptor)
        if child.poll() is None:
            child.kill()
        child.wait()
        sentinel.terminate()
        sentinel.wait()


def test_real_completed_evaluation_child_is_not_signalled():
    child = subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(.05)'])
    descriptor = os.pidfd_open(child.pid)
    try:
        code, signals = final.finish_child(child, descriptor, time.time()+2, grace_seconds=.1)
        assert code == 0 and signals == []
    finally:
        os.close(descriptor)
        child.wait()


def test_canonical_selection_consumer_never_creates_marker_or_STATE(prepared, monkeypatch):
    config, unused = prepared
    calls = []
    common = final.read(config['common_config']['path'])
    common['initial_checkpoint'] = dict(path='/canonical/checkpoint.json')
    put(Path(config['common_config']['path']), common)
    config['common_config'] = final.ref(config['common_config']['path'])
    config['common_lineage'] = {name: config['common_config']
        for name in ('CONFIG.json', 'INITIALIZED.json', 'ADOPTION.json')}
    selection = dict(schema='R118_FINAL_SELECTION_V1', shared_root=config['common'],
        scheduled_unix=final.START, selected_unix=final.START, evaluation_deadline_unix=final.END,
        checkpoint=common['initial_checkpoint'], lineage_sha256={'CONFIG.json': config['common_config']['sha256']},
        branches=['F1'], generation=0, committed_sleep=None)
    put(Path(config['selection_path']), selection)
    before = Path(config['selection_path']).read_bytes()
    monkeypatch.setattr(final, 'module_from', lambda *args: SimpleNamespace(SCHEMA=selection['schema'],
        validate_selection=lambda root, **kwargs: calls.append(root) or selection))
    assert final.selection_checkpoint(config, final.START) == selection
    assert calls == [Path(config['common'])]
    assert Path(config['selection_path']).read_bytes() == before
    assert not (Path(config['common'])/'STATE.json').exists()


def test_existing_attempt_cannot_be_replayed(prepared, monkeypatch):
    config, unused = prepared
    root = Path(config['root'])
    final.write(root/'ATTEMPT.json', dict(preserve=True))
    monkeypatch.setattr(final.time, 'time', lambda: final.START+1)
    monkeypatch.setattr(final, 'release_evidence', lambda config: {})
    monkeypatch.setattr(final, 'selection_checkpoint', lambda config, now: dict(checkpoint={}))
    with pytest.raises(ValueError, match='prior_attempt_preserved_no_replay'):
        final.dispatch(config)
    assert final.read(root/'ATTEMPT.json') == dict(preserve=True)
    assert not (root/'SEALED_FINAL.json').exists()


def test_actual_existing_FINAL_readout_uses_separate_48_call_ledger(tmp_path, monkeypatch):
    from gpu import orch_r111_route_pair_shared as route

    root = tmp_path/'evaluation'
    output = root/'sealed_final_readouts/readout_0001'
    output.mkdir(parents=True)
    plan = dict(bounds=dict(hard_end_unix=final.END, native_calls=48, parent_calls=0))
    put(root/'PLAN.json', plan)
    put(root/'SEALED_FINAL.json', dict(tasks=[dict(id=f'FINAL-{index}', world={}, task={})
        for index in range(8)], store={}))
    checkpoint = tmp_path/'CHECKPOINT.json'
    put(checkpoint, dict(adapter={}, source_process=[1, 2]))
    unchanged = []
    monkeypatch.setattr(route.time, 'time', lambda: final.START+1)
    monkeypatch.setattr(route, 'verify', lambda root, gpu: plan)
    monkeypatch.setattr(route, 'load_engine', lambda *args, **kwargs: SimpleNamespace(
        engine=object(), process=[3, 4], verify_unchanged=lambda: unchanged.append(True)))
    batches = []
    def generate(engine, messages, cap):
        batches.append((len(messages), cap))
        return [dict(raw='fixture', token_ids=[7, 9], terminal=True, input_truncated=False,
                     full_prompt_prefix_verified=True) for message in messages]
    def episode(world, task, generate_call, store, system):
        for turn in range(6):
            try:
                generate_call([dict(role='user', content='fixture observation')])
            except LookupError:
                break
        return dict(fixture=True)
    monkeypatch.setattr(route, 'generate_batch', generate)
    monkeypatch.setattr(route, 'episode', episode)
    route.readout(root, 1, checkpoint, scope='final')
    rows = [json.loads(line) for line in (root/'RESERVATIONS.jsonl').read_text().splitlines()]
    assert len(rows) == 48 and all(row['kind'] == 'NATIVE' for row in rows)
    assert len(batches) == 6 and batches[0] == (8, 2048)
    assert final.read(output/'COMPLETE.json')['held_tasks'] == 8
    assert unchanged == [True]
    assert not (root/'ROWS.json').exists() and not (root/'parent_queue').exists()
    with pytest.raises(ValueError, match='declared_lifetime_call_bound'):
        route.reserve(root, 'NATIVE', dict(phase='readout'))
    with pytest.raises(ValueError, match='declared_lifetime_call_bound'):
        route.reserve(root, 'PARENT', {})


@pytest.fixture
def canonical(prepared):
    from gpu import orch_r118_final_selection as selector

    config, unused = prepared
    common = Path(config['common'])
    owner = Path(config['original_root'])
    optimizer = owner/'fixture_optimizer.pt'
    optimizer.write_bytes(b'fixture_saved_optimizer')
    checkpoint = owner/'fixture_checkpoint.json'
    put(checkpoint, dict(complete=True, optimizer_rng_sha256=final.sha(optimizer)))
    reference = dict(path=str(checkpoint), path_sha256=final.sha(checkpoint),
                     optimizer_path=str(optimizer), optimizer_path_sha256=final.sha(optimizer))
    metrics = dict(optimizer_steps=1125, child_token_exposures=68231, anchor_token_exposures=20351)
    put(common/'CONFIG.json', dict(owner='F1', branches={branch: dict(root=str(owner))
        for branch in selector.BRANCHES}, initial_checkpoint=reference, pretransition_metrics=metrics))
    put(common/'INITIALIZED.json', dict(fixture=True))
    put(common/'ADOPTION.json', dict(fixture=True))
    config['common_lineage'] = {name: final.ref(common/name)
        for name in ('CONFIG.json', 'INITIALIZED.json', 'ADOPTION.json')}
    config['common_config'] = config['common_lineage']['CONFIG.json']
    config['selector_source'] = final.ref(selector.__file__)
    put(common/'STATE.json', dict(generation=0, checkpoint=reference,
        config_sha256=config['common_config']['sha256'], **metrics,
        **{'shared_'+name: 0 for name in metrics}))
    selected = selector.select(common, config_sha256=config['common_lineage']['CONFIG.json']['sha256'],
        initialized_sha256=config['common_lineage']['INITIALIZED.json']['sha256'],
        adoption_sha256=config['common_lineage']['ADOPTION.json']['sha256'], clock=lambda: final.START+1)
    return config, selected


def test_actual_Main_selector_contract_consumed_read_only(canonical):
    config, selected = canonical
    root = Path(config['common'])
    before = {name: (root/name).read_bytes() for name in ('STATE.json', 'FINAL_SELECTION.json')}
    assert final.selection_checkpoint(config, final.START+2) == selected
    assert all((root/name).read_bytes() == value for name, value in before.items())
    assert not (root/'SEALED_FINAL.json').exists()


def test_missing_selection_never_falls_back_to_STATE_or_partial_sleep(canonical):
    config, selected = canonical
    Path(config['selection_path']).unlink()
    root = Path(config['common'])
    put(root/'generation_000000/sleep/START.json', dict(partial=True))
    with pytest.raises(FileNotFoundError):
        final.selection_checkpoint(config, final.START+2)
    assert not Path(config['selection_path']).exists()


@pytest.mark.parametrize('tamper', ['optimizer', 'lineage', 'future_selection', 'uncommitted'])
def test_canonical_consumer_rejects_tampering_or_uncommitted_checkpoint(canonical, tamper):
    config, selected = canonical
    if tamper == 'optimizer':
        Path(selected['checkpoint']['optimizer_path']).write_bytes(b'corrupt')
    elif tamper == 'lineage':
        selected['lineage_sha256']['CONFIG.json'] = 'wrong'
    elif tamper == 'future_selection':
        selected['selected_unix'] = final.START+100
    else:
        selected['generation'] = 1
        selected['committed_sleep'] = dict(path=str(Path(config['common'])/'not_a_commit.json'), sha256='absent')
    put(Path(config['selection_path']), selected)
    with pytest.raises(ValueError):
        final.selection_checkpoint(config, final.START+2)


def test_no_reselection_after_canonical_freeze(canonical):
    config, selected = canonical
    put(Path(config['common'])/'STATE.json', dict(unexpected_later_state=True))
    assert final.selection_checkpoint(config, final.START+2) == selected


def test_CPU_scheduler_refuses_GPU_visibility(prepared, monkeypatch):
    monkeypatch.setenv('CUDA_VISIBLE_DEVICES', 'GPU-not-CPU')
    with pytest.raises(ValueError, match='CPU_only_scheduler'):
        final.wait(prepared[1])


def test_changed_CPU_receipt_blocks_scheduler(prepared):
    config, reference = prepared
    put(Path(config['cpu']['path']), dict(exitcode=1))
    with pytest.raises(ValueError, match='immutable_reference'):
        final.validate_config(reference)
