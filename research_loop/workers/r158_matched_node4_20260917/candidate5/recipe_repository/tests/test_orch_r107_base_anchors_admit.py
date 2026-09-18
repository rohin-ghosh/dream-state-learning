"""Fail-closed admission retries do not add model reservations or weaken scans."""

import pytest

from gpu import orch_r107_base_anchors_admit as recovery


def test_zero_dispatch_transient_failure_required(tmp_path):
    with pytest.raises(ValueError,match='zero_dispatch'):
        recovery.eligible(tmp_path)
    (tmp_path/'LAUNCH_ONCE').mkdir()
    recovery.run.write(tmp_path/'ADMISSIONS/000.json',dict(scanner_euid=0,
        blocking_reasons=['process_identity_drift:1'],gpu=dict(memory_used_mib=0,utilization_percent=0),compute_processes=[]))
    recovery.eligible(tmp_path)
    (tmp_path/'readout').mkdir()
    with pytest.raises(ValueError,match='zero_dispatch'):
        recovery.eligible(tmp_path)


@pytest.mark.parametrize('reason',['open_device_pid:1','unknown_visibility:1','uuid_reservation:1'])
def test_real_block_not_eligible(tmp_path,reason):
    (tmp_path/'LAUNCH_ONCE').mkdir()
    recovery.run.write(tmp_path/'ADMISSIONS/000.json',dict(scanner_euid=0,
        blocking_reasons=[reason],gpu=dict(memory_used_mib=0,utilization_percent=0),compute_processes=[]))
    with pytest.raises(ValueError,match='transient'):
        recovery.eligible(tmp_path)


def test_wrong_host_hash_rejected_before_recovery(tmp_path,monkeypatch):
    monkeypatch.setattr(recovery.run.ownership,'host_identity',lambda:'0'*64)
    with pytest.raises(ValueError,match='pinned_host'):
        recovery.recover(tmp_path,tmp_path/'unused.json')
