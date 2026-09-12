import datetime
import json
import os
from pathlib import Path
import subprocess
import sys

from gpu import astra_semantic_objective_probe as probe
from gpu.astra_mini_sudoku_diagnostic import check_free

root = Path.home() / 'astra_diagnostics/astra_semantic_objective_20260912_attempt1'
logs = Path.home() / 'astra_diagnostics/astra_semantic_objective_20260912_attempt1_launch'
assert not logs.exists() and not (root / 'STARTED.json').exists()
out, prepared, rows, tokenizer = probe.verify_prepared(root)
assert probe.file_hash(root / 'PREPARED.json') == '9b1bcbf697b49a804b31428b36e6e95b9f345075c675c2877a006e642cfadc77'
assert probe.file_hash(Path('/tmp/astra_objective_native_cpu_20260912.log')) == '7408f18f923b4c897da2dd580f70a52c4371d6935c9de1dcb3850552723e8697'
gpu, xml = check_free('0')
assert gpu['gpu_uuid'] == prepared['runtime_config']['gpu_uuid']
logs.mkdir(exist_ok=False)
(logs / 'gpu.xml').write_text(xml)
environment = dict(os.environ, CUDA_VISIBLE_DEVICES=gpu['gpu_uuid'], CUBLAS_WORKSPACE_CONFIG=':4096:8',
    HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1', OMP_NUM_THREADS='1', PYTHONDONTWRITEBYTECODE='1')
command = [sys.executable, '-B', '-m', 'gpu.astra_semantic_objective_probe', 'execute',
    '--out', str(root), '--timeout-seconds', '1800', '--allow-gpu']
with (logs / 'controller.log').open('xb') as stream:
    process = subprocess.Popen(command, env=environment, stdin=subprocess.DEVNULL, stdout=stream,
        stderr=subprocess.STDOUT, start_new_session=True)
receipt = dict(status='LAUNCHED_NOT_COMPLETED', pid=process.pid, node=3, device='0', gpu=gpu,
    started_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(), command=command,
    source=str(Path(probe.__file__).resolve().parents[1]), preparation_sha256=probe.file_hash(root / 'PREPARED.json'),
    native_cpu_sha256=probe.file_hash(Path('/tmp/astra_objective_native_cpu_20260912.log')),
    launcher_sha256=probe.file_hash(Path(__file__)), fits=2, optimizer_steps=512, generation_requests=384,
    decision_prefix_forwards=384, max_new_tokens=32, total_seconds=1800, worker_seconds_max=900,
    root_index=1, mapping='W+', training_seed=1, continuous_reservation=True,
    original_data_unchanged=True, original_gate_unchanged=True, no_automatic_followup=True,
    model_origin='UNRESOLVED_LOCAL_HASHES_ONLY')
probe.write(logs, 'launch.json', receipt)
print(json.dumps(receipt, sort_keys=True), flush=True)
