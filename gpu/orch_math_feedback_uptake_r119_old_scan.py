"""Full root scanner with bounded per-process identity-consistent FD/CVD samples."""

import hashlib
import json
import os
from pathlib import Path
import select
import sys
import time

import gpu
import organism_v6

LEGACY = Path('/localhome/local-rohing/orch_math_feedback_uptake_r110_20260915_attempt1/source')
if LEGACY.is_dir():
    gpu.__path__ = [str(LEGACY/'gpu'), *gpu.__path__]
    organism_v6.__path__ = [str(LEGACY/'organism_v6'), *organism_v6.__path__]
from gpu import orch_math_feedback_uptake_r110_run as old

pinned = old.machinery.previous.scanner.pinned
legacy = pinned.existing
minor_api = old.machinery.previous.scanner
ROOT = old.ROOT
INDEX = 2
UUID = old.policy.DEVICES[INDEX]


def kernel_identity(identity):
    return {name: identity[name] for name in ('pid', 'uid', 'start_ticks', 'boot_id', 'exe_device', 'exe_inode')}


def process_identity(directory):
    identity = pinned.identity(directory)
    try:
        executable = (directory/'exe').stat()
        identity.update(exe_device=executable.st_dev, exe_inode=executable.st_ino)
    except FileNotFoundError:
        if identity['command_sha256'] != hashlib.sha256(b'').hexdigest():
            raise
        identity.update(exe_device=None, exe_inode=None)
    return identity


def reservation(entry, environments, opened):
    entry = dict(entry, cvd=environments[-1], target_device_open=any(opened),
        cvd_observations=environments, fd_observations=opened)
    if environments[0] != environments[-1]:
        entry['unreadable'] = 'cvd_transition'
    return entry


def inactive_kind(command_sha256, state, flags, descriptor_count):
    if command_sha256 != hashlib.sha256(b'').hexdigest() or descriptor_count:
        return None
    if flags & 0x00200000:
        return 'kernel_thread_no_userspace_or_fds'
    if state == 'Z':
        return 'zombie_no_userspace_or_fds'
    return None


def inactive_process(directory):
    before = pinned.identity(directory)
    fields = (directory/'stat').read_text().rsplit(')', 1)[1].split()
    kind = inactive_kind(before['command_sha256'], fields[0], int(fields[6]), len(list((directory/'fd').iterdir())))
    if kind is None:
        return None
    after = pinned.identity(directory)
    final = (directory/'stat').read_text().rsplit(')', 1)[1].split()
    if before != after or fields[0] != final[0] or fields[6] != final[6] or list((directory/'fd').iterdir()):
        return dict(before, unreadable='inactive_process_transition')
    return dict(before, cvd=None, target_device_open=False, process_class=kind,
        pinned_identity=after, identity_consistent=True, verified_empty_fds=True)


def stable_capture(sample, attempts=3):
    observed = []
    for attempt in range(attempts):
        before, entry, after = sample()
        observed.append(dict(before=before, observation=entry, after=after))
        if kernel_identity(before) != kernel_identity(after):
            return dict(entry, unreadable='kernel_process_identity_changed'), observed
        if before == after:
            return dict(entry, pinned_identity=after, identity_consistent=True), observed
    return dict(observed[-1]['observation'], unreadable='unstable_process_identity'), observed


def capture(directory, minor, expected):
    descriptor = os.pidfd_open(int(directory.name))
    try:
        def sample():
            before = process_identity(directory)
            environments, opened = [], []
            for observation in range(2):
                environment = (directory/'environ').read_bytes().split(b'\0')
                environments.append(next((part.split(b'=', 1)[1].decode() for part in environment if part.startswith(b'CUDA_VISIBLE_DEVICES=')), None))
                target_open = False
                for link in (directory/'fd').iterdir():
                    try:
                        target_open |= os.readlink(link) == f'/dev/nvidia{minor}'
                    except FileNotFoundError:
                        continue
                opened.append(target_open)
            entry = reservation(dict(before, target_device_path=f'/dev/nvidia{minor}'), environments, opened)
            if before['pid'] == expected['pid']:
                executable = (directory/'exe').resolve(strict=True)
                entry.update(executable=str(executable), executable_sha256=pinned.sha(executable))
                entry['verified_persistence_service'] = bool(environments == [None, None] and all(entry.get(key) == expected.get(key)
                    for key in ('pid', 'uid', 'start_ticks', 'boot_id', 'command_sha256', 'executable', 'executable_sha256')))
            return before, entry, process_identity(directory)
        entry, observations = stable_capture(sample)
        return entry, observations
    finally:
        os.close(descriptor)


