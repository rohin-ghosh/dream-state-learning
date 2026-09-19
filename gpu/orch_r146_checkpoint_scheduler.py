"""Bounded node2 saved-checkpoint polling; no parenting or source-node access.

R130_SCHEDULER_ADMISSION_SHA256 must bind the complete operator config.
Only content-addressed READY receipts beneath the admitted local inbox are
polled. New original/R137 lineages require a hash-pinned enrollment registry.
The frozen six-checkpoint results seed deduplication. Reservations are durable
and never replayed after an ambiguous exit. Both physical0/1 locks are held
throughout the bounded scheduler lifetime; no generator is ever signaled.
Private output and status-only receipts are separate, immutable files.

Non-material R146 repair: require the full declared dispatch window before
admission and reservation publication; preserve the frozen R130 protocol.
"""

import argparse
from contextlib import ExitStack
from datetime import datetime, timezone
import fcntl
import hashlib
import json
import math
import os
from pathlib import Path
import re
import shlex
import socket
import subprocess
import time

from gpu import orch_r130_benchmark_sidecar as sidecar


SCHEMA = 'R130_SAVED_CHECKPOINT_SCHEDULER_V1'
LINEAGES_SCHEMA = 'R130_SAVED_CHECKPOINT_LINEAGES_V1'
READY_SCHEMA = 'R130_SAVED_CHECKPOINT_READY_V1'
RELAY_SCHEMA = 'R130_SCHEDULER_STATUS_RELAY_V1'
REGISTRY_SHA256 = '41bb6acbd4a65fa1158d7720b5be801a1fa247b9d4e84f0efc1ddd96e023a3fc'
SEED_LABELS = {'legacy_initial': 'legacy', 'legacy_sleep17': 'legacy',
    'pilot_initial': 'pilot', 'pilot_latest': 'pilot',
    'kernel_initial': 'kernel', 'kernel_first_sleep': 'kernel'}
require = sidecar.require
sha = sidecar.sha
read = sidecar.read
write = sidecar.write
digest = sidecar.digest


def regular_path(value, roots):
    path = Path(value)
    require(path.is_absolute() and '..' not in path.parts, 'absolute_local_path_required')
    require(not any(parent.is_symlink() for parent in (path, *path.parents)), 'no_symlink_paths')
    resolved = path.resolve(strict=True)
    require(any(resolved.is_relative_to(Path(root).resolve(strict=True)) for root in roots),
        'path_outside_admitted_local_roots')
    return resolved


def finite_number(value):
    return type(value) in (int, float) and math.isfinite(value)


def dispatch_window(config, now):
    require(finite_number(now) and finite_number(config['hard_end_unix'])
        and type(config['job_max_seconds']) is int and config['job_max_seconds'] == 3600,
        'fixed_finite_dispatch_budget')
    available = config['hard_end_unix'] - now
    required = config['job_max_seconds'] + 15
    return dict(status='FULL_JOB_WINDOW_AVAILABLE' if available > required else 'DEFER_WITHOUT_RESERVATION',
        available_seconds=available, required_seconds=required,
        reservation_created=False, failed_checkpoint_replayed=False)


def key_for(lineage_id, commit_sha256):
    return digest(dict(lineage_id=lineage_id, commit_sha256=commit_sha256,
        corpus_sha256=sidecar.CORPUS_SHA256))


def enrolled_lineages(document):
    require(set(document) == {'schema', 'lineages'} and document['schema'] == LINEAGES_SCHEMA,
        'lineage_registry_schema')
    require(isinstance(document['lineages'], list) and 3 <= len(document['lineages']) <= 64,
        'bounded_lineage_inventory')
    entries = {}
    for item in document['lineages']:
        fields = {'lineage_id', 'cohort', 'initial_commit_sha256'}
        if item.get('cohort') == 'R137':
            fields |= {'first_sleep_commit_sha256', 'programme_start_unix'}
        require(set(item) == fields, 'lineage_fields')
        name = item['lineage_id']
        require(isinstance(name, str) and re.fullmatch('[a-z][a-z0-9_]{0,63}', name), 'lineage_identifier')
        require(name not in entries and sidecar.runner._hash(item['initial_commit_sha256']),
            'unique_pinned_lineage')
        require((item['cohort'] == 'original' and name in ('legacy', 'pilot', 'kernel'))
            or (item['cohort'] == 'R137' and name.startswith('r137_')), 'only_original_or_R137_scope')
        if item['cohort'] == 'R137':
            require(sidecar.runner._hash(item['first_sleep_commit_sha256'])
                and item['first_sleep_commit_sha256'] != item['initial_commit_sha256']
                and finite_number(item['programme_start_unix'])
                and 0 < item['programme_start_unix'] <= time.time(), 'R137_baselines_and_start_pinned')
        entries[name] = item
    require(set(('legacy', 'pilot', 'kernel')) <= set(entries), 'all_original_lineages_registered')
    return entries


