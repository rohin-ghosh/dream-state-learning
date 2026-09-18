import hashlib
import os
from pathlib import Path
import re
import socket
import stat
import time
BASE = Path('/localhome/local-rohing')
PYTHON = BASE / 'v2/venv/bin/python'
DEVICES = {2: 'GPU-d62ba12e-ff08-9e5e-ba35-14c723f6e05b', 6: 'GPU-67a989f7-2660-a76b-40e8-3619b9fa2987'}
def require(condition, reason):
    if not condition:
        raise ValueError(reason)
def require_host():
    require(socket.gethostname() == '[REDACTED_HOST]', 'exact_node5_host')

def device_containment_command(physical, minor, uid, gid, unit, source, command, lifetime):
    require(type(physical) is int and physical in DEVICES, 'explicit_NODE4_physical')
    require(type(minor) is int and 0 <= minor <= 7, 'verified_GPU_minor')
    require(type(uid) is int and uid > 0 and type(gid) is int and gid > 0, 'nonroot_probe_identity')
    require(re.fullmatch(r'orch-r136-(nvml|native)-[a-f0-9]{32}', unit), 'unique_probe_unit')
    source = Path(source)
    require(source.is_absolute() and '..' not in source.parts, 'absolute_probe_source')
    require(type(lifetime) is int and lifetime > 0, 'bounded_containment_lifetime')
    properties = dict(User=str(uid), Group=str(gid), NoNewPrivileges='yes',
        DevicePolicy='strict', CapabilityBoundingSet='', AmbientCapabilities='',
        ProtectControlGroups='yes', RuntimeMaxSec=str(lifetime), TimeoutStopSec='5',
        KillMode='control-group', WorkingDirectory=str(source))
    devices = ['/dev/null rw', '/dev/zero rw', '/dev/random r', '/dev/urandom r',
        f'/dev/nvidia{minor} rw', '/dev/nvidiactl rw', '/dev/nvidia-uvm rw']
    return ['sudo', '-n', 'systemd-run', '--quiet', '--wait', '--pipe', '--unit='+unit,
        *['--property='+key+'='+value for key, value in properties.items()],
        '--property=DeviceAllow=', *['--property=DeviceAllow='+entry for entry in devices],
        '/usr/bin/env', '-i', 'PATH=/usr/bin:/bin', 'HOME='+str(BASE),
        'CUDA_VISIBLE_DEVICES='+DEVICES[physical], 'PYTHONDONTWRITEBYTECODE=1',
        'PYTHONPATH='+str(source), 'HF_HUB_OFFLINE=1', 'TRANSFORMERS_OFFLINE=1',
        'OMP_NUM_THREADS=1', 'MKL_NUM_THREADS=1', 'TOKENIZERS_PARALLELISM=false', *command]

def gpu_descriptors():
    result = []
    for descriptor in Path('/proc/self/fd').iterdir():
        try:
            target = os.readlink(descriptor)
            if not target.startswith('/dev/nvidia'):
                continue
            metadata = descriptor.stat()
            require(stat.S_ISCHR(metadata.st_mode), 'GPU_descriptor_character_device')
            result.append(dict(fd=int(descriptor.name), path=target,
                major=os.major(metadata.st_rdev), minor=os.minor(metadata.st_rdev)))
        except FileNotFoundError:
            continue
    return sorted(result, key=lambda entry: entry['fd'])

def device_minor(gpu_uuid):
    require(gpu_uuid in DEVICES.values(), 'known_NODE4_UUID')
    matches = []
    for path in Path('/proc/driver/nvidia/gpus').glob('*/information'):
        fields = dict(line.split(':', 1) for line in path.read_text().splitlines() if ':' in line)
        if fields.get('GPU UUID', '').strip() == gpu_uuid:
            matches.append(int(fields['Device Minor'].strip()))
    require(len(matches) == 1 and 0 <= matches[0] <= 7, 'one_kernel_UUID_minor_mapping')
    node = Path('/dev/nvidia'+str(matches[0]))
    metadata = node.lstat()
    require(stat.S_ISCHR(metadata.st_mode) and os.major(metadata.st_rdev) == 195
        and os.minor(metadata.st_rdev) == matches[0], 'real_bound_GPU_character_device')
    return matches[0]

def verify_device_containment(config, plan):
    policy = config['device_containment']
    require_host()
    require(os.getuid() == policy['uid'] > 0 and os.getgid() == policy['gid'] > 0, 'nonroot_contained_identity')
    require(Path('/proc/self/cgroup').read_text().strip() ==
        '0::/system.slice/'+policy['unit']+'.service', 'exact_contained_service')
    require(device_minor(plan['gpu_uuid']) == policy['minor'], 'unchanged_UUID_minor')
    require(not gpu_descriptors(), 'no_inherited_GPU_descriptors')
    denied = []
    for minor in range(8):
        if minor == policy['minor']:
            continue
        try:
            descriptor = os.open('/dev/nvidia'+str(minor), os.O_RDWR | os.O_CLOEXEC)
        except PermissionError:
            denied.append(minor)
        else:
            os.close(descriptor)
            raise ValueError('foreign_GPU_not_denied_before_native_start')
    require(os.environ.get('CUDA_VISIBLE_DEVICES') == plan['gpu_uuid'], 'one_GPU_contained_environment')
    return dict(policy=policy, denied_foreign_minors=denied,
        checked_unix=time.time(), pid=os.getpid(), existing_processes_modified=False)
