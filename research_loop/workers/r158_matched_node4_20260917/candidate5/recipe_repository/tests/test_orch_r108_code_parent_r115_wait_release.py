from pathlib import Path
import time

import pytest

from gpu import orch_r108_code_parent_r115_wait_release as waiter


def test_cpu_waiter_rejects_other_physical_before_wait(tmp_path, monkeypatch):
    monkeypatch.setenv('CUDA_VISIBLE_DEVICES', '')
    monkeypatch.setattr(waiter.guard, 'verify', lambda root: {'physical': 2})
    with pytest.raises(ValueError, match='cpu_waiter_A3_only'):
        waiter.wait_release(tmp_path)
    assert not (tmp_path / 'WAIT_RELEASE_ONCE').exists()


@pytest.mark.parametrize('release', [dict(exited=False, physical=6, receiver='Cicero'),
    dict(exited=True, physical=7, receiver='Cicero'),
    dict(exited=True, physical=6, receiver='other')])
def test_release_must_be_explicit_correct_owner_and_slot(tmp_path, monkeypatch, release):
    previous = tmp_path / 'old'
    previous.mkdir()
    waiter.guard.run.write(previous / 'RELEASE.json', release)
    waiter.guard.run.write(tmp_path / 'ADMISSION_SOURCE_SHA256.json', {})
    monkeypatch.setenv('CUDA_VISIBLE_DEVICES', '')
    monkeypatch.setattr(waiter.guard, 'verify', lambda root:
        dict(physical=6, hard_deadline_unix=time.time()+3600))
    monkeypatch.setattr(waiter, 'Path', lambda value: previous if str(value).endswith('/R115_HANDOFF') else Path(value))
    monkeypatch.setattr(waiter.subprocess, 'Popen', lambda *args, **kwargs:
        pytest.fail('No process launch before valid owner release'))
    with pytest.raises(ValueError, match='explicit_owner_cycle_release'):
        waiter.wait_release(tmp_path)
    assert not (tmp_path / 'PREDECESSOR_RELEASE.json').exists()
