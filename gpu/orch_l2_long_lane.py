"""A100 physical1 guardian; all science stages are SHORT's shared driver."""

import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re
import signal
import subprocess
import time

from gpu.orch_l2_long_backend import write
from organism_v6.orch_l2_long_parent import digest


GPU_INDEX = 1
GPU_UUID = 'GPU-604c4ea8-8c29-099e-76ed-571ec7d9be4b'
ROOT = Path('/tmp/orch_l2_long_20260914_attempt1')
SHARED_ROOT = Path('/tmp/orch_l2_shared_20260914_attempt1')
PYTHON = '/localhome/local-rohing/v2/venv/bin/python'
HOURS = 12
LEASE_CUTOFF = datetime(2026, 9, 25, tzinfo=timezone.utc).timestamp()
PHASES = ((1, 'experience'), (0, 'readout'), (1, 'sleep'), (1, 'readout')) + tuple(
    (cycle, phase) for cycle in (2, 3) for phase in ('experience', 'sleep', 'readout'))


def file_hash(path):
    from hashlib import sha256

    return sha256(Path(path).read_bytes()).hexdigest()


def scan(index, uuid):
    if (index, uuid) != (GPU_INDEX, GPU_UUID):
        raise ValueError('only_owned_physical1_scan')
    publication = json.loads((ROOT / 'PUBLICATION.json').read_text())
    for name, expected in publication['shared_scanner_files'].items():
        if file_hash(SHARED_ROOT / name) != expected:
            raise ValueError('shared_scanner_binding_changed')
    scan_root = ROOT / 'scans'
    scan_root.mkdir(exist_ok=True)
    for attempt in range(5):
        with (SHARED_ROOT / 'service_exceptions.json').open() as exceptions:
            result = subprocess.run(['python3', str(SHARED_ROOT / 'scanner.py'), str(index), uuid],
                stdin=exceptions, capture_output=True, text=True, timeout=45,
                env=dict(os.environ, CUDA_VISIBLE_DEVICES=''))
        report = json.loads(result.stdout)
        rows = [list(map(str.strip, line.split(','))) for line in report['gpus'].splitlines()]
        target = next(row for row in rows if row[0] == str(index))
        report['safe'] = (result.returncode == 0 and report['clear'] and target[1] == uuid
                          and 'A100' in target[2] and int(target[5]) <= 2)
        write(scan_root / f'{time.time_ns()}_{attempt}.json', report)
        if report['safe'] or report['owners'] or not report['unresolved']:
            return report
        if any(item.get('comm') != 'sshd' for item in report['unresolved']):
            return report
        time.sleep(2)
    return report


def verify_shared(root, prepared):
    from organism_v6 import orch_l2_shared as shared

    if root != SHARED_ROOT:
        raise ValueError('exact_shared_root_required')
    cohort = json.loads((root / 'COHORT.json').read_text())
    identity = json.loads((root / 'INITIAL.json').read_text())
    if (digest(cohort) != prepared['cohort_sha256'] or cohort['recipe'] != shared.RECIPE
            or cohort['caps'] != shared.CAPS or identity['state_sha256'] != shared.INITIAL_STATE):
        raise ValueError('exact_shared_cohort_recipe_initial_identity_required')
    if (shared.CAPS['all_calls'] > 20000 or shared.CAPS['updates_per_sleep'] > 6000
            or shared.RECIPE['trajectory_presentations'] != 4):
        raise ValueError('shared_budget_scope_drift')
    from organism_v6.orch_guided_bridge import AdapterIdentity

    AdapterIdentity.from_document(identity)
    return dict(cohort_sha256=digest(cohort), initial=identity,
                prepare_sha256=file_hash(root / 'PREPARE.json'), recipe=shared.RECIPE,
                source_sha256=file_hash(root / 'SOURCE.json') if (root / 'SOURCE.json').exists() else None,
                source_policy='SINGLE_SHARED_SOURCE_CURRENT_TRAIN_RECEIPTS_ONLY')


