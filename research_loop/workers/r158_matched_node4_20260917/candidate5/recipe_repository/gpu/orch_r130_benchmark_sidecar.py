"""Bounded R130 operator sidecar: ovx physical0/1, no parenting interfaces.

The operator stages a committed source snapshot plus this hash-pinned helper,
opaque sealed corpus, and four adapter-only copies of native checkpoints.
Config binds all sources, CPU gate, dated Builder entry, existing lease/FORKS,
exact generator/supervisor identities, and two ordered plans per physical GPU.
R130_SIDECAR_ADMISSION_SHA256 binds the exact config bytes before any signal.
No adapter, optimizer, child stream, or parent control file is ever updated.

preflight validates plans/copies without loading CUDA. supervise first pauses
the exact generation supervisor, catches and rechecks a completed task boundary
under pidfd SIGSTOP, hashes preserved captures, and retires only that pair.
An unsuccessful boundary search resumes both original processes. A privileged
existing scanner must then admit the exact empty GPU before each fresh-process
runner. A fixed lease margin and timeout guard cap all benchmark subprocesses.
Private per-family checkpoint curves are written by the supervisor; CLI output
is limited to status and hashes. Raw stderr belongs only in private node logs.
"""

import argparse
from contextlib import contextmanager
import fcntl
import hashlib
import json
import os
from pathlib import Path
import signal
import socket
import subprocess
import sys
import tarfile
import time

from gpu import orch_r130_checkpoint_benchmark as runner


SCHEMA = 'R130_OVX_BENCHMARK_SIDECAR_V1'
SOURCE_COMMIT = '7c9c25da6819ff462465619fb3d6c13dd579ff4d'
RUNNER_SHA256 = '845ce272f9b7234cdcab7987d983049ef1d5eefeca26d451f06e9d8cb66e6707'
CORPUS_SHA256 = '47e2f4780ff44aeb9312d1f5a9b5bcc4712d3ccfe70cdd1c771994daf0d2c3a8'
HOST_SHA256 = '0e183169e60b06badac84e0eca6036a53b7ad90c433b8cd69b2a9aaf9159389b'
DEVICES = {0: 'GPU-c70cba10-6ab6-a287-e2db-51dccd617ab0',
    1: 'GPU-e7a322fc-fe84-919f-7534-cdfefb6ce1e4'}
GENERATOR_ROOT = Path('/localhome/local-rohing/orch_r119_l1_generation_20260915_attempt2')
LABELS = {0: ('legacy_initial', 'legacy_sleep17'), 1: ('pilot_initial', 'pilot_latest')}
KERNEL_LABELS = ('kernel_initial', 'kernel_first_sleep')
require = runner.require
sha = runner.sha
digest = runner.digest


def read(path):
    return runner.parse_json(Path(path).read_bytes())


def write(path, document):
    return runner._write_once(Path(path), document)


def source_inventory(root):
    root = Path(root)
    return {str(path.relative_to(root)): sha(path) for path in sorted(root.rglob('*.py'))}


def extract_regular_archive(archive, destination, expected_sha256):
    require(sha(archive) == expected_sha256, 'archive_hash')
    destination = Path(destination)
    require(not destination.exists(), 'new_extract_destination')
    with tarfile.open(archive) as stream:
        members = stream.getmembers()
        names = set()
        for member in members:
            path = Path(member.name)
            require(not path.is_absolute() and '..' not in path.parts
                and (member.isfile() or member.isdir()) and member.name not in names,
                'regular_unique_archive_members')
            names.add(member.name)
        destination.mkdir(parents=True, mode=0o700)
        for member in members:
            target = destination / member.name
            if member.isdir():
                target.mkdir(parents=True, exist_ok=True, mode=0o700)
            else:
                target.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
                with stream.extractfile(member) as source:
                    write(target, source.read())
    return dict(archive_sha256=expected_sha256,
        files={str(path.relative_to(destination)): sha(path) for path in sorted(destination.rglob('*')) if path.is_file()})


def checkpoint_manifest(directory, expected_commit_sha256):
    directory = Path(directory)
    manifest = dict(schema=runner.MANIFEST_SCHEMA, adapter_path='adapter', commit_path='COMMIT.json',
        commit_sha256=expected_commit_sha256)
    checkpoint = runner.verify_checkpoint(manifest, directory)
    write(directory / 'manifest.json', manifest)
    return checkpoint


