"""Identity-bound complete-episode rollover of owned node3 generation slots."""

import argparse
import ctypes
import fcntl
import hashlib
import json
import os
from pathlib import Path
import select
import signal
import struct
import time

from gpu.orch_rich_hot_node3_run import bind_host
from gpu.orch_rich_hot_node1_run import sha, write
from gpu.orch_rich_hot_node1_scan import process_identity
from gpu import orch_rich_intensity_guard as ownership


BASE = Path('/localhome/local-rohing')
ORIGINAL = BASE / 'orch_rich_hot_node3_20260915_attempt1'
PHASES = [
    ('orch_rich_hot_node3_20260915_route_v2_batch03', 'gpu.orch_rich_hot_node3_route_batch03_run',
     'RICH_HOT_NODE3_ROUTE_V2_BATCH03_UNSEEN_DISPLAYS'),
    ('orch_rich_hot_node3_20260915_route_v2_batch02', 'gpu.orch_rich_hot_node3_route_next_run',
     'RICH_HOT_NODE3_ROUTE_V2_BATCH02_UNSEEN_DISPLAYS'),
]


def identify(pid, root, module, index, mode='run'):
    directory = Path('/proc') / str(pid)
    identity = process_identity(directory)
    command = (directory / 'cmdline').read_bytes()
    arguments = command.split(b'\0')
    expected = [b'-m', module.encode(), mode.encode(), b'--root', str(root).encode(),
                b'--index', str(index).encode()]
    assert any(arguments[position:position + len(expected)] == expected for position in range(len(arguments)))
    assert identity['uid'] == os.getuid()
    if mode == 'run':
        assert os.getpgid(pid) == pid and os.getsid(pid) == pid
        assert ('CUDA_VISIBLE_DEVICES=' + ownership.DEVICES[index]).encode() in (directory / 'environ').read_bytes().split(b'\0')
    return dict(identity, command_sha256=hashlib.sha256(command).hexdigest())


def cancel_unlaunched_guard(destination, index):
    name, module, phase = PHASES[0]
    root = BASE / name
    if (root / f'LAUNCH_{index}.json').exists():
        return
    for directory in Path('/proc').glob('[0-9]*'):
        try:
            command = (directory / 'cmdline').read_bytes()
            if module.encode() not in command or b'watch\0' not in command:
                continue
            expected = identify(int(directory.name), root, module, index, mode='watch')
        except (AssertionError, FileNotFoundError, ProcessLookupError, PermissionError):
            continue
        pid = expected['pid']
        os.kill(pid, signal.SIGSTOP)
        try:
            assert identify(pid, root, module, index, mode='watch') == expected
            children = (directory / 'task' / str(pid) / 'children').read_text().split()
            if children or (root / f'LAUNCH_{index}.json').exists():
                continue
            write(destination / f'RETIRED_PENDING_GUARD_{index}.json', dict(identity=expected,
                reason='ROHIN100_supersedes_unlaunched_old_prompt', no_children=True, native_calls=0))
            os.kill(pid, signal.SIGTERM)
        finally:
            try:
                os.kill(pid, signal.SIGCONT)
            except ProcessLookupError:
                pass


def episode_complete(rows, episodes, reservations):
    return ({row['global_call'] for row in rows} == {row['global_call'] for row in reservations}
            and {row['task_id'] for row in rows} <= {row['task_id'] for row in episodes})


