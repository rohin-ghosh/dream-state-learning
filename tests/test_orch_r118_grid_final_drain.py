import os
from pathlib import Path
import signal
import subprocess
import sys
import time

import pytest

from gpu import orch_r118_grid_final as final
from gpu import orch_r118_grid_final_drain as drain


@pytest.mark.parametrize('now', [drain.DRAIN - .001, drain.LATEST, drain.LATEST + 1])
def test_never_stop_healthy_life_before_original_cutoff(tmp_path, monkeypatch, now):
    monkeypatch.setattr(drain, 'discover', lambda unused: pytest.fail('no process inspection before window'))
    with pytest.raises(ValueError, match='1655_deadline'):
        drain.stop({}, tmp_path, final.write, clock=lambda: now)


@pytest.mark.parametrize('key', ['pid', 'uid', 'start_ticks', 'boot_id'])
def test_pid_reuse_uid_boot_or_start_drift_not_same_process(key):
    expected = dict(pid=1, uid=2, start_ticks='3', boot_id='4')
    assert not drain.same_process(dict(expected, **{key: 'changed'}), expected)


def test_cpu_real_pidfd_stop_only_pinned_child_preserves_foreign(tmp_path, monkeypatch):
    if not hasattr(os, 'pidfd_open'):
        pytest.skip('Linux pidfds required')
    child = subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(60)'])
    foreign = subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(60)'])
    root = tmp_path / 'branch'
    root.mkdir()
    for name in ('CONFIG.json', 'LEDGER.jsonl', 'CARRY.json', 'shared_repair_v1/LOADED.json'):
        path = root / name
        path.parent.mkdir(exist_ok=True)
        path.write_text('{}')
    try:
        time.sleep(.05)
        record = drain.identity(child.pid)
        record['command_sha256'] = final.sha(Path('/proc') / str(child.pid) / 'cmdline')

        def discover(unused):
            if child.poll() is not None:
                return []
            observed = drain.identity(child.pid)
            return [] if observed['state'] == 'Z' else [record]

        monkeypatch.setattr(drain, 'discover', discover)
        receipt = drain.stop(dict(branch_root=str(root)), tmp_path / 'drain', final.write,
                             clock=lambda: drain.DRAIN + 1)
        assert receipt['status'] == 'RELEASED'
        assert {item['pid'] for item in receipt['signals']} == {child.pid}
        assert foreign.poll() is None
        assert (root / 'LEDGER.jsonl').read_text() == '{}'
        assert not (root / 'R118_SHARED_REPAIR_TERMINAL.json').exists()
    finally:
        for process in (child, foreign):
            if process.poll() is None:
                process.terminate()
            process.wait(timeout=5)


def test_pidfd_open_failure_does_not_claim_release(tmp_path, monkeypatch):
    monkeypatch.setattr(drain, 'discover', lambda unused: [dict(pid=1)])
    monkeypatch.setattr(os, 'pidfd_open', lambda unused: (_ for unused in ()).throw(ProcessLookupError()))
    with pytest.raises(ProcessLookupError):
        drain.stop({}, tmp_path, final.write, clock=lambda: drain.DRAIN + 1)
    assert not (tmp_path / 'RELEASE.json').exists()


def test_same_user_foreign_command_is_not_an_owned_grid_actor(tmp_path):
    plan = dict(branch_root=str(tmp_path), runtime=str(Path.cwd()), uuid='GPU-test')
    with pytest.raises(ValueError, match='exact_owned_branch_command'):
        drain.inspect_owned(os.getpid(), plan)


def test_command_changed_after_pin_gets_no_signal(monkeypatch):
    record = drain.identity(os.getpid())
    record['command_sha256'] = 'changed'
    descriptor = os.pidfd_open(os.getpid())
    monkeypatch.setattr(signal, 'pidfd_send_signal', lambda *args: pytest.fail('no signal on changed command'))
    try:
        with pytest.raises(ValueError, match='no_command_exec_drift'):
            drain.send(descriptor, record, signal.SIGTERM)
    finally:
        os.close(descriptor)


def test_pid_reuse_after_pidfd_open_does_not_even_send_cleanup_continue(tmp_path, monkeypatch):
    record = drain.identity(os.getpid())
    record['command_sha256'] = final.sha(Path('/proc') / str(os.getpid()) / 'cmdline')
    monkeypatch.setattr(drain, 'discover', lambda unused: [record])
    monkeypatch.setattr(drain, 'identity', lambda unused: dict(record, start_ticks='reused'))
    monkeypatch.setattr(signal, 'pidfd_send_signal', lambda *args: pytest.fail('foreign cleanup signal forbidden'))
    with pytest.raises(ValueError, match='same_process_after_pidfd_open'):
        drain.stop({}, tmp_path, final.write, clock=lambda: drain.DRAIN + 1)
    assert not (tmp_path / 'RELEASE.json').exists()