def seed_completed(config, lineages):
    registry = read(config['registry_path'])
    require(registry['status'] == 'EXECUTION_COMPLETE_VERIFIED'
        and registry['corpus_sha256'] == sidecar.CORPUS_SHA256
        and registry['runner_sha256'] == sidecar.RUNNER_SHA256, 'frozen_seed_registry')
    require(len(registry['checkpoints']) == 6
        and {row['label'] for row in registry['checkpoints']} == set(SEED_LABELS), 'six_exact_seed_checkpoints')
    keys = set()
    for row in registry['checkpoints']:
        require(sha(row['complete_path']) == row['complete_sha256'], 'seed_native_receipt_binding')
        lineage = SEED_LABELS[row['label']]
        if row['label'].endswith('_initial'):
            require(row['checkpoint_commit_sha256'] == lineages[lineage]['initial_commit_sha256'],
                'original_lineage_baseline_binding')
        keys.add(key_for(lineage, row['checkpoint_commit_sha256']))
    require(len(keys) == 6, 'distinct_seed_checkpoint_keys')
    return keys


def validate(config_path):
    require(os.environ.get('R130_SCHEDULER_ADMISSION_SHA256') == sha(config_path), 'scheduler_admission_binding')
    config = read(config_path)
    require(config['schema'] == SCHEMA and config['source_commit'] == sidecar.SOURCE_COMMIT,
        'scheduler_schema_source')
    require(hashlib.sha256(socket.gethostname().encode()).hexdigest() == sidecar.HOST_SHA256,
        'only_bound_node2')
    require(config['physical_devices'] == [0, 1]
        and config['gpu_uuids'] == [sidecar.DEVICES[0], sidecar.DEVICES[1]], 'only_benchmark_devices')
    require(os.environ.get('CUDA_VISIBLE_DEVICES') == '', 'scheduler_is_CPU_only')
    source = Path(config['source_root']).resolve(strict=True)
    require(source == Path(__file__).resolve().parents[1]
        and sidecar.source_inventory(source) == config['sources'], 'entire_scheduler_source_binding')
    require(sha(source / 'gpu/orch_r130_checkpoint_benchmark.py') == sidecar.RUNNER_SHA256,
        'immutable_runner_source')
    require(config['registry_sha256'] == REGISTRY_SHA256
        and config['corpus_sha256'] == sidecar.CORPUS_SHA256, 'frozen_registry_and_corpus')
    for name in ('registry', 'lineages', 'cpu_gate', 'builder_entry', 'forks', 'service',
            'reservation', 'corpus', 'template_plan'):
        require(sha(config[name + '_path']) == config[name + '_sha256'], name + '_hash_binding')
    root = Path(config['registry_path']).resolve().parent
    require(Path(config['operator_root']).resolve() == root, 'original_operator_root')
    for name, suffix in [('inbox', 'scheduler_inbox'), ('ledger', 'scheduler_ledger')]:
        path = Path(config[name + '_root'])
        require(path == root / suffix and path.is_dir() and not path.is_symlink(), 'fixed_' + name + '_root')
        require(path.stat().st_uid == os.getuid() and path.stat().st_mode & 0o077 == 0,
            'private_owned_' + name)
    require(config['copy_roots'] == [str(root / 'checkpoints'), str(root / 'scheduler_inbox/copies')],
        'only_checkpoint_copy_roots')
    output = Path(config['output_root'])
    require(output.parent == root and re.fullmatch('scheduler_run_[a-z0-9_]+', output.name)
        and not output.is_symlink(), 'new_scheduler_output_scope')
    forks = read(config['forks_path'])
    require(Path(config['forks_path']) == sidecar.GENERATOR_ROOT / 'FORKS.json'
        and forks['node'] == 'ovx' and forks['uuid_by_index'][:2] == config['gpu_uuids'], 'original_lease_devices')
    require(config['lease_end_unix'] == forks['lease_end_unix']
        and forks['hard_deadline_unix'] == config['lease_end_unix'] - 21600, 'original_six_hour_margin')
    require(all(finite_number(config[name]) for name in ('created_unix', 'hard_end_unix', 'first_dispatch_unix'))
        and config['created_unix'] <= time.time() < config['hard_end_unix']
        <= min(config['created_unix'] + 7200, forks['hard_deadline_unix']), 'bounded_scheduler_wall')
    require(config['created_unix'] <= config['first_dispatch_unix'] < config['hard_end_unix'], 'first_dispatch_bound')
    require(config['poll_seconds'] == 30 and config['dispatch_seconds'] == 1800
        and type(config['max_jobs']) is int and 1 <= config['max_jobs'] <= 32
        and config['job_max_seconds'] == 3600, 'bounded_poll_dispatch_and_jobs')
    reservation = read(config['reservation_path'])
    require(reservation['node_alias'] == 'node2' and reservation['physical_devices'] == [0, 1]
        and reservation['ad_hoc_generator_takeover_allowed'] is False
        and reservation['preserved_generation_devices'] == list(range(2, 8)), 'benchmark_reservation_only')
    gate = read(config['cpu_gate_path'])
    require(gate['status'] == 'PASS' and gate['test_exit_code'] == 0
        and gate['scheduler_sha256'] == sha(__file__)
        and gate['source_inventory_sha256'] == digest(config['sources'])
        and gate['test_log_sha256'] == sha(gate['test_log_path']), 'CPU_provenance_gate')
    require(Path(config['builder_entry_path']).read_text().startswith('## [Builder] 2026-09-16'),
        'dated_builder_gate_required')
    template = read(config['template_plan_path'])
    require(template['model_id'] == sidecar.runner.MODEL_ID
        and template['base_sha256'] == sidecar.runner.BASE_SHA256
        and template['decoder'] == sidecar.runner.DECODER
        and template['corpus_path'] == config['corpus_path']
        and template['corpus_sha256'] == sidecar.CORPUS_SHA256, 'frozen_template_contract')
    require(Path(config['python']).is_absolute() and Path(config['python']).is_file(), 'pinned_python_path')
    require(len(config['release_receipts']) == 2, 'two_original_release_receipts')
    for physical, receipt in enumerate(config['release_receipts']):
        require(sha(receipt['path']) == receipt['sha256'], 'release_receipt_binding')
        release = read(receipt['path'])
        require(release['status'] == 'SAFE_TASK_BOUNDARY_RELEASED' and release['physical'] == physical
            and sidecar.gone(release['generator']) and sidecar.gone(release['supervisor']),
            'original_generator_pairs_remain_retired')
    lineages = enrolled_lineages(read(config['lineages_path']))
    return config, lineages, seed_completed(config, lineages)


