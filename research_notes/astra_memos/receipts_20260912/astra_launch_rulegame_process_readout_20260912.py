import datetime
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import time

from gpu.astra_mini_sudoku_diagnostic import check_free

source = Path.home() / 'astra_sources/4c3064c1c3eef068951e9c3b2ca46630754564e7'
driver = Path('/tmp/astra_rulegame_process_readout_20260912.py')
spec = importlib.util.spec_from_file_location('process_readout', driver)
bridge = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = bridge
spec.loader.exec_module(bridge)
assert bridge.digest(driver) == '46e3d0974cab9a3c35e732634a22c29ad25ccd670472dc5b1a57c344cb20af46'
root = Path.home() / 'astra_diagnostics/astra_rulegame_process_readout_v2_20260912_attempt1'
plan_hash = '8b0f23858427d57b579688bcc06dbae4768b9bbbc2198660d1f1dbe31f092323'
root, plan, diagnostic = bridge.checked_plan(root, plan_hash)
assert plan['source_root'] == str(source) and plan['device'] == '2'
assert time.time() + 1800 < min(plan['deadline'], plan['lease_cutoff'])
assert not (root / 'run').exists()
lineage = bridge.accepted_writes(plan)
release = Path.home() / 'astra_diagnostics/astra_rulegame_process_write_v2_20260912_attempt1_collection_attempt1/validation.json'
assert bridge.digest(release) == 'fbc01b2979003948869cc25f5ae00ecae12a357681791706089658e11eed62db'
collection = bridge.read(release)
assert collection['status'] == 'COLLECTED_PAIRED_WRITE' and collection['full_release'] is True
assert collection['aggregate_available'] is True and collection['plan_sha256'] == plan['write_plan_sha256']
logs = root.parent / (root.name + '_launch')
assert not logs.exists()
cpu = Path('/tmp/astra_process_readout_native_cpu_20260912.log')
assert 'Ran 22 tests' in cpu.read_text() and cpu.read_text().rstrip().endswith('OK')
gpu, xml = check_free('2')
logs.mkdir()
with (logs / 'gpu.xml').open('x') as stream:
    stream.write(xml)
environment = dict(os.environ, CUDA_VISIBLE_DEVICES='2', V6_MODEL=plan['model'],
                   PYTHONPATH=str(source), ASTRA_SOURCE_ROOT=str(source),
                   HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1', OMP_NUM_THREADS='1',
                   PYTHONNOUSERSITE='1', PYTHONDONTWRITEBYTECODE='1',
                   VLLM_WORKER_MULTIPROC_METHOD='spawn')
command = [plan['python'], '-B', str(driver), 'evaluate', '--root', str(root),
           '--plan-sha256', plan_hash, '--allow-gpu']
started = datetime.datetime.now(datetime.timezone.utc).isoformat()
with (logs / 'controller.log').open('xb') as stream:
    process = subprocess.Popen(command, cwd=source, env=environment, stdin=subprocess.DEVNULL,
                               stdout=stream, stderr=subprocess.STDOUT, start_new_session=True)
receipt = dict(status='LAUNCHED_NOT_COMPLETED', phase='process_v2_parent_free_readout', pid=process.pid,
               node=3, device='2', gpu=gpu, started_utc=started, command=command,
               source=str(source), root=str(root), plan_sha256=plan_hash,
               write_plan_sha256=plan['write_plan_sha256'], write_release_sha256=bridge.digest(release),
               write_release_path=str(release), native_cpu_sha256=bridge.digest(cpu), driver_sha256=bridge.digest(driver),
               launcher_sha256=bridge.digest(__file__), continuous_reservation=True,
               controller_seconds=1800, cleanup_reserve=140, worker_cap_seconds=600,
               external_collection_margin_seconds=300,
               model_origin='UNRESOLVED_LOCAL_HASHES_ONLY', cells=['OFF', 'P_ON', 'A_ON'],
               adaptation_test=False, updates=0, parent_calls=0,
               claim_boundary='Exploratory process-v2 parent-free development readout; no adult updates or G5/H2')
bridge.write_json(logs / 'launch.json', receipt)
print(json.dumps(receipt, sort_keys=True), flush=True)
