"""Prospective local R146 copier and safe status relay; no deployment or retirement.

The config is admitted with R146_PHASE_COPY_SHA256. It binds the completed
SUCCESSOR_COPY_V2.json predecessor and its STARTED/COMPLETE bytes, the original
COPIER_CONFIG_V1.json transitively, the node phase config/helper, local imported
dependencies, lease evidence, and Builder/CPU gates. Only the original copier's
source_command reads the three original roots; R137 copies stay on node2.
Relay receipts contain counters/identities, never held benchmark output.

Integration config fields (all paths absolute): schema, helper_sha256,
copier_sha256, local_dependencies (absolute Python source path -> SHA256),
predecessor_copy_path/sha256, predecessor_started_path/sha256,
predecessor_complete_path/sha256, source_lease_evidence_path/sha256,
builder_entry_path/sha256, cpu_gate_path/sha256, destination_wrapper,
remote_phase_local_path/sha256, remote_phase_path/sha256,
remote_helper_local_path/sha256, remote_helper_path/sha256, source_root,
created_unix, first_copy_unix, first_dispatch_unix, hard_end_unix,
copy_lead_seconds=180, dispatch_seconds=1800, max_cycles=1..30, output_root.
Here path/sha256 means two keys ending in _path and _sha256. The CPU gate
requires status=PASS, test_exit_code=0, helper_sha256, remote_helper_sha256,
test_path/test_sha256 and test_log_path/test_log_sha256. test_path names this
helper's regression test. The remote phase bytes must be copied unchanged to
remote_phase_path by the separate deployment owner; this helper never deploys.
"""

import argparse
import json
import os
from pathlib import Path
import shlex
import subprocess
import time

from gpu import orch_r130_checkpoint_copier as copier


SCHEMA = 'R146_BOUNDED_SUCCESSOR_CHECKPOINT_COPY_V1'
WALL = 1789617240
ROOT = Path(copier.ROOT)
EVIDENCE_ROOT = Path('/data/home/rohing/dream-state-orch/research_notes/analysis')
ORIGINAL_CONFIG_SHA256 = '815e0850a616203603271b0aea03961b166eda19b2d267c8f7e3cbd6218cac2d'
ORIGINAL_COPIER_SHA256 = '842a09f70dbadcb3e8520ee19c0a90755a68fb9aedd8e33c9043d8bf3b1b5898'
ORIGINAL_SCHEDULER_SHA256 = '4d8de2d60f14d604361c5d27bea22a1775e2c9f4d0f6f80958ee6b14da7d7735'
MAX_ARCHIVE_BYTES = 512 * 1024 * 1024
STATES = {'SEGMENT_RUNNING', 'WAITING_SEGMENT', 'BOUNDED_PHASE_FINISHED', 'FAILED'}
KNOWN = {'ALREADY_STAGED', 'ALREADY_RESERVED_NO_REPLAY'}
COUNTS = ('completed_checkpoint_count', 'future_completed_checkpoints',
          'reserved_checkpoint_count', 'remaining_total_call_budget', 'pending_unique_checkpoints',
          'registered_lineages')
scheduler = copier.scheduler
sha, read, write, require = copier.sha, copier.read, copier.write, copier.require


def plain_path(value, root=None):
    path = Path(value)
    require(path.is_absolute() and '..' not in path.parts
            and not any(item.is_symlink() for item in (path, *path.parents)), 'plain_absolute_path')
    if root is not None:
        require(path != Path(root) and path.is_relative_to(root), 'path_inside_bound_root')
    return path


def bound(document, name):
    path = plain_path(document[name + '_path'])
    require(path.is_file() and sha(path) == document[name + '_sha256'], name + '_binding')
    return path


def digest_value(value):
    return isinstance(value, str) and len(value) == 64 and all(character in '0123456789abcdef' for character in value)


