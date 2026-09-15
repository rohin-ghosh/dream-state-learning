import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
from types import SimpleNamespace

import pytest

from gpu import orch_r118_grid_failed_startup_run as recovery


def test_help_has_no_model_import_or_side_effect():
    result = subprocess.run([sys.executable, '-B', recovery.__file__, '--help'], capture_output=True, text=True)
    assert result.returncode == 0
    assert 'bind' in result.stdout


def test_immutable_writer_and_hash_check(tmp_path):
    reference = recovery.write(tmp_path / 'receipt.json', {'retained': True})
    assert recovery.read(reference) == {'retained': True}
    with pytest.raises(FileExistsError):
        recovery.write(tmp_path / 'receipt.json', {'retained': False})
    with pytest.raises(ValueError, match='exact_reference'):
        recovery.read(dict(reference, sha256='wrong'))


def command_fixture():
    plan = dict(path='/own/parallel_exec_1513/PLAN.json', sha256='frozen')
    command = b'python\0/own/source/gpu/orch_r118_grid_parallel_run.py\0timer\0--plan\0' + plan['path'].encode() + b'\0--sha256\0frozen\0'
    expected = dict(pid=123, uid=os.getuid(), command_sha256=hashlib.sha256(command).hexdigest())
    return plan, command, expected


def test_exact_original_timer_cpu_command():
    plan, command, expected = command_fixture()
    recovery.timer_command(expected, plan, command, b'CUDA_VISIBLE_DEVICES=\0')


@pytest.mark.parametrize('change', ['selector', 'other_plan', 'readout', 'CUDA', 'source'])
def test_timer_scope_rejects_foreign_or_eval(change):
    plan, command, expected = command_fixture()
    environment = b'CUDA_VISIBLE_DEVICES=\0'
    if change == 'selector':
        expected['pid'] = recovery.SELECTOR_PID
    elif change == 'other_plan':
        plan = dict(plan, path='/foreign/PLAN.json')
    elif change == 'readout':
        command = command.replace(b'timer', b'readout')
        expected['command_sha256'] = hashlib.sha256(command).hexdigest()
    elif change == 'source':
        command = command.replace(b'orch_r118_grid_parallel_run.py', b'other.py')
        expected['command_sha256'] = hashlib.sha256(command).hexdigest()
    else:
        environment = b'CUDA_VISIBLE_DEVICES=7\0'
    with pytest.raises(ValueError):
        recovery.timer_command(expected, plan, command, environment)


def test_failed_session_rejected_before_runtime(monkeypatch):
    monkeypatch.setenv('R118_PARALLEL_SESSION_SHA256', recovery.FAILED_SESSION_SHA)
    with pytest.raises(ValueError, match='new_Main_session'):
        recovery.validate_active_session({}, None)


def test_new_failed_session_rejected_before_model(tmp_path, monkeypatch):
    monkeypatch.setenv('R118_PARALLEL_SESSION', str(tmp_path / 'SESSION.json'))
    monkeypatch.setenv('R118_PARALLEL_SESSION_SHA256', 'new')
    (tmp_path / 'FAILED.json').write_text('{}')
    handoff = SimpleNamespace(parallel=SimpleNamespace(fresh_session=lambda *args: ({}, tmp_path)))
    with pytest.raises(ValueError, match='before_any_model_load'):
        recovery.validate_active_session({}, handoff)


def test_recovery_wrapper_preserves_original_runner(tmp_path, monkeypatch):
    original = Path(recovery.__file__).with_name('orch_r118_grid_parallel_run.py')
    before = original.read_bytes()
    runner = recovery.configured_runner({})
    assert runner.TERMINAL == recovery.TERMINAL != recovery.ORIGINAL_TERMINAL
    assert runner.__file__ == recovery.__file__
    assert runner.retire_old_timers is recovery.retire_previous_timer
    assert original.read_bytes() == before


def test_guard_requires_bound_plan_before_modules(tmp_path):
    result = subprocess.run([sys.executable, '-B', recovery.__file__, 'guard'], capture_output=True, text=True)
    assert result.returncode != 0
    assert 'exact_plan_required' in result.stderr


