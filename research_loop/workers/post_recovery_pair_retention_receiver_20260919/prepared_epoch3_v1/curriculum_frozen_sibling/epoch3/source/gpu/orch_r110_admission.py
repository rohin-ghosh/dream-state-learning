"""Reconcile argv-only drift without relaxing target-GPU ownership checks."""

from copy import deepcopy
import os
from pathlib import Path

from gpu import orch_rich_hot_a100_minor_scan as minor


REASONS = ('process_identity_drift:', 'minor_scan_identity_changed:', 'minor_scan_process_drift:')
KERNEL_KEYS = ('pid', 'uid', 'start_ticks', 'boot_id')


def reconcile(report, observations):
    result = deepcopy(report)
    result['unreconciled_blocking_reasons'] = list(report['blocking_reasons'])
    result['argv_only_non_gpu_processes'] = []
    if report['scanner_euid'] != 0 or report['gpu']['memory_used_mib'] != 0:
        return result
    if any(entry['gpu_uuid'] == report['gpu']['uuid'] for entry in report['compute_processes']):
        return result
    accepted = set()
    processes = {entry['pid']: entry for entry in report['processes']}
    for pid, samples in observations.items():
        process = processes.get(pid)
        if not process or len(samples) < 3 or process.get('target_device_open') is not False:
            continue
        if process.get('cvd') not in (None, '', '-1'):
            continue
        if any(entry.get('pid') == pid for entry in report['compute_processes']):
            continue
        first = samples[0]
        if any(sample.get('visibility_complete') is not True or sample.get('target_open') is not False
               or sample.get('cvd') not in (None, '', '-1') for sample in samples):
            continue
        if any(any(sample[key] != first[key] for key in KERNEL_KEYS + ('executable_identity',))
               for sample in samples):
            continue
        if any(process.get(key) != first[key] for key in ('uid', 'start_ticks')):
            continue
        pinned = process.get('pinned_identity', {})
        if any(pinned.get(key) != first[key] for key in KERNEL_KEYS):
            continue
        if len({sample['command_sha256'] for sample in samples}) < 2:
            continue
        accepted.add(pid)
    retained = []
    removed = []
    for reason in report['blocking_reasons']:
        parts = reason.rsplit(':', 1)
        if any(reason.startswith(prefix) for prefix in REASONS) and parts[-1].isdigit() \
                and int(parts[-1]) in accepted:
            removed.append(reason)
        else:
            retained.append(reason)
    result['blocking_reasons'] = retained
    result['clear'] = not retained
    result['argv_only_non_gpu_processes'] = sorted({int(reason.rsplit(':', 1)[1]) for reason in removed})
    result['identity_observations'] = {str(pid): observations[pid]
        for pid in result['argv_only_non_gpu_processes']}
    return result


def scan(index, service_path):
    if os.geteuid() != 0:
        raise ValueError('privileged_scoped_scan_required')
    target = '/dev/nvidia' + str(minor.device_minor(minor.pinned.policy.DEVICES[index]))
    observations = {}
    original = minor.pinned.identity

    def observed(directory):
        identity = original(directory)
        sample = dict(identity, visibility_complete=False)
        try:
            executable = (directory / 'exe').stat()
            sample['executable_identity'] = [executable.st_dev, executable.st_ino]
            environment = (directory / 'environ').read_bytes().split(b'\0')
            values = [value.split(b'=', 1)[1].decode() for value in environment
                if value.startswith(b'CUDA_VISIBLE_DEVICES=')]
            if len(values) > 1:
                raise ValueError('duplicate_visibility_environment')
            sample['cvd'] = values[0] if values else None
            opened = False
            for descriptor in (directory / 'fd').iterdir():
                try:
                    opened |= os.readlink(descriptor) == target
                except FileNotFoundError:
                    continue
            sample.update(target_open=opened, visibility_complete=True)
        except (OSError, UnicodeError, ValueError):
            pass
        observations.setdefault(identity['pid'], []).append(sample)
        return identity

    minor.pinned.identity = observed
    try:
        report = minor.scan(index, Path(service_path))
    finally:
        minor.pinned.identity = original
    return reconcile(report, observations)
