"""Append-only, quota-preserving continuation of the frozen R146 benchmark."""

import argparse
from contextlib import ExitStack, contextmanager
import fcntl
import hashlib
import json
import math
import os
from pathlib import Path
import shlex
import subprocess
import sys
import time

from gpu import orch_r146_successor_phase as previous


scheduler = previous.scheduler
ROOT = previous.ROOT
SCHEMA = 'R158_BENCHMARK_CONTINUATION_V1'
COPY_SCHEMA = 'R158_BENCHMARK_COPY_CONTINUATION_V1'
PREVIOUS_SHA = '02f6fa655ef77f920c700ca973112535424b8ef36ca68d804e99e1b3eb8dab4b'
ORIGINAL_COPY_SHA = '815e0850a616203603271b0aea03961b166eda19b2d267c8f7e3cbd6218cac2d'
PREVIOUS_COPY_SHA = '4e3f13e6dc8a6eeee386484e26d5f3b4b97cff5ed81077b8ab00dca4fae679fb'
OWN_FILES = {'gpu/orch_r158_benchmark_continuation.py', 'tests/test_orch_r158_benchmark_continuation.py'}
ORIGINALS = ('legacy', 'pilot', 'kernel')
MAX_ARCHIVE = 512 * 1024 * 1024
sha, read, write, require = scheduler.sha, scheduler.read, scheduler.write, scheduler.require


def copier_backend():
    from gpu import orch_r130_checkpoint_copier
    return orch_r130_checkpoint_copier


@contextmanager
def scheduler_environment(checksum):
    name = 'R130_SCHEDULER_ADMISSION_SHA256'
    old = os.environ.get(name)
    os.environ[name] = checksum
    try:
        yield
    finally:
        if old is None:
            os.environ.pop(name, None)
        else:
            os.environ[name] = old


def bound(document, name):
    path = Path(document[name + '_path'])
    require(path.is_absolute() and '..' not in path.parts
            and not any(parent.is_symlink() for parent in (path, *path.parents)), 'regular_bound_path')
    require(sha(path) == document[name + '_sha256'], name + '_hash_binding')
    return read(path)


def snapshot_delta(old, new):
    require(set(new) - set(old) == OWN_FILES
            and all(new.get(name) == checksum for name, checksum in old.items()), 'only_two_append_only_files')


def scheduler_delta(old, new):
    allowed = {'source_root', 'sources', 'cpu_gate_path', 'cpu_gate_sha256', 'created_unix',
               'hard_end_unix', 'first_dispatch_unix', 'max_jobs', 'output_root'}
    require(set(old) == set(new) and all(new[name] == value for name, value in old.items()
                                       if name not in allowed), 'wall_only_scheduler_delta')


def phase_header(path):
    require(os.environ.get('R158_ADMISSION_SHA256') == sha(path), 'R158_admission_binding')
    phase = read(path)
    require(phase['schema'] == SCHEMA and phase['helper_sha256'] == sha(__file__), 'R158_source_binding')
    require(Path(phase['operator_root']) == ROOT and Path(path).parent == ROOT, 'original_operator_root')
    require(Path(phase['output_root']).parent == ROOT
            and Path(phase['output_root']).name.startswith('successor_phase_r158_'), 'new_phase_output')
    require(phase['total_call_cap'] == 4800 and phase['max_phase_jobs'] == 58, 'unchanged_both_caps')
    return phase


def historical_configs(phase):
    old = bound(phase, 'predecessor')
    require(phase['predecessor_sha256'] == PREVIOUS_SHA, 'exact_R146_predecessor')
    earlier = bound(old, 'predecessor_phase')
    configs = {}
    for output in (Path(old['output_root']), Path(earlier['output_root'])):
        for path in output.glob('SEGMENT_*.CONFIG.json'):
            configs[str(path)] = sha(path)
    require(configs == phase['charged_configs'], 'all_predecessor_configs_counted')
    return configs


