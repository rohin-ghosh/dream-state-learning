"""Enroll verified copies in a bounded successor without replaying reservations."""

import argparse
from contextlib import ExitStack
from copy import deepcopy
import fcntl
import hashlib
import json
import math
import os
from pathlib import Path
import re
import subprocess
import sys
import time

from gpu import orch_r146_benchmark_enrollment_phase as enrollment
from gpu import orch_r146_checkpoint_scheduler as scheduler


ROOT = Path('/localhome/local-rohing/orch_r130_checkpoint_benchmark_20260916_attempt1')
WALL = 1789617240.0
ORIGINAL_CONFIG_SHA = 'a22dfa29a16ef419de3cb2e2ad2740b673700c4669c9ecbfc76de1238dea0805'
PREDECESSOR_PHASE_SHA = 'f32bf19f79f8f0ded3d90376323a6bb30b1f88522db470b27d542d204b72843b'
SCHEMA = 'R146_BENCHMARK_ENROLLED_PHASE_V1'
sha, read, write, require = scheduler.sha, scheduler.read, scheduler.write, scheduler.require


def snapshot_delta(original, proposed):
    require(all(proposed.get(name) == checksum for name, checksum in original.items()),
            'all_original_source_bytes_preserved')
    additions = set(proposed) - set(original)
    require(3 <= len(additions) <= 16 and all(
        name.startswith(('gpu/orch_r146_', 'tests/test_orch_r146_')) and name.endswith('.py')
        for name in additions), 'only_bound_R146_source_additions')
    require('gpu/orch_r146_checkpoint_scheduler.py' in additions
            and 'gpu/orch_r146_successor_phase.py' in additions, 'new_scheduler_and_controller')


def bound(path, checksum):
    path = scheduler.regular_path(str(path), [str(ROOT)])
    require(path.is_file() and sha(path) == checksum, 'phase_bound_regular_file')
    return read(path)


