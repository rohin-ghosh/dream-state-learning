"""R177 adaptation of established strict systemd GPU-device containment."""

import argparse
import errno
import hashlib
import json
import os
from pathlib import Path
import stat
import subprocess
import sys
import time

from gpu import ny_caption_data as data


DEVICE = 'GPU-35dcea35-12bc-f2f3-d5d2-d2eaa8bacdd8'
MINOR = 1
PYTHON = '/localhome/local-rohing/v2/venv/bin/python'
MODULE = 'research_loop.workers.r177_caption_game_stage1_20260917.data_judge.physical2_confinement'


def command(root, inventory_sha256, mode, max_seconds=7200):
    data.require(mode in ('probe', 'train'), 'exact_contained_mode')
    data.require(type(max_seconds) is int and 0 < max_seconds <= 7200, 'bounded_outer_runtime')
    unit = 'orch-r177-judge-'+mode+'-'+inventory_sha256[:24]
    properties = dict(User='2524', Group='2524', NoNewPrivileges='yes', DevicePolicy='strict',
        CapabilityBoundingSet='', AmbientCapabilities='', ProtectControlGroups='yes',
        RuntimeMaxSec='60' if mode == 'probe' else str(max_seconds), TimeoutStopSec='5',
        KillMode='control-group', WorkingDirectory=str(root), MemoryMax=str(24*1024**3), TasksMax='128')
    devices = ['/dev/null rw', '/dev/zero rw', '/dev/random r', '/dev/urandom r',
        '/dev/nvidia1 rw', '/dev/nvidiactl rw', '/dev/nvidia-uvm rw']
    return ['sudo', '-n', '/usr/bin/systemd-run', '--quiet', '--wait', '--pipe', '--unit='+unit,
        *['--property='+key+'='+value for key, value in properties.items()], '--property=DeviceAllow=',
        *['--property=DeviceAllow='+entry for entry in devices], '/usr/bin/env', '-i',
        'PATH=/usr/bin:/bin', 'HOME='+str(root), 'TMPDIR=/tmp', 'CUDA_VISIBLE_DEVICES='+DEVICE,
        'PYTHONDONTWRITEBYTECODE=1', 'PYTHONPATH='+str(root), 'HF_HUB_OFFLINE=1', 'TRANSFORMERS_OFFLINE=1',
        'OMP_NUM_THREADS=2', 'MKL_NUM_THREADS=2', 'TOKENIZERS_PARALLELISM=false',
        PYTHON, '-B', '-m', MODULE, mode, '--root', str(root), '--inventory-sha256', inventory_sha256,
        '--unit', unit]


def device_checks(opener=os.open, closer=os.close):
    allowed, denied = [], []
    for minor in range(8):
        path = '/dev/nvidia'+str(minor)
        try:
            descriptor = opener(path, os.O_RDWR | os.O_CLOEXEC)
        except OSError as error:
            data.require(minor != MINOR and error.errno in (errno.EPERM, errno.EACCES), 'foreign_minor_actual_permission_denial')
            denied.append(minor)
        else:
            closer(descriptor)
            data.require(minor == MINOR, 'foreign_GPU_open_allowed_abort')
            allowed.append(path)
    for path in ('/dev/nvidiactl', '/dev/nvidia-uvm'):
        descriptor = opener(path, os.O_RDWR | os.O_CLOEXEC)
        closer(descriptor)
        allowed.append(path)
    data.require(len(denied) == 7, 'seven_foreign_minors_denied')
    return dict(allowed_open_close=allowed, denied_foreign_minors=denied)


