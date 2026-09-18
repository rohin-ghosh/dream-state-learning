from copy import deepcopy
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import threading
import time

import pytest

from gpu import orch_r111_shared_cutoff as guard


def put(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value))


@pytest.fixture
def scenario():
    peers = {branch: dict(bounds=dict(native_calls=100, parent_calls=40, cycles=43)) for branch in guard.BRANCHES}
    control = dict(peers=peers, drain_unix=guard.DRAIN, freeze_unix=guard.CUTOFF - 60)
    observations = {branch: dict(counts=dict(native=1, parent=1), native=dict(pid=123),
                                terminal=None, completed_cycle=2) for branch in guard.BRANCHES}
    snapshot = dict(state=dict(generation=0), present=['F1'], sleep_started=False, sleep_complete=False)
    return control, snapshot, observations, {}


def test_healthy_lanes_keep_collecting(scenario):
    control, snapshot, observations, memory = scenario
    assert guard.decision(control, snapshot, observations, guard.DRAIN - 3600, memory)['action'] == 'MONITOR'
    assert not memory.get('drain_generation')


def test_scheduled_review_drains_without_interrupting_current_sleep(scenario):
    control, snapshot, observations, memory = scenario
    snapshot.update(present=list(guard.BRANCHES), sleep_started=True)
    result = guard.decision(control, snapshot, observations, guard.DRAIN, memory)
    assert result['action'] == 'DRAIN' and result['target_generation'] == 1
    snapshot['state']['generation'] = 1
    snapshot['sleep_started'] = False
    assert guard.decision(control, snapshot, observations, guard.DRAIN + 30, memory)['action'] == 'DRAIN_STOP'


@pytest.mark.parametrize('label,value', [('native', 100), ('parent', 40)])
def test_exhausted_missing_peer_cancels_barrier_without_reset(scenario, label, value):
    control, snapshot, observations, memory = scenario
    observations['F2']['counts'][label] = value
    original = deepcopy(control)
    action = guard.decision(control, snapshot, observations, guard.DRAIN - 100, memory)
    assert action['action'] == 'STOP'
    assert action['peers']['F2'] == 'ORIGINAL_' + label.upper() + '_CAP'
    assert control == original


def test_final_cycle_exhaustion_is_not_a_score_criterion(scenario):
    control, snapshot, observations, memory = scenario
    observations['F2']['completed_cycle'] = 43
    assert guard.decision(control, snapshot, observations, guard.DRAIN - 10, memory)['peers']['F2'] == 'ORIGINAL_CYCLE_CAP'


def test_submitted_exhausted_peer_allows_current_shared_sleep(scenario):
    control, snapshot, observations, memory = scenario
    snapshot['present'].append('F2')
    observations['F2']['counts']['native'] = 100
    assert guard.decision(control, snapshot, observations, guard.DRAIN - 10, memory)['action'] == 'DRAIN'


def test_actual_terminal_not_missing_provider_reply_ends_unavailable_peer(scenario):
    control, snapshot, observations, memory = scenario
    observations['A3']['terminal'] = dict(path='real-era-terminal', sha256='fixture')
    action = guard.decision(control, snapshot, observations, guard.DRAIN - 10, memory)
    assert action['peers'] == {'A3': 'ACTUAL_ERA_TERMINAL'}


def test_crash_absence_has_bounded_recovery_grace(scenario):
    control, snapshot, observations, memory = scenario
    observations['F4']['native'] = None
    start = guard.DRAIN - 3600
    assert guard.decision(control, snapshot, observations, start, memory)['action'] == 'MONITOR'
    assert guard.decision(control, snapshot, observations, start + 299, memory)['action'] == 'MONITOR'
    assert guard.decision(control, snapshot, observations, start + 300, memory)['peers']['F4'] == 'NATIVE_ABSENCE'


def test_repaired_peer_clears_absence_timer(scenario):
    control, snapshot, observations, memory = scenario
    observations['F4']['native'] = None
    start = guard.DRAIN - 3600
    guard.decision(control, snapshot, observations, start, memory)
    observations['F4']['native'] = dict(pid=456)
    assert guard.decision(control, snapshot, observations, start + 299, memory)['action'] == 'MONITOR'
    assert 'F4' not in memory['missing_since']


