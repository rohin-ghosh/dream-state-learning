import datetime
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys


script = Path('/tmp/astra_two_habit_runner_20260912.py')
spec = importlib.util.spec_from_file_location('two_habit', script)
runner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runner)
source = Path.home() / 'astra_sources/d1e70002d12052f6b7357d42cf5997aa915e16f7'
runner.bind(source)
from gpu.astra_mini_sudoku_diagnostic import check_free
root = Path.home() / 'astra_diagnostics/astra_fundamental_two_habit_20260912_attempt1/seed0'
plan = runner.verify(root)
assert runner.base.digest(root / 'plan.json') == 'af4988757fb01e93fe88e6f310c61656f26b2920d45c21561f6b035d208d11e9'
assert plan['seed'] == 0 and plan['device'] == '0'
assert not (root / 'launch').exists() and not (root / 'run').exists()
gpu, xml = check_free(plan['device'])
target = root / 'launch'
target.mkdir()
with (target / 'gpu.xml').open('x') as output:
    output.write(xml)
command = [sys.executable, '-B', str(script), 'run', '--source-root', str(source),
           '--runroot', str(root), '--allow-gpu']
environment = dict(os.environ, CUDA_VISIBLE_DEVICES=plan['device'], PYTHONPATH=str(source),
    PYTHONNOUSERSITE='1', PYTHONDONTWRITEBYTECODE='1', HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1', OMP_NUM_THREADS='1')
with (target / 'controller.log').open('xb') as output:
    process = subprocess.Popen(command, cwd=source, env=environment, stdin=subprocess.DEVNULL,
        stdout=output, stderr=subprocess.STDOUT, start_new_session=True)
receipt = dict(status='LAUNCHED_NOT_COMPLETED', seed=0, node=3, device=plan['device'], pid=process.pid,
    started_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(), command=command,
    source=str(source), plan_sha256=runner.base.digest(root / 'plan.json'),
    script_sha256=runner.base.digest(script), launcher_sha256=runner.base.digest(__file__),
    bound_seconds=1200, continuous_reservation=True, gpu=gpu)
runner.old.write(target / 'launch.json', receipt)
print(json.dumps(receipt, sort_keys=True), flush=True)
