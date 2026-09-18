"""Node1 full privileged process admission with XML and kernel minor joins."""

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import socket
import stat
import subprocess
import xml.etree.ElementTree as ET

from organism_v6 import orch_rich_hot_node1 as policy


def host():
    policy.require(hashlib.sha256(socket.gethostname().encode()).hexdigest() == policy.HOST_SHA256,
                   'node1_hashed_host_mismatch')


def process_identity(directory):
    return dict(pid=int(directory.name), uid=directory.stat().st_uid,
        start_ticks=(directory / 'stat').read_text().rsplit(')', 1)[1].split()[19],
        boot_id=Path('/proc/sys/kernel/random/boot_id').read_text().strip())


def inventory():
    host()
    document = ET.fromstring(subprocess.check_output(['nvidia-smi', '-q', '-x'], text=True))
    kernels = {}
    for path in Path('/proc/driver/nvidia/gpus').glob('*/information'):
        fields = dict(line.split(':', 1) for line in path.read_text().splitlines() if ':' in line)
        kernels[fields['GPU UUID'].strip()] = int(fields['Device Minor'].strip())
    indexes = subprocess.check_output(['nvidia-smi', '--query-gpu=index,uuid,pci.bus_id',
        '--format=csv,noheader,nounits'], text=True).splitlines()
    result = []
    xml_by_uuid = {gpu.findtext('uuid'): gpu for gpu in document.findall('gpu')}
    for line in indexes:
        index_text, uuid, pci = [part.strip() for part in line.split(',')]
        index = int(index_text)
        policy.allocation(index)
        gpu = xml_by_uuid[uuid]
        minor = int(gpu.findtext('minor_number'))
        device = Path(f'/dev/nvidia{minor}').stat()
        policy.require(uuid == policy.UUIDS[index] and minor == policy.MINORS[index]
                       and kernels[uuid] == minor and stat.S_ISCHR(device.st_mode)
                       and os.minor(device.st_rdev) == minor, 'uuid_xml_kernel_device_minor_mismatch')
        result.append(dict(index=index, uuid=uuid, minor=minor, pci=pci,
            memory_used_mib=int(gpu.findtext('fb_memory_usage/used').split()[0]),
            utilization_percent=int(gpu.findtext('utilization/gpu_util').split()[0])))
    policy.require(sorted(row['index'] for row in result) == list(range(8)), 'exact_eight_devices')
    return sorted(result, key=lambda row: row['index'])


def service(path):
    host()
    policy.require(os.geteuid() == 0, 'privileged_service_binding')
    matches = []
    for directory in Path('/proc').glob('[0-9]*'):
        try:
            if (directory / 'exe').resolve(strict=True) != Path('/usr/bin/nvidia-persistenced'):
                continue
            before = process_identity(directory)
            executable = (directory / 'exe').resolve(strict=True)
            entry = dict(before, command_sha256=hashlib.sha256((directory / 'cmdline').read_bytes()).hexdigest(),
                executable=str(executable), executable_sha256=hashlib.sha256(executable.read_bytes()).hexdigest())
            policy.require(before == process_identity(directory), 'service_identity_race')
            matches.append(entry)
        except (FileNotFoundError, ProcessLookupError):
            continue
    policy.require(len(matches) == 1, 'single_verified_persistence_service')
    with path.open('x') as stream:
        json.dump(matches[0], stream, indent=2)


def evaluate(snapshot, index):
    reasons = []
    gpu = snapshot['gpu']
    if gpu['index'] != index or gpu['uuid'] != policy.UUIDS[index] or gpu['minor'] != policy.MINORS[index]:
        reasons.append('allocation_or_minor_mismatch')
    if gpu['memory_used_mib'] > 2 or gpu['utilization_percent'] != 0:
        reasons.append('unexplained_gpu_activity')
    if any(entry['gpu_uuid'] == gpu['uuid'] for entry in snapshot['compute_processes']):
        reasons.append('active_compute')
    for entry in snapshot['processes']:
        if entry.get('vanished'):
            continue
        if entry.get('unreadable'):
            reasons.append('unknown_process_visibility:' + str(entry['pid']))
            continue
        visible = entry.get('cvd')
        if visible not in (None, '', '-1'):
            for selection in visible.split(','):
                selection = selection.strip()
                if selection in (str(index), str(gpu['minor'])) or gpu['uuid'].startswith(selection):
                    reasons.append('reserved_cvd:' + str(entry['pid']))
                if selection not in policy.UUIDS and selection not in map(str, range(8)):
                    reasons.append('ambiguous_cvd:' + str(entry['pid']))
        if entry.get('target_device_open') and not entry.get('verified_persistence_service'):
            reasons.append('mapped_minor_device_open:' + str(entry['pid']))
    return sorted(set(reasons))


