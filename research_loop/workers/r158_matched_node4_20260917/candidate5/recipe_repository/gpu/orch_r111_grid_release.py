"""R111 administrative handoff of owned Node5/6 at a complete grid cycle only."""

import hashlib
import argparse
import json
import os
from pathlib import Path
import signal
import socket
import time


ROOT = Path('/localhome/local-rohing/orch_r109_grid_node5_6_20260915_attempt1')
UUID = 'GPU-67a989f7-2660-a76b-40e8-3619b9fa2987'
HOST_SHA = '0cb7eb43862102b79ae0a30d2babfedfbf9598b31967a1a04122c3cf849c746d'
READY_SHA = 'cf5191a5657018b8379c6444ca3fcf7fa4fa92fe8f5e605d5e99ed7fb83a1c97'
END = 1789491720.0


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def read(path):
    return json.loads(path.read_text())


def ref(path):
    return dict(path=str(path), sha256=hashlib.sha256(path.read_bytes()).hexdigest())


def write(path, value):
    with path.open('x') as stream:
        json.dump(value, stream, indent=2, sort_keys=True)
        stream.flush()
        os.fsync(stream.fileno())


def identity(directory):
    return dict(pid=int(directory.name), uid=directory.stat().st_uid,
        start_ticks=(directory/'stat').read_text().rsplit(')',1)[1].split()[19],
        command_sha256=ref(directory/'cmdline')['sha256'],
        boot_id=Path('/proc/sys/kernel/random/boot_id').read_text().strip())


def boundary(root, complete_path):
    require(complete_path.parent.name == 'held' and complete_path.is_relative_to(root), 'full_cycle_only')
    complete = read(complete_path)
    train_path = complete_path.parent.parent/'train/COMPLETE.json'
    train = read(train_path)
    require(complete['status'] == train['status'] == 'COMPLETE'
        and complete['held_parent_free'] is True and train['held_parent_free'] is False,
        'TRAIN_and_HELD_complete')
    rows = [json.loads(line) for line in (root/'LEDGER.jsonl').read_text().splitlines() if line.strip()]
    if any(row['reserved_unix'] > complete['finished_unix'] for row in rows):
        return None
    native = [row for row in rows if row['kind'] == 'NATIVE']
    parent = [row for row in rows if row['kind'] == 'PARENT']
    for row in native:
        path = root/'calls'/f'N{row["number"]:05d}.json'
        if not path.exists():
            return None
        call = read(path)
        if call['status'] != 'COMPLETE' or call['finished_unix'] > complete['finished_unix']:
            return None
    for row in parent:
        path = root/'parent_queue'/f'P{row["number"]:04d}.response.json'
        if not path.exists() or read(path)['status'] != 'COMPLETE':
            return None
    return dict(full_cycle=ref(complete_path), train_cycle=ref(train_path),
        ledger=ref(root/'LEDGER.jsonl'), charged_native=len(native), charged_parent=len(parent),
        no_pending_calls=True, next_cycle_charged=False, outcome_selection=False)


