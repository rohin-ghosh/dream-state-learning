"""Actual assigned-minor confinement and one-shot four-GPU pilot dispatch."""

import argparse
import errno
import json
import os
from pathlib import Path
import stat
import subprocess
import sys
import time

from ddp_pilot import require, sha, write


def verify_devices(config, opener=os.open, closer=os.close):
    require(config['physical'] in ([0, 1, 2, 3], [4, 5, 6, 7]) and len(set(config['device_uuids'])) == 4, 'assigned_four_only')
    require(os.environ.get('CUDA_VISIBLE_DEVICES') == ','.join(config['device_uuids']), 'exact_four_UUID_environment')
    for minor in range(8):
        try:
            descriptor = opener('/dev/nvidia' + str(minor), os.O_RDWR | os.O_CLOEXEC)
        except OSError as error:
            require(minor not in config['physical'] and error.errno in (errno.EPERM, errno.EACCES), 'foreign_GPU_denial_required')
        else:
            closer(descriptor)
            require(minor in config['physical'], 'foreign_GPU_open_is_not_allowed')
    for path in ['/dev/nvidiactl', '/dev/nvidia-uvm']:
        descriptor = opener(path, os.O_RDWR | os.O_CLOEXEC)
        closer(descriptor)
    require(os.getuid() == config['uid'] and os.getgid() == config['gid'], 'nonroot_service_identity')
    status = dict(line.split(':', 1) for line in Path('/proc/self/status').read_text().splitlines() if ':' in line)
    require(int(status['CapEff'].strip(), 16) == 0 and status['NoNewPrivs'].strip() == '1', 'non_escalating_service')
    require(config['unit_prefix'] in Path('/proc/self/cgroup').read_text(), 'actual_systemd_service')
    for minor, uuid, pci in zip(config['physical'], config['device_uuids'], config['pci']):
        fields = dict(line.split(':', 1) for line in (Path('/proc/driver/nvidia/gpus') / pci.lower() / 'information').read_text().splitlines() if ':' in line)
        require(fields['GPU UUID'].strip() == uuid and int(fields['Device Minor']) == minor, 'actual_kernel_UUID_minor')
        metadata = Path('/dev/nvidia' + str(minor)).stat()
        require(stat.S_ISCHR(metadata.st_mode) and os.minor(metadata.st_rdev) == minor, 'actual_device_minor')


def command(root, config, probe=False):
    unit = config['unit_prefix'] + ('probe' if probe else 'pilot')
    properties = dict(User=str(config['uid']), Group=str(config['gid']), NoNewPrivileges='yes', DevicePolicy='strict',
        CapabilityBoundingSet='', AmbientCapabilities='', ProtectControlGroups='yes', RuntimeMaxSec='90' if probe else str(config.get('runtime_max_seconds', 1800)),
        TimeoutStopSec='20', KillMode='control-group', WorkingDirectory=str(root), MemoryMax=str(256 * 1024**3), TasksMax='1024')
    devices = ['/dev/null rw', '/dev/zero rw', '/dev/random r', '/dev/urandom r', '/dev/nvidiactl rw', '/dev/nvidia-uvm rw']
    devices += ['/dev/nvidia' + str(minor) + ' rw' for minor in config['physical']]
    arguments = ['sudo', '-n', '/usr/bin/systemd-run', '--quiet', '--wait', '--pipe', '--unit=' + unit,
        *['--property=' + key + '=' + value for key, value in properties.items()], '--property=DeviceAllow=',
        *['--property=DeviceAllow=' + device for device in devices], '/usr/bin/env', '-i', 'PATH=/usr/bin:/bin',
        'HOME=' + str(root), 'TMPDIR=/tmp', 'CUDA_VISIBLE_DEVICES=' + ','.join(config['device_uuids']),
        'PYTHONDONTWRITEBYTECODE=1', 'PYTHONPATH=' + str(root), 'HF_HUB_OFFLINE=1', 'TRANSFORMERS_OFFLINE=1',
        'OMP_NUM_THREADS=2', 'MKL_NUM_THREADS=2', 'TOKENIZERS_PARALLELISM=false', 'NCCL_IB_DISABLE=1',
        'NCCL_P2P_DISABLE=1', 'NCCL_CUMEM_ENABLE=0', 'NCCL_CUMEM_HOST_ENABLE=0', 'NCCL_SOCKET_IFNAME=lo', 'NCCL_DEBUG=INFO',
        config['python'], '-B']
    if probe:
        return arguments + [str(root / 'four_gpu_admission.py'), 'probe', '--root', str(root)]
    return arguments + ['-m', 'torch.distributed.run', '--standalone', '--nnodes=1', '--nproc-per-node=4',
        str(root / config.get('entrypoint', 'ddp_pilot.py')), '--root', str(root)]


def scan(root, config):
    require(os.geteuid() == 0, 'privileged_fresh_scan')
    blocking = []
    targets = {'/dev/nvidia' + str(minor) for minor in config['physical']}
    for process in Path('/proc').glob('[0-9]*'):
        try:
            for descriptor in (process / 'fd').iterdir():
                try:
                    target = os.readlink(descriptor)
                except FileNotFoundError:
                    continue
                if target in targets:
                    blocking.append(dict(pid=int(process.name), device=target))
        except (FileNotFoundError, ProcessLookupError):
            continue
    nvml = subprocess.check_output(['nvidia-smi', '--query-compute-apps=gpu_uuid,pid', '--format=csv,noheader'], text=True, timeout=15)
    if blocking or any(uuid in nvml for uuid in config['device_uuids']):
        write(root / 'BLOCKED_ADMISSION.json', dict(observed_unix=time.time(), blockers=blocking,
            target_nvml=[line for line in nvml.splitlines() if any(uuid in line for uuid in config['device_uuids'])],
            unchanged_exclusive_admission=True))
    require(not blocking and not any(uuid in nvml for uuid in config['device_uuids']), 'assigned_devices_must_be_actually_free')
    print(json.dumps(dict(observed_unix=time.time(), privileged=True, clear=True, target_physical=config['physical'], blockers=blocking)))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('mode', choices=['scan', 'probe', 'dispatch'])
    parser.add_argument('--root', type=Path, required=True)
    arguments = parser.parse_args()
    root = arguments.root.resolve()
    config = json.loads((root / 'PILOT_CONFIG.json').read_bytes())
    if arguments.mode == 'scan':
        scan(root, config)
        return
    if arguments.mode == 'probe':
        verify_devices(config)
        write(root / 'CONFINEMENT_CPU.json', dict(passed=True, observed_unix=time.time(), allowed=config['physical'], denied=[minor for minor in range(8) if minor not in config['physical']], config_sha256=sha(root / 'PILOT_CONFIG.json')))
        return
    require(config['host'] == os.uname().nodename and config['pilot_end_unix'] > time.time() + 600, 'current_host_and_pilot_wall')
    write(root / 'DISPATCH_ATTEMPT.json', dict(started_unix=time.time(), no_retry=True, candidate_count=1, config_sha256=sha(root / 'PILOT_CONFIG.json')))
    subprocess.run(command(root, config, probe=True), check=True, timeout=100)
    receipt = subprocess.check_output(['sudo', '-n', config['python'], '-B', str(root / 'four_gpu_admission.py'), 'scan', '--root', str(root)], text=True, timeout=45)
    write(root / 'ADMISSION.json', json.loads(receipt))
    status = subprocess.run(command(root, config), check=False).returncode
    write(root / 'OUTER_EXIT.json', dict(status=status, observed_unix=time.time()))


if __name__ == '__main__':
    main()
