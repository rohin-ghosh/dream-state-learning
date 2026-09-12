import datetime
import json
import os
from pathlib import Path
import subprocess
import sys

from organism_v6 import citation_sleep_diagnostic as diagnostic
from gpu.astra_mini_sudoku_diagnostic import check_free, write_new

preparation = Path.home() / 'astra_diagnostics/astra_citation_sleep_preparation_20260912_attempt1'
root = Path.home() / 'astra_diagnostics/astra_citation_sleep_20260912_attempt1'
logs = root.with_name(root.name + '_launch')
assert not root.exists() and not logs.exists()
prep, digest, config, panel, check = diagnostic.load_preparation(preparation, native=True)
native = diagnostic.read('/tmp/astra_citation_sleep_native_preparation_20260912.json')
assert native['status'] == 'NATIVE_CITATION_SLEEP_PREPARATION_PASS'
assert native['preparation_sha256'] == digest
cpu_log = Path('/tmp/astra_citation_sleep_native_cpu_20260912.log')
assert 'Ran ' in cpu_log.read_text() and cpu_log.read_text().rstrip().endswith('OK')
lease_cutoff = '2026-09-25T21:03:00+00:00'
diagnostic.lease_check(lease_cutoff, diagnostic.PROTOCOL['outer_seconds'])
gpu, xml = check_free('1')
logs.mkdir(exist_ok=False)
(logs / 'gpu.xml').write_text(xml)
environment = dict(os.environ, CUDA_VISIBLE_DEVICES=gpu['gpu_uuid'], V6_MODEL=config['model_path'],
                   HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1', OMP_NUM_THREADS='1',
                   VLLM_WORKER_MULTIPROC_METHOD='spawn', PYTHONDONTWRITEBYTECODE='1')
command = [sys.executable, '-B', '-m', 'organism_v6.citation_sleep_diagnostic',
           '--preparation', str(prep), '--out', str(root), '--device', gpu['gpu_uuid'],
           '--lease-deadline-utc', lease_cutoff, '--allow-gpu']
with (logs / 'controller.log').open('xb') as stream:
    process = subprocess.Popen(command, env=environment, stdin=subprocess.DEVNULL,
                               stdout=stream, stderr=subprocess.STDOUT, start_new_session=True)
receipt = dict(status='LAUNCHED_NOT_COMPLETED', pid=process.pid, node=3, device='1', gpu=gpu,
               started_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(), command=command,
               source=str(Path(diagnostic.__file__).resolve().parents[1]), preparation=str(prep),
               preparation_sha256=digest, native_cpu_sha256=diagnostic.digest(cpu_log),
               launcher_sha256=diagnostic.digest(Path(__file__)), generation_calls=24, fits=2,
               protocol=diagnostic.PROTOCOL, boundary=diagnostic.BOUNDARY,
               supervised_tokens=native['supervised_tokens'], input_tokens=native['input_tokens'],
               continuous_reservation=True, lease_finish_cutoff_utc=lease_cutoff,
               lease_source='Supplied node3 expiry minus six hours; not fresh control-plane verification',
               model_origin='UNRESOLVED_LOCAL_HASHES_ONLY')
write_new(logs / 'launch.json', receipt)
print(json.dumps(receipt, sort_keys=True), flush=True)
