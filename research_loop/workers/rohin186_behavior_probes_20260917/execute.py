"""Bounded copy-only queue using the selected copy's existing strict launcher."""

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time


ROOT = Path(__file__).resolve().parent
PYTHON = '/localhome/local-rohing/v2/venv/bin/python'
PARENT = Path(json.loads((ROOT / 'JOB.json').read_bytes())['parent_root'])
MAX_SECONDS = 1200


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def read(path):
    return json.loads(Path(path).read_bytes())


def write(path, document):
    payload = (json.dumps(document, sort_keys=True, allow_nan=False) + '\n').encode()
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(descriptor, 'wb') as stream:
        stream.write(payload)
        stream.flush()
        os.fsync(stream.fileno())


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def stage():
    os.umask(0o077)
    source = ROOT / 'source'
    shutil.copytree(PARENT / 'source', source, ignore=shutil.ignore_patterns('__pycache__'))
    for origin, destination in ((ROOT / 'orch_r186_behavior_readout.py', source / 'gpu/orch_r186_behavior_readout.py'),
            (ROOT / 'probe_entry.py', source / 'gpu/r186_probe_entry.py'),
            (ROOT / 'test_orch_r186_behavior_readout.py', source / 'tests/test_orch_r186_behavior_readout.py')):
        require(not destination.exists(), 'new_owned_source_only')
        shutil.copy2(origin, destination)
    environment = dict(os.environ, CUDA_VISIBLE_DEVICES='', PYTHONPATH=str(source), PYTHONDONTWRITEBYTECODE='1')
    with (ROOT / 'CPU_TESTS.log').open('x') as output:
        result = subprocess.run([PYTHON, '-B', '-m', 'unittest', 'discover', '-s', 'tests',
            '-p', 'test_orch_r186_behavior_readout.py', '-v'], cwd=source, env=environment,
            stdout=output, stderr=subprocess.STDOUT, timeout=60)
    require(result.returncode == 0, 'existing_23_tests_must_pass')
    pins = {str(path.relative_to(source)): sha(path) for path in source.rglob('*.py')}
    write(ROOT / 'CPU.json', dict(passed=True, tests=23, source_pins=pins,
        log_sha256=sha(ROOT / 'CPU_TESTS.log'), config_sha256=sha(ROOT / 'CONFIG.json'),
        original_parent=str(PARENT), observed_unix=time.time(), GPU_launched=False))
    print(json.dumps(dict(status='CPU_READY_WAITING_FOR_NATIVE_EXIT', tests=23, root=str(ROOT))))


def terminal_metadata():
    control = PARENT / 'control'
    paths = [control / name for name in ('EXIT.json', 'OUTER_EXIT.json')]
    if not all(path.exists() for path in paths):
        return None
    values = [read(path) for path in paths]
    require(values[0]['exit_code'] == 0 and values[1]['status'] == 0, 'native_failed_not_successful_treatment')
    require(read(control / 'PLAN.json')['max_sleeps'] == 44, 'fixed_three_sleep_source')
    return {path.name: dict(sha256=sha(path), receipt=value) for path, value in zip(paths, values)}


def target_idle(device):
    result = subprocess.run(['nvidia-smi', '--query-compute-apps=gpu_uuid,pid', '--format=csv,noheader'],
        capture_output=True, text=True, timeout=20, check=True)
    return not any(line.split(',')[0].strip() == device for line in result.stdout.splitlines())


def contained_command(guard_path, *, device_only):
    from gpu import r184_node2_confinement as containment
    command = containment.command(guard_path, 'probe' if device_only else 'child')
    unit = next(item.split('=', 1)[1] for item in command if item.startswith('--unit='))
    position = command.index('-m')
    command[position + 1:] = ['gpu.r186_probe_entry', '--guard', str(guard_path), '--unit', unit]
    if device_only:
        command.append('--device-only')
    else:
        remaining = min(360, int(read(ROOT / 'QUEUE_STARTED.json')['deadline_unix'] - time.time() - 5))
        require(remaining > 90, 'bounded_time_for_readout')
        command = ['--property=RuntimeMaxSec=' + str(remaining)
            if item.startswith('--property=RuntimeMaxSec=') else item for item in command]
    return command


