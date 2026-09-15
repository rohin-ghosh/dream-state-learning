"""Single-dispatch, source-pinned supervision for R133 public TRAIN collection."""

import argparse
from datetime import datetime
import hashlib
import json
import os
from pathlib import Path
import socket
import signal
import subprocess
import sys
import time
from types import SimpleNamespace

from gpu import orch_r133_code_feedback_collection as collection


GPU_UUID = 'GPU-9e6cdf73-7181-4405-2aec-787cc73a3e5b'
require, read, sha, write = collection.require, collection.read, collection.sha, collection.write


def reference(document):
    require(set(document) == {'path', 'sha256'}, 'exact_file_reference')
    path = Path(document['path'])
    require(path.is_absolute() and sha(path) == document['sha256'], 'reference_bytes_changed')
    return path


def validate_scope(config, now):
    require(config['schema'] == 'R133_MAIN_GUARD_V1' and config['wrapper'] == 'ovx3'
            and config['physical'] == 7 and config['gpu_uuid'] == GPU_UUID, 'exact_released_slot')
    require(config['created_unix'] <= now < config['hard_end_unix']
            and config['hard_end_unix'] - config['created_unix'] <= 7200, 'bounded_native_wall')
    require(config['hard_end_unix'] < config['next_reserved_unix'] - 600
            and config['hard_end_unix'] < config['lease_end_unix'] - 21600, 'timer_and_lease_margin')
    require(config['max_native_calls'] == collection.CALL_CAP, 'fixed_96_call_limit')


def validate_checkpoint(authorization, checkpoint):
    metadata = checkpoint['metadata']
    require(metadata['update'] == 18404 and metadata['arm'] == 'FULL', 'fixed_FULL_checkpoint18404')
    expected = metadata['adapter']
    actual = authorization['adapter']
    require(all(actual[field] == expected[field] for field in ('base_sha256', 'state_sha256', 'files')),
            'checkpoint_adapter_identity')
    for name, expected_hash in actual['files']:
        require(sha(Path(actual['path']) / name) == expected_hash
                and checkpoint['files']['adapter/' + name] == expected_hash, 'checkpoint_adapter_bytes')


def validate_inventory(inventory, projections):
    collection.exclusions(inventory)
    require(inventory['inventory_refs'] == [dict(ref=document['ref'], sha256=file_hash)
            for document, file_hash in projections], 'declared_projection_refs')
    for field in ('spec_sha256', 'task_id_sha256', 'used_seed_sha256'):
        require(inventory[field] == sorted({value for document, _ in projections for value in document[field]}),
                'complete_projection_union:' + field)


def validate_allocation(allocation, config, authorization):
    require(allocation['schema'] == 'R133_DATED_ALLOCATION_V1'
            and allocation['purpose'] == 'PUBLIC_TRAIN_READONLY_COLLECTION', 'declared_collection_only')
    for field in ('wrapper', 'physical', 'gpu_uuid', 'max_native_calls', 'hard_end_unix'):
        require(allocation[field] == config[field], 'allocation_scope:' + field)
    require(allocation['plan_sha256'] == authorization['plan_sha256']
            and allocation['checkpoint'] == 18404 and allocation['optimizer_steps'] == 0
            and allocation['parent_calls'] == 0, 'allocation_science_contract')
    declared = datetime.fromisoformat(allocation['declared_utc'].replace('Z', '+00:00'))
    require(declared.tzinfo is not None and declared.utcoffset().total_seconds() == 0
            and config['created_unix'] - 3600 <= declared.timestamp() <= time.time(), 'dated_allocation')
    entry = reference(allocation['builder_entry']).read_text()
    require('[Builder / Main' in entry and allocation['declared_utc'] in entry
            and allocation['plan_sha256'] in entry, 'dated_builder_entry_content')


def validate_native_entry(config_path, config):
    output = Path(config['output_root'])
    require((output / 'DISPATCH_ONCE').is_dir(), 'supervisor_dispatch_required')
    launch = read(output / 'LAUNCH.json')
    require(launch['pid'] == os.getppid() and launch['guard_sha256'] == sha(config_path)
            and launch['parent_start_ticks'] == Path('/proc', str(os.getppid()), 'stat').read_text().split(') ', 1)[1].split()[19],
            'actual_timeout_parent_required')
    require(launch['hard_end_unix'] == config['hard_end_unix']
            and 0 <= time.time() - launch['admission_verified_unix'] <= 120, 'fresh_admitted_launch')
    report = read(output / 'ADMISSION.json')
    require(sha(output / 'ADMISSION.json') == launch['admission_sha256']
            and report['clear'] and report['scanner_euid'] == 0
            and not report['blocking_reasons'] and report['host_sha256'] == config['host_sha256']
            and report['device_minor'] == config['physical'], 'launch_admission_binding')


def reap_owned_child(process):
    if process is None or process.poll() is not None:
        return
    try:
        os.killpg(process.pid, signal.SIGTERM)
    except ProcessLookupError:
        process.wait(timeout=10)
        return
    try:
        process.wait(timeout=10)
    except subprocess.TimeoutExpired:
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        process.wait(timeout=10)