def local_validate(path):
    require(os.environ.get('R146_PHASE_COPY_SHA256') == sha(path), 'local_copy_environment_binding')
    config = read(path)
    require(config['schema'] == SCHEMA and config['helper_sha256'] == sha(__file__)
            and config['copier_sha256'] == sha(copier.__file__) == ORIGINAL_COPIER_SHA256
            and sha(scheduler.__file__) == ORIGINAL_SCHEDULER_SHA256, 'immutable_original_helpers')
    required = {str(Path(module.__file__).resolve()) for module in
                (copier, scheduler, scheduler.sidecar, scheduler.sidecar.runner)}
    require(required <= set(config['local_dependencies']), 'complete_local_dependencies')
    for source_path, checksum in config['local_dependencies'].items():
        require(sha(plain_path(source_path)) == checksum, 'local_dependency_binding')
    predecessor_path = bound(config, 'predecessor_copy')
    require(predecessor_path.name == 'SUCCESSOR_COPY_V2.json', 'exact_predecessor_copy')
    predecessor = read(predecessor_path)
    original_path = bound(predecessor, 'predecessor_copier')
    require(original_path.name == 'COPIER_CONFIG_V1.json'
            and predecessor['predecessor_copier_sha256'] == ORIGINAL_CONFIG_SHA256, 'original_config_pin')
    original = read(original_path)
    require(original['schema'] == copier.SCHEMA
            and original['copier_sha256'] == predecessor['copier_sha256'] == ORIGINAL_COPIER_SHA256,
            'original_copy_contract')
    for source_path, checksum in predecessor['local_dependencies'].items():
        require(sha(plain_path(source_path)) == checksum, 'predecessor_dependency_binding')
    predecessor_output = plain_path(predecessor['output_root'])
    started_path, complete_path = bound(config, 'predecessor_started'), bound(config, 'predecessor_complete')
    require(started_path == predecessor_output / 'STARTED.json'
            and complete_path == predecessor_output / 'COMPLETE.json'
            and not (predecessor_output / 'FAILED.json').exists(), 'predecessor_output_binding')
    started, complete = read(started_path), read(complete_path)
    require(started['config_sha256'] == config['predecessor_copy_sha256']
            and started['status'] == 'BOUNDED_SUCCESSOR_COPY_ARMED'
            and complete['status'] == 'BOUNDED_PHASE_COPY_FINISHED', 'predecessor_finished_binding')
    identity = started['identity']
    require(set(identity) == {'pid', 'uid', 'start_ticks', 'boot_id'}
            and type(identity['pid']) is int and identity['pid'] > 0
            and type(identity['uid']) is int and identity['uid'] == os.getuid()
            and isinstance(identity['start_ticks'], str) and identity['start_ticks'].isdigit()
            and isinstance(identity['boot_id'], str) and bool(identity['boot_id'])
            and scheduler.sidecar.gone(identity), 'predecessor_identity_gone')
    repository = Path(copier.__file__).resolve().parents[1]
    require(config['destination_wrapper'] == predecessor['destination_wrapper'] == original['destination_wrapper']
            == str(repository / 'gpu/ovx_ssh.sh')
            and sha(config['destination_wrapper']) == original['destination_wrapper_sha256'], 'only_node2_wrapper')
    require([item['lineage_id'] for item in original['sources']] == ['legacy', 'pilot', 'kernel'], 'three_original_sources_only')
    for source in original['sources']:
        require(source['wrapper_path'] == str(repository / 'gpu' / copier.WRAPPERS[source['lineage_id']])
                and sha(source['wrapper_path']) == source['wrapper_sha256'], 'source_wrapper_pin')
        selected = read(bound(source, 'prior_selection'))['checkpoints']
        initial = [item for item in selected if item['label'] == source['lineage_id'] + '_initial']
        require(len(initial) == 1 and source['initial_commit_path'] == initial[0]['path']
                and source['checkpoint_root'] == str(Path(initial[0]['path']).parent.parent)
                and source['initial_commit_sha256'] == initial[0]['commit_sha256'], 'original_selection_scope')
        require(source['native_schema'] == scheduler.sidecar.runner.NATIVE_SCHEMA
                and source['base_sha256'] == scheduler.sidecar.runner.BASE_SHA256, 'original_native_contract')
    require(all(scheduler.finite_number(config[name]) for name in
                ('created_unix', 'first_dispatch_unix', 'first_copy_unix', 'hard_end_unix')), 'finite_copy_times')
    require(config['created_unix'] <= time.time() < config['hard_end_unix'] <= WALL
            and config['created_unix'] <= config['first_copy_unix'] < config['hard_end_unix']
            and config['first_dispatch_unix'] % 1800 == 0
            and config['first_copy_unix'] == config['first_dispatch_unix'] - 180
            and config['first_dispatch_unix'] + 180 < config['hard_end_unix']
            and config['copy_lead_seconds'] == 180 and config['dispatch_seconds'] == 1800
            and type(config['max_cycles']) is int and 1 <= config['max_cycles'] <= 30, 'bounded_copy_cadence')
    require(config['source_lease_evidence_path'] == predecessor['source_lease_evidence_path']
            and config['source_lease_evidence_sha256'] == predecessor['source_lease_evidence_sha256'], 'preserved_lease_evidence')
    evidence = read(bound(config, 'source_lease_evidence'))['sources']
    expected_wrappers = {(source['wrapper_path'], source['wrapper_sha256']) for source in original['sources']}
    require(evidence and {(item['wrapper_path'], item['wrapper_sha256']) for item in evidence} == expected_wrappers
            and all(scheduler.finite_number(item['conservative_read_end_unix'])
                    and config['hard_end_unix'] < item['conservative_read_end_unix']
                    and sha(item['wrapper_path']) == item['wrapper_sha256'] for item in evidence), 'source_lease_bounds')
    remote_phase = read(bound(config, 'remote_phase_local'))
    require(remote_phase['schema'] == 'R146_BENCHMARK_ENROLLED_PHASE_V1'
            and config['remote_phase_local_sha256'] == config['remote_phase_sha256']
            and remote_phase['source_root'] == config['source_root']
            and config['hard_end_unix'] <= remote_phase['hard_end_unix'] <= WALL, 'remote_phase_binding')
    plain_path(config['remote_phase_path'], ROOT)
    source_root = plain_path(config['source_root'], ROOT)
    require(Path(config['remote_phase_path']).parent == ROOT
            and source_root.parent == ROOT and source_root.name.startswith('source_r146_')
            and config['remote_helper_path'] == str(source_root / 'gpu/orch_r146_successor_phase.py')
            and bound(config, 'remote_helper_local').name == 'orch_r146_successor_phase.py'
            and config['remote_helper_local_sha256'] == config['remote_helper_sha256']
            == remote_phase['helper_sha256']
            == remote_phase['sources']['gpu/orch_r146_successor_phase.py'], 'new_node_helper_binding')
    require(bound(config, 'builder_entry').read_text().startswith('## [Builder] 2026-09-16'), 'dated_builder_gate')
    gate = read(bound(config, 'cpu_gate'))
    require(gate['status'] == 'PASS' and type(gate['test_exit_code']) is int and gate['test_exit_code'] == 0
            and gate['helper_sha256'] == sha(__file__)
            and gate['remote_helper_sha256'] == config['remote_helper_sha256'], 'copy_CPU_gate')
    require(bound(gate, 'test') == repository / 'tests/test_orch_r146_checkpoint_copy_phase.py', 'copy_regression_test_pin')
    bound(gate, 'test_log')
    output = plain_path(config['output_root'], EVIDENCE_ROOT)
    require(output.name.startswith('r146_successor_copy_') and output.parent.is_dir(), 'private_repo_evidence_output')
    return config, original