def candidate(config, lineages, path):
    path = regular_path(path, [Path(config['inbox_root']) / 'ready'])
    require(path.name == sha(path) + '.json', 'content_addressed_ready_receipt')
    item = read(path)
    require(set(item) == {'schema', 'lineage_id', 'manifest_path', 'manifest_sha256', 'commit_sha256'}
        and item['schema'] == READY_SCHEMA, 'ready_fields_no_prompts_or_commands')
    require(item['lineage_id'] in lineages, 'lineage_not_pinned_in_admitted_registry')
    manifest = regular_path(item['manifest_path'], config['copy_roots'])
    require(sha(manifest) == item['manifest_sha256'], 'ready_manifest_binding')
    document = read(manifest)
    checkpoint = sidecar.runner.verify_checkpoint(document, manifest.parent)
    for name in ('adapter_path', 'commit_path'):
        regular_path(checkpoint[name], config['copy_roots'])
    require(checkpoint['commit_sha256'] == item['commit_sha256'], 'ready_original_commit_binding')
    commit = read(checkpoint['commit_path'])
    require(type(commit.get('optimizer_steps')) is int and commit['optimizer_steps'] >= 0
        and finite_number(commit.get('created_unix'))
        and 0 < commit['created_unix'] <= time.time(), 'native_checkpoint_metadata')
    initial = item['commit_sha256'] == lineages[item['lineage_id']]['initial_commit_sha256']
    require(not initial or commit['optimizer_steps'] == 0, 'registered_initial_is_native_step_zero')
    return dict(item, key=key_for(item['lineage_id'], item['commit_sha256']),
        ready_path=str(path), ready_sha256=sha(path), created_unix=commit['created_unix'],
        is_initial=initial, cohort=lineages[item['lineage_id']]['cohort'],
        is_first_sleep=item['commit_sha256'] == lineages[item['lineage_id']].get('first_sleep_commit_sha256'))


