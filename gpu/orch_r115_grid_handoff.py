"""Retire only the owned original grid life at a complete receiver-ready cycle."""

import argparse
import hashlib
import json
import os
from pathlib import Path
import signal
import socket
import time

from gpu import orch_r111_grid_release as prior
from gpu import orch_r115_grid_native as native


def target(index, receiver):
    native.require((index, receiver) in ((7, 'F4_ASTRA'), (6, 'Cicero')), 'owned_receiver_pair')
    return Path(f'/localhome/local-rohing/orch_r109_grid_node5_{index}_20260915_attempt1')


def release(index, receiver_path):
    receiver = native.read(receiver_path)
    root = target(index, receiver['receiver'])
    native.require(receiver['ready'] is True and receiver['physical'] == index
        and receiver['source_reference'], 'actual_receiver_ready')
    native.require(hashlib.sha256(socket.gethostname().encode()).hexdigest() == native.HOST_SHA, 'exact_host')
    ready = native.read(root / 'READY.json')
    loaded = native.read(root / 'RESIDENT_LOADED.json')
    native.require(ready['allocation']['index'] == index, 'old_exact_physical')
    pid = loaded['pid']
    directory = Path('/proc') / str(pid)
    identity = prior.identity(directory)
    uuid = ready['allocation']['uuid']
    native.require(identity['uid'] == os.getuid() and (directory / 'cwd').resolve() == root / 'source_v1', 'own_old_process')
    native.require(('CUDA_VISIBLE_DEVICES=' + uuid).encode() in (directory / 'environ').read_bytes().split(b'\0'), 'old_UUID')
    command = (directory / 'cmdline').read_bytes().split(b'\0')
    native.require(b'gpu.orch_r109_grid_run' in command and b'resident' in command, 'old_native_only')
    output = root / 'R115_HANDOFF'
    output.mkdir()
    native.write(output / 'REQUEST.json', dict(identity=identity, receiver=receiver,
        receiver_receipt=native.ref(receiver_path), old_ready=native.ref(root / 'READY.json'), created_unix=time.time()))
    descriptor = os.pidfd_open(pid)
    stopped = False
    seen = set(root.glob('*/cycle*/held/COMPLETE.json'))
    try:
        while time.time() < native.END:
            native.require(prior.identity(directory) == identity, 'old_identity_pinned')
            fresh = set(root.glob('*/cycle*/held/COMPLETE.json')) - seen
            if not fresh:
                time.sleep(.002)
                continue
            seen.update(fresh)
            complete = max(fresh, key=lambda path: native.read(path)['finished_unix'])
            signal.pidfd_send_signal(descriptor, signal.SIGSTOP)
            stopped = True
            for unused in range(100):
                if (directory / 'stat').read_text().rsplit(')', 1)[1].split()[0] in ('T', 't'):
                    break
                time.sleep(.001)
            snapshot = prior.boundary(root, complete)
            if snapshot is None:
                signal.pidfd_send_signal(descriptor, signal.SIGCONT); stopped = False
                continue
            native.write(output / 'BOUNDARY.json', dict(snapshot=snapshot, identity=identity,
                raw_preserved_in_place=True, outcome_selection=False, observed_unix=time.time()))
            native.require(prior.identity(directory) == identity, 'pre_signal_identity')
            signal.pidfd_send_signal(descriptor, signal.SIGTERM)
            signal.pidfd_send_signal(descriptor, signal.SIGCONT); stopped = False
            until = time.time() + 90
            while directory.exists() and time.time() < until:
                if (directory / 'stat').read_text().rsplit(')', 1)[1].split()[0] == 'Z':
                    break
                time.sleep(.1)
            exited = not directory.exists() or (directory / 'stat').read_text().rsplit(')', 1)[1].split()[0] == 'Z'
            native.write(output / 'RELEASE.json', dict(prior_pid=pid, physical=index, receiver=receiver['receiver'],
                exited=exited, fresh_receiver_admission_required=True, observed_unix=time.time()))
            native.require(exited, 'own_exit_pending_no_force_kill')
            return
        native.write(output / 'WAIT_EXPIRED.json', dict(old_life_left_unchanged=True))
    finally:
        if stopped:
            signal.pidfd_send_signal(descriptor, signal.SIGCONT)
        os.close(descriptor)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--physical', type=int, choices=(6, 7), required=True)
    parser.add_argument('--receiver-ready', type=Path, required=True)
    args = parser.parse_args()
    release(args.physical, args.receiver_ready)
