import datetime
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import time

from gpu.astra_mini_sudoku_diagnostic import check_free

source = Path.home() / 'astra_sources/610c6edd05ce9c85720ee6e992889badecc2c158'
driver = Path('/tmp/astra_rulegame_record_write_v2_20260912.py')
spec = importlib.util.spec_from_file_location('record_write', driver)
bridge = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = bridge
spec.loader.exec_module(bridge)
assert bridge.digest(driver) == '183b48be6193da953f699d718575f9227fd946d9f8111d2d1647ae5dd431ec7c'
root = Path.home() / 'astra_diagnostics/astra_rulegame_interaction_v3_record_write_20260912_attempt2'
plan_hash = '48effd1ba154f497e5946d308f990624ada63bd905c198e0abfdf668131a8ee4'
root, plan, diagnostic, exporter, trainer = bridge.checked_plan(root, plan_hash)
assert plan['source_root'] == str(source) and plan['device'] == '2'
assert plan['python'] == '/localhome/local-rohing/v2/venv/bin/python'
assert time.time() + 1200 < min(plan['deadline'], plan['lease_cutoff'])
assert not (root / 'run').exists() and not (root / 'fits').exists()
logs = root.parent / (root.name + '_launch')
assert not logs.exists()
cpu = Path('/tmp/astra_rulegame_record_write_v2_native_tests_20260912.log')
assert 'Ran 24 tests' in cpu.read_text() and cpu.read_text().rstrip().endswith('OK')
subprocess.run([plan['python'], '-B', '-c', 'import torch, transformers, peft; print(torch.__version__)'], check=True)
gpu, xml = check_free('2')
logs.mkdir()
with (logs / 'gpu.xml').open('x') as stream:
    stream.write(xml)
environment = dict(os.environ, CUDA_VISIBLE_DEVICES='2', V6_MODEL=plan['model'],
                   PYTHONPATH=str(source), ASTRA_SOURCE_ROOT=str(source),
                   HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1', OMP_NUM_THREADS='1',
                   PYTHONNOUSERSITE='1', PYTHONDONTWRITEBYTECODE='1',
                   VLLM_WORKER_MULTIPROC_METHOD='spawn')
command = [plan['python'], '-B', str(driver), 'write', '--root', str(root),
           '--plan-sha256', plan_hash, '--allow-gpu']
started = datetime.datetime.now(datetime.timezone.utc).isoformat()
with (logs / 'controller.log').open('xb') as stream:
    process = subprocess.Popen(command, cwd=source, env=environment, stdin=subprocess.DEVNULL,
                               stdout=stream, stderr=subprocess.STDOUT, start_new_session=True)
receipt = dict(status='LAUNCHED_NOT_COMPLETED', phase='actual_record_write', pid=process.pid,
               node=3, device='2', gpu=gpu, started_utc=started, command=command,
               source=str(source), root=str(root), plan_sha256=plan_hash,
               native_cpu_sha256=bridge.digest(cpu), driver_sha256=bridge.digest(driver),
               launcher_sha256=bridge.digest(__file__), continuous_reservation=True,
               controller_seconds=1200, cleanup_reserve=140, worker_cap_seconds=600,
               model_origin='UNRESOLVED_LOCAL_HASHES_ONLY', readout='PENDING_SEPARATE_OFF_P_ON_A_ON')
bridge.write_json(logs / 'launch.json', receipt)
print(json.dumps(receipt, sort_keys=True), flush=True)
