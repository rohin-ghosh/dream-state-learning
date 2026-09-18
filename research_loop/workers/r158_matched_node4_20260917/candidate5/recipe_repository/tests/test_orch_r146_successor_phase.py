"""Synthetic CPU-only successor ownership, enrollment and immutable protocol tests."""

from copy import deepcopy
import fcntl
import io
import math
from pathlib import Path
import shutil
import sys
import time
from types import SimpleNamespace

import pytest

from gpu import orch_r146_successor_phase as phase
from test_orch_r130_checkpoint_scheduler import setup, dump, copied_checkpoint
from test_orch_r130_checkpoint_copier import destination, source


@pytest.fixture
def admitted(setup, monkeypatch):
    root = setup.root
    old = deepcopy(setup.config)
    old_path = root / 'SCHEDULER_CONFIG_V1.json'
    monkeypatch.setattr(phase, 'ROOT', root)
    monkeypatch.setattr(phase, 'ORIGINAL_CONFIG_SHA', dump(old_path, old))
    wall = old['lease_end_unix'] - 21600
    monkeypatch.setattr(phase, 'WALL', wall)
    previous = dict(predecessor_path=str(old_path), hard_end_unix=wall,
                    total_call_cap=4800, max_phase_jobs=58,
                    output_root=str(root / 'successor_phase_v2'))
    previous_path = root / 'SUCCESSOR_PHASE_V2.json'
    previous_sha = dump(previous_path, previous)
    monkeypatch.setattr(phase, 'PREDECESSOR_PHASE_SHA', previous_sha)
    frozen = root / 'source_r146_test'
    shutil.copytree(old['source_root'], frozen)
    for module in (phase, phase.scheduler, phase.enrollment):
        destination_path = frozen / 'gpu' / Path(module.__file__).name
        destination_path.write_bytes(Path(module.__file__).read_bytes())
        if module is not phase.enrollment:
            monkeypatch.setattr(module, '__file__', str(destination_path))
    monkeypatch.setattr(phase.scheduler, 'REGISTRY_SHA256', old['registry_sha256'])
    checkpoints = {role: copied_checkpoint(Path(old['copy_roots'][1]), role, steps=steps,
                    created=time.time() - age)
                   for role, steps, age in [('initial', 0, 100), ('firstsleep', 48, 60), ('latest', 100, 30)]}
    checked = {role: phase.enrollment.copied_checkpoint(item, old['copy_roots'])
               for role, item in checkpoints.items()}
    item = dict(entry=dict(lineage_id='r137_raw_synthetic', cohort='R137',
        initial_commit_sha256=checked['initial']['commit_sha256'],
        first_sleep_commit_sha256=checked['firstsleep']['commit_sha256'], programme_start_unix=time.time() - 120),
        checkpoints=checked, source_custody_content_independently_reviewed=True)
    registry = phase.enrollment.extend_registry(phase.read(old['lineages_path']), [item])
    registry_path = root / 'R146_LINEAGES.json'
    registry_sha = dump(registry_path, registry)
    candidates_path = root / 'R146_CANDIDATES.json'
    candidates_sha = dump(candidates_path, phase.enrollment.ready_candidates([item]))
    validation_path = root / 'R146_VALIDATION.json'
    validation_sha = dump(validation_path, dict(status='ACTUAL_COPIES_VALIDATED_NOT_ADMITTED',
        proposed_registry_sha256=registry_sha, candidates_sha256=candidates_sha, verified_lineages=[item]))
    inventory = phase.scheduler.sidecar.source_inventory(frozen)
    gate_path = root / 'R146_CPU.json'
    gate = dict(phase.read(old['cpu_gate_path']), helper_sha256=phase.sha(phase.__file__),
        scheduler_sha256=phase.sha(phase.scheduler.__file__), source_inventory_sha256=phase.scheduler.digest(inventory))
    gate_sha = dump(gate_path, gate)
    config = dict(schema=phase.SCHEMA, helper_sha256=phase.sha(phase.__file__), operator_root=str(root),
        predecessor_phase_path=str(previous_path), predecessor_phase_sha256=previous_sha,
        source_root=str(frozen), sources=inventory, lineages_path=str(registry_path), lineages_sha256=registry_sha,
        enrollment_validation_path=str(validation_path), enrollment_validation_sha256=validation_sha,
        candidates_path=str(candidates_path), candidates_sha256=candidates_sha, hard_end_unix=wall,
        total_call_cap=4800, max_phase_jobs=58, poll_seconds=30, segment_seconds=7200, dispatch_seconds=1800,
        created_unix=time.time(), output_root=str(root / 'successor_phase_r146_test'), run_label='test',
        cpu_gate_path=str(gate_path), cpu_gate_sha256=gate_sha,
        builder_entry_path=old['builder_entry_path'], builder_entry_sha256=old['builder_entry_sha256'])
    path = root / 'R146_PHASE.json'

    def bind():
        monkeypatch.setenv('R146_PHASE_SHA256', dump(path, config))

    bind()
    return SimpleNamespace(config=config, old=old, path=path, bind=bind, root=root,
                           previous=previous, item=item, setup=setup)


