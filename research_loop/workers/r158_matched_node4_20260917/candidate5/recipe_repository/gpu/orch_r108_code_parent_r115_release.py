"""Exact owned pidfd release at a verified completed-cycle boundary only."""

import argparse
import ctypes
import json
import os
from pathlib import Path
import select
import signal
import struct
import time

from gpu.orch_rich_hot_a100_scan import host_identity, identity, sha


HOST_SHA = '0cb7eb43862102b79ae0a30d2babfedfbf9598b31967a1a04122c3cf849c746d'


def read(path):
    return json.loads(path.read_text())


def write(path, value):
    with path.open('x') as stream:
        json.dump(value, stream, sort_keys=True, indent=2)
        stream.flush()
        os.fsync(stream.fileno())


def eligible(cycle, rows, receiver_ready):
    return receiver_ready is True and type(cycle) is int and cycle > 0 and bool(rows) \
        and all(type(row.get('cycle')) is int and row['cycle'] <= cycle
            and row.get('status') in ('COMPLETE', 'MISSING', 'FAILED') for row in rows)


def release(root):
    assert root in [Path(f'/localhome/local-rohing/orch_r108_code_parent_node5_{physical}_20260915_attempt2')
        for physical in (4, 5)] and host_identity() == HOST_SHA
    request = read(root / 'R115_RECEIVER_READY.json')
    assert request['receiver_ready'] is True and request['explicit_owner_request']
    lane = root / 'campaign_code_parent'
    expected = read(lane / 'NATIVE_REQUEST.json')['process']
    process = Path('/proc') / str(expected['pid'])
    assert expected['uid'] == os.getuid() and identity(process) == expected
    descriptor = os.pidfd_open(expected['pid'])
    library = ctypes.CDLL(None, use_errno=True)
    watch = library.inotify_init1(os.O_NONBLOCK | os.O_CLOEXEC)
    assert watch >= 0
    assert library.inotify_add_watch(watch, os.fsencode(lane), 0x8 | 0x80) >= 0
    deadline = read(root / 'LIFETIME.json')['hard_deadline_unix']
    write(root / 'R115_RELEASE_WATCHER.json', dict(expected_identity=expected,
        watcher_identity=identity(Path('/proc') / str(os.getpid())), started_unix=time.time(),
        request_sha256=sha(root / 'R115_RECEIVER_READY.json')))
    try:
        while time.time() < deadline:
            ready, _, _ = select.select([watch, descriptor], [], [], 10)
            if descriptor in ready:
                return
            if watch not in ready:
                continue
            data = os.read(watch, 65536)
            offset = 0
            candidates = []
            while offset + 16 <= len(data):
                _, mask, _, length = struct.unpack_from('iIII', data, offset)
                name = data[offset+16:offset+16+length].split(b'\0', 1)[0].decode()
                offset += 16 + length
                if name.startswith('CYCLE_') and name.endswith('_COMPLETE.json'):
                    candidates.append(lane / name)
            for path in candidates:
                assert identity(process) == expected
                signal.pidfd_send_signal(descriptor, signal.SIGSTOP)
                stopped = False
                try:
                    for attempt in range(100):
                        state = (process / 'stat').read_text().rsplit(')', 1)[1].split()[0]
                        if state in ('T', 't'):
                            stopped = True
                            break
                        time.sleep(0.01)
                    assert stopped and identity(process) == expected
                    cycle = read(path)['cycle']
                    cells = sorted((lane / 'cells').glob('*.json'))
                    if not eligible(cycle, [read(item) for item in cells], request['receiver_ready']):
                        continue
                    queue = lane / 'code_parent_queue'
                    outstanding = [item for item in queue.glob('*.request.json')
                        if not item.with_name(item.name.replace('.request.json', '.response.json')).exists()]
                    if outstanding:
                        continue
                    write(root / 'R115_RELEASE_PRESERVED.json', dict(expected_identity=expected,
                        completed_cycle=cycle, cycle_receipt_sha256=sha(path),
                        cells={item.name: sha(item) for item in cells},
                        request_sha256=sha(root / 'R115_RECEIVER_READY.json'),
                        outstanding_requests=0, observed_unix=time.time(), raw_stays_node=True))
                    signal.pidfd_send_signal(descriptor, signal.SIGTERM)
                    signal.pidfd_send_signal(descriptor, signal.SIGCONT)
                    stopped = False
                    if not select.select([descriptor], [], [], 30)[0]:
                        raise RuntimeError('owned_native_exit_not_verified')
                    write(root / 'R115_RELEASE_COMPLETE.json', dict(explicit_owner_release=True,
                        physical=request['physical'], completed_cycle=cycle, identity=expected,
                        preserved_sha256=sha(root / 'R115_RELEASE_PRESERVED.json'),
                        exited=True, finished_unix=time.time(), receiver_root=request['receiver_root']))
                    return
                finally:
                    if stopped:
                        signal.pidfd_send_signal(descriptor, signal.SIGCONT)
    finally:
        os.close(watch)
        os.close(descriptor)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', type=Path, required=True)
    release(parser.parse_args().root)
