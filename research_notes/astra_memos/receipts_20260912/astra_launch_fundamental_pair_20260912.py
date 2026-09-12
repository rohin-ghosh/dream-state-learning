import datetime
import json
import os
from pathlib import Path
import runpy
import subprocess
import sys

from gpu.astra_mini_sudoku_diagnostic import check_free

scope = runpy.run_path('/tmp/astra_fundamental_pair_20260912.py', run_name='fundamental_orchestration')
base, root = scope['base'], scope['ROOT']
arm = sys.argv[1]
assert arm in ('teach', 'control')
device = {'teach': '0', 'control': '1'}[arm]
plan = scope['verify']()
logs = root / ('launch_' + arm)
assert not logs.exists() and not (root / ('fit_' + arm)).exists()
cpu = Path('/tmp/astra_fundamental_trainer_native_direct_cpu_20260912.log')
assert cpu.read_text().rstrip().endswith('9/9 passed')
assert plan['tokens']['teach'] == plan['tokens']['control'] == dict(input_tokens=4517, target_tokens=912)
assert plan['lease_end'] - datetime.datetime.now(datetime.timezone.utc).timestamp() > 1800
gpu, xml = check_free(device)
logs.mkdir()
with (logs / 'gpu.xml').open('x') as stream:
    stream.write(xml)
environment = dict(os.environ, CUDA_VISIBLE_DEVICES=device, V6_MODEL=plan['model'],
    PYTHONPATH=str(base.REPO), PYTHONNOUSERSITE='1', PYTHONDONTWRITEBYTECODE='1',
    HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1', OMP_NUM_THREADS='1')
command = [sys.executable, '-B', '/tmp/astra_fundamental_pair_20260912.py', 'fit',
    '--arm', arm, '--device', device, '--allow-gpu']
with (logs / 'controller.log').open('xb') as stream:
    process = subprocess.Popen(command, cwd=base.REPO, env=environment, stdin=subprocess.DEVNULL,
        stdout=stream, stderr=subprocess.STDOUT, start_new_session=True)
receipt = dict(status='LAUNCHED_NOT_COMPLETED', node=3, device=device, arm=arm, pid=process.pid,
    started_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(), source=str(base.REPO),
    root=str(root), gpu=gpu, command=command, plan_sha256=base.digest(root / 'plan.json'),
    launcher_sha256=base.digest(__file__), fit_script_sha256=base.digest('/tmp/astra_fundamental_pair_20260912.py'),
    native_trainer_cpu_sha256=base.digest(cpu), expected_steps=80,
    expected_target_tokens_seen=3648, expected_input_tokens_seen=18068,
    continuous_reservation=True, model_origin=plan['model_origin'], material_role=plan['material_role'])
base.write_json(logs / 'launch.json', receipt)
print(json.dumps(receipt, sort_keys=True))