def identity(pid):
    directory = Path('/proc') / str(pid)
    fields = (directory / 'stat').read_text().rsplit(')', 1)[1].split()
    return dict(pid=pid, uid=directory.stat().st_uid, start_ticks=fields[19],
        boot_id=Path('/proc/sys/kernel/random/boot_id').read_text().strip())


def gone(expected):
    try:
        if identity(expected['pid']) != expected:
            return True
        return (Path('/proc') / str(expected['pid']) / 'stat').read_text().rsplit(')', 1)[1].split()[0] == 'Z'
    except FileNotFoundError:
        return True


def owned_descriptor(expected, physical, role, command_sha256):
    require(physical in DEVICES and role in ('supervise', 'generate'), 'bounded_generator_role')
    require(identity(expected['pid']) == expected and expected['uid'] == os.getuid(), 'owned_process_identity')
    directory = Path('/proc') / str(expected['pid'])
    raw = (directory / 'cmdline').read_bytes()
    args = raw.split(b'\0')
    require(hashlib.sha256(raw).hexdigest() == command_sha256, 'owned_command_hash')
    require(str(GENERATOR_ROOT).encode() in args and role.encode() in args
        and b'--index' in args and args[args.index(b'--index') + 1] == str(physical).encode(),
        'owned_generation_only_command')
    if role == 'generate':
        require(('CUDA_VISIBLE_DEVICES=' + DEVICES[physical]).encode()
            in (directory / 'environ').read_bytes().split(b'\0'), 'owned_exact_GPU')
    descriptor = os.pidfd_open(expected['pid'])
    try:
        require(identity(expected['pid']) == expected, 'pidfd_identity_race')
        return descriptor
    except BaseException:
        os.close(descriptor)
        raise


def wait_stopped(expected):
    until = time.monotonic() + 3
    while time.monotonic() < until:
        require(identity(expected['pid']) == expected, 'paused_identity_drift')
        fields = (Path('/proc') / str(expected['pid']) / 'stat').read_text().rsplit(')', 1)[1].split()
        if fields[0] in ('T', 't'):
            return
        time.sleep(.001)
    raise TimeoutError('pause_ack_timeout')


def candidate_boundary(directory):
    directory = Path(directory)
    progress = read(directory / 'PROGRESS.json')
    count = progress['calls']
    last_path = directory / f'CALL_{count:06d}.json'
    if not last_path.exists() or (directory / f'INTENT_{count + 1:06d}.json').exists():
        return None
    return progress


def boundary(directory):
    directory = Path(directory)
    progress = candidate_boundary(directory)
    if progress is None:
        return None
    last_path = directory / f'CALL_{progress["calls"]:06d}.json'
    last = read(last_path)
    require(not list(directory.glob('FAILED_*.json')), 'generator_failed_capture_present')
    require('response' in last and last['finished_unix'] <= progress['finished_unix'], 'completed_task_progress')
    if last['family'] == 'route':
        require((directory / f'EPISODE_{progress["batch"]:04d}_{progress["position"]:02d}.json').is_file(),
            'completed_route_episode_required')
    return progress


@contextmanager
def plan_environment(plan_path, gpu_uuid):
    updates = {'R130_ADMISSION_PLAN_SHA256': sha(plan_path), 'CUDA_VISIBLE_DEVICES': gpu_uuid}
    previous = {name: os.environ.get(name) for name in updates}
    os.environ.update(updates)
    try:
        yield
    finally:
        for name, value in previous.items():
            if value is None:
                os.environ.pop(name, None)
            else:
                os.environ[name] = value


