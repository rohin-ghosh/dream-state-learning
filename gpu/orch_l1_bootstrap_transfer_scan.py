"""A1004/5/6 adapter over the existing privileged full-process scanner."""

import argparse
import hashlib
import json
import os
from pathlib import Path
import socket
import subprocess

from gpu import orch_math_replication_guard as existing
from gpu.orch_l2_rich_math_bootstrap import read, sha, write
from organism_v6 import orch_l1_bootstrap_transfer as policy


def host_identity():
    return hashlib.sha256(socket.gethostname().encode()).hexdigest()


def identity(directory):
    fields = (directory / 'stat').read_text().rsplit(')', 1)[1].split()
    return dict(pid=int(directory.name), uid=directory.stat().st_uid,
        start_ticks=fields[19], boot_id=Path('/proc/sys/kernel/random/boot_id').read_text().strip())


def service(path):
    assert os.geteuid() == 0 and host_identity() == policy.HOST_SHA
    process_ids = subprocess.check_output(['pgrep', '-x', 'nvidia-persiste'], text=True).split()
    assert len(process_ids) == 1
    directory = Path('/proc') / process_ids[0]
    before = identity(directory)
    executable = (directory / 'exe').resolve(strict=True)
    assert str(executable) == '/usr/bin/nvidia-persistenced'
    document = dict(before, command_sha256=sha(directory / 'cmdline'), executable=str(executable),
        executable_sha256=sha(executable))
    assert identity(directory) == before
    assert not path.exists()
    write(path, document)


def scan(index, service_path, timeout_seconds=60):
    devices = dict(policy.DEVICES.values())
    assert index in devices and host_identity() == policy.HOST_SHA
    if os.geteuid() != 0:
        result = subprocess.run(['sudo', '-n', 'env', 'CUDA_VISIBLE_DEVICES=', 'PYTHONDONTWRITEBYTECODE=1',
            'PYTHONPATH=' + str(Path(__file__).resolve().parents[1]), 'python3', '-B', '-m',
            'gpu.orch_l1_bootstrap_transfer_scan', 'scan', '--index', str(index),
            '--service', str(service_path)], capture_output=True, text=True, timeout=timeout_seconds, check=True)
        return json.loads(result.stdout)
    before = {}
    for directory in Path('/proc').glob('[0-9]*'):
        try:
            before[int(directory.name)] = identity(directory)
        except FileNotFoundError:
            continue
    expected_service = read(service_path)
    assert identity(Path('/proc') / str(expected_service['pid'])) == {
        key: expected_service[key] for key in ('pid', 'uid', 'start_ticks', 'boot_id')}
    existing.ALLOWED = set(devices)
    snapshot = existing.scan(index, devices[index], service_path)
    issues = list(snapshot['blocking_reasons'])
    for process in snapshot['processes']:
        if process.get('vanished'):
            continue
        process_id = process['pid']
        try:
            after = identity(Path('/proc') / str(process_id))
            if ((process_id in before and before[process_id] != after)
                    or process.get('start_ticks') != after['start_ticks'] or process.get('uid') != after['uid']
                    or process.get('command_sha256') != sha(Path('/proc') / str(process_id) / 'cmdline')):
                issues.append('process_identity_drift:' + str(process_id))
            process['pinned_identity'] = after
        except FileNotFoundError:
            process['vanished_after_scan'] = True
        visible = process.get('cvd')
        if visible and any(devices[index].startswith(part.strip()) for part in visible.split(',')
                           if part.strip().startswith('GPU-')):
            issues.append('partial_or_exact_uuid_reservation:' + str(process_id))
    snapshot.update(blocking_reasons=sorted(set(issues)), clear=not issues,
        scanner_sha256=sha(Path(__file__)), reused_scanner_sha256=sha(Path(existing.__file__)),
        host_sha256=host_identity(), boot_id=Path('/proc/sys/kernel/random/boot_id').read_text().strip())
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