def quota(phase, config, seeds, lineages):
    configs = dict(phase['charged_configs'])
    configs[phase['scheduler_path']] = phase['scheduler_sha256']
    own_count = charged = 0
    for path in Path(config['ledger_root']).glob('*.RESERVED.json'):
        claim = read(path)
        require(path.name == scheduler.key_for(claim['lineage_id'], claim['commit_sha256']) + '.RESERVED.json',
                'reservation_identity')
        config_path = claim['config_path']
        if config_path in configs:
            require(claim['config_sha256'] == configs[config_path], 'charged_config_hash')
            charged += 1
            own_count += config_path == phase['scheduler_path']
        else:
            require(config_path == str(ROOT / 'SCHEDULER_CONFIG_V1.json')
                    and claim['config_sha256'] == previous.ORIGINAL_CONFIG_SHA,
                    'unknown_reservation_config_refused')
    taken, completed, _ = scheduler.ledger_state(config, seeds, lineages)
    require(charged <= 58 and len(taken) <= 80, 'caps_not_exceeded')
    remaining = previous.enrollment.remaining_budget(4800, taken, charged, 58)
    require(config['max_jobs'] <= remaining + own_count, 'own_admissions_plus_residual_cap')
    return dict(remaining_jobs=remaining, own_admitted=own_count, phase_charged=charged,
                reserved_checkpoint_count=len(taken), completed_checkpoint_count=len(completed),
                future_completed_checkpoints=len(completed - seeds), remaining_total_call_budget=4800 - 60 * len(taken))


def predecessor_clear(phase):
    old = bound(phase, 'predecessor')
    output = Path(old['output_root'])
    require(not (output / 'FAILED.json').exists(), 'R146_not_failed')
    complete = read(output / 'COMPLETE.json')
    require(complete['phase_sha256'] == PREVIOUS_SHA and complete['status'] == 'BOUNDED_PHASE_FINISHED',
            'R146_completed_normally')
    require(scheduler.sidecar.gone(read(output / 'STARTED.json')['identity']), 'previous_controller_still_alive')
    for config_path in phase['charged_configs']:
        directory = Path(read(config_path)['output_root'])
        for launch in [directory / 'STARTED.json', *directory.glob('dispatch_*/**/LAUNCH.json')]:
            if launch.exists():
                require(scheduler.sidecar.gone(read(launch)['identity']), 'previous_job_or_scheduler_still_alive')


def validate(path):
    phase = phase_header(path)
    old = bound(phase, 'predecessor')
    historical_configs(phase)
    template = bound(phase, 'template')
    require(phase['charged_configs'].get(phase['template_path']) == phase['template_sha256'],
            'template_is_historical_segment')
    config = bound(phase, 'scheduler')
    scheduler_delta(template, config)
    snapshot_delta(old['sources'], config['sources'])
    require(Path(config['source_root']) == Path(__file__).resolve().parents[1]
            and config['sources']['gpu/orch_r158_benchmark_continuation.py'] == sha(__file__), 'executing_new_source')
    require(config['hard_end_unix'] == phase['hard_end_unix'] > old['hard_end_unix']
            and config['created_unix'] >= old['hard_end_unix'], 'nonoverlapping_wall_continuation')
    require(sha(phase['builder_path']) == phase['builder_sha256']
            and Path(phase['builder_path']).read_text().startswith('## [Builder] 2026-09-17 R158'), 'fresh_builder_gate')
    gate = bound(config, 'cpu_gate')
    require(gate['helper_sha256'] == sha(__file__)
            and gate['test_sha256'] == sha(Path(config['source_root']) / 'tests/test_orch_r158_benchmark_continuation.py'),
            'continuation_CPU_source_gate')
    for preserved_path, checksum in phase['preserved'].items():
        require(sha(preserved_path) == checksum, 'historical_artifact_preserved')
    custody = bound(phase, 'custody')
    require(set(custody['sources']) == set(ORIGINALS), 'same_three_source_lineages')
    for lineage, source in custody['sources'].items():
        require(source['read_end_unix'] > phase['hard_end_unix']
                and source['lineage_id'] == lineage, 'source_read_ceiling')
    with scheduler_environment(phase['scheduler_sha256']):
        checked, lineages, seeds = scheduler.validate(Path(phase['scheduler_path']))
    require(checked == config, 'scheduler_config_unchanged')
    remaining = quota(phase, config, seeds, lineages)
    return phase, config, lineages, seeds, remaining