def validate(config_path, physical, *, preflight=False):
    require(physical in DEVICES, 'only_ovx_physical0_1')
    config_path = Path(config_path).resolve(strict=True)
    require(os.environ.get('R130_SIDECAR_ADMISSION_SHA256') == sha(config_path), 'sidecar_admission_binding')
    config = read(config_path)
    require(config['schema'] == SCHEMA and config['source_commit'] == SOURCE_COMMIT, 'sidecar_source_commit')
    require(hashlib.sha256(socket.gethostname().encode()).hexdigest() == HOST_SHA256, 'only_bound_ovx_host')
    require(config['physical'] == physical and config['gpu_uuid'] == DEVICES[physical], 'bound_device')
    require(config['generator_root'] == str(GENERATOR_ROOT), 'only_authorized_generator_root')
    source = Path(config['source_root']).resolve(strict=True)
    require(source == Path(__file__).resolve().parents[1], 'executing_sidecar_source')
    require(source_inventory(source) == config['sources'], 'entire_source_inventory')
    require(sha(source / 'gpu/orch_r130_checkpoint_benchmark.py') == RUNNER_SHA256, 'pinned_runner_source')
    require(config['runner_sha256'] == RUNNER_SHA256 and config['corpus_sha256'] == CORPUS_SHA256,
        'frozen_runner_corpus_contract')
    for name in ('cpu_gate', 'builder_entry', 'forks', 'service', 'corpus_manifest', 'corpus_validation'):
        require(sha(config[name + '_path']) == config[name + '_sha256'], name + '_binding')
    forks = read(config['forks_path'])
    require(config['forks_path'] == str(GENERATOR_ROOT / 'FORKS.json') and forks['node'] == 'ovx'
        and forks['uuid_by_index'][physical] == DEVICES[physical], 'actual_generator_lease')
    require(config['lease_end_unix'] == forks['lease_end_unix']
        and forks['hard_deadline_unix'] == config['lease_end_unix'] - 21600,
        'original_six_hour_lease_margin')
    require(time.time() < config['hard_end_unix'] <= min(forks['hard_deadline_unix'], config['created_unix'] + 7200),
        'bounded_benchmark_wall')
    gate = read(config['cpu_gate_path'])
    require(gate['status'] == 'PASS' and gate['test_exit_code'] == 0
        and gate['runner_sha256'] == RUNNER_SHA256 and gate['corpus_sha256'] == CORPUS_SHA256
        and gate['source_inventory_sha256'] == digest(config['sources'])
        and gate['helper_sha256'] == sha(__file__), 'CPU_provenance_gate')
    require(sha(gate['test_log_path']) == gate['test_log_sha256'], 'CPU_test_log_binding')
    require(Path(config['builder_entry_path']).read_text().startswith('## [Builder] 2026-09-16'),
        'dated_builder_entry_required')
    corpus_manifest = read(config['corpus_manifest_path'])
    corpus_validation = read(config['corpus_validation_path'])
    require(corpus_manifest['task_file_sha256'] == CORPUS_SHA256
        and corpus_manifest['compatible_runner_sha256'] == RUNNER_SHA256
        and corpus_validation['status'] == 'PASS' and corpus_validation['corpus_sha256'] == CORPUS_SHA256
        and corpus_validation['runner_source_sha256'] == RUNNER_SHA256, 'sealed_corpus_compatibility')
    matrix = config.get('matrix', 'legacy_pilot')
    require(matrix in ('legacy_pilot', 'kernel_followup'), 'bounded_benchmark_matrix')
    if matrix == 'kernel_followup':
        require(physical == 0, 'kernel_followup_uses_only_released_ovx0')
        verify_prior_matrix(config['prior_matrix'])
        labels = KERNEL_LABELS
    else:
        labels = LABELS[physical]
    require(tuple(job['label'] for job in config['jobs']) == labels, 'exact_checkpoint_order')
    retained = config.get('retained_completed', [])
    require([entry['label'] for entry in retained] == list(labels[:len(retained)])
        and len(retained) < len(labels), 'retained_successes_must_be_ordered_prefix')
    retained_by_label = {entry['label']: entry for entry in retained}
    for job in config['jobs']:
        require(sha(job['plan_path']) == job['plan_sha256'], 'job_plan_binding')
        if job['label'] in retained_by_label:
            verify_retained(config, job, retained_by_label[job['label']])
            continue
        plan = read(job['plan_path'])
        require(plan['gpu_uuid'] == DEVICES[physical] and plan['corpus_sha256'] == CORPUS_SHA256
            and plan['sources'] == config['sources'] and plan['source_root'] == str(source)
            and plan['hard_end_unix'] == config['hard_end_unix'], 'job_inherits_admission')
        if preflight:
            with plan_environment(job['plan_path'], DEVICES[physical]):
                context = runner.prepare(job['plan_path'])
            require(len(context['tasks']) == 30
                and context['checkpoint']['commit_sha256'] == job['checkpoint_commit_sha256'],
                'exact_saved_checkpoint_and_corpus')
    return config