def remote_command(config, action, payload=None):
    require(action in ('status', 'known', 'stage') and ((action == 'status') == (payload is None)), 'remote_action_protocol')
    command = ['env', 'CUDA_VISIBLE_DEVICES=', 'PYTHONDONTWRITEBYTECODE=1',
               'R146_PHASE_SHA256=' + config['remote_phase_sha256'], 'PYTHONPATH=' + config['source_root'],
               '/localhome/local-rohing/v2/venv/bin/python', '-B', '-m', 'gpu.orch_r146_successor_phase',
               action, '--config', config['remote_phase_path']]
    if payload is not None:
        command += ['--payload', json.dumps(payload, sort_keys=True, allow_nan=False)]
    return shlex.join(command)


def remote(config, action, payload=None, stream=None):
    result = subprocess.run(['bash', config['destination_wrapper'], remote_command(config, action, payload)],
                            stdin=stream if stream is not None else subprocess.DEVNULL,
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True,
                            timeout=min(120 if action == 'stage' else 60, remaining(config)))
    require(len(result.stdout) <= 1024 * 1024, 'bounded_remote_receipt')
    return scheduler.sidecar.runner.parse_json(result.stdout)


def safe_status(config, status):
    require(status['status'] in STATES and status['phase_sha256'] == config['remote_phase_sha256'], 'safe_phase_status')
    projected = dict(status=status['status'], phase_sha256=status['phase_sha256'])
    for name in COUNTS:
        value = status.get(name)
        require(value is None or (type(value) is int and value >= 0), 'safe_status_counter')
        projected[name] = value
    for name in ('next_dispatch_unix', 'observed_unix'):
        value = status.get(name)
        require(value is None or (scheduler.finite_number(value) and value >= 0
                and (name == 'observed_unix' or value <= WALL)), 'safe_status_timestamp')
        projected[name] = value
    active_path, active_sha = status.get('active_config_path'), status.get('active_config_sha256')
    require((active_path is None and active_sha is None) or
            (isinstance(active_path, str) and Path(active_path).is_relative_to(ROOT)
             and '..' not in Path(active_path).parts and digest_value(active_sha)), 'safe_active_config')
    require(status['status'] != 'SEGMENT_RUNNING' or active_path is not None, 'running_segment_binding')
    projected.update(active_config_path=active_path, active_config_sha256=active_sha)
    physical = status.get('active_physical', [])
    require(isinstance(physical, list) and len(physical) <= 2
            and all(type(device) is int and device in (0, 1) for device in physical), 'safe_active_devices')
    projected['active_physical'] = physical
    return projected


