"""Bounded own-process guardian and fail-closed physical GPU admission."""

import argparse
import csv
from datetime import datetime, timezone
import io
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time


LEASE_CUTOFF = datetime(2026, 9, 19, 21, 3, tzinfo=timezone.utc).timestamp()
PYTHON = '/localhome/local-rohing/v2/venv/bin/python'
DEVICES = {'ORIGINAL37EC': (5, 'GPU-bc211959-642d-664b-3581-42a0dbe434e9'),
           'FULL_TARGET': (0, 'GPU-0ee6f753-c61e-e18a-8aea-acccd3042939'),
           'NEW_TRAJECTORY_LOSS_OFF': (1, 'GPU-71e5a3e2-e9c8-5caf-70d8-73794ac34821')}


def save(path, value):
    Path(path).write_text(json.dumps(value, sort_keys=True, indent=2) + '\n')


def query(fields, kind):
    output = subprocess.check_output(['nvidia-smi', f'--query-{kind}={fields}', '--format=csv,noheader,nounits'],
                                     text=True, timeout=20)
    return [list(map(str.strip, row)) for row in csv.reader(io.StringIO(output)) if row]


def environment_bytes(entry):
    try:
        return (entry / 'environ').read_bytes(), False
    except PermissionError:
        raw = subprocess.check_output(['sudo', '-n', '/usr/bin/cat', str(entry / 'environ')],
                                      stderr=subprocess.DEVNULL, timeout=5)
        return raw, True


def scan(index, uuid):
    gpus = query('index,uuid,memory.used', 'gpu')
    matches = [row for row in gpus if row[0] == str(index)]
    if len(matches) != 1 or matches[0][1] != uuid:
        raise ValueError('physical_uuid_changed')
    compute = query('gpu_uuid,pid,used_gpu_memory', 'compute-apps')
    owners = [row for row in compute if row[0] == uuid]
    unresolved, reservations, privileged_reads = [], [], []
    checked = 0
    for entry in Path('/proc').iterdir():
        if not entry.name.isdigit() or int(entry.name) == os.getpid():
            continue
        try:
            if entry.stat().st_uid != os.getuid():
                continue
            arguments = (entry / 'cmdline').read_bytes().split(b'\0')
            if not arguments[0]:
                continue
            executable = Path(arguments[0].decode(errors='replace')).name
            raw_environment, privileged = environment_bytes(entry)
            environment = raw_environment.split(b'\0')
            visible = next((item.split(b'=', 1)[1].decode() for item in environment
                            if item.startswith(b'CUDA_VISIBLE_DEVICES=')), None)
            checked += 1
            row = dict(pid=int(entry.name), executable=executable, cuda_visible_devices=visible)
            if privileged:
                privileged_reads.append(row)
            if visible is not None:
                devices = visible.split(',')
                if str(index) in devices or uuid in devices or visible.lower() == 'all':
                    reservations.append(row)
            elif any(name in executable.lower() for name in ('python', 'torch', 'vllm', 'jupyter')):
                unresolved.append(row)
        except FileNotFoundError:
            continue
        except (PermissionError, ProcessLookupError, subprocess.SubprocessError) as error:
            if entry.exists():
                unresolved.append(dict(pid=int(entry.name), error=type(error).__name__))
    return dict(index=index, uuid=uuid, gpu=matches[0], compute_owners=owners,
                cuda_reservations=reservations, unresolved=unresolved, checked_processes=checked,
                privileged_environment_reads=privileged_reads, process_exemptions=[],
                timestamp_utc=datetime.now(timezone.utc).isoformat(),
                safe=not owners and not reservations and not unresolved and int(matches[0][2]) <= 2)


def stop(child):
    if child.poll() is not None:
        return
    os.killpg(child.pid, signal.SIGTERM)
    try:
        child.wait(timeout=15)
    except subprocess.TimeoutExpired:
        os.killpg(child.pid, signal.SIGKILL)
        child.wait(timeout=15)


