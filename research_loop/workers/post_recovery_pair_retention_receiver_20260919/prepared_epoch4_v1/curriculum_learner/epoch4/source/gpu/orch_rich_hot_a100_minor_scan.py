"""Non-material UUID-to-device-minor repair; preserve every other admission gate."""

import argparse
import json
import os
from pathlib import Path
import subprocess

from gpu import orch_rich_hot_a100_scan as pinned


def minor_from_documents(documents, uuid):
    matches = []
    for text in documents:
        fields = dict(line.split(':', 1) for line in text.splitlines() if ':' in line)
        if fields.get('GPU UUID', '').strip() == uuid:
            matches.append(int(fields['Device Minor'].strip()))
    pinned.policy.require(len(matches) == 1 and 0 <= matches[0] < 256, 'unique_kernel_uuid_minor_required')
    return matches[0]


def device_minor(uuid):
    return minor_from_documents([path.read_text() for path in Path('/proc/driver/nvidia/gpus').glob('*/information')], uuid)


def scan(index, service_path):
    pinned.policy.allocation(index)
    if os.geteuid() != 0:
        result = subprocess.run(['sudo', '-n', 'env', 'CUDA_VISIBLE_DEVICES=', 'PYTHONDONTWRITEBYTECODE=1',
            'PYTHONPATH=' + str(Path(pinned.__file__).resolve().parents[1]), 'python3', '-B', str(Path(__file__).resolve()),
            '--index', str(index), '--service', str(service_path)], capture_output=True, text=True,
            timeout=90, check=True)
        return json.loads(result.stdout)
    uuid = pinned.policy.DEVICES[index]
    minor = device_minor(uuid)
    report = pinned.scan(index, service_path)
    original_issues = list(report['blocking_reasons'])
    issues = [reason for reason in original_issues if not reason.startswith('open_device_pid:')]
    processes = {entry['pid']: entry for entry in report['processes']}
    target_device = f'/dev/nvidia{minor}'
    for directory in Path('/proc').glob('[0-9]*'):
        try:
            before = pinned.identity(directory)
            opened = False
            for descriptor in (directory / 'fd').iterdir():
                try:
                    opened |= os.readlink(descriptor) == target_device
                except FileNotFoundError:
                    continue
            after = pinned.identity(directory)
            process = processes.get(int(directory.name))
            if before != after:
                issues.append('minor_scan_process_drift:' + directory.name)
            if process is not None:
                if process.get('pinned_identity') != after:
                    issues.append('minor_scan_identity_changed:' + directory.name)
                process['legacy_index_device_open'] = process.get('target_device_open')
                process['target_device_open'] = opened
                process['target_device_path'] = target_device
            if opened and not (process and process.get('verified_persistence_service')):
                issues.append('open_device_pid:' + directory.name)
        except FileNotFoundError:
            continue
        except (PermissionError, OSError) as error:
            issues.append('unknown_minor_process_visibility:' + directory.name + ':' + type(error).__name__)
    if device_minor(uuid) != minor:
        issues.append('kernel_uuid_minor_changed')
    report.update(clear=not issues, blocking_reasons=sorted(set(issues)),
                  original_index_assumption_blocking_reasons=original_issues, device_minor=minor,
                  device_path=target_device, minor_scanner_sha256=pinned.sha(__file__))
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--index', type=int, required=True)
    parser.add_argument('--service', type=Path, required=True)
    options = parser.parse_args()
    print(json.dumps(scan(options.index, options.service), indent=2))