def remaining(config):
    seconds = config['hard_end_unix'] - time.time()
    require(seconds > 0, 'copy_wall_expired')
    return seconds


def next_copy(now, wall):
    return copier.next_copy(now, wall)


def copy_one(config, source, directory, revalidate):
    revalidate()
    require(remaining(config) > 300, 'copy_remaining_wall')
    params = {key: source[key] for key in ('lineage_id', 'checkpoint_root', 'initial_commit_path',
                                         'initial_commit_sha256', 'native_schema', 'base_sha256')}
    result = subprocess.run(['bash', source['wrapper_path'], copier.source_command(params)],
                            stdin=subprocess.DEVNULL, capture_output=True, check=True, timeout=min(60, remaining(config)))
    require(len(result.stdout) <= 4 * 1024 * 1024, 'bounded_source_selection')
    selection = scheduler.sidecar.runner.parse_json(result.stdout)
    selected = selection['selected']
    require(selection['status'] == 'COMMITTED_CHECKPOINT_SELECTED' and selected['lineage_id'] == source['lineage_id']
            and digest_value(selected['commit_sha256']) and digest_value(selected['adapter_state_sha256'])
            and Path(selected['commit_path']).parent.parent == Path(source['checkpoint_root'])
            and Path(selected['commit_path']).name == 'COMMIT.json', 'same_original_selected_root')
    payload = dict(lineage_id=source['lineage_id'], initial_commit_sha256=source['initial_commit_sha256'],
                   commit_sha256=selected['commit_sha256'], adapter_state_sha256=selected['adapter_state_sha256'])
    revalidate()
    receipt = remote(config, 'known', payload)
    if receipt['status'] in KNOWN:
        require(receipt['lineage_id'] == payload['lineage_id']
                and receipt['commit_sha256'] == payload['commit_sha256'], 'known_checkpoint_identity')
        return dict(payload, status=receipt['status'])
    require(receipt['status'] == 'NEEDS_COPY', 'known_before_source_copy')
    revalidate()
    archive = directory / (source['lineage_id'] + '.tar')
    with archive.open('xb') as stream:
        subprocess.run(['bash', source['wrapper_path'], copier.source_command(params, selected)],
                       stdin=subprocess.DEVNULL, stdout=stream, stderr=subprocess.PIPE, check=True,
                       timeout=min(120, remaining(config)))
    require(0 < archive.stat().st_size <= MAX_ARCHIVE_BYTES, 'bounded_adapter_archive')
    payload['archive_sha256'] = sha(archive)
    revalidate()
    with archive.open('rb') as stream:
        receipt = remote(config, 'stage', payload, stream)
    require(receipt['status'] in KNOWN | {'COPIED_AND_READY_VERIFIED'}
            and receipt['lineage_id'] == payload['lineage_id']
            and receipt['commit_sha256'] == payload['commit_sha256'], 'verified_stage_identity')
    return dict(payload, status=receipt['status'])