def native_command(source_root, shared_root, cycle, phase, *, resume_experience=False):
    if (cycle, phase) not in PHASES:
        raise ValueError('only_declared_long_stages')
    arguments = [PYTHON, '-m', 'gpu.orch_l2_shared_run', '--root', str(shared_root),
                 '--arm', 'LONG', '--cycle', str(cycle), '--phase', phase]
    if resume_experience:
        if (cycle, phase) != (1, 'experience'):
            raise ValueError('only_original_cycle1_experience_resume')
        arguments.append('--resume-experience')
    return arguments


def reconcile_resume(root, shared_root, publication):
    from gpu.orch_l2_long_envelope import parse_json_envelope

    state_path = root / 'RESUME_STATE_001.json'
    if file_hash(state_path) != publication.get('resume_state_sha256'):
        raise ValueError('published_resume_state_required')
    if file_hash(root / 'run/TERMINAL.json') != publication.get('original_terminal_sha256'):
        raise ValueError('published_original_terminal_required')
    state = json.loads(state_path.read_text())
    original = json.loads((root / 'run/START.json').read_text())
    terminal = json.loads((root / 'run/TERMINAL.json').read_text())
    if (original != state['original_start'] or original['gpu_uuid'] != GPU_UUID
            or terminal['status'] != 'FAILED'
            or terminal['error']['message'] != 'native_long_stage_failed:experience'
            or len(terminal['stages']) != 1 or terminal['stages'][0]['cycle'] != 1
            or terminal['stages'][0]['phase'] != 'experience'
            or not 0 <= terminal['assigned_gpu_hours'] < HOURS):
        raise ValueError('original_failed_guardian_required')
    for name, expected in state['archive']['members'].items():
        if Path(name).is_absolute() or '..' in Path(name).parts:
            raise ValueError('relative_resume_evidence_only')
        if file_hash(shared_root / name) != expected:
            raise ValueError('original_resume_evidence_changed:' + name)
    for index in ('0001', '0002'):
        name = index + '_LONG_C1'
        request_path = shared_root / 'parent_queue' / (name + '.request.json')
        request = json.loads(request_path.read_text())
        recovered = json.loads((shared_root / 'parent_queue' / (name + '.recovered.response.json')).read_text())
        provenance = recovered['recovery']
        saved = state['provider_outputs'][name]
        if (recovered['id'] != name or recovered['request_sha256'] != digest(request)
                or provenance['provider_calls'] != 0
                or provenance['request_file_sha256'] != file_hash(request_path)
                or provenance['original_response_sha256'] != file_hash(
                    request_path.with_name(name + '.response.json'))
                or provenance['stdout_sha256'] != saved['sha256']
                or provenance['parser_sha256'] != file_hash(Path(__file__).with_name('orch_l2_long_envelope.py'))
                or recovered['result'] != parse_json_envelope(saved['result'])):
            raise ValueError('exact_saved_provider_recovery_required')
    result = dict(original_start=original, original_terminal_sha256=file_hash(root / 'run/TERMINAL.json'),
                  resume_state_sha256=file_hash(state_path), prior_gpu_hours=terminal['assigned_gpu_hours'],
                  decisions_consumed=2, completed_episodes=4, child_calls=16, provider_calls=0)
    predecessor = publication.get('resume_predecessor_directory')
    if predecessor:
        if not re.fullmatch(r'run_resume_v5(?:_0[2-9])?', predecessor):
            raise ValueError('own_resume_predecessor_only')
        path = root / predecessor / 'TERMINAL.json'
        prior = json.loads(path.read_text())
        if (file_hash(path) != publication['resume_predecessor_terminal_sha256']
                or prior['status'] != 'FAILED' or len(prior['stages']) != 1
                or prior['stages'][0]['cycle'] != 1 or prior['stages'][0]['phase'] != 'experience'
                or not result['prior_gpu_hours'] <= prior['assigned_gpu_hours'] < HOURS):
            raise ValueError('failed_precollection_resume_receipt_required')
        result.update(prior_gpu_hours=prior['assigned_gpu_hours'],
                      predecessor_terminal_sha256=file_hash(path), predecessor_directory=predecessor)
    return result


