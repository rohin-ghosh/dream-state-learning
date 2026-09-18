"""Bounded successor controller; frozen runners, shared ledger, no source signals."""

import argparse
from contextlib import ExitStack
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

from gpu import orch_r130_checkpoint_scheduler as scheduler


ROOT = Path('/localhome/local-rohing/orch_r130_checkpoint_benchmark_20260916_attempt1')
PREDECESSOR_SHA = 'a22dfa29a16ef419de3cb2e2ad2740b673700c4669c9ecbfc76de1238dea0805'
COPY_PREDECESSOR_SHA = '815e0850a616203603271b0aea03961b166eda19b2d267c8f7e3cbd6218cac2d'
WALL = 1789617240.0
SCHEMA = 'R130_BOUNDED_SUCCESSOR_PHASE_V1'
sha, read, write, require = scheduler.sha, scheduler.read, scheduler.write, scheduler.require


def budget(total_cap, taken, admitted, phase_cap):
    require(type(total_cap) is int and total_cap % 60 == 0 and 360 <= total_cap <= 4800, 'total_call_cap')
    return max(0, min(8, total_cap // 60 - len(taken), phase_cap - admitted))


def next_copy(now, wall):
    dispatch = (math.floor((now + 180) / 1800) + 1) * 1800
    return dispatch - 180 if dispatch + 180 < wall else None


def validate(path, *, allow_expired=False):
    require(os.environ.get('R130_PHASE_SHA256') == sha(path), 'phase_environment_binding')
    phase = read(path)
    require(phase['schema'] == SCHEMA and phase['helper_sha256'] == sha(__file__), 'phase_source_binding')
    require(Path(phase['operator_root']) == ROOT and Path(phase['predecessor_path']) == ROOT / 'SCHEDULER_CONFIG_V1.json'
        and sha(phase['predecessor_path']) == PREDECESSOR_SHA, 'original_predecessor_pin')
    old = read(phase['predecessor_path'])
    require(hashlib.sha256(scheduler.socket.gethostname().encode()).hexdigest() == scheduler.sidecar.HOST_SHA256
        and os.environ.get('CUDA_VISIBLE_DEVICES') == '', 'node2_CPU_controller_only')
    require(old['physical_devices'] == [0, 1] and old['gpu_uuids'] == list(scheduler.sidecar.DEVICES.values()),
        'only_reserved_benchmark_devices')
    require(old['source_root'] == phase['source_root']
        and scheduler.sidecar.source_inventory(old['source_root']) == old['sources'], 'unchanged_frozen_source_snapshot')
    for name in ('forks', 'registry', 'lineages', 'reservation', 'service', 'cpu_gate', 'template_plan', 'corpus'):
        require(sha(old[name + '_path']) == old[name + '_sha256'], 'predecessor_' + name + '_binding')
    require(old['registry_sha256'] == scheduler.REGISTRY_SHA256
        and old['corpus_sha256'] == scheduler.sidecar.CORPUS_SHA256, 'fixed_registry_and_corpus')
    lineages = scheduler.enrolled_lineages(read(old['lineages_path']))
    require(set(lineages) == {'legacy', 'pilot', 'kernel'}
        and all(value['cohort'] == 'original' for value in lineages.values()), 'only_registered_three_originals')
    forks = read(old['forks_path'])
    require(phase['hard_end_unix'] == min(WALL, forks['hard_deadline_unix'])
        and forks['hard_deadline_unix'] == old['lease_end_unix'] - 21600, 'actual_lease_and_user_wall')
    require(phase['created_unix'] <= time.time() and (allow_expired or time.time() < phase['hard_end_unix'])
        and phase['created_unix'] < phase['hard_end_unix'] <= phase['created_unix'] + 20 * 3600, 'bounded_phase_wall')
    require(old['hard_end_unix'] + 120 <= phase['start_unix'] < phase['first_dispatch_unix']
        < phase['hard_end_unix'] and phase['first_dispatch_unix'] % 1800 == 0, 'nonoverlapping_phase_start')
    require(phase['poll_seconds'] == 30 and phase['segment_seconds'] == 7200
        and phase['dispatch_seconds'] == 1800 and phase['max_phase_jobs'] == 58, 'bounded_phase_cadence')
    budget(phase['total_call_cap'], set(), 0, phase['max_phase_jobs'])
    require(Path(phase['output_root']).parent == ROOT and Path(phase['output_root']).name == 'successor_phase_v2'
        and not Path(phase['output_root']).is_symlink(), 'phase_output_scope')
    for name in ('builder_entry', 'cpu_gate'):
        require(sha(phase[name + '_path']) == phase[name + '_sha256'], 'phase_' + name + '_binding')
    gate = read(phase['cpu_gate_path'])
    require(gate['status'] == 'PASS' and gate['test_exit_code'] == 0
        and gate['helper_sha256'] == sha(__file__)
        and sha(gate['test_log_path']) == gate['test_log_sha256'], 'phase_CPU_gate')
    require(Path(phase['builder_entry_path']).read_text().startswith('## [Builder] 2026-09-16'), 'phase_builder_gate')
    return phase, old, lineages


def predecessor_clear(old):
    output = Path(old['output_root'])
    terminal = next((output / name for name in ('COMPLETE.json', 'FAILED.json') if (output / name).is_file()), None)
    if terminal is None or not scheduler.sidecar.gone(read(output / 'STARTED.json')['identity']):
        return False
    require(read(terminal)['config_sha256'] == PREDECESSOR_SHA, 'predecessor_terminal_binding')
    for launch in output.glob('dispatch_*/**/LAUNCH.json'):
        require(scheduler.sidecar.gone(read(launch)['identity']), 'predecessor_runner_identity_still_live')
    with ExitStack() as stack:
        for physical in (0, 1):
            lock = stack.enter_context((Path(old['operator_root']) / f'physical{physical}.lock').open('a'))
            try:
                fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError:
                return False
    return True


def segment_config(phase, old, now, remaining, segment):
    end = min(phase['hard_end_unix'], now + 7200)
    first = max(phase['first_dispatch_unix'], (math.floor(now / 1800) + 1) * 1800)
    require(first + 180 < end and 1 <= remaining <= 8, 'segment_remaining_wall_and_budget')
    return dict(old, created_unix=now, hard_end_unix=end, first_dispatch_unix=first,
        max_jobs=remaining, output_root=str(ROOT / f'scheduler_run_phase2_{segment:02d}'),
        builder_entry_path=phase['builder_entry_path'], builder_entry_sha256=phase['builder_entry_sha256'])


def segment_command(old, path):
    return [old['python'], '-B', '-m', 'gpu.orch_r130_checkpoint_scheduler', 'run', '--config', str(path)]


def node(path):
    phase, old, lineages = validate(path)
    output = Path(phase['output_root'])
    output.mkdir(mode=0o700, exist_ok=False)
    seeds = scheduler.seed_completed(old, lineages)
    sequence, admitted = 0, 0
    active, active_path = None, None
    next_start = phase['start_unix']
    handoff = False
    segment = 0
    with (ROOT / 'successor_phase_owner.lock').open('a') as owner:
        fcntl.flock(owner, fcntl.LOCK_EX | fcntl.LOCK_NB)
        write(output / 'STARTED.json', dict(status='SUCCESSOR_ARMED', phase_sha256=sha(path),
            identity=scheduler.sidecar.identity(os.getpid()), hard_end_unix=phase['hard_end_unix']))
        while time.time() < phase['hard_end_unix']:
            validate(path)
            taken, completed, _ = scheduler.ledger_state(old, seeds, lineages)
            remaining = budget(phase['total_call_cap'], taken, admitted, phase['max_phase_jobs'])
            status = 'WAITING_PREDECESSOR' if not handoff else 'WAITING_SEGMENT'
            dispatch = phase['first_dispatch_unix'] if not handoff else None
            physical, pending = [], None
            if not handoff and time.time() >= phase['start_unix']:
                handoff = predecessor_clear(old)
                if handoff:
                    write(output / 'HANDOFF.json', dict(status='PREDECESSOR_TERMINAL_IDENTITIES_GONE_LOCKS_CLEAR',
                        predecessor_config_sha256=PREDECESSOR_SHA, observed_unix=time.time(),
                        historical_reserved_checkpoint_count=len(taken), historical_completed_checkpoint_count=len(completed)))
            if active is not None:
                current = read(active_path)
                statuses = sorted(Path(current['output_root']).glob('STATUS_*.json'))
                if statuses:
                    receipt = read(statuses[-1])
                    physical, pending = receipt['active_physical'], receipt['pending_unique_checkpoints']
                    dispatch = receipt['next_dispatch_unix']
                status = 'SEGMENT_RUNNING'
                code = active.poll()
                if code is not None:
                    terminal = Path(current['output_root']) / 'COMPLETE.json'
                    write(output / f'SEGMENT_{segment:02d}.EXIT.json', dict(exit_code=code, observed_unix=time.time()))
                    require(code == 0 and terminal.exists(), 'segment_failed_no_automatic_replay')
                    final = read(terminal)
                    require(final['config_sha256'] == sha(active_path), 'segment_terminal_binding')
                    admitted += final['admitted_future_checkpoints']
                    active, active_path = None, None
                    segment += 1
                    next_start = current['hard_end_unix'] + 15
            if handoff and active is None and time.time() >= next_start:
                taken, completed, _ = scheduler.ledger_state(old, seeds, lineages)
                remaining = budget(phase['total_call_cap'], taken, admitted, phase['max_phase_jobs'])
                if remaining == 0 or time.time() + 300 >= phase['hard_end_unix']:
                    break
                now = time.time()
                end = min(phase['hard_end_unix'], now + 7200)
                first = max(phase['first_dispatch_unix'], (math.floor(now / 1800) + 1) * 1800)
                if first + 180 >= end:
                    break
                current = segment_config(phase, old, now, remaining, segment)
                active_path = output / f'SEGMENT_{segment:02d}.CONFIG.json'
                write(active_path, current)
                environment = dict(os.environ, R130_SCHEDULER_ADMISSION_SHA256=sha(active_path),
                    CUDA_VISIBLE_DEVICES='', PYTHONPATH=old['source_root'], PYTHONDONTWRITEBYTECODE='1')
                with (output / f'SEGMENT_{segment:02d}.private.log').open('x') as log:
                    active = subprocess.Popen(segment_command(old, active_path), cwd=old['source_root'], env=environment,
                        stdin=subprocess.DEVNULL, stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
                write(output / f'SEGMENT_{segment:02d}.LAUNCH.json', dict(identity=scheduler.sidecar.identity(active.pid),
                    config_path=str(active_path), config_sha256=sha(active_path), observed_unix=time.time()))
                status, dispatch = 'SEGMENT_RUNNING', first
            write(output / f'STATUS_{sequence:06d}.json', dict(status=status, phase_sha256=sha(path),
                completed_checkpoint_count=len(completed), future_completed_checkpoints=len(completed - seeds),
                reserved_checkpoint_count=len(taken), remaining_total_call_budget=max(0, phase['total_call_cap'] - 60 * len(taken)),
                active_physical=physical, pending_unique_checkpoints=pending, next_dispatch_unix=dispatch,
                active_config_path=str(active_path) if active_path else None,
                active_config_sha256=sha(active_path) if active_path else None,
                observed_unix=time.time(), hard_end_unix=phase['hard_end_unix']))
            sequence += 1
            time.sleep(min(phase['poll_seconds'], max(0, phase['hard_end_unix'] - time.time())))
        if active is not None:
            active.wait(timeout=90)
        taken, completed, _ = scheduler.ledger_state(old, seeds, lineages)
        write(output / 'COMPLETE.json', dict(status='BOUNDED_PHASE_FINISHED', phase_sha256=sha(path),
            completed_checkpoint_count=len(completed), future_completed_checkpoints=len(completed - seeds),
            reserved_checkpoint_count=len(taken), next_dispatch_unix=None, observed_unix=time.time()))


def phase_status(phase):
    output = Path(phase['output_root'])
    terminal = [output / name for name in ('COMPLETE.json', 'FAILED.json') if (output / name).is_file()]
    paths = terminal or sorted(output.glob('STATUS_*.json'))
    require(bool(paths), 'phase_status_not_yet_available')
    return read(paths[-1])


def stage(path, action, payload):
    phase, old, lineages = validate(path)
    status = phase_status(phase)
    require(status['status'] == 'SEGMENT_RUNNING' and status['active_config_path'], 'active_successor_segment_required')
    current_path = Path(status['active_config_path'])
    require(sha(current_path) == status['active_config_sha256'], 'active_segment_config_hash')
    current = read(current_path)
    output = Path(current['output_root'])
    require(not (output / 'COMPLETE.json').exists() and not (output / 'FAILED.json').exists()
        and not scheduler.sidecar.gone(read(output / 'STARTED.json')['identity']), 'active_scheduler_identity')
    require(time.time() + 180 < current['hard_end_unix'], 'copy_before_segment_wall')
    lineage = payload['lineage_id']
    require(lineage in lineages and lineages[lineage]['initial_commit_sha256'] == payload['initial_commit_sha256'],
        'same_registered_source_root')
    key = scheduler.key_for(lineage, payload['commit_sha256'])
    seeds = scheduler.seed_completed(old, lineages)
    taken, _, _ = scheduler.ledger_state(old, seeds, lineages)
    for ready in (Path(old['inbox_root']) / 'ready').glob('*.json'):
        item = read(ready)
        if item['lineage_id'] == lineage and item['commit_sha256'] == payload['commit_sha256']:
            scheduler.candidate(old, lineages, ready)
            return dict(status='ALREADY_STAGED', lineage_id=lineage, commit_sha256=payload['commit_sha256'])
    if key in taken:
        return dict(status='ALREADY_RESERVED_NO_REPLAY', lineage_id=lineage, commit_sha256=payload['commit_sha256'])
    if action == 'known':
        return dict(status='NEEDS_COPY')
    require(action == 'stage', 'copy_stage_action')
    raw = sys.stdin.buffer.read(513 * 1024 * 1024)
    require(len(raw) <= 512 * 1024 * 1024 and hashlib.sha256(raw).hexdigest() == payload['archive_sha256'], 'archive_hash')
    archive = ROOT / 'incoming' / ('future_' + lineage + '_' + payload['commit_sha256'] + '.tar')
    if archive.exists():
        require(sha(archive) == payload['archive_sha256'], 'existing_archive_hash')
    else:
        write(archive, raw)
    destination = Path(old['inbox_root']) / 'copies' / (lineage + '_' + payload['commit_sha256'])
    if not destination.exists():
        staging = destination.parent / ('.phase2_' + key + '_' + str(os.getpid()))
        scheduler.sidecar.extract_regular_archive(archive, staging, payload['archive_sha256'])
        scheduler.sidecar.checkpoint_manifest(staging, payload['commit_sha256'])
        proof = read(staging / 'SOURCE_COPY_RECEIPT.json')
        require(proof['original_commit_sha256'] == payload['commit_sha256']
            and proof['initial_commit_sha256'] == payload['initial_commit_sha256']
            and proof['lineage_id'] == lineage and proof['before_after_verified'] is True, 'source_copy_proof')
        require({item.name for item in staging.iterdir()} == {'COMMIT.json', 'adapter', 'manifest.json', 'SOURCE_COPY_RECEIPT.json'},
            'adapter_only_payload')
        checkpoint = scheduler.sidecar.runner.verify_checkpoint(read(staging / 'manifest.json'), staging)
        require(checkpoint['adapter_state_sha256'] == payload['adapter_state_sha256'], 'native_adapter_state_hash')
        os.rename(staging, destination)
    manifest = destination / 'manifest.json'
    checkpoint = scheduler.sidecar.runner.verify_checkpoint(read(manifest), destination)
    require(checkpoint['commit_sha256'] == payload['commit_sha256']
        and checkpoint['adapter_state_sha256'] == payload['adapter_state_sha256'], 'destination_provenance')
    ready = dict(schema=scheduler.READY_SCHEMA, lineage_id=lineage, manifest_path=str(manifest),
        manifest_sha256=sha(manifest), commit_sha256=payload['commit_sha256'])
    raw = (json.dumps(ready, indent=2, sort_keys=True) + '\n').encode()
    ready_path = Path(old['inbox_root']) / 'ready' / (hashlib.sha256(raw).hexdigest() + '.json')
    if not ready_path.exists():
        temporary = Path(old['inbox_root']) / ('.phase2_ready_' + key + '_' + str(os.getpid()))
        write(temporary, raw)
        os.link(temporary, ready_path)
        temporary.unlink()
    scheduler.candidate(old, lineages, ready_path)
    return dict(status='COPIED_AND_READY_VERIFIED', lineage_id=lineage, commit_sha256=payload['commit_sha256'],
        archive_sha256=sha(archive), manifest_sha256=sha(manifest), ready_sha256=sha(ready_path),
        copy_receipt_sha256=sha(destination / 'SOURCE_COPY_RECEIPT.json'))


def remote_command(config, action, payload=None):
    command = ['env', 'CUDA_VISIBLE_DEVICES=', 'PYTHONDONTWRITEBYTECODE=1',
        'R130_PHASE_SHA256=' + config['remote_phase_sha256'], 'PYTHONPATH=' + config['source_root'],
        '/localhome/local-rohing/v2/venv/bin/python', '-B', config['remote_helper_path'],
        action, '--config', config['remote_phase_path']]
    if payload is not None:
        command += ['--payload', json.dumps(payload, sort_keys=True)]
    return shlex.join(command)


def local_validate(path):
    from gpu import orch_r130_checkpoint_copier as copier
    require(os.environ.get('R130_PHASE_COPY_SHA256') == sha(path), 'local_phase_copy_binding')
    config = read(path)
    require(config['helper_sha256'] == sha(__file__) and config['copier_sha256'] == sha(copier.__file__), 'copy_source_pins')
    require(sha(config['predecessor_copier_path']) == config['predecessor_copier_sha256'], 'predecessor_copy_pin')
    old = read(config['predecessor_copier_path'])
    require(config['predecessor_copier_sha256'] == COPY_PREDECESSOR_SHA,
        'original_copy_controller_only')
    require(config['destination_wrapper'] == old['destination_wrapper']
        and sha(config['destination_wrapper']) == old['destination_wrapper_sha256'], 'destination_wrapper_pin')
    repository = Path(copier.__file__).resolve().parents[1]
    require(config['destination_wrapper'] == str(repository / 'gpu/ovx_ssh.sh'), 'only_node2_wrapper')
    require(config['hard_end_unix'] <= WALL and time.time() < config['hard_end_unix']
        and config['first_copy_unix'] == config['first_dispatch_unix'] - 180
        and config['max_cycles'] == 30, 'bounded_copy_phase')
    require(config['remote_phase_path'] == str(ROOT / 'SUCCESSOR_PHASE_V2.json')
        and config['source_root'] == str(ROOT / 'source6_scheduler')
        and config['remote_helper_path'] == str(ROOT / 'successor_tools_v2/gpu/orch_r130_successor_phase.py'),
        'only_bound_successor_destination')
    for source_path, checksum in config['local_dependencies'].items():
        require(sha(source_path) == checksum, 'immutable_local_dependency')
    require(sha(config['source_lease_evidence_path']) == config['source_lease_evidence_sha256'], 'source_lease_evidence_pin')
    evidence = read(config['source_lease_evidence_path'])
    require(all(config['hard_end_unix'] < item['conservative_read_end_unix']
        and sha(item['wrapper_path']) == item['wrapper_sha256'] for item in evidence['sources']), 'copy_within_source_lease_bounds')
    if time.time() >= config['first_copy_unix']:
        require(sha(config['predecessor_launch_path']) == config['predecessor_launch_sha256'], 'predecessor_copy_launch_pin')
        require((Path(old['output_root']) / 'COMPLETE.json').exists()
            and scheduler.sidecar.gone(read(config['predecessor_launch_path'])['identity']), 'no_overlapping_copy_controller')
    require(sha(config['builder_entry_path']) == config['builder_entry_sha256'], 'local_copy_builder_gate')
    require(sha(config['cpu_gate_path']) == config['cpu_gate_sha256'], 'local_copy_CPU_gate_hash')
    gate = read(config['cpu_gate_path'])
    require(gate['status'] == 'PASS' and gate['helper_sha256'] == sha(__file__)
        and sha(gate['test_log_path']) == gate['test_log_sha256'], 'local_copy_CPU_gate')
    require([source['lineage_id'] for source in old['sources']] == ['legacy', 'pilot', 'kernel'], 'only_three_copy_roots')
    for source in old['sources']:
        require(source['wrapper_path'] == str(repository / 'gpu' / copier.WRAPPERS[source['lineage_id']])
            and sha(source['wrapper_path']) == source['wrapper_sha256'], 'source_wrapper_pin')
        require(sha(source['prior_selection_path']) == source['prior_selection_sha256'], 'original_selection_pin')
        original = next(item for item in read(source['prior_selection_path'])['checkpoints']
            if item['label'] == source['lineage_id'] + '_initial')
        require(source['initial_commit_path'] == original['path']
            and source['checkpoint_root'] == str(Path(original['path']).parent.parent)
            and source['initial_commit_sha256'] == original['commit_sha256'], 'same_original_source_root')
    return config, old, copier


def copy_loop(path):
    config, old, copier = local_validate(path)
    output = Path(config['output_root'])
    require(output.parent == Path('/tmp/r130-deploy-20260916') and output.name == 'successor_copy_v2', 'local_copy_output')
    output.mkdir(mode=0o700, exist_ok=False)
    write(output / 'STARTED.json', dict(status='BOUNDED_SUCCESSOR_COPY_ARMED', config_sha256=sha(path),
        identity=scheduler.sidecar.identity(os.getpid()), next_copy_unix=config['first_copy_unix'], hard_end_unix=config['hard_end_unix']))
    following = config['first_copy_unix']
    previous_status = None
    cycles = 0
    while time.time() < config['hard_end_unix']:
        local_validate(path)
        result = subprocess.run(['bash', config['destination_wrapper'], remote_command(config, 'status')],
            capture_output=True, timeout=60)
        if result.returncode == 0:
            status = json.loads(result.stdout)
            projected = {key: status.get(key) for key in ('status', 'completed_checkpoint_count',
                'future_completed_checkpoints', 'active_physical', 'next_dispatch_unix')}
            if projected != previous_status:
                entry = dict(projected, receipt_sha256=scheduler.digest(status))
                notebook = Path(copier.__file__).resolve().parents[1] / 'research_loop/COORDINATION.md'
                scheduler.append_notebook_status(notebook, entry)
                write(output / f'RELAY_{time.time_ns()}.json', entry)
                previous_status = projected
            if status['status'] in ('BOUNDED_PHASE_FINISHED', 'FAILED'):
                break
        if following is not None and time.time() >= following and cycles < config['max_cycles']:
            directory = output / f'cycle_{cycles:02d}'
            directory.mkdir(mode=0o700)
            copies = []
            for source in old['sources']:
                try:
                    local_validate(path)
                    require(time.time() + 300 < config['hard_end_unix'], 'copy_remaining_wall')
                    params = {key: source[key] for key in ('lineage_id', 'checkpoint_root', 'initial_commit_path',
                        'initial_commit_sha256', 'native_schema', 'base_sha256')}
                    result = subprocess.run(['bash', source['wrapper_path'], copier.source_command(params)],
                        capture_output=True, check=True, timeout=60)
                    selected = json.loads(result.stdout)['selected']
                    payload = dict(lineage_id=source['lineage_id'], initial_commit_sha256=source['initial_commit_sha256'],
                        commit_sha256=selected['commit_sha256'], adapter_state_sha256=selected['adapter_state_sha256'])
                    result = subprocess.run(['bash', config['destination_wrapper'], remote_command(config, 'known', payload)],
                        capture_output=True, check=True, timeout=60)
                    receipt = json.loads(result.stdout)
                    if receipt['status'] == 'NEEDS_COPY':
                        archive = directory / (source['lineage_id'] + '.tar')
                        with archive.open('xb') as stream:
                            subprocess.run(['bash', source['wrapper_path'], copier.source_command(params, selected)],
                                stdout=stream, stderr=subprocess.PIPE, check=True, timeout=120)
                        payload['archive_sha256'] = sha(archive)
                        with archive.open('rb') as stream:
                            result = subprocess.run(['bash', config['destination_wrapper'], remote_command(config, 'stage', payload)],
                                stdin=stream, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True, timeout=120)
                        receipt = json.loads(result.stdout)
                    require(receipt['status'] in ('ALREADY_STAGED', 'ALREADY_RESERVED_NO_REPLAY', 'COPIED_AND_READY_VERIFIED'),
                        'copy_status_protocol')
                except Exception as error:
                    receipt = dict(status='COPY_FAILED_NO_READY_ASSUMED', lineage_id=source['lineage_id'], error_type=type(error).__name__)
                copies.append(receipt)
            following = next_copy(time.time(), config['hard_end_unix'])
            write(directory / 'COMPLETE.json', dict(status='COPY_CYCLE_FINISHED', copies=copies,
                next_copy_unix=following, observed_unix=time.time()))
            cycles += 1
        time.sleep(min(60, max(0, config['hard_end_unix'] - time.time())))
    write(output / 'COMPLETE.json', dict(status='BOUNDED_PHASE_COPY_FINISHED', cycles=cycles, observed_unix=time.time()))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=['node', 'copy', 'status', 'known', 'stage', 'validate'])
    parser.add_argument('--config', type=Path, required=True)
    parser.add_argument('--payload')
    args = parser.parse_args()
    try:
        if args.action == 'node':
            node(args.config)
        elif args.action == 'copy':
            copy_loop(args.config)
        elif args.action == 'status':
            phase, _, _ = validate(args.config, allow_expired=True)
            print(json.dumps(phase_status(phase), sort_keys=True))
        elif args.action == 'validate':
            validate(args.config)
            print(json.dumps(dict(status='PASS')))
        else:
            print(json.dumps(stage(args.config, args.action, json.loads(args.payload)), sort_keys=True))
    except Exception as error:
        if args.action == 'node':
            output = Path(read(args.config)['output_root'])
            if output.is_dir() and not (output / 'FAILED.json').exists():
                write(output / 'FAILED.json', dict(status='FAILED', error_type=type(error).__name__,
                    next_dispatch_unix=None, observed_unix=time.time()))
        print(json.dumps(dict(status='FAILED', error_type=type(error).__name__)))
        raise SystemExit(1)


if __name__ == '__main__':
    main()
