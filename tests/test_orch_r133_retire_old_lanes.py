import hashlib
import json
import os
from pathlib import Path
import signal
import subprocess
import sys

import pytest

from gpu import orch_r133_retire_old_lanes as retirement


def put(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value))


@pytest.fixture
def boundary(tmp_path):
    put(tmp_path / 'PROGRESS.json', dict(inherited_calls=10, calls=12, finished_unix=30))
    for number in (11, 12):
        intent = dict(cumulative_call=number, task_id='task', started_unix=number)
        put(tmp_path / f'INTENT_{number:06d}.json', intent)
        put(tmp_path / f'CALL_{number:06d}.json', dict(intent, response={}, outcome={}, finished_unix=20))
    return tmp_path


def test_exact_saved_frontier(boundary):
    assert retirement.frontier(boundary)['outstanding_intents'] == 0


@pytest.mark.parametrize('completed', [False, True])
def test_stale_checkpoint_never_discards_later_work(boundary, completed):
    put(boundary / 'INTENT_000013.json', dict(cumulative_call=13))
    if completed:
        put(boundary / 'CALL_000013.json', dict(cumulative_call=13))
    with pytest.raises(ValueError, match='later_or_missing_work'):
        retirement.frontier(boundary)


def test_missing_prior_response_rejected(boundary):
    (boundary / 'CALL_000011.json').unlink()
    with pytest.raises(ValueError, match='later_or_missing_work'):
        retirement.frontier(boundary)


def test_partial_boundary_is_not_complete(boundary):
    (boundary / 'PROGRESS.json').write_text('{')
    with pytest.raises(json.JSONDecodeError):
        retirement.frontier(boundary)


def test_failure_preserved_not_retired(boundary):
    put(boundary / 'FAILED_000012.json', {})
    with pytest.raises(ValueError, match='failed_generation'):
        retirement.frontier(boundary)


def test_intent_response_mismatch_rejected(boundary):
    value = retirement.read(boundary / 'CALL_000012.json')
    value['task_id'] = 'different'
    put(boundary / 'CALL_000012.json', value)
    with pytest.raises(ValueError, match='intent_response_join'):
        retirement.frontier(boundary)


def test_result_after_boundary_rejected(boundary):
    value = retirement.read(boundary / 'CALL_000012.json')
    value['finished_unix'] = 31
    put(boundary / 'CALL_000012.json', value)
    with pytest.raises(ValueError, match='result_after_saved_cursor'):
        retirement.frontier(boundary)


def test_immutable_receipt_never_overwritten(tmp_path):
    path = tmp_path / 'receipt.json'
    retirement.immutable(path, dict(missing_RNG=True))
    with pytest.raises(FileExistsError):
        retirement.immutable(path, dict(missing_RNG=False))
    assert retirement.read(path)['missing_RNG'] is True
    assert path.stat().st_mode & 0o222 == 0


def test_archive_copies_and_verifies_exact_bytes(tmp_path):
    root = tmp_path / 'state'
    root.mkdir()
    (root / 'optimizer.pt').write_bytes(b'actual AdamW')
    (root / 'rank0.pt').write_bytes(b'actual RNG')
    result = retirement.archive([root], tmp_path / 'snapshot.tar')
    assert len(result['files']) == 2
    assert result['files'][str(root / 'optimizer.pt')]['sha256'] == hashlib.sha256(b'actual AdamW').hexdigest()


def test_archive_rejects_unresolved_state_symlink(tmp_path):
    root = tmp_path / 'state'
    root.mkdir()
    (root / 'optimizer.pt').symlink_to('/does/not/exist')
    with pytest.raises(ValueError, match='unresolved_archive_symlink'):
        retirement.archive([root], tmp_path / 'snapshot.tar')


@pytest.mark.parametrize('node,physical', [('ovx2', 2), ('a40r', 0), ('a40r', 1), ('a40r', 2),
                                         ('a100', 0), ('ovx3', 2), ('ovx3', 6)])
def test_unsupported_and_protected_lanes_never_signalled(node, physical, monkeypatch):
    monkeypatch.setattr(retirement.signal, 'pidfd_send_signal', lambda *args: pytest.fail('signal attempted'))
    with pytest.raises(ValueError, match='unsupported_lane'):
        retirement.retire_remote(dict(node=node, physical=physical))


def test_missing_gate_never_inspects_or_signals(monkeypatch):
    monkeypatch.setattr(retirement, 'provenance', lambda: pytest.fail('gate bypassed'))
    with pytest.raises(ValueError, match='dated_CPU_Builder_gate'):
        retirement.retire_remote(dict(node='ovx2', physical=0, gate=dict(cpu_passed=False)))


