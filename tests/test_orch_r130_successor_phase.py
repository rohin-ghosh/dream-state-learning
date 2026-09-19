"""CPU-only phase ownership, historical budgets and immutable copy tests."""

from copy import deepcopy
import fcntl
import io
import json
import math
from pathlib import Path
import shlex
import sys
import time
from types import SimpleNamespace

import pytest

from gpu import orch_r130_successor_phase as phase
from test_orch_r130_checkpoint_scheduler import setup, dump
from test_orch_r130_checkpoint_copier import source, destination, admitted_config


@pytest.fixture
def admitted(setup, monkeypatch):
    old = setup.config
    predecessor = setup.root / 'SCHEDULER_CONFIG_V1.json'
    checksum = dump(predecessor, old)
    monkeypatch.setattr(phase, 'ROOT', setup.root)
    monkeypatch.setattr(phase, 'PREDECESSOR_SHA', checksum)
    wall = old['lease_end_unix'] - 21600
    monkeypatch.setattr(phase, 'WALL', wall)
    gate_path = setup.root / 'phase_gate.json'
    old_gate = phase.read(old['cpu_gate_path'])
    gate = dict(status='PASS', test_exit_code=0, helper_sha256=phase.sha(phase.__file__),
        test_log_path=old_gate['test_log_path'], test_log_sha256=old_gate['test_log_sha256'])
    gate_sha = dump(gate_path, gate)
    start = old['hard_end_unix'] + 125
    config = dict(schema=phase.SCHEMA, helper_sha256=phase.sha(phase.__file__), operator_root=str(setup.root),
        predecessor_path=str(predecessor), source_root=old['source_root'], hard_end_unix=wall,
        created_unix=time.time(), start_unix=start, first_dispatch_unix=(math.floor(start / 1800) + 1) * 1800,
        poll_seconds=30, segment_seconds=7200, dispatch_seconds=1800, max_phase_jobs=58, total_call_cap=4800,
        output_root=str(setup.root / 'successor_phase_v2'), builder_entry_path=old['builder_entry_path'],
        builder_entry_sha256=old['builder_entry_sha256'], cpu_gate_path=str(gate_path), cpu_gate_sha256=gate_sha)
    path = setup.root / 'PHASE.json'
    def bind():
        monkeypatch.setenv('R130_PHASE_SHA256', dump(path, config))
    bind()
    return SimpleNamespace(config=config, old=old, path=path, bind=bind, setup=setup)


def test_phase_binding_positive(admitted):
    config, old, lineages = phase.validate(admitted.path)
    assert config == admitted.config and old == admitted.old
    assert set(lineages) == {'legacy', 'pilot', 'kernel'}


@pytest.mark.parametrize('change', ['env', 'wall', 'start', 'cap', 'cadence', 'source', 'gate'])
def test_reject_phase_scope_and_provenance(admitted, monkeypatch, change):
    if change == 'env':
        monkeypatch.setenv('R130_PHASE_SHA256', '0' * 64)
    elif change == 'wall':
        admitted.config['hard_end_unix'] += 1
        admitted.bind()
    elif change == 'start':
        admitted.config['start_unix'] = admitted.old['hard_end_unix']
        admitted.bind()
    elif change == 'cap':
        admitted.config['total_call_cap'] = 4801
        admitted.bind()
    elif change == 'cadence':
        admitted.config['dispatch_seconds'] = 1
        admitted.bind()
    elif change == 'source':
        (Path(admitted.old['source_root']) / 'unexpected.py').write_text('synthetic')
    elif change == 'gate':
        Path(admitted.config['cpu_gate_path']).write_text('{}')
    with pytest.raises(ValueError):
        phase.validate(admitted.path)


def test_budget_counts_historical_and_ambiguous_reservations():
    assert phase.budget(4800, set(range(78)), 0, 58) == 2
    assert phase.budget(4800, set(range(80)), 0, 58) == 0
    assert phase.budget(4800, set(range(6)), 57, 58) == 1
    assert phase.budget(4800, set(range(6)), 0, 58) == 8


