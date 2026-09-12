import datetime
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import xml.etree.ElementTree as ET

home = Path.home()
source = home / 'astra_sources/52e0e4db0d67d54defa4151cb091ccc925cd9e8c'
sys.path.insert(0, str(source))
from organism_v6 import run_reasoning_neutral as supervisor

rate_tag, device = sys.argv[1:3]
assert (rate_tag, device) in (('3e5', '0'), ('1e5', '2'))
run = home / ('astra_diagnostics/astra_A1_lowerlr_bank0_ts2_' + rate_tag + '_20260912_attempt1')
logs = run / 'logs'
rate = '3e-5' if rate_tag == '3e5' else '1e-5'
job = Path('/tmp/astra_lowerlr_job_20260912.sh')
if os.environ.get('ASTRA_LOWERLR_CONTROLLER') == '1':
    try:
        supervisor.run_worker(['bash', str(job), str(run), rate], log_path=logs / 'worker.log', timeout=2700, device=device)
        result = dict(status='WORKER_COMPLETED', finished_utc=datetime.datetime.now(datetime.timezone.utc).isoformat())
    except BaseException as error:
        result = dict(status='WORKER_FAILED', error=repr(error), finished_utc=datetime.datetime.now(datetime.timezone.utc).isoformat())
        with (logs / 'controller_result.json').open('x') as target:
            json.dump(result, target)
        raise
    with (logs / 'controller_result.json').open('x') as target:
        json.dump(result, target)
    print(json.dumps(result))
    raise SystemExit(0)
assert not (logs / 'launch_receipt.json').exists() and not (logs / 'controller.log').exists()
comparison = json.loads((run / 'provenance/comparison.json').read_text())
baseline = Path(comparison['baseline_root'])
for name, digest in comparison['baseline_hashes'].items():
    assert hashlib.sha256((baseline / name).read_bytes()).hexdigest() == digest, name
receipt = json.loads((run / 'seed_run_receipt.json').read_text())
for name, metadata in receipt['inputs'].items():
    assert hashlib.sha256((run / name).read_bytes()).hexdigest() == metadata['sha256'], name
display = subprocess.run(['nvidia-smi', '-i', device, '-q', '-x'], capture_output=True, text=True, timeout=30, check=True)
gpu = ET.fromstring(display.stdout).findall('gpu')
assert len(gpu) == 1 and gpu[0].find('processes') is not None and not list(gpu[0].find('processes')) and not (gpu[0].find('processes').text or '').strip()
uuid = gpu[0].findtext('uuid')
ancestors = set()
ancestor = os.getppid()
while ancestor > 1 and ancestor not in ancestors:
    ancestors.add(ancestor)
    ancestor = int((Path('/proc') / str(ancestor) / 'stat').read_text().rsplit(')', 1)[1].split()[1])
reconciled = []
for process in Path('/proc').glob('[0-9]*'):
    try:
        if process.stat().st_uid != os.getuid():
            continue
        entries = (process / 'environ').read_bytes().split(b'\x00')
    except FileNotFoundError:
        continue
    except PermissionError:
        try:
            command = (process / 'cmdline').read_bytes().replace(b'\x00', b' ').strip()
        except FileNotFoundError:
            continue
        if (process.name == '3245' and command == b'/usr/lib/systemd/systemd --user') or (process.name == '3246' and command == b'(sd-pam)') or (int(process.name) in ancestors and command == b'sshd: local-rohing@notty'):
            reconciled.append(dict(pid=process.name, command=command.decode()))
            continue
        raise RuntimeError('unreconciled own process ' + process.name)
    for entry in entries:
        if entry.startswith(b'CUDA_VISIBLE_DEVICES=') and set(entry.split(b'=', 1)[1].decode().split(',')) & {device, uuid, 'all'}:
            raise RuntimeError('existing GPU reservation ' + process.name)
for state in ('pending', 'running'):
    assert not list((home / 'queue' / state).glob('*.job')), 'pending/running queue requires reconciliation'
environment = {key: os.environ[key] for key in ('HOME', 'USER', 'LOGNAME', 'PATH', 'LD_LIBRARY_PATH', 'TMPDIR') if key in os.environ}
environment.update(CUDA_VISIBLE_DEVICES=device, ASTRA_LOWERLR_CONTROLLER='1', V6_MODEL='Qwen/Qwen2.5-7B-Instruct', PYTHONPATH=str(source), PYTHONNOUSERSITE='1', PYTHONDONTWRITEBYTECODE='1', HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1', CUDA_HOME='/usr/local/cuda-13.0', OMP_NUM_THREADS='1', TOKENIZERS_PARALLELISM='false')
environment['PATH'] = '/usr/local/cuda-13.0/bin:' + str(home / 'v2/venv/bin') + ':' + environment['PATH']
command = [str(home / 'v2/venv/bin/python'), '-B', str(Path(__file__).resolve()), rate_tag, device]
with (logs / 'controller.log').open('xb') as output:
    process = subprocess.Popen(command, cwd=source, env=environment, stdin=subprocess.DEVNULL, stdout=output, stderr=subprocess.STDOUT, start_new_session=True)
result = dict(status='LAUNCHED_NOT_COMPLETED', node=3, gpu=int(device), gpu_uuid=uuid, pid=process.pid, started_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(), run_dir=str(run), source_commit=source.name, rate=rate, command=command, worker_seconds_cap=2700, job_sha256=hashlib.sha256(job.read_bytes()).hexdigest(), reconciled_system_services=reconciled, clean_lineage=False, reused_baseline_node=2, model_authentication='UNRESOLVED_LOCAL_HASHES_ONLY')
with (logs / 'launch_receipt.json').open('x') as target:
    json.dump(result, target, sort_keys=True, indent=2)
(logs / 'gpu_before.xml').write_text(display.stdout)
print(json.dumps(result, sort_keys=True))