def validate(path, *, allow_expired=False):
    require(os.environ.get('R146_PHASE_SHA256') == sha(path), 'phase_environment_binding')
    phase = read(path)
    require(phase['schema'] == SCHEMA and phase['helper_sha256'] == sha(__file__), 'phase_source_binding')
    require(Path(phase['operator_root']) == ROOT and Path(path).parent == ROOT, 'original_operator_root')
    require(phase['predecessor_phase_path'] == str(ROOT / 'SUCCESSOR_PHASE_V2.json')
            and phase['predecessor_phase_sha256'] == PREDECESSOR_PHASE_SHA, 'exact_previous_phase')
    previous_phase = bound(phase['predecessor_phase_path'], PREDECESSOR_PHASE_SHA)
    require(previous_phase['predecessor_path'] == str(ROOT / 'SCHEDULER_CONFIG_V1.json'),
            'original_scheduler_predecessor')
    original = bound(previous_phase['predecessor_path'], ORIGINAL_CONFIG_SHA)
    require(os.environ.get('CUDA_VISIBLE_DEVICES') == ''
            and hashlib.sha256(scheduler.socket.gethostname().encode()).hexdigest()
            == scheduler.sidecar.HOST_SHA256, 'node2_CPU_controller_only')
    source = Path(phase['source_root'])
    require(source.parent == ROOT and source.name.startswith('source_r146_')
            and source == Path(__file__).resolve().parents[1]
            and scheduler.sidecar.source_inventory(source) == phase['sources'], 'entire_new_source_binding')
    snapshot_delta(original['sources'], phase['sources'])
    require(phase['sources']['gpu/orch_r146_checkpoint_scheduler.py'] == sha(scheduler.__file__)
            and phase['sources']['gpu/orch_r146_successor_phase.py'] == sha(__file__)
            and phase['sources']['gpu/orch_r130_checkpoint_benchmark.py'] == scheduler.sidecar.RUNNER_SHA256,
            'exact_controller_scheduler_and_frozen_runner')
    for name in ('forks', 'registry', 'reservation', 'service', 'template_plan', 'corpus', 'lineages'):
        require(sha(original[name + '_path']) == original[name + '_sha256'], 'original_' + name + '_binding')
    registry = bound(phase['lineages_path'], phase['lineages_sha256'])
    enrollment.registry_delta(read(original['lineages_path']), registry)
    lineages = scheduler.enrolled_lineages(registry)
    validation = bound(phase['enrollment_validation_path'], phase['enrollment_validation_sha256'])
    require(validation['status'] == 'ACTUAL_COPIES_VALIDATED_NOT_ADMITTED'
            and validation['proposed_registry_sha256'] == phase['lineages_sha256']
            and validation['candidates_sha256'] == phase['candidates_sha256'], 'actual_copy_validation_binding')
    proposed_entries = [item['entry'] for item in validation['verified_lineages']]
    require(registry['lineages'] == read(original['lineages_path'])['lineages'] + proposed_entries
            and all(item['source_custody_content_independently_reviewed'] is True
                    for item in validation['verified_lineages']), 'reviewed_exact_new_lineages')
    candidates = bound(phase['candidates_path'], phase['candidates_sha256'])
    require(candidates == enrollment.ready_candidates(validation['verified_lineages']), 'exact_ready_candidates')
    forks = read(original['forks_path'])
    require(phase['hard_end_unix'] == previous_phase['hard_end_unix'] == min(WALL, forks['hard_deadline_unix'])
            and forks['hard_deadline_unix'] == original['lease_end_unix'] - 21600, 'unchanged_lease_wall')
    require(phase['total_call_cap'] == previous_phase['total_call_cap'] == 4800
            and phase['max_phase_jobs'] == previous_phase['max_phase_jobs'] == 58,
            'original_aggregate_and_phase_caps')
    require(phase['poll_seconds'] == 30 and phase['segment_seconds'] == 7200
            and phase['dispatch_seconds'] == 1800, 'unchanged_poll_and_dispatch_cadence')
    require(scheduler.finite_number(phase['created_unix']) and phase['created_unix'] <= time.time()
            and (allow_expired or time.time() < phase['hard_end_unix']), 'bounded_current_phase')
    require(Path(phase['output_root']).parent == ROOT
            and Path(phase['output_root']).name.startswith('successor_phase_r146_')
            and not Path(phase['output_root']).is_symlink(), 'new_phase_output')
    require(isinstance(phase['run_label'], str)
            and re.fullmatch('[a-z0-9_]{1,48}', phase['run_label']), 'bounded_run_label')
    gate = bound(phase['cpu_gate_path'], phase['cpu_gate_sha256'])
    require(gate['status'] == 'PASS' and gate['test_exit_code'] == 0
            and gate['helper_sha256'] == sha(__file__) and gate['scheduler_sha256'] == sha(scheduler.__file__)
            and gate['source_inventory_sha256'] == scheduler.digest(phase['sources'])
            and sha(gate['test_log_path']) == gate['test_log_sha256'], 'new_phase_CPU_provenance')
    require(sha(phase['builder_entry_path']) == phase['builder_entry_sha256']
            and Path(phase['builder_entry_path']).read_text().startswith('## [Builder] 2026-09-16'),
            'dated_builder_scope')
    template = dict(deepcopy(original), source_root=phase['source_root'], sources=phase['sources'],
        lineages_path=phase['lineages_path'], lineages_sha256=phase['lineages_sha256'],
        cpu_gate_path=phase['cpu_gate_path'], cpu_gate_sha256=phase['cpu_gate_sha256'],
        builder_entry_path=phase['builder_entry_path'], builder_entry_sha256=phase['builder_entry_sha256'])
    return phase, template, lineages


def predecessor_clear(phase):
    previous = read(phase['predecessor_phase_path'])
    output = Path(previous['output_root'])
    if not any((output / name).is_file() for name in ('COMPLETE.json', 'FAILED.json')):
        return False
    if not scheduler.sidecar.gone(read(output / 'STARTED.json')['identity']):
        return False
    for config_path in output.glob('SEGMENT_*.CONFIG.json'):
        config = read(config_path)
        segment_output = Path(config['output_root'])
        started = segment_output / 'STARTED.json'
        if started.exists() and not scheduler.sidecar.gone(read(started)['identity']):
            return False
        for launch in segment_output.glob('dispatch_*/**/LAUNCH.json'):
            if not scheduler.sidecar.gone(read(launch)['identity']):
                return False
    with ExitStack() as stack:
        for physical in (0, 1):
            lock = stack.enter_context((ROOT / f'physical{physical}.lock').open('a'))
            try:
                fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError:
                return False
    return True


