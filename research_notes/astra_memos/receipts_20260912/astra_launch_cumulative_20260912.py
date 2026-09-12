import datetime
import json
import os
from pathlib import Path
import subprocess
import sys

from gpu import astra_memory_cumulative_diagnostic as diagnostic
from gpu.astra_mini_sudoku_diagnostic import check_free, write_new

root = Path.home() / 'astra_diagnostics/astra_cumulative_20260912_attempt1'
logs = root.with_name(root.name + '_launch')
assert not logs.exists() and not (root / 'RUN_STARTED.json').exists()
digest = 'dc9f33071392c374da4e77c19b9c7f87de0bbe2ee2d4bc503c954c6078910f3d'
manifest = diagnostic.verify_prepared(root, digest)
cpu_log = Path('/tmp/astra_cumulative_native_cpu_20260912.log')
assert 'Ran 20 tests' in cpu_log.read_text() and cpu_log.read_text().rstrip().endswith('OK')
lease_cutoff = datetime.datetime.fromisoformat('2026-09-25T21:03:00+00:00').timestamp()
assert datetime.datetime.now(datetime.timezone.utc).timestamp() + 5400 < lease_cutoff
gpu, xml = check_free('0')
logs.mkdir(exist_ok=False)
(logs / 'gpu.xml').write_text(xml)
environment = dict(os.environ, CUDA_VISIBLE_DEVICES=gpu['gpu_uuid'], V6_MODEL=manifest['model'],
    HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1', OMP_NUM_THREADS='1', PYTHONDONTWRITEBYTECODE='1')
command = [sys.executable, '-B', '-m', 'gpu.astra_memory_cumulative_diagnostic', 'run',
    '--root', str(root), '--manifest-sha256', digest,
    '--lease-cutoff-unix', str(lease_cutoff), '--allow-gpu']
with (logs / 'controller.log').open('xb') as stream:
    process = subprocess.Popen(command, env=environment, stdin=subprocess.DEVNULL, stdout=stream,
        stderr=subprocess.STDOUT, start_new_session=True)
receipt = dict(status='LAUNCHED_NOT_COMPLETED', pid=process.pid, node=3, device='0', gpu=gpu,
    started_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(), command=command,
    source=str(Path(diagnostic.__file__).resolve().parents[1]), manifest_sha256=digest,
    native_cpu_sha256=diagnostic.file_sha(cpu_log), launcher_sha256=diagnostic.file_sha(Path(__file__)),
    fits=2, fresh_checkpoint_reads=4, generation_calls=0, cap_reserved_seconds=5400,
    stages=list(diagnostic.STAGES), lineage=manifest['lineage'],
    starting_state=diagnostic.STARTING_STATE, continuous_reservation=True,
    lease_finish_cutoff_utc='2026-09-25T21:03:00Z',
    lease_source='Supplied node3 expiry minus six hours, not a fresh control-plane lease verification',
    model_origin='UNRESOLVED_LOCAL_HASHES_ONLY')
write_new(logs / 'launch.json', receipt)
print(json.dumps(receipt, sort_keys=True), flush=True)