def native_stage(root, phase, state):
    limit = 1200 if phase == 'collect' else 2400
    if time.time() + limit + 30 >= LEASE_CUTOFF:
        raise ValueError('conservative_lease_end_margin')
    label = 'collection' if phase == 'collect' else state
    started = time.monotonic()
    for attempt in range(4):
        report = scan(*DEVICES[state])
        save(root / f'{label}_SCAN_{attempt}.json', report)
        if report['safe']:
            break
        time.sleep(5)
    else:
        raise ValueError('physical_admission_failed_no_unknown_whitelist')
    environment = dict(os.environ, CUDA_VISIBLE_DEVICES=DEVICES[state][1])
    command = [PYTHON, '-B', '-m', 'gpu.orch_replication', '--root', str(root), '--phase', phase, '--state', state]
    with (root / f'{label}_native.log').open('x') as stream:
        child = subprocess.Popen(command, env=environment, stdout=stream, stderr=subprocess.STDOUT, start_new_session=True)
        save(root / f'{label}_LAUNCH.json', dict(guardian_pid=os.getpid(), native_pid=child.pid, command=command,
             gpu_uuid=DEVICES[state][1], max_seconds=limit, deadline_epoch=time.time()+limit,
             lease_cutoff_epoch=LEASE_CUTOFF))

        def interrupted(signum, frame):
            stop(child)
            raise SystemExit(128 + signum)

        signal.signal(signal.SIGTERM, interrupted)
        signal.signal(signal.SIGINT, interrupted)
        try:
            code = child.wait(timeout=max(1, limit - (time.monotonic() - started)))
        except subprocess.TimeoutExpired:
            stop(child)
            code = 124
        save(root / f'{label}_EXIT.json', dict(returncode=code, elapsed_seconds=time.monotonic()-started))
        if code:
            raise RuntimeError('native_stage_failed:' + label)


def sequence(root):
    started = time.monotonic()
    native_stage(root, 'collect', 'ORIGINAL37EC')
    children = []
    try:
        for state in DEVICES:
            stream = (root / f'{state}_guard.log').open('x')
            child = subprocess.Popen([sys.executable, '-B', '-m', 'gpu.orch_replication_guard',
                      '--root', str(root), '--state', state], stdout=stream, stderr=subprocess.STDOUT,
                      start_new_session=True)
            stream.close()
            children.append(child)

        def interrupted(signum, frame):
            for child in children:
                stop(child)
            raise SystemExit(128 + signum)

        signal.signal(signal.SIGTERM, interrupted)
        signal.signal(signal.SIGINT, interrupted)
        codes = [child.wait(timeout=max(1, 3900-(time.monotonic()-started))) for child in children]
        if any(codes):
            raise RuntimeError('one_or_more_readouts_failed')
        subprocess.run([PYTHON, '-B', '-m', 'gpu.orch_replication', '--root', str(root), '--phase', 'reduce'],
                       check=True, timeout=60)
        save(root / 'TERMINAL.json', dict(status='COMPLETE', elapsed_seconds=time.monotonic()-started))
    finally:
        for child in children:
            stop(child)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--state', choices=DEVICES)
    parser.add_argument('--scan', action='store_true')
    parser.add_argument('--sequence', action='store_true')
    options = parser.parse_args()
    os.environ.update(CUDA_VISIBLE_DEVICES='', HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1',
                      TOKENIZERS_PARALLELISM='false', OMP_NUM_THREADS='1', MKL_NUM_THREADS='1',
                      PYTHONDONTWRITEBYTECODE='1')
    if options.scan:
        save(options.root / 'ADMISSION.json', {state: scan(*device) for state, device in DEVICES.items()})
    elif options.sequence:
        sequence(options.root)
    else:
        native_stage(options.root, 'readout', options.state)


if __name__ == '__main__':
    main()
