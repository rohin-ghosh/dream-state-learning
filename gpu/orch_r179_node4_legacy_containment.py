"""Strict NODE4 device launch for only the two existing unconfined R179 lives."""

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import socket
import stat
import subprocess
import time

from gpu import orch_r125_continual_native as native


BASE = Path('/localhome/local-rohing')
PYTHON = BASE / 'v2/venv/bin/python'
HOST_SHA = 'e376292376f9f56a83e1255021f5b1a4249f1afdff42b5aed3cad36a9635834b'
DEVICES = {
    0: 'GPU-5b370d4d-bdcc-21d5-cf06-e9bea52e602d',
    1: 'GPU-4b071167-a06a-773c-f947-60cb8c2f7512',
}
ROOTS = {
    0: str(BASE / 'orch_r132_kernel_child_20260916_attempt1/run1'),
    1: str(BASE / 'orch_r136_raw_unparented_a40r1_20260916_attempt1/run1'),
}
MODULE = 'gpu.orch_r179_node4_legacy_containment'
require = native.require


def write(path, document):
    native.write_once(Path(path), document)


def require_host():
    require(hashlib.sha256(socket.gethostname().encode()).hexdigest() == HOST_SHA,
            'exact_node4_host_hash')


def validate_scope(config, plan):
    require(type(plan['physical']) is int and plan['physical'] in DEVICES,
            'R179_node4_legacy_slots_only')
    require(plan['gpu_uuid'] == DEVICES[plan['physical']]
            and plan['root'] == ROOTS[plan['physical']], 'exact_existing_life_and_GPU')
    require(config['host_sha256'] == HOST_SHA and config['resume'] is True,
            'same_host_saved_resume_only')
    policy = config['device_containment']
    require(policy['uid'] == policy['gid'] == 2524, 'exact_node4_nonroot_identity')
    require(type(policy['minor']) is int and 0 <= policy['minor'] <= 7,
            'verified_not_assumed_device_minor')
    require(re.fullmatch(r'orch-r136-(nvml|native)-[a-f0-9]{32}', policy['unit']),
            'unique_bounded_service_unit')
    require(config['hard_end_unix'] == plan['hard_end_unix'], 'one_bound_wall')


def device_minor(gpu_uuid):
    require(gpu_uuid in DEVICES.values(), 'known_node4_legacy_UUID')
    matches = []
    for path in Path('/proc/driver/nvidia/gpus').glob('*/information'):
        fields = dict(line.split(':', 1) for line in path.read_text().splitlines() if ':' in line)
        if fields.get('GPU UUID', '').strip() == gpu_uuid:
            matches.append(int(fields['Device Minor'].strip()))
    require(len(matches) == 1 and 0 <= matches[0] <= 7, 'one_kernel_UUID_minor_mapping')
    metadata = Path('/dev/nvidia' + str(matches[0])).lstat()
    require(stat.S_ISCHR(metadata.st_mode) and os.major(metadata.st_rdev) == 195
            and os.minor(metadata.st_rdev) == matches[0], 'real_bound_GPU_character_device')
    return matches[0]


def gpu_descriptors():
    result = []
    for descriptor in Path('/proc/self/fd').iterdir():
        try:
            target = os.readlink(descriptor)
            if target.startswith('/dev/nvidia'):
                metadata = descriptor.stat()
                require(stat.S_ISCHR(metadata.st_mode), 'GPU_descriptor_character_device')
                result.append(dict(fd=int(descriptor.name), path=target,
                    major=os.major(metadata.st_rdev), minor=os.minor(metadata.st_rdev)))
        except FileNotFoundError:
            continue
    return sorted(result, key=lambda entry: entry['fd'])