@pytest.fixture
def failed_start(tmp_path, monkeypatch):
    root = tmp_path / 'A4'
    old_directory = root / 'parallel_exec_1513'
    old_directory.mkdir(parents=True)
    ledger = recovery.write(root / 'LEDGER.jsonl', {'NATIVE': 567, 'PARENT': 40})
    carry = recovery.write(root / 'CARRY.json', {'retained': True})
    terminal = recovery.write(root / recovery.ORIGINAL_TERMINAL, {'status': 'FAILED'})
    session = recovery.write(tmp_path / 'SESSION.json', {'state': {'generation': 1,
        'checkpoint': {'path_sha256': recovery.CHECKPOINT_SHA}},
        'owners': {'A4': {'bootstrap_path': str(old_directory / 'CANONICAL_BOOTSTRAP.json')}}})
    monkeypatch.setattr(recovery, 'FAILED_SESSION_SHA', session['sha256'])
    control = tmp_path / 'SESSION.dispatch'
    failure = recovery.write(control / 'FAILED.json', {'session_sha256': session['sha256'], 'retry_allowed': False})
    old_plan = dict(root=str(root), branch='A4', directory=str(old_directory),
                    bounds={'train_end_unix': 1789491300}, boundary={'unchanged': True})
    old_plan_ref = recovery.write(old_directory / 'PLAN.json', old_plan)
    observation = recovery.write(tmp_path / 'OBSERVED.json', {'session': session, 'GO_exists': False,
        'branches': {'A4': {'new_generation_calls': 0, 'optimizer_steps': 0, 'preserved_mismatches': [],
            'extra_call_or_parent_or_triple_files': [], 'ledger_counts': {'NATIVE': 567, 'PARENT': 40},
            'ledger': ledger, 'carry': carry}}})
    document = dict(schema='R118_GRID_FAILED_STARTUP_RECOVERY_V1', root=str(root), branch='A4',
        failed_session=session, failed_dispatch=failure, old_plan=old_plan_ref, old_terminal=terminal,
        observation=observation, predecessors=[{'pid': 123}], preserved_files={'CARRY.json': carry['sha256']})
    document_ref = recovery.write(root / 'RECOVERY.json', document)
    plan = dict(old_plan, directory=str(root / 'parallel_recovery_1548'), failed_startup_recovery=document_ref)
    released = []
    handoff = SimpleNamespace(parallel=SimpleNamespace(predecessor_released=released.append),
                             inside=lambda actual, name: actual / name)
    return plan, handoff, root, control, released


def test_real_zero_call_failure_validation_keeps_carry_pending(failed_start):
    plan, handoff, root, control, released = failed_start
    before = {name: (root / name).read_bytes() for name in ('LEDGER.jsonl','CARRY.json')}
    recovery.verify_failed_start(plan, handoff)
    assert released == [{'pid': 123}]
    assert before == {name: (root / name).read_bytes() for name in before}
    assert not (Path(plan['directory']) / 'GUARD_ONCE').exists()


@pytest.mark.parametrize('mutation', ['ledger','carry','GO','bootstrap','entry','same_directory','bounds'])
def test_failed_start_no_replay_invariants(failed_start, mutation):
    plan, handoff, root, control, released = failed_start
    if mutation in ('ledger','carry'):
        (root / ('LEDGER.jsonl' if mutation == 'ledger' else 'CARRY.json')).write_text('changed')
    elif mutation == 'GO':
        (control / 'GO.json').write_text('{}')
    elif mutation == 'bootstrap':
        (control / 'A4.BOOTSTRAP_START.json').write_text('{}')
    elif mutation == 'entry':
        (root / 'parallel_exec_1513/ENTRY.json').write_text('{}')
    elif mutation == 'same_directory':
        plan['directory'] = str(root / 'parallel_exec_1513')
    else:
        plan['bounds'] = dict(train_end_unix=1789499999)
    with pytest.raises(ValueError):
        recovery.verify_failed_start(plan, handoff)


def test_preparation_requires_CPU_authority_before_reading_owner(tmp_path):
    from gpu import orch_r118_grid_failed_startup_stage as stage
    authority = recovery.write(tmp_path / 'AUTH.json', {'schema': 'R118_GRID_FAILED_STARTUP_CPU_AUTH_V1',
        'GPU_start_authorized': True, 'expires_unix': 1789488600})
    with pytest.raises(ValueError, match='CPU_authorization'):
        stage.prepare_branch(None, None, None, authority)


def test_native_timer_identity_without_uid_uses_actual_uid():
    from gpu import orch_r118_grid_failed_startup_stage as stage
    original = dict(pid=123, start_ticks=42, boot_id='fixture')
    actual = dict(original, start_ticks='42', uid=os.getuid(), state='S')
    stage.validate_timer_identity(actual, original)
    assert 'uid' not in original
    for change in (dict(uid=os.getuid()+1), dict(start_ticks=43), dict(state='Z'), dict(boot_id='other')):
        with pytest.raises(ValueError, match='retained_live_timer'):
            stage.validate_timer_identity(dict(actual, **change), original)