def select_candidates(items, taken, last_lineage, physical, completed, lineages, completed_times):
    require(physical in (0, 1), 'only_benchmark_dispatch')
    groups = {}
    for item in items:
        if item['key'] in taken:
            continue
        lineage = lineages[item['lineage_id']]
        if key_for(item['lineage_id'], lineage['initial_commit_sha256']) not in completed and not item['is_initial']:
            continue
        if item['cohort'] == 'R137' and not item['is_initial']:
            first_sleep = key_for(item['lineage_id'], lineage['first_sleep_commit_sha256'])
            if first_sleep not in completed and not item['is_first_sleep']:
                continue
            if first_sleep in completed:
                start = lineage['programme_start_unix']
                last_hour = max([0] + [math.floor((timestamp - start) / 3600)
                    for timestamp in completed_times.get(item['lineage_id'], [])])
                if item['created_unix'] < start + (last_hour + 1) * 3600:
                    continue
        groups.setdefault(item['lineage_id'], []).append(item)
    selected = []
    for group in groups.values():
        initial = [item for item in group if item['is_initial']]
        baseline = initial or [item for item in group if item['is_first_sleep']]
        if baseline:
            selected.append(min(baseline, key=lambda item: item['ready_sha256']))
        elif group[0]['cohort'] == 'R137':
            selected.append(min(group, key=lambda item: (item['created_unix'], item['commit_sha256'])))
        else:
            selected.append(max(group, key=lambda item: (item['created_unix'], item['commit_sha256'])))
    preferred = 'original' if physical == 0 else 'R137'
    selected.sort(key=lambda item: (0 if item['is_initial'] else 1 if item['is_first_sleep'] else 2, item['cohort'] != preferred,
        item['lineage_id'] <= (last_lineage or ''), item['lineage_id']))
    return selected


def ledger_state(config, seeds, lineages):
    root = Path(config['ledger_root'])
    taken = set(seeds)
    completed = set(seeds)
    completed_times = {}
    for path in sorted(root.glob('*.RESERVED.json')):
        claim = read(path)
        key = path.name.removesuffix('.RESERVED.json')
        require(key == key_for(claim['lineage_id'], claim['commit_sha256'])
            and claim['corpus_sha256'] == sidecar.CORPUS_SHA256, 'ledger_claim_binding')
        taken.add(key)
        terminal_path = root / (key + '.COMPLETE.json')
        if terminal_path.exists():
            terminal = read(terminal_path)
            require(terminal['claim_sha256'] == sha(path) and terminal['key'] == key
                and sha(terminal['native_complete_path']) == terminal['native_complete_sha256'],
                'ledger_complete_binding')
            complete = read(terminal['native_complete_path'])
            require(complete['status'] == 'COMPLETE' and complete['calls'] == 60
                and complete['before_after_verified'] is True
                and sha(claim['plan_path']) == claim['plan_sha256'] == complete['plan_sha256']
                and complete['corpus_sha256'] == sidecar.CORPUS_SHA256
                and complete['checkpoint']['commit_sha256'] == claim['commit_sha256'], 'ledger_native_complete')
            completed.add(key)
            completed_times.setdefault(claim['lineage_id'], []).append(claim['checkpoint_created_unix'])
    return taken, completed, completed_times