def copy_loop(path):
    config, original = local_validate(path)
    output = Path(config['output_root'])
    output.mkdir(mode=0o700, exist_ok=False)
    write(output / 'STARTED.json', dict(status='BOUNDED_SUCCESSOR_COPY_ARMED', config_sha256=sha(path),
          identity=scheduler.sidecar.identity(os.getpid()), hard_end_unix=config['hard_end_unix']))
    cycles, previous, following = 0, None, config['first_copy_unix']
    try:
        while time.time() < config['hard_end_unix'] and cycles < config['max_cycles']:
            local_validate(path)
            status = safe_status(config, remote(config, 'status'))
            comparable = {key: value for key, value in status.items() if key != 'observed_unix'}
            if comparable != previous:
                write(output / f'RELAY_{time.time_ns()}.json', status)
                previous = comparable
            require(status['status'] != 'FAILED', 'remote_phase_failed')
            if status['status'] == 'BOUNDED_PHASE_FINISHED' or following is None:
                break
            now = time.time()
            if now >= following:
                if now >= following + 180:
                    following = next_copy(now, config['hard_end_unix'])
                    continue
                if status['status'] == 'SEGMENT_RUNNING':
                    directory = output / f'cycle_{cycles:02d}'
                    directory.mkdir(mode=0o700)
                    copies = []
                    for source in original['sources']:
                        try:
                            receipt = copy_one(config, source, directory, lambda: local_validate(path))
                        except Exception as error:
                            receipt = dict(status='COPY_FAILED_NO_READY_ASSUMED', lineage_id=source['lineage_id'],
                                           error_type=type(error).__name__)
                        write(directory / (source['lineage_id'] + '.STATUS.json'), receipt)
                        copies.append(receipt)
                    cycles += 1
                    following = next_copy(time.time(), config['hard_end_unix'])
                    write(directory / 'COMPLETE.json', dict(status='COPY_CYCLE_FINISHED', copies=copies,
                          next_copy_unix=following, observed_unix=time.time()))
            delay = min(30, max(0, config['hard_end_unix'] - time.time()))
            if following is not None and following > time.time():
                delay = min(delay, following - time.time())
            time.sleep(max(0, delay))
        write(output / 'COMPLETE.json', dict(status='BOUNDED_PHASE_COPY_FINISHED', cycles=cycles,
              config_sha256=sha(path), observed_unix=time.time()))
    except BaseException as error:
        write(output / 'FAILED.json', dict(status='FAILED', cycles=cycles, error_type=type(error).__name__))
        raise


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('validate', 'copy'))
    parser.add_argument('--config', required=True, type=Path)
    args = parser.parse_args()
    try:
        if args.action == 'copy':
            copy_loop(args.config)
        else:
            local_validate(args.config)
        print(json.dumps(dict(status='LOCAL_COPY_' + args.action.upper() + '_COMPLETE')))
    except Exception as error:
        print(json.dumps(dict(status='LOCAL_COPY_FAILED', error_type=type(error).__name__)))
        raise SystemExit(1)


if __name__ == '__main__':
    main()
