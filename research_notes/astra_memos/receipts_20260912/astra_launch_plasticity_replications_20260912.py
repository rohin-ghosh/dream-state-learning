import datetime
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys

script = Path('/tmp/astra_fading_replication_20260912.py')
spec = importlib.util.spec_from_file_location('replication', script)
replication = importlib.util.module_from_spec(spec)
spec.loader.exec_module(replication)
source = Path.home() / 'astra_sources/3a12807f88747bafd0aada1d4a09ba88b915f903'
replication.bind(source, '/tmp/astra_fading_sentinel_20260912.py')
from gpu.astra_mini_sudoku_diagnostic import check_free
root = Path.home() / 'astra_diagnostics/astra_fundamental_plasticity_replications_20260912_attempt1'
replication.verify(root)
assert not (root / 'launch').exists()
assert all(not (root / name).exists() for name in replication.BRANCHES)
vacancy = {name: check_free(branch['device']) for name, branch in replication.BRANCHES.items()}
launch = root / 'launch'
launch.mkdir()
for name, branch in replication.BRANCHES.items():
    target = launch / name
    target.mkdir()
    gpu, xml = vacancy[name]
    with (target / 'gpu.xml').open('x') as output:
        output.write(xml)
    command = [sys.executable, '-B', str(script), 'run', '--source-root', str(source),
               '--runroot', str(root), '--branch', name, '--allow-gpu']
    environment = dict(os.environ, CUDA_VISIBLE_DEVICES=branch['device'], PYTHONPATH=str(source),
        PYTHONNOUSERSITE='1', PYTHONDONTWRITEBYTECODE='1', HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1', OMP_NUM_THREADS='1')
    with (target / 'controller.log').open('xb') as output:
        process = subprocess.Popen(command, cwd=source, env=environment, stdin=subprocess.DEVNULL,
                                   stdout=output, stderr=subprocess.STDOUT, start_new_session=True)
    receipt = dict(status='LAUNCHED_NOT_COMPLETED', branch=name, node=3, **branch, pid=process.pid,
        started_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(), command=command,
        source=str(source), plan_sha256=replication.base.digest(root / 'plan.json'),
        script_sha256=replication.base.digest(script), launcher_sha256=replication.base.digest(__file__),
        bound_seconds=600, continuous_reservation=True, gpu=gpu)
    replication.old.write(target / 'launch.json', receipt)
    print(json.dumps(receipt, sort_keys=True), flush=True)
