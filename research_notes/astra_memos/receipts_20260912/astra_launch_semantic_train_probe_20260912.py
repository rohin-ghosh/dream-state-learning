import datetime
import json
import os
from pathlib import Path
import subprocess
import sys

from gpu import astra_semantic_train_probe as probe
from gpu.astra_mini_sudoku_diagnostic import check_free

root = Path.home() / 'astra_diagnostics/astra_semantic_exact_train_20260912_attempt1'
original = Path.home() / 'astra_diagnostics/astra_semantic_writer_Q0_20260912_attempt1'
prepared = probe.read(root / 'native_preparation.json')
assert prepared['status'] == 'NATIVE_TOKEN_AND_SOURCE_PREFLIGHT_NO_MODEL_LOAD'
assert prepared['source_pins'] == probe.source_pins()
selected = []
for root_index, device in [(0, '0'), (1, '7')]:
    out = root / f'root{root_index}'
    logs = root / 'launch_logs' / f'root{root_index}'
    assert not out.exists() and not logs.exists()
    gpu, xml = check_free(device)
    selected.append((root_index, device, out, logs, gpu, xml))
for root_index, device, out, logs, gpu, xml in selected:
    logs.mkdir(parents=True, exist_ok=False)
    gpu_now, xml_now = check_free(device)
    assert gpu_now['gpu_uuid'] == gpu['gpu_uuid']
    (logs / 'gpu.xml').write_text(xml_now)
    environment = dict(os.environ, CUDA_VISIBLE_DEVICES=gpu['gpu_uuid'], CUBLAS_WORKSPACE_CONFIG=':4096:8',
        HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1', OMP_NUM_THREADS='1', PYTHONDONTWRITEBYTECODE='1')
    command = [sys.executable, '-B', '-m', 'gpu.astra_semantic_train_probe', '--original', str(original),
        '--out', str(out), '--root-index', str(root_index), '--gpu-uuid', gpu['gpu_uuid'],
        '--timeout-seconds', '1800', '--allow-gpu']
    with (logs / 'controller.log').open('xb') as stream:
        process = subprocess.Popen(command, env=environment, stdin=subprocess.DEVNULL, stdout=stream,
            stderr=subprocess.STDOUT, start_new_session=True)
    receipt = dict(status='LAUNCHED_NOT_COMPLETED', pid=process.pid, node=3, device=device, root_index=root_index,
        gpu=gpu_now, source=str(Path(probe.__file__).resolve().parents[1]), command=command,
        started_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(), new_fits=0,
        continuous_reservation=True, execution_timeout_seconds=1800, worker_seconds_max=900,
        native_cpu_sha256=probe.file_hash(root / 'native_cpu.log'),
        native_preparation_sha256=probe.file_hash(root / 'native_preparation.json'),
        launcher_sha256=probe.file_hash(Path(__file__)))
    probe.write(logs, 'launch.json', receipt)
    print(json.dumps(receipt, sort_keys=True), flush=True)