def status(phase):
    return previous.phase_status(phase)


def node(path):
    phase, config, lineages, seeds, remaining = validate(path)
    require(remaining['remaining_jobs'] > 0, 'remaining_phase_quota')
    require(scheduler.dispatch_window(config, max(time.time(), config['first_dispatch_unix']))['status']
            == 'FULL_JOB_WINDOW_AVAILABLE', 'full_first_dispatch_window')
    output = Path(phase['output_root'])
    with (ROOT / 'successor_phase_owner.lock').open('a') as owner:
        fcntl.flock(owner, fcntl.LOCK_EX | fcntl.LOCK_NB)
        predecessor_clear(phase)
        with ExitStack() as locks:
            for physical in (0, 1):
                lock = locks.enter_context((ROOT / f'physical{physical}.lock').open('a'))
                fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        output.mkdir(mode=0o700, exist_ok=False)
        write(output / 'STARTED.json', dict(status='R158_CONTINUATION_STARTED', phase_sha256=sha(path),
              identity=scheduler.sidecar.identity(os.getpid()), observed_unix=time.time(), **remaining))
        environment = dict(os.environ, CUDA_VISIBLE_DEVICES='', PYTHONDONTWRITEBYTECODE='1',
                           PYTHONPATH=config['source_root'], R130_SCHEDULER_ADMISSION_SHA256=phase['scheduler_sha256'])
        active = None
        try:
            with (output / 'scheduler.private.log').open('x') as log:
                active = subprocess.Popen([config['python'], '-B', '-m', 'gpu.orch_r146_checkpoint_scheduler',
                    'run', '--config', phase['scheduler_path']], cwd=config['source_root'], env=environment,
                    stdin=subprocess.DEVNULL, stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
            write(output / 'SCHEDULER_LAUNCH.json', dict(identity=scheduler.sidecar.identity(active.pid),
                  config_path=phase['scheduler_path'], config_sha256=phase['scheduler_sha256']))
            sequence = 0
            while active.poll() is None:
                if time.time() >= phase['hard_end_unix']:
                    active.wait(timeout=90)
                    break
                _, _, _, _, remaining = validate(path)
                files = sorted(Path(config['output_root']).glob('STATUS_*.json'))
                current = read(files[-1]) if files else {}
                receipt = dict(status='SEGMENT_RUNNING', phase_sha256=sha(path), observed_unix=time.time(),
                    hard_end_unix=phase['hard_end_unix'], active_config_path=phase['scheduler_path'],
                    active_config_sha256=phase['scheduler_sha256'], registered_lineages=len(lineages),
                    active_physical=current.get('active_physical', []),
                    pending_unique_checkpoints=current.get('pending_unique_checkpoints'),
                    next_dispatch_unix=current.get('next_dispatch_unix', config['first_dispatch_unix']), **remaining)
                write(output / f'STATUS_{sequence:06d}.json', receipt)
                sequence += 1
                time.sleep(min(30, max(0, phase['hard_end_unix'] - time.time())))
            terminal_path = Path(config['output_root']) / 'COMPLETE.json'
            require(active.returncode == 0 and terminal_path.is_file(), 'scheduler_failure_no_automatic_replay')
            terminal = read(terminal_path)
            require(terminal['config_sha256'] == phase['scheduler_sha256'], 'scheduler_terminal_binding')
            write(output / 'COMPLETE.json', dict(status='BOUNDED_PHASE_FINISHED', phase_sha256=sha(path),
                observed_unix=time.time(), next_dispatch_unix=None, failed_attempts=terminal['failed_attempts'],
                **quota(phase, config, seeds, lineages)))
        except BaseException as error:
            if active is not None and active.poll() is None:
                active.wait(timeout=max(90, phase['hard_end_unix'] - time.time() + 90))
            write(output / 'FAILED.json', dict(status='FAILED', phase_sha256=sha(path),
                  error_type=type(error).__name__, automatic_retry=False, observed_unix=time.time()))
            raise


def source_payload(phase, lineages, payload):
    require(set(payload) in ({'lineage_id', 'initial_commit_sha256', 'commit_sha256', 'adapter_state_sha256'},
                            {'lineage_id', 'initial_commit_sha256', 'commit_sha256', 'adapter_state_sha256', 'archive_sha256'}),
            'exact_copy_payload')
    lineage = payload['lineage_id']
    require(lineage in ORIGINALS and lineage in lineages, 'only_original_source_lineages')
    for name, value in payload.items():
        if name.endswith('sha256'):
            require(isinstance(value, str) and len(value) == 64 and all(char in '0123456789abcdef' for char in value),
                    'copy_digest')
    custody = bound(phase, 'custody')['sources'][lineage]
    require(payload['initial_commit_sha256'] == lineages[lineage]['initial_commit_sha256']
            == custody['initial_commit_sha256'], 'same_original_baseline')
    return custody


def stage(path, action, payload):
    phase, config, lineages, seeds, _ = validate(path)
    custody = source_payload(phase, lineages, payload)
    current = status(phase)
    require(current['status'] == 'SEGMENT_RUNNING'
            and current['active_config_sha256'] == phase['scheduler_sha256'], 'active_phase_binding')
    output = Path(config['output_root'])
    require(not (output / 'COMPLETE.json').exists() and not (output / 'FAILED.json').exists()
            and not scheduler.sidecar.gone(read(output / 'STARTED.json')['identity']), 'active_scheduler_identity')
    require(time.time() + 180 < config['hard_end_unix'], 'copy_before_wall')
    lineage = payload['lineage_id']
    key = scheduler.key_for(lineage, payload['commit_sha256'])
    taken, _, _ = scheduler.ledger_state(config, seeds, lineages)
    if key in taken:
        return dict(status='ALREADY_RESERVED_NO_REPLAY', lineage_id=lineage, commit_sha256=payload['commit_sha256'])
    for ready in (Path(config['inbox_root']) / 'ready').glob('*.json'):
        item = read(ready)
        if item['lineage_id'] == lineage and item['commit_sha256'] == payload['commit_sha256']:
            scheduler.candidate(config, lineages, ready)
            return dict(status='ALREADY_STAGED', lineage_id=lineage, commit_sha256=payload['commit_sha256'])
    if action == 'known':
        return dict(status='NEEDS_COPY')
    require(action == 'stage' and 'archive_sha256' in payload, 'stage_requires_archive')
    raw = sys.stdin.buffer.read(MAX_ARCHIVE + 1)
    require(len(raw) <= MAX_ARCHIVE and hashlib.sha256(raw).hexdigest() == payload['archive_sha256'], 'archive_hash')
    archive = ROOT / 'incoming' / ('r158_' + lineage + '_' + payload['commit_sha256'] + '.tar')
    if archive.exists():
        require(sha(archive) == payload['archive_sha256'], 'preserved_archive_identity')
    else:
        write(archive, raw)
    destination = Path(config['inbox_root']) / 'copies' / (lineage + '_' + payload['commit_sha256'])
    if not destination.exists():
        temporary = destination.parent / ('.r158_' + key + '_' + str(os.getpid()))
        scheduler.sidecar.extract_regular_archive(archive, temporary, payload['archive_sha256'])
        scheduler.sidecar.checkpoint_manifest(temporary, payload['commit_sha256'])
        proof = read(temporary / 'SOURCE_COPY_RECEIPT.json')
        require(proof['lineage_id'] == lineage and proof['checkpoint_root'] == custody['checkpoint_root']
                and Path(proof['original_commit_path']).parent.parent == Path(custody['checkpoint_root'])
                and proof['original_commit_sha256'] == payload['commit_sha256']
                and proof['initial_commit_sha256'] == payload['initial_commit_sha256']
                and proof['before_after_verified'] is True and proof['source_writes'] is False
                and proof['optimizer_or_TRAIN_opened'] is False, 'readonly_original_source_proof')
        require({item.name for item in temporary.iterdir()}
                == {'COMMIT.json', 'adapter', 'manifest.json', 'SOURCE_COPY_RECEIPT.json'}, 'adapter_only_payload')
        verified = scheduler.sidecar.runner.verify_checkpoint(read(temporary / 'manifest.json'), temporary)
        require(verified['adapter_state_sha256'] == payload['adapter_state_sha256'], 'source_adapter_state')
        os.rename(temporary, destination)
    checkpoint = scheduler.sidecar.runner.verify_checkpoint(read(destination / 'manifest.json'), destination)
    require(checkpoint['commit_sha256'] == payload['commit_sha256']
            and checkpoint['adapter_state_sha256'] == payload['adapter_state_sha256'], 'copied_adapter_identity')
    published = previous.publish_ready(config, lineages, dict(schema=scheduler.READY_SCHEMA, lineage_id=lineage,
        manifest_path=str(destination / 'manifest.json'), manifest_sha256=sha(destination / 'manifest.json'),
        commit_sha256=payload['commit_sha256']))
    return dict(status='COPIED_AND_READY_VERIFIED', lineage_id=lineage, commit_sha256=payload['commit_sha256'],
                ready_sha256=published['ready_sha256'], copy_receipt_sha256=sha(destination / 'SOURCE_COPY_RECEIPT.json'))


def copy_validate(path):
    copier = copier_backend()
    require(os.environ.get('R158_COPY_ADMISSION_SHA256') == sha(path), 'copy_admission_binding')
    config = read(path)
    require(config['schema'] == COPY_SCHEMA and config['helper_sha256'] == sha(__file__), 'copy_helper_binding')
    modules = [sys.modules[__name__], scheduler, previous, previous.enrollment,
               copier, copier.scheduler, scheduler.sidecar, scheduler.sidecar.runner]
    require(set(config['local_dependencies']) == {str(Path(module.__file__).resolve()) for module in modules},
            'complete_local_copy_closure')
    for name, checksum in config['local_dependencies'].items():
        require(sha(name) == checksum, 'local_copy_dependency_binding')
    predecessor = bound(config, 'predecessor')
    require(config['predecessor_sha256'] == PREVIOUS_COPY_SHA, 'exact_previous_copier')
    old_output = Path(predecessor['output_root'])
    terminal = bound(config, 'predecessor_complete')
    require(Path(config['predecessor_complete_path']) == old_output / 'COMPLETE.json'
            and terminal['config_sha256'] == PREVIOUS_COPY_SHA
            and terminal['status'] == 'BOUNDED_PHASE_COPY_FINISHED'
            and not (old_output / 'FAILED.json').exists(), 'copier_normal_terminal')
    require(scheduler.sidecar.gone(read(old_output / 'STARTED.json')['identity']), 'previous_copier_alive')
    original = bound(config, 'original_copy')
    require(config['original_copy_sha256'] == ORIGINAL_COPY_SHA, 'original_copy_pin')
    phase = bound(config, 'phase_local')
    require(phase['schema'] == SCHEMA and config['phase_local_sha256'] == config['remote_phase_sha256']
            and phase['helper_sha256'] == sha(__file__), 'same_local_remote_new_helper')
    require(Path(config['remote_phase_path']).parent == ROOT
            and Path(config['remote_source_root']).parent == ROOT
            and Path(config['remote_source_root']).name.startswith('source_r158_'), 'bound_remote_paths')
    gate = bound(config, 'cpu_gate')
    require(gate['status'] == 'PASS' and gate['helper_sha256'] == sha(__file__)
            and gate['test_log_sha256'] == sha(gate['test_log_path']), 'copy_CPU_gate')
    require(config['destination_wrapper'] == original['destination_wrapper']
            and sha(config['destination_wrapper']) == original['destination_wrapper_sha256'], 'only_node2_destination')
    custody = bound(config, 'custody')
    require(config['custody_sha256'] == phase['custody_sha256'], 'same_source_custody')
    require([source['lineage_id'] for source in original['sources']] == list(ORIGINALS), 'original_three_roots_only')
    for source in original['sources']:
        lineage = source['lineage_id']
        proof = custody['sources'][lineage]
        require(sha(source['wrapper_path']) == source['wrapper_sha256'] == proof['wrapper_sha256']
                and all(source[name] == proof[name] for name in
                        ('checkpoint_root', 'initial_commit_path', 'initial_commit_sha256', 'wrapper_path'))
                and proof['read_end_unix'] > phase['hard_end_unix'], 'same_root_and_current_read_authority')
    require(time.time() < config['hard_end_unix'] == phase['hard_end_unix']
            and config['first_dispatch_unix'] % 1800 == 0
            and config['first_copy_unix'] == config['first_dispatch_unix'] - 180, 'bounded_copy_clock')
    return config, phase, original


def remote(config, phase, action, payload=None, stream=None):
    command = ['env', 'CUDA_VISIBLE_DEVICES=', 'PYTHONDONTWRITEBYTECODE=1',
        'PYTHONPATH=' + config['remote_source_root'], 'R158_ADMISSION_SHA256=' + config['remote_phase_sha256'],
        config['remote_python'], '-B', '-m', 'gpu.orch_r158_benchmark_continuation', action,
        '--config', config['remote_phase_path']]
    if payload is not None:
        command += ['--payload', json.dumps(payload, sort_keys=True, allow_nan=False)]
    result = subprocess.run(['bash', config['destination_wrapper'], shlex.join(command)],
        stdin=stream if stream is not None else subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        check=True, timeout=min(120, max(1, phase['hard_end_unix'] - time.time())))
    require(len(result.stdout) <= 1024 * 1024, 'bounded_metadata_response')
    return scheduler.sidecar.runner.parse_json(result.stdout)


def copy_one(path, config, phase, source, directory):
    copier = copier_backend()
    copy_validate(path)
    params = {name: source[name] for name in ('lineage_id', 'checkpoint_root', 'initial_commit_path',
        'initial_commit_sha256', 'native_schema', 'base_sha256')}
    result = subprocess.run(['bash', source['wrapper_path'], copier.source_command(params)],
        stdin=subprocess.DEVNULL, capture_output=True, check=True, timeout=60)
    require(len(result.stdout) <= 4 * 1024 * 1024, 'bounded_source_metadata')
    selection = scheduler.sidecar.runner.parse_json(result.stdout)
    selected = selection['selected']
    require(selection['status'] == 'COMMITTED_CHECKPOINT_SELECTED'
            and selected['lineage_id'] == source['lineage_id']
            and Path(selected['commit_path']).parent.parent == Path(source['checkpoint_root']), 'same_selected_root')
    payload = dict(lineage_id=source['lineage_id'], initial_commit_sha256=source['initial_commit_sha256'],
                   commit_sha256=selected['commit_sha256'], adapter_state_sha256=selected['adapter_state_sha256'])
    result = remote(config, phase, 'known', payload)
    if result['status'] in {'ALREADY_STAGED', 'ALREADY_RESERVED_NO_REPLAY'}:
        require(result['lineage_id'] == payload['lineage_id'] and result['commit_sha256'] == payload['commit_sha256'],
                'known_identity')
        return result
    require(result['status'] == 'NEEDS_COPY', 'known_before_transfer')
    archive = directory / (source['lineage_id'] + '.tar')
    copy_validate(path)
    with archive.open('xb') as stream:
        subprocess.run(['bash', source['wrapper_path'], copier.source_command(params, selected)],
            stdin=subprocess.DEVNULL, stdout=stream, stderr=subprocess.PIPE, check=True, timeout=120)
    require(0 < archive.stat().st_size <= MAX_ARCHIVE, 'bounded_archive')
    payload['archive_sha256'] = sha(archive)
    copy_validate(path)
    with archive.open('rb') as stream:
        result = remote(config, phase, 'stage', payload, stream)
    require(result['status'] in {'COPIED_AND_READY_VERIFIED', 'ALREADY_STAGED', 'ALREADY_RESERVED_NO_REPLAY'}
            and result['lineage_id'] == payload['lineage_id'] and result['commit_sha256'] == payload['commit_sha256'],
            'ready_identity')
    return result


def copy_loop(path):
    config, phase, original = copy_validate(path)
    output = Path(config['output_root'])
    with (Path(config['predecessor_path']).parent / 'r158_copier_owner.lock').open('a') as owner:
        fcntl.flock(owner, fcntl.LOCK_EX | fcntl.LOCK_NB)
        output.mkdir(mode=0o700, exist_ok=False)
        write(output / 'STARTED.json', dict(status='R158_COPY_STARTED', config_sha256=sha(path),
              identity=scheduler.sidecar.identity(os.getpid()), observed_unix=time.time()))
        following = config['first_copy_unix']
        cycle = 0
        try:
            while following < config['hard_end_unix']:
                config, phase, original = copy_validate(path)
                if scheduler.dispatch_window(dict(hard_end_unix=config['hard_end_unix'], job_max_seconds=3600),
                        following + 180)['status'] != 'FULL_JOB_WINDOW_AVAILABLE':
                    break
                if time.time() < following:
                    time.sleep(min(30, following - time.time()))
                    continue
                if time.time() >= following + 180:
                    following += 1800
                    continue
                current = remote(config, phase, 'status')
                require(current['phase_sha256'] == config['remote_phase_sha256'], 'remote_phase_identity')
                if current['status'] == 'BOUNDED_PHASE_FINISHED':
                    break
                require(current['status'] == 'SEGMENT_RUNNING', 'active_remote_phase')
                directory = output / f'cycle_{cycle:02d}'
                directory.mkdir(mode=0o700)
                receipts = []
                for source in original['sources']:
                    try:
                        receipt = copy_one(path, config, phase, source, directory)
                    except Exception as error:
                        receipt = dict(status='COPY_FAILED_NO_READY_ASSUMED', lineage_id=source['lineage_id'],
                                       error_type=type(error).__name__)
                    write(directory / (source['lineage_id'] + '.STATUS.json'), receipt)
                    receipts.append(receipt)
                write(directory / 'COMPLETE.json', dict(status='COPY_CYCLE_FINISHED', copies=receipts,
                      observed_unix=time.time()))
                following += 1800
                cycle += 1
            write(output / 'COMPLETE.json', dict(status='R158_COPY_FINISHED', config_sha256=sha(path),
                  cycles=cycle, observed_unix=time.time()))
        except BaseException as error:
            write(output / 'FAILED.json', dict(status='FAILED', config_sha256=sha(path),
                  error_type=type(error).__name__, observed_unix=time.time()))
            raise


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=['validate', 'node', 'status', 'known', 'stage', 'copy-validate', 'copy'])
    parser.add_argument('--config', type=Path, required=True)
    parser.add_argument('--payload')
    args = parser.parse_args()
    try:
        if args.action == 'node':
            node(args.config)
        elif args.action == 'copy':
            copy_loop(args.config)
        elif args.action == 'copy-validate':
            copy_validate(args.config)
            print(json.dumps(dict(status='COPY_VALIDATION_PASS')))
        elif args.action == 'validate':
            phase, _, _, _, remaining = validate(args.config)
            predecessor_clear(phase)
            print(json.dumps(dict(status='VALIDATION_PASS', **remaining)))
        elif args.action == 'status':
            print(json.dumps(status(phase_header(args.config))))
        else:
            print(json.dumps(stage(args.config, args.action, json.loads(args.payload))))
    except Exception as error:
        message = str(error)
        gate = message if message and len(message) < 100 and all(
            char.isascii() and (char.isalnum() or char == '_') for char in message) else 'nonpublic_error_redacted'
        print(json.dumps(dict(status='BLOCKED_NO_PRIVATE_CONTENT', error_type=type(error).__name__, gate=gate)))
        raise SystemExit(1)


if __name__ == '__main__':
    main()
