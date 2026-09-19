"""Node2 device0-3 binding over the existing privileged full-process scanner."""

import argparse
import json
import os
from pathlib import Path
import socket
import subprocess

from gpu import orch_math_replication_guard as existing
from organism_v6 import orch_l2_budget_readout as policy


HOST = 'ipp2-ovx-p2-08'


def identity(directory):
    fields = (directory / 'stat').read_text().rsplit(')', 1)[1].split()
    return dict(pid=int(directory.name), uid=directory.stat().st_uid, start_ticks=fields[19],
                boot_id=Path('/proc/sys/kernel/random/boot_id').read_text().strip())


def service(path):
    policy.require(os.geteuid() == 0 and socket.gethostname() == HOST, 'privileged_node2_only')
    process_ids = subprocess.check_output(['pgrep', '-x', 'nvidia-persiste'], text=True).split()
    policy.require(len(process_ids) == 1, 'single_persistence_service_required')
    directory = Path('/proc') / process_ids[0]
    before = identity(directory)
    executable = (directory / 'exe').resolve(strict=True)
    policy.require(str(executable) == '/usr/bin/nvidia-persistenced', 'persistence_executable_mismatch')
    import hashlib
    document = dict(before, command_sha256=hashlib.sha256((directory / 'cmdline').read_bytes()).hexdigest(),
        executable=str(executable), executable_sha256=hashlib.sha256(executable.read_bytes()).hexdigest())
    policy.require(identity(directory) == before, 'persistence_identity_changed')
    with path.open('x') as stream:
        json.dump(document, stream, indent=2)


def scan(index, service_path, timeout_seconds=45):
    devices = dict(policy.DEVICES.values())
    policy.require(index in devices and socket.gethostname() == HOST, 'node2_allocation_mismatch')
    if os.geteuid() != 0:
        completed = subprocess.run(['sudo', '-n', 'env', 'CUDA_VISIBLE_DEVICES=', 'PYTHONDONTWRITEBYTECODE=1',
            'PYTHONPATH=' + str(Path(__file__).resolve().parents[1]), 'python3', '-B', '-m',
            'gpu.orch_l2_budget_readout_scan', 'scan', '--index', str(index), '--service', str(service_path)],
            capture_output=True, text=True, timeout=timeout_seconds, check=True)
        return json.loads(completed.stdout)
    before = {}
    for directory in Path('/proc').glob('[0-9]*'):
        try:
            before[int(directory.name)] = identity(directory)
        except FileNotFoundError:
            continue
    expected = json.loads(service_path.read_text())
    policy.require(identity(Path('/proc') / str(expected['pid'])) == {
        key: expected[key] for key in ('pid', 'uid', 'start_ticks', 'boot_id')}, 'service_identity_drift')
    existing.ALLOWED = set(devices)
    snapshot = existing.scan(index, devices[index], service_path)
    issues = list(snapshot['blocking_reasons'])
    import hashlib
    for process in snapshot['processes']:
        if process.get('vanished'):
            continue
        directory = Path('/proc') / str(process['pid'])
        try:
            after = identity(directory)
            if ((process['pid'] in before and before[process['pid']] != after)
                    or process.get('start_ticks') != after['start_ticks'] or process.get('uid') != after['uid']
                    or process.get('command_sha256') != hashlib.sha256((directory / 'cmdline').read_bytes()).hexdigest()):
                issues.append('process_identity_drift:' + str(process['pid']))
            process['pinned_identity'] = after
        except FileNotFoundError:
            process['vanished_after_scan'] = True
        visible = process.get('cvd')
        if visible and any(devices[index].startswith(part.strip()) for part in visible.split(',')
                           if part.strip().startswith('GPU-')):
            issues.append('partial_or_exact_uuid_reservation:' + str(process['pid']))
    snapshot.update(blocking_reasons=sorted(set(issues)), clear=not issues, host=socket.gethostname(),
        scanner_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        reused_scanner_sha256=hashlib.sha256(Path(existing.__file__).read_bytes()).hexdigest())
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
