import fcntl
import hashlib
import json
import os
from pathlib import Path
import signal
import socket
import stat
import subprocess
import sys
import time
from types import SimpleNamespace

import pytest

from gpu import orch_r111_route_boundary as boundary


def put(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value))


@pytest.fixture
def cycle(tmp_path):
    root = tmp_path / 'life'
    current = root / 'cycle_0003'
    put(current / 'START.json', dict(cycle=3))
    checkpoint = current / 'checkpoint/CHECKPOINT.json'
    optimizer = checkpoint.parent / 'optimizer_rng.pt'
    optimizer.parent.mkdir()
    optimizer.write_bytes(b'actual preserved fixture optimizer')
    adapter = checkpoint.parent / 'adapter'
    adapter.mkdir()
    (adapter / 'adapter.bin').write_bytes(b'preserved adapter')
    put(checkpoint, dict(complete=True, cycle=3, sleeps=3, optimizer_rng_sha256=boundary.sha(optimizer),
        adapter=dict(path=str(adapter), files=[['adapter.bin', boundary.sha(adapter / 'adapter.bin')]])))
    put(current / 'SLEEP.json', dict(sleeps=3, checkpoint_sha256=boundary.sha(checkpoint)))
    put(root / 'OWN_CARRY.json', dict(reflection='preserved', checkpoint_sha256=boundary.sha(checkpoint)))
    put(root / 'open_readouts/readout_0003/COMPLETE.json', dict(status='COMPLETE'))
    put(current / 'COMPLETE.json', dict(cycle=3, sleeps=3))
    put(current / 'CALL_000001.json', dict(finished_unix=1))
    put(root / 'parent_queue/000001_F1_C0003.observed.json', dict(status='MISSING', observed_unix=2))
    rows = [dict(kind='NATIVE', number=1, cycle=3), dict(kind='PARENT', number=1, cycle=3)]
    (root / 'RESERVATIONS.jsonl').write_text(''.join(json.dumps(row) + '\n' for row in rows))
    return root, current


def test_complete_original_cycle_accepts_settled_missing_not_success_only(cycle):
    root, current = cycle
    receipt = boundary.completed_boundary(root, current)
    assert receipt['charged'] == dict(NATIVE=1, PARENT=1)
    assert receipt['original_COMPLETE_written'] is True
    assert receipt['no_pending_calls'] is True


def test_empty_next_start_is_preserved_not_an_uncharged_task_skip(cycle):
    root, current = cycle
    path = root / 'cycle_0004/START.json'
    put(path, dict(cycle=4))
    before = path.read_bytes()
    assert boundary.completed_boundary(root, current)['empty_successor_start'] == boundary.reference(path)
    assert path.read_bytes() == before


@pytest.mark.parametrize('kind', ['NATIVE', 'PARENT'])
def test_raced_next_reservation_disqualifies_boundary(cycle, kind):
    root, current = cycle
    with (root / 'RESERVATIONS.jsonl').open('a') as stream:
        stream.write(json.dumps(dict(kind=kind, number=2, cycle=4)) + '\n')
    assert boundary.completed_boundary(root, current) is None


def test_morning_readout_crossing_does_not_skip_final(cycle):
    root, current = cycle
    assert boundary.candidate(root, boundary.MORNING_CUT - 1) == current
    assert boundary.candidate(root, boundary.MORNING_CUT) is None
    put(root / 'FINAL_MORNING_REQUESTED.json', dict(sleep=3))
    assert boundary.candidate(root, boundary.MORNING_CUT) is None
    put(root / 'sealed_final_readouts/readout_0003/PROCESS_RESULT.json', dict(status='CRASHED_READOUT_CONTINUE_LIFE'))
    assert boundary.candidate(root, boundary.MORNING_CUT) == current


def test_earlier_final_attempt_already_done_is_not_repeated(cycle):
    root, current = cycle
    put(root / 'FINAL_MORNING_REQUESTED.json', dict(sleep=2))
    assert boundary.candidate(root, boundary.MORNING_CUT) == current