def test_phase_and_new_scheduler_validate_real_byte_bound_synthetic_inputs(admitted, monkeypatch):
    config, template, lineages = phase.validate(admitted.path)
    assert config == admitted.config and len(lineages) == 4
    changed = {'source_root', 'sources', 'lineages_path', 'lineages_sha256', 'cpu_gate_path', 'cpu_gate_sha256',
               'builder_entry_path', 'builder_entry_sha256'}
    assert {key: value for key, value in template.items() if key not in changed} == {
        key: value for key, value in admitted.old.items() if key not in changed}
    current = phase.segment_config(config, template, time.time(), 4, 0)
    current_path = admitted.root / 'SEGMENT_00.CONFIG.json'
    monkeypatch.setenv('R130_SCHEDULER_ADMISSION_SHA256', dump(current_path, current))
    _, registered, seeds = phase.scheduler.validate(current_path)
    assert len(registered) == 4 and len(seeds) == 6


@pytest.mark.parametrize('change', ['env', 'source', 'original_source', 'registry', 'candidate', 'review',
                                    'wall', 'cap', 'phase_cap', 'cadence', 'label', 'cpu', 'predecessor'])
def test_fail_closed_on_scope_or_binding_changes(admitted, monkeypatch, change):
    config = admitted.config
    if change == 'env':
        monkeypatch.setenv('R146_PHASE_SHA256', '0' * 64)
    elif change in ('source', 'original_source'):
        target = 'gpu/unrelated.py' if change == 'source' else 'gpu/orch_r130_checkpoint_benchmark.py'
        (Path(config['source_root']) / target).write_text('synthetic mutation')
    else:
        if change == 'registry':
            registry = phase.read(config['lineages_path'])
            registry['lineages'][0]['initial_commit_sha256'] = 'a' * 64
            config['lineages_sha256'] = dump(Path(config['lineages_path']), registry)
        elif change == 'candidate':
            config['candidates_sha256'] = dump(Path(config['candidates_path']), [])
        elif change == 'review':
            validation = phase.read(config['enrollment_validation_path'])
            validation['verified_lineages'][0]['source_custody_content_independently_reviewed'] = False
            config['enrollment_validation_sha256'] = dump(Path(config['enrollment_validation_path']), validation)
        elif change == 'wall':
            config['hard_end_unix'] += 1
        elif change == 'cap':
            config['total_call_cap'] = 4860
        elif change == 'phase_cap':
            config['max_phase_jobs'] = 59
        elif change == 'cadence':
            config['dispatch_seconds'] = 1
        elif change == 'label':
            config['run_label'] = '../../outside'
        elif change == 'cpu':
            config['cpu_gate_sha256'] = '0' * 64
        elif change == 'predecessor':
            config['predecessor_phase_sha256'] = '0' * 64
        admitted.bind()
    with pytest.raises(ValueError):
        phase.validate(admitted.path)


