"""Fresh free-device checks and finite-token eval launch; no life signals."""

import argparse
import json
import os
from pathlib import Path
import subprocess
import time

from epoch import require_config, sha


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--mode', choices=['player', 'judge'], required=True)
    options = parser.parse_args()
    root = options.root
    config_path = root / 'CONFIG.json'
    config = json.loads(config_path.read_bytes())
    require_config(config, time.time())
    if os.getuid() != 1352 or root.resolve() != root or str(root) != config['root']:
        raise ValueError('registered_receiving_user_and_canonical_root')
    physical = config[options.mode + '_physical']
    mapping = subprocess.check_output(['nvidia-smi', '--query-gpu=index,uuid,memory.used', '--format=csv,noheader,nounits'], text=True)
    row = next(line.split(',') for line in mapping.splitlines() if int(line.split(',')[0]) == physical)
    gpu = row[1].strip()
    processes = subprocess.check_output(['nvidia-smi', '--query-compute-apps=gpu_uuid,pid', '--format=csv,noheader'], text=True)
    if int(row[2]) >= 100 or gpu in processes:
        raise ValueError('owned_device_not_free_no_eviction')
    for relative, expected in json.loads((root / 'SOURCE_MANIFEST.json').read_bytes()).items():
        if sha(root / 'source' / relative) != expected:
            raise ValueError('receiving_source_manifest_mismatch')
    marker = root / (options.mode + '_DISPATCHED.json')
    if marker.exists():
        raise ValueError('one_dispatch_per_immutable_source')
    unit = root.parent.name.replace('_', '-') + '-' + root.name + '-' + options.mode
    command = ['sudo', '-n', 'systemd-run', '--unit=' + unit, '--property=User=1352', '--property=Group=1352',
        '--property=WorkingDirectory=' + str(root / 'source'),
        '--property=RuntimeMaxSec=' + str(int(config['deadline_unix'] - time.time())),
        '--property=TimeoutStopSec=15', '--property=KillMode=control-group', '--property=UMask=0077',
        '--property=DevicePolicy=closed', '--property=NoNewPrivileges=yes',
        '--property=StandardOutput=append:' + str(root / (options.mode + '.log')),
        '--property=StandardError=append:' + str(root / (options.mode + '.log'))]
    for device in ['/dev/nvidia' + str(physical), '/dev/nvidiactl', '/dev/nvidia-uvm', '/dev/nvidia-uvm-tools']:
        command.append('--property=DeviceAllow=' + device + ' rw')
    environment = dict(CUDA_VISIBLE_DEVICES=gpu, HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1',
        PYTHONDONTWRITEBYTECODE='1', PYTHONPATH=str(root / 'source'), OMP_NUM_THREADS='2', MKL_NUM_THREADS='2',
        TOKENIZERS_PARALLELISM='false', HOME='/localhome/local-rohing')
    command += ['--setenv=' + key + '=' + value for key, value in environment.items()]
    command += ['/localhome/local-rohing/v2/venv/bin/python', '-B', '-m',
        'research_loop.workers.post_recovery_age_queue_20260918.runner', '--config', str(config_path),
        '--config-sha256', sha(config_path), '--mode', options.mode]
    subprocess.run(command, check=True, capture_output=True, timeout=30)
    receipt = dict(unix=time.time(), unit=unit, mode=options.mode, physical=physical,
        config_sha256=sha(config_path), source_manifest_sha256=sha(root / 'SOURCE_MANIFEST.json'),
        deadline_unix=config['deadline_unix'], state='DISPATCHED_NOT_LOADED',
        existing_life_signals=[], prior_probe_results_modified=False)
    with marker.open('x') as stream:
        json.dump(receipt, stream, sort_keys=True)
    print(json.dumps(receipt))


if __name__ == '__main__':
    main()
