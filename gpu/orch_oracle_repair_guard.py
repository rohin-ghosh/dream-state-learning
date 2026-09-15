"""Node3-only all-process ownership scan and one bounded four-GPU launch."""

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import signal
import socket
import subprocess
import time

from gpu.orch_math_replication_guard import command_output, verify_sources
from organism_v6.orch_oracle_repair import sha256, write


DEVICES = {
    0: 'GPU-0ee6f753-c61e-e18a-8aea-acccd3042939',
    1: 'GPU-71e5a3e2-e9c8-5caf-70d8-73794ac34821',
    2: 'GPU-41a86250-88eb-ed8a-ddfe-9d6f93515da1',
    3: 'GPU-e1277146-04f2-c38f-d1ae-1a98132f907e',
}
PYTHON = '/localhome/local-rohing/v2/venv/bin/python'
MODEL = '/localhome/local-rohing/.cache/huggingface/hub/models--Qwen--Qwen2.5-7B-Instruct/snapshots/a09a35458c702b33eeacc393d103063234e8bc28'
BUNDLE = '/tmp/astra_portable_37ec_20260914_attempt1'
LEASE_CUTOFF = datetime(2026, 9, 18, tzinfo=timezone.utc).timestamp()


def evaluate(snapshot, index):
    reasons = []
    uuid = DEVICES.get(index)
    if uuid is None or snapshot['gpu']['index'] != index or snapshot['gpu']['uuid'] != uuid:
        reasons.append('physical_allocation_mismatch')
    if snapshot['gpu']['memory_used_mib'] > 2 or snapshot['gpu']['utilization_percent'] != 0:
        reasons.append('unexplained_memory_or_utilization')
    for process in snapshot['compute_processes']:
        if process['gpu_uuid'] == uuid:
            reasons.append('active_compute_pid:' + str(process['pid']))
    for process in snapshot['processes']:
        if process.get('vanished'):
            continue
        if process.get('unreadable'):
            reasons.append('unknown_visibility:' + str(process['pid']))
            continue
        visible = process.get('cvd')
        if visible not in (None, '', '-1'):
            selections = visible.split(',')
            if str(index) in selections or uuid in selections:
                reasons.append('reserved_cvd_pid:' + str(process['pid']))
            if any(selection not in snapshot['all_gpu_uuids'] and selection not in
                   snapshot['all_gpu_indices'] for selection in selections):
                reasons.append('unknown_cvd_pid:' + str(process['pid']))
        if process.get('target_device_open') and not process.get('verified_persistence_service'):
            reasons.append('open_device_pid:' + str(process['pid']))
    return sorted(set(reasons))


def scan(index, service):
    if index not in DEVICES or socket.gethostname() != 'ipp2-ovx-p6-09':
        raise ValueError('only_node3_assigned_devices')
    if os.geteuid() != 0:
        output = subprocess.check_output(['sudo', '-n', 'env', 'CUDA_VISIBLE_DEVICES=',
                 'PYTHONDONTWRITEBYTECODE=1', 'PYTHONPATH=' + str(Path(__file__).resolve().parents[1]),
                 'python3', str(Path(__file__).resolve()), '--snapshot-only', '--index', str(index),
                 '--service', str(service)], text=True, timeout=60)
        snapshot = json.loads(output)
        if snapshot['blocking_reasons'] != evaluate(snapshot, index):
            raise ValueError('privileged_scan_policy_mismatch')
        return snapshot
    identity = json.loads(service.read_text())
    devices = [list(map(str.strip, line.split(','))) for line in command_output([
        'nvidia-smi', '--query-gpu=index,uuid,memory.used,utilization.gpu',
        '--format=csv,noheader,nounits']).splitlines()]
    target = next(row for row in devices if row[0] == str(index))
    snapshot = dict(created_utc=datetime.now(timezone.utc).isoformat(), scanner_euid=os.geteuid(),
                    gpu=dict(index=int(target[0]), uuid=target[1], memory_used_mib=int(target[2]),
                             utilization_percent=int(target[3])),
                    all_gpu_indices=[row[0] for row in devices], all_gpu_uuids=[row[1] for row in devices],
                    compute_processes=[], processes=[], service_sha256=sha256(service))
    for line in command_output(['nvidia-smi', '--query-compute-apps=gpu_uuid,pid',
                                '--format=csv,noheader,nounits']).splitlines():
        uuid, process_id = line.split(',')
        snapshot['compute_processes'].append(dict(gpu_uuid=uuid.strip(), pid=int(process_id)))
    for directory in sorted(Path('/proc').iterdir()):
        if not directory.name.isdigit() or int(directory.name) == os.getpid():
            continue
        entry = dict(pid=int(directory.name))
        try:
            commandline = (directory / 'cmdline').read_bytes()
            if not commandline:
                continue
            entry.update(uid=directory.stat().st_uid,
                         command_sha256=hashlib.sha256(commandline).hexdigest(),
                         start_ticks=(directory / 'stat').read_text().rsplit(')', 1)[1].split()[19])
            environment = (directory / 'environ').read_bytes().split(b'\0')
            entry['cvd'] = next((part.split(b'=', 1)[1].decode() for part in environment
                                 if part.startswith(b'CUDA_VISIBLE_DEVICES=')), None)
            entry['target_device_open'] = False
            for descriptor in (directory / 'fd').iterdir():
                try:
                    entry['target_device_open'] |= os.readlink(descriptor) == f'/dev/nvidia{index}'
                except FileNotFoundError:
                    pass
            if entry['pid'] == identity['pid']:
                executable = (directory / 'exe').resolve(strict=True)
                entry.update(executable=str(executable), executable_sha256=sha256(executable))
                entry['verified_persistence_service'] = bool(
                    str(executable) == '/usr/bin/nvidia-persistenced' and entry['cvd'] is None
                    and all(entry.get(key) == identity.get(key) for key in
                            ('pid', 'uid', 'start_ticks', 'command_sha256', 'executable', 'executable_sha256')))
        except (FileNotFoundError, ProcessLookupError):
            entry['vanished' if not directory.exists() else 'unreadable'] = True
        except (PermissionError, OSError) as error:
            entry['unreadable'] = type(error).__name__
        snapshot['processes'].append(entry)
    snapshot['blocking_reasons'] = evaluate(snapshot, index)
    snapshot['clear'] = not snapshot['blocking_reasons']
    return snapshot


