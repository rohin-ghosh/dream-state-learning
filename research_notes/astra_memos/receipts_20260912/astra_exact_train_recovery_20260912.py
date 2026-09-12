import datetime
import json
import os
from pathlib import Path
import subprocess
import sys

from gpu import astra_semantic_train_probe as probe
from gpu.astra_mini_sudoku_diagnostic import check_free

prior = Path.home() / 'astra_diagnostics/astra_semantic_exact_train_20260912_attempt1'
failed = prior / 'root0'
out, manifest, evidence, requests = probe.verify_probe(failed)
assert not Path('/proc/114258').exists()
assert (failed / 'FAILED.json').is_file() and not (failed / 'COMPLETED.json').exists()
assert 'timed out after 15 seconds' in (failed / 'r0_plus.log').read_text()
assert not (failed / 'r0_plus/LOAD.json').exists()
assert not (failed / 'r0_plus/records.jsonl').exists()
assert probe.read(failed / 'OFF/DONE.json')['count'] == 256
assert probe.file_hash(failed / 'OFF/records.jsonl') == probe.read(failed / 'OFF/DONE.json')['records_sha256']
cleanups = list(failed.glob('*.cleanup.json'))
assert len(cleanups) == 2
for path in cleanups:
    cleanup = probe.read(path)
    assert cleanup['owned_group_empty'] and cleanup['gpu_processes_absent'] and cleanup['cleanup_error'] is None
gpu, xml = check_free('0')
if sys.argv[1] == 'capture':
    probe.write(failed, 'MAIN_FAILURE_AUDIT.json', dict(
        observed_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        status='INFRASTRUCTURE_FAILURE_BEFORE_FIRST_ADAPTER_LOAD',
        source_verified=True, completed_off_records=256, adapter_loads=0,
        controller_absent=True, cleanup_count=2, gpu=gpu, xml=xml,
        retry_policy='One fresh full root0 retry; do not overwrite or promote partial attempt1.'))
    print(json.dumps(dict(status='FAILURE_CAPTURED_AND_GPU0_RELEASED', gpu=gpu)))
elif sys.argv[1] == 'launch':
    assert (failed / 'MAIN_FAILURE_AUDIT.json').is_file()
    prepared = probe.read(prior / 'native_preparation.json')
    assert prepared['source_pins'] == probe.source_pins()
    assert probe.file_hash(prior / 'native_cpu.log') == '75423f9d9d8326ebbc10d1053c7b7375b107a490d99591ad9dcea6e5722aca7d'
    assert probe.file_hash(prior / 'native_preparation.json') == '836fdb36bd2cca1d883cf4b2a668ed0a6aef23db488ec7dac07aac9b69ad70c3'
    root = Path.home() / 'astra_diagnostics/astra_semantic_exact_train_20260912_attempt2'
    root.mkdir(exist_ok=False)
    logs = root / 'launch_logs/root0'
    logs.mkdir(parents=True, exist_ok=False)
    (logs / 'gpu.xml').write_text(xml)
    environment = dict(os.environ, CUDA_VISIBLE_DEVICES=gpu['gpu_uuid'], CUBLAS_WORKSPACE_CONFIG=':4096:8',
        HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1', OMP_NUM_THREADS='1', PYTHONDONTWRITEBYTECODE='1')
    command = [sys.executable, '-B', '-m', 'gpu.astra_semantic_train_probe', '--original', manifest['original'],
        '--out', str(root / 'root0'), '--root-index', '0', '--gpu-uuid', gpu['gpu_uuid'],
        '--timeout-seconds', '1800', '--allow-gpu']
    with (logs / 'controller.log').open('xb') as stream:
        process = subprocess.Popen(command, env=environment, stdin=subprocess.DEVNULL, stdout=stream,
            stderr=subprocess.STDOUT, start_new_session=True)
    receipt = dict(status='LAUNCHED_NOT_COMPLETED', pid=process.pid, node=3, device='0', root_index=0,
        gpu=gpu, source=str(Path(probe.__file__).resolve().parents[1]), command=command,
        started_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(), new_fits=0,
        continuous_reservation=True, execution_timeout_seconds=1800, worker_seconds_max=900,
        prior_failure=str(failed), prior_failure_audit_sha256=probe.file_hash(failed / 'MAIN_FAILURE_AUDIT.json'),
        reason='Fresh full retry after pre-adapter-load nvidia-smi timeout; same source, settings and requests.',
        native_cpu_sha256=probe.file_hash(prior / 'native_cpu.log'),
        native_preparation_sha256=probe.file_hash(prior / 'native_preparation.json'),
        launcher_sha256=probe.file_hash(Path(__file__)))
    probe.write(logs, 'launch.json', receipt)
    print(json.dumps(receipt, sort_keys=True), flush=True)
else:
    raise ValueError('capture or launch required')