def verify_retained(config, job, retained):
    for name in ('original_config', 'complete', 'release'):
        require(sha(retained[name + '_path']) == retained[name + '_sha256'], 'retained_receipt_binding')
    original = read(retained['original_config_path'])
    require(original['physical'] == config['physical'] and original['gpu_uuid'] == config['gpu_uuid']
        and original['source_commit'] == SOURCE_COMMIT and original['corpus_sha256'] == CORPUS_SHA256,
        'retained_original_allocation')
    require(job == next(item for item in original['jobs'] if item['label'] == retained['label']),
        'retained_exact_original_job')
    plan = read(job['plan_path'])
    require(sha(job['plan_path']) == job['plan_sha256'] and plan['corpus_sha256'] == CORPUS_SHA256
        and sha(plan['corpus_path']) == CORPUS_SHA256
        and plan['sources']['gpu/orch_r130_checkpoint_benchmark.py'] == RUNNER_SHA256,
        'retained_runner_and_corpus')
    require(source_inventory(Path(plan['source_root'])) == plan['sources'], 'retained_source_files_changed')
    require(sha(plan['manifest_path']) == plan['manifest_sha256'], 'retained_manifest_changed')
    checkpoint = runner.verify_checkpoint(read(plan['manifest_path']), Path(plan['manifest_path']).parent)
    require(checkpoint['commit_sha256'] == job['checkpoint_commit_sha256'], 'retained_checkpoint_changed')
    output = Path(plan['output_path'])
    require(Path(retained['complete_path']) == output / 'COMPLETE.json' and not (output / 'FAILED.json').exists(),
        'retained_complete_path')
    complete = read(retained['complete_path'])
    require(complete['status'] == 'COMPLETE' and complete['before_after_verified'] is True
        and complete['calls'] == 60 and complete['plan_sha256'] == job['plan_sha256']
        and complete['corpus_sha256'] == CORPUS_SHA256
        and complete['checkpoint']['commit_sha256'] == job['checkpoint_commit_sha256'],
        'only_verified_complete_calls_can_be_retained')
    for name, checksum in complete['receipts'].items():
        require(Path(name).name == name and sha(output / name) == checksum, 'retained_raw_receipt_changed')
    records = [read(output / name) for name in complete['receipts']
        if name.startswith('CALL_') and name.count('.') == 1]
    tasks = runner.validate_tasks(read(plan['corpus_path']))
    coverage = runner.reduce_coverage(tasks, records)
    require(len(tasks) == 30 and len(records) == 60
        and all(row['completed_items'] == 30 and row['missing_items'] == row['failed_items'] == 0
            for row in coverage.values()), 'retained_complete_cell_inventory')
    release = read(retained['release_path'])
    require(release['status'] == 'SAFE_TASK_BOUNDARY_RELEASED' and release['physical'] == config['physical']
        and release['generator'] == config['generator'] == original['generator']
        and release['supervisor'] == config['supervisor'] == original['supervisor'], 'retained_owned_release')


def verify_prior_matrix(prior):
    require(isinstance(prior, list) and len(prior) == 2, 'both_initial_matrix_lanes_required')
    physicals = set()
    for receipt in prior:
        for name in ('config', 'complete', 'release'):
            require(sha(receipt[name + '_path']) == receipt[name + '_sha256'], 'prior_matrix_receipt_hash')
        config = read(receipt['config_path'])
        complete = read(receipt['complete_path'])
        release = read(receipt['release_path'])
        physical = config['physical']
        require(physical in DEVICES and physical not in physicals
            and config.get('matrix', 'legacy_pilot') == 'legacy_pilot', 'prior_matrix_physical_identity')
        physicals.add(physical)
        require(config['source_commit'] == SOURCE_COMMIT and config['corpus_sha256'] == CORPUS_SHA256
            and config['gpu_uuid'] == DEVICES[physical], 'prior_matrix_source_and_corpus')
        require(complete['status'] == 'COMPLETE' and tuple(complete['completed']) == LABELS[physical]
            and complete['config_sha256'] == receipt['config_sha256'], 'initial_matrix_must_finish_before_kernel')
        require(release['status'] == 'SAFE_TASK_BOUNDARY_RELEASED' and release['physical'] == physical
            and release['generator'] == config['generator'] and release['supervisor'] == config['supervisor'],
            'prior_owned_release_binding')
    require(physicals == set(DEVICES), 'both_initial_matrix_lanes_required')


