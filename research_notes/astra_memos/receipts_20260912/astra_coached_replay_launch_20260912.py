import datetime
import json
import os
from pathlib import Path
import subprocess
import sys
import xml.etree.ElementTree as ET

home = Path.home()
commit = sys.argv[1]
source = home / 'astra_sources' / commit
root = home / 'astra_diagnostics/astra_coached_note_replay_20260912_attempt1'
logs = home / 'astra_diagnostics/astra_coached_note_replay_20260912_attempt1_logs'
pair = home / 'astra_diagnostics/astra_P0_material_6101_20260912_attempt1'
device = 'GPU-71e5a3e2-e9c8-5caf-70d8-73794ac34821'
if root.exists() or logs.exists():
    raise RuntimeError('fresh replay and logs required')
model = json.loads((pair / 'lesson/config.json').read_text())['model_path']
display = subprocess.run(['nvidia-smi', '-i', device, '-q', '-x'], capture_output=True, text=True, check=True, timeout=30)
gpu = ET.fromstring(display.stdout).findall('gpu')
if len(gpu) != 1 or gpu[0].find('processes') is None or list(gpu[0].find('processes')) or (gpu[0].find('processes').text or '').strip():
    raise RuntimeError('GPU1 occupied or unknown')
reservations = []
unreadable_own = []
reconciled_services = []
ancestors = set()
ancestor = os.getppid()
while ancestor > 1 and ancestor not in ancestors:
    ancestors.add(ancestor)
    ancestor = int((Path('/proc') / str(ancestor) / 'stat').read_text().rsplit(')', 1)[1].split()[1])
for process in Path('/proc').glob('[0-9]*'):
    try:
        if process.stat().st_uid != os.getuid():
            continue
        entries = (process / 'environ').read_bytes().split(b'\x00')
    except FileNotFoundError:
        continue
    except PermissionError:
        try:
            command_line = (process / 'cmdline').read_bytes().replace(b'\x00', b' ').strip()
            if (process.name == '3245' and command_line == b'/usr/lib/systemd/systemd --user') or (process.name == '3246' and command_line == b'(sd-pam)'):
                reconciled_services.append(dict(pid=process.name, command=command_line.decode()))
                continue
            if int(process.name) in ancestors and command_line == b'sshd: local-rohing@notty':
                reconciled_services.append(dict(pid=process.name, command=command_line.decode(), current_launch_ancestor=True))
                continue
        except FileNotFoundError:
            continue
        metadata = subprocess.run(['ps', '-o', 'pid,ppid,uid,lstart,stat,args', '-p', process.name], capture_output=True, text=True, check=False).stdout
        unreadable_own.append(dict(pid=process.name, command=command_line.decode(errors='replace'), ps=metadata))
        continue
    for entry in entries:
        if entry.startswith(b'CUDA_VISIBLE_DEVICES='):
            values = entry.split(b'=', 1)[1].decode().split(',')
            if set(values) & {'1', device, 'all'}:
                reservations.append(process.name)
if reservations or unreadable_own:
    raise RuntimeError(f'Unreconciled reservations={reservations}, own unreadable={unreadable_own}')
for state in ('pending', 'running'):
    if list((home / 'queue' / state).glob('*.job')):
        raise RuntimeError('reconcile node3 queue before manual launch')
environment = {key: os.environ[key] for key in ('HOME', 'USER', 'LOGNAME', 'PATH', 'LD_LIBRARY_PATH', 'CUDA_HOME', 'TMPDIR') if key in os.environ}
environment.update(V6_MODEL=model, CUDA_VISIBLE_DEVICES=device, PYTHONPATH=str(source), PYTHONNOUSERSITE='1', PYTHONDONTWRITEBYTECODE='1', HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1', VLLM_WORKER_MULTIPROC_METHOD='spawn', OMP_NUM_THREADS='1', TOKENIZERS_PARALLELISM='false')
command = [str(home / 'v2/venv/bin/python'), '-B', '-m', 'organism_v6.parent_note_replay_diagnostic', '--lesson-root', str(pair / 'lesson'), '--sham-root', str(pair / 'sham'), '--out', str(root), '--log', str(logs / 'worker.log'), '--execute']
logs.mkdir()
(logs / 'gpu_before.xml').write_text(display.stdout)
with (logs / 'controller.log').open('xb') as output:
    process = subprocess.Popen(command, cwd=source, env=environment, stdin=subprocess.DEVNULL, stdout=output, stderr=subprocess.STDOUT, start_new_session=True)
receipt = dict(source_commit=commit, node=3, gpu=1, gpu_uuid=device, pid=process.pid, started_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(), command=command, run_dir=str(root), external_logs=str(logs), maximum_note_requests=512, maximum_worker_seconds=3600, source_replayed=True, new_world_actions=0, training=False, clean_lineage=False, official_authentication='UNRESOLVED_LOCAL_HASHES_ONLY', reservations_before=reservations, status='LAUNCHED_NOT_COMPLETED')
receipt['reconciled_unreadable_system_services'] = reconciled_services
with (logs / 'launch_receipt.json').open('x') as output:
    json.dump(receipt, output, sort_keys=True, indent=2)
print(json.dumps(receipt, sort_keys=True))