def test_deadline_fuse_overrides_alive_peers_and_active_sleep(scenario):
    control, snapshot, observations, memory = scenario
    snapshot.update(present=list(guard.BRANCHES), sleep_started=True)
    assert guard.decision(control, snapshot, observations, guard.CUTOFF - 60, memory)['reason'] == 'COMMON_TRAIN_DEADLINE'


def test_math_native_bound_never_extended_for_final(scenario):
    control, snapshot, observations, memory = scenario
    peer = dict(bounds=dict(native_end_unix=1789491540, hard_end_unix=1789491720))
    assert guard.classify(peer, observations['F2'], 1789491540, {}, 'F2') == 'ORIGINAL_CLOCK_BOUND'
    assert guard.CUTOFF < 1789491540 < guard.FINAL


def test_unknown_counter_is_not_reported_as_zero_exhaustion(scenario):
    control, snapshot, observations, memory = scenario
    observations['F4'].update(native=None, counts=dict(native=None, parent=None))
    assert guard.decision(control, snapshot, observations, guard.DRAIN - 1000, memory)['action'] == 'MONITOR'


def test_selected_grid_repair_terminal_preserves_failed_historical_marker(tmp_path):
    put(tmp_path / 'SHARED_TERMINAL.json', dict(status='FAILED'))
    (tmp_path / 'LEDGER.jsonl').write_text('')
    peer = dict(root=str(tmp_path), family='grid', terminal='R118_SHARED_REPAIR_TERMINAL.json',
                loaded='shared_repair_v1/LOADED.json')
    before = (tmp_path / 'SHARED_TERMINAL.json').read_bytes()
    assert guard.peer_observation(peer, {})['terminal'] is None
    assert (tmp_path / 'SHARED_TERMINAL.json').read_bytes() == before
    put(tmp_path / 'R118_SHARED_REPAIR_TERMINAL.json', dict(status='FAILED'))
    assert guard.peer_observation(peer, {})['terminal'] == guard.ref(tmp_path / 'R118_SHARED_REPAIR_TERMINAL.json')


def test_peer_arrival_race_prevents_obsolete_stop(tmp_path, monkeypatch):
    control = dict(directory=str(tmp_path), common=str(tmp_path), routes={})
    monkeypatch.setattr(guard, 'common_snapshot', lambda unused: dict(state=dict(generation=0),
        present=list(guard.BRANCHES), sleep_started=True))
    trigger = dict(reason='PEER_CANNOT_COMPLETE_BARRIER', generation=0, peers={'F2': 'terminal'})
    assert guard.stop_routes(control, trigger['reason'], trigger=trigger) is False
    assert not (tmp_path / 'COMPLETED.json').exists()


def test_fuse_stops_even_when_common_STATE_is_unreadable(tmp_path, monkeypatch):
    control = dict(directory=str(tmp_path), common=str(tmp_path / 'absent'), routes={'F1': {}, 'A1': {}})
    stopped = []
    monkeypatch.setattr(guard, 'terminate_tree', lambda spec, output, reason: stopped.append(str(output)) or dict(status='RELEASED'))
    with pytest.raises(FileNotFoundError):
        guard.stop_routes(control, 'COMMON_TRAIN_DEADLINE')
    assert len(stopped) == 2
    assert (tmp_path / 'F1/DISPOSITION.json').exists()
    assert not (tmp_path / 'TERMINAL.json').exists()


def test_both_route_shutdowns_start_in_parallel_not_behind_peer_teardown(tmp_path, monkeypatch):
    rendezvous = threading.Barrier(2)
    calls = []
    control = dict(directory=str(tmp_path), common=str(tmp_path), routes={'A1': {}, 'F1': {}})
    def terminate(spec, output, reason):
        rendezvous.wait(timeout=2)
        calls.append(output.parent.name)
        return dict(status='RELEASED')
    monkeypatch.setattr(guard, 'terminate_tree', terminate)
    monkeypatch.setattr(guard, 'checkpoint_evidence', lambda unused: dict(preserved=True))
    assert guard.stop_routes(control, 'COMMON_TRAIN_DEADLINE') is True
    assert set(calls) == {'F1', 'A1'}