def prepare_call(cycle, deadline):
    from gpu import orch_r125_continual_native as native
    source = ROOT / 'source'
    control = ROOT / ('sleep_%06d' % cycle)
    control.mkdir(mode=0o700)
    checkpoint_name = 'sleep_%06d' % cycle
    original_checkpoint = PARENT / 'raw/checkpoints' / checkpoint_name
    document = read(original_checkpoint / 'COMMIT.json')
    original_plan = read(PARENT / 'control/PLAN.json')
    expected = Path(original_plan['root']) / 'checkpoints' / checkpoint_name
    require(document['adapter_path'] == str(expected / 'adapter')
        and document['optimizer_rng_path'] == str(expected / 'optimizer_rng.pt'), 'unchanged_logical_COMMIT_paths')
    destination = ROOT / 'raw/checkpoints' / checkpoint_name
    (destination / 'adapter').mkdir(parents=True, mode=0o700)
    for name in document['adapter_files']:
        require(Path(name).name == name, 'checkpoint_adapter_local_filename')
        shutil.copy2(original_checkpoint / 'adapter' / name, destination / 'adapter' / name)
    for name in ('COMMIT.json', 'optimizer_rng.pt'):
        shutil.copy2(original_checkpoint / name, destination / name)
    mapping = {'COMMIT.json': sha(original_checkpoint / 'COMMIT.json'),
        'optimizer_rng.pt': sha(original_checkpoint / 'optimizer_rng.pt'),
        **{'adapter/' + name: digest for name, digest in document['adapter_files'].items()}}
    require(all(sha(destination / name) == digest for name, digest in mapping.items()), 'exact_checkpoint_copy')
    write(control / 'SOURCE_CHECKPOINT.json', dict(source=str(original_checkpoint), copy=str(destination),
        files=mapping, native_exit=terminal_metadata(), observed_unix=time.time(), history_read=False))
    plan = dict(original_plan, source_root=str(source))
    if plan.get('startup_context'):
        plan['startup_context'] = dict(plan['startup_context'], path=str(source / 'context/R153_STARTUP.md'))
    native.validate_plan(plan)
    write(control / 'PLAN.json', plan)
    shutil.copy2(PARENT / 'LEASE.json', control / 'LEASE.json')
    cpu = read(ROOT / 'CPU.json')
    allocation = dict(plan_sha256=sha(control / 'PLAN.json'), cpu_tests_passed=True,
        gpu_uuid=plan['gpu_uuid'], physical=plan['physical'], builder_entry_logged=True,
        cpu_receipt_path=str(ROOT / 'CPU.json'), cpu_receipt_sha256=sha(ROOT / 'CPU.json'), declared_unix=time.time())
    write(control / 'ALLOCATION.json', allocation)
    original_guard = read(PARENT / 'control/GUARD.json')
    config = dict(original_guard, copy_raw=str(ROOT / 'raw'), source_pins=cpu['source_pins'],
        plan_path=str(control / 'PLAN.json'), plan_sha256=sha(control / 'PLAN.json'), attempt_dir=str(control),
        lease_path=str(control / 'LEASE.json'), lease_sha256=sha(control / 'LEASE.json'),
        allocation_path=str(control / 'ALLOCATION.json'), allocation_sha256=sha(control / 'ALLOCATION.json'),
        behavior_config_path=str(ROOT / 'CONFIG.json'), behavior_config_sha256=sha(ROOT / 'CONFIG.json'),
        checkpoint_path=str(expected / 'COMMIT.json'),
        behavior_output=str(Path(plan['root']) / 'behavior_readouts' / checkpoint_name))
    write(control / 'GUARD.json', config)
    return control, plan