def remaining_jobs(phase, config, taken):
    previous = read(phase['predecessor_phase_path'])
    configs = {}
    for output in (Path(previous['output_root']), Path(phase['output_root'])):
        for path in output.glob('SEGMENT_*.CONFIG.json'):
            configs[str(path)] = sha(path)
    charged = set()
    for path in Path(config['ledger_root']).glob('*.RESERVED.json'):
        claim = read(path)
        if claim.get('config_path') in configs:
            require(claim['config_sha256'] == configs[claim['config_path']], 'charged_phase_config_binding')
            charged.add(path.name.removesuffix('.RESERVED.json'))
    return enrollment.remaining_budget(phase['total_call_cap'], taken, len(charged), phase['max_phase_jobs'])


def segment_config(phase, template, now, remaining, segment):
    first = (math.floor(now / 1800) + 1) * 1800
    end = min(phase['hard_end_unix'], now + phase['segment_seconds'])
    require(scheduler.dispatch_window(dict(hard_end_unix=end, job_max_seconds=3600), first)['status']
            == 'FULL_JOB_WINDOW_AVAILABLE', 'full_first_dispatch_window')
    require(1 <= remaining <= 8, 'bounded_remaining_segment_jobs')
    return dict(template, created_unix=now, hard_end_unix=end, first_dispatch_unix=first,
        max_jobs=remaining, output_root=str(ROOT / f'scheduler_run_r146_{phase["run_label"]}_{segment:02d}'))


def publish_ready(config, lineages, document):
    require(set(document) == {'schema', 'lineage_id', 'manifest_path', 'manifest_sha256', 'commit_sha256'}
            and document['schema'] == scheduler.READY_SCHEMA and document['lineage_id'] in lineages,
            'exact_registered_ready_document')
    verified = enrollment.copied_checkpoint(
        {key: document[key] for key in enrollment.REFERENCE_FIELDS}, config['copy_roots'])
    require(document['commit_sha256'] != lineages[document['lineage_id']]['initial_commit_sha256']
            or verified['optimizer_steps'] == 0, 'initial_native_step_zero')
    raw = (json.dumps(document, indent=2, sort_keys=True) + '\n').encode()
    destination = Path(config['inbox_root']) / 'ready' / (hashlib.sha256(raw).hexdigest() + '.json')
    if not destination.exists():
        temporary = Path(config['inbox_root']) / ('.r146_ready_' + str(time.time_ns()))
        write(temporary, raw)
        os.link(temporary, destination)
        temporary.unlink()
    scheduler.candidate(config, lineages, destination)
    return dict(ready_path=str(destination), ready_sha256=sha(destination))


