import datetime
import json
import os
from pathlib import Path
import subprocess
import sys

from organism_v6 import rulegame_parenting_diagnostic as diagnostic
from gpu.astra_mini_sudoku_diagnostic import check_free

phase = sys.argv[1]
assert phase in ('formation', 'write', 'evaluate')
root = Path.home() / 'astra_diagnostics/astra_rulegame_interaction_v2_20260912_attempt1'
logs = root.parent / (root.name + '_' + phase + '_launch')
assert not logs.exists()
plan = diagnostic.verify_plan(root)
assert plan['protocol'] == 'interaction_v2'
native = diagnostic.read(root / 'native_preparation.json')
assert native['status'] == 'NATIVE_RULEGAME_PREPARATION_PASS'
assert native['plan_sha256'] == diagnostic.digest(root / 'plan.json')
cpu = Path('/tmp/astra_rulegame_v2_native_cpu_20260912.log')
assert 'Ran ' in cpu.read_text() and cpu.read_text().rstrip().endswith('OK')
assert diagnostic.remaining_seconds(root, plan) > diagnostic.CLEANUP_RESERVE
if phase == 'write':
    diagnostic.verify_material(root, plan)
if phase == 'evaluate':
    diagnostic.verify_material(root, plan)
    diagnostic.verify_fits(root, plan)
gpu, xml = check_free(plan['device'])
logs.mkdir()
(logs / 'gpu.xml').write_text(xml)
environment = dict(os.environ, CUDA_VISIBLE_DEVICES=plan['device'], V6_MODEL=plan['model'],
                   HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1', OMP_NUM_THREADS='1',
                   PYTHONNOUSERSITE='1', PYTHONDONTWRITEBYTECODE='1',
                   VLLM_WORKER_MULTIPROC_METHOD='spawn')
command = [sys.executable, '-B', '-m', 'organism_v6.rulegame_parenting_diagnostic',
           phase, '--root', str(root), '--allow-gpu']
with (logs / 'controller.log').open('xb') as stream:
    process = subprocess.Popen(command, env=environment, stdin=subprocess.DEVNULL,
                               stdout=stream, stderr=subprocess.STDOUT, start_new_session=True)
receipt = dict(status='LAUNCHED_NOT_COMPLETED', phase=phase, pid=process.pid,
               node=3, device=plan['device'], gpu=gpu,
               started_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
               command=command, source=str(diagnostic.REPO), root=str(root),
               plan_sha256=diagnostic.digest(root / 'plan.json'),
               native_preparation_sha256=diagnostic.digest(root / 'native_preparation.json'),
               native_cpu_sha256=diagnostic.digest(cpu),
               launcher_sha256=diagnostic.digest(Path(__file__)),
               continuous_reservation_within_phase=True, aggregate_worker_cap_seconds=1800,
               model_origin='UNRESOLVED_LOCAL_HASHES_ONLY',
               claim_boundary=diagnostic.CLAIM_BOUNDARY)
diagnostic.write_json(logs / 'launch.json', receipt)
print(json.dumps(receipt, sort_keys=True), flush=True)