def device_containment_command(physical, minor, uid, gid, unit, source, command, lifetime):
    require(type(physical) is int and physical in DEVICES, 'R179_node4_legacy_slots_only')
    require(type(minor) is int and 0 <= minor <= 7, 'verified_not_assumed_device_minor')
    require(uid == gid == 2524, 'exact_node4_nonroot_identity')
    require(re.fullmatch(r'orch-r136-(nvml|native)-[a-f0-9]{32}', unit), 'unique_bounded_service_unit')
    require(type(lifetime) is int and 0 < lifetime <= 172800, 'bounded_containment_lifetime')
    source = Path(source)
    require(source.is_absolute() and '..' not in source.parts, 'absolute_successor_source')
    require(type(command) is list and command and all(type(part) is str for part in command),
            'explicit_command_argv')
    properties = dict(User=str(uid), Group=str(gid), NoNewPrivileges='yes',
        DevicePolicy='strict', CapabilityBoundingSet='', AmbientCapabilities='',
        ProtectControlGroups='yes', RuntimeMaxSec=str(lifetime), TimeoutStopSec='5',
        KillMode='control-group', WorkingDirectory=str(source))
    devices = ['/dev/null rw', '/dev/zero rw', '/dev/random r', '/dev/urandom r',
        f'/dev/nvidia{minor} rw', '/dev/nvidiactl rw', '/dev/nvidia-uvm rw']
    return ['sudo', '-n', 'systemd-run', '--quiet', '--wait', '--pipe', '--unit=' + unit,
        *['--property=' + key + '=' + value for key, value in properties.items()],
        '--property=DeviceAllow=', *['--property=DeviceAllow=' + entry for entry in devices],
        '/usr/bin/env', '-i', 'PATH=/usr/bin:/bin', 'HOME=' + str(BASE),
        'CUDA_VISIBLE_DEVICES=' + DEVICES[physical], 'PYTHONDONTWRITEBYTECODE=1',
        'PYTHONPATH=' + str(source), 'HF_HUB_OFFLINE=1', 'TRANSFORMERS_OFFLINE=1',
        'OMP_NUM_THREADS=1', 'MKL_NUM_THREADS=1', 'TOKENIZERS_PARALLELISM=false', *command]


def verify_device_containment(config, plan):
    validate_scope(config, plan)
    require_host()
    policy = config['device_containment']
    require(os.getuid() == policy['uid'] and os.getgid() == policy['gid'],
            'actual_nonroot_contained_identity')
    require(Path('/proc/self/cgroup').read_text().strip() ==
            '0::/system.slice/' + policy['unit'] + '.service', 'exact_contained_service')
    require(device_minor(plan['gpu_uuid']) == policy['minor'], 'unchanged_UUID_minor')
    require(not gpu_descriptors(), 'no_inherited_GPU_descriptors')
    denied = []
    for minor in range(8):
        if minor == policy['minor']:
            continue
        try:
            descriptor = os.open('/dev/nvidia' + str(minor), os.O_RDWR | os.O_CLOEXEC)
        except PermissionError:
            denied.append(minor)
        else:
            os.close(descriptor)
            raise ValueError('foreign_GPU_not_denied_before_native_start')
    require(os.environ.get('CUDA_VISIBLE_DEVICES') == plan['gpu_uuid'], 'one_GPU_contained_environment')
    return dict(policy=policy, denied_foreign_minors=denied, checked_unix=time.time(),
        pid=os.getpid(), existing_processes_modified=False)


def scan(config_path, output):
    command = ['sudo', '-n', 'env', 'CUDA_VISIBLE_DEVICES=', 'PYTHONDONTWRITEBYTECODE=1',
        'PYTHONPATH=' + str(Path(__file__).resolve().parents[1]), str(PYTHON), '-B', '-m',
        'gpu.orch_r125_continual_guard', 'scan', '--config', str(config_path)]
    report = json.loads(subprocess.check_output(command, text=True, timeout=90))
    write(output, report)
    return report


