import argparse
import datetime
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import time

from gpu.astra_mini_sudoku_diagnostic import check_free

parser = argparse.ArgumentParser()
parser.add_argument('--seed', required=True, type=int, choices=(1, 2))
seed = parser.parse_args().seed
source = Path.home() / 'astra_sources/22b7e528f6f62358981ed2264d30ee7242926160'
script = Path('/tmp/astra_interleaved_memory_replication_20260912.py')
spec = importlib.util.spec_from_file_location('replication', script)
runner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runner)
runner.bind(source)
watch_script = Path('/tmp/astra_interleaved_replication_watchdog_20260912.py')
watch_spec = importlib.util.spec_from_file_location('replication_watch', watch_script)
watch = importlib.util.module_from_spec(watch_spec)
watch_spec.loader.exec_module(watch)
assert runner.base.digest(script) == 'dc92b9d18f1fc7e8b9907f304e366de34a5e12340223f8dd17506e007093065f'
assert runner.base.digest(watch_script) == 'a2f3bb6b8583994b845c38ea1fcf765c937f4230700f92bfebd512d8f569ac54'
pins = {1: '0cb346c44656c4ecea1adc8f2cd969c5442f465453a0926813bc37c70a2f22bd',
        2: 'cafc5822aa32f917ef971720ba0a3a9244a0162b02f836da5128519216077a58'}
root = Path.home() / 'astra_diagnostics/astra_interleaved_memory_replay_20260912_attempt1' / f'fits_root{seed}_attempt1'
assert runner.base.digest(root / 'plan.json') == pins[seed]
plan = runner.verify(root)
device = {1: '0', 2: '1'}[seed]
assert plan['device'] == device and plan['seed'] == seed
assert not (root / 'run').exists() and not (root / 'launch').exists()
watch_out = Path(f'/tmp/astra_interleaved_replication_watch_seed{seed}_20260912_attempt1')
assert not watch_out.exists()
assert time.time() + 1800 < plan['deadline']
assert time.time() + 2100 < plan['real_lease_end'] - 21600
for filename, count in [('astra_interleaved_replication_native_tests_20260912.log', 43),
                        ('astra_interleaved_replication_watchdog_native_tests_20260912.log', 45)]:
    text = (Path('/tmp') / filename).read_text()
    assert f'Ran {count} tests' in text and text.rstrip().endswith('OK')
gpu, xml = check_free(device)
launch = root / 'launch'
launch.mkdir()
with (launch / 'gpu.xml').open('x') as stream:
    stream.write(xml)
command = [plan['python'], '-B', str(script), 'run', '--source-root', str(source), '--runroot', str(root), '--allow-gpu']
environment = dict(os.environ, CUDA_VISIBLE_DEVICES=device, PYTHONPATH=str(source),
                   PYTHONDONTWRITEBYTECODE='1', PYTHONNOUSERSITE='1', HF_HUB_OFFLINE='1',
                   TRANSFORMERS_OFFLINE='1', OMP_NUM_THREADS='1')
started = datetime.datetime.now(datetime.timezone.utc).isoformat()
with (launch / 'controller.log').open('xb') as stream:
    process = subprocess.Popen(command, cwd=source, env=environment, stdin=subprocess.DEVNULL,
                               stdout=stream, stderr=subprocess.STDOUT, start_new_session=True)
runner.old.write(launch / 'startup.json', dict(pid=process.pid, started_utc=started, command=command))
print(json.dumps(dict(status='STARTING_NOT_COMPLETED', seed=seed, pid=process.pid, started_utc=started)), flush=True)
wait_end = time.monotonic() + 30
while not (root / 'run/reservation.json').is_file():
    assert process.poll() is None and time.monotonic() < wait_end, 'startup failed; preserve and reconcile, no retry'
    time.sleep(.1)
reservation = runner.base.read(root / 'run/reservation.json')
identity = watch.Proc().read(process.pid)
assert identity['command'] == command and identity['pgid'] == process.pid and identity['uid'] == os.getuid()
receipt = dict(status='LAUNCHED_NOT_COMPLETED', node=3, device=device, seed=seed, pid=process.pid,
               pgid=identity['pgid'], proc_start_ticks=identity['proc_start_ticks'],
               controller_started_unix=reservation['started'], effective_deadline=reservation['effective_deadline'],
               reservation_sha256=runner.base.digest(root / 'run/reservation.json'),
               started_utc=started, command=command, source=str(source), root=str(root),
               plan_sha256=pins[seed], script_sha256=runner.base.digest(script),
               launcher_sha256=runner.base.digest(__file__), controller_bound_seconds=1800,
               external_collection_margin_seconds=300, continuous_reservation=True, gpu=gpu,
               arm_order=plan['arm_order'], claim=runner.CLAIM, origin='UNRESOLVED_LOCAL_HASHES_ONLY',
               generation_calls=224, no_automatic_progression=True,
               parent_plan_sha256=plan['parent_pin'][0], seed0_gate_sha256=plan['seed0_gate']['sha256'])
runner.old.write(launch / 'launch.json', receipt)
launch_hash = runner.base.digest(launch / 'launch.json')
watch.load_contract(root, pins[seed], launch_hash)
watch_command = [plan['python'], '-B', str(watch_script), '--root', str(root), '--plan-sha256', pins[seed],
                 '--launch-sha256', launch_hash, '--out', str(watch_out)]
watch_environment = dict(environment)
watch_environment.pop('CUDA_VISIBLE_DEVICES')
with (launch / 'watchdog.log').open('xb') as stream:
    watcher = subprocess.Popen(watch_command, cwd=source, env=watch_environment, stdin=subprocess.DEVNULL,
                               stdout=stream, stderr=subprocess.STDOUT, start_new_session=True)
runner.old.write(launch / 'watchdog_launch.json', dict(pid=watcher.pid, command=watch_command,
                 watchdog_sha256=runner.base.digest(watch_script), launch_sha256=launch_hash, out=str(watch_out)))
wait_end = time.monotonic() + 10
while not (watch_out / 'watch.json').is_file():
    assert watcher.poll() is None and time.monotonic() < wait_end, 'watchdog startup failed; reconcile live controller'
    time.sleep(.1)
assert watcher.poll() is None
print(json.dumps(dict(receipt, watchdog_pid=watcher.pid, watchdog_ready=True), sort_keys=True), flush=True)