def release(receiver_ready=None):
    require(receiver_ready is not None, 'R112_receiver_ready_required_unarmed_by_default')
    receiver = read(Path(receiver_ready))
    require(receiver.get('physical') == 6 and receiver.get('receiver') == 'Cicero'
        and receiver.get('ready') is True and bool(receiver.get('source_reference')),
        'R112_exact_receiver_ready_receipt')
    require(hashlib.sha256(socket.gethostname().encode()).hexdigest() == HOST_SHA, 'exact_node5')
    require(ref(ROOT/'READY.json')['sha256'] == READY_SHA, 'exact_old_life')
    pid = read(ROOT/'RESIDENT_LOADED.json')['pid']
    directory = Path('/proc')/str(pid)
    expected = identity(directory)
    require(expected['uid'] == os.getuid() and (directory/'cwd').resolve() == ROOT/'source_v1', 'own_source_process')
    arguments = [part.decode() for part in (directory/'cmdline').read_bytes().split(b'\0') if part]
    require(arguments[-5:] == ['-m','gpu.orch_r109_grid_run','resident','--lane','ovx3'], 'own_native_command')
    require(b'CUDA_VISIBLE_DEVICES='+UUID.encode() in (directory/'environ').read_bytes().split(b'\0'), 'physical6_only')
    output = ROOT/'R111_HANDOFF'
    output.mkdir(exist_ok=False)
    write(output/'REQUEST.json', dict(requested_unix=time.time(), identity=expected, uuid=UUID,
        directive='R111v2 direct Main/user: release physical6 to Cicero only at completed cycle boundary',
        root=str(ROOT), source=ref(Path(__file__)), receiver_ready=ref(Path(receiver_ready)),
        no_quality_selection=True, no_restart=True))
    descriptor = os.pidfd_open(pid)
    stopped = False
    seen = set()
    attempts = 0
    try:
        while time.time() < END:
            require(identity(directory) == expected, 'identity_stayed_pinned')
            paths = sorted(ROOT.glob('*/cycle*/held/COMPLETE.json'))
            candidates = [path for path in paths if path not in seen]
            if not candidates:
                time.sleep(.01)
                continue
            candidate = candidates[-1]
            seen.update(candidates)
            signal.pidfd_send_signal(descriptor, signal.SIGSTOP)
            stopped = True
            for unused in range(100):
                if (directory/'stat').read_text().rsplit(')',1)[1].split()[0] in ('T','t'):
                    break
                time.sleep(.01)
            require(identity(directory) == expected, 'stopped_identity')
            snapshot = boundary(ROOT, candidate)
            attempts += 1
            if snapshot is None:
                write(output/f'MISSED_BOUNDARY_{attempts:02d}.json', dict(observed_unix=time.time(),
                    candidate=ref(candidate), action='RESUME_UNCHANGED_NEXT_CYCLE', no_calls_retried=True))
                signal.pidfd_send_signal(descriptor, signal.SIGCONT)
                stopped = False
                continue
            inventory = {}
            for folder in ('calls','parent_queue','parent_transcripts'):
                for path in (ROOT/folder).rglob('*'):
                    if path.is_file():
                        inventory[str(path.relative_to(ROOT))] = ref(path)['sha256']
            snapshot.update(identity=expected, captured_unix=time.time(), uuid=UUID, raw_inventory=inventory,
                all_raw_preserved_in_place=True, reason='ADMINISTRATIVE_R111_BOUNDARY_REALLOCATION_NOT_MODEL_FAILURE',
                guardian_may_record_signal_as_failure=True)
            write(output/'BOUNDARY_SNAPSHOT.json', snapshot)
            require(identity(directory) == expected, 'pre_signal_identity')
            signal.pidfd_send_signal(descriptor, signal.SIGTERM)
            signal.pidfd_send_signal(descriptor, signal.SIGCONT)
            stopped = False
            until = time.time()+90
            while directory.exists() and time.time() < until:
                if (directory/'stat').read_text().rsplit(')',1)[1].split()[0] == 'Z':
                    break
                time.sleep(.2)
            exited = not directory.exists() or (directory/'stat').read_text().rsplit(')',1)[1].split()[0] == 'Z'
            write(output/'EXIT.json', dict(observed_unix=time.time(), owned_process_exited=exited,
                prior_pid=pid, boundary_snapshot=ref(output/'BOUNDARY_SNAPSHOT.json'),
                physical=6, receiver='Cicero', strict_release='PENDING_GUARD_FINAL_SCAN_AND_RECEIVER_FRESH_ADMISSION',
                no_force_kill=True, no_restart=True))
            require(exited, 'exit_pending_no_force_kill')
            return
        write(output/'WAIT_EXPIRED.json', dict(observed_unix=time.time(), native_left_unchanged=True))
    finally:
        if stopped:
            signal.pidfd_send_signal(descriptor, signal.SIGCONT)
        os.close(descriptor)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--receiver-ready', type=Path, required=True)
    release(parser.parse_args().receiver_ready)
