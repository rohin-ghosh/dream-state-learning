"""Stop an exact V1 worker only after all its task stages are durably complete."""

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

from gpu import orch_rich_hot_node1_scan as scanner
from gpu.orch_rich_hot_node1_run import sha, write
from organism_v6 import orch_rich_hot_node1_premise as policy
from gpu.orch_rich_hot_node1_premise_board import require_board


def complete_tasks(rows, reservations, index, context_failures=()):
    own_reserved = {entry['global_call'] for entry in reservations if entry['index'] == index}
    own_rows = [row for row in rows if row['index'] == index]
    if own_reserved != {row['global_call'] for row in own_rows}:
        return None
    expected = {'source', 'own_second_pass'} if index >= 4 else {'source'}
    by_task = {}
    for row in own_rows:
        by_task.setdefault(row['task_id'], set()).add(row['stage'])
    for failure in context_failures:
        if failure['task_id'] in by_task:
            by_task[failure['task_id']].add(failure['stage'])
    if not by_task or any(stages != expected for stages in by_task.values()):
        return None
    return sorted(by_task)


def identity(pid, root, index):
    directory = Path('/proc') / str(pid)
    result = scanner.process_identity(directory)
    arguments = (directory / 'cmdline').read_bytes().split(b'\0')
    expected = [b'-m', b'gpu.orch_rich_hot_node1_exhaustion_run', b'run', b'--root',
                str(root).encode(), b'--index', str(index).encode()]
    policy.require(any(arguments[position:position + len(expected)] == expected
                       for position in range(len(arguments))), 'exact_v1_worker_argv_required')
    environment = (directory / 'environ').read_bytes().split(b'\0')
    policy.require(('CUDA_VISIBLE_DEVICES=' + policy.UUIDS[index]).encode() in environment,
                   'exact_uuid_environment_required')
    policy.require(result['uid'] == os.getuid() and os.getpgid(pid) == pid and os.getsid(pid) == pid,
                   'exact_owned_process_group_required')
    result.update(command_sha256=hashlib.sha256((directory / 'cmdline').read_bytes()).hexdigest(),
                  pgid=pid, sid=pid, uuid=policy.UUIDS[index])
    return result