def test_scope_rejects_foreign_branch_before_any_signals():
    with pytest.raises(ValueError, match='scope'):
        guard.validate(dict(schema='R118_ROUTE_CUTOFF_V1', signals_only=['F1', 'F4']))


def test_pid_reuse_identity_prevents_signal(monkeypatch):
    called = []
    monkeypatch.setattr(guard, 'alive', lambda unused: False)
    monkeypatch.setattr(guard.signal, 'pidfd_send_signal', lambda *args: called.append(args))
    with pytest.raises(ValueError, match='identity_before_signal'):
        guard.signal_bound(123, dict(pid=456), signal.SIGTERM)
    assert not called


def test_checkpoint_evidence_preserves_exact_optimizer_and_detects_corruption(tmp_path):
    checkpoint = tmp_path / 'checkpoint.json'
    optimizer = tmp_path / 'optimizer.bin'
    put(checkpoint, dict(complete=True))
    optimizer.write_bytes(b'original optimizer')
    state = dict(generation=0, checkpoint=dict(path=str(checkpoint), path_sha256=guard.sha(checkpoint),
        optimizer_path=str(optimizer), optimizer_path_sha256=guard.sha(optimizer)))
    put(tmp_path / 'STATE.json', state)
    put(tmp_path / 'generation_000000/sleep/START.json', dict(generation=0))
    before = (tmp_path / 'STATE.json').read_bytes()
    proof = guard.checkpoint_evidence(tmp_path)
    assert proof['incomplete_updates_not_committed'] is True
    assert (tmp_path / 'STATE.json').read_bytes() == before
    optimizer.write_bytes(b'corrupt')
    with pytest.raises(ValueError, match='committed_checkpoint_bytes'):
        guard.checkpoint_evidence(tmp_path)


def test_serial_workload_uses_timed_counts_not_invented_row_timestamps(tmp_path):
    folder = tmp_path / 'generation_000000/sleep'
    put(folder / 'START.json', dict(started_unix=100, row_count=8, rehearsal_rows=4))
    put(folder / 'ENCODING.json', dict(new=8, old=4, rejected=[]))
    row = dict(step=1, child_token_exposures=10, anchor_token_exposures=5)
    (folder / 'UPDATES.jsonl').write_text(json.dumps(row) + '\n')
    memory = {}
    snapshot = dict(state=dict(generation=0), sleep_started=True)
    first = guard.serial_workload(tmp_path, snapshot, 110, memory)
    assert first['seconds_per_update'] is None and first['scheduled_updates'] == 132
    row['step'] = 21
    (folder / 'UPDATES.jsonl').write_text(json.dumps(row) + '\n' + '{"incomplete')
    second = guard.serial_workload(tmp_path, snapshot, 150, memory)
    assert second['seconds_per_update'] == 2
    assert second['observed_interval_updates'] == 20
    assert second['remaining_scheduled_updates'] == 111


def test_no_serial_start_means_unknown_timing(tmp_path):
    result = guard.serial_workload(tmp_path, dict(state=dict(generation=0), sleep_started=False), 100, {})
    assert result['seconds_per_update'] is None and result['measurement'] == 'UNKNOWN_NOT_STARTED'


