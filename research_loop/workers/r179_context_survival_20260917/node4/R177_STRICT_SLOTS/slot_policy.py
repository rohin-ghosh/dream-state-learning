"""NODE4 R167 outer device policy, CPU proof and one-shot owner launch."""

import argparse
import fcntl
import hashlib
import json
import math
import os
from pathlib import Path
import re
import socket
import stat
import subprocess
import sys
import time
from types import SimpleNamespace
import uuid


BASE = Path('/localhome/local-rohing')
PYTHON = str(BASE / 'v2/venv/bin/python')
HOST_SHA = 'e376292376f9f56a83e1255021f5b1a4249f1afdff42b5aed3cad36a9635834b'
HARD_END = 1789754400
LEASE = BASE / 'orch_r132_kernel_child_20260916_attempt1/control1/LEASE_BUDGET.json'
LEASE_SHA = 'ca4ead20b2b772c09e4d30e271c24988f0bbcc5f625665e6b63a441fe0e112a2'
DEVICES = {
    2: ('GPU-35dcea35-12bc-f2f3-d5d2-d2eaa8bacdd8', 1, 'Ampere'),
    5: ('GPU-2e7eb3b8-9b0b-3729-f5ff-2bbdad6a4a30', 6, 'Bacon'),
}
ROOTS = {
    2: BASE / 'orch_r177_ampere_judge_20260917',
    5: BASE / 'orch_r177_local_qwen_vision_20260917',
}
MAX_SECONDS = {2: 8000, 5: 3600}
BUNDLE = Path(__file__).resolve().parent
SCRIPT = BUNDLE / 'slot_policy.py'


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def read(path):
    return json.loads(Path(path).read_text())


def write(path, document):
    with Path(path).open('x') as stream:
        json.dump(document, stream, sort_keys=True, indent=2, allow_nan=False)
        stream.write('\n')
        stream.flush()
        os.fsync(stream.fileno())


def reference(path):
    return dict(path=str(path), sha256=sha(path))


def bound(reference_record):
    require(sha(reference_record['path']) == reference_record['sha256'], 'exact_reference_bytes')
    return read(reference_record['path'])


def scoped_path(path, root):
    path, root = Path(path), Path(root)
    require(path.is_absolute() and '..' not in path.parts and path.resolve() == path,
            'absolute_unsymlinked_path')
    require(path.is_relative_to(root), 'exact_owner_root_only')
    return path


def source_pins(root):
    root = Path(root)
    result = {}
    for path in sorted(root.rglob('*.py')):
        scoped_path(path, root)
        require(path.is_file(), 'regular_python_source')
        result[str(path.relative_to(root))] = sha(path)
    return result


def verify_bundle():
    manifest = read(BUNDLE / 'BUNDLE.json')
    require(manifest['schema'] == 'R177_NODE4_STRICT_SLOTS_BUNDLE_V1', 'bundle_schema')
    require(manifest['python_files'] == source_pins(BUNDLE), 'entire_immutable_wrapper_scanner_closure')
    require(manifest['remote_root'] == str(BUNDLE), 'exact_receiving_bundle_root')
    gate = read(BUNDLE / 'CPU_RECEIVING.json')
    require(gate['status'] == 'PASS' and gate['bundle_sha256'] == sha(BUNDLE / 'BUNDLE.json')
            and sha(gate['log']['path']) == gate['log']['sha256'], 'receiving_CPU_gate_bound')
    return reference(BUNDLE / 'BUNDLE.json')


def require_host_wall():
    require(hashlib.sha256(socket.gethostname().encode()).hexdigest() == HOST_SHA, 'exact_node4_host')
    require(sha(LEASE) == LEASE_SHA and read(LEASE)['hard_end_unix'] == HARD_END,
            'unchanged_existing_lease_receipt')
    require(time.time() + 30 < HARD_END, 'unchanged_wall_not_expired')


