from datetime import datetime, timezone
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import time


script = Path('/tmp/astra_conditional_readout_run_20260912.py')
spec = importlib.util.spec_from_file_location('conditional_controller', script)
driver = importlib.util.module_from_spec(spec)
spec.loader.exec_module(driver)
source = Path.home() / 'astra_sources/90e181a4b0a02cfe655bc76ba480eac9166222b4'
root = Path.home() / 'astra_diagnostics/astra_conditional_behavior_20260912_attempt2/readouts_root0_attempt1'
manifest_pin = '5a26f0da17d53518aa00c80bce3bfbfbe76ef61e65ea5ebc781f797dd33190a6'
driver_pin = 'e7a42bf3644d6e4ce5fbd1f129b37008cc455ea2088d3f65dbc18d27bd1ccd74'
manifest = driver.manifest(source, root, manifest_pin, driver_pin)
api = driver.import_api(source)
assert api.sources() == manifest['source_hashes'] and manifest['device'] == '0'
assert not (root / 'controller').exists() and not (root / 'launch').exists()
assert all(not (Path(phase['root']) / 'run').exists() for phase in manifest['phases'])
from gpu.astra_mini_sudoku_diagnostic import check_free

gpu, xml = check_free('0')
launch = root / 'launch'
launch.mkdir()
with (launch / 'gpu.xml').open('x') as stream:
    stream.write(xml)
deadline = time.time() + 4560
lease_end = datetime(2026, 9, 26, 3, 3, tzinfo=timezone.utc).timestamp()
command = [sys.executable, '-B', str(script), 'run', '--source-root', str(source), '--runroot', str(root),
           '--manifest-sha256', manifest_pin, '--driver-sha256', driver_pin, '--deadline', str(deadline),
           '--lease-end', str(lease_end), '--allow-gpu']
environment = dict(os.environ, CUDA_VISIBLE_DEVICES='0', PYTHONPATH=str(source), PYTHONDONTWRITEBYTECODE='1',
                   PYTHONNOUSERSITE='1', HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1', OMP_NUM_THREADS='1')
with (launch / 'controller.log').open('xb') as stream:
    process = subprocess.Popen(command, cwd=source, env=environment, stdin=subprocess.DEVNULL,
                               stdout=stream, stderr=subprocess.STDOUT, start_new_session=True)
receipt = dict(status='LAUNCHED_NOT_COMPLETED', node=3, device='0', seed=0, pid=process.pid,
               started_utc=datetime.now(timezone.utc).isoformat(), command=command, source=str(source),
               manifest_sha256=manifest_pin, driver_sha256=driver_pin, launcher_sha256=driver.digest(__file__),
               phase_order=[phase['state'] + '_' + phase['phase'] for phase in manifest['phases']],
               gpu=gpu, continuous_reservation=True, controller_bound_seconds=4500, cleanup_seconds=140,
               prior_fit_full_reservation_seconds=464.397178, external_collection_margin_seconds=300,
               generation_calls_planned=672, candidate_forwards_planned=576,
               origin='UNRESOLVED_LOCAL_HASHES_ONLY', supplies_l1_verdict=False)
driver.write(launch / 'launch.json', receipt)
print(json.dumps(receipt, sort_keys=True), flush=True)
