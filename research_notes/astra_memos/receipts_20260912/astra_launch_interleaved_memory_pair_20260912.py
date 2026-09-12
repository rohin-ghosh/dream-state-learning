import datetime
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import time


script = Path('/tmp/astra_interleaved_memory_pair_20260912.py')
spec = importlib.util.spec_from_file_location('interleaved_pair', script)
runner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runner)
source = Path.home() / 'astra_sources/22b7e528f6f62358981ed2264d30ee7242926160'
runner.bind(source)
from gpu.astra_mini_sudoku_diagnostic import check_free

watch_script = Path('/tmp/astra_interleaved_controller_watchdog_20260912.py')
watch_spec = importlib.util.spec_from_file_location('interleaved_watch', watch_script)
watch = importlib.util.module_from_spec(watch_spec)
watch_spec.loader.exec_module(watch)
assert runner.base.digest(script) == 'd100cb58296499c7cd6489d20e96528898f2e48b698147a97dae99fa38946bbe'
assert runner.base.digest(watch_script) == 'c9924b8ff09a046d8a5ec0b41a2cd57a6902650f84c3caab0942213ad93cdd96'
root = Path.home() / 'astra_diagnostics/astra_interleaved_memory_replay_20260912_attempt1/fits_root0_attempt1'
assert runner.base.digest(root / 'plan.json') == '4cad487a53d0e992b896eb4324ff2de1adb24ccc176856de7043d1132c0ee388'
plan = runner.verify(root)
assert plan['device'] == '1' and plan['seed'] == 0
assert not (root / 'run').exists() and not (root / 'launch').exists()
watch_out = Path('/tmp/astra_interleaved_controller_watch_20260912_attempt1')
assert not watch_out.exists()
assert time.time() + 1800 < plan['deadline']
assert time.time() + 2100 < plan['real_lease_end'] - 21600
for name, count in [('astra_interleaved_pair_native_tests_20260912.log', 28),
                    ('astra_interleaved_watchdog_native_tests_20260912.log', 26)]:
    text = (Path('/tmp') / name).read_text()
    assert f'Ran {count} tests' in text and text.rstrip().endswith('OK')
gpu, xml = check_free('1')
launch = root / 'launch'
launch.mkdir()
with (launch / 'gpu.xml').open('x') as stream:
    stream.write(xml)
command = [plan['python'], '-B', str(script), 'run', '--source-root', str(source), '--runroot', str(root), '--allow-gpu']
environment = dict(os.environ, CUDA_VISIBLE_DEVICES='1', PYTHONPATH=str(source),
                   PYTHONDONTWRITEBYTECODE='1', PYTHONNOUSERSITE='1', HF_HUB_OFFLINE='1',
                   TRANSFORMERS_OFFLINE='1', OMP_NUM_THREADS='1')
started = datetime.datetime.now(datetime.timezone.utc).isoformat()
with (launch / 'controller.log').open('xb') as stream:
    process = subprocess.Popen(command, cwd=source, env=environment, stdin=subprocess.DEVNULL,
                               stdout=stream, stderr=subprocess.STDOUT, start_new_session=True)
runner.old.write(launch / 'startup.json', dict(pid=process.pid, started_utc=started, command=command))
print(json.dumps(dict(status='STARTING_NOT_COMPLETED', pid=process.pid, started_utc=started)), flush=True)
wait_end = time.monotonic() + 30
while not (root / 'run/reservation.json').is_file():
    assert process.poll() is None and time.monotonic() < wait_end, 'startup failed; preserve and reconcile, no retry'
    time.sleep(.1)
reservation = runner.base.read(root / 'run/reservation.json')
identity = watch.Proc().read(process.pid)
assert identity['command'] == command and identity['pgid'] == process.pid and identity['uid'] == os.getuid()
receipt = dict(status='LAUNCHED_NOT_COMPLETED', node=3, device='1', seed=0, pid=process.pid,
               pgid=identity['pgid'], proc_start_ticks=identity['proc_start_ticks'],
               controller_started_unix=reservation['started'], effective_deadline=reservation['effective_deadline'],
               reservation_sha256=runner.base.digest(root / 'run/reservation.json'),
               started_utc=started, command=command, source=str(source), root=str(root),
               plan_sha256=runner.base.digest(root / 'plan.json'), script_sha256=runner.base.digest(script),
               launcher_sha256=runner.base.digest(__file__), controller_bound_seconds=1800,
               external_collection_margin_seconds=300, continuous_reservation=True, gpu=gpu,
               arm_order=plan['arm_order'], claim=runner.CLAIM, origin='UNRESOLVED_LOCAL_HASHES_ONLY',
               generation_calls=224, no_automatic_progression=True)
runner.old.write(launch / 'launch.json', receipt)
launch_hash = runner.base.digest(launch / 'launch.json')
watch.load_contract(launch / 'launch.json', launch_hash)
watch_command = [plan['python'], '-B', str(watch_script), '--launch', str(launch / 'launch.json'),
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