def validate_scope(config, now=None):
    now = time.time() if now is None else now
    physical = config['physical']
    require(type(physical) is int and physical in DEVICES, 'only_R167_physical2_or5')
    device, minor, owner = DEVICES[physical]
    require(config['schema'] == 'R177_NODE4_STRICT_SLOT_V1' and config['host_sha256'] == HOST_SHA,
            'exact_schema_host')
    require(config['gpu_uuid'] == device and config['minor'] == minor and config['owner'] == owner,
            'exact_owner_UUID_minor')
    require(config['uid'] == config['gid'] == 2524, 'exact_nonroot_identity')
    require(config['hard_end_unix'] == HARD_END and config['lease'] == dict(path=str(LEASE), sha256=LEASE_SHA),
            'unchanged_wall_and_lease')
    require(re.fullmatch(r'orch-r177-slot' + str(physical) + r'-[a-f0-9]{32}', config['unit']),
            'unique_slot_scoped_service')
    require(type(config['seconds']) is int and 0 < config['seconds'] <= MAX_SECONDS[physical],
            'bounded_owner_runtime')
    created, end = config['created_unix'], config['end_unix']
    require(type(created) in (int, float) and type(end) in (int, float)
            and math.isfinite(created) and math.isfinite(end)
            and created <= now < end and end == created + config['seconds'] and end + 30 < HARD_END,
            'bounded_prepared_runtime_inside_wall')
    require(config['mode'] in ('probe', 'launch', 'check'), 'known_mode')
    attempt = scoped_path(config['attempt'], BUNDLE / 'attempts')
    require(attempt != BUNDLE / 'attempts', 'individual_attempt')
    if config['mode'] == 'launch':
        root = scoped_path(config['workload_root'], ROOTS[physical])
        scoped_path(config['pythonpath'], root)
        entrypoint = scoped_path(config['entrypoint'], root)
        require(entrypoint.suffix == '.py', 'explicit_owner_python_entrypoint')
        command = config['command']
        require(type(command) is list and len(command) >= 3
                and all(type(part) is str and '\0' not in part for part in command)
                and command[:3] == [PYTHON, '-B', str(entrypoint)], 'explicit_pinned_python_argv_no_shell')
        require(bool(config['workload_python_files'])
                and str(entrypoint.relative_to(root)) in config['workload_python_files'], 'entrypoint_in_closure')
    return config


def validate_config(path):
    require_host_wall()
    bundle = verify_bundle()
    config = validate_scope(read(path))
    require(config['bundle'] == bundle, 'config_exact_bundle_binding')
    require(Path(path) == Path(config['attempt']) / 'CONFIG.json', 'config_exact_attempt')
    if config['mode'] == 'launch':
        require(config['workload_python_files'] == source_pins(config['workload_root']),
                'entire_workload_python_closure_unchanged')
        for item in config['metadata_pins']:
            scoped_path(item['path'], config['workload_root'])
            require(sha(item['path']) == item['sha256'], 'owner_metadata_bytes_unchanged')
        verify_probe(config['probe'], config['physical'], bundle)
    return config


def device_minor(gpu_uuid):
    matches = []
    for path in Path('/proc/driver/nvidia/gpus').glob('*/information'):
        fields = dict(line.split(':', 1) for line in path.read_text().splitlines() if ':' in line)
        if fields.get('GPU UUID', '').strip() == gpu_uuid:
            matches.append(int(fields['Device Minor'].strip()))
    require(len(matches) == 1, 'one_kernel_UUID_mapping')
    metadata = Path('/dev/nvidia' + str(matches[0])).lstat()
    require(stat.S_ISCHR(metadata.st_mode) and os.major(metadata.st_rdev) == 195
            and os.minor(metadata.st_rdev) == matches[0], 'actual_GPU_character_node')
    return matches[0]


def inherited_gpu_descriptors():
    result = []
    for descriptor in Path('/proc/self/fd').iterdir():
        try:
            target = os.readlink(descriptor)
            metadata = descriptor.stat()
            if target.startswith('/dev/nvidia') or (stat.S_ISCHR(metadata.st_mode)
                                                    and os.major(metadata.st_rdev) == 195):
                result.append(target)
        except FileNotFoundError:
            continue
    return result