@pytest.fixture
def cpu_life(tmp_path):
    source, root = tmp_path / 'source', tmp_path / 'life'
    (source / 'gpu').mkdir(parents=True)
    root.mkdir()
    (source / 'gpu/__init__.py').write_text('')
    (source / 'gpu/orch_r111_route_pair_shared.py').write_text('''import os,sys,time,subprocess,signal
from pathlib import Path
root=Path(sys.argv[sys.argv.index('--root')+1])
if sys.argv[1]=='supervise':
    child=subprocess.Popen([sys.executable,'-m','gpu.orch_r111_route_pair_shared','run','--root',str(root)])
    (root/'child.pid').write_text(str(child.pid))
    child.wait()
else:
    def stop(signum, frame):
        if not (root/'ignore_term').exists(): raise SystemExit(0)
    signal.signal(signal.SIGTERM, stop)
    (root/'running').write_text('ready')
    while True:
        if sys.argv[1]=='run' and (root/'spawn_readout').exists() and not (root/'readout.pid').exists():
            child=subprocess.Popen([sys.executable,'-m','gpu.orch_r111_route_pair_shared','readout','--root',str(root),'--sleep-index','1','--checkpoint',str(root/'PLAN.json'),'--scope','dev'])
            (root/'readout.pid').write_text(str(child.pid))
        time.sleep(.01)
''')
    environment = dict(os.environ, PYTHONPATH=str(source), CUDA_VISIBLE_DEVICES='fixture-UUID')
    supervisor = subprocess.Popen([sys.executable, '-m', guard.MODULE, 'supervise', '--root', str(root)],
        env=environment, cwd=source, start_new_session=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    deadline = time.monotonic() + 5
    while not (root / 'running').exists() and time.monotonic() < deadline:
        time.sleep(.01)
    assert (root / 'running').exists()
    actor_pid = int((root / 'child.pid').read_text())
    put(root / 'PLAN.json', dict(fixture=True))
    spec = dict(root=str(root), uid=os.getuid(), uuid='fixture-UUID', source_root=str(source),
        plan=guard.ref(root / 'PLAN.json'), supervisor=guard.identity(supervisor.pid), initial_actor=guard.identity(actor_pid))
    descriptors = [os.pidfd_open(pid) for pid in (supervisor.pid, actor_pid)]
    try:
        yield spec, root
    finally:
        for descriptor in descriptors:
            try:
                signal.pidfd_send_signal(descriptor, signal.SIGCONT)
                signal.pidfd_send_signal(descriptor, signal.SIGKILL)
            except ProcessLookupError:
                pass
            finally:
                os.close(descriptor)
        supervisor.wait(timeout=5)


def test_real_cpu_pidfds_stop_only_bound_supervisor_actor_preserving_files(cpu_life, tmp_path):
    spec, root = cpu_life
    put(root / 'RESERVATIONS.jsonl', dict(native=12, parent=3))
    before = {path.name: path.read_bytes() for path in root.iterdir() if path.is_file()}
    unrelated = subprocess.Popen([sys.executable, '-c', 'import time;time.sleep(20)'])
    output = tmp_path / 'stop'
    output.mkdir()
    try:
        result = guard.terminate_tree(spec, output, 'CPU_TEST', grace_seconds=.5)
        assert result['status'] == 'RELEASED'
        assert {item['pid'] for item in result['signals']} == {spec['supervisor']['pid'], spec['initial_actor']['pid']}
        assert unrelated.poll() is None
        for name, content in before.items():
            assert (root / name).read_bytes() == content
        assert not (root / 'TERMINAL.json').exists()
    finally:
        unrelated.terminate()
        unrelated.wait(timeout=5)


def test_changed_PLAN_blocks_real_process_signals(cpu_life, tmp_path):
    spec, root = cpu_life
    put(root / 'PLAN.json', dict(changed=True))
    with pytest.raises(ValueError, match='unchanged_route_PLAN'):
        guard.terminate_tree(spec, tmp_path / 'stop', 'CPU_TEST')
    assert guard.alive(spec['supervisor']) and guard.alive(spec['initial_actor'])


def test_real_cpu_ignored_TERM_has_bounded_identity_checked_escalation(cpu_life, tmp_path):
    spec, root = cpu_life
    (root / 'ignore_term').touch()
    output = tmp_path / 'force'
    output.mkdir()
    result = guard.terminate_tree(spec, output, 'CPU_DEADLINE_TEST', grace_seconds=.05)
    assert result['status'] == 'RELEASED'
    killed = [item for item in result['signals'] if item['signal'] == 'SIGKILL_AFTER_BOUNDED_GRACE']
    assert [item['pid'] for item in killed] == [spec['initial_actor']['pid']]
    assert not (root / 'TERMINAL.json').exists()


def test_real_cpu_known_orphan_is_not_left_waiting_after_supervisor_exit(cpu_life, tmp_path):
    spec, root = cpu_life
    descriptor = os.pidfd_open(spec['supervisor']['pid'])
    try:
        guard.signal_bound(descriptor, spec['supervisor'], signal.SIGTERM)
        assert guard.exited(descriptor, 2)
    finally:
        os.close(descriptor)
    output = tmp_path / 'orphan'
    output.mkdir()
    result = guard.terminate_tree(spec, output, 'CPU_ORPHAN_TEST', grace_seconds=.5)
    assert result['status'] == 'RELEASED'
    assert {item['pid'] for item in result['signals']} == {spec['initial_actor']['pid']}


def test_real_cpu_readout_child_options_are_bound_and_shutdown(cpu_life, tmp_path):
    spec, root = cpu_life
    (root / 'spawn_readout').touch()
    deadline = time.monotonic() + 5
    while not (root / 'readout.pid').exists() and time.monotonic() < deadline:
        time.sleep(.01)
    pid = int((root / 'readout.pid').read_text())
    descriptor = os.pidfd_open(pid)
    try:
        deadline = time.monotonic() + 5
        while time.monotonic() < deadline:
            try:
                observed = guard.route_process(pid, spec, 'readout')
                break
            except ValueError:
                time.sleep(.01)
        assert observed['ppid'] == spec['initial_actor']['pid']
        output = tmp_path / 'readout_stop'
        output.mkdir()
        result = guard.terminate_tree(spec, output, 'CPU_READOUT_TEST', grace_seconds=.5)
        assert result['status'] == 'RELEASED'
        assert {item['role'] for item in result['processes']} == {'supervisor', 'actor', 'readout'}
        assert guard.exited(descriptor, 1)
    finally:
        if not guard.exited(descriptor):
            signal.pidfd_send_signal(descriptor, signal.SIGKILL)
        os.close(descriptor)


def test_no_lifecycle_effect_on_import(tmp_path):
    assert not (tmp_path / 'TERMINAL.json').exists()
    assert not (tmp_path / 'COMPLETED.json').exists()


def test_atomic_replacement_cleanup_does_not_crash_monitor(tmp_path):
    path = tmp_path / 'STATUS.json'
    guard.write(path, dict(sequence=1), replace=True)
    guard.write(path, dict(sequence=2), replace=True)
    assert guard.read(path) == dict(sequence=2)
    assert not list(tmp_path.glob('*.tmp'))
    with pytest.raises(FileExistsError):
        guard.write(path, dict(sequence=3))
    assert guard.read(path) == dict(sequence=2)


def test_actual_monitor_loop_survives_multiple_status_replacements(tmp_path, monkeypatch, scenario):
    control, snapshot, observations, memory = scenario
    control.update(directory=str(tmp_path), common=str(tmp_path), routes={}, poll_seconds=.01,
                   no_progress_alarm_seconds=600, controller_end_unix=guard.CUTOFF)
    put(tmp_path / 'CONTROL.json', control)
    monkeypatch.setattr(guard, 'validate', lambda unused: None)
    monkeypatch.setattr(guard, 'common_snapshot', lambda unused: snapshot)
    monkeypatch.setattr(guard, 'peer_observation', lambda unused, cache: observations['F1'])
    monkeypatch.setattr(guard.time, 'time', lambda: guard.DRAIN - 3600)
    iterations = []
    def pause(unused):
        iterations.append(guard.read(tmp_path / 'STATUS.json'))
        if len(iterations) == 3:
            put(tmp_path / 'COMPLETED.json', dict(cpu_test_exit=True))
    monkeypatch.setattr(guard.time, 'sleep', pause)
    guard.run(tmp_path / 'CONTROL.json', guard.sha(tmp_path / 'CONTROL.json'), 'monitor')
    assert len(iterations) == 3
    assert all(item['decision']['action'] == 'MONITOR' for item in iterations)
    assert not (tmp_path / 'MONITOR_ERROR.json').exists()