def test_snapshot_never_rewrites_original_modules():
    original = {'gpu/original.py': 'a' * 64}
    additions = {'gpu/orch_r146_checkpoint_scheduler.py': 'b' * 64,
                 'gpu/orch_r146_successor_phase.py': 'c' * 64, 'gpu/orch_r146_extra.py': 'd' * 64}
    phase.snapshot_delta(original, dict(original, **additions))
    with pytest.raises(ValueError):
        phase.snapshot_delta(original, dict(additions, **{'gpu/original.py': 'e' * 64}))
    with pytest.raises(ValueError):
        phase.snapshot_delta(original, dict(original, **additions, unrelated='e' * 64))


def test_predecessor_models_controller_and_device_locks_must_clear(admitted, monkeypatch):
    output = Path(admitted.previous['output_root'])
    dump(output / 'STARTED.json', dict(identity={'controller': True}))
    assert not phase.predecessor_clear(admitted.config)
    dump(output / 'FAILED.json', dict(status='FAILED', synthetic_intentional_handoff=True))
    monkeypatch.setattr(phase.scheduler.sidecar, 'gone', lambda identity: False)
    assert not phase.predecessor_clear(admitted.config)
    monkeypatch.setattr(phase.scheduler.sidecar, 'gone', lambda identity: True)
    with (admitted.root / 'physical1.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        assert not phase.predecessor_clear(admitted.config)
    assert phase.predecessor_clear(admitted.config)
    segment_output = admitted.root / 'scheduler_run_old_test'
    dump(output / 'SEGMENT_00.CONFIG.json', dict(output_root=str(segment_output)))
    dump(segment_output / 'dispatch_0001/job/LAUNCH.json', dict(identity={'model': True}))
    monkeypatch.setattr(phase.scheduler.sidecar, 'gone', lambda identity: not identity.get('model'))
    assert not phase.predecessor_clear(admitted.config)


def test_phase_caps_charge_old_and_new_ambiguous_reservations(admitted):
    phase_config, template, _ = phase.validate(admitted.path)
    previous_output = Path(admitted.previous['output_root'])
    new_output = Path(phase_config['output_root'])
    ledger = Path(template['ledger_root'])
    for index in range(57):
        config_path = (previous_output if index < 30 else new_output) / f'SEGMENT_{index:02d}.CONFIG.json'
        checksum = dump(config_path, dict(synthetic=True))
        dump(ledger / f'key{index}.RESERVED.json', dict(config_path=str(config_path), config_sha256=checksum))
    assert phase.remaining_jobs(phase_config, template, set(range(60))) == 1
    assert phase.remaining_jobs(phase_config, template, set(range(80))) == 0


def test_short_segment_defers_without_creating_config_or_ready(admitted):
    config, template, _ = phase.validate(admitted.path)
    now = config['hard_end_unix'] - 300
    with pytest.raises(ValueError, match='full_first_dispatch_window'):
        phase.segment_config(config, template, now, 1, 0)
    assert not list((admitted.root / 'scheduler_inbox/ready').iterdir())


def test_ready_publication_is_verified_idempotent_and_step_zero(admitted):
    _, template, lineages = phase.validate(admitted.path)
    documents = phase.enrollment.ready_candidates([admitted.item])
    result = phase.publish_ready(template, lineages, documents[0])
    assert phase.publish_ready(template, lineages, documents[0]) == result
    assert len(list((admitted.root / 'scheduler_inbox/ready').glob('*.json'))) == 1
    changed = dict(documents[1], lineage_id='unknown')
    with pytest.raises(ValueError):
        phase.publish_ready(template, lineages, changed)
    assert len(list((admitted.root / 'scheduler_inbox/ready').glob('*.json'))) == 1


def test_original_source_stage_keeps_existing_copier_protocol(destination, monkeypatch):
    monkeypatch.setattr(phase, 'ROOT', destination.root)
    config = phase.read(destination.root / 'SCHEDULER_CONFIG_V1.json')
    lineages = phase.scheduler.enrolled_lineages(phase.read(config['lineages_path']))
    path = destination.root / 'current.json'
    checksum = dump(path, config)
    status = dict(status='SEGMENT_RUNNING', active_config_path=str(path), active_config_sha256=checksum)
    monkeypatch.setattr(phase, 'validate', lambda path: ({}, config, lineages))
    monkeypatch.setattr(phase, 'phase_status', lambda phase_config: status)
    monkeypatch.setattr(phase.scheduler, 'seed_completed', lambda *args: set())
    monkeypatch.setattr(phase.scheduler, 'ledger_state', lambda *args: (set(), set(), {}))
    monkeypatch.setattr(sys, 'stdin', SimpleNamespace(buffer=io.BytesIO(destination.archive)))
    result = phase.stage(path, 'stage', destination.payload)
    assert result['status'] == 'COPIED_AND_READY_VERIFIED'
    monkeypatch.setattr(sys, 'stdin', SimpleNamespace(buffer=io.BytesIO(b'must not read twice')))
    assert phase.stage(path, 'stage', destination.payload)['status'] == 'ALREADY_STAGED'


def test_node_uses_new_scheduler_without_touching_historical_ledger(admitted, monkeypatch):
    config, template, lineages = phase.validate(admitted.path)
    clock = [time.time()]
    monkeypatch.setattr(phase.time, 'time', lambda: clock[0])
    monkeypatch.setattr(phase.time, 'sleep', lambda seconds: clock.__setitem__(0, config['hard_end_unix']))
    monkeypatch.setattr(phase, 'predecessor_clear', lambda value: True)
    monkeypatch.setattr(phase, 'validate', lambda path: (config, template, lineages))
    monkeypatch.setattr(phase.scheduler.sidecar, 'identity', lambda pid: {'synthetic_pid': pid})
    calls = []

    def spawn(command, **kwargs):
        calls.append((command, kwargs))
        segment_path = Path(command[-1])
        current = phase.read(segment_path)
        dump(Path(current['output_root']) / 'COMPLETE.json', dict(config_sha256=phase.sha(segment_path)))
        return SimpleNamespace(pid=12345, poll=lambda: 0, wait=lambda timeout: 0)

    monkeypatch.setattr(phase.subprocess, 'Popen', spawn)
    ledger = Path(template['ledger_root'])
    before = {path.name: path.read_bytes() for path in ledger.iterdir()}
    phase.node(admitted.path)
    assert len(calls) == 1
    assert calls[0][0][3] == 'gpu.orch_r146_checkpoint_scheduler'
    assert calls[0][1]['env']['CUDA_VISIBLE_DEVICES'] == ''
    assert phase.read(Path(config['output_root']) / 'ENROLLMENT.json')['status'] == 'COPIES_ENROLLED_READY_PUBLISHED'
    assert len(list((admitted.root / 'scheduler_inbox/ready').glob('*.json'))) == 3
    assert {path.name: path.read_bytes() for path in ledger.iterdir()} == before
    assert phase.read(Path(config['output_root']) / 'COMPLETE.json')['status'] == 'BOUNDED_PHASE_FINISHED'


def test_ambiguous_old_reservation_never_fetches_payload(destination, monkeypatch):
    monkeypatch.setattr(phase, 'ROOT', destination.root)
    config = phase.read(destination.root / 'SCHEDULER_CONFIG_V1.json')
    lineages = phase.scheduler.enrolled_lineages(phase.read(config['lineages_path']))
    path = destination.root / 'current.json'
    checksum = dump(path, config)
    monkeypatch.setattr(phase, 'validate', lambda path: ({}, config, lineages))
    monkeypatch.setattr(phase, 'phase_status', lambda value: dict(status='SEGMENT_RUNNING',
        active_config_path=str(path), active_config_sha256=checksum))
    monkeypatch.setattr(phase.scheduler, 'seed_completed', lambda *args: set())
    key = phase.scheduler.key_for(destination.payload['lineage_id'], destination.payload['commit_sha256'])
    monkeypatch.setattr(phase.scheduler, 'ledger_state', lambda *args: ({key}, set(), {}))
    monkeypatch.setattr(sys, 'stdin', SimpleNamespace(buffer=None))
    assert phase.stage(path, 'stage', destination.payload)['status'] == 'ALREADY_RESERVED_NO_REPLAY'
