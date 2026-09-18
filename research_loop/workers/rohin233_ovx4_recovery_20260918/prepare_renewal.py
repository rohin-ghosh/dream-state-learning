"""Warm lease-bound successors on their assigned physical scorers only."""

import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import time
import xml.etree.ElementTree as XML


BASE = Path('/localhome/local-rohing')
MODULE = 'research_loop.workers.rohin233_ovx4_recovery_20260918'


def read(path):
    return json.loads(Path(path).read_bytes())


def ref(path):
    path = Path(path).resolve()
    return dict(path=str(path), sha256=hashlib.sha256(path.read_bytes()).hexdigest())


def write(path, value):
    with Path(path).open('x') as stream:
        json.dump(value, stream, sort_keys=True)


def unit_run(root, source, role, deadline, module, config_path, physical=None):
    unit = 'orch-r233-lease-' + role + '-20260918'
    command = ['sudo', '-n', 'systemd-run', '--unit='+unit, '--property=User='+str(os.getuid()),
        '--property=Group='+str(os.getgid()), '--property=WorkingDirectory='+str(source),
        '--property=RuntimeMaxSec='+str(int(deadline-time.time())), '--property=TimeoutStopSec=15',
        '--property=KillMode=control-group', '--property=UMask=0077', '--property=DevicePolicy=closed',
        '--property=NoNewPrivileges=yes', '--property=StandardOutput=append:'+str(root / (role+'.log')),
        '--property=StandardError=append:'+str(root / (role+'.log'))]
    environment = dict(PYTHONPATH=str(source), PYTHONDONTWRITEBYTECODE='1', HOME=str(BASE),
        HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1', OMP_NUM_THREADS='2', MKL_NUM_THREADS='2', TOKENIZERS_PARALLELISM='false')
    if physical is not None:
        document = XML.fromstring(subprocess.check_output(['nvidia-smi', '-q', '-x']))
        gpu = document.findall('gpu')[physical]
        environment['CUDA_VISIBLE_DEVICES'] = gpu.findtext('uuid')
        minor = int(gpu.findtext('minor_number'))
        free = int(gpu.findtext('fb_memory_usage/free').split()[0])
        assert free >= 16000, 'measured_overlap_memory_admission'
        for device in ('/dev/nvidia'+str(minor), '/dev/nvidiactl', '/dev/nvidia-uvm', '/dev/nvidia-uvm-tools'):
            command += ['--property=DeviceAllow='+device+' rw']
    command += ['--setenv='+key+'='+value for key,value in environment.items()]
    command += [str(BASE / 'v2/venv/bin/python') if physical is not None else '/usr/bin/python3',
        '-B', '-m', module, '--config', str(config_path)]
    subprocess.run(command, check=True, capture_output=True, timeout=20)
    return unit


def prepare(payload):
    alias = payload['alias']
    assert alias in ('ovx4', 'node4')
    lease = payload['lease']['bounds'][alias]
    if alias == 'ovx4':
        assert os.getuid() == 1352
        previous = BASE / 'orch_r233_ovx4_recovery_20260918/attempt3'
        roles = [('shared2', 'shared', 6, 400982, previous / 'shared2/CONFIG.private.json'),
            ('shared3', 'shared', 7, 400990, previous / 'shared3/CONFIG.private.json')]
    else:
        assert os.getuid() == 2524
        roles = [('p3', 'p3', 0, 254441, BASE / 'orch_r233_p3_scorer_recovery_20260918/attempt4/CONFIG.private.json')]
    results = []
    for role, kind, physical, predecessor, prior_path in roles:
        assert Path('/proc', str(predecessor)).exists(), 'verified_original_owner_running'
        prior = read(prior_path)
        root = BASE / 'orch_r233_lease_renewal_20260918/attempt2' / role
        root.mkdir(parents=True, exist_ok=False, mode=0o700)
        source = root / 'source'
        shutil.copytree(prior['source_root'], source)
        for name, content in payload['files'].items():
            destination = source / MODULE.replace('.', '/') / name
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_text(content)
        files = {str(path.relative_to(source)):ref(path)['sha256'] for path in source.rglob('*.py')}
        write(root / 'SOURCE_MANIFEST.json', files)
        write(root / 'LEASE_SOURCE.json', payload['lease'])
        config = dict(root=str(root), kind=kind, physical=physical, deadline_unix=lease['job_end_unix'],
            lease_boundary_unix=lease['conservative_lease_end_unix'], lease_source=ref(root / 'LEASE_SOURCE.json'),
            prior_config=ref(prior_path), predecessor_pid=predecessor,
            predecessor_start_ticks=Path('/proc', str(predecessor), 'stat').read_text().rsplit(')',1)[1].split()[19],
            source_manifest=ref(root / 'SOURCE_MANIFEST.json'), socket='/tmp/r233-lease-'+role+'.sock')
        write(root / 'CONFIG.private.json', config)
        smoke = 'import research_loop.workers.rohin233_ovx4_recovery_20260918.warm_service; import research_loop.workers.rohin233_ovx4_recovery_20260918.lease_bridge'
        subprocess.run([str(BASE / 'v2/venv/bin/python'), '-B', '-c', smoke], cwd=source,
            env=dict(os.environ, PYTHONPATH=str(source), CUDA_VISIBLE_DEVICES=''), check=True, capture_output=True)
        unit = unit_run(root, source, role, config['deadline_unix'], MODULE.replace('/', '.')+'.warm_service',
            root / 'CONFIG.private.json', physical)
        receipt = dict(unix=time.time(), role=role, unit=unit, physical=physical,
            deadline_unix=config['deadline_unix'], status='WARM_DISPATCHED_NOT_SESSION_OWNER',
            source_manifest_sha256=ref(root / 'SOURCE_MANIFEST.json')['sha256'], predecessor_pid=predecessor,
            CPU_import_pass=True, old_process_signals=[], historical_rescoring=False)
        write(root / 'DISPATCHED.json', receipt)
        results.append(receipt)
    return results
