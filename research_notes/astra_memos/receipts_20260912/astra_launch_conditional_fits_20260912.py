import datetime
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys


script = Path('/tmp/astra_conditional_fits_20260912.py')
spec = importlib.util.spec_from_file_location('conditional_fits', script)
runner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runner)
source = Path.home() / 'astra_sources/5f6e1f1d217dcdb15176dc84b9ac34ec960c48de'
runner.bind(source)
from gpu.astra_mini_sudoku_diagnostic import check_free

root = Path.home() / 'astra_diagnostics/astra_conditional_behavior_20260912_attempt2/fits_root0_attempt1'
assert runner.digest(script) == '3be6583f97f68d944774ff15f5fcd4d66522991d62bf865b03f005808cf4f96f'
assert runner.digest(root / 'plan.json') == '680e5239cd90c15b72de998d22c09cf5aa451d2e71111d99e940532e43510f11'
plan = runner.verify(root)
assert plan['device'] == '1' and plan['seed'] == 0
assert not (root / 'run').exists() and not (root / 'launch').exists()
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
with (launch / 'controller.log').open('xb') as stream:
    process = subprocess.Popen(command, cwd=source, env=environment, stdin=subprocess.DEVNULL,
                               stdout=stream, stderr=subprocess.STDOUT, start_new_session=True)
receipt = dict(status='LAUNCHED_NOT_COMPLETED', node=3, device=plan['device'], seed=0, pid=process.pid,
               started_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(), command=command,
               source=str(source), plan_sha256=runner.digest(root / 'plan.json'),
               script_sha256=runner.digest(script), launcher_sha256=runner.digest(__file__),
               controller_bound_seconds=1200, continuous_reservation=True, gpu=gpu,
               claim=runner.CLAIM, origin='UNRESOLVED_LOCAL_HASHES_ONLY', generation_calls=0)
runner.write(launch / 'launch.json', receipt)
print(json.dumps(receipt, sort_keys=True), flush=True)
