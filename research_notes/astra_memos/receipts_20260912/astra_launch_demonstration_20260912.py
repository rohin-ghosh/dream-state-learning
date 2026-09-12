import datetime
import json
import os
from pathlib import Path
import subprocess
import sys

from organism_v6 import constraint_demonstration_diagnostic as diagnostic
from gpu.astra_mini_sudoku_diagnostic import check_free, write_new

preparation = Path.home() / 'astra_diagnostics/astra_demonstration_preparation_20260912_attempt1'
root = Path.home() / 'astra_diagnostics/astra_demonstration_20260912_attempt1'
logs = root.with_name(root.name + '_launch')
assert not root.exists() and not logs.exists()
prep, digest, config, pairs, check = diagnostic.validate_preparation(preparation)
assert check['status'] == 'READY' and len(pairs) == 8 and not config['synthetic']
native = diagnostic.read('/tmp/astra_demonstration_native_preparation_20260912.json')
assert native['status'] == 'NATIVE_DEMONSTRATION_PREPARATION_AND_OVERLAP_PASS' and native['preparation_sha256'] == digest
cpu_log = Path('/tmp/astra_demonstration_native_cpu_20260912.log')
assert 'Ran 19 tests' in cpu_log.read_text() and cpu_log.read_text().rstrip().endswith('OK')
gpu, xml = check_free('1')
logs.mkdir(exist_ok=False)
(logs / 'gpu.xml').write_text(xml)
environment = dict(os.environ, CUDA_VISIBLE_DEVICES=gpu['gpu_uuid'], V6_MODEL=config['model_path'],
    HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1', OMP_NUM_THREADS='1',
    VLLM_WORKER_MULTIPROC_METHOD='spawn', PYTHONDONTWRITEBYTECODE='1')
command = [sys.executable, '-B', '-m', 'organism_v6.constraint_demonstration_diagnostic',
    '--preparation', str(prep), '--out', str(root), '--allow-gpu']
with (logs / 'controller.log').open('xb') as stream:
    process = subprocess.Popen(command, env=environment, stdin=subprocess.DEVNULL, stdout=stream,
        stderr=subprocess.STDOUT, start_new_session=True)
receipt = dict(status='LAUNCHED_NOT_COMPLETED', pid=process.pid, node=3, device='1', gpu=gpu,
    started_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(), command=command,
    source=str(Path(diagnostic.__file__).resolve().parents[1]), preparation=str(prep), preparation_sha256=digest,
    native_cpu_sha256=diagnostic.base.formation._hash(cpu_log),
    launcher_sha256=diagnostic.base.formation._hash(Path(__file__)), generation_calls=32,
    source_calls_per_arm=8, parent_free_application_calls_per_arm=8, fits=0, generation_seed=7101,
    seed_role=diagnostic.base.SEED_ROLE, total_seconds=1800, max_seconds_per_arm=900,
    explanation_tokens=native['explanation_tokens'], continuous_reservation=True,
    no_training_approval=True, model_origin='UNRESOLVED_LOCAL_HASHES_ONLY')
write_new(logs / 'launch.json', receipt)
print(json.dumps(receipt, sort_keys=True), flush=True)
