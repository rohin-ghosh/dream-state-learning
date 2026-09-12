import datetime
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import time


script = Path('/tmp/astra_varied_memory_pair_20260912.py')
spec = importlib.util.spec_from_file_location('varied_pair', script)
runner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runner)
source = Path.home() / 'astra_sources/dc2e9a3c11ccd9a3f10ea28513723bbfb8420247'
runner.bind(source, '/tmp/astra_memory_only_20260912.py', '/tmp/astra_fading_sentinel_20260912.py')
from gpu.astra_mini_sudoku_diagnostic import check_free

root = Path.home() / 'astra_diagnostics/astra_varied_memory_replay_20260912_attempt1/fits_root0_attempt1'
assert runner.base.digest(script) == 'b58f65cd482bbd2d762edc030c7967a1ecd004829cf8271c74c15d3ca54bc8c7'
assert runner.base.digest(root / 'plan.json') == '2120bb93d0458b789bb3db408e57dd077f528cfadec35691b0e5fb27889756ca'
plan = runner.verify(root)
assert plan['device'] == '1' and plan['seed'] == 0
assert not (root / 'run').exists() and not (root / 'launch').exists()
assert time.time() + 1500 < min(plan['deadline'], plan['real_lease_end'] - 6 * 3600)
gpu, xml = check_free(plan['device'])
launch = root / 'launch'
launch.mkdir()
with (launch / 'gpu.xml').open('x') as stream:
    stream.write(xml)
command = [sys.executable, '-B', str(script), 'run', '--source-root', str(source),
           '--runroot', str(root), '--allow-gpu']
environment = dict(os.environ, CUDA_VISIBLE_DEVICES=plan['device'], PYTHONPATH=str(source),
                   PYTHONDONTWRITEBYTECODE='1', PYTHONNOUSERSITE='1', HF_HUB_OFFLINE='1',
                   TRANSFORMERS_OFFLINE='1', OMP_NUM_THREADS='1')
started = datetime.datetime.now(datetime.timezone.utc).isoformat()
with (launch / 'controller.log').open('xb') as stream:
    process = subprocess.Popen(command, cwd=source, env=environment, stdin=subprocess.DEVNULL,
                               stdout=stream, stderr=subprocess.STDOUT, start_new_session=True)
receipt = dict(status='LAUNCHED_NOT_COMPLETED', node=3, device=plan['device'], seed=0, pid=process.pid,
               started_utc=started, command=command, source=str(source), root=str(root),
               plan_sha256=runner.base.digest(root / 'plan.json'), script_sha256=runner.base.digest(script),
               launcher_sha256=runner.base.digest(__file__), controller_bound_seconds=1500,
               external_collection_margin_seconds=300, aggregate_campaign_ceiling_seconds=5400,
               continuous_reservation=True, gpu=gpu, arm_order=plan['arm_order'],
               claim=runner.CLAIM, origin='UNRESOLVED_LOCAL_HASHES_ONLY', generation_calls=128,
               no_automatic_progression=True)
runner.old.write(launch / 'launch.json', receipt)
print(json.dumps(receipt, sort_keys=True), flush=True)