def node(path):
    phase, template, lineages = validate(path)
    output = Path(phase['output_root'])
    output.mkdir(mode=0o700, exist_ok=False)
    seeds = scheduler.seed_completed(template, lineages)
    sequence, segment = 0, 0
    active, active_path = None, None
    with (ROOT / 'successor_phase_owner.lock').open('a') as owner:
        fcntl.flock(owner, fcntl.LOCK_EX | fcntl.LOCK_NB)
        require(predecessor_clear(phase), 'predecessor_jobs_and_controller_gone')
        write(output / 'STARTED.json', dict(status='ENROLLED_SUCCESSOR_STARTED', phase_sha256=sha(path),
            identity=scheduler.sidecar.identity(os.getpid()), observed_unix=time.time()))
        try:
            ready = [publish_ready(template, lineages, item)
                     for item in read(phase['candidates_path'])]
            write(output / 'ENROLLMENT.json', dict(status='COPIES_ENROLLED_READY_PUBLISHED',
                phase_sha256=sha(path), lineages_sha256=phase['lineages_sha256'], ready=ready,
                observed_unix=time.time(), scientific_result_claim=False))
            while time.time() < phase['hard_end_unix']:
                phase, template, lineages = validate(path)
                taken, completed, _ = scheduler.ledger_state(template, seeds, lineages)
                remaining = remaining_jobs(phase, template, taken)
                physical, pending, dispatch = [], None, None
                if active is not None:
                    current = read(active_path)
                    statuses = sorted(Path(current['output_root']).glob('STATUS_*.json'))
                    if statuses:
                        receipt = read(statuses[-1])
                        physical, pending = receipt['active_physical'], receipt['pending_unique_checkpoints']
                        dispatch = receipt['next_dispatch_unix']
                    code = active.poll()
                    if code is not None:
                        terminal = Path(current['output_root']) / 'COMPLETE.json'
                        write(output / f'SEGMENT_{segment:02d}.EXIT.json', dict(exit_code=code,
                            observed_unix=time.time()))
                        require(code == 0 and terminal.is_file()
                                and read(terminal)['config_sha256'] == sha(active_path),
                                'segment_failed_no_automatic_replay')
                        active, active_path = None, None
                        segment += 1
                if active is None:
                    first = (math.floor(time.time() / 1800) + 1) * 1800
                    if remaining == 0 or scheduler.dispatch_window(
                            dict(hard_end_unix=phase['hard_end_unix'], job_max_seconds=3600), first)[
                                'status'] != 'FULL_JOB_WINDOW_AVAILABLE':
                        break
                    current = segment_config(phase, template, time.time(), remaining, segment)
                    active_path = output / f'SEGMENT_{segment:02d}.CONFIG.json'
                    write(active_path, current)
                    environment = dict(os.environ, R130_SCHEDULER_ADMISSION_SHA256=sha(active_path),
                        CUDA_VISIBLE_DEVICES='', PYTHONPATH=phase['source_root'], PYTHONDONTWRITEBYTECODE='1')
                    with (output / f'SEGMENT_{segment:02d}.private.log').open('x') as log:
                        active = subprocess.Popen([template['python'], '-B', '-m',
                            'gpu.orch_r146_checkpoint_scheduler', 'run', '--config', str(active_path)],
                            cwd=phase['source_root'], env=environment, stdin=subprocess.DEVNULL,
                            stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
                    write(output / f'SEGMENT_{segment:02d}.LAUNCH.json', dict(
                        identity=scheduler.sidecar.identity(active.pid), config_path=str(active_path),
                        config_sha256=sha(active_path), observed_unix=time.time()))
                    dispatch = current['first_dispatch_unix']
                write(output / f'STATUS_{sequence:06d}.json', dict(status='SEGMENT_RUNNING',
                    phase_sha256=sha(path), completed_checkpoint_count=len(completed),
                    future_completed_checkpoints=len(completed - seeds), reserved_checkpoint_count=len(taken),
                    remaining_total_call_budget=max(0, phase['total_call_cap'] - 60 * len(taken)),
                    active_physical=physical, pending_unique_checkpoints=pending, next_dispatch_unix=dispatch,
                    active_config_path=str(active_path), active_config_sha256=sha(active_path),
                    registered_lineages=len(lineages), observed_unix=time.time(), hard_end_unix=phase['hard_end_unix']))
                sequence += 1
                time.sleep(min(phase['poll_seconds'], max(0, phase['hard_end_unix'] - time.time())))
            if active is not None:
                active.wait(timeout=90)
            taken, completed, _ = scheduler.ledger_state(template, seeds, lineages)
            write(output / 'COMPLETE.json', dict(status='BOUNDED_PHASE_FINISHED', phase_sha256=sha(path),
                completed_checkpoint_count=len(completed), future_completed_checkpoints=len(completed - seeds),
                reserved_checkpoint_count=len(taken), next_dispatch_unix=None, observed_unix=time.time()))
        except BaseException as error:
            write(output / 'FAILED.json', dict(status='FAILED', phase_sha256=sha(path),
                error_type=type(error).__name__, next_dispatch_unix=None, observed_unix=time.time()))
            raise


def phase_status(phase):
    output = Path(phase['output_root'])
    terminal = [output / name for name in ('COMPLETE.json', 'FAILED.json') if (output / name).is_file()]
    paths = terminal or sorted(output.glob('STATUS_*.json'))
    require(bool(paths), 'phase_status_not_yet_available')
    return read(paths[-1])


def stage(path, action, payload):
    phase, config, lineages = validate(path)
    status = phase_status(phase)
    require(status['status'] == 'SEGMENT_RUNNING' and status['active_config_path'],
            'active_successor_segment_required')
    current_path = Path(status['active_config_path'])
    require(sha(current_path) == status['active_config_sha256'], 'active_segment_config_hash')
    current = read(current_path)
    output = Path(current['output_root'])
    require(not (output / 'COMPLETE.json').exists() and not (output / 'FAILED.json').exists()
            and not scheduler.sidecar.gone(read(output / 'STARTED.json')['identity']), 'active_scheduler_identity')
    require(time.time() + 180 < current['hard_end_unix'], 'copy_before_segment_wall')
    lineage = payload['lineage_id']
    require(lineage in ('legacy', 'pilot', 'kernel') and lineage in lineages
            and lineages[lineage]['initial_commit_sha256'] == payload['initial_commit_sha256'],
            'same_registered_original_source_root')
    key = scheduler.key_for(lineage, payload['commit_sha256'])
    seeds = scheduler.seed_completed(config, lineages)
    taken, _, _ = scheduler.ledger_state(config, seeds, lineages)
    for ready in (Path(config['inbox_root']) / 'ready').glob('*.json'):
        item = read(ready)
        if item['lineage_id'] == lineage and item['commit_sha256'] == payload['commit_sha256']:
            scheduler.candidate(config, lineages, ready)
            return dict(status='ALREADY_STAGED', lineage_id=lineage, commit_sha256=payload['commit_sha256'])
    if key in taken:
        return dict(status='ALREADY_RESERVED_NO_REPLAY', lineage_id=lineage, commit_sha256=payload['commit_sha256'])
    if action == 'known':
        return dict(status='NEEDS_COPY')
    require(action == 'stage', 'copy_stage_action')
    raw = sys.stdin.buffer.read(513 * 1024 * 1024)
    require(len(raw) <= 512 * 1024 * 1024 and hashlib.sha256(raw).hexdigest() == payload['archive_sha256'],
            'archive_hash')
    archive = ROOT / 'incoming' / ('future_' + lineage + '_' + payload['commit_sha256'] + '.tar')
    if archive.exists():
        require(sha(archive) == payload['archive_sha256'], 'existing_archive_hash')
    else:
        write(archive, raw)
    destination = Path(config['inbox_root']) / 'copies' / (lineage + '_' + payload['commit_sha256'])
    if not destination.exists():
        staging = destination.parent / ('.r146_' + key + '_' + str(os.getpid()))
        scheduler.sidecar.extract_regular_archive(archive, staging, payload['archive_sha256'])
        scheduler.sidecar.checkpoint_manifest(staging, payload['commit_sha256'])
        proof = read(staging / 'SOURCE_COPY_RECEIPT.json')
        require(proof['original_commit_sha256'] == payload['commit_sha256']
                and proof['initial_commit_sha256'] == payload['initial_commit_sha256']
                and proof['lineage_id'] == lineage and proof['before_after_verified'] is True, 'source_copy_proof')
        require({item.name for item in staging.iterdir()}
                == {'COMMIT.json', 'adapter', 'manifest.json', 'SOURCE_COPY_RECEIPT.json'}, 'adapter_only_payload')
        checkpoint = scheduler.sidecar.runner.verify_checkpoint(read(staging / 'manifest.json'), staging)
        require(checkpoint['adapter_state_sha256'] == payload['adapter_state_sha256'], 'native_adapter_state_hash')
        os.rename(staging, destination)
    manifest = destination / 'manifest.json'
    checkpoint = scheduler.sidecar.runner.verify_checkpoint(read(manifest), destination)
    require(checkpoint['commit_sha256'] == payload['commit_sha256']
            and checkpoint['adapter_state_sha256'] == payload['adapter_state_sha256'], 'destination_provenance')
    published = publish_ready(config, lineages, dict(schema=scheduler.READY_SCHEMA, lineage_id=lineage,
        manifest_path=str(manifest), manifest_sha256=sha(manifest), commit_sha256=payload['commit_sha256']))
    return dict(status='COPIED_AND_READY_VERIFIED', lineage_id=lineage, commit_sha256=payload['commit_sha256'],
        archive_sha256=sha(archive), manifest_sha256=sha(manifest), ready_sha256=published['ready_sha256'],
        copy_receipt_sha256=sha(destination / 'SOURCE_COPY_RECEIPT.json'))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=['node', 'status', 'validate', 'known', 'stage'])
    parser.add_argument('--config', type=Path, required=True)
    parser.add_argument('--payload')
    args = parser.parse_args()
    if args.action == 'node':
        node(args.config)
    elif args.action in ('known', 'stage'):
        print(json.dumps(stage(args.config, args.action, json.loads(args.payload)), sort_keys=True))
    else:
        phase, _, _ = validate(args.config, allow_expired=args.action == 'status')
        print(json.dumps(phase_status(phase) if args.action == 'status' else dict(status='PASS'), sort_keys=True))


if __name__ == '__main__':
    main()
