import datetime
import json
import os
from pathlib import Path
import subprocess
import sys
import time

from organism_v6 import rulegame_parenting_diagnostic as diagnostic
from gpu.astra_mini_sudoku_diagnostic import check_free


source = Path.home() / 'astra_sources/610c6edd05ce9c85720ee6e992889badecc2c158'
assert diagnostic.REPO == source
root = Path.home() / 'astra_diagnostics/astra_rulegame_interaction_v3_20260912_attempt1'
logs = root.parent / (root.name + '_formation_launch')
assert not logs.exists() and not (root / 'formation').exists()
plan = diagnostic.verify_plan(root)
assert plan['protocol'] == 'interaction_v3' and plan['device'] == '2'
assert diagnostic.digest(root / 'plan.json') == '7dae3ca492ed39545987ab8deb5f39631a40332d480ddb99292e5f083741c468'
native = diagnostic.read(root / 'native_preparation.json')
assert native['status'] == 'NATIVE_RULEGAME_V3_FORMATION_PREPARATION_PASS'
assert native['plan_sha256'] == diagnostic.digest(root / 'plan.json')
cpu = Path('/tmp/astra_rulegame_v3_native_cpu_20260912.log')
assert 'Ran 76 tests' in cpu.read_text() and cpu.read_text().rstrip().endswith('OK')
assert time.time() + 1800 < plan['lease_end']
gpu, xml = check_free(plan['device'])
logs.mkdir()
with (logs / 'gpu.xml').open('x') as stream:
    stream.write(xml)
environment = dict(os.environ, CUDA_VISIBLE_DEVICES=plan['device'], V6_MODEL=plan['model'],
                   PYTHONPATH=str(source), HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1',
                   OMP_NUM_THREADS='1', PYTHONNOUSERSITE='1', PYTHONDONTWRITEBYTECODE='1',
                   VLLM_WORKER_MULTIPROC_METHOD='spawn')
command = [sys.executable, '-B', '-m', 'organism_v6.rulegame_parenting_diagnostic',
           'formation', '--root', str(root), '--allow-gpu']
started = datetime.datetime.now(datetime.timezone.utc).isoformat()
with (logs / 'controller.log').open('xb') as stream:
    process = subprocess.Popen(command, cwd=source, env=environment, stdin=subprocess.DEVNULL,
                               stdout=stream, stderr=subprocess.STDOUT, start_new_session=True)
receipt = dict(status='LAUNCHED_NOT_COMPLETED', phase='formation', pid=process.pid, node=3,
               device=plan['device'], gpu=gpu, started_utc=started, command=command,
               source=str(source), root=str(root), plan_sha256=diagnostic.digest(root / 'plan.json'),
               native_preparation_sha256=diagnostic.digest(root / 'native_preparation.json'),
               native_cpu_sha256=diagnostic.digest(cpu), launcher_sha256=diagnostic.digest(__file__),
               continuous_reservation_within_phase=True, worker_cap_seconds=600,
               aggregate_worker_cap_seconds=1800, model_origin='UNRESOLVED_LOCAL_HASHES_ONLY',
               claim_boundary=diagnostic.CLAIM_BOUNDARY, no_automatic_write_or_readout=True)
diagnostic.write_json(logs / 'launch.json', receipt)
print(json.dumps(receipt, sort_keys=True), flush=True)
