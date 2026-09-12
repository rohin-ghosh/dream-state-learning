import datetime
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import time

from gpu.astra_mini_sudoku_diagnostic import check_free

source_id = '5a1f300fed4b7f1ef54524869c2bf11509e965ca'
source = Path.home() / 'astra_sources' / source_id
driver = Path('/tmp/astra_sequential_memory_pair_20260912.py')
spec = importlib.util.spec_from_file_location('sequential_main_launch', driver)
bridge = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = bridge
spec.loader.exec_module(bridge)
assert bridge.digest(driver) == '29d70e46f0c65817f65f52f6ed310fcfaa91cda64928f9bdfc54b70834a0c232'
bridge.bind(source, source_id)
root = Path.home() / 'astra_diagnostics/astra_sequential_memory_20260912_attempt2/seed0_pair_attempt2'
plan_hash = '9e53c716373c2458586ff7b6a72d0fe5822d41d5a0129057e2a4e805acab8b49'
assert bridge.digest(root / 'plan.json') == plan_hash
plan = bridge.verify(root)
assert plan['source_root'] == str(source) and plan['device'] == '0'
assert time.time() + 5100 < plan['deadline']
assert time.time() + 5400 < plan['real_lease_end'] - 21600
assert not (root / 'run').exists()
cpu = Path('/tmp/astra_sequential_memory_pair_native_cpu_20260912_attempt2.log')
assert 'Ran 19 tests' in cpu.read_text() and cpu.read_text().rstrip().endswith('OK')
logs = root / 'launch'
assert not logs.exists()
gpu, xml = check_free('0')
logs.mkdir()
with (logs / 'gpu.xml').open('x') as stream:
    stream.write(xml)
environment = dict(os.environ, CUDA_VISIBLE_DEVICES='0', V6_MODEL=plan['model'],
    PYTHONPATH=str(source), ASTRA_SOURCE_ROOT=str(source), HF_HUB_OFFLINE='1',
    TRANSFORMERS_OFFLINE='1', OMP_NUM_THREADS='1', PYTHONNOUSERSITE='1',
    PYTHONDONTWRITEBYTECODE='1', VLLM_WORKER_MULTIPROC_METHOD='spawn')
command = [plan['python'], '-B', str(driver), 'run', '--source-root', str(source),
    '--source-id', source_id, '--runroot', str(root), '--allow-gpu']
started = datetime.datetime.now(datetime.timezone.utc)
with (logs / 'controller.log').open('xb') as stream:
    process = subprocess.Popen(command, cwd=source, env=environment, stdin=subprocess.DEVNULL,
        stdout=stream, stderr=subprocess.STDOUT, start_new_session=True)
receipt = dict(status='LAUNCHED_NOT_COMPLETED', root=str(root), source=str(source), source_commit=source_id,
    plan_sha256=plan_hash, script_sha256=bridge.digest(driver), launcher_sha256=bridge.digest(__file__),
    node=3, device='0', seed=0, parent_seed=0, source_branch='FOUR_VIEW',
    parent_plan_sha256=plan['s0']['parent_plan_sha256'], s0_adapter_files=plan['s0']['parent_files'],
    controller_bound_seconds=5100, external_collection_margin_seconds=300, generation_calls=640,
    worker_count=9, pid=process.pid, pgid=os.getpgid(process.pid), started_utc=started.isoformat(),
    gpu=gpu, command=command, native_cpu_sha256=bridge.digest(cpu), continuous_reservation=True,
    expected_hard_end_unix=started.timestamp()+5100, expected_custody_deadline_unix=started.timestamp()+5400,
    independent_pidfd_watcher=False, monitoring='Main plus controller alarm and owned worker supervisors',
    automatic_progression=False, claim=bridge.CLAIM, model_origin='UNRESOLVED_LOCAL_HASHES_ONLY')
bridge.old.write(logs / 'launch.json', receipt)
print(json.dumps(receipt, sort_keys=True), flush=True)