def stop_owned(child):
    if child.poll() is None:
        os.killpg(child.pid, signal.SIGTERM)
        try:
            child.wait(timeout=15)
        except subprocess.TimeoutExpired:
            os.killpg(child.pid, signal.SIGKILL)
            child.wait(timeout=10)


def launch(root, service):
    if os.geteuid() == 0 or socket.gethostname() != 'ipp2-ovx-p6-09':
        raise ValueError('unprivileged_node3_guardian_required')
    publication = json.loads((root / 'PUBLICATION.json').read_text())
    prepared = json.loads((root / 'prepare/PREPARED.json').read_text())
    for filename in ('SOURCE_SHA256.json', 'ROSTER.json', 'prepare/PREPARED.json', 'SERVICE_IDENTITY.json'):
        if publication['files'][filename] != sha256(root / filename):
            raise ValueError('publication_hash_mismatch:' + filename)
    if (not publication['pre_gpu_evidence_complete'] or prepared['status'] != 'CPU_PREPARED'
            or prepared['native_calls'] != 0 or not prepared['base_verification']['verified']):
        raise ValueError('own_published_cpu_provenance_required')
    verify_sources(root / 'source', root / 'SOURCE_SHA256.json')
    output = root / 'run'
    output.mkdir(exist_ok=False)
    started = time.time()
    if started + 3600 >= LEASE_CUTOFF:
        raise ValueError('lease_margin_violation')
    deadline = started + 3300
    write(output / 'START.json', dict(started_unix=started, hard_deadline_unix=started + 3600,
          native_deadline_unix=deadline, assigned_gpus=DEVICES,
          publication_sha256=sha256(root / 'PUBLICATION.json'), max_calls=96, fits=0))
    children, logs = [], []
    status = 'FAILED'
    try:
        cleared = False
        for attempt in range(3):
            snapshots = []
            for index in DEVICES:
                snapshot = scan(index, service)
                write(output / f'SCAN_{attempt}_{index}.json', snapshot)
                snapshots.append(snapshot)
            if all(snapshot['clear'] for snapshot in snapshots):
                cleared = True
                break
            if attempt < 2:
                time.sleep(5)
        if not cleared:
            raise ValueError('OWNERSHIP_BLOCKED_NO_NATIVE_LAUNCH')
        for index, uuid in DEVICES.items():
            environment = dict(os.environ, CUDA_VISIBLE_DEVICES=uuid, PYTHONPATH=str(root / 'source'),
                               HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1', OMP_NUM_THREADS='1',
                               MKL_NUM_THREADS='1', TOKENIZERS_PARALLELISM='false', PYTHONDONTWRITEBYTECODE='1')
            log = (output / f'shard{index}.log').open('x')
            logs.append(log)
            command = [PYTHON, '-B', '-m', 'gpu.orch_oracle_repair_native', '--phase', 'native',
                       '--bundle', BUNDLE, '--model-dir', MODEL, '--roster', str(root / 'ROSTER.json'),
                       '--output', str(output / f'shard{index}'), '--shard', str(index),
                       '--gpu-uuid', uuid, '--deadline', str(deadline)]
            child = subprocess.Popen(command, cwd=root / 'source', env=environment,
                                     stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
            children.append(child)
            write(output / f'OWNED_{index}.json', dict(pid=child.pid, guardian_pid=os.getpid(),
                  index=index, uuid=uuid, start_ticks=Path(f'/proc/{child.pid}/stat').read_text().rsplit(')', 1)[1].split()[19],
                  launched_unix=time.time(), command=command))
        while any(child.poll() is None for child in children):
            if time.time() >= deadline + 30:
                raise TimeoutError('guardian_cleanup_margin')
            if any(child.poll() not in (None, 0) for child in children):
                raise RuntimeError('owned_native_failure')
            time.sleep(2)
        if any(child.returncode != 0 for child in children):
            raise RuntimeError('native_nonzero')
        status = 'COMPLETE'
    except BaseException as error:
        write(output / 'GUARD_FAILURE.json', dict(error_type=type(error).__name__, error=str(error)))
    finally:
        for child in children:
            stop_owned(child)
        for log in logs:
            log.close()
        finished = time.time()
        write(output / 'TERMINAL.json', dict(status=status, started_unix=started, finished_unix=finished,
              elapsed_seconds=finished - started, assigned_gpu_hours=4 * (finished - started) / 3600,
              returncodes=[child.returncode for child in children], native_children=len(children)))
    if status != 'COMPLETE':
        raise SystemExit(3)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--snapshot-only', action='store_true')
    parser.add_argument('--index', type=int, choices=range(4))
    parser.add_argument('--service', type=Path, required=True)
    parser.add_argument('--root', type=Path)
    options = parser.parse_args()
    if options.snapshot_only:
        if os.geteuid() != 0:
            raise ValueError('readonly_snapshot_must_be_privileged')
        print(json.dumps(scan(options.index, options.service), sort_keys=True))
    else:
        launch(options.root, options.service)


if __name__ == '__main__':
    main()