def verify_device_containment(config):
    validate_scope(config)
    require_host_wall()
    require(os.getuid() == os.geteuid() == config['uid']
            and os.getgid() == os.getegid() == config['gid'], 'actual_nonroot_identity')
    cgroup = Path('/proc/self/cgroup').read_text().strip()
    require(cgroup == '0::/system.slice/' + config['unit'] + '.service', 'actual_exact_strict_service')
    status = dict(line.split(':', 1) for line in Path('/proc/self/status').read_text().splitlines() if ':' in line)
    require(status['NoNewPrivs'].strip() == '1'
            and all(int(status[key].strip(), 16) == 0 for key in ('CapEff', 'CapPrm', 'CapBnd', 'CapAmb')),
            'no_privilege_or_capability_escape')
    require(os.environ.get('CUDA_VISIBLE_DEVICES') == config['gpu_uuid'], 'exact_one_UUID_CVD')
    require(device_minor(config['gpu_uuid']) == config['minor'], 'fresh_kernel_UUID_minor')
    require(not inherited_gpu_descriptors(), 'no_inherited_NVIDIA_descriptors')
    denied = []
    for minor in range(8):
        if minor == config['minor']:
            continue
        try:
            descriptor = os.open('/dev/nvidia' + str(minor), os.O_RDWR | os.O_CLOEXEC)
        except PermissionError:
            denied.append(minor)
        else:
            os.close(descriptor)
            raise ValueError('foreign_minor_accessible')
    target = os.open('/dev/nvidia' + str(config['minor']), os.O_RDWR | os.O_CLOEXEC)
    os.close(target)
    return dict(status='PASS_STRICT_CPU_DEVICE_PROBE_NOT_MODEL_LOAD', physical=config['physical'],
                gpu_uuid=config['gpu_uuid'], minor=config['minor'], denied_foreign_minors=denied,
                target_open_close=True, uid=os.getuid(), gid=os.getgid(), cgroup=cgroup,
                boot_id=Path('/proc/sys/kernel/random/boot_id').read_text().strip(),
                pid=os.getpid(), observed_unix=time.time(), bundle=config['bundle'],
                configuration=reference(Path(config['attempt']) / 'CONFIG.json'),
                model_calls=0, existing_processes_modified=False)


def verify_probe(probe_reference, physical, bundle):
    probe = bound(probe_reference)
    device, minor, owner = DEVICES[physical]
    require(probe['status'] == 'PASS_STRICT_CPU_DEVICE_PROBE_NOT_MODEL_LOAD'
            and probe['physical'] == physical and probe['gpu_uuid'] == device and probe['minor'] == minor
            and probe['denied_foreign_minors'] == [item for item in range(8) if item != minor]
            and probe['uid'] == probe['gid'] == 2524 and probe['target_open_close'] is True
            and probe['bundle'] == bundle, 'same_bundle_complete_receiving_strict_probe')
    require(probe['boot_id'] == Path('/proc/sys/kernel/random/boot_id').read_text().strip(), 'same_receiving_boot')
    return probe


def device_containment_command(config, config_path):
    validate_scope(config)
    remaining = int(config['end_unix'] - time.time())
    require(remaining > 5, 'time_for_bounded_service')
    root = config.get('workload_root', str(BUNDLE))
    pythonpath = config.get('pythonpath', str(BUNDLE))
    properties = dict(User='2524', Group='2524', NoNewPrivileges='yes', DevicePolicy='strict',
        CapabilityBoundingSet='', AmbientCapabilities='', ProtectControlGroups='yes',
        RuntimeMaxSec=str(remaining), TimeoutStopSec='5', KillMode='control-group', WorkingDirectory=root)
    devices = ['/dev/null rw', '/dev/zero rw', '/dev/random r', '/dev/urandom r',
               '/dev/nvidia' + str(config['minor']) + ' rw', '/dev/nvidiactl rw', '/dev/nvidia-uvm rw']
    return ['sudo', '-n', 'systemd-run', '--quiet', '--wait', '--pipe', '--unit=' + config['unit'],
        *['--property=' + key + '=' + value for key, value in properties.items()], '--property=DeviceAllow=',
        *['--property=DeviceAllow=' + item for item in devices], '/usr/bin/env', '-i',
        'PATH=/usr/bin:/bin', 'HOME=' + str(BASE), 'CUDA_VISIBLE_DEVICES=' + config['gpu_uuid'],
        'PYTHONDONTWRITEBYTECODE=1', 'PYTHONPATH=' + pythonpath, 'HF_HUB_OFFLINE=1',
        'TRANSFORMERS_OFFLINE=1', 'OMP_NUM_THREADS=1', 'MKL_NUM_THREADS=1',
        'OPENBLAS_NUM_THREADS=1', 'TOKENIZERS_PARALLELISM=false', PYTHON, '-B', str(SCRIPT),
        'inner', '--config', str(config_path)]