def published_manifest(root, publication):
    name = publication.get('native_manifest_filename', 'PREPARE_LONG.json')
    if not re.fullmatch(r'PREPARE_LONG(?:_V[0-9]+)?\.json', name):
        raise ValueError('own_native_manifest_filename_required')
    return root / name


def allocation_deadline(started, shared_deadline, continuation=None):
    deadline = min(started + HOURS * 3600, shared_deadline, LEASE_CUTOFF)
    if continuation:
        original = continuation['original_start']
        deadline = min(deadline, original['deadline_unix'], original['started_unix'] + HOURS * 3600)
    return deadline


def process_identity(process_id):
    status = Path(f'/proc/{process_id}/stat').read_text().rsplit(')', 1)[1].split()
    return dict(pid=process_id, start_ticks=status[19], pgid=int(status[2]),
                boot_id=Path('/proc/sys/kernel/random/boot_id').read_text().strip())


def stop_owned(child, identity):
    if child.poll() is not None:
        return
    if process_identity(child.pid) != identity or identity['pgid'] != child.pid:
        raise RuntimeError('owned_process_identity_changed_no_signal')
    os.killpg(child.pid, signal.SIGTERM)
    try:
        child.wait(timeout=10)
    except subprocess.TimeoutExpired:
        if process_identity(child.pid) != identity:
            raise RuntimeError('owned_process_identity_changed_no_signal')
        os.killpg(child.pid, signal.SIGKILL)
        child.wait(timeout=10)


