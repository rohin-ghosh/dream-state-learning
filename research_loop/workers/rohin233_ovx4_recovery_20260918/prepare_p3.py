"""Prepare/dispatch only the exact original P3 scorer on its original device."""

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time
import xml.etree.ElementTree as ET


ROOT = Path('/localhome/local-rohing/orch_r233_p3_scorer_recovery_20260918/attempt4')
ORIGINAL = Path('/localhome/local-rohing/orch_r226_caption_scorer_20260918')
DEADLINE = 1789754370


def read(path):
    return json.loads(Path(path).read_bytes())


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def device_minor(xml, expected_uuid):
    matches = [gpu for gpu in ET.fromstring(xml).findall('gpu') if gpu.findtext('uuid') == expected_uuid]
    assert len(matches) == 1, 'exact_unique_physical_device'
    minor = int(matches[0].findtext('minor_number'))
    assert 0 <= minor < 8, 'actual_bounded_device_minor'
    return minor


def write(path, document):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x') as stream:
        json.dump(document, stream, sort_keys=True, indent=2)


def prepare(payload):
    assert os.getuid() == 2524 and 180 < DEADLINE-time.time() < 3600
    guard_path = Path('/localhome/local-rohing/orch_r201_node4_20260918/node4/R195_FLEET/SCALE_physical3/control/GUARD.json')
    guard = read(guard_path)
    assert hashlib.sha256(subprocess.check_output(['hostname']).strip()).hexdigest() == guard['host_sha256']
    assert sha(guard['lease_path']) == guard['lease_sha256']
    lease = read(guard['lease_path'])
    assert DEADLINE+21600 <= lease['lease_end_unix'] and DEADLINE <= guard['hard_end_unix']
    original_loaded = read(ORIGINAL / 'session2/LOADED.json')
    assert not Path('/proc', str(original_loaded['pid'])).exists(), 'old_scorer_absent'
    ROOT.mkdir(mode=0o700, exist_ok=False)
    state_path = ORIGINAL / 'session2/SESSION_STATE.private.json'
    state_sha = sha(state_path)
    state = read(state_path)
    assert state['phase'] == 'COMPLETE' and len(state['seen']) == 48
    initial_seen = set(read(ORIGINAL / 'RESUME_STATE.private.json')['seen'])
    results = sorted((ORIGINAL / 'session2/attempts').glob('*/RESULT.json'), key=lambda path:read(path)['unix'])
    for result in results:
        document = read(result)
        assert document['origin']['record_sha256'] not in initial_seen
        initial_seen.add(document['origin']['record_sha256'])
    assert initial_seen == set(state['seen'])
    latest = read(results[-1].parent / 'AFTER.json')
    assert latest == dict(game=state['game'], policy=state['policy'])
    shutil.copyfile(state_path, ROOT / 'RESUME_STATE.private.json')
    assert state_sha == sha(state_path) == sha(ROOT / 'RESUME_STATE.private.json')
    source_files = {}
    for path in (ORIGINAL / 'source').rglob('*.py'):
        assert path.is_file() and not path.is_symlink()
        relative = path.relative_to(ORIGINAL / 'source')
        destination = ROOT / 'source' / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(path, destination)
        assert sha(path) == sha(destination)
        source_files[str(relative)] = sha(path)
    for name, expected in read(ORIGINAL / 'BUNDLE.json')['files'].items():
        assert source_files[name] == expected
    for relative, content in payload['files'].items():
        path = ROOT / 'source' / relative
        assert not path.exists() and not Path(relative).is_absolute() and '..' not in Path(relative).parts
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content)
    inputs = Path('/localhome/local-rohing/orch_r209_first_caption_game_20260918')
    arguments = dict(game_manifest=original_loaded['game_manifest']['path'],
        data_manifest=str(inputs / 'inputs/DEVELOPMENT_MANIFEST.private.json'),
        image_map=str(inputs / 'inputs/GAME_IMAGE_MAP.json'), judge_config=original_loaded['scalar']['path'],
        encoder_manifest=str(inputs / 'similarity/embedding_snapshot.json'),
        pixel_config=str(inputs / 'similarity/pixel_config.json'), relevance_config=str(inputs / 'RELEVANCE_PROBE.json'),
        life_root=state['life_root'], agent_id=state['game']['agent_id'] if 'agent_id' in state['game'] else 'C2-SCALE3-R213-caption')
    assert sha(arguments['game_manifest']) == original_loaded['game_manifest']['sha256']
    assert sha(arguments['judge_config']) == original_loaded['scalar']['sha256']
    config = dict(physical=0, deadline_unix=DEADLINE, source_root=str(ROOT / 'source'),
        source_files=source_files, recovery_root=str(ROOT), arguments=arguments,
        resume_state=dict(path=str(ROOT / 'RESUME_STATE.private.json'), sha256=state_sha),
        socket='/tmp/r233_p3_caption.sock', expected_gpu=read(ORIGINAL / 'PREPARED.json')['gpu_uuid'],
        lease=dict(path=guard['lease_path'], sha256=guard['lease_sha256']), guard_sha256=sha(guard_path))
    write(ROOT / 'CONFIG.private.json', config)
    environment = dict(os.environ, PYTHONPATH=str(ROOT / 'source'), PYTHONDONTWRITEBYTECODE='1', CUDA_VISIBLE_DEVICES='')
    entry = ROOT / 'source/research_loop/workers/rohin233_ovx4_recovery_20260918/p3_recovery.py'
    result = subprocess.run(['/localhome/local-rohing/v2/venv/bin/python', '-B', str(entry),
        '--config', str(ROOT / 'CONFIG.private.json'), '--smoke'], cwd=ROOT / 'source',
        env=environment, capture_output=True, text=True, timeout=35)
    if result.returncode:
        print(result.stderr, file=sys.stderr)
        raise RuntimeError('receiving_cpu_failed')
    receipt = dict(json.loads(result.stdout), state_sha256=state_sha, source_files=len(source_files),
        six_hour_margin=True, deadline_unix=DEADLINE, native_signals=[], parent_publications=[])
    write(ROOT / 'CPU_READY.json', receipt)
    return receipt