def scan(index, service_path):
    host()
    policy.allocation(index)
    if os.geteuid() != 0:
        result = subprocess.check_output(['sudo', '-n', 'env', 'CUDA_VISIBLE_DEVICES=',
            'PYTHONDONTWRITEBYTECODE=1', 'PYTHONPATH=' + str(Path(__file__).resolve().parents[1]),
            'python3', '-B', '-m', 'gpu.orch_rich_hot_node1_scan', 'scan', '--index', str(index),
            '--service', str(service_path)], text=True, timeout=60)
        snapshot = json.loads(result)
        policy.require(snapshot['scanner_euid'] == 0 and snapshot['blocking_reasons'] == evaluate(snapshot, index),
                       'privileged_scanner_verdict_mismatch')
        return snapshot
    devices = inventory()
    expected = json.loads(service_path.read_text())
    snapshot = dict(created_utc=datetime.now(timezone.utc).isoformat(), scanner_euid=os.geteuid(),
        host_sha256=policy.HOST_SHA256, gpu=devices[index], devices=devices,
        service_sha256=hashlib.sha256(service_path.read_bytes()).hexdigest(), compute_processes=[], processes=[])
    for line in subprocess.check_output(['nvidia-smi', '--query-compute-apps=gpu_uuid,pid',
            '--format=csv,noheader,nounits'], text=True).splitlines():
        uuid, pid = line.split(',')
        snapshot['compute_processes'].append(dict(gpu_uuid=uuid.strip(), pid=int(pid)))
    for directory in Path('/proc').glob('[0-9]*'):
        if int(directory.name) == os.getpid():
            continue
        entry = dict(pid=int(directory.name))
        try:
            command = (directory / 'cmdline').read_bytes()
            if not command:
                continue
            before = process_identity(directory)
            entry.update(before, command_sha256=hashlib.sha256(command).hexdigest())
            environment = (directory / 'environ').read_bytes().split(b'\0')
            entry['cvd'] = next((part.split(b'=', 1)[1].decode() for part in environment
                                  if part.startswith(b'CUDA_VISIBLE_DEVICES=')), None)
            entry['target_device_open'] = False
            for descriptor in (directory / 'fd').iterdir():
                try:
                    entry['target_device_open'] |= os.readlink(descriptor) == f'/dev/nvidia{policy.MINORS[index]}'
                except FileNotFoundError:
                    pass
            if entry['pid'] == expected['pid']:
                executable = (directory / 'exe').resolve(strict=True)
                entry.update(executable=str(executable), executable_sha256=hashlib.sha256(executable.read_bytes()).hexdigest())
                entry['verified_persistence_service'] = (entry['cvd'] is None
                    and all(entry.get(key) == value for key, value in expected.items()))
            if before != process_identity(directory) or command != (directory / 'cmdline').read_bytes():
                entry['unreadable'] = 'identity_changed_during_scan'
        except (FileNotFoundError, ProcessLookupError):
            entry['vanished'] = not directory.exists()
            if not entry['vanished']:
                entry['unreadable'] = 'incomplete_process_visibility'
        except (PermissionError, OSError) as error:
            entry['unreadable'] = type(error).__name__
        snapshot['processes'].append(entry)
    snapshot['blocking_reasons'] = evaluate(snapshot, index)
    snapshot['clear'] = not snapshot['blocking_reasons']
    return snapshot


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('phase', choices=('service', 'scan', 'inventory'))
    parser.add_argument('--index', type=int)
    parser.add_argument('--service', type=Path)
    options = parser.parse_args()
    if options.phase == 'service':
        service(options.service)
    else:
        print(json.dumps(inventory() if options.phase == 'inventory' else scan(options.index, options.service)))