def retire(config, directory):
    physical = config['physical']
    expected = config['generator']
    supervisor = config['supervisor']
    stage = Path(config['stage'])
    require(stage.parent == GENERATOR_ROOT / f'gpu{physical}', 'owned_stage_path')
    require(read(stage / 'LAUNCH.json')['identity'] == expected, 'current_generator_launch')
    descriptors = {}
    paused = set()
    terminated = False
    until = min(time.time() + 900, config['hard_end_unix'] - 120)
    try:
        descriptors['supervisor'] = owned_descriptor(supervisor, physical, 'supervise', config['supervisor_cmdline_sha256'])
        descriptors['generator'] = owned_descriptor(expected, physical, 'generate', config['generator_cmdline_sha256'])
        write(directory / 'PRE_SIGNAL.json', dict(physical=physical, supervisor=supervisor,
            generator=expected, config_sha256=config['_sha256'], observed_unix=time.time(),
            reason='R130_authorized_generation_only_benchmark_reallocation'))
        signal.pidfd_send_signal(descriptors['supervisor'], signal.SIGSTOP)
        paused.add('supervisor')
        wait_stopped(supervisor)
        output = stage / f'gpu{physical}'
        while time.time() < until:
            require(identity(expected['pid']) == expected, 'generator_identity_changed')
            before = candidate_boundary(output)
            if before is not None:
                signal.pidfd_send_signal(descriptors['generator'], signal.SIGSTOP)
                paused.add('generator')
                wait_stopped(expected)
                after = boundary(output)
                if after == before:
                    break
                signal.pidfd_send_signal(descriptors['generator'], signal.SIGCONT)
                paused.remove('generator')
            time.sleep(.0005)
        else:
            raise TimeoutError('safe_task_boundary_unavailable_original_processes_resumed')
        files = {str(path.relative_to(stage)): sha(path) for path in sorted(output.iterdir()) if path.is_file()}
        write(directory / 'PRESERVED_CAPTURES.json', dict(files=files, progress=after,
            stage_plan_sha256=sha(stage / 'PLAN.json'), launch_sha256=sha(stage / 'LAUNCH.json'),
            supervisor=supervisor, generator=expected, original_files_unchanged=True))
        require(boundary(output) == after, 'paused_boundary_changed')
        write(directory / 'BOUNDARY_VERIFIED.json', dict(progress=after,
            preserved_sha256=sha(directory / 'PRESERVED_CAPTURES.json'), observed_unix=time.time()))
        terminated = True
        for role in ('supervisor', 'generator'):
            signal.pidfd_send_signal(descriptors[role], signal.SIGTERM)
        for role in ('supervisor', 'generator'):
            signal.pidfd_send_signal(descriptors[role], signal.SIGCONT)
            paused.discard(role)
        until = min(time.time() + 30, config['hard_end_unix'])
        while not (gone(expected) and gone(supervisor)):
            require(time.time() < until, 'owned_retirement_not_confirmed')
            time.sleep(.1)
        require(all(sha(stage / relative) == checksum for relative, checksum in files.items()),
            'retired_captures_changed')
        write(directory / 'RELEASED.json', dict(status='SAFE_TASK_BOUNDARY_RELEASED', physical=physical,
            generator=expected, supervisor=supervisor, captured_files=len(files),
            preserved_sha256=sha(directory / 'PRESERVED_CAPTURES.json'), observed_unix=time.time()))
    finally:
        for role in paused:
            try:
                signal.pidfd_send_signal(descriptors[role], signal.SIGCONT)
            except ProcessLookupError:
                pass
        for descriptor in descriptors.values():
            os.close(descriptor)
        if not terminated and descriptors:
            write(directory / 'NO_RETIREMENT.json', dict(status='ORIGINAL_PROCESSES_RESUMED_NO_RETRY',
                observed_unix=time.time()))