def privileged_scan(config_path):
    config = validate_config(config_path)
    require(os.geteuid() == 0 and os.environ.get('CUDA_VISIBLE_DEVICES') == '', 'original_privileged_CPU_scan')
    require(device_minor(config['gpu_uuid']) == config['minor'], 'fresh_UUID_minor_before_scan')
    sys.path.insert(0, str(BUNDLE / 'scanner'))
    from gpu import orch_rich_hot_a100_minor_scan as minor
    from gpu import orch_r111_route_admission as admission
    def allocation(physical):
        require(physical == config['physical'], 'only_exact_owned_slot')
    minor.pinned.policy = SimpleNamespace(HOST_SHA=HOST_SHA,
        DEVICES={config['physical']: config['gpu_uuid']}, require=require, allocation=allocation)
    service = Path(config['attempt']) / 'SERVICE_IDENTITY.json'
    minor.pinned.service(service)
    return admission.scan(config['physical'], service)


def require_clear(report, config):
    require(report['scanner_euid'] == 0 and report['clear'] is True and report['blocking_reasons'] == []
            and report['gpu']['index'] == config['physical'] and report['gpu']['uuid'] == config['gpu_uuid']
            and report['host_sha256'] == HOST_SHA and report['device_minor'] == config['minor'],
            'original_privileged_report_must_be_genuinely_clear')


def scan_to_receipt(config_path, config):
    command = ['sudo', '-n', '/usr/bin/env', '-i', 'PATH=/usr/bin:/bin', 'CUDA_VISIBLE_DEVICES=',
               'PYTHONDONTWRITEBYTECODE=1', PYTHON, '-B', str(SCRIPT), 'scan', '--config', str(config_path)]
    result = subprocess.run(command, capture_output=True, text=True, timeout=120, check=False)
    attempt = Path(config['attempt'])
    write(attempt / 'SCAN_EXECUTION.json', dict(command=command, returncode=result.returncode,
                                              stdout=result.stdout, stderr=result.stderr))
    require(result.returncode == 0, 'privileged_scanner_failed_preserved_no_retry')
    report = json.loads(result.stdout)
    write(attempt / 'ORIGINAL_ADMISSION.json', report)
    require_clear(report, config)
    write(attempt / 'ADMISSION_BINDING.json', dict(report=reference(attempt / 'ORIGINAL_ADMISSION.json'),
        config=reference(config_path), verified_unix=time.time(), original_scanner_unmodified=True))


def inner(config_path):
    config = validate_config(config_path)
    require(config['mode'] in ('probe', 'launch'), 'no_check_service')
    attempt = Path(config['attempt'])
    require((attempt / 'DISPATCH_ONCE').is_dir(), 'one_shot_outer_dispatch')
    proof = verify_device_containment(config)
    write(attempt / 'CONTAINMENT.json', proof)
    if config['mode'] == 'probe':
        print(json.dumps(proof), flush=True)
        return
    admission = read(attempt / 'ADMISSION_BINDING.json')
    require(admission['config'] == reference(config_path)
            and 0 <= time.time() - admission['verified_unix'] < 100, 'fresh_exact_original_admission')
    require_clear(bound(admission['report']), config)
    validate_config(config_path)
    require(config['end_unix'] - time.time() > 10, 'time_for_model_entrypoint')
    write(attempt / 'OWNER_EXEC.json', dict(command=config['command'], observed_unix=time.time(), pid=os.getpid(),
        config=reference(config_path), admission=reference(attempt / 'ADMISSION_BINDING.json'),
        containment=reference(attempt / 'CONTAINMENT.json'), status='EXEC_REQUESTED_NOT_MODEL_LOAD', no_retry=True))
    os.execv(PYTHON, config['command'])


def launch(config_path):
    config = validate_config(config_path)
    require(os.getuid() == os.geteuid() == 2524 and os.environ.get('CUDA_VISIBLE_DEVICES', '') == '',
            'unprivileged_CPU_outer_environment')
    require(config['mode'] == 'launch', 'explicit_launch_config')
    attempt = Path(config['attempt'])
    with open('/tmp/orch_r177_strict_slot_' + str(config['physical']) + '.lock', 'a+b') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        (attempt / 'DISPATCH_ONCE').mkdir()
        scan_to_receipt(config_path, config)
        run_service(config_path, config)