@pytest.mark.parametrize('file', ['optimizer_rng.pt', 'adapter/adapter.bin'])
def test_changed_checkpoint_payload_fails_closed(cycle, file):
    root, current = cycle
    (current / 'checkpoint' / file).write_bytes(b'drift')
    with pytest.raises(ValueError, match='bytes_preserved'):
        boundary.completed_boundary(root, current)


def test_pending_native_is_not_a_safe_boundary(cycle):
    root, current = cycle
    put(current / 'CALL_000001.json', dict(status='PENDING'))
    with pytest.raises(ValueError, match='native_settled'):
        boundary.completed_boundary(root, current)


def test_pending_parent_is_not_a_safe_boundary(cycle):
    root, current = cycle
    (root / 'parent_queue/000001_F1_C0003.observed.json').unlink()
    with pytest.raises(ValueError, match='parent_settled'):
        boundary.completed_boundary(root, current)


def test_complete_checkpoint_is_insufficient_without_original_COMPLETE(cycle):
    root, current = cycle
    (current / 'COMPLETE.json').unlink()
    assert boundary.completed_boundary(root, current) is None


def test_no_overwrite_write_preserves_original(tmp_path):
    path = tmp_path / 'receipt.json'
    boundary.write_new(path, dict(first=True))
    before = path.read_bytes()
    with pytest.raises(FileExistsError):
        boundary.write_new(path, dict(first=False))
    assert path.read_bytes() == before


def test_uncoordinated_shared_request_never_opens_process(tmp_path, monkeypatch):
    request = tmp_path / 'REQUEST.json'
    authorization = tmp_path / 'AUTH.json'
    put(request, dict(purpose='SHARED_ADOPTION'))
    put(authorization, dict(request_sha256=boundary.sha(request), purpose='SHARED_ADOPTION', authorized=True,
                            all_eight_ready=False, common_handoff_coordinated=False))
    monkeypatch.setattr(os, 'pidfd_open', lambda unused: pytest.fail('must not touch live processes'))
    with pytest.raises(ValueError, match='no_premature_shared_stop'):
        boundary.execute(request, authorization)


def test_refusal_not_a_wait600_authorization(tmp_path, monkeypatch):
    request = tmp_path / 'REQUEST.json'
    authorization = tmp_path / 'AUTH.json'
    put(request, dict(purpose='WAIT600_TRANSPORT'))
    put(authorization, dict(request_sha256=boundary.sha(request), purpose='WAIT600_TRANSPORT', authorized=True,
        successor_ready=True, prospective_only=True, refusals_never_retried=True,
        transport_basis='SAFETY_REFUSAL', basis_reference='not latency'))
    monkeypatch.setattr(os, 'pidfd_open', lambda unused: pytest.fail('must not touch live processes'))
    with pytest.raises(ValueError, match='refusal_is_not_transport_authorization'):
        boundary.execute(request, authorization)


@pytest.mark.skipif(not hasattr(os, 'pidfd_open'), reason='Linux pidfd')
def test_actual_owned_cpu_process_pidfd_stop_resume_and_identity_guard():
    process = subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(30)'])
    descriptor = os.pidfd_open(process.pid)
    try:
        expected = boundary.identity(process.pid)
        with pytest.raises(ValueError, match='identity_before_stop'):
            boundary.stop(descriptor, dict(expected, start_ticks='wrong'))
        boundary.stop(descriptor, expected)
        assert boundary.process_state(process.pid) in ('T', 't')
        signal.pidfd_send_signal(descriptor, signal.SIGCONT)
        signal.pidfd_send_signal(descriptor, signal.SIGTERM)
        assert boundary.wait_exit(descriptor, 3)
        process.wait(timeout=3)
    finally:
        if process.poll() is None:
            signal.pidfd_send_signal(descriptor, signal.SIGCONT)
            process.terminate()
            process.wait(timeout=3)
        os.close(descriptor)


def test_actual_reservation_lock_blocks_new_work_without_rewriting_ledger(tmp_path):
    path = tmp_path / 'RESERVATIONS.jsonl'
    path.write_text('old\n')
    command = ('import fcntl,sys; stream=open(sys.argv[1],"a"); '
               'fcntl.flock(stream,fcntl.LOCK_EX); stream.write("new\\n"); stream.close()')
    with path.open('r') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        process = subprocess.Popen([sys.executable, '-c', command, str(path)])
        try:
            time.sleep(.1)
            assert process.poll() is None
            assert path.read_text() == 'old\n'
        finally:
            fcntl.flock(lock, fcntl.LOCK_UN)
            process.wait(timeout=3)
    assert path.read_text() == 'old\nnew\n'