def checkpoint(destination, index):
    bind_host()
    assert index in (3, 4, 5)
    assert not (destination / f'CHECKPOINT_{index}.json').exists()
    cancel_unlaunched_guard(destination, index)
    choices = []
    for name, module, phase in PHASES:
        root = BASE / name
        launch = root / f'LAUNCH_{index}.json'
        if not launch.exists():
            continue
        pid = json.loads(launch.read_text())['pid']
        live = (Path('/proc') / str(pid)).exists()
        choices.append((live, root, module, phase, pid))
        if live:
            break
    assert choices
    live, root, module, phase, pid = next((entry for entry in choices if entry[0]), choices[0])
    expected = identify(pid, root, module, index) if live else None
    shard = root / f'shard{index}'
    deadline = json.loads((ORIGINAL / 'run/START.json').read_text())['native_deadline_unix']
    libc = ctypes.CDLL(None, use_errno=True)
    descriptor = libc.inotify_init1(os.O_NONBLOCK | os.O_CLOEXEC)
    assert descriptor >= 0 and libc.inotify_add_watch(descriptor, str(shard).encode(), 0x80) >= 0
    try:
        while time.time() < deadline:
            live = (Path('/proc') / str(pid)).exists()
            if live:
                assert identify(pid, root, module, index) == expected
                if not select.select([descriptor], [], [], 2)[0]:
                    continue
                buffer = os.read(descriptor, 65536)
                position, completed = 0, False
                while position + 16 <= len(buffer):
                    watched, mask, cookie, length = struct.unpack_from('iIII', buffer, position)
                    name = buffer[position + 16:position + 16 + length].split(b'\0')[0]
                    completed |= name.startswith(b'EPISODE_') or name == b'RESULT.json'
                    position += 16 + length
                if not completed:
                    continue
                try:
                    assert identify(pid, root, module, index) == expected
                    os.killpg(pid, signal.SIGSTOP)
                except (FileNotFoundError, ProcessLookupError):
                    continue
            stopped = live
            try:
                if live:
                    assert identify(pid, root, module, index) == expected
                else:
                    assert json.loads((shard / 'RESULT.json').read_text())['status'] == 'COMPLETE'
                with (ORIGINAL / 'CALL_RESERVATIONS.jsonl').open() as ledger:
                    try:
                        fcntl.flock(ledger, fcntl.LOCK_SH | fcntl.LOCK_NB)
                    except BlockingIOError:
                        continue
                    reservations = [json.loads(line) for line in ledger if line.strip()]
                reservations = [row for row in reservations if row.get('physical_index') == index
                                and row.get('phase_version') == phase]
                calls = sorted(path for path in shard.glob('CALL_*.json') if path.stem[5:].isdigit())
                episodes = sorted(shard.glob('EPISODE_*.json'))
                rows = [json.loads(path.read_text()) for path in calls]
                episode_rows = [json.loads(path.read_text()) for path in episodes]
                if not episode_complete(rows, episode_rows, reservations):
                    continue
                write(destination / f'CHECKPOINT_{index}.json', dict(index=index, prior_root=str(root),
                    original_identity=expected, safe_episode_boundary=True, pending_calls=0,
                    completed_calls=len(rows), completed_episodes=len(episode_rows),
                    files={str(path.relative_to(root)): sha(path) for path in calls + episodes},
                    created_unix=time.time(), natural_completion=not live))
                if live:
                    assert identify(pid, root, module, index) == expected
                    os.killpg(pid, signal.SIGTERM)
                    os.killpg(pid, signal.SIGCONT)
                    stopped = False
                    limit = time.monotonic() + 30
                    while (Path('/proc') / str(pid)).exists() and time.monotonic() < limit:
                        time.sleep(0.2)
                    assert not (Path('/proc') / str(pid)).exists()
                print(json.dumps(dict(index=index, safe_episode_boundary=True,
                    completed_calls=len(rows), completed_episodes=len(episode_rows), prior_pid=pid)))
                return
            finally:
                if stopped:
                    os.killpg(pid, signal.SIGCONT)
    finally:
        os.close(descriptor)
    raise TimeoutError('original_node3_deadline_before_safe_boundary')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--destination', type=Path, required=True)
    parser.add_argument('--index', type=int, choices=(3, 4, 5), required=True)
    arguments = parser.parse_args()
    checkpoint(arguments.destination, arguments.index)
