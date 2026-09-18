import json
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from gpu import orch_r118_route_parallel_lifecycle as lifecycle
from gpu import orch_r118_route_startup_recovery as recovery


@pytest.mark.parametrize('cvd,clear', [('', True), ('GPU-fixture', False)])
def test_actual_frozen_launch_CPU_reservation_and_native_UUID(tmp_path, monkeypatch, cvd, clear):
    root = tmp_path / 'life'
    root.mkdir()
    plan = dict(uuid='GPU-fixture', parallel_source=str(tmp_path), route_boundary_release={},
                parallel_stage=dict(authorization={}))
    monkeypatch.setenv('CUDA_VISIBLE_DEVICES', cvd)
    monkeypatch.setattr(lifecycle, 'verify_plan', lambda path: plan)
    monkeypatch.setattr(lifecycle.boundary, 'released', lambda *args: None)
    monkeypatch.setattr(lifecycle, 'verify_retirements', lambda *args: None)
    monkeypatch.setattr(lifecycle, 'bound', lambda *args: {})
    monkeypatch.setattr(lifecycle, 'validate_broker_binding', lambda *args: None)
    monkeypatch.setattr(lifecycle, 'ref', lambda path: dict(path=str(path), sha256='fixture'))
    monkeypatch.setattr(lifecycle.boundary.prior, 'identity', lambda pid: dict(pid=pid))
    captures = []

    def scanner(command, **kwargs):
        assert 'CUDA_VISIBLE_DEVICES=' in command
        captures.append(command)
        return SimpleNamespace(stdout=json.dumps(dict(clear=clear)).encode())

    monkeypatch.setattr(lifecycle.subprocess, 'run', scanner)
    process = Mock(return_value=SimpleNamespace(pid=42))
    monkeypatch.setattr(lifecycle.subprocess, 'Popen', process)
    if clear:
        lifecycle.launch(root, '/fixture/python')
        assert process.call_args.kwargs['env']['CUDA_VISIBLE_DEVICES'] == 'GPU-fixture'
        assert process.call_args.args[0][-3:] == ['supervise', '--root', str(root)]
    else:
        with pytest.raises(ValueError, match='fresh_privileged'):
            lifecycle.launch(root, '/fixture/python')
        process.assert_not_called()
    assert len(captures) == 2
    assert (root / 'R118_PARALLEL_LAUNCH_ATTEMPT.json').exists()


@pytest.mark.parametrize('name', ['DISPATCH', 'SUPERVISOR', 'ACTOR_READY', 'FRESH_BOOTSTRAP',
                                  'TERMINAL', 'ADMISSION'])
def test_any_inference_era_evidence_blocks_recovery(tmp_path, name):
    (tmp_path / ('R118_PARALLEL_' + name + '.json')).write_text('{}')
    with pytest.raises(ValueError, match='pre_inference_only'):
        recovery.no_inference(tmp_path)


def test_old_failed_attempt_preserved_not_mistaken_for_inference(tmp_path):
    path = tmp_path / 'R118_PARALLEL_LAUNCH_ATTEMPT.json'
    path.write_text('{"failed": true}')
    before = path.read_bytes()
    recovery.no_inference(tmp_path)
    assert path.read_bytes() == before


def test_recovery_requires_empty_CVD_before_verifying_or_launching(monkeypatch):
    monkeypatch.setenv('CUDA_VISIBLE_DEVICES', 'GPU-fixture')
    with pytest.raises(ValueError, match='CPU_launcher_requires_empty_CVD_at_exec'):
        recovery.verify({}, Mock())


