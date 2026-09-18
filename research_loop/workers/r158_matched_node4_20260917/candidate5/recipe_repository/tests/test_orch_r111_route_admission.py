from copy import deepcopy

from gpu import orch_r111_route_admission as admission
from test_orch_r110_admission import fixture


def test_idle_one_mib_argv_drift_preserves_exact_memory_and_evidence():
    report, observations = fixture()
    report['gpu']['memory_used_mib'] = 1
    before = deepcopy(report)
    result = admission.reconcile(report, observations)
    assert result['clear']
    assert result['gpu']['memory_used_mib'] == 1
    assert report == before
    assert result['unreconciled_blocking_reasons'] == before['blocking_reasons']


def test_resource_visibility_and_identity_unknowns_never_waived():
    for reason in ('open_device_pid:41', 'uuid_reservation:41', 'unknown_visibility:41'):
        report, observations = fixture()
        report['gpu']['memory_used_mib'] = 1
        report['blocking_reasons'].append(reason)
        assert not admission.reconcile(report, observations)['clear']
    for mutate in ('memory', 'cvd', 'fd', 'identity', 'compute'):
        report, observations = fixture()
        report['gpu']['memory_used_mib'] = 1
        if mutate == 'memory': report['gpu']['memory_used_mib'] = 2
        if mutate == 'cvd': observations[41][1]['cvd'] = 'GPU-target'
        if mutate == 'fd': observations[41][1]['target_open'] = True
        if mutate == 'identity': observations[41][1]['start_ticks'] = 'different'
        if mutate == 'compute': report['compute_processes'] = [dict(pid=41, gpu_uuid='GPU-other')]
        assert not admission.reconcile(report, observations)['clear']