def test_PID_reuse_not_same_actor(monkeypatch):
    old = dict(pid=123, uid=os.getuid(), start_ticks='1', boot_id='boot')
    monkeypatch.setattr(retirement, 'identity', lambda pid: dict(old, start_ticks='2'))
    assert not retirement.alive(old)
    with pytest.raises(ValueError, match='identity_drift'):
        retirement.same(old)


def test_argv_change_is_not_exit_proof(monkeypatch):
    old = dict(pid=123, uid=os.getuid(), start_ticks='1', boot_id='boot', argv=['original'])
    monkeypatch.setattr(retirement, 'identity', lambda pid: dict(old, argv=['different']))
    assert retirement.alive(old)
    with pytest.raises(ValueError, match='identity_drift'):
        retirement.same(old)


def test_transport_rejects_raw_host_and_other_node_actuator():
    with pytest.raises(ValueError, match='wrappers_only'):
        retirement.remote('raw-destination', 'inspect')
    with pytest.raises(ValueError, match='no_other_live_actuator'):
        retirement.remote('a40r', 'retire')


def test_pidfd_pause_and_resume_owned_CPU_process():
    child = subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(60)'],
                             env=dict(os.environ, CUDA_VISIBLE_DEVICES=''))
    descriptor = os.pidfd_open(child.pid)
    try:
        expected = retirement.identity(child.pid)
        retirement.pause(expected, descriptor)
        assert retirement.stopped(expected)
        signal.pidfd_send_signal(descriptor, signal.SIGCONT)
        assert retirement.alive(expected)
    finally:
        signal.pidfd_send_signal(descriptor, signal.SIGCONT)
        child.terminate()
        child.wait(timeout=10)
        os.close(descriptor)


def test_recovery_cannot_target_arbitrary_receipts():
    with pytest.raises(ValueError, match='exact_retirement_evidence_root'):
        retirement.verify_release_remote(dict(evidence_root='/tmp/other'))


def test_recovery_never_signals(monkeypatch, tmp_path):
    monkeypatch.setattr(retirement, 'BASE', tmp_path)
    output = tmp_path / 'orch_r133_retirement_20260916/physical0_test'
    put(output / 'REQUEST.json', dict(request=dict(node='ovx2', physical=0, actor={}, supervisor={})))
    monkeypatch.setattr(retirement, 'alive', lambda record: True)
    monkeypatch.setattr(retirement.signal, 'pidfd_send_signal', lambda *args: pytest.fail('recovery signal'))
    with pytest.raises(ValueError, match='both_original_processes_exited'):
        retirement.verify_release_remote(dict(evidence_root=str(output)))


@pytest.fixture
def math_boundary(tmp_path):
    lane = tmp_path / 'math'
    phase = lane / 'R119_LEASE_V3/cycle91/experience'
    actor = dict(pid=42, boot_id='boot', start_ticks='123')
    process = ['boot', 42, 123]
    put(phase / 'STATE.json', dict(memory='actual saved own memory', pending=None))
    complete = dict(status='COMPLETE', process=process, phase='experience', cycle=91,
                    child_calls=8, new_child_calls=8, weight_writes=0, adapter=None, optimizer=None,
                    finished_unix=30, state_sha256=retirement.sha(phase / 'STATE.json'))
    put(phase / 'COMPLETE.json', complete)
    put(phase / 'AFTER.json', dict(process=process, actual_mounted_base_verified=True,
                                 adapter=None, optimizer=None,
                                 base_sha256='a2367093892219a833eea1bc7b3e0e2069bcaecad335df357809679d272f4992'))
    put(phase / 'REQUEST.json', dict(started_unix=1))
    rows = []
    for number in range(1, 9):
        put(phase / f'CALL_{number:04d}.json', dict(response={}, outcome={}, process=process,
                                                 updates=0, finished_unix=20))
        rows.append(json.dumps(dict(index=number, reserved_unix=10)))
    (lane / 'CALLS_NATIVE.jsonl').write_text('\n'.join(rows) + '\n')
    (lane / 'CALLS_PARENT.jsonl').write_text(json.dumps(dict(index=1, reserved_unix=10)) + '\n')
    return phase, actor, lane


def test_math_exact_state_and_all_charges_preserved(math_boundary):
    assert retirement.math_frontier(*math_boundary)['calls'] == 8


