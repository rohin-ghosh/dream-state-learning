"""Dispatch only preserved owned recovery roles after CPU and physical admission."""

import hashlib
import json
import os
from pathlib import Path
import stat
import subprocess
import time


def dispatch(attempt):
    assert attempt in ('attempt2', 'attempt3')
    root = Path('/localhome/local-rohing/orch_r233_ovx4_recovery_20260918') / attempt
    ready = json.loads((root / 'CPU_READY.json').read_bytes())
    assert ready['status'] == 'CPU_PROVENANCE_PASS_NOT_DISPATCHED'
    receipts = []
    for role, mode, physical in [('shared2', 'shared', 2), ('shared3', 'shared', 3), ('base', 'scorer', 5), ('base', 'player', 4)]:
        output = root / role
        receipt_path = output / (mode + '_DISPATCHED.json')
        assert not receipt_path.exists(), 'one_owned_dispatch_per_role'
        source = output / 'source'
        manifest = json.loads((output / 'SOURCE_MANIFEST.json').read_bytes())
        expected = next(item['source_manifest_sha256'] for item in ready['receiving_tests'] if item['role'] == role)
        assert hashlib.sha256((output / 'SOURCE_MANIFEST.json').read_bytes()).hexdigest() == expected
        assert all(hashlib.sha256((source / name).read_bytes()).hexdigest() == checksum for name, checksum in manifest.items())
        config_path = output / ('CONFIG.private.json' if mode == 'shared' else 'EPOCH.json')
        config = json.loads(config_path.read_bytes())
        assert physical in (2, 3, 4, 5) and 60 < config['deadline_unix'] - time.time() < 14400
        assert config['deadline_unix'] + 21600 <= config['allocation']['conservative_lease_boundary_unix']
        mapping = subprocess.check_output(['nvidia-smi', '-i', str(physical), '--query-gpu=uuid,memory.used', '--format=csv,noheader,nounits'], text=True).strip().split(',')
        gpu = mapping[0].strip()
        assert int(mapping[1]) < 100
        assert gpu not in subprocess.check_output(['nvidia-smi', '--query-compute-apps=gpu_uuid,pid', '--format=csv,noheader'], text=True)
        if mode == 'shared':
            service = Path(config['service_root'])
            listeners = subprocess.check_output(['ss', '-xlnH'], text=True)
            for name in ('native.sock', 'base.sock'):
                path = service / name
                assert str(path) not in listeners, 'no_live_listener_replacement'
                if path.exists():
                    assert stat.S_ISSOCK(path.lstat().st_mode)
                    destination = path.with_name(name + '.expired-before-r233-recovery-' + attempt)
                    assert not destination.exists()
                    path.rename(destination)
            prior_listening = service / 'LISTENING.json'
            if prior_listening.exists():
                destination = service / ('LISTENING.before-r233-recovery-' + attempt + '.json')
                assert not destination.exists()
                prior_listening.rename(destination)
            arguments = ['research_loop.workers.rohin233_ovx4_recovery_20260918.shared_restore', '--config', str(config_path)]
        else:
            arguments = ['research_loop.workers.rohin233_ovx4_recovery_20260918.base_epoch', '--root', str(output), '--mode', mode]
        unit = 'orch-r233-recovery-' + attempt + '-' + role + '-' + mode + '-20260918'
        command = ['sudo', '-n', 'systemd-run', '--unit='+unit, '--property=User=1352', '--property=Group=1352',
            '--property=WorkingDirectory='+str(source), '--property=RuntimeMaxSec='+str(int(config['deadline_unix']-time.time())),
            '--property=TimeoutStopSec=15', '--property=KillMode=control-group', '--property=UMask=0077',
            '--property=DevicePolicy=closed', '--property=NoNewPrivileges=yes',
            '--property=StandardOutput=append:'+str(output/(mode+'.log')), '--property=StandardError=append:'+str(output/(mode+'.log'))]
        for device in ('/dev/nvidia'+str(physical), '/dev/nvidiactl', '/dev/nvidia-uvm', '/dev/nvidia-uvm-tools'):
            command.append('--property=DeviceAllow='+device+' rw')
        environment = dict(CUDA_VISIBLE_DEVICES=gpu, HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1', PYTHONDONTWRITEBYTECODE='1',
            PYTHONPATH=str(source), OMP_NUM_THREADS='2', MKL_NUM_THREADS='2', TOKENIZERS_PARALLELISM='false', HOME='/localhome/local-rohing')
        command += ['--setenv='+key+'='+value for key, value in environment.items()]
        command += ['/localhome/local-rohing/v2/venv/bin/python', '-B', '-m'] + arguments
        subprocess.run(command, capture_output=True, check=True, timeout=20)
        receipt = dict(unix=time.time(), role=role, mode=mode, physical=physical, unit=unit,
            status='DISPATCHED_NOT_YET_LOADED', deadline_unix=config['deadline_unix'],
            source_manifest_sha256=expected, pair_or_existing_life_signals=[])
        receipt_path.write_text(json.dumps(receipt, indent=2))
        receipts.append(receipt)
    return dict(unix=time.time(), receipts=receipts)