def run_service(config_path, config):
    command = device_containment_command(config, config_path)
    attempt = Path(config['attempt'])
    write(attempt / 'SERVICE_COMMAND.json', dict(command=command, observed_unix=time.time()))
    with (attempt / 'SERVICE.log').open('x') as log:
        result = subprocess.run(command, stdout=log, stderr=subprocess.STDOUT, check=False,
                                timeout=int(config['end_unix'] - time.time()) + 20)
    write(attempt / 'SERVICE_EXIT.json', dict(returncode=result.returncode, finished_unix=time.time(), no_retry=True))
    require(result.returncode == 0, 'strict_service_failed_preserved_no_retry')


def prepare(physical, mode, seconds, workload_root=None, pythonpath=None, entrypoint=None,
            arguments=None, probe_path=None, metadata=None):
    require_host_wall()
    bundle = verify_bundle()
    require(type(physical) is int and physical in DEVICES, 'only_R167_physical2_or5')
    device, minor, owner = DEVICES[physical]
    now = time.time()
    attempt = BUNDLE / 'attempts' / (mode + '_' + str(physical) + '_' + str(time.time_ns()))
    config = dict(schema='R177_NODE4_STRICT_SLOT_V1', mode=mode, physical=physical, owner=owner,
        gpu_uuid=device, minor=minor, uid=2524, gid=2524, host_sha256=HOST_SHA, hard_end_unix=HARD_END,
        lease=dict(path=str(LEASE), sha256=LEASE_SHA), unit='orch-r177-slot' + str(physical) + '-' + uuid.uuid4().hex,
        seconds=seconds, created_unix=now, end_unix=now + seconds, attempt=str(attempt), bundle=bundle)
    if mode == 'launch':
        root = scoped_path(workload_root, ROOTS[physical])
        source = scoped_path(pythonpath or root, root)
        entry = scoped_path(entrypoint, root)
        pins = [reference(scoped_path(path, root)) for path in metadata or []]
        probe_reference = reference(probe_path)
        verify_probe(probe_reference, physical, bundle)
        config.update(workload_root=str(root), pythonpath=str(source), entrypoint=str(entry),
            command=[PYTHON, '-B', str(entry), *(arguments or [])], probe=probe_reference,
            metadata_pins=pins, workload_python_files=source_pins(root))
    validate_scope(config)
    attempt.mkdir(parents=True)
    config_path = attempt / 'CONFIG.json'
    write(config_path, config)
    return config_path, config


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('probe', 'check', 'prepare', 'launch', 'inner', 'scan'))
    parser.add_argument('--physical', type=int, choices=(2, 5))
    parser.add_argument('--config', type=Path)
    parser.add_argument('--seconds', type=int)
    parser.add_argument('--root', type=Path)
    parser.add_argument('--pythonpath', type=Path)
    parser.add_argument('--entrypoint', type=Path)
    parser.add_argument('--probe', type=Path)
    parser.add_argument('--bind', type=Path, action='append', default=[])
    raw_arguments = sys.argv[1:]
    separator = raw_arguments.index('--') if '--' in raw_arguments else len(raw_arguments)
    options = parser.parse_args(raw_arguments[:separator])
    if options.action in ('launch', 'inner', 'scan'):
        require(options.config is not None, 'explicit_config_required')
        if options.action == 'scan':
            print(json.dumps(privileged_scan(options.config)))
        else:
            (launch if options.action == 'launch' else inner)(options.config)
        return
    require(options.physical is not None, 'explicit_physical_required')
    arguments = raw_arguments[separator + 1:]
    config_path, config = prepare(options.physical,
        'launch' if options.action == 'prepare' else options.action,
        options.seconds if options.seconds is not None else 180, options.root, options.pythonpath,
        options.entrypoint, arguments, options.probe, options.bind)
    if options.action == 'probe':
        (Path(config['attempt']) / 'DISPATCH_ONCE').mkdir()
        run_service(config_path, config)
    elif options.action == 'check':
        scan_to_receipt(config_path, config)
    print(json.dumps(dict(config=str(config_path), attempt=config['attempt'], action=options.action)), flush=True)


if __name__ == '__main__':
    main()
