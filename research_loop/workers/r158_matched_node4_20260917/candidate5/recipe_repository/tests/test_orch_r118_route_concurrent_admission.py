from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import pytest

from gpu import orch_r118_route_concurrent_admission as route
from gpu import orch_math_feedback_uptake_r118_argv_admission as argv
from gpu import orch_admission_transient_exit as transient
from tests.test_orch_admission_transient_exit import FakeSession, report_fixture


MATH_SOURCE = Path(__file__).resolve().parents[1] / 'dependencies/orch_math_feedback_uptake_r118_preinfer.py'
if not MATH_SOURCE.exists():
    MATH_SOURCE = Path(__file__).resolve().parents[1] / 'gpu/orch_math_feedback_uptake_r118_preinfer.py'


def test_exact_math_binding_retains_both_exit_proofs():
    evidence = []
    report = report_fixture()

    def scanner():
        report['created_utc'] = datetime.now(timezone.utc).isoformat()
        return report

    binding = route.proof_binding(MATH_SOURCE.read_text(), transient, lambda kind, doc: evidence.append((kind, doc)))
    with patch.object(transient, '_ProcSession', return_value=FakeSession()), patch.object(route.os, 'geteuid', return_value=0):
        result = binding(scanner)
    assert result['clear']
    assert evidence[0][0] == 'PIDFD_ENVELOPE'
    decision = evidence[0][1]['reconciliation']['decisions'][0]
    assert decision['first_observation']['proven'] and decision['final_observation']['proven']


@pytest.mark.parametrize('case', ['live', 'reuse', 'fd', 'cvd', 'compute', 'unknown', 'reappear'])
def test_no_live_foreign_or_unknown_waiver(case):
    session = FakeSession()
    report = report_fixture()
    if case == 'live':
        session.observations = [dict(proven=False, disposition='pid_present')]
    elif case == 'reuse':
        report['processes'][0]['pinned_identity']['start_ticks'] = '999'
    elif case == 'fd':
        report['processes'][0]['target_device_open'] = True
    elif case == 'cvd':
        report['processes'][0]['cvd'] = 'GPU-target'
    elif case == 'compute':
        report['compute_processes'].append(dict(pid=101))
    elif case == 'unknown':
        report['blocking_reasons'].append('unknown_process_visibility:999')
    else:
        session.observations = [session.prove_exit(session.pins[101]), dict(proven=False, disposition='reappeared')]

    def scanner():
        report['created_utc'] = datetime.now(timezone.utc).isoformat()
        return report

    saved = []
    binding = route.proof_binding(MATH_SOURCE.read_text(), transient, lambda kind, doc: saved.append(doc))
    with patch.object(transient, '_ProcSession', return_value=session), patch.object(route.os, 'geteuid', return_value=0):
        result = binding(scanner)
    assert not result['clear']
    assert saved


def test_forged_envelope_is_preserved_before_rejection():
    envelope = dict(schema='wrong')
    fake = SimpleNamespace(reconcile_scan=lambda scanner: envelope, TRANSIENT_REASONS=transient.TRANSIENT_REASONS)
    saved = []
    binding = route.proof_binding(MATH_SOURCE.read_text(), fake, lambda kind, doc: saved.append(deepcopy(doc)))
    with patch.object(route.os, 'geteuid', return_value=0), pytest.raises(ValueError, match='schema'):
        binding(lambda: None)
    assert saved == [envelope]


@pytest.mark.parametrize('bad', [False, True])
def test_argv_rejected_samples_never_dropped(bad):
    identity = dict(pid=3159, uid=0, start_ticks='2046', boot_id='boot', command_sha256='first')
    samples = [dict(identity, command_sha256=command, executable_identity=[1, 2],
        target_open=False, visibility_complete=True, cvd=None) for command in ('first', 'second', 'first')]
    if bad:
        samples[1]['target_open'] = True
    report = dict(scanner_euid=0, gpu=dict(uuid='GPU-target', memory_used_mib=1), compute_processes=[],
        processes=[dict(identity, pinned_identity=deepcopy(identity), target_device_open=False, cvd=None)],
        blocking_reasons=['process_identity_drift:3159'], clear=False)
    result = route.keep_observations(argv, report, {3159: samples})
    assert result['clear'] is (not bad)
    assert result['all_identity_observations']['3159'] == samples
    assert result['argv_original_report'] == report


def test_fixed_window_and_both_failed_sessions_required():
    request = dict(expires_unix=route.STARTUP_END, failed_dispatch=dict(sha256=next(iter(route.FAILED_SESSIONS))),
                   preserved_failures=[dict(sha256=value) for value in route.FAILED_SESSIONS])
    with patch.object(route.time, 'time', return_value=route.STARTUP_END-1):
        route.validate_window(request)
        with pytest.raises(ValueError, match='no_sliding'):
            route.validate_window(dict(request, expires_unix=route.STARTUP_END+1))
        with pytest.raises(ValueError, match='both_failed'):
            route.validate_window(dict(request, preserved_failures=[]))
        old = deepcopy(request)
        updated = route.bind_window(request, route.STARTUP_END)
        assert updated['expires_unix'] == route.STARTUP_END and request == old
        with pytest.raises(ValueError, match='fixed_1635'):
            route.bind_window(request, route.STARTUP_END+1)


def test_failed_session_blocks_before_model_spawn(monkeypatch, tmp_path):
    monkeypatch.setenv('R118_PARALLEL_SESSION', '/new')
    monkeypatch.setenv('R118_PARALLEL_SESSION_SHA256', 'new')
    (tmp_path / 'FAILED.json').write_text('{}')
    backend = SimpleNamespace(fresh_session=lambda *args: (dict(startup_deadline_unix=route.STARTUP_END), tmp_path))
    with pytest.raises(ValueError, match='before_model_spawn'):
        route.session_live(backend)
