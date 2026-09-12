import datetime
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys


script = Path('/tmp/astra_memory_only_20260912.py')
spec = importlib.util.spec_from_file_location('memory_only', script)
memory = importlib.util.module_from_spec(spec)
spec.loader.exec_module(memory)
source = Path.home() / 'astra_sources/3a12807f88747bafd0aada1d4a09ba88b915f903'
memory.bind(source, '/tmp/astra_fading_sentinel_20260912.py')
from gpu.astra_mini_sudoku_diagnostic import check_free
root = Path.home() / 'astra_diagnostics/astra_fundamental_memory_only_20260912_attempt1'
plan = memory.verify(root)
assert memory.base.digest(root / 'plan.json') == '0f8d1a3042b92c3c940309f0b909f7ee535c295e3c3fb6197a8d45c4c137ac90'
assert not (root / 'launch').exists()
assert all(not (root / ('seed' + seed)).exists() for seed in plan['branches'])
vacancy = {seed: check_free(branch['device']) for seed, branch in plan['branches'].items()}
launch = root / 'launch'
launch.mkdir()
for seed, branch in plan['branches'].items():
    target = launch / ('seed' + seed)
    target.mkdir()
    gpu, xml = vacancy[seed]
    with (target / 'gpu.xml').open('x') as output:
        output.write(xml)
    command = [sys.executable, '-B', str(script), 'run', '--source-root', str(source),
               '--runroot', str(root), '--seed', seed, '--allow-gpu']
    environment = dict(os.environ, CUDA_VISIBLE_DEVICES=branch['device'], PYTHONPATH=str(source),
        PYTHONNOUSERSITE='1', PYTHONDONTWRITEBYTECODE='1', HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1', OMP_NUM_THREADS='1')
    with (target / 'controller.log').open('xb') as output:
        process = subprocess.Popen(command, cwd=source, env=environment, stdin=subprocess.DEVNULL,
            stdout=output, stderr=subprocess.STDOUT, start_new_session=True)
    receipt = dict(status='LAUNCHED_NOT_COMPLETED', seed=seed, node=3, device=branch['device'], pid=process.pid,
        started_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(), command=command,
        source=str(source), plan_sha256=memory.base.digest(root / 'plan.json'),
        script_sha256=memory.base.digest(script), launcher_sha256=memory.base.digest(__file__),
        bound_seconds=900, continuous_reservation=True, gpu=gpu)
    memory.old.write(target / 'launch.json', receipt)
    print(json.dumps(receipt, sort_keys=True), flush=True)
