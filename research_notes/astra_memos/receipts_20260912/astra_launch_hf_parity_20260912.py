import datetime
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys

script = Path('/tmp/astra_fundamental_hf_parity_20260912.py')
spec = importlib.util.spec_from_file_location('parity', script)
parity = importlib.util.module_from_spec(spec)
spec.loader.exec_module(parity)
source = Path.home() / 'astra_sources/3a12807f88747bafd0aada1d4a09ba88b915f903'
parity.bind(source)
from gpu.astra_mini_sudoku_diagnostic import check_free
root = Path.home() / 'astra_diagnostics/astra_fundamental_hf_parity_20260912_attempt1'
parity.verify(root)
assert not (root / 'launch').exists() and not (root / 'run').exists()
gpu, xml = check_free('0')
launch = root / 'launch'
launch.mkdir()
with (launch / 'gpu.xml').open('x') as output:
    output.write(xml)
command = [sys.executable, '-B', str(script), 'run', '--source-root', str(source),
           '--root', str(root), '--allow-gpu']
environment = dict(os.environ, CUDA_VISIBLE_DEVICES='0', PYTHONPATH=str(source),
                   PYTHONNOUSERSITE='1', PYTHONDONTWRITEBYTECODE='1',
                   HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1', OMP_NUM_THREADS='1')
with (launch / 'controller.log').open('xb') as output:
    process = subprocess.Popen(command, cwd=source, env=environment, stdin=subprocess.DEVNULL,
                               stdout=output, stderr=subprocess.STDOUT, start_new_session=True)
receipt = dict(status='LAUNCHED_NOT_COMPLETED', node=3, device='0', pid=process.pid,
    started_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(), source=str(source), command=command,
    plan_sha256=parity.base.digest(root / 'plan.json'), script_sha256=parity.base.digest(script),
    launcher_sha256=parity.base.digest(__file__), gpu=gpu, optimizer_steps=0, forwards=32, new_vllm_calls=0)
parity.write(launch / 'launch.json', receipt)
print(json.dumps(receipt, sort_keys=True), flush=True)