def evaluate(snapshot):
    legacy.ALLOWED = {INDEX}
    reasons = legacy.evaluate_snapshot(snapshot, INDEX, UUID)
    for process in snapshot['processes']:
        for part in (process.get('cvd') or '').split(','):
            if part.strip().startswith('GPU-') and UUID.startswith(part.strip()):
                reasons.append('uuid_reservation:' + str(process['pid']))
    if snapshot['scanner_euid'] != 0:
        reasons.append('root_visibility_required')
    return sorted(set(reasons))


def scan():
    old.configure(ROOT)
    old.require(os.geteuid() == 0, 'root_full_proc_required')
    old.require(pinned.host_identity() == old.policy.HOST_SHA, 'pinned_host')
    expected = json.loads((ROOT/'SERVICE_IDENTITY.json').read_text())
    old.require(Path('/proc/sys/kernel/random/boot_id').read_text().strip() == expected['boot_id'], 'pinned_boot')
    minor = minor_api.device_minor(UUID)
    def gpu_snapshot():
        fields = legacy.command_output(['nvidia-smi', '-i', str(INDEX), '--query-gpu=index,uuid,memory.used,utilization.gpu', '--format=csv,noheader,nounits']).split(',')
        compute = []
        for line in legacy.command_output(['nvidia-smi', '--query-compute-apps=gpu_uuid,pid', '--format=csv,noheader,nounits']).splitlines():
            device, pid = line.split(',')
            compute.append(dict(gpu_uuid=device.strip(), pid=int(pid)))
        return dict(index=int(fields[0]), uuid=fields[1].strip(), memory_used_mib=int(fields[2]), utilization_percent=int(fields[3])), compute
    device, compute = gpu_snapshot()
    report = dict(created_unix=time.time(), scanner_euid=os.geteuid(), scanner_pid=os.getpid(), gpu=device,
        compute_processes=compute, processes=[], process_attempts={}, device_minor=minor, host_sha256=pinned.host_identity(),
        scanner_sha256=pinned.sha(__file__), service_identity_sha256=pinned.sha(ROOT/'SERVICE_IDENTITY.json'),
        identity_method='pidfd_plus_exact_before_after_per_process_fd_cvd_sample', discarded_blockers=[])
    scanned = set()
    for census in range(3):
        directories = [path for path in Path('/proc').glob('[0-9]*') if int(path.name) not in scanned]
        if not directories:
            break
        for directory in directories:
            pid = int(directory.name)
            try:
                inactive = inactive_process(directory)
                entry, attempts = (inactive, []) if inactive is not None else capture(directory, minor, expected)
                report['process_attempts'][str(pid)] = attempts
                report['processes'].extend(attempt['observation'] for attempt in attempts[:-1])
                report['processes'].append(entry)
            except (FileNotFoundError, ProcessLookupError):
                report['processes'].append(dict(pid=pid, vanished=not directory.exists(),
                    **({} if not directory.exists() else dict(unreadable='process_visibility_race'))))
            except (PermissionError, OSError, ValueError) as error:
                report['processes'].append(dict(pid=pid, unreadable=type(error).__name__))
            scanned.add(pid)
    after, after_compute = gpu_snapshot()
    report['blocking_reasons'] = evaluate(report)
    report['blocking_reasons'].extend(evaluate(dict(report, gpu=after, compute_processes=after_compute)))
    report['gpu_after'] = after
    report['compute_processes_after'] = after_compute
    if minor_api.device_minor(UUID) != minor:
        report['blocking_reasons'].append('kernel_uuid_minor_changed')
    if not any(process.get('verified_persistence_service') for process in report['processes']):
        report['blocking_reasons'].append('persistence_service_not_verified')
    report['blocking_reasons'] = sorted(set(report['blocking_reasons']))
    report['clear'] = not report['blocking_reasons']
    report['finished_unix'] = time.time()
    return report


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--index', type=int, choices=(1, 2), required=True)
    args = parser.parse_args()
    INDEX = args.index
    UUID = old.policy.DEVICES[INDEX]
    print(json.dumps(scan()))