def dispatch(config, config_path, lineages, item, physical, directory):
    require(type(physical) is int and physical in (0, 1), 'only_benchmark_dispatch')
    validate(config_path)
    if dispatch_window(config, time.time())['status'] != 'FULL_JOB_WINDOW_AVAILABLE':
        return None
    require(candidate(config, lineages, item['ready_path']) == item, 'candidate_changed_before_dispatch')
    job_root = directory / (f'physical{physical}_job_' + item['key'])
    job_root.mkdir(mode=0o700)
    scan_config = dict(physical=physical, gpu_uuid=sidecar.DEVICES[physical],
        service_path=config['service_path'], hard_end_unix=config['hard_end_unix'])
    scan = sidecar.scan(scan_config)
    scan_path = job_root / 'ADMISSION.private.json'
    write(scan_path, scan)
    if not scan['clear'] or scan['blocking_reasons']:
        write(job_root / 'DEFERRED.json', dict(status='DEVICE_BUSY_NO_SIGNALS', physical=physical,
            scanner_sha256=sha(scan_path), observed_unix=time.time()))
        return None
    plan = dict(read(config['template_plan_path']), source_root=config['source_root'], sources=config['sources'],
        gpu_uuid=sidecar.DEVICES[physical], manifest_path=item['manifest_path'],
        manifest_sha256=item['manifest_sha256'], output_path=str(job_root / 'results'),
        hard_end_unix=min(config['hard_end_unix'] - 15, time.time() + config['job_max_seconds']))
    plan_path = job_root / 'PLAN.json'
    write(plan_path, plan)
    with sidecar.plan_environment(plan_path, sidecar.DEVICES[physical]):
        context = sidecar.runner.prepare(plan_path)
    require(len(context['tasks']) == 30 and context['checkpoint']['commit_sha256'] == item['commit_sha256'],
        'exact_frozen_corpus_and_checkpoint')
    validate(config_path)
    claim_path = Path(config['ledger_root']) / (item['key'] + '.RESERVED.json')
    claim = dict(lineage_id=item['lineage_id'], commit_sha256=item['commit_sha256'],
        corpus_sha256=sidecar.CORPUS_SHA256, ready_sha256=item['ready_sha256'],
        config_path=str(config_path), config_sha256=sha(config_path), plan_path=str(plan_path),
        plan_sha256=sha(plan_path), checkpoint_created_unix=item['created_unix'], observed_unix=time.time())
    window = dispatch_window(config, time.time())
    if window['status'] != 'FULL_JOB_WINDOW_AVAILABLE':
        write(job_root / 'DEFERRED.json', dict(window, physical=physical, observed_unix=time.time()))
        return None
    write(claim_path, claim)
    remaining = max(1, int(plan['hard_end_unix'] - time.time()))
    command = ['timeout', '--signal=TERM', '--kill-after=5s', str(remaining) + 's',
        config['python'], '-B', '-m', 'gpu.orch_r130_checkpoint_benchmark', '--plan', str(plan_path)]
    environment = dict(os.environ, CUDA_VISIBLE_DEVICES=sidecar.DEVICES[physical],
        R130_ADMISSION_PLAN_SHA256=sha(plan_path), PYTHONPATH=config['source_root'], PYTHONDONTWRITEBYTECODE='1',
        HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1', TOKENIZERS_PARALLELISM='false', OMP_NUM_THREADS='1', MKL_NUM_THREADS='1')
    with (job_root / 'runner.private.log').open('x') as log:
        process = subprocess.Popen(command, cwd=config['source_root'], env=environment,
            stdin=subprocess.DEVNULL, stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
    write(job_root / 'LAUNCH.json', dict(status='LAUNCHED', identity=sidecar.identity(process.pid), physical=physical,
        config_sha256=sha(config_path), plan_sha256=sha(plan_path), claim_sha256=sha(claim_path),
        scanner_sha256=sha(scan_path), observed_unix=time.time()))
    return dict(process=process, item=item, physical=physical, job_root=job_root,
        claim_path=claim_path, job=dict(label=item['key'], plan_path=str(plan_path),
            plan_sha256=sha(plan_path), checkpoint_commit_sha256=item['commit_sha256']))


def finish(config, active, code):
    directory = active['job_root']
    item = active['item']
    write(directory / 'EXIT.json', dict(exit_code=code, observed_unix=time.time()))
    try:
        output = directory / 'results'
        require(code == 0 and not (output / 'FAILED.json').exists(), 'native_runner_completed_without_failure')
        complete = read(output / 'COMPLETE.json')
        require(complete['calls'] == 60, 'sixty_native_calls_required')
        curve = sidecar.private_curve({'jobs': [active['job']]}, [item['key']], directory)
        plan = read(active['job']['plan_path'])
        tasks = sidecar.runner.validate_tasks(read(plan['corpus_path']))
        records = [read(output / name) for name in complete['receipts']
            if name.startswith('CALL_') and name.count('.') == 1]
        coverage = sidecar.runner.reduce_coverage(tasks, records)
        require(coverage == complete['coverage'] and len(records) == 60
            and all(row['completed_items'] == 30 and row['missing_items'] == row['failed_items'] == 0
                for row in coverage.values()), 'full_call_coverage_separate_from_validity')
        write(Path(config['ledger_root']) / (item['key'] + '.COMPLETE.json'), dict(status='COMPLETE', key=item['key'],
            claim_sha256=sha(active['claim_path']), native_complete_path=str(output / 'COMPLETE.json'),
            native_complete_sha256=sha(output / 'COMPLETE.json'), private_curve_path=str(curve),
            private_curve_sha256=sha(curve), observed_unix=time.time()))
        return True
    except Exception as error:
        write(directory / 'FAILED.json', dict(status='FAILED', error_type=type(error).__name__,
            key=item['key'], automatic_retry=False, observed_unix=time.time()))
        return False


def run(config_path):
    config, lineages, seeds = validate(config_path)
    output = Path(config['output_root'])
    output.mkdir(mode=0o700, exist_ok=False)
    receipts = output / 'receipts'
    receipts.mkdir(mode=0o700)
    active = {}
    admitted = 0
    failed = 0
    sequence = 0
    dispatch_number = 0
    last_lineage = {0: None, 1: None}
    next_dispatch = config['first_dispatch_unix']
    final_error = None
    with ExitStack() as stack:
        for physical in (0, 1):
            lock = stack.enter_context((Path(config['operator_root']) / f'physical{physical}.lock').open('a'))
            fcntl.flock(lock.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        write(output / 'STARTED.json', dict(status='BOUNDED_SCHEDULER_RUNNING', identity=sidecar.identity(os.getpid()),
            config_sha256=sha(config_path), physical_devices=[0, 1], hard_end_unix=config['hard_end_unix'],
            next_dispatch_unix=next_dispatch if dispatch_window(config, max(next_dispatch, time.time()))[
                'status'] == 'FULL_JOB_WINDOW_AVAILABLE' else None, observed_unix=time.time()))
        try:
            while time.time() < config['hard_end_unix']:
                config, lineages, seeds = validate(config_path)
                for physical, job in list(active.items()):
                    code = job['process'].poll()
                    if code is not None:
                        failed += not finish(config, job, code)
                        del active[physical]
                taken, completed, completed_times = ledger_state(config, seeds, lineages)
                items = []
                inbox_paths = sorted((Path(config['inbox_root']) / 'ready').glob('*.json'))
                for path in inbox_paths[:256]:
                    receipt_id = digest(str(path))
                    try:
                        item = candidate(config, lineages, path)
                        items.append(item)
                        receipt = receipts / (receipt_id + '.ACCEPTED.json')
                        if not receipt.exists():
                            write(receipt, dict(status='READY_VALIDATED', ready_sha256=item['ready_sha256'],
                                key=item['key'], deduplicated=item['key'] in taken, observed_unix=time.time()))
                    except Exception as error:
                        receipt = receipts / (receipt_id + '.REJECTED.json')
                        if not receipt.exists():
                            write(receipt, dict(status='REJECTED_NO_MODEL_CALL', error_type=type(error).__name__,
                                observed_unix=time.time()))
                now = time.time()
                if now >= next_dispatch and dispatch_window(config, now)['status'] == 'FULL_JOB_WINDOW_AVAILABLE':
                    dispatch_number += 1
                    directory = output / f'dispatch_{dispatch_number:04d}'
                    directory.mkdir(mode=0o700)
                    for physical in (0, 1):
                        if physical in active or admitted >= config['max_jobs']:
                            continue
                        selected = select_candidates(items, taken, last_lineage[physical], physical,
                            completed, lineages, completed_times)
                        if not selected:
                            continue
                        item = selected[0]
                        try:
                            job = dispatch(config, config_path, lineages, item, physical, directory)
                            if job is not None:
                                active[physical] = job
                                taken.add(item['key'])
                                admitted += 1
                                last_lineage[physical] = item['lineage_id']
                        except Exception as error:
                            write(directory / f'physical{physical}.FAILED.json', dict(status='ADMISSION_FAILED_NO_MODEL_REPLAY',
                                key=item['key'], error_type=type(error).__name__, observed_unix=time.time()))
                            taken.add(item['key'])
                            failed += 1
                    next_dispatch = (math.floor(time.time() / config['dispatch_seconds']) + 1) * config['dispatch_seconds']
                status = dict(status='BOUNDED_POLLING', sequence=sequence, config_sha256=sha(config_path),
                    observed_unix=time.time(), hard_end_unix=config['hard_end_unix'],
                    next_dispatch_unix=next_dispatch if dispatch_window(config, max(next_dispatch, time.time()))[
                        'status'] == 'FULL_JOB_WINDOW_AVAILABLE' else None,
                    baseline_completed_checkpoints=len(seeds), completed_checkpoint_count=len(completed),
                    future_completed_checkpoints=len(completed - seeds), admitted_future_checkpoints=admitted,
                    active_physical=sorted(active), ready_receipt_count=len(items),
                    rejected_receipt_count=len(list(receipts.glob('*.REJECTED.json'))),
                    inbox_overflow_count=max(0, len(inbox_paths) - 256),
                    pending_unique_checkpoints=len({item['key'] for item in items} - taken), failed_attempts=failed,
                    registered_original_lineages=sum(item['cohort'] == 'original' for item in lineages.values()),
                    registered_R137_lineages=sum(item['cohort'] == 'R137' for item in lineages.values()),
                    held_content_or_scores_in_status=False)
                write(output / f'STATUS_{sequence:06d}.json', status)
                sequence += 1
                if not active and (admitted >= config['max_jobs'] or dispatch_window(
                        config, max(next_dispatch, time.time()))['status'] != 'FULL_JOB_WINDOW_AVAILABLE'):
                    break
                time.sleep(min(config['poll_seconds'], max(0, config['hard_end_unix'] - time.time())))
        except BaseException as error:
            final_error = type(error).__name__
        finally:
            for job in active.values():
                try:
                    remaining = max(1, read(job['job']['plan_path'])['hard_end_unix'] + 10 - time.time())
                    code = job['process'].wait(timeout=remaining)
                    failed += not finish(config, job, code)
                except Exception as error:
                    final_error = type(error).__name__
            _, completed, _ = ledger_state(config, seeds, lineages)
            terminal = dict(status='FAILED' if final_error else 'BOUNDED_SCHEDULER_FINISHED',
                error_type=final_error, config_sha256=sha(config_path), observed_unix=time.time(),
                completed_checkpoint_count=len(completed), future_completed_checkpoints=len(completed - seeds),
                admitted_future_checkpoints=admitted, failed_attempts=failed, next_dispatch_unix=None)
            write(output / ('FAILED.json' if final_error else 'COMPLETE.json'), terminal)
    return terminal


def status_projection(bundle, config_sha256):
    require(set(bundle) == {'receipt', 'receipt_sha256', 'receipt_name'}, 'status_bundle_fields')
    require(sidecar.runner._hash(bundle['receipt_sha256']) and isinstance(bundle['receipt_name'], str)
        and re.fullmatch(r'(STATUS_[0-9]{6}|COMPLETE|FAILED)\.json', bundle['receipt_name']), 'status_receipt_identity')
    status = bundle['receipt']
    require(status['config_sha256'] == config_sha256
        and status['status'] in ('BOUNDED_POLLING', 'BOUNDED_SCHEDULER_FINISHED', 'FAILED'), 'status_config_identity')
    for name in ('completed_checkpoint_count', 'future_completed_checkpoints'):
        require(type(status[name]) is int and status[name] >= 0, 'status_count_integer')
    require(status['completed_checkpoint_count'] == 6 + status['future_completed_checkpoints'], 'status_seed_count')
    next_dispatch = status.get('next_dispatch_unix')
    require(next_dispatch is None or (finite_number(next_dispatch) and next_dispatch > 0), 'status_dispatch_time')
    active = status.get('active_physical', [])
    require(isinstance(active, list) and all(type(index) is int for index in active)
        and active in ([], [0], [1], [0, 1]), 'status_only_benchmark_devices')
    require(finite_number(status['observed_unix']), 'status_observed_time')
    return dict(status=status['status'], completed_checkpoint_count=status['completed_checkpoint_count'],
        future_completed_checkpoints=status['future_completed_checkpoints'], next_dispatch_unix=next_dispatch,
        active_physical=active, receipt_sha256=bundle['receipt_sha256'], receipt_name=bundle['receipt_name'])


def fetch_status(wrapper, remote_output, config_sha256):
    require(re.fullmatch(r'/localhome/local-rohing/orch_r130_checkpoint_benchmark_20260916_attempt1/'
        r'scheduler_run_[a-z0-9_]+', remote_output), 'only_bound_remote_status_directory')
    script = ('from pathlib import Path; import json,hashlib; root=Path(' + repr(remote_output) + '); '
        'paths=sorted(root.glob("STATUS_*.json")); '
        'terminal=[root/name for name in ("COMPLETE.json","FAILED.json") if (root/name).is_file()]; '
        'path=(terminal or paths)[-1]; raw=path.read_bytes(); '
        'print(json.dumps(dict(receipt=json.loads(raw),receipt_sha256=hashlib.sha256(raw).hexdigest(),receipt_name=path.name)))')
    result = subprocess.run(['bash', str(wrapper), 'python3 -c ' + shlex.quote(script)],
        capture_output=True, text=True, check=True, timeout=30)
    return status_projection(sidecar.runner.parse_json(result.stdout), config_sha256)


def append_notebook_status(path, status):
    dispatch = datetime.fromtimestamp(status['next_dispatch_unix'], timezone.utc).isoformat() \
        if status['next_dispatch_unix'] is not None else 'none (bounded scheduler terminal/no remaining dispatch)'
    observed = datetime.now(timezone.utc).isoformat()
    entry = (f'{observed} [Builder] R137 node2 bounded checkpoint scheduler status: '
        f'{status["status"]}; completed checkpoints={status["completed_checkpoint_count"]} '
        f'(future completed={status["future_completed_checkpoints"]}, sealed baseline=6); '
        f'next dispatch={dispatch}; active benchmark physical={status["active_physical"]}; '
        f'status receipt SHA256 {status["receipt_sha256"]}. '
        'Status/counts only; Main remains blind; held results stay sealed; generators2-7 untouched.')
    for _ in range(3):
        ending = Path(path).read_text().splitlines()[-3:]
        patch = '\n'.join(['*** Begin Patch', '*** Update File: ' + str(path), '@@',
            *(' ' + line for line in ending), '+', '+' + entry, '*** End of File', '*** End Patch', ''])
        result = subprocess.run(['apply_patch'], input=patch, text=True, capture_output=True)
        if result.returncode == 0:
            return hashlib.sha256(entry.encode()).hexdigest()
    raise RuntimeError('concurrent_notebook_append_failed')


def relay(config_path):
    require(os.environ.get('R130_SCHEDULER_RELAY_SHA256') == sha(config_path), 'relay_admission_binding')
    config = read(config_path)
    require(config['schema'] == RELAY_SCHEMA and config['scheduler_source_sha256'] == sha(__file__), 'relay_source_binding')
    repository = Path(__file__).resolve().parents[1]
    wrapper = Path(config['wrapper_path']).resolve(strict=True)
    notebook = Path(config['notebook_path']).resolve(strict=True)
    require(wrapper == repository / 'gpu/ovx_ssh.sh' and sha(wrapper) == config['wrapper_sha256'], 'only_ovx_wrapper')
    require(notebook == repository / 'research_loop/COORDINATION.md', 'only_coordination_append')
    require(finite_number(config['hard_end_unix']) and time.time() < config['hard_end_unix']
        <= time.time() + 7260 and config['poll_seconds'] == 60, 'bounded_status_relay')
    output = Path(config['output_root'])
    require(output.is_absolute() and output.parent == Path('/tmp/r130-deploy-20260916')
        and re.fullmatch('scheduler_relay_[a-z0-9_]+', output.name) and not output.is_symlink(), 'relay_output_scope')
    output.mkdir(mode=0o700)
    write(output / 'STARTED.json', dict(status='BOUNDED_STATUS_RELAY_RUNNING',
        config_sha256=sha(config_path), identity=sidecar.identity(os.getpid()), hard_end_unix=config['hard_end_unix']))
    previous = None
    failures = 0
    sequence = 0
    while time.time() < config['hard_end_unix']:
        try:
            require(os.environ.get('R130_SCHEDULER_RELAY_SHA256') == sha(config_path)
                and sha(__file__) == config['scheduler_source_sha256']
                and sha(wrapper) == config['wrapper_sha256'], 'relay_immutable_inputs')
            status = fetch_status(wrapper, config['remote_output_root'], config['remote_config_sha256'])
            state = {key: value for key, value in status.items() if key not in ('receipt_sha256', 'receipt_name')}
            if state != previous:
                entry_sha256 = append_notebook_status(notebook, status)
                write(output / f'NOTE_{sequence:04d}.json', dict(status=status, entry_sha256=entry_sha256))
                sequence += 1
                previous = state
            failures = 0
            if status['status'] != 'BOUNDED_POLLING':
                break
        except Exception as error:
            failures += 1
            write(output / f'ERROR_{time.time_ns()}.json', dict(error_type=type(error).__name__, consecutive_failures=failures))
            if failures >= 3:
                write(output / 'FAILED.json', dict(status='RELAY_FAILED', notebook_updates=sequence))
                return dict(status='FAILED')
        time.sleep(min(config['poll_seconds'], max(0, config['hard_end_unix'] - time.time())))
    write(output / 'COMPLETE.json', dict(status='BOUNDED_RELAY_FINISHED', notebook_updates=sequence))
    return dict(status='BOUNDED_RELAY_FINISHED')


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('preflight', 'run', 'relay'))
    parser.add_argument('--config', required=True, type=Path)
    options = parser.parse_args(argv)
    try:
        result = validate(options.config) if options.action == 'preflight' else (
            relay(options.config) if options.action == 'relay' else run(options.config))
        status = 'PASS' if options.action == 'preflight' else result['status']
        print(json.dumps(dict(status=status, config_sha256=sha(options.config))))
        return int(status == 'FAILED')
    except BaseException as error:
        print(json.dumps(dict(status='FAILED', error_type=type(error).__name__)))
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