@pytest.mark.parametrize('kind', ['NATIVE', 'PARENT'])
def test_math_new_charge_after_boundary_refuses_retirement(math_boundary, kind):
    phase, actor, lane = math_boundary
    with (lane / f'CALLS_{kind}.jsonl').open('a') as stream:
        stream.write(json.dumps(dict(index=9, reserved_unix=31)) + '\n')
    with pytest.raises(ValueError, match='later_charge_after_saved_phase'):
        retirement.math_frontier(phase, actor, lane)


def test_math_later_phase_request_refuses_even_before_native_call(math_boundary):
    phase, actor, lane = math_boundary
    put(phase.parent / 'readout/REQUEST.json', dict(started_unix=31))
    with pytest.raises(ValueError, match='later_phase_request'):
        retirement.math_frontier(phase, actor, lane)


def test_math_state_hash_mismatch_refuses(math_boundary):
    phase, actor, lane = math_boundary
    put(phase / 'STATE.json', dict(memory='changed'))
    with pytest.raises(ValueError, match='exact_latest_state'):
        retirement.math_frontier(phase, actor, lane)


def test_math_active_optimizer_or_update_cannot_use_inference_retirement(math_boundary):
    phase, actor, lane = math_boundary
    complete = retirement.read(phase / 'COMPLETE.json')
    complete['weight_writes'] = 1
    put(phase / 'COMPLETE.json', complete)
    with pytest.raises(ValueError, match='verified_BASE_only_boundary'):
        retirement.math_frontier(phase, actor, lane)


def test_math_incomplete_response_refuses(math_boundary):
    phase, actor, lane = math_boundary
    put(phase / 'CALL_0008.json', dict(process=['boot', 42, 123], updates=0))
    with pytest.raises(ValueError, match='complete_phase_call'):
        retirement.math_frontier(phase, actor, lane)


@pytest.fixture
def code_boundary(tmp_path):
    root = tmp_path / 'code'
    lane = root / 'campaign_code_parent'
    put(root / 'cohort.json', [dict(cycle=101)])
    put(root / 'cohorts.json', dict(chunks=[dict(chunk=0, last_cycle=101,
                                             cohort=retirement.ref(root / 'cohort.json'))]))
    put(root / 'PLAN.json', dict(cohorts=retirement.ref(root / 'cohorts.json'),
                                 ancestry=dict(native_used=10, parent_used=20)))
    put(root / 'CHUNK_000_COMPLETE.json', dict(chunk=0, optimizer_updates=0, finished_unix=30,
                                             cumulative_counts=dict(NATIVE=11, PARENT=21)))
    put(root / 'CHUNK_000_CARRY_PRIVATE.json', dict(own_context='complete context', lessons=['carried']))
    model = dict(adapter_sha256='unchanged', optimizer_updates=0)
    put(root / 'ACTOR_READY.json', dict(model=model))
    put(lane / 'CYCLE_101_COMPLETE.json', dict(cycle=101, status='COMPLETE', updates=0, no_adapter=model))
    put(lane / 'CONTEXT_DISTILLATION_C101.json', dict(status='COMPLETE', weight_updates=0,
                                                   own_context='complete context'))
    put(lane / 'cells/N.json', dict(cycle=101, kind='NATIVE', status='COMPLETE', response={},
                                   started_unix=10, finished_unix=20))
    put(lane / 'cells/P.json', dict(cycle=101, kind='PARENT', status='PENDING', started_unix=10))
    return root


def test_code_full_chunk_keeps_context_lessons_and_pending(code_boundary):
    result = retirement.code_frontier(code_boundary, 0)
    assert result['last_cycle'] == 101 and result['pending_parents'] == 1


def test_code_next_cycle_intent_blocks_old_chunk(code_boundary):
    put(code_boundary / 'campaign_code_parent/cells/later.json', dict(cycle=102, kind='NATIVE', status='STARTED'))
    with pytest.raises(ValueError, match='later_cycle_work_after_chunk'):
        retirement.code_frontier(code_boundary, 0)


def test_code_missing_chunk_carry_cannot_use_cycle_complete(code_boundary):
    (code_boundary / 'CHUNK_000_CARRY_PRIVATE.json').unlink()
    with pytest.raises(FileNotFoundError):
        retirement.code_frontier(code_boundary, 0)


def test_code_charge_mismatch_blocks(code_boundary):
    path = code_boundary / 'CHUNK_000_COMPLETE.json'
    row = retirement.read(path)
    row['cumulative_counts']['NATIVE'] += 1
    put(path, row)
    with pytest.raises(ValueError, match='saved_chunk_charge_frontier'):
        retirement.code_frontier(code_boundary, 0)


