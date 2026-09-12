import datetime
import json
import os
from pathlib import Path
import subprocess
import sys

from organism_v6 import constraint_check_diagnostic as diagnostic
from gpu.astra_mini_sudoku_diagnostic import check_free, write_new

seed = diagnostic.validate_generation_seed(int(sys.argv[1]))
device = {7101: '1', 7102: '2', 7103: '3'}[seed]
preparation = Path.home() / f'astra_diagnostics/astra_constraint_v2_preparation_20260912_seed{seed}_attempt1'
root = Path.home() / f'astra_diagnostics/astra_constraint_v2_20260912_seed{seed}_attempt1'
logs = root.with_name(root.name + '_launch')
assert not root.exists() and not logs.exists()
prep, digest, config, cases, check = diagnostic.validate_preparation(preparation)
assert check['status'] == 'READY' and len(cases) == 8 and not config['synthetic']
assert diagnostic.selected_generation_seed(config, seed) == seed
preparation_report = diagnostic.read('/tmp/astra_constraint_v2_native_preparation_20260912.json')
assert preparation_report['status'] == 'NATIVE_V2_PREPARATION_AND_ORIGINAL_OVERLAP_CHECK_PASS'
assert any(row['generation_seed'] == seed and row['preparation_sha256'] == digest
           for row in preparation_report['pairs'])
cpu_log = Path('/tmp/astra_constraint_v2_native_cpu_20260912.log')
assert 'Ran 28 tests' in cpu_log.read_text() and cpu_log.read_text().rstrip().endswith('OK')
gpu, xml = check_free(device)
logs.mkdir(exist_ok=False)
(logs / 'gpu.xml').write_text(xml)
environment = dict(os.environ, CUDA_VISIBLE_DEVICES=gpu['gpu_uuid'], V6_MODEL=config['model_path'],
    HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1', OMP_NUM_THREADS='1',
    VLLM_WORKER_MULTIPROC_METHOD='spawn', PYTHONDONTWRITEBYTECODE='1')
command = [sys.executable, '-B', '-m', 'organism_v6.constraint_check_diagnostic',
    '--preparation', str(prep), '--out', str(root), '--generation-seed', str(seed), '--allow-gpu']
with (logs / 'controller.log').open('xb') as stream:
    process = subprocess.Popen(command, env=environment, stdin=subprocess.DEVNULL, stdout=stream,
        stderr=subprocess.STDOUT, start_new_session=True)
receipt = dict(status='LAUNCHED_NOT_COMPLETED', pid=process.pid, node=3, device=device, gpu=gpu,
    started_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(), command=command,
    source=str(Path(diagnostic.__file__).resolve().parents[1]), preparation=str(prep),
    preparation_sha256=digest, native_cpu_sha256=diagnostic.formation._hash(cpu_log),
    launcher_sha256=diagnostic.formation._hash(Path(__file__)), generation_calls=16, cases_per_arm=8,
    fits=0, generation_seed=seed, seed_role=diagnostic.SEED_ROLE,
    max_tokens_per_call=128, total_seconds=1800, max_seconds_per_arm=900,
    card_tokens=check['card_tokens'], continuous_reservation=True,
    no_training_approval=True, model_origin='UNRESOLVED_LOCAL_HASHES_ONLY')
write_new(logs / 'launch.json', receipt)
print(json.dumps(receipt, sort_keys=True), flush=True)