def contained_native(config_path):
    from gpu import orch_r125_continual_guard as guard
    from gpu.orch_r133_code_feedback_guard import publish_launch, reap_owned_child
    config, plan = guard.validate(config_path)
    attempt = Path(config['attempt_dir'])
    proof = verify_device_containment(config, plan)
    write(attempt / 'CONTAINMENT_VERIFIED.json', proof)
    admission = native.read(attempt / 'ADMISSION.json')
    admitted = native.read(attempt / 'ADMISSION_TIME.json')['verified_unix']
    require(admission['clear'] and admission['scanner_euid'] == 0 and not admission['blocking_reasons']
            and admission['gpu']['uuid'] == plan['gpu_uuid'] and 0 <= time.time()-admitted < 100,
            'fresh_unchanged_privileged_admission')
    remaining = int(plan['hard_end_unix']-time.time()-10)
    require(remaining > 10, 'time_for_native_load')
    command = ['timeout', '--signal=TERM', '--kill-after=5s', str(remaining)+'s', str(PYTHON),
        '-B', '-m', 'gpu.orch_r125_continual_guard', 'native', '--config', str(config_path)]
    process = None
    try:
        with (attempt / 'NATIVE.log').open('x') as log:
            process = subprocess.Popen(command, cwd=plan['source_root'], stdin=subprocess.PIPE,
                stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
            ticks = Path('/proc', str(process.pid), 'stat').read_text().rsplit(')', 1)[1].split()[19]
            publish_launch(attempt / 'LAUNCH.json', dict(pid=process.pid,
                parent_start_ticks=ticks, started_unix=time.time(), admission_verified_unix=admitted,
                admission_sha256=native.sha(attempt / 'ADMISSION.json'), guard_sha256=native.sha(config_path),
                command_sha256=native.digest(command), plan_sha256=config['plan_sha256'],
                gpu_uuid=plan['gpu_uuid'], hard_end_unix=plan['hard_end_unix'], no_retry=True,
                containment_sha256=native.sha(attempt / 'CONTAINMENT_VERIFIED.json')))
            process.stdin.write(b'LAUNCH_READY\n')
            process.stdin.close()
            status = process.wait()
        write(attempt / 'EXIT.json', dict(exit_code=status, finished_unix=time.time(), no_retry=True))
        require(status == 0, 'contained_native_failed_no_retry')
    except BaseException:
        reap_owned_child(process)
        raise


def contained_supervise(config_path):
    from gpu import orch_r125_continual_guard as guard
    config, plan = guard.validate(config_path)
    validate_scope(config, plan)
    require_host()
    policy = config['device_containment']
    require(device_minor(plan['gpu_uuid']) == policy['minor'], 'fresh_UUID_minor_before_launch')
    attempt = Path(config['attempt_dir'])
    (attempt / 'DISPATCH_ONCE').mkdir()
    report = scan(config_path, attempt / 'ADMISSION.json')
    require(report['clear'] and report['scanner_euid'] == 0 and not report['blocking_reasons']
            and report['gpu']['uuid'] == plan['gpu_uuid'], 'unchanged_global_exclusive_admission')
    write(attempt / 'ADMISSION_TIME.json', dict(verified_unix=time.time()))
    command = device_containment_command(plan['physical'], policy['minor'], policy['uid'], policy['gid'],
        policy['unit'], plan['source_root'], [str(PYTHON), '-B', '-m', MODULE,
            'contained-native', '--config', str(config_path)], int(plan['hard_end_unix']-time.time()))
    write(attempt / 'CONTAINED_COMMAND.json', dict(command=command, started_unix=time.time()))
    result = subprocess.run(command, check=False)
    write(attempt / 'SERVICE_EXIT.json', dict(returncode=result.returncode, finished_unix=time.time()))
    require(result.returncode == 0, 'contained_service_failed_no_retry')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('probe', 'contained-native', 'contained-supervise'))
    parser.add_argument('--config', type=Path, required=True)
    args = parser.parse_args()
    if args.action == 'probe':
        from gpu import orch_r125_continual_guard as guard
        config, plan = guard.validate(args.config)
        print(json.dumps(verify_device_containment(config, plan), sort_keys=True))
    elif args.action == 'contained-native':
        contained_native(args.config)
    else:
        contained_supervise(args.config)


if __name__ == '__main__':
    main()