def scan(config):
    from gpu.orch_rich_hot_node2_scan import scan as existing_scan

    snapshot = existing_scan(config['physical'], Path(config['service_path']))
    require(snapshot['scanner_euid'] == 0 and snapshot['gpu']['uuid'] == config['gpu_uuid'],
        'privileged_exact_GPU_scan')
    return snapshot


def await_clear(config, directory, label, *, max_wait=120):
    until = min(time.time() + max_wait, config['hard_end_unix'] - 120)
    attempt = 0
    while time.time() < until:
        report = scan(config)
        path = directory / f'{label}.ADMISSION_{attempt:03d}.private.json'
        write(path, report)
        if report['clear'] and not report['blocking_reasons']:
            return path
        attempt += 1
        time.sleep(2)
    raise TimeoutError('bounded_fresh_admission_wait_exhausted_no_model_call')


def checkpoint_steps(output, complete, job):
    path = Path(output) / 'COMMIT.original.json'
    require(sha(path) == complete['checkpoint']['commit_sha256'] == job['checkpoint_commit_sha256'],
        'curve_original_commit_binding')
    steps = read(path).get('optimizer_steps')
    require(type(steps) is int and steps >= 0, 'curve_native_optimizer_steps')
    require('optimizer_steps' not in job or job['optimizer_steps'] == steps,
        'curve_operator_steps_must_match_native_commit')
    return steps


def private_curve(config, completed, directory):
    tasks = runner.validate_tasks(read(read(config['jobs'][0]['plan_path'])['corpus_path']))
    rows = []
    for job in config['jobs']:
        if job['label'] not in completed:
            continue
        plan = read(job['plan_path'])
        output = Path(plan['output_path'])
        complete = read(output / 'COMPLETE.json')
        require(complete['status'] == 'COMPLETE' and complete['before_after_verified'] is True,
            'verified_curve_evidence_required')
        require(complete['plan_sha256'] == job['plan_sha256'] and complete['corpus_sha256'] == CORPUS_SHA256
            and complete['checkpoint']['commit_sha256'] == job['checkpoint_commit_sha256'],
            'curve_plan_corpus_checkpoint_binding')
        for name, expected in complete['receipts'].items():
            require(Path(name).name == name and sha(output / name) == expected, 'curve_receipt_binding')
        records = [read(path) for path in sorted(output.glob('CALL_*.json'))
            if path.name.count('.') == 1]
        families = {}
        for family in sorted({task['family'] for task in tasks}):
            selected = [task for task in tasks if task['family'] == family]
            identifiers = {task['task_id'] for task in selected}
            families[family] = runner.reduce_coverage(selected,
                [record for record in records if record['task_id'] in identifiers])
        rows.append(dict(label=job['label'], checkpoint_commit_sha256=job['checkpoint_commit_sha256'],
            complete_sha256=sha(output / 'COMPLETE.json'), complete_path=str(output / 'COMPLETE.json'),
            optimizer_steps=checkpoint_steps(output, complete, job), families=families,
            pooled_secondary_only=complete['coverage']))
    path = directory / f'CURVE_{len(rows):02d}.private.json'
    write(path, dict(schema='R130_PRIVATE_CHECKPOINT_CURVE_V1', corpus_sha256=CORPUS_SHA256,
        exploratory=True, no_semantic_thought_unit_claims=True,
        pair_level_derived_metrics='not_reduced_here_private_metadata_retained', rows=rows))
    return path