def run_call(cycle, deadline):
    from gpu import orch_r125_continual_guard as guard
    control, plan = prepare_call(cycle, deadline)
    config_path = control / 'GUARD.json'
    guard.validate(config_path)
    with (control / 'DEVICE_SERVICE.log').open('x') as output:
        subprocess.run(contained_command(config_path, device_only=True), stdout=output, stderr=subprocess.STDOUT,
            timeout=90, check=True)
    scan_command = ['sudo', '-n', 'env', 'CUDA_VISIBLE_DEVICES=', 'PYTHONDONTWRITEBYTECODE=1',
        'PYTHONPATH=' + str(ROOT / 'source'), PYTHON, '-B', '-m', 'gpu.orch_r125_continual_guard',
        'scan', '--config', str(config_path)]
    scan_result = subprocess.run(scan_command, capture_output=True, text=True, timeout=90)
    write(control / 'SCAN_PROCESS.json', dict(exit_code=scan_result.returncode, stdout=scan_result.stdout,
        stderr=scan_result.stderr, observed_unix=time.time()))
    require(scan_result.returncode == 0, 'strict_scan_process_failed')
    report = json.loads(scan_result.stdout)
    write(control / 'ADMISSION.json', dict(report=report, guard_sha256=sha(config_path), verified_unix=time.time()))
    require(report['scanner_euid'] == 0 and report['clear'] and not report['blocking_reasons'], 'strict_target_not_clear')
    command = contained_command(config_path, device_only=False)
    write(control / 'SERVICE_DISPATCH.json', dict(command=command, dispatched_unix=time.time(),
        physical=plan['physical'], gpu_uuid=plan['gpu_uuid'], no_retry=True))
    with (control / 'SERVICE.log').open('x') as output:
        result = subprocess.run(command, stdout=output, stderr=subprocess.STDOUT, timeout=380)
    write(control / 'SERVICE_EXIT.json', dict(status=result.returncode, finished_unix=time.time()))
    released = target_idle(plan['gpu_uuid'])
    write(control / 'GPU_RELEASE.json', dict(observed_unix=time.time(), gpu_uuid=plan['gpu_uuid'],
        physical=plan['physical'], service_exit=result.returncode, target_compute_empty=released,
        semantic_results_read=False))
    require(result.returncode == 0 and (control / 'READOUT_COMPLETE_METADATA.json').exists(), 'readout_failed_no_retry')
    require(released, 'target_not_released')


def queue():
    os.umask(0o077)
    sys.path.insert(0, str(ROOT / 'source'))
    started = time.time()
    deadline = started + MAX_SECONDS
    plan = read(PARENT / 'control/PLAN.json')
    require(deadline < plan['hard_end_unix'], 'within_existing_lease_wall')
    write(ROOT / 'QUEUE_STARTED.json', dict(pid=os.getpid(), started_unix=started, deadline_unix=deadline,
        physical=plan['physical'], gpu_uuid=plan['gpu_uuid'], source=str(PARENT), cycles=[42, 43, 44, 41],
        no_signals_to_native=True, no_retry=True, cpu_sha256=sha(ROOT / 'CPU.json')))
    completed = []
    try:
        while time.time() < deadline - 360:
            terminal = terminal_metadata()
            if terminal and target_idle(plan['gpu_uuid']):
                write(ROOT / 'NATIVE_RELEASE_OBSERVED.json', dict(receipts=terminal, observed_unix=time.time()))
                break
            time.sleep(15)
        else:
            raise TimeoutError('native_or_generic32_not_released_within_bounded_queue')
        for cycle in (42, 43, 44, 41):
            if time.time() > deadline - 360:
                break
            run_call(cycle, deadline)
            completed.append(cycle)
        write(ROOT / 'QUEUE_FINISHED.json', dict(completed_cycles=completed, finished_unix=time.time(),
            remaining_cycles=[cycle for cycle in (42, 43, 44, 41) if cycle not in completed], semantic_results_read=False))
    except BaseException as error:
        write(ROOT / 'QUEUE_FAILED.json', dict(error_type=type(error).__name__, error=str(error),
            completed_cycles=completed, finished_unix=time.time(), no_retry=True))
        raise


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=('stage', 'queue'))
    arguments = parser.parse_args()
    stage() if arguments.action == 'stage' else queue()