def run_lane(root, shared_root, source_root, *, resume_experience=False):
    from gpu import orch_l2_shared_run as shared_driver

    if root != ROOT or root.is_symlink() or shared_root != SHARED_ROOT:
        raise ValueError('own_long_root_and_shared_root_required')
    if shared_driver.DEVICES.get('LONG') != (GPU_INDEX, GPU_UUID):
        raise ValueError('shared_driver_long_hook_not_published')
    publication = json.loads((root / 'PUBLICATION.json').read_text())
    if (publication.get('status') != 'PUBLISHED_PRE_GPU' or not publication.get('cpu_tests_passed')
            or publication.get('gpu_uuid') != GPU_UUID):
        raise ValueError('own_published_cpu_pre_gpu_required')
    for name, expected in publication['files'].items():
        if file_hash(source_root / name) != expected:
            raise ValueError('long_published_source_drift:' + name)
    prepared = json.loads((shared_root / 'PREPARE.json').read_text())
    binding = verify_shared(shared_root, prepared)
    if publication['shared_prepare_sha256'] != binding['prepare_sha256']:
        raise ValueError('published_shared_preparation_drift')
    native_manifest = published_manifest(root, publication)
    if publication['native_manifest_sha256'] != file_hash(native_manifest):
        raise ValueError('published_long_native_manifest_drift')
    started = time.time()
    continuation = reconcile_resume(root, shared_root, publication) if resume_experience else None
    deadline = allocation_deadline(started, float((shared_root / 'DEADLINE').read_text()), continuation)
    if deadline <= started + 60:
        raise ValueError('no_time_remaining_in_shared_allocation')
    run_name = publication.get('resume_run_directory', 'run_resume_v5') if resume_experience else 'run'
    if resume_experience and not re.fullmatch(r'run_resume_v5(?:_0[2-9])?', run_name):
        raise ValueError('own_resume_directory_required')
    run = root / run_name
    run.mkdir(exist_ok=False)
    write(run / 'START.json', dict(started_unix=started, deadline_unix=deadline,
        assigned_physical_index=GPU_INDEX, gpu_uuid=GPU_UUID, max_gpu_hours=12,
        lease_cutoff_unix=LEASE_CUTOFF, shared_binding=binding, continuation=continuation))
    receipt = dict(status='FAILED', stages=[], unknown_process_signals=0)
    child, identity = None, None

    def handle_signal(signum, frame):
        if child is not None and identity is not None:
            stop_owned(child, identity)
        raise SystemExit(128 + signum)

    signal.signal(signal.SIGTERM, handle_signal)
    signal.signal(signal.SIGINT, handle_signal)
    try:
        for cycle, phase in PHASES:
            admission = scan(GPU_INDEX, GPU_UUID)
            write(run / f'C{cycle}_{phase}_ADMISSION.json', admission)
            if not admission['safe']:
                raise RuntimeError('physical1_admission_not_clear')
            if time.time() >= deadline:
                raise TimeoutError('long_12h_deadline')
            if phase == 'readout':
                while not (shared_root / 'SOURCE.json').exists():
                    if (shared_root / 'SOURCE_GUARD/FAILED.json').exists():
                        raise RuntimeError('shared_source_failed')
                    if time.time() >= deadline:
                        raise TimeoutError('shared_readout_source_deadline')
                    time.sleep(2)
            arguments = native_command(source_root, shared_root, cycle, phase,
                resume_experience=resume_experience and (cycle, phase) == (1, 'experience'))
            environment = dict(os.environ, CUDA_VISIBLE_DEVICES=GPU_UUID, CUDA_DEVICE_ORDER='PCI_BUS_ID',
                HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1', TOKENIZERS_PARALLELISM='false',
                OMP_NUM_THREADS='1', MKL_NUM_THREADS='1', PYTHONDONTWRITEBYTECODE='1',
                L2_NATIVE_MANIFEST=str(native_manifest))
            with (run / f'C{cycle}_{phase}.log').open('x') as stream:
                stage_started = time.time()
                child = subprocess.Popen(arguments, cwd=source_root, env=environment,
                    stdout=stream, stderr=subprocess.STDOUT, start_new_session=True)
                identity = process_identity(child.pid)
                launch = dict(cycle=cycle, phase=phase, process=identity,
                    command=arguments, started_unix=stage_started, gpu_uuid=GPU_UUID)
                write(run / f'C{cycle}_{phase}_LAUNCH.json', launch)
                try:
                    code = child.wait(timeout=max(0.1, deadline - time.time()))
                finally:
                    stop_owned(child, identity)
                    stage = dict(launch, exit_code=child.returncode,
                                 elapsed_seconds=time.time() - stage_started)
                    receipt['stages'].append(stage)
                    write(run / 'PROGRESS.json', receipt)
                completion = shared_root / 'LONG' / f'cycle{cycle}' / phase / 'COMPLETE.json'
                if completion.is_file():
                    stage['completion_sha256'] = file_hash(completion)
                write(run / 'PROGRESS.json', receipt)
                if code or not completion.is_file():
                    raise RuntimeError('native_long_stage_failed:' + phase)
                if json.loads(completion.read_text()).get('status') != 'COMPLETE':
                    raise RuntimeError('native_long_stage_not_complete:' + phase)
        receipt['status'] = 'COMPLETE'
    except BaseException as error:
        receipt['error'] = dict(type=type(error).__name__, message=str(error))
        raise
    finally:
        receipt.update(finished_unix=time.time(), elapsed_seconds=time.time() - started,
            assigned_gpu_hours=sum(stage['elapsed_seconds'] for stage in receipt['stages']) / 3600
                + (continuation['prior_gpu_hours'] if continuation else 0))
        write(run / 'TERMINAL.json', receipt)
        write(run / 'RELEASE_GPU1.json', scan(GPU_INDEX, GPU_UUID))
    return receipt


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', type=Path, default=ROOT)
    parser.add_argument('--shared-root', type=Path, default=SHARED_ROOT)
    parser.add_argument('--source-root', type=Path, required=True)
    parser.add_argument('--resume-experience', action='store_true')
    options = parser.parse_args()
    run_lane(options.root, options.shared_root, options.source_root, resume_experience=options.resume_experience)


if __name__ == '__main__':
    main()
