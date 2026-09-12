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
driver = Path('/tmp/astra_rulegame_record_readout_20260912.py')
spec = importlib.util.spec_from_file_location('record_readout', driver)
bridge = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = bridge
spec.loader.exec_module(bridge)
assert bridge.digest(driver) == '120e260a76395586736d47e4f8a55c425b090f9f8654208dcfbef7eac5cccbde'
root = Path.home() / 'astra_diagnostics/astra_rulegame_interaction_v3_record_readout_20260912_attempt1'
plan_hash = 'cdb71865359498ca0f75db57566e638b667d2e849cc11c9cbd45dd6bfbb97375'
root, plan, diagnostic = bridge.checked_plan(root, plan_hash)
assert plan['source_root'] == str(source) and plan['device'] == '2'
assert time.time() + 1800 < min(plan['deadline'], plan['lease_cutoff'])
assert not (root / 'run').exists()
lineage = bridge.accepted_writes(plan)
assert not Path('/proc/233174').exists()
release = Path(plan['write_root']) / 'run' / 'main_release.json'
assert release.is_file()
logs = root.parent / (root.name + '_launch')
assert not logs.exists()
cpu = Path('/tmp/astra_rulegame_record_readout_native_tests_20260912.log')
assert 'Ran 25 tests' in cpu.read_text() and cpu.read_text().rstrip().endswith('OK')
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
receipt = dict(status='LAUNCHED_NOT_COMPLETED', phase='actual_record_parent_free_readout', pid=process.pid,
               node=3, device='2', gpu=gpu, started_utc=started, command=command,
               source=str(source), root=str(root), plan_sha256=plan_hash,
               write_plan_sha256=plan['write_plan_sha256'], write_release_sha256=bridge.digest(release),
               native_cpu_sha256=bridge.digest(cpu), driver_sha256=bridge.digest(driver),
               launcher_sha256=bridge.digest(__file__), continuous_reservation=True,
               controller_seconds=1800, cleanup_reserve=140, worker_cap_seconds=600,
               model_origin='UNRESOLVED_LOCAL_HASHES_ONLY', cells=['OFF', 'P_ON', 'A_ON'],
               adaptation_test=False, claim_boundary=diagnostic.CLAIM_BOUNDARY)
bridge.write_json(logs / 'launch.json', receipt)
print(json.dumps(receipt, sort_keys=True), flush=True)
