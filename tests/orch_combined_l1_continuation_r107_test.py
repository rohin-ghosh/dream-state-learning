from unittest.mock import Mock

import pytest

from gpu import orch_combined_l1_continuation_r107 as continuation


def test_extension_fixed_deadlines_not_restart_clock():
    previous = dict(started_unix=123, original_started_unix=100, readout_calls=1760)
    now = continuation.utc('2026-09-15T07:20:00+00:00')
    value = continuation.continuation_clock(previous, now, continuation.run.LEASE_END)
    assert value['started_unix'] == 123 and value['original_started_unix'] == 100
    assert value['training_deadline_unix'] == continuation.utc('2026-09-15T08:00:00+00:00')
    assert value['hard_deadline_unix'] == continuation.utc('2026-09-15T09:03:00+00:00')
    assert value['terminal_calls_remaining'] == 416 and value['readout_calls'] == 1760
    assert value['total_readout_calls_including_base'] == 1824
    assert value['extra_physical_off_recovery_updates'] == 117
    assert previous == dict(started_unix=123, original_started_unix=100, readout_calls=1760)


@pytest.mark.parametrize('now,lease',[("2026-09-15T07:51:00+00:00", 1e20),
    ("2026-09-15T05:00:00+00:00", 1e20), ("2026-09-15T07:20:00+00:00", 1)])
def test_expired_or_overbudget_or_lease_violation(now,lease):
    with pytest.raises(AssertionError):
        continuation.continuation_clock({},continuation.utc(now),lease)


def test_exact_existing_pair_and_five_gpu_topology():
    assert continuation.UPDATE == 6628 and set(continuation.COMMITS)=={'FULL','OFF'}
    assert continuation.run.TOPOLOGY == {'FULL':(0,2,6),'OFF':(1,3)}
    assert set(continuation.run.DEVICES)=={0,1,2,3,6}


def test_no_launch_without_publication(tmp_path,monkeypatch):
    monkeypatch.setenv('CUDA_VISIBLE_DEVICES','')
    monkeypatch.setattr(continuation.os,'geteuid',lambda:1000)
    directory=tmp_path/continuation.SEGMENT; directory.mkdir()
    continuation.run.write(directory/'READY.json',{})
    spawned=Mock()
    monkeypatch.setattr(continuation.subprocess,'Popen',spawned)
    with pytest.raises(FileNotFoundError):
        continuation.launch(tmp_path)
    assert not spawned.called and not (directory/'STARTED.json').exists()


def test_settling_requires_zero_memory_and_no_matching_compute():
    report=dict(blocking_reasons=['device_not_idle'],gpu=dict(memory_used_mib=0,uuid='owned'),compute_processes=[])
    assert continuation.settling_only(report)
    assert not continuation.settling_only(dict(report,compute_processes=[dict(gpu_uuid='owned')]))
    assert not continuation.settling_only(dict(report,gpu=dict(memory_used_mib=1,uuid='owned')))


def test_transient_failure_preserved_until_actual_clear(tmp_path,monkeypatch):
    failed=dict(clear=False,blocking_reasons=['device_not_idle'],gpu=dict(memory_used_mib=0,uuid='own'),compute_processes=[])
    clear=dict(failed,clear=True,blocking_reasons=[])
    monkeypatch.setattr(continuation.run,'scan',Mock(side_effect=[failed,clear]))
    monkeypatch.setattr(continuation.time,'sleep',lambda seconds:None)
    continuation.admit(tmp_path,[0],'test')
    assert continuation.run.read(tmp_path/continuation.SEGMENT/'ADMISSIONS/test_0_000.json') == failed
    assert continuation.run.read(tmp_path/continuation.SEGMENT/'ADMISSIONS/test_0_001.json') == clear
