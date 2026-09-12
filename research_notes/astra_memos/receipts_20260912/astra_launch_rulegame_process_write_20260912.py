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
driver = Path('/tmp/astra_rulegame_process_write_20260912.py')
spec = importlib.util.spec_from_file_location('process_writer', driver)
bridge = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = bridge
spec.loader.exec_module(bridge)
assert bridge.digest(driver) == 'a73dd6074fdd099cea19f46cfed94bf31f22b2ce02b8741ac2f224413ee514d9'
root = Path.home() / 'astra_diagnostics/astra_rulegame_process_write_v2_20260912_attempt1'
plan_hash = '67f2b89a769dd1f21e2ae3f048aa2d3743a5761f0574dcca3f47e1a8c51b0f44'
root, plan, diagnostic, exporter, trainer = bridge.checked_plan(root, plan_hash)
assert plan['source_root'] == str(source) and plan['device'] == '2'
assert time.time() + 1200 < min(plan['deadline'], plan['lease_cutoff'])
assert not (root / 'run').exists()
logs = root.parent / (root.name + '_launch')
assert not logs.exists()
cpu = Path('/tmp/astra_process_write_native_cpu_20260912.log')
assert 'Ran 35 tests' in cpu.read_text() and cpu.read_text().rstrip().endswith('OK')
gpu, xml = check_free('2')
logs.mkdir()
with (logs / 'gpu.xml').open('x') as stream:
    stream.write(xml)
environment = dict(os.environ, CUDA_VISIBLE_DEVICES='2', PYTHONPATH=str(source),
                   ASTRA_SOURCE_ROOT=str(source), HF_HUB_OFFLINE='1',
                   TRANSFORMERS_OFFLINE='1', OMP_NUM_THREADS='1',
                   PYTHONNOUSERSITE='1', PYTHONDONTWRITEBYTECODE='1')
command = [plan['python'], '-B', str(driver), 'write', '--root', str(root),
           '--plan-sha256', plan_hash, '--allow-gpu']
started = datetime.datetime.now(datetime.timezone.utc).isoformat()
with (logs / 'controller.log').open('xb') as stream:
    process = subprocess.Popen(command, cwd=source, env=environment, stdin=subprocess.DEVNULL,
                               stdout=stream, stderr=subprocess.STDOUT, start_new_session=True)
receipt = dict(status='LAUNCHED_NOT_COMPLETED', phase='process_v2_context_distillation_write',
               pid=process.pid, node=3, device='2', gpu=gpu, started_utc=started,
               command=command, source=str(source), root=str(root), plan_sha256=plan_hash,
               native_cpu_sha256=bridge.digest(cpu), driver_sha256=bridge.digest(driver),
               launcher_sha256=bridge.digest(__file__), continuous_reservation=True,
               controller_seconds=1200, cleanup_reserve=140, worker_cap_seconds=600,
               external_collection_margin_seconds=300, arms=['P', 'A'], seed=2,
               fresh_base=True, updates_per_arm=12,
               model_origin='UNRESOLVED_LOCAL_HASHES_ONLY', adaptation_test=False,
               claim_boundary='Exploratory own-wake context-distillation write, not usefulness or G3/P1/G5/H1/H2')
bridge.write_json(logs / 'launch.json', receipt)
print(json.dumps(receipt, sort_keys=True), flush=True)
