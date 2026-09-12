import datetime
import json
import os
from pathlib import Path
import subprocess
import sys

from organism_v6 import fundamental_teaching_readout as readout
from gpu.astra_mini_sudoku_diagnostic import check_free

base = readout.base
root = Path.home() / 'astra_diagnostics/astra_fundamental_teaching_20260912_attempt1'
preparation = base.read(root / 'readout_preparation.json')
assert preparation['status'] == 'ALL_THREE_NATIVE_READOUTS_PREPARED'
assert preparation['readout_source'] == str(base.REPO)
cell = sys.argv[1]
assert cell in ('OFF', 'teach', 'control')
selected = preparation['cells'][cell]
destination = Path(selected['root'])
assert base.digest(destination / 'plan.json') == selected['plan_sha256']
plan, cases = readout.verify(destination)
assert len(cases) == 48 and plan['device'] == selected['device']
assert plan['lease_end'] - datetime.datetime.now(datetime.timezone.utc).timestamp() > 21600 + 1800
cpu = Path('/tmp/astra_fundamental_readout_native_cpu_20260912.log')
assert 'Ran 22 tests' in cpu.read_text() and cpu.read_text().rstrip().endswith('OK')
logs = destination / 'launch'
assert not logs.exists() and not (destination / 'run').exists()
gpu, xml = check_free(plan['device'])
logs.mkdir()
with (logs / 'gpu.xml').open('x') as stream:
    stream.write(xml)
environment = dict(os.environ, CUDA_VISIBLE_DEVICES=plan['device'], V6_MODEL=plan['model'],
    PYTHONPATH=str(base.REPO), PYTHONNOUSERSITE='1', PYTHONDONTWRITEBYTECODE='1',
    HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1', OMP_NUM_THREADS='1')
command = [sys.executable, '-B', '-m', 'organism_v6.fundamental_teaching_readout',
    'run', '--root', str(destination), '--allow-gpu']
with (logs / 'controller.log').open('xb') as stream:
    process = subprocess.Popen(command, cwd=base.REPO, env=environment, stdin=subprocess.DEVNULL,
        stdout=stream, stderr=subprocess.STDOUT, start_new_session=True)
receipt = dict(status='LAUNCHED_NOT_COMPLETED', node=3, device=plan['device'], cell=cell,
    pid=process.pid, started_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
    source=str(base.REPO), root=str(destination), command=command,
    plan_sha256=selected['plan_sha256'], launcher_sha256=base.digest(__file__),
    native_cpu_sha256=base.digest(cpu), cases=48, confirmation_requests=0,
    continuous_reservation=True, gpu=gpu)
base.write_json(logs / 'launch.json', receipt)
print(json.dumps(receipt, sort_keys=True))
