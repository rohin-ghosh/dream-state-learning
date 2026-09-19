"""CPU-only artificial metadata and processes; no SSH, science reads or signals."""

from copy import deepcopy
import hashlib
import json
import os
from pathlib import Path
import shutil
import signal
from types import SimpleNamespace

import pytest

from gpu import orch_r146_benchmark_idle_handoff as handoff


def dump(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    raw = handoff.encoded(value)
    path.write_bytes(raw)
    return hashlib.sha256(raw).hexdigest()


def load(path):
    return json.loads(path.read_bytes())


def change(path, **values):
    value = load(path)
    value.update(values)
    return dump(path, value)


@pytest.fixture
def boundary(tmp_path, monkeypatch):
    root = tmp_path / 'old'
    phase_root = root / 'successor_phase_v2'
    scheduler_root = root / 'scheduler_run_phase2_02'
    ledger_root = root / 'scheduler_ledger'
    for name, value in dict(ROOT=root, PHASE_ROOT=phase_root, PHASE_CONFIG=root / 'SUCCESSOR_PHASE_V2.json',
            SEGMENT_CONFIG=phase_root / 'SEGMENT_02.CONFIG.json', SCHEDULER_ROOT=scheduler_root,
            LEDGER_ROOT=ledger_root).items():
        monkeypatch.setattr(handoff, name, value)
    source = root / 'source6_scheduler'
    source.mkdir(parents=True)
    ledger_root.mkdir()
    python = '/synthetic/python'
    phase = dict(output_root=str(phase_root), hard_end_unix=10000)
    config = dict(output_root=str(scheduler_root), ledger_root=str(ledger_root), python=python,
        source_root=str(source), hard_end_unix=9000)
    monkeypatch.setattr(handoff, 'PHASE_SHA256', dump(handoff.PHASE_CONFIG, phase))
    monkeypatch.setattr(handoff, 'SEGMENT_SHA256', dump(handoff.SEGMENT_CONFIG, config))
    phase_identity = dict(pid=40001, uid=os.getuid(), start_ticks='100', boot_id='synthetic-boot',
        ppid=40000, cwd=str(tmp_path), cmdline=[python, '-B',
            str(root / 'successor_tools_v2/gpu/orch_r130_successor_phase.py'),
            'node', '--config', str(handoff.PHASE_CONFIG)])
    scheduler_identity = dict(pid=40002, uid=os.getuid(), start_ticks='101', boot_id='synthetic-boot',
        ppid=40001, cwd=str(source), cmdline=[python, '-B', '-m',
            'gpu.orch_r130_checkpoint_scheduler', 'run', '--config', str(handoff.SEGMENT_CONFIG)])
    identities = {40001: phase_identity, 40002: scheduler_identity}
    environment = {40001: dict(CUDA_VISIBLE_DEVICES='', R130_PHASE_SHA256=handoff.PHASE_SHA256),
        40002: dict(CUDA_VISIBLE_DEVICES='', R130_SCHEDULER_ADMISSION_SHA256=handoff.SEGMENT_SHA256)}
    monkeypatch.setattr(handoff, 'process_identity', lambda pid: deepcopy(identities[pid]))
    monkeypatch.setattr(handoff, 'process_environment', lambda pid: environment[pid])
    monkeypatch.setattr(handoff, 'scheduler_children', lambda pid: [])
    monkeypatch.setattr(handoff, 'launch_gone', lambda identity: True)
    clock = dict(wall=1000.0, monotonic=100.0)
    monkeypatch.setattr(handoff.time, 'time', lambda: clock['wall'])
    monkeypatch.setattr(handoff.time, 'monotonic', lambda: clock['monotonic'])
    sent, opened, closed = [], [], []

    def open_pidfd(pid, flags):
        opened.append((pid, flags))
        return 123456

    real_close = os.close

    def close_pidfd(descriptor):
        if descriptor == 123456:
            closed.append(descriptor)
        else:
            real_close(descriptor)

    monkeypatch.setattr(handoff.os, 'pidfd_open', open_pidfd)
    monkeypatch.setattr(handoff.os, 'close', close_pidfd)
    monkeypatch.setattr(handoff.signal, 'pidfd_send_signal', lambda *args: sent.append(args))
    dump(phase_root / 'STARTED.json', dict(identity=handoff.legacy(phase_identity), phase_sha256=handoff.PHASE_SHA256))
    dump(scheduler_root / 'STARTED.json', dict(identity=handoff.legacy(scheduler_identity),
        config_sha256=handoff.SEGMENT_SHA256))
    dump(phase_root / 'SEGMENT_02.LAUNCH.json', dict(identity=handoff.legacy(scheduler_identity),
        config_path=str(handoff.SEGMENT_CONFIG), config_sha256=handoff.SEGMENT_SHA256))
    phase_status = phase_root / 'STATUS_000001.json'
    scheduler_status = scheduler_root / 'STATUS_000002.json'
    dump(phase_status, dict(status='SEGMENT_RUNNING', phase_sha256=handoff.PHASE_SHA256,
        active_config_path=str(handoff.SEGMENT_CONFIG), active_config_sha256=handoff.SEGMENT_SHA256,
        active_physical=[], observed_unix=990, hard_end_unix=10000, next_dispatch_unix=2000,
        reserved_checkpoint_count=8, completed_checkpoint_count=7))
    dump(scheduler_status, dict(status='BOUNDED_POLLING', config_sha256=handoff.SEGMENT_SHA256,
        active_physical=[], observed_unix=995, hard_end_unix=9000, next_dispatch_unix=2000,
        baseline_completed_checkpoints=6, completed_checkpoint_count=7))
    jobs, claims = [], []
    for index, complete in enumerate((True, False)):
        claim = dict(lineage_id='legacy', commit_sha256=str(index) * 64, corpus_sha256='c' * 64,
            config_path=str(handoff.SEGMENT_CONFIG), config_sha256=handoff.SEGMENT_SHA256)
        key = handoff.digest_legacy_key(claim)
        job = scheduler_root / 'dispatch_0001' / ('physical' + str(index) + '_job_' + key)
        plan_path = job / 'PLAN.json'
        claim.update(plan_path=str(plan_path), plan_sha256=dump(plan_path,
            dict(corpus_path='/MUST_NOT_READ/sealed.json', output_path=str(job / 'results'))))
        claim_path = ledger_root / (key + '.RESERVED.json')
        claim_sha = dump(claim_path, claim)
        dump(job / 'LAUNCH.json', dict(identity=dict(pid=50001 + index, uid=os.getuid(), start_ticks='50',
            boot_id='synthetic-boot'), claim_sha256=claim_sha, plan_sha256=claim['plan_sha256'],
            config_sha256=handoff.SEGMENT_SHA256))
        dump(job / 'EXIT.json', dict(exit_code=0 if complete else 1, observed_unix=950))
        if complete:
            dump(ledger_root / (key + '.COMPLETE.json'), dict(status='COMPLETE', key=key,
                claim_sha256=claim_sha, native_complete_path='/MUST_NOT_READ/native-science.json',
                native_complete_sha256='d' * 64, private_curve_path='/MUST_NOT_READ/curve.json'))
        else:
            dump(job / 'FAILED.json', dict(status='FAILED', key=key, automatic_retry=False))
        jobs.append(job)
        claims.append(claim_path)
    request = dict(schema=handoff.SCHEMA, operation_id='main-idle-001', hostname=handoff.socket.gethostname(),
        phase_identity=deepcopy(phase_identity), scheduler_identity=deepcopy(scheduler_identity))
    return SimpleNamespace(root=root, phase_root=phase_root, scheduler_root=scheduler_root,
        phase_status=phase_status, scheduler_status=scheduler_status, ledger_root=ledger_root,
        request=request, identities=identities, environment=environment, clock=clock,
        sent=sent, opened=opened, closed=closed, jobs=jobs, claims=claims, output=tmp_path / 'operation',
        approval=tmp_path / 'approval.json')


def observe_and_approve(boundary):
    observed = handoff.observe(boundary.request, boundary.output)
    assert observed['status'] == 'ELIGIBLE_OBSERVATION_ONLY', observed
    approval = dict(schema=handoff.APPROVAL_SCHEMA, operation_id=boundary.request['operation_id'],
        action=handoff.ACTION, approved_by='Main', cpu_tests_passed=True, provenance_passed=True,
        observation_sha256=hashlib.sha256((boundary.output / 'OBSERVATION.json').read_bytes()).hexdigest(),
        request_sha256=observed['request_sha256'], snapshot_sha256=observed['snapshot_sha256'],
        helper_sha256=observed['helper_sha256'], issued_unix=1000, expires_unix=1020)
    return dump(boundary.approval, approval)


def assert_deferred(boundary, result):
    assert result['status'] == 'DEFER_WITHOUT_SIGNAL', result
    assert result['signal_sent'] is False
    assert boundary.sent == []


def test_observation_only_preserves_all_old_bytes(boundary):
    before = {path: path.read_bytes() for path in boundary.root.rglob('*') if path.is_file()}
    result = handoff.observe(boundary.request, boundary.output)
    assert result['status'] == 'ELIGIBLE_OBSERVATION_ONLY', result
    assert result['snapshot']['ledger'] == dict(reservations=2, completed=1, terminal_failed=1)
    assert boundary.sent == boundary.opened == []
    assert before == {path: path.read_bytes() for path in before}
    with pytest.raises(FileExistsError):
        handoff.observe(boundary.request, boundary.output)


def test_exactly_one_pidfd_sigint_scheduler_only(boundary):
    checksum = observe_and_approve(boundary)
    result = handoff.execute(boundary.output, boundary.approval, checksum)
    assert result['status'] == 'INTENTIONAL_IDLE_HANDOFF', result
    assert result['scientific_failure'] is False
    assert result['retirement_verified'] is False
    assert boundary.opened == [(40002, 0)]
    assert boundary.sent == [(123456, signal.SIGINT, None, 0)]
    assert boundary.closed == [123456]
    assert load(boundary.output / 'INTENT.json')['status'] == 'INTENTIONAL_IDLE_HANDOFF'
    assert handoff.execute(boundary.output, boundary.approval, checksum)['status'] == 'ALREADY_CONSUMED_NO_RETRY'
    assert len(boundary.sent) == 1
    assert not (boundary.phase_root / 'FAILED.json').exists()


@pytest.mark.parametrize('field,value', [('pid', 40003), ('uid', 999999), ('start_ticks', '999'),
    ('boot_id', 'other-boot'), ('ppid', 1), ('cmdline', ['python', 'model']), ('cwd', '/wrong')])
@pytest.mark.parametrize('pid', [40001, 40002])
def test_exact_live_identity_drift_defers(boundary, field, value, pid):
    boundary.identities[pid][field] = value
    assert_deferred(boundary, handoff.observe(boundary.request, boundary.output))


@pytest.mark.parametrize('target', ['phase_status', 'scheduler_status'])
@pytest.mark.parametrize('values', [dict(active_physical=[0]), dict(next_dispatch_unix=1120),
    dict(next_dispatch_unix=None), dict(next_dispatch_unix=999), dict(observed_unix=934),
    dict(observed_unix=1001), dict(hard_end_unix=1120), dict(status='FAILED'),
    dict(completed_checkpoint_count=100)])
def test_active_stale_late_or_conflicting_status_defers(boundary, target, values):
    change(getattr(boundary, target), **values)
    assert_deferred(boundary, handoff.observe(boundary.request, boundary.output))


@pytest.mark.parametrize('damage', ['phase_pin', 'segment_pin', 'started_identity', 'phase_launch_identity',
    'unresolved', 'live_launch', 'missing_exit', 'bad_exit', 'bad_completion', 'plan_changed',
    'retry_allowed', 'new_status', 'terminal_phase', 'terminal_scheduler', 'child', 'cuda', 'env_pin',
    'parent', 'hostname', 'orphan_plan', 'symlink', 'orphan_completion'])
def test_fail_closed_metadata_and_process_cases(boundary, monkeypatch, damage):
    if damage in ('phase_pin', 'segment_pin'):
        path = handoff.PHASE_CONFIG if damage == 'phase_pin' else handoff.SEGMENT_CONFIG
        change(path, extra='changed')
    elif damage in ('started_identity', 'phase_launch_identity'):
        path = boundary.scheduler_root / 'STARTED.json' if damage == 'started_identity' else (
            boundary.phase_root / 'SEGMENT_02.LAUNCH.json')
        change(path, identity=dict(handoff.legacy(boundary.identities[40002]), start_ticks='wrong'))
    elif damage == 'unresolved':
        (boundary.jobs[1] / 'FAILED.json').unlink()
    elif damage == 'live_launch':
        monkeypatch.setattr(handoff, 'launch_gone', lambda identity: False)
    elif damage == 'missing_exit':
        (boundary.jobs[1] / 'EXIT.json').unlink()
    elif damage == 'bad_exit':
        change(boundary.jobs[0] / 'EXIT.json', exit_code=1)
    elif damage == 'bad_completion':
        change(next(boundary.ledger_root.glob('*.COMPLETE.json')), claim_sha256='wrong')
    elif damage == 'plan_changed':
        change(boundary.jobs[1] / 'PLAN.json', extra=True)
    elif damage == 'retry_allowed':
        change(boundary.jobs[1] / 'FAILED.json', automatic_retry=True)
    elif damage == 'new_status':
        dump(boundary.scheduler_root / 'STATUS_000003.json', dict(load(boundary.scheduler_status), active_physical=[1]))
    elif damage.startswith('terminal_'):
        root = boundary.phase_root if damage == 'terminal_phase' else boundary.scheduler_root
        dump(root / 'FAILED.json', dict(status='FAILED'))
    elif damage == 'child':
        monkeypatch.setattr(handoff, 'scheduler_children', lambda pid: ['50001'])
    elif damage == 'cuda':
        boundary.environment[40002]['CUDA_VISIBLE_DEVICES'] = '0'
    elif damage == 'env_pin':
        boundary.environment[40002]['R130_SCHEDULER_ADMISSION_SHA256'] = 'wrong'
    elif damage == 'parent':
        boundary.request['scheduler_identity']['ppid'] = 1
    elif damage == 'hostname':
        boundary.request['hostname'] = 'source-node-forbidden'
    elif damage == 'orphan_plan':
        dump(boundary.scheduler_root / 'dispatch_0002/physical0_job_unreserved/PLAN.json', {})
    elif damage == 'symlink':
        path = boundary.jobs[1] / 'EXIT.json'
        target = path.with_name('saved-exit')
        path.rename(target)
        path.symlink_to(target)
    elif damage == 'orphan_completion':
        dump(boundary.ledger_root / ('f' * 64 + '.COMPLETE.json'), {})
    assert_deferred(boundary, handoff.observe(boundary.request, boundary.output))


def test_explicit_prelaunch_admission_failure_allowed(boundary):
    job = boundary.jobs[1]
    failure = load(job / 'FAILED.json')
    for name in ('LAUNCH.json', 'EXIT.json', 'FAILED.json'):
        (job / name).unlink()
    dump(job.parent / 'physical1.FAILED.json', dict(status='ADMISSION_FAILED_NO_MODEL_REPLAY', key=failure['key']))
    result = handoff.observe(boundary.request, boundary.output)
    assert result['status'] == 'ELIGIBLE_OBSERVATION_ONLY', result


@pytest.mark.parametrize('values', [dict(approved_by='Archimedes'), dict(cpu_tests_passed=False),
    dict(provenance_passed=False), dict(action='SIGTERM'), dict(observation_sha256='wrong'),
    dict(request_sha256='wrong'), dict(snapshot_sha256='wrong'), dict(helper_sha256='wrong'),
    dict(operation_id='other'), dict(expires_unix=1000), dict(expires_unix=1031), dict(issued_unix=1001),
    dict(extra=True)])
def test_bound_external_approval_required_and_attempt_consumed(boundary, values):
    observe_and_approve(boundary)
    checksum = change(boundary.approval, **values)
    assert_deferred(boundary, handoff.execute(boundary.output, boundary.approval, checksum))
    assert handoff.execute(boundary.output, boundary.approval, checksum)['status'] == 'ALREADY_CONSUMED_NO_RETRY'


def test_approval_bytes_must_be_pinned(boundary):
    observe_and_approve(boundary)
    assert_deferred(boundary, handoff.execute(boundary.output, boundary.approval, 'wrong'))


def test_operation_directory_copy_cannot_replay_approval(boundary):
    checksum = observe_and_approve(boundary)
    copied = boundary.output.with_name('copied-operation')
    shutil.copytree(boundary.output, copied)
    assert_deferred(boundary, handoff.execute(copied, boundary.approval, checksum))


@pytest.mark.parametrize('mutation', ['status', 'pid', 'children', 'expiry', 'late_window', 'clock_jump', 'new_launch'])
def test_race_after_pidfd_open_defers_and_closes(boundary, monkeypatch, mutation):
    checksum = observe_and_approve(boundary)
    original = handoff.os.pidfd_open

    def race(pid, flags):
        descriptor = original(pid, flags)
        if mutation == 'status':
            change(boundary.scheduler_status, active_physical=[1])
        elif mutation == 'pid':
            boundary.identities[40002]['start_ticks'] = 'replacement'
        elif mutation == 'children':
            monkeypatch.setattr(handoff, 'scheduler_children', lambda pid: ['new-job'])
        elif mutation == 'expiry':
            boundary.clock.update(wall=1021, monotonic=121)
        elif mutation == 'late_window':
            boundary.clock.update(wall=1880, monotonic=980)
        elif mutation == 'clock_jump':
            boundary.clock['wall'] = 999
        else:
            dump(boundary.scheduler_root / 'dispatch_0002/physical0_job_new/LAUNCH.json',
                dict(identity=handoff.legacy(boundary.identities[40002])))
        return descriptor

    monkeypatch.setattr(handoff.os, 'pidfd_open', race)
    assert_deferred(boundary, handoff.execute(boundary.output, boundary.approval, checksum))
    assert boundary.closed == [123456]


def test_signal_error_is_uncertain_and_never_retried(boundary, monkeypatch):
    checksum = observe_and_approve(boundary)

    def fail(*args):
        boundary.sent.append(args)
        raise ProcessLookupError('exited')

    monkeypatch.setattr(handoff.signal, 'pidfd_send_signal', fail)
    result = handoff.execute(boundary.output, boundary.approval, checksum)
    assert result['status'] == 'SIGNAL_OUTCOME_UNKNOWN_NO_RETRY'
    assert boundary.closed == [123456]
    assert handoff.execute(boundary.output, boundary.approval, checksum)['status'] == 'ALREADY_CONSUMED_NO_RETRY'
    assert len(boundary.sent) == 1


def test_no_science_or_source_node_reads(boundary, monkeypatch):
    original = handoff.read_bytes
    reads = []

    def metadata_only(path):
        path = Path(path)
        reads.append(path)
        assert 'results' not in path.parts
        assert 'MUST_NOT_READ' not in path.parts
        assert path.suffix == '.py' or path.suffix == '.json'
        return original(path)

    monkeypatch.setattr(handoff, 'read_bytes', metadata_only)
    checksum = observe_and_approve(boundary)
    assert handoff.execute(boundary.output, boundary.approval, checksum)['signal_sent']
    assert reads


def test_old_artifact_output_is_rejected(boundary):
    with pytest.raises(handoff.Defer, match='read_only'):
        handoff.observe(boundary.request, boundary.root / 'new-operation')


def test_metadata_allowlist_rejects_native_complete_and_answers(boundary):
    reader = handoff.Metadata()
    for path in (boundary.jobs[0] / 'results/COMPLETE.json', boundary.jobs[0] / 'CALL_000.json',
            boundary.jobs[0] / 'private_curve.json', boundary.root / 'corpus.json'):
        with pytest.raises(handoff.Defer):
            reader.read(path)


def test_duplicate_json_keys_rejected():
    with pytest.raises(handoff.Defer, match='duplicate_json_key'):
        handoff.document(b'{"active_physical": [0], "active_physical": []}')


def test_real_self_process_identity_metadata_only():
    identity = handoff.process_identity(os.getpid())
    assert set(identity) == handoff.IDENTITY_FIELDS
    assert identity['pid'] == os.getpid()
    assert identity['ppid'] == os.getppid()
    assert identity['uid'] == os.getuid()
    assert identity['cwd'] == os.getcwd()
    assert handoff.launch_gone(handoff.legacy(identity)) is False
    assert handoff.launch_gone(dict(handoff.legacy(identity), start_ticks='0')) is True


def test_new_status_during_inventory_is_not_missed(boundary, monkeypatch):
    original = handoff.ledger_check

    def racing_ledger(*args):
        counts = original(*args)
        dump(boundary.scheduler_root / 'STATUS_000003.json', dict(load(boundary.scheduler_status), active_physical=[1]))
        return counts

    monkeypatch.setattr(handoff, 'ledger_check', racing_ledger)
    assert_deferred(boundary, handoff.observe(boundary.request, boundary.output))


def test_inventory_changes_between_passes_defer(boundary, monkeypatch):
    original = handoff.inventory
    calls = []

    def racing_inventory():
        calls.append(True)
        paths = original()
        return paths if len(calls) == 1 else paths[:-1]

    monkeypatch.setattr(handoff, 'inventory', racing_inventory)
    assert_deferred(boundary, handoff.observe(boundary.request, boundary.output))


def test_pidfd_unavailable_never_falls_back_to_kill(boundary, monkeypatch):
    checksum = observe_and_approve(boundary)

    def unavailable(*args):
        raise OSError('pidfd unavailable')

    def forbidden(*args):
        pytest.fail('numeric PID/group fallback forbidden')

    monkeypatch.setattr(handoff.os, 'pidfd_open', unavailable)
    monkeypatch.setattr(handoff.os, 'kill', forbidden)
    monkeypatch.setattr(handoff.os, 'killpg', forbidden)
    assert_deferred(boundary, handoff.execute(boundary.output, boundary.approval, checksum))


def test_write_once_result_failure_leaves_consumed_claim(boundary, monkeypatch):
    checksum = observe_and_approve(boundary)
    original = handoff.write_once

    def fail_result(path, value):
        if path.name == 'RESULT.json':
            raise OSError('simulated storage failure')
        return original(path, value)

    monkeypatch.setattr(handoff, 'write_once', fail_result)
    with pytest.raises(OSError, match='storage failure'):
        handoff.execute(boundary.output, boundary.approval, checksum)
    assert len(boundary.sent) == 1
    assert (boundary.output / 'INTENT.json').is_file()
    assert handoff.execute(boundary.output, boundary.approval, checksum)['status'] == 'ALREADY_CONSUMED_NO_RETRY'


def test_real_gone_identity_rejects_boot_and_uid_ambiguity():
    identity = handoff.legacy(handoff.process_identity(os.getpid()))
    with pytest.raises(handoff.Defer, match='boot_ambiguity'):
        handoff.launch_gone(dict(identity, boot_id='different-boot'))
    with pytest.raises(handoff.Defer, match='legacy_identity_values'):
        handoff.launch_gone(dict(identity, uid=os.getuid() + 1))


def test_sigint_cascade_contract_without_running_original_helpers():
    scheduler = (Path(__file__).parents[1] / 'gpu/orch_r130_checkpoint_scheduler.py').read_text()
    phase = (Path(__file__).parents[1] / 'gpu/orch_r130_successor_phase.py').read_text()
    assert 'except BaseException as error:' in scheduler
    assert "'FAILED.json' if final_error else 'COMPLETE.json'" in scheduler
    assert "require(code == 0 and terminal.exists(), 'segment_failed_no_automatic_replay')" in phase
    assert "status['status'] in ('BOUNDED_PHASE_FINISHED', 'FAILED')" in phase
