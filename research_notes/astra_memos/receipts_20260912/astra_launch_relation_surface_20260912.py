import datetime
import json
import os
from pathlib import Path
import subprocess
import sys

from organism_v6 import relation_surface_diagnostic as diagnostic
from gpu.astra_mini_sudoku_diagnostic import check_free

base = diagnostic.base
root = Path.home() / 'astra_diagnostics/astra_relation_surface_20260912_attempt1'
plan, cases = diagnostic.verify(root)
assert len(plan['requests']) == 9 and plan['output_cap'] == 624
assert plan['lease_end'] - datetime.datetime.now(datetime.timezone.utc).timestamp() > 900
cpu = Path('/tmp/astra_relation_native_cpu_20260912.log')
assert 'Ran 9 tests' in cpu.read_text() and cpu.read_text().rstrip().endswith('OK')
preparation = Path('/tmp/astra_relation_native_preparation_20260912.json')
assert base.read(preparation) == plan
logs = root.parent / (root.name + '_launch')
assert not logs.exists() and not (root / 'run').exists()
gpu, xml = check_free('0')
logs.mkdir()
with (logs / 'gpu.xml').open('x') as output:
    output.write(xml)
environment = dict(os.environ, CUDA_VISIBLE_DEVICES='0', V6_MODEL=plan['model'],
    PYTHONPATH=str(base.REPO), PYTHONNOUSERSITE='1', PYTHONDONTWRITEBYTECODE='1',
    HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1', OMP_NUM_THREADS='1',
    VLLM_WORKER_MULTIPROC_METHOD='spawn')
command = [sys.executable, '-B', '-m', 'organism_v6.relation_surface_diagnostic',
           'run', '--root', str(root), '--allow-gpu']
with (logs / 'controller.log').open('xb') as output:
    process = subprocess.Popen(command, cwd=base.REPO, env=environment,
        stdin=subprocess.DEVNULL, stdout=output, stderr=subprocess.STDOUT,
        start_new_session=True)
receipt = dict(status='LAUNCHED_NOT_COMPLETED', pid=process.pid, node=3, device='0',
    gpu=gpu, root=str(root), source=str(base.REPO), command=command,
    started_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
    plan_sha256=base.digest(root / 'plan.json'), launcher_sha256=base.digest(__file__),
    native_cpu_sha256=base.digest(cpu), native_preparation_sha256=base.digest(preparation),
    continuous_reservation=True, worker_seconds=600, calls=9, output_token_ceiling=624,
    fits=0, parent_calls=0, world_actions=0, model_origin='UNRESOLVED_LOCAL_HASHES_ONLY',
    claim_boundary=diagnostic.LIMITS)
base.write_json(logs / 'launch.json', receipt)
print(json.dumps(receipt, sort_keys=True))