@pytest.fixture
def owned_process_pair(cycle, monkeypatch):
    root, current = cycle
    pid_file = root / 'CPU_CHILD_PID'
    script = ('import subprocess,sys,time,pathlib; '
              'child=subprocess.Popen([sys.executable,"-c","import time; time.sleep(30)"]); '
              'pathlib.Path(sys.argv[1]).write_text(str(child.pid)); time.sleep(30)')
    supervisor = subprocess.Popen([sys.executable, '-c', script, str(pid_file)])
    deadline = time.monotonic() + 3
    while not pid_file.exists() and time.monotonic() < deadline:
        time.sleep(.01)
    assert pid_file.exists()
    actor_pid = int(pid_file.read_text())
    actor_descriptor = os.pidfd_open(actor_pid)
    identities = dict(actor=boundary.identity(actor_pid), supervisor=boundary.identity(supervisor.pid))
    source = root / 'SOURCE.py'
    source.write_text('CPU stand-in, not a live GPU source')
    bounds = dict(hard_end_unix=time.time() + 20, native_calls=300, parent_calls=200)
    put(root / 'PLAN.json', dict(bounds=bounds, physical=0, uuid='GPU-test', source_files={str(source): boundary.sha(source)}))
    put(root / 'ACTOR_READY.json', dict(pid=actor_pid))
    request_path = root / 'handoff/REQUEST.json'
    mapping = dict(physical=0, uuid='GPU-test', kernel_minor=0)
    request = dict(schema='R118_ROUTE_BOUNDARY_REQUEST_V1', root=str(root), purpose='SHARED_ADOPTION',
        **identities, plan=boundary.reference(root / 'PLAN.json'), ready=boundary.reference(root / 'ACTOR_READY.json'),
        source=boundary.reference(source), host_sha256=hashlib.sha256(socket.gethostname().encode()).hexdigest(),
        mapping=mapping, bounds=bounds, expires_unix=time.time() + 10)
    put(request_path, request)
    authorization = request_path.parent / 'AUTH.json'
    put(authorization, dict(request_sha256=boundary.sha(request_path), purpose='SHARED_ADOPTION',
        authorized=True, all_eight_ready=True, common_handoff_coordinated=True))
    monkeypatch.setattr(boundary, 'ROOT_TEMPLATE', str(root))
    monkeypatch.setattr(boundary, 'UUIDS', {0: 'GPU-test'})
    monkeypatch.setattr(boundary, 'MORNING_CUT', time.time() + 600)
    monkeypatch.setattr(boundary, 'gpu_mapping', lambda *unused: mapping)
    monkeypatch.setattr(boundary, 'pinned_process', lambda pid, *unused: boundary.identity(pid))
    monkeypatch.setattr(boundary, 'source_binding', lambda *unused: None)
    try:
        yield root, request_path, authorization, identities
    finally:
        if not boundary.wait_exit(actor_descriptor, .01):
            signal.pidfd_send_signal(actor_descriptor, signal.SIGCONT)
            signal.pidfd_send_signal(actor_descriptor, signal.SIGTERM)
            boundary.wait_exit(actor_descriptor, 3)
        os.close(actor_descriptor)
        if supervisor.poll() is None:
            os.kill(supervisor.pid, signal.SIGCONT)
            supervisor.terminate()
        supervisor.wait(timeout=3)


@pytest.mark.skipif(not hasattr(os, 'pidfd_open'), reason='Linux pidfd')
def test_full_controller_actual_cpu_pair_releases_preserving_all_bytes(owned_process_pair):
    root, request, authorization, identities = owned_process_pair
    before = {str(path): path.read_bytes() for path in root.rglob('*') if path.is_file()}
    result = boundary.execute(request, authorization)
    assert result['status'] == 'RELEASED'
    assert result['actor'] == identities['actor']
    assert all(Path(path).read_bytes() == data for path, data in before.items())
    assert not (root / 'TERMINAL.json').exists()
    assert (request.parent / 'BOUNDARY.json').exists()