def test_predecessor_must_finish_exit_and_release_locks(admitted, monkeypatch):
    output = Path(admitted.old['output_root'])
    output.mkdir()
    dump(output / 'STARTED.json', dict(identity={'synthetic': True}))
    monkeypatch.setattr(phase.scheduler.sidecar, 'gone', lambda identity: True)
    assert not phase.predecessor_clear(admitted.old)
    dump(output / 'COMPLETE.json', dict(config_sha256=phase.PREDECESSOR_SHA))
    monkeypatch.setattr(phase.scheduler.sidecar, 'gone', lambda identity: False)
    assert not phase.predecessor_clear(admitted.old)
    monkeypatch.setattr(phase.scheduler.sidecar, 'gone', lambda identity: True)
    with (admitted.setup.root / 'physical1.lock').open('a') as held:
        fcntl.flock(held, fcntl.LOCK_EX | fcntl.LOCK_NB)
        assert not phase.predecessor_clear(admitted.old)
    assert phase.predecessor_clear(admitted.old)


def test_predecessor_runner_still_live_rejects(admitted, monkeypatch):
    output = Path(admitted.old['output_root'])
    dump(output / 'STARTED.json', dict(identity={'owner': True}))
    dump(output / 'COMPLETE.json', dict(config_sha256=phase.PREDECESSOR_SHA))
    dump(output / 'dispatch_0001/job/LAUNCH.json', dict(identity={'owner': False}))
    monkeypatch.setattr(phase.scheduler.sidecar, 'gone', lambda identity: identity['owner'])
    with pytest.raises(ValueError, match='runner_identity'):
        phase.predecessor_clear(admitted.old)


def test_segment_preserves_shared_ledger_frozen_sources_and_decoder(admitted):
    original = deepcopy(admitted.old)
    now = admitted.config['start_unix']
    config = phase.segment_config(admitted.config, original, now, 2, 0)
    for key in ('ledger_root', 'inbox_root', 'registry_path', 'registry_sha256', 'lineages_sha256',
            'source_root', 'sources', 'template_plan_sha256', 'corpus_sha256', 'physical_devices', 'release_receipts'):
        assert config[key] == original[key]
    assert config['hard_end_unix'] <= now + 7200
    assert config['max_jobs'] == 2
    assert original == admitted.old
    assert phase.segment_command(original, 'synthetic.json')[-3:] == ['run', '--config', 'synthetic.json']


def test_copy_cadence_and_exact_wall():
    assert phase.next_copy(13 * 3600 + 5 * 60, 20 * 3600) == 13 * 3600 + 27 * 60
    assert phase.next_copy(20 * 3600 - 100, 20 * 3600) is None
    assert time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime(1789617240)) == '2026-09-17T03:54:00Z'


def test_successor_stage_uses_native_copy_readonly_and_dedup(destination, source, monkeypatch):
    monkeypatch.setattr(phase, 'ROOT', destination.root)
    old = phase.read(destination.root / 'SCHEDULER_CONFIG_V1.json')
    lineages = phase.scheduler.enrolled_lineages(phase.read(old['lineages_path']))
    config_path = destination.root / 'active.json'
    config_sha = dump(config_path, old)
    status = dict(status='SEGMENT_RUNNING', active_config_path=str(config_path), active_config_sha256=config_sha)
    monkeypatch.setattr(phase, 'validate', lambda path: ({}, old, lineages))
    monkeypatch.setattr(phase, 'phase_status', lambda config: status)
    monkeypatch.setattr(phase.scheduler, 'seed_completed', lambda *args: set())
    monkeypatch.setattr(phase.scheduler, 'ledger_state', lambda *args: (set(), set(), {}))
    monkeypatch.setattr(sys, 'stdin', SimpleNamespace(buffer=io.BytesIO(destination.archive)))
    receipt = phase.stage(config_path, 'stage', destination.payload)
    assert receipt['status'] == 'COPIED_AND_READY_VERIFIED'
    monkeypatch.setattr(sys, 'stdin', SimpleNamespace(buffer=io.BytesIO(b'must not read twice')))
    assert phase.stage(config_path, 'stage', destination.payload)['status'] == 'ALREADY_STAGED'
    assert len(list((destination.root / 'scheduler_inbox/ready').glob('*.json'))) == 1