def test_code_unsaved_native_blocks(code_boundary):
    path = code_boundary / 'campaign_code_parent/cells/N.json'
    row = retirement.read(path)
    row['status'] = 'STARTED'
    put(path, row)
    with pytest.raises(ValueError, match='unfinished_native_after_chunk'):
        retirement.code_frontier(code_boundary, 0)


@pytest.fixture
def grid_boundary(tmp_path):
    root = tmp_path / 'grid'
    root.mkdir()
    put(root / 'CARRY.json', ['actual sourced history'])
    (root / 'LEDGER.jsonl').write_text(json.dumps(dict(cycle=2, kind='NATIVE', number=9)) + '\n')
    put(root / 'calls/N00009.json', dict(status='COMPLETE', response={}))
    put(root / 'lease_budget_r119_learned/C0002_CONTINUED.json', dict(cycle=2, optimizer_steps=0,
        observed_unix=30, carry=retirement.ref(root / 'CARRY.json'), ledger=retirement.ref(root / 'LEDGER.jsonl')))
    return root


def test_grid_saved_carry_and_ledger_exact(grid_boundary):
    assert retirement.grid_frontier(grid_boundary, 2)['carry_items'] == 1


def test_grid_new_charge_invalidates_saved_boundary(grid_boundary):
    with (grid_boundary / 'LEDGER.jsonl').open('a') as stream:
        stream.write(json.dumps(dict(cycle=3, kind='NATIVE', number=10)) + '\n')
    with pytest.raises(ValueError, match='later_grid_charge_after_saved_boundary'):
        retirement.grid_frontier(grid_boundary, 2)


def test_grid_changed_memory_blocks(grid_boundary):
    put(grid_boundary / 'CARRY.json', ['later thought'])
    with pytest.raises(ValueError, match='reference_hash'):
        retirement.grid_frontier(grid_boundary, 2)


def test_grid_incomplete_native_blocks(grid_boundary):
    put(grid_boundary / 'calls/N00009.json', dict(status='STARTED'))
    with pytest.raises(ValueError, match='complete_grid_native_results'):
        retirement.grid_frontier(grid_boundary, 2)


def test_archive_overlapping_inputs_deduplicates(tmp_path):
    root = tmp_path / 'state'
    root.mkdir()
    (root / 'weights').write_bytes(b'weights')
    assert len(retirement.archive([root, root / 'weights'], tmp_path / 'saved.tar')['files']) == 1


def test_idle_scan_retry_preserves_rejections_without_signals(tmp_path, monkeypatch):
    monkeypatch.setattr(retirement, 'read', lambda path: dict(pythonpath='frozen', node3_scanner='frozen_scanner'))
    reports = iter([dict(clear=False, blocking_reasons=['device_not_idle']),
                    dict(clear=True, scanner_euid=0, gpu=dict(index=0, uuid=retirement.UUID))])
    monkeypatch.setattr(retirement.subprocess, 'check_output', lambda *args, **kwargs: json.dumps(next(reports)))
    monkeypatch.setattr(retirement.time, 'sleep', lambda seconds: None)
    monkeypatch.setattr(retirement.signal, 'pidfd_send_signal', lambda *args: pytest.fail('scan signal'))
    assert retirement.fresh_release(tmp_path)['clear']
    assert len(list(tmp_path.glob('SCAN_*.json'))) == 2


def test_foreign_occupancy_never_overridden(tmp_path, monkeypatch):
    monkeypatch.setattr(retirement, 'read', lambda path: dict(pythonpath='frozen', node3_scanner='frozen_scanner'))
    monkeypatch.setattr(retirement.subprocess, 'check_output', lambda *args, **kwargs:
                        json.dumps(dict(clear=False, blocking_reasons=['foreign_PID:99'])))
    with pytest.raises(ValueError, match='release_not_proven'):
        retirement.fresh_release(tmp_path)
    assert len(list(tmp_path.glob('SCAN_*.json'))) == 1


def test_release_post_appends_without_replacing_others(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    path = tmp_path / 'research_loop/COORDINATION.md'
    path.parent.mkdir()
    path.write_text('Other worker entry\n')
    retirement.post_release(dict(status='RELEASED', physical=3, uuid=retirement.DEVICES[3],
                                 released_utc='2026-09-16T12:00:00Z'), 'receipt.json')
    assert path.read_text().startswith('Other worker entry\n')
    assert 'physical3 RELEASED' in path.read_text()


def test_pending_status_cannot_post_release(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    with pytest.raises(ValueError, match='only_verified_own_release_post'):
        retirement.post_release(dict(status='WAIT_EXPIRED_NO_RETIREMENT'), 'receipt.json')
