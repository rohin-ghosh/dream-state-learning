"""Own hashed-host adapter over the pinned all-UID physical-device scanner."""

import argparse
import hashlib
import json
import os
from pathlib import Path
import socket
import subprocess

from gpu import orch_math_replication_guard as existing
from organism_v6 import orch_rich_hot_a100 as policy


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def host_identity():
    return hashlib.sha256(socket.gethostname().encode()).hexdigest()


def identity(directory):
    fields = (directory / 'stat').read_text().rsplit(')', 1)[1].split()
    return dict(pid=int(directory.name), uid=directory.stat().st_uid, start_ticks=fields[19],
                boot_id=Path('/proc/sys/kernel/random/boot_id').read_text().strip(),
                command_sha256=sha(directory / 'cmdline'))


def service(path):
    policy.require(os.geteuid() == 0 and host_identity() == policy.HOST_SHA, 'privileged_exact_host')
    process_ids = subprocess.check_output(['pgrep', '-x', 'nvidia-persiste'], text=True).split()
    policy.require(len(process_ids) == 1, 'single_known_persistence_service')
    directory = Path('/proc') / process_ids[0]
    before = identity(directory)
    executable = (directory / 'exe').resolve(strict=True)
    policy.require(str(executable) == '/usr/bin/nvidia-persistenced', 'wrong_service_executable')
    document = dict(before, executable=str(executable), executable_sha256=sha(executable))
    policy.require(identity(directory) == before, 'service_identity_race')
    with path.open('x') as stream:
        json.dump(document, stream, indent=2)


def scan(index, service_path):
    policy.allocation(index)
    policy.require(host_identity() == policy.HOST_SHA, 'wrong_host')
    if os.geteuid() != 0:
        result = subprocess.run(['sudo', '-n', 'env', 'CUDA_VISIBLE_DEVICES=', 'PYTHONDONTWRITEBYTECODE=1',
            'PYTHONPATH=' + str(Path(__file__).resolve().parents[1]), 'python3', '-B', '-m',
            'gpu.orch_rich_hot_a100_scan', 'scan', '--index', str(index), '--service', str(service_path)],
            capture_output=True, text=True, timeout=90, check=True)
        return json.loads(result.stdout)
    before = {}
    for directory in Path('/proc').glob('[0-9]*'):
        try:
            before[int(directory.name)] = identity(directory)
        except FileNotFoundError:
            continue
    expected = json.loads(service_path.read_text())
    policy.require(identity(Path('/proc') / str(expected['pid'])) ==
                   {key: expected[key] for key in ('pid', 'uid', 'start_ticks', 'boot_id', 'command_sha256')},
                   'service_identity_changed')
    existing.ALLOWED = set(policy.DEVICES)
    snapshot = existing.scan(index, policy.DEVICES[index], service_path)
    issues = list(snapshot['blocking_reasons'])
    for process in snapshot['processes']:
        if process.get('vanished'):
            continue
        process_id = process['pid']
        try:
            after = identity(Path('/proc') / str(process_id))
            if ((process_id in before and before[process_id] != after) or
                    any(process.get(key) != after[key] for key in ('start_ticks', 'uid', 'command_sha256'))):
                issues.append('process_identity_drift:' + str(process_id))
            process['pinned_identity'] = after
        except FileNotFoundError:
            process['vanished_after_scan'] = True
        if any(policy.DEVICES[index].startswith(part.strip()) for part in (process.get('cvd') or '').split(',')
               if part.strip().startswith('GPU-')):
            issues.append('uuid_reservation:' + str(process_id))
    snapshot.update(clear=not issues, blocking_reasons=sorted(set(issues)), host_sha256=host_identity(),
                    scanner_sha256=sha(__file__), reused_scanner_sha256=sha(existing.__file__))
    return snapshot


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('phase', choices=('service', 'scan'))
    parser.add_argument('--index', type=int)
    parser.add_argument('--service', type=Path, required=True)
    options = parser.parse_args()
    if options.phase == 'service':
        service(options.service)
    else:
        print(json.dumps(scan(options.index, options.service), indent=2))