@pytest.mark.parametrize('clear', [True, False])
def test_recovery_uses_new_attempt_and_leaves_old_scan_untouched(tmp_path, monkeypatch, clear):
    root = tmp_path / 'life'
    root.mkdir()
    old = root / 'R118_PARALLEL_LAUNCH_ATTEMPT.json'
    old.write_text('{"original":true}')
    scan = root / 'SCAN_original.json'
    scan.write_text('{"clear":false}')
    originals = {path: path.read_bytes() for path in (old, scan)}
    directory = root / 'R118_STARTUP_RECOVERY_test'
    request = dict(attempt_directory=str(directory), failed_dispatch=dict(sha256='old'), plan={})
    plan = dict(uuid='GPU-fixture', parallel_source='/frozen', shared_learner=dict(branch='A1'))
    monkeypatch.setenv('CUDA_VISIBLE_DEVICES', '')
    monkeypatch.setenv('R118_PARALLEL_SESSION', '/new/SESSION.json')
    monkeypatch.setenv('R118_PARALLEL_SESSION_SHA256', 'new')
    monkeypatch.setenv('R118_PARALLEL_BRANCH', 'A1')
    monkeypatch.setattr(recovery, 'verify', lambda *args: (root, plan))
    backend = SimpleNamespace(fresh_session=lambda *args: (
        dict(startup_deadline_unix=10**12, source_files={str(Path(recovery.__file__).resolve()):
             recovery.digest(recovery.__file__)}), tmp_path / 'control'),
        read=lambda path: dict(session_sha256='new', identity={}), live_identity=lambda identity: None)
    runtime = SimpleNamespace(MODULE='frozen.route', boundary=SimpleNamespace(
        prior=SimpleNamespace(identity=lambda pid: dict(pid=pid))))
    calls = []

    def scanner(command, **kwargs):
        assert recovery.os.environ['CUDA_VISIBLE_DEVICES'] == ''
        assert 'CUDA_VISIBLE_DEVICES=' in command
        calls.append(command)
        return SimpleNamespace(returncode=0, stdout=json.dumps(dict(clear=clear)).encode(), stderr=b'')

    monkeypatch.setattr(recovery.subprocess, 'run', scanner)
    process = Mock(return_value=SimpleNamespace(pid=123))
    monkeypatch.setattr(recovery.subprocess, 'Popen', process)
    if clear:
        recovery.launch(request, runtime, backend)
        assert process.call_args.kwargs['env']['CUDA_VISIBLE_DEVICES'] == 'GPU-fixture'
        assert (directory / 'DISPATCH.json').exists()
    else:
        with pytest.raises(ValueError, match='fresh_privileged'):
            recovery.launch(request, runtime, backend)
        process.assert_not_called()
        assert (directory / 'FAILED.json').exists()
        with pytest.raises(FileExistsError):
            recovery.launch(request, runtime, backend)
    assert len(calls) == 2
    assert {path: path.read_bytes() for path in originals} == originals


def test_write_new_never_overwrites_failure(tmp_path):
    path = tmp_path / 'FAILED.json'
    recovery.write_new(path, dict(failure='original'))
    with pytest.raises(FileExistsError):
        recovery.write_new(path, dict(failure='replacement'))
    assert json.loads(path.read_text()) == dict(failure='original')


def test_full_verification_preserves_actual_refs_and_rejects_new_charges(tmp_path, monkeypatch):
    monkeypatch.setenv('CUDA_VISIBLE_DEVICES', '')
    root = tmp_path / 'root'
    root.mkdir()

    def reference(name, value):
        path = root / name
        recovery.write_new(path, value)
        return dict(path=str(path), sha256=recovery.digest(path))

    plan = dict(route_boundary_release={}, parallel_stage=dict(authorization={}),
                shared_learner=dict(branch='F1'))
    plan_ref = reference('R118_PARALLEL_PLAN.json', plan)
    session_ref = reference('SESSION.json', dict(owners=dict(F1=dict(
        bootstrap_path=str(root / 'R118_PARALLEL_FRESH_BOOTSTRAP.json')))))
    failure_ref = reference('FAILED.json', dict(session_sha256=session_ref['sha256'],
        retry_allowed=False, spawned=dict(F1=2147483647)))
    ledger = root / 'RESERVATIONS.jsonl'
    ledger.write_text('{"kind":"NATIVE","number":425}\n')
    request = dict(authorized_by_Main=True, scope='PRE_INFERENCE_STARTUP_ONLY',
        expires_unix=10**12, root=str(root), plan=plan_ref, preserved_failures=[failure_ref],
        failed_dispatch=session_ref, failed_dispatch_terminal=failure_ref,
        reservations_sha256=recovery.digest(ledger), old_attempt=None)
    runtime = SimpleNamespace(PLAN='R118_PARALLEL_PLAN.json',
        boundary=SimpleNamespace(TRAIN_END=10**12+180, released=Mock()),
        verify_plan=Mock(return_value=plan), verify_retirements=Mock(),
        validate_broker_binding=Mock(), bound=lambda value: value)
    assert recovery.verify(request, runtime) == (root, plan)
    runtime.verify_plan.assert_called_once_with(root, gpu=False)
    ledger.write_text(ledger.read_text()+'{"kind":"NATIVE","number":426}\n')
    with pytest.raises(ValueError, match='no_new_charges'):
        recovery.verify(request, runtime)
