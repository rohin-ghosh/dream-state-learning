"""Scanner-race recovery never waives occupancy or retries a native call."""

from copy import deepcopy

import pytest

from gpu import orch_r107_continual_capability_admit as recovery


def snapshot():
    return dict(scanner_euid=0, blocking_reasons=['process_identity_drift:4583'],
        gpu=dict(memory_used_mib=0, utilization_percent=0), compute_processes=[])


def test_exact_process_race_can_be_rescanned():
    assert recovery.transient(snapshot())


@pytest.mark.parametrize('field,value', [
    ('scanner_euid', 1), ('blocking_reasons', ['open_device_pid:1']),
    ('blocking_reasons', ['unknown_visibility:1']), ('blocking_reasons', []),
    ('compute_processes', [dict(gpu_uuid=recovery.run.GPU_UUID, pid=1)]),
    ('gpu', dict(memory_used_mib=1, utilization_percent=0)),
    ('gpu', dict(memory_used_mib=0, utilization_percent=1)),
])
def test_no_ownership_or_visibility_waiver(field, value):
    report = deepcopy(snapshot())
    report[field] = value
    assert not recovery.transient(report)


@pytest.mark.parametrize('already_dispatched', ['LAUNCH.json', 'readout'])
def test_any_dispatch_prevents_recovery(tmp_path, already_dispatched):
    (tmp_path / 'LAUNCH_ONCE').mkdir()
    recovery.run.write(tmp_path / 'FULL_SCAN.json', snapshot())
    recovery.eligible(tmp_path)
    if already_dispatched == 'readout':
        (tmp_path / already_dispatched).mkdir()
    else:
        recovery.run.write(tmp_path / already_dispatched, {})
    with pytest.raises(ValueError, match='zero_dispatch'):
        recovery.eligible(tmp_path)


def test_missing_original_failure_cannot_create_new_launch(tmp_path):
    with pytest.raises(ValueError, match='zero_dispatch'):
        recovery.eligible(tmp_path)


def test_recovery_requires_pinned_host_hash_before_reading_plan(tmp_path, monkeypatch):
    monkeypatch.setenv('CUDA_VISIBLE_DEVICES', '')
    monkeypatch.setattr(recovery.run, 'host_identity', lambda: '0' * 64)
    with pytest.raises(ValueError, match='exact_cpu_a100'):
        recovery.recover(tmp_path, tmp_path / 'unused_publication.json')
