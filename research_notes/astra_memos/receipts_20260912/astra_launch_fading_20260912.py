import datetime
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys

script = Path('/tmp/astra_fading_sentinel_20260912.py')
spec = importlib.util.spec_from_file_location('sentinel', script)
sentinel = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sentinel)
source = Path.home() / 'astra_sources/3a12807f88747bafd0aada1d4a09ba88b915f903'
sentinel.bind(source)
from gpu.astra_mini_sudoku_diagnostic import check_free
root = Path.home() / 'astra_diagnostics/astra_fundamental_fading_20260912_attempt1/runs'
plan = sentinel.verify(root)
assert not (root / 'launch').exists()
assert all(not (root / ('rate-' + rate)).exists() for rate in sentinel.RATES)
vacancy = {rate: check_free(device) for rate, (_, device) in sentinel.RATES.items()}
launch = root / 'launch'
launch.mkdir()
for rate, (_, device) in sentinel.RATES.items():
    target = launch / ('rate-' + rate)
    target.mkdir()
    gpu, xml = vacancy[rate]
    with (target / 'gpu.xml').open('x') as output:
        output.write(xml)
    command = [sys.executable, '-B', str(script), 'run-one-rate', '--source-root', str(source),
               '--runroot', str(root), '--rate', rate, '--allow-gpu']
    environment = dict(os.environ, CUDA_VISIBLE_DEVICES=device, PYTHONPATH=str(source),
                       PYTHONNOUSERSITE='1', PYTHONDONTWRITEBYTECODE='1',
                       HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1', OMP_NUM_THREADS='1')
    with (target / 'controller.log').open('xb') as output:
        process = subprocess.Popen(command, cwd=source, env=environment, stdin=subprocess.DEVNULL,
                                   stdout=output, stderr=subprocess.STDOUT, start_new_session=True)
    receipt = dict(status='LAUNCHED_NOT_COMPLETED', rate=rate, device=device, node=3, pid=process.pid,
                   started_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(), command=command,
                   plan_sha256=sentinel.base.digest(root / 'plan.json'), source=str(source),
                   launcher_sha256=sentinel.base.digest(__file__), continuous_reservation=True,
                   bound_seconds=1800, gpu=gpu)
    sentinel.write(target / 'launch.json', receipt)
    print(json.dumps(receipt, sort_keys=True), flush=True)