def checkpoint(root, destination, index, floor_receipt):
    scanner.host()
    policy.allocation(index)
    require_board(destination, index)
    policy.require(not (destination / f'CHECKPOINT_{index}.json').exists(), 'no_repeated_checkpoint')
    floor = json.loads(floor_receipt.read_text())
    policy.require(floor['active_generators'] >= 2 and floor['minimum_during_one_gpu_roll'] >= 1
                   and time.time() - floor['observed_unix'] < 30, 'fresh_generation_floor_required')
    launch = json.loads((root / f'LAUNCH_{index}.json').read_text())
    pid = launch['identity']['pid']
    expected = identity(pid, root, index)
    policy.require(all(expected[key] == value for key, value in launch['identity'].items()), 'original_launch_identity_join')
    shard = root / f'shard{index}'
    lifetime = json.loads((root / 'LIFETIME.json').read_text())
    libc = ctypes.CDLL(None, use_errno=True)
    descriptor = libc.inotify_init1(os.O_NONBLOCK | os.O_CLOEXEC)
    policy.require(descriptor >= 0, 'inotify_setup_failed')
    watch = libc.inotify_add_watch(descriptor, str(shard).encode(), 0x80)
    policy.require(watch >= 0, 'inotify_watch_failed')
    try:
        while time.time() < lifetime['native_deadline_unix']:
            policy.require(identity(pid, root, index) == expected, 'waiting_worker_identity_drift')
            if not select.select([descriptor], [], [], 5)[0]:
                continue
            buffer = os.read(descriptor, 65536)
            position, progressed = 0, False
            while position + 16 <= len(buffer):
                watched, mask, cookie, length = struct.unpack_from('iIII', buffer, position)
                name = buffer[position + 16:position + 16 + length].split(b'\0')[0]
                progressed |= name == b'PROGRESS.json'
                position += 16 + length
            if not progressed:
                continue
            progress = json.loads((shard / 'PROGRESS.json').read_text())
            if index >= 4 and progress['stage'] != 'own_second_pass':
                continue
            floor = json.loads(floor_receipt.read_text())
            policy.require(floor['active_generators'] >= 2 and floor['minimum_during_one_gpu_roll'] >= 1
                           and time.time() - floor['observed_unix'] < 30, 'refresh_floor_before_boundary')
            policy.require(identity(pid, root, index) == expected, 'pre_stop_identity_drift')
            os.killpg(pid, signal.SIGSTOP)
            stopped = True
            try:
                policy.require(identity(pid, root, index) == expected, 'stopped_identity_drift')
                with (Path(json.loads((root / 'CONTINUATION.json').read_text())['original_root']) / 'CALL_RESERVATIONS.jsonl').open() as ledger:
                    try:
                        fcntl.flock(ledger, fcntl.LOCK_SH | fcntl.LOCK_NB)
                    except BlockingIOError:
                        continue
                    reservations = [json.loads(line) for line in ledger if line.strip()]
                    reservations = [row for row in reservations if row.get('phase_version') == 'ROHIN100_EXHAUSTION_V1']
                paths = sorted(shard.glob('CALL_[0-9][0-9][0-9][0-9][0-9].json'))
                rows = [json.loads(path.read_text()) for path in paths]
                contexts = [json.loads(path.read_text()) for path in shard.glob('CONTEXT_*.json')]
                completed = complete_tasks(rows, reservations, index, contexts)
                if completed is None:
                    continue
                previous_checkpoint = json.loads((root / f'CHECKPOINT_{index}.json').read_text())
                completed = sorted(set(completed) | set(previous_checkpoint['completed_tasks']))
                frozen = dict(index=index, phase_version='V1_V2_AND_EXHAUSTION_PRESERVED', original_root=str(root),
                    original_identity=expected, completed_tasks=completed, unfinished_calls=[],
                    pending_source_second_pass_pairs=[], completed_calls=len(rows),
                    completed_global_calls=sorted(row['global_call'] for row in rows),
                    files={str(path.relative_to(root)): sha(path) for path in paths + [root / f'CHECKPOINT_{index}.json']},
                    previous_checkpoint_sha256=sha(root / f'CHECKPOINT_{index}.json'),
                    original_tasks_sha256=sha(root / 'TASKS.json'),
                    original_lifetime_sha256=sha(root / 'LIFETIME.json'),
                    floor_receipt=floor, checkpoint_unix=time.time(), regenerated_calls=0)
                write(destination / f'CHECKPOINT_{index}.json', frozen)
                policy.require(identity(pid, root, index) == expected, 'pre_term_identity_drift')
                os.killpg(pid, signal.SIGTERM)
                os.killpg(pid, signal.SIGCONT)
                stopped = False
                end = time.monotonic() + 30
                while (Path('/proc') / str(pid)).exists() and time.monotonic() < end:
                    time.sleep(0.2)
                policy.require(not (Path('/proc') / str(pid)).exists(), 'owned_exit_not_confirmed')
                for attempt in range(12):
                    release = scanner.scan(index, root / 'SERVICE_IDENTITY.json')
                    write(destination / f'PRIOR_RELEASE_{index}_{attempt:02d}.json', release)
                    if release['clear']:
                        break
                    time.sleep(3)
                policy.require(release['clear'], 'released_gpu_not_clear')
                print(json.dumps(dict(index=index, stopped_pid=pid, complete_tasks=len(completed),
                    complete_calls=len(rows), unfinished_calls=0, release_clear=True)))
                return
            finally:
                if stopped:
                    os.killpg(pid, signal.SIGCONT)
    finally:
        os.close(descriptor)
    raise TimeoutError('no_safe_task_boundary_before_original_deadline')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--destination', type=Path, required=True)
    parser.add_argument('--index', type=int, choices=range(8), required=True)
    parser.add_argument('--floor-receipt', type=Path, required=True)
    options = parser.parse_args()
    checkpoint(options.root, options.destination, options.index, options.floor_receipt)