def test_successor_stage_refuses_ambiguous_historical_replay(destination, monkeypatch):
    old = phase.read(destination.root / 'SCHEDULER_CONFIG_V1.json')
    lineages = phase.scheduler.enrolled_lineages(phase.read(old['lineages_path']))
    config_path = destination.root / 'active.json'
    config_sha = dump(config_path, old)
    monkeypatch.setattr(phase, 'validate', lambda path: ({}, old, lineages))
    monkeypatch.setattr(phase, 'phase_status', lambda config: dict(status='SEGMENT_RUNNING',
        active_config_path=str(config_path), active_config_sha256=config_sha))
    monkeypatch.setattr(phase.scheduler, 'seed_completed', lambda *args: set())
    key = phase.scheduler.key_for(destination.payload['lineage_id'], destination.payload['commit_sha256'])
    monkeypatch.setattr(phase.scheduler, 'ledger_state', lambda *args: ({key}, set(), {}))
    monkeypatch.setattr(sys, 'stdin', SimpleNamespace(buffer=io.BytesIO(b'never consume')))
    assert phase.stage(config_path, 'stage', destination.payload)['status'] == 'ALREADY_RESERVED_NO_REPLAY'
    assert not list((destination.root / 'scheduler_inbox/ready').glob('*.json'))


@pytest.fixture
def admitted_copy(admitted_config, tmp_path, monkeypatch):
    from gpu import orch_r130_checkpoint_copier as copier
    old = admitted_config.config
    old_sha = phase.sha(admitted_config.path)
    monkeypatch.setattr(phase, 'COPY_PREDECESSOR_SHA', old_sha)
    gate_path = tmp_path / 'successor_gate.json'
    gate = phase.read(old['cpu_gate_path'])
    gate['helper_sha256'] = phase.sha(phase.__file__)
    gate_sha = dump(gate_path, gate)
    evidence_path = tmp_path / 'leases.json'
    evidence = dict(sources=[dict(wrapper_path=old['destination_wrapper'],
        wrapper_sha256=old['destination_wrapper_sha256'], conservative_read_end_unix=time.time() + 86400)])
    evidence_sha = dump(evidence_path, evidence)
    first = time.time() + 1000
    config = dict(helper_sha256=phase.sha(phase.__file__), copier_sha256=phase.sha(copier.__file__),
        predecessor_copier_path=str(admitted_config.path), predecessor_copier_sha256=old_sha,
        destination_wrapper=old['destination_wrapper'], hard_end_unix=min(phase.WALL, time.time() + 3600),
        first_copy_unix=first, first_dispatch_unix=first + 180, max_cycles=30,
        remote_phase_path=str(phase.ROOT / 'SUCCESSOR_PHASE_V2.json'), source_root=str(phase.ROOT / 'source6_scheduler'),
        remote_helper_path=str(phase.ROOT / 'successor_tools_v2/gpu/orch_r130_successor_phase.py'),
        local_dependencies={str(Path(phase.__file__)): phase.sha(phase.__file__)},
        source_lease_evidence_path=str(evidence_path), source_lease_evidence_sha256=evidence_sha,
        builder_entry_path=old['builder_entry_path'], builder_entry_sha256=old['builder_entry_sha256'],
        cpu_gate_path=str(gate_path), cpu_gate_sha256=gate_sha)
    path = tmp_path / 'successor_copy.json'
    def bind():
        monkeypatch.setenv('R130_PHASE_COPY_SHA256', dump(path, config))
    bind()
    return SimpleNamespace(config=config, path=path, bind=bind)


def test_copy_phase_preflight_and_immutable_sources(admitted_copy):
    config, old, _ = phase.local_validate(admitted_copy.path)
    assert config == admitted_copy.config
    assert len(old['sources']) == 3


@pytest.mark.parametrize('field,value', [('remote_phase_path', '/another/config'),
    ('source_root', '/another/source'), ('max_cycles', 1000), ('hard_end_unix', 9999999999),
    ('helper_sha256', '0' * 64), ('predecessor_copier_sha256', '0' * 64)])
def test_copy_phase_rejects_scope_drift(admitted_copy, field, value):
    admitted_copy.config[field] = value
    admitted_copy.bind()
    with pytest.raises(ValueError):
        phase.local_validate(admitted_copy.path)