def dispatch():
    config, ready = read(ROOT / 'CONFIG.private.json'), read(ROOT / 'CPU_READY.json')
    assert ready['status'] == 'CPU_EXACT_48_SEEN_RESTORE_PASS' and not (ROOT / 'DISPATCHED.json').exists()
    assert DEADLINE+21600 <= read(config['lease']['path'])['lease_end_unix'] and 120 < DEADLINE-time.time()
    mapping = subprocess.check_output(['nvidia-smi', '-i', '0', '--query-gpu=uuid,memory.used', '--format=csv,noheader,nounits'], text=True).strip().split(',')
    assert mapping[0].strip() == config['expected_gpu'] and int(mapping[1]) < 100
    assert config['expected_gpu'] not in subprocess.check_output(['nvidia-smi', '--query-compute-apps=gpu_uuid,pid', '--format=csv,noheader'], text=True)
    assert config['socket'] not in subprocess.check_output(['ss','-xlnH'],text=True)
    minor = device_minor(subprocess.check_output(['nvidia-smi', '-q', '-x']), config['expected_gpu'])
    assert os.minor(Path('/dev/nvidia'+str(minor)).stat().st_rdev) == minor
    unit = 'orch-r233-p3-scorer-recovery-attempt4-20260918'
    command = ['sudo','-n','systemd-run','--unit='+unit,'--property=User=2524','--property=Group=2524',
        '--property=WorkingDirectory='+str(ROOT / 'source'), '--property=RuntimeMaxSec='+str(int(DEADLINE-time.time())),
        '--property=TimeoutStopSec=15','--property=KillMode=control-group','--property=UMask=0077',
        '--property=DevicePolicy=closed','--property=NoNewPrivileges=yes',
        '--property=StandardOutput=append:'+str(ROOT / 'scorer.log'), '--property=StandardError=append:'+str(ROOT / 'scorer.log')]
    for device in ('/dev/nvidia'+str(minor),'/dev/nvidiactl','/dev/nvidia-uvm','/dev/nvidia-uvm-tools'):
        command.append('--property=DeviceAllow='+device+' rw')
    environment = dict(CUDA_VISIBLE_DEVICES=config['expected_gpu'], PYTHONPATH=str(ROOT / 'source'),
        HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',PYTHONDONTWRITEBYTECODE='1',OMP_NUM_THREADS='2',MKL_NUM_THREADS='2',
        TOKENIZERS_PARALLELISM='false',HOME='/localhome/local-rohing')
    command += ['--setenv='+name+'='+value for name,value in environment.items()]
    command += ['/localhome/local-rohing/v2/venv/bin/python','-B',str(ROOT / 'source/research_loop/workers/rohin233_ovx4_recovery_20260918/p3_recovery.py'), '--config',str(ROOT / 'CONFIG.private.json')]
    result = subprocess.run(command,check=True,capture_output=True,timeout=20)
    receipt = dict(unix=time.time(),unit=unit,physical=0,minor=minor,deadline_unix=DEADLINE,status='DISPATCHED_NOT_YET_LOADED',
        CPU_ready_sha256=sha(ROOT / 'CPU_READY.json'),native_signals=[],parent_publications=[])
    write(ROOT / 'DISPATCHED.json',receipt)
    return receipt


if __name__ == '__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('action',choices=['prepare','dispatch'])
    args=parser.parse_args()
    print(json.dumps(prepare(json.load(sys.stdin)) if args.action=='prepare' else dispatch()))
