"""Admit read-only evaluation sharing only its own candidate's first physical GPU."""

import argparse
import errno
import json
import os
from pathlib import Path
import subprocess
import sys
import time

from ddp_pilot import require, write


def main(root, probe):
    config = json.loads((root / 'PILOT_CONFIG.json').read_bytes())
    minor = config['physical'][0]
    if probe:
        require(os.environ['CUDA_VISIBLE_DEVICES'] == config['device_uuids'][0], 'one_own_candidate_device')
        for device in range(8):
            try:
                descriptor = os.open('/dev/nvidia' + str(device), os.O_RDWR | os.O_CLOEXEC)
            except OSError as error:
                require(device != minor and error.errno in [errno.EACCES, errno.EPERM], 'unassigned_devices_denied')
            else:
                os.close(descriptor)
                require(device == minor, 'only_own_candidate_device_allowed')
        print('STRICT_SINGLE_DEVICE_DIAGNOSTIC_PROBE_PASS', flush=True)
        return
    require(os.uname().nodename == config['host'] and (root / 'training/LOADED.json').exists(), 'live_candidate_not_new_training')
    processes = subprocess.check_output(['nvidia-smi', '--query-compute-apps=gpu_uuid,pid', '--format=csv,noheader'], text=True)
    own = []
    for line in processes.splitlines():
        uuid, pid = [field.strip() for field in line.split(',')]
        if uuid != config['device_uuids'][0]:
            continue
        arguments = (Path('/proc') / pid / 'cmdline').read_bytes().decode().split('\0')
        require(str(root) in arguments and str(root / 'ddp_pilot.py') in arguments, 'only_own_candidate_current_device_users')
        own.append(int(pid))
    require(own, 'actual_candidate_processes_present')
    free = int(subprocess.check_output(['nvidia-smi', '-i', str(minor), '--query-gpu=memory.free', '--format=csv,noheader,nounits'], text=True).strip())
    require(free >= 22000, 'actual_headroom_for_bounded_readonly_sidecar')
    directory = Path(__file__).resolve().parent
    write(root / 'DIAGNOSTIC_ADMISSION.json', dict(observed_unix=time.time(), physical=minor,
        candidate_pids=own, free_MiB=free, memory_fraction_limit=0.42, deliberate_same_candidate_sharing=True,
        no_training_mutation=True, source=str(directory)))
    common = ['sudo', '-n', '/usr/bin/systemd-run', '--quiet', '--wait', '--pipe',
        '--property=User='+str(config['uid']), '--property=Group='+str(config['gid']),
        '--property=NoNewPrivileges=yes', '--property=DevicePolicy=strict', '--property=CapabilityBoundingSet=',
        '--property=AmbientCapabilities=', '--property=ProtectControlGroups=yes', '--property=KillMode=control-group',
        '--property=TimeoutStopSec=15', '--property=MemoryMax=68719476736', '--property=TasksMax=256',
        '--property=WorkingDirectory='+str(directory), '--property=DeviceAllow=']
    common += ['--property=DeviceAllow='+device for device in ['/dev/null rw','/dev/zero rw','/dev/random r',
        '/dev/urandom r','/dev/nvidiactl rw','/dev/nvidia-uvm rw','/dev/nvidia'+str(minor)+' rw']]
    environment = ['/usr/bin/env','-i','PATH=/usr/bin:/bin','HOME='+str(directory),'TMPDIR=/tmp',
        'CUDA_VISIBLE_DEVICES='+config['device_uuids'][0],'PYTHONDONTWRITEBYTECODE=1','PYTHONPATH='+str(directory),
        'HF_HUB_OFFLINE=1','TRANSFORMERS_OFFLINE=1','OMP_NUM_THREADS=2','MKL_NUM_THREADS=2',
        'TOKENIZERS_PARALLELISM=false',config['python'],'-B']
    unit = 'orch-r209-rank'+str(config['lora_rank'])+'-diagnostics'
    subprocess.run(common + ['--unit='+unit+'-probe','--property=RuntimeMaxSec=90'] + environment +
        [__file__, '--root', str(root), '--probe'], check=True, timeout=100)
    status = subprocess.run(common + ['--unit='+unit,'--property=RuntimeMaxSec='+str(int(config['training_end_unix']-time.time()))]
        + environment + [str(directory/'checkpoint_diagnostics.py'),'watch','--root',str(root)], check=False).returncode
    write(root / 'DIAGNOSTIC_OUTER_EXIT.json', dict(status=status, observed_unix=time.time()))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--probe', action='store_true')
    arguments = parser.parse_args()
    main(arguments.root, arguments.probe)
