from copy import deepcopy

import pytest

from gpu import orch_r110_admission as admission


def fixture():
    identity = dict(pid=41, uid=1000, start_ticks='555', boot_id='boot', command_sha256='first')
    samples = [dict(identity, command_sha256=command, executable_identity=[1, 2],
        target_open=False, visibility_complete=True, cvd=None) for command in ('first', 'second', 'second')]
    process = dict(identity, pinned_identity=identity, target_device_open=False, cvd=None)
    report = dict(scanner_euid=0, gpu=dict(uuid='GPU-target', memory_used_mib=0), compute_processes=[],
        processes=[process], blocking_reasons=['process_identity_drift:41', 'minor_scan_identity_changed:41'], clear=False)
    return report, {41: samples}


def test_argv_only_drift_keeps_full_original_evidence():
    report, samples = fixture()
    before = deepcopy(report)
    result = admission.reconcile(report, samples)
    assert result['clear'] and result['blocking_reasons'] == []
    assert result['unreconciled_blocking_reasons'] == before['blocking_reasons']
    assert result['argv_only_non_gpu_processes'] == [41]
    assert report == before and result['identity_observations']['41'] == samples[41]


@pytest.mark.parametrize('field,value', [('pid', 42), ('uid', 0), ('start_ticks', '556'),
    ('boot_id', 'other'), ('executable_identity', [1, 3]), ('target_open', True),
    ('visibility_complete', False), ('cvd', 'GPU-target')])
def test_kernel_reuse_or_any_target_visibility_stays_blocked(field, value):
    report, samples = fixture()
    samples[41][1][field] = value
    assert not admission.reconcile(report, samples)['clear']


@pytest.mark.parametrize('reason', ['open_device_pid:41', 'uuid_reservation:41',
    'unknown_minor_process_visibility:41:PermissionError', 'process_identity_drift:42'])
def test_non_argv_blockers_never_removed(reason):
    report, samples = fixture()
    report['blocking_reasons'].append(reason)
    result = admission.reconcile(report, samples)
    assert not result['clear'] and reason in result['blocking_reasons']


def test_no_argv_change_or_incomplete_samples_never_reconciled():
    report, samples = fixture()
    assert not admission.reconcile(report, {41: samples[41][:2]})['clear']
    for sample in samples[41]:
        sample['command_sha256'] = 'same'
    assert not admission.reconcile(report, samples)['clear']


def test_busy_target_or_process_compute_stays_blocked():
    report, samples = fixture()
    report['gpu']['memory_used_mib'] = 1
    assert not admission.reconcile(report, samples)['clear']
    report['gpu']['memory_used_mib'] = 0
    report['compute_processes'] = [dict(pid=41, gpu_uuid='GPU-other')]
    assert not admission.reconcile(report, samples)['clear']