def validate(config_path):
    config = read(config_path)
    validate_scope(config, time.time())
    require(config['host_sha256'] == hashlib.sha256(socket.gethostname().encode()).hexdigest(),
            'native_host_hash_binding')
    source = Path(config['source_root']).resolve()
    require(source == Path(__file__).resolve().parents[1], 'frozen_source_location')
    actual_sources = {str(path.relative_to(source)): sha(path) for path in source.rglob('*.py')}
    require(actual_sources == config['source_pins'], 'all_python_source_pins')
    output = Path(config['output_root']).resolve()
    require(not output.is_relative_to(source), 'raw_outside_source')
    authorization = read(reference(config['authorization']))
    require(authorization['native_end_unix'] == config['hard_end_unix']
            and authorization['gpu_uuid'] == GPU_UUID
            and authorization['plan_sha256'] == sha(output / 'PLAN.json'), 'authorization_binding')
    validate_checkpoint(authorization, read(reference(config['checkpoint_commit'])))
    projections = [(read(reference(item)), item['sha256']) for item in config['inventory_projections']]
    validate_inventory(read(output / 'EXCLUSIONS.json'), projections)
    prior = read(reference(config['prior_terminal']))
    require(prior['status'] == 'COMPLETE'
            and prior['conditions'] == ['SEED', 'GUIDED_C6', 'UNPARENTED_C6']
            and prior['optimizer_steps'] == prior['parent_calls'] == 0,
            'prior_R130_complete')
    timer = read(reference(config['timer_plan']))
    require(config['next_reserved_unix'] == timer['morning_unix']
            and config['lease_end_unix'] <= timer['hard_end_unix'], 'existing_timer_binding')
    publication = read(output / 'PUBLICATION.json')
    require(publication['guard_sha256'] == sha(config_path)
            and publication['allocation_sha256'] == sha(reference(config['allocation']))
            and publication['dated_builder_publication'] is True, 'published_before_dispatch')
    validate_allocation(read(reference(config['allocation'])), config, authorization)
    collection.verified(output, require_launchable=True)
    return config, authorization


def scan(config_path):
    config, _ = validate(config_path)
    require(os.geteuid() == 0 and os.environ.get('CUDA_VISIBLE_DEVICES') == '', 'privileged_cpu_scan')
    from gpu import orch_rich_hot_a100_minor_scan as minor
    from gpu import orch_r111_route_admission as admission

    def allocation(index):
        require(index == 7, 'owned_index_only')

    minor.pinned.policy = SimpleNamespace(HOST_SHA=config['host_sha256'],
        DEVICES={7: GPU_UUID}, require=require, allocation=allocation)
    service = Path(config['output_root']) / 'SERVICE_IDENTITY.json'
    if not service.exists():
        minor.pinned.service(service)
    return admission.scan(7, service)


def supervise(config_path):
    config, _ = validate(config_path)
    output = Path(config['output_root'])
    (output / 'DISPATCH_ONCE').mkdir()
    environment = dict(os.environ, CUDA_VISIBLE_DEVICES='', PYTHONDONTWRITEBYTECODE='1',
        PYTHONPATH=config['source_root'], HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1',
        OMP_NUM_THREADS='1', MKL_NUM_THREADS='1', TOKENIZERS_PARALLELISM='false')
    process = None
    try:
        scan_command = ['sudo', '-n', 'env', 'CUDA_VISIBLE_DEVICES=', 'PYTHONDONTWRITEBYTECODE=1',
            'PYTHONPATH=' + config['source_root'], sys.executable, '-B', str(Path(__file__).resolve()),
            'scan', '--config', str(config_path)]
        report = json.loads(subprocess.check_output(scan_command, text=True, timeout=100))
        write(output / 'ADMISSION.json', report)
        require(report['clear'] and report['scanner_euid'] == 0 and not report['blocking_reasons'],
                'fresh_exclusive_admission')
        admission_verified = time.time()
        remaining = int(config['hard_end_unix'] - time.time() - 10)
        require(remaining > 10, 'time_for_native')
        command = ['timeout', '--signal=TERM', '--kill-after=5s', str(remaining) + 's',
            sys.executable, '-B', '-m', 'gpu.orch_r133_code_feedback_guard', 'native',
            '--config', str(config_path)]
        with (output / 'NATIVE.log').open('x') as stream:
            process = subprocess.Popen(command, cwd=config['source_root'],
                env=dict(environment, CUDA_VISIBLE_DEVICES=GPU_UUID), stdin=subprocess.DEVNULL,
                stdout=stream, stderr=subprocess.STDOUT, start_new_session=True)
            write(output / 'LAUNCH.json', dict(pid=process.pid, started_unix=time.time(),
                command_sha256=hashlib.sha256(json.dumps(command).encode()).hexdigest(),
                parent_start_ticks=Path('/proc', str(process.pid), 'stat').read_text().split(') ', 1)[1].split()[19],
                guard_sha256=sha(config_path), admission_sha256=sha(output / 'ADMISSION.json'),
                admission_verified_unix=admission_verified,
                hard_end_unix=config['hard_end_unix'], no_retry=True))
            exit_code = process.wait()
        write(output / 'EXIT.json', dict(exit_code=exit_code, finished_unix=time.time(), no_retry=True))
        terminal = read(output / 'NATIVE_TERMINAL.json')
        require(exit_code == 0 and terminal['status'] == 'COMPLETE', 'native_complete_no_retry')
        write(output / 'SUPERVISOR_COMPLETE.json', dict(status='COMPLETE',
            finished_unix=time.time(), native_terminal_sha256=sha(output / 'NATIVE_TERMINAL.json')))
    except BaseException as error:
        reap_owned_child(process)
        write(output / 'SUPERVISOR_FAILED.json', dict(status='FAILED', error_type=type(error).__name__,
            error=str(error), finished_unix=time.time(), no_retry=True))
        raise


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=('scan', 'supervise', 'native'))
    parser.add_argument('--config', type=Path, required=True)
    arguments = parser.parse_args()
    if arguments.action == 'scan':
        print(json.dumps(scan(arguments.config), sort_keys=True))
    elif arguments.action == 'native':
        native_config, native_authorization = validate(arguments.config)
        validate_native_entry(arguments.config, native_config)
        collection.collect(Path(native_config['output_root']), native_authorization,
                           expected_gpu_uuid=GPU_UUID)
    else:
        supervise(arguments.config)