@pytest.mark.skipif(not hasattr(os, 'pidfd_open'), reason='Linux pidfd')
def test_boundary_failure_resumes_both_actual_cpu_processes(owned_process_pair, monkeypatch):
    root, request, authorization, identities = owned_process_pair

    def fail(*unused):
        raise ValueError('injected_boundary_guard')

    monkeypatch.setattr(boundary, 'completed_boundary', fail)
    with pytest.raises(ValueError, match='injected_boundary_guard'):
        boundary.execute(request, authorization)
    deadline = time.monotonic() + 2
    while time.monotonic() < deadline:
        if all(boundary.process_state(row['pid']) not in ('T', 't') for row in identities.values()):
            break
        time.sleep(.01)
    assert all(boundary.process_state(row['pid']) not in ('T', 't', 'Z') for row in identities.values())
    assert not (request.parent / 'RELEASED.json').exists()
    assert read_error(request)['after_supervisor_termination'] is False


def read_error(request):
    return boundary.read(request.parent / 'ERROR.json')


def test_query_uses_supported_UUID_fields_and_kernel_minor(tmp_path, monkeypatch):
    kernel = tmp_path / 'kernel/0000:00:01.0/information'
    kernel.parent.mkdir(parents=True)
    kernel.write_text('GPU UUID: GPU-test\nDevice Minor: 4\n')
    commands = []

    def query(command, **kwargs):
        commands.append(command)
        return '0, GPU-test\n'

    class Devices:
        def __truediv__(self, name):
            assert name == 'nvidia4'
            return SimpleNamespace(stat=lambda: SimpleNamespace(st_mode=stat.S_IFCHR,
                                                                st_rdev=os.makedev(195, 4)))

    def paths(value):
        if value == '/proc/driver/nvidia/gpus':
            return tmp_path / 'kernel'
        if value == '/dev':
            return Devices()
        return Path(value)

    monkeypatch.setattr(boundary.subprocess, 'check_output', query)
    monkeypatch.setattr(boundary, 'Path', paths)
    assert boundary.gpu_mapping(0, 'GPU-test') == dict(physical=0, uuid='GPU-test', kernel_minor=4)
    assert '--query-gpu=index,uuid' in commands[0]


def test_shared_successor_resumes_only_verified_empty_cycle(cycle):
    root, current = cycle
    start = root / 'cycle_0004/START.json'
    put(start, dict(cycle=4))
    saved = boundary.completed_boundary(root, current)
    handoff = root / 'handoff'
    put(handoff / 'BOUNDARY.json', saved)
    put(handoff / 'RELEASED.json', dict(status='RELEASED', original_plan=dict(path=str(root / 'PLAN.json')),
        boundary=boundary.reference(handoff / 'BOUNDARY.json')))
    reference = boundary.reference(handoff / 'RELEASED.json')
    assert boundary.successor_cycle(root, reference) == 4
    original = start.read_bytes()
    path = boundary.successor_start(root, start.parent, reference)
    assert path.name.startswith('RESUMED_START_')
    put(path, dict(cycle=4, resumed=True))
    assert start.read_bytes() == original
    assert boundary.successor_cycle(root, reference) == 5


def test_shared_successor_refuses_changed_ledger_for_empty_cycle(cycle):
    root, current = cycle
    start = root / 'cycle_0004/START.json'
    put(start, dict(cycle=4))
    handoff = root / 'handoff'
    put(handoff / 'BOUNDARY.json', boundary.completed_boundary(root, current))
    put(handoff / 'RELEASED.json', dict(status='RELEASED', original_plan=dict(path=str(root / 'PLAN.json')),
        boundary=boundary.reference(handoff / 'BOUNDARY.json')))
    reference = boundary.reference(handoff / 'RELEASED.json')
    with (root / 'RESERVATIONS.jsonl').open('a') as stream:
        stream.write(json.dumps(dict(kind='NATIVE', cycle=4, number=2)) + '\n')
    with pytest.raises(ValueError, match='no_unrecorded_empty_cycle_charge'):
        boundary.successor_cycle(root, reference)