def verify(root, expected, unit):
    from research_loop.workers.r177_caption_game_stage1_20260917.data_judge import released_receiving
    released_receiving.verified(root, expected)
    data.require(os.getuid() == os.getgid() == 2524, 'exact_nonroot_identity')
    cgroup = Path('/proc/self/cgroup').read_text().strip()
    data.require(cgroup == '0::/system.slice/'+unit+'.service', 'actual_strict_service_cgroup')
    status = dict(line.split(':', 1) for line in Path('/proc/self/status').read_text().splitlines() if ':' in line)
    data.require(int(status['CapEff'].strip(), 16) == 0 and status['NoNewPrivs'].strip() == '1', 'unprivileged_non_escalating_service')
    info = Path('/proc/driver/nvidia/gpus/0000:41:00.0/information')
    fields = dict(line.split(':', 1) for line in info.read_text().splitlines() if ':' in line)
    data.require(fields['GPU UUID'].strip() == DEVICE and int(fields['Device Minor'].strip()) == MINOR, 'current_kernel_UUID_minor_binding')
    metadata = Path('/dev/nvidia1').lstat()
    data.require(stat.S_ISCHR(metadata.st_mode) and os.major(metadata.st_rdev) == 195
        and os.minor(metadata.st_rdev) == MINOR, 'actual_GPU_character_device')
    for descriptor in Path('/proc/self/fd').iterdir():
        try:
            data.require(not os.readlink(descriptor).startswith('/dev/nvidia'), 'no_inherited_GPU_fds')
        except FileNotFoundError:
            pass
    checks = device_checks()
    data.require(os.environ.get('CUDA_VISIBLE_DEVICES') == DEVICE, 'exact_UUID_environment')
    return dict(schema='NY_ACTUAL_STRICT_PHYSICAL2_CONFINEMENT_V1', status='PASS_CPU_OPEN_CLOSE_ONLY',
        inventory_sha256=expected, unit=unit, cgroup=cgroup, pid=os.getpid(), uid=os.getuid(), gid=os.getgid(),
        device_uuid=DEVICE, target_minor=MINOR, checks=checks, kernel_metadata_sha256=data.file_ref(info)['sha256'],
        GPU_model_calls=0, torch_imported=False, existing_processes_modified=False, observed_unix=time.time())


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('mode', choices=('dispatch-probe', 'dispatch-train', 'probe', 'train'))
    parser.add_argument('--root', required=True)
    parser.add_argument('--inventory-sha256', required=True)
    parser.add_argument('--unit')
    args = parser.parse_args()
    root = Path(args.root).resolve()
    if args.mode.startswith('dispatch-'):
        mode = args.mode.removeprefix('dispatch-')
        inventory_ref = dict(path=str(root/'INVENTORY.json'), sha256=args.inventory_sha256)
        inventory = data.bound(inventory_ref)
        config = data.bound(inventory['config'])
        argv = command(root, args.inventory_sha256, mode, config['max_seconds'])
        if mode == 'train':
            probe = data.bound(data.file_ref(root/'CONFINEMENT_CPU_PROOF.json'))
            data.require(probe['inventory_sha256'] == args.inventory_sha256
                and probe['checks']['denied_foreign_minors'] == [0, 2, 3, 4, 5, 6, 7], 'prior_actual_strict_device_proof')
        data.private_write(root/('OUTER_'+mode.upper()+'_COMMAND.json'), dict(command=argv,
            command_sha256=data.digest(argv), source=data.file_ref(Path(__file__).resolve()), issued_unix=time.time()))
        raise SystemExit(subprocess.run(argv, check=False).returncode)
    proof = verify(root, args.inventory_sha256, args.unit)
    reference = data.private_write(root/('CONFINEMENT_CPU_PROOF.json' if args.mode == 'probe' else 'TRAIN_CONFINEMENT_PROOF.json'), proof)
    print(json.dumps(dict(status=proof['status'], receipt=reference, target_minor=MINOR, foreign_denied=7)), flush=True)
    if args.mode == 'train':
        from research_loop.workers.r177_caption_game_stage1_20260917.data_judge import released_receiving
        released_receiving.run(root, args.inventory_sha256)


if __name__ == '__main__':
    main()