def supervise(config_path, physical):
    config = validate(config_path, physical, preflight=True)
    config['_sha256'] = sha(config_path)
    directory = Path(config['supervisor_output'])
    directory.mkdir(parents=True, mode=0o700, exist_ok=False)
    completed = [entry['label'] for entry in config.get('retained_completed', [])]
    lock_path = directory.parent / f'physical{physical}.lock'
    with lock_path.open('a') as lock:
        fcntl.flock(lock.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        try:
            if config.get('matrix') == 'kernel_followup' or config.get('retained_completed'):
                if config.get('matrix') == 'kernel_followup':
                    verify_prior_matrix(config['prior_matrix'])
                require(gone(config['generator']) and gone(config['supervisor']), 'original_generator_pair_stays_retired')
                write(directory / 'REUSED_RELEASE.json', dict(status='REUSE_PREVIOUSLY_RELEASED_DEVICE_NO_SIGNALS',
                    prior_matrix=config.get('prior_matrix'), retained_completed=config.get('retained_completed'),
                    config_sha256=config['_sha256'], observed_unix=time.time()))
            else:
                retire(config, directory)
            for job in config['jobs']:
                if job['label'] in completed:
                    continue
                validate(config_path, physical)
                require(gone(config['generator']) and gone(config['supervisor']), 'released_owners_must_stay_gone')
                report_path = await_clear(config, directory, job['label'])
                validate(config_path, physical)
                with plan_environment(job['plan_path'], config['gpu_uuid']):
                    runner.prepare(job['plan_path'])
                remaining = int(config['hard_end_unix'] - time.time() - 10)
                require(remaining > 120, 'remaining_benchmark_wall')
                command = ['timeout', '--signal=TERM', '--kill-after=5s', str(remaining) + 's',
                    config['python'], '-B', '-m', 'gpu.orch_r130_checkpoint_benchmark', '--plan', job['plan_path']]
                environment = dict(os.environ, CUDA_VISIBLE_DEVICES=config['gpu_uuid'],
                    R130_ADMISSION_PLAN_SHA256=job['plan_sha256'], PYTHONPATH=config['source_root'],
                    PYTHONDONTWRITEBYTECODE='1', HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1',
                    TOKENIZERS_PARALLELISM='false', OMP_NUM_THREADS='1', MKL_NUM_THREADS='1')
                with (directory / (job['label'] + '.private.log')).open('x') as log:
                    process = subprocess.Popen(command, cwd=config['source_root'], env=environment,
                        stdin=subprocess.DEVNULL, stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
                    write(directory / (job['label'] + '.LAUNCH.json'), dict(status='LAUNCHED',
                        identity=identity(process.pid), plan_sha256=job['plan_sha256'],
                        config_sha256=config['_sha256'], scanner_sha256=sha(report_path),
                        hard_end_unix=config['hard_end_unix'], observed_unix=time.time()))
                    code = process.wait()
                write(directory / (job['label'] + '.EXIT.json'), dict(exit_code=code, observed_unix=time.time()))
                output = Path(read(job['plan_path'])['output_path'])
                require(code == 0 and (output / 'COMPLETE.json').is_file() and not (output / 'FAILED.json').exists(),
                    'benchmark_must_complete_no_retry')
                completed.append(job['label'])
                curve = private_curve(config, completed, directory)
                write(directory / (job['label'] + '.STATUS.json'), dict(status='COMPLETE',
                    complete_sha256=sha(output / 'COMPLETE.json'), curve_sha256=sha(curve),
                    curve_path=str(curve), observed_unix=time.time()))
            write(directory / 'COMPLETE.json', dict(status='COMPLETE', completed=completed,
                curve_path=str(curve), curve_sha256=sha(curve), config_sha256=config['_sha256'],
                observed_unix=time.time()))
        except BaseException as error:
            write(directory / 'FAILED.json', dict(status='FAILED', error_type=type(error).__name__,
                completed=completed, config_sha256=config['_sha256'], observed_unix=time.time()))
            raise


def main(argv=None):
    parser = argparse.ArgumentParser(description='R130 private bounded ovx0/1 operator sidecar')
    parser.add_argument('action', choices=('preflight', 'supervise'))
    parser.add_argument('--config', required=True, type=Path)
    parser.add_argument('--physical', required=True, type=int, choices=(0, 1))
    options = parser.parse_args(argv)
    try:
        if options.action == 'preflight':
            validate(options.config, options.physical, preflight=True)
        else:
            supervise(options.config, options.physical)
    except BaseException as error:
        print(json.dumps(dict(status='FAILED', error_type=type(error).__name__)))
        return 1
    print(json.dumps(dict(status='PASS', config_sha256=sha(options.config))))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
