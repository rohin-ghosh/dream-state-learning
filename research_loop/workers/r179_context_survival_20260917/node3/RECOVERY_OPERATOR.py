"""Node3 authorized terminal saved-prefix segments; no original journal mutation."""

import argparse
from copy import deepcopy
import fcntl
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import shutil
import socket
import subprocess
import sys
import time
import uuid


HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
WALL_ROOT = Path('/localhome/local-rohing/orch_r179_node3_wall_20260917t1752z_2')
OLD_ROOT = Path('/localhome/local-rohing/orch_r179_node3_context_20260917t1715z_1')
WALL_SHA = '63d425139bffa4d4db8d13a07d3026e080a03ee9289050fb9d9e375f77020f16'
R154_SHA = '0d44d1106c64d867ea481f0d23d8e625ebaf8a697bc45ffc940e3af079128ae5'
POST_WALL_SHA = '5c39e54187c756bd31cd874916128a3754f1217f1aa3b2849b3d8de6adfea735'
PHYSICALS = (0, 1, 2, 3, 4, 7)
PYTHON = '/localhome/local-rohing/v2/venv/bin/python'


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def regular(path):
    path = Path(path)
    require(path.is_absolute() and '..' not in path.parts and path == path.resolve()
            and not any(part.is_symlink() for part in (path, *path.parents)), 'canonical_nonlink')
    return path


def sha(path):
    hasher = hashlib.sha256()
    with regular(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1048576), b''):
            hasher.update(block)
    return hasher.hexdigest()


def read(path):
    return json.loads(regular(path).read_bytes())


def write(path, document):
    with regular(path).open('x') as stream:
        json.dump(document, stream, indent=2, sort_keys=True, allow_nan=False)
        stream.flush()
        os.fsync(stream.fileno())


def reference(path):
    return dict(path=str(path), sha256=sha(path))


def load(path, expected):
    require(sha(path) == expected, 'pinned_dependency:' + str(path))
    spec = importlib.util.spec_from_file_location('recovery_' + Path(path).stem, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def namespaces():
    require(sha(WALL_ROOT / 'bootstrap/WALL_OPERATOR.py') == WALL_SHA, 'frozen_wall_adapter')
    wall = dict(__name__='node3_recovery_private_wall', __file__=str(Path(__file__).resolve()))
    exec(compile((WALL_ROOT / 'bootstrap/WALL_OPERATOR.py').read_bytes(), str(__file__), 'exec'), wall)
    family, adapter = wall['family_namespace']()
    family['contained_command'] = lambda plan, config, original, config_path, lifetime: mapped_command(
        family, plan, config, original, config_path.parent, 'contained', lifetime)
    return wall, family, adapter


def output_path(physical):
    require(type(physical) is int and physical in PHYSICALS, 'six_scoped_physical_devices')
    require(ROOT.parent == Path('/localhome/local-rohing') and ROOT.name.startswith('orch_r179_node3_recovery_'),
            'fresh_recovery_root')
    return ROOT / ('control' + str(physical))


def bound_cpu():
    require(sha(HERE / 'POST_WALL.md') == POST_WALL_SHA, 'exact_Main_post_terminal_authority')
    receipt = read(HERE / 'CPU_LOCAL.json')
    require(receipt['status'] == 'PASS' and receipt['failed'] == 0 and receipt['operator_sha256'] == sha(__file__),
            'exact_local_CPU_before_actions')
    for name, expected in receipt['files'].items():
        require(Path(name).name == name and sha(HERE / name) == expected, 'bound_receiving_bootstrap:' + name)
    return receipt


def verify_exits(actors):
    require(set(actors) == {'actor', 'timer', 'supervisor'}, 'all_three_original_roles')
    for expected in actors.values():
        require(expected.get('absent') is True, 'terminal_witness_all_absent')
        require(not Path('/proc', str(expected['pid'])).exists(), 'original_pid_still_absent')


def verify_terminal(row):
    verify_exits(row['actors'])
    require(row['terminal']['EXIT.json']['document']['exit_code'] == 124, 'natural_original_wall_timeout')
    for receipt in row['terminal'].values():
        require(reference(receipt['reference']['path']) == receipt['reference'], 'terminal_receipt_unchanged')
    for receipt in (row['head']['reference'], row['saved']['record_ref'], row['saved']['checkpoint_ref']):
        require(reference(receipt['path']) == receipt, 'terminal_saved_and_suffix_binding')
    paths = sorted(path for path in (Path(row['logical_life']) / 'stream/records').glob('*.json')
                   if re.fullmatch(r'\d{20}\.json', path.name))
    require(len(paths) == row['head']['index'] + 1 and str(paths[-1]) == row['head']['reference']['path'],
            'final_terminal_head_no_catchup')


def independent_tree(original, destination):
    original, destination = regular(original), regular(destination)
    shutil.copytree(original, destination)
    pins = {}
    for prior in sorted(original.rglob('*')):
        regular(prior)
        if prior.is_file():
            copied = destination / prior.relative_to(original)
            require(sha(prior) == sha(copied) and (prior.stat().st_dev, prior.stat().st_ino) !=
                    (copied.stat().st_dev, copied.stat().st_ino), 'independent_exact_checkpoint_file')
            pins[str(prior.relative_to(original))] = sha(copied)
    return pins


def readout_markers(plan, cycle, original, destination):
    revision = plan.get('readout_revision', 1)
    suffix = '' if revision == 1 else '_r' + str(revision)
    required = {'sleep_%06d%s_DISPATCH.json' % (index, suffix) for index in range(cycle + 1)}
    paths = sorted(original.glob('*_DISPATCH.json'))
    require(required <= {path.name for path in paths}, 'every_consumed_historical_readout_marker')
    refs = []
    for prior in paths:
        regular(prior)
        shutil.copyfile(prior, destination / prior.name)
        require(sha(prior) == sha(destination / prior.name), 'readout_marker_exact_no_replay')
        refs.append(reference(prior))
    return refs


def stage(physical):
    bound_cpu()
    wall, family, adapter = namespaces()
    require(socket.gethostname() == family['api']().HOST and time.time() < wall['NEW_WALL'] - 900,
            'actual_host_remaining_existing_lease')
    row = next(row for row in read(HERE / 'TERMINAL.json')['rows'] if row['physical'] == physical)
    verify_terminal(row)
    lane = adapter['lane_for'](physical)
    old_config, old_plan = read(lane['guard_ref']['path']), read(lane['plan_ref']['path'])
    require(row['logical_life'] == old_plan['root'], 'exact_original_logical_life')
    prior = WALL_ROOT / ('preflight' + str(physical))
    saved = read(prior / 'SAVED.json')
    require(saved['state_sha256'] == row['saved']['state_sha256'] and saved['cycle'] == row['saved']['cycle'],
            'terminal_saved_not_stale_preparation')
    output = output_path(physical)
    output.mkdir(mode=0o700)
    backing = output / 'run1'
    backing.mkdir(mode=0o700)
    original = Path(old_plan['root'])
    recovery = load(HERE / 'R154.py', R154_SHA)
    records = [read(path) for path in sorted((original / 'stream/records').glob('*.json'))
               if re.fullmatch(r'\d{20}\.json', path.name)]
    recovery.chain(records, read(original / 'stream/JOURNAL.json'))
    summary = recovery.suffix_summary(records, row['saved']['index'], row['saved']['optimizer_steps'])
    require(summary['unsaved_updates'] == row['suffix']['unsaved_updates']
            and summary['last_optimizer_step'] == row['suffix']['last_observed_optimizer_step'], 'final_spent_update_gap')
    counts = {}
    for record in records:
        counts[record['kind']] = counts.get(record['kind'], 0) + 1
    write(output / 'SPENT_ACCOUNTING.json', dict(original_terminal_kind_counts=counts, suffix=summary,
        historical_records=len(records), cumulative_spend_retained=True, restored_model_optimizer_steps=row['saved']['optimizer_steps'],
        unsaved_updates_refunded=False, historical_child_provider_readout_calls_replayed=False,
        future_accounting='new_segment_records_after_saved_prefix_are_additional_spend_not_original_counter_replacement'))
    prefix = recovery.copy_prefix(original / 'stream', backing / 'stream', row['saved']['index'])
    inbox = recovery.copy_saved_inbox(original / 'stream', backing / 'stream', row['saved']['index'])
    (backing / 'checkpoints').mkdir()
    checkpoint_name = 'sleep_%06d' % saved['cycle']
    checkpoint_files = independent_tree(original / 'checkpoints' / checkpoint_name,
                                       backing / 'checkpoints' / checkpoint_name)
    (backing / 'readouts').mkdir()
    markers = readout_markers(old_plan, saved['cycle'], original / 'readouts', backing / 'readouts')
    require(markers == row['existing_readout_dispatch_refs'], 'terminal_dispatch_census_exact')
    write(output / 'PREFIX_COPY.json', dict(files=prefix, saved_inbox=inbox, checkpoint_files=checkpoint_files,
        checkpoint_directory=checkpoint_name, readout_dispatch=markers, suffix_inbox_copied=False))
    write(output / 'RECOVERY_SEGMENT.json', dict(schema='R179_NODE3_TERMINAL_SAVED_PREFIX_V1', physical=physical,
        terminal=row, logical_root=str(original), host_backing_root=str(backing), original_root_inode=original.stat().st_ino,
        original_root_device=original.stat().st_dev, exact_saved_state_only=True, uninterrupted=False,
        unsaved_updates=row['suffix']['unsaved_updates'], original_full_journal_preserved=True,
        suffix_replayed=False, archived_suffix_in_active_view=False, parent_provider_restarted=False,
        parent_routing='original_host_root_archival_Main_owns_future_cursor_routing', created_unix=time.time()))
    source = OLD_ROOT / ('physical' + str(physical)) / 'source'
    sys.path.insert(0, str(source))
    plan = wall['proposed_plan'](old_plan, source, saved)
    write(output / 'PLAN.json', plan)
    write(output / 'SAVED.json', saved)
    write(output / 'LEASE_BUDGET.json', dict(schema='R131_EXISTING_LEASE_RUNTIME_BUDGET_V1',
        authority_path=str(HERE / 'CONTINUATION.md'), authority_sha256=wall['AUTH_SHA'],
        previous_receipt_path=old_config['lease_path'], previous_receipt_sha256=wall['LEASE_SHA'],
        lease_end_unix=wall['CEILING'], hard_end_unix=wall['NEW_WALL'], safety_margin_seconds=600, lease_extended=False))
    write(output / 'ALLOCATION.json', dict(read(old_config['allocation_path']), plan_sha256=sha(output / 'PLAN.json')))
    config = family['readmission_guard'](old_config, old_plan, output)
    config.update(plan_path=str(output / 'PLAN.json'), plan_sha256=sha(output / 'PLAN.json'),
        lease_path=str(output / 'LEASE_BUDGET.json'), lease_sha256=sha(output / 'LEASE_BUDGET.json'),
        allocation_path=str(output / 'ALLOCATION.json'), allocation_sha256=sha(output / 'ALLOCATION.json'),
        source_pins=read(source.parent / 'PROPOSED_GUARD.json')['source_pins'], hard_end_unix=wall['NEW_WALL'])
    write(output / 'GUARD.json', config)
    family['verify_source'](source.parent / 'PROPOSED_GUARD.json', old_config, old_plan, config, plan)
    write(output / 'STAGED.json', dict(operator_sha256=sha(__file__), new_config_sha256=sha(output / 'GUARD.json'),
        old_config=lane['guard_ref']['path'], old_config_sha256=lane['guard_ref']['sha256'],
        source_binding=str(source.parent / 'PROPOSED_GUARD.json'), terminal_sha256=sha(HERE / 'TERMINAL.json'),
        segment_sha256=sha(output / 'RECOVERY_SEGMENT.json'), physical=physical, signals_sent=0))
    verify_terminal(row)
    write(output / 'RETIRED.json', dict(status='EXACT_OLD_PROCESSES_EXITED', exit_mode='ORIGINAL_WALL_TIMEOUT',
        operator_signals=0, terminal_sha256=sha(HERE / 'TERMINAL.json'), actors=row['actors']))
    return dict(status='TERMINAL_SEGMENT_STAGED_NOT_LAUNCHED', physical=physical, output=str(output),
                unsaved_updates=row['suffix']['unsaved_updates'])


def verify_mount(output):
    segment = read(output / 'RECOVERY_SEGMENT.json')
    logical, backing = Path(segment['logical_root']).stat(), (output / 'run1').stat()
    require((logical.st_dev, logical.st_ino) == (backing.st_dev, backing.st_ino)
            and (logical.st_dev, logical.st_ino) != (segment['original_root_device'], segment['original_root_inode']),
            'only_private_new_segment_not_original')
    return dict(logical_root=segment['logical_root'], backing_root=str(output / 'run1'),
                inode=logical.st_ino, device=logical.st_dev, original_hidden=True)


def modules(output):
    bound_cpu()
    output = regular(output)
    request = read(output / 'STAGED.json')
    require(output == output_path(request['physical']) and request['operator_sha256'] == sha(__file__)
            and request['new_config_sha256'] == sha(output / 'GUARD.json')
            and request['segment_sha256'] == sha(output / 'RECOVERY_SEGMENT.json')
            and request['terminal_sha256'] == sha(HERE / 'TERMINAL.json'), 'exact_staged_execution')
    config = read(output / 'GUARD.json')
    plan = read(config['plan_path'])
    sys.path.insert(0, plan['source_root'])
    wall, family, adapter = namespaces()
    config, plan, original = family['new_modules'](output / 'GUARD.json')
    return wall, family, config, plan, original


def mapped_command(family, plan, config, original, output, action, lifetime, policy=None):
    policy = deepcopy(config['device_containment'] if policy is None else policy)
    payload = [PYTHON, '-B', str(Path(__file__).resolve()), '--action', action, '--physical', str(plan['physical'])]
    if action == 'branch-cpu':
        payload += ['--policy', json.dumps(policy, sort_keys=True)]
    if plan['physical'] in (0, 2):
        command = family['direct_command'](plan, policy, payload, lifetime)
    elif plan['physical'] == 1:
        command = original.programmes.device_containment_command(1, policy['minor'], policy['uid'], policy['gid'],
            policy['unit'], plan['source_root'], payload, lifetime)
    else:
        command = original.programmes.containment_command(plan, policy, payload, lifetime)
    position = command.index('/usr/bin/env')
    command[position:position] = ['--property=BindPaths=' + str(output / 'run1') + ':' + plan['root'],
                                 '--property=ReadOnlyPaths=' + plan['source_root']]
    return command


def verify_saved_inbox(journal, stream, state_sha256):
    before = stream.history.checkpoint()
    for event in journal.read_inbox():
        require(stream.history.append(event) is False, 'saved_inbox_event_already_in_history')
    require(stream.history.checkpoint() == before and journal.latest_checkpoint()['expected_sha256'] == state_sha256,
            'saved_inbox_no_history_or_journal_change')


def branch_cpu(output, policy):
    mount = verify_mount(output)
    wall, family, config, plan, original = modules(output)
    probe = load(HERE / 'device_probe.py', bound_cpu()['files']['device_probe.py'])
    device = probe.probe(policy, plan['gpu_uuid'])
    os.environ['CUDA_VISIBLE_DEVICES'] = ''
    from gpu.orch_r125_stream_journal import StreamJournal
    native = original.native
    copied = read(output / 'PREFIX_COPY.json')
    root = Path(plan['root'])
    for name, expected in copied['files'].items():
        require(sha(root / 'stream' / name) == expected, 'exact_independent_prefix_before_CPU')
    require({path.name: sha(path) for path in (root / 'stream/inbox').iterdir()} == copied['saved_inbox'],
            'only_saved_registered_inbox_no_suffix')
    saved = read(output / 'SAVED.json')
    with StreamJournal(root / 'stream', create=False) as journal:
        checkpoint = journal.latest_checkpoint()
        require(checkpoint['expected_sha256'] == saved['state_sha256'], 'copied_latest_exact_saved_state')
        stream = native.ContinualStream.restore(checkpoint['document'], expected_sha256=checkpoint['expected_sha256'])
        require(stream.pending is None and stream.sleep_frontier == len(stream.rows), 'complete_saved_view_only')
        verify_saved_inbox(journal, stream, saved['state_sha256'])
    proof = wall['state_cpu'](output)
    require({name: sha(root / 'stream' / name) for name in copied['files']} == copied['files'],
            'CPU_does_not_change_prefix_bytes')
    proof.update(mount=mount, device=device, config_sha256=sha(output / 'GUARD.json'),
                 segment_sha256=sha(output / 'RECOVERY_SEGMENT.json'), history_exact_saved=True,
                 replayed_calls=0, CUDA_context_created=False)
    return proof


def preflight(output):
    wall, family, config, plan, original = modules(output)
    (output / 'CPU_ONCE').mkdir()
    policy = deepcopy(config['device_containment'])
    policy['unit'] = policy['unit'].rsplit('-', 1)[0] + '-' + uuid.uuid4().hex
    command = family['api']().allocator_command(mapped_command(family, plan, config, original, output,
        'branch-cpu', 300, policy))
    result = subprocess.run(command, text=True, capture_output=True, timeout=330, cwd=plan['source_root'],
                            env=family['environment'](plan['source_root']))
    write(output / 'CPU_PROCESS.json', dict(returncode=result.returncode, stdout=result.stdout,
        stderr=result.stderr, command=command, observed_unix=time.time()))
    require(result.returncode == 0, 'actual_private_mount_receiving_CPU_failed_no_retry')
    proof = json.loads(result.stdout)
    require(proof['status'] == 'PASS' and proof['no_CUDA'] is True and proof['device']['policy'] == policy
            and proof['config_sha256'] == sha(output / 'GUARD.json'), 'actual_CPU_exact_configuration')
    write(output / 'BRANCH_CPU.json', proof)
    write(output / 'BUILDER_LAUNCH_RECEIPT.json', dict(author='Builder/node3', observed_unix=time.time(),
        operator_sha256=sha(__file__), authority=reference(HERE / 'AUTHORITY.md'),
        continuation=reference(HERE / 'CONTINUATION.md'), local_cpu=reference(HERE / 'CPU_LOCAL.json'),
        post_wall_authority=reference(HERE / 'POST_WALL.md'), spent_accounting=reference(output / 'SPENT_ACCOUNTING.json'),
        branch_cpu=reference(output / 'BRANCH_CPU.json'), segment=reference(output / 'RECOVERY_SEGMENT.json'),
        source_pins=config['source_pins'], stage=reference(output / 'STAGED.json'), learner_signals=0,
        exact_saved_state_only=True, uninterrupted=False, hardware_lease_extended=False))
    return dict(status='RECEIVING_RECOVERY_CPU_PASS', physical=plan['physical'], output=str(output))


def launch_gate(output):
    wall, family, config, plan, original = modules(output)
    receipt = read(output / 'BUILDER_LAUNCH_RECEIPT.json')
    for key, name in (('branch_cpu', 'BRANCH_CPU.json'), ('segment', 'RECOVERY_SEGMENT.json'), ('stage', 'STAGED.json')):
        require(receipt[key] == reference(output / name), 'bound_Builder_gate:' + key)
    require(receipt['operator_sha256'] == sha(__file__) and receipt['local_cpu'] == reference(HERE / 'CPU_LOCAL.json')
            and receipt['authority'] == reference(HERE / 'AUTHORITY.md')
            and receipt['source_pins'] == config['source_pins'], 'bound_Builder_code_authority_source')
    verify_exits(read(output / 'RECOVERY_SEGMENT.json')['terminal']['actors'])
    return wall, family, config, plan, original


def contained(output):
    write(output / 'SEGMENT_MOUNT_VERIFIED.json', verify_mount(output))
    wall, family, config, plan, original = launch_gate(output)
    if plan['physical'] in (0, 2):
        return family['contained'](output)
    return original.programmes.contained_native(output / 'GUARD.json')


def monitor(output, process):
    segment, saved = read(output / 'RECOVERY_SEGMENT.json'), read(output / 'SAVED.json')
    start = segment['terminal']['saved']['index']
    proof = read(output / 'BRANCH_CPU.json')
    deadline = time.monotonic() + 600
    while time.monotonic() < deadline:
        require(process.poll() is None and not any((output / name).exists() for name in
                ('EXIT.json', 'SERVICE_EXIT.json', 'SUPERVISOR_FAILED.json')), 'successor_failed_no_retry')
        wall_records = []
        for path in sorted((output / 'run1/stream/records').glob('*.json')):
            if not re.fullmatch(r'\d{20}\.json', path.name) or int(path.stem) <= start:
                continue
            record = read(path)
            expected_hash = hashlib.sha256(json.dumps({key: value for key, value in record.items() if key != 'sha256'},
                sort_keys=True, separators=(',', ':'), allow_nan=False).encode()).hexdigest()
            require(record['sha256'] == expected_hash, 'actual_new_journal_record_hash')
            if record['kind'] == 'WALL_EXTENDED':
                require(record['document'] == proof['wall_record'], 'actual_exact_wall_extension')
                wall_records.append(reference(path))
            if record['kind'] == 'LOADED':
                document = record['document']
                require(len(wall_records) == 1 and document['resume'] is True
                        and document['optimizer_steps'] == proof['optimizer_steps']
                        and document['adapter_sha256'] == proof['adapter_state_sha256'], 'actual_saved_state_loaded')
                wall, family, config, plan, original = modules(output)
                actor = family['api']().identity(document['pid'])
                require(actor['argv'][-1] == str(output / 'GUARD.json') and actor['cwd'] == plan['source_root'],
                        'actual_successor_source_guard')
                launch = read(output / 'LAUNCH.json')
                require(actor['parent'] == launch['pid'] and launch['guard_sha256'] == sha(output / 'GUARD.json')
                        and launch['plan_sha256'] == config['plan_sha256'], 'actual_successor_launch_binding')
                receipt = dict(status='SAVED_PREFIX_R179_WALL_SUCCESSOR_LOADED', physical=plan['physical'],
                    actor=actor, record=reference(path), wall=wall_records[0],
                    optimizer_steps=document['optimizer_steps'], saved_cycle=saved['cycle'],
                    unsaved_updates=segment['unsaved_updates'], exact_saved_state_only=True, uninterrupted=False,
                    original_root=plan['root'], active_host_root=str(output / 'run1'), source_root=plan['source_root'],
                    hard_end_unix=plan['hard_end_unix'], lease_end_unix=plan['lease_end_unix'],
                    context_retained_event_observed=False, completed_sleep_observed=False, observed_unix=time.time())
                write(output / 'LOADED_RECEIPT.json', receipt)
                return receipt
        time.sleep(1)
    write(output / 'MONITOR_TIMEOUT.json', dict(no_retry=True, observed_unix=time.time()))
    return dict(status='LOAD_UNCERTAIN_NO_RETRY', output=str(output))


def dispatch(output):
    wall, family, config, plan, original = launch_gate(output)
    (output / 'START_ONCE').mkdir()
    lock = os.open('/localhome/local-rohing/orch_r142_allocator_ovx2_ROLLOUT.lock',
                   os.O_RDWR | os.O_CLOEXEC | os.O_NOFOLLOW)
    try:
        fcntl.flock(lock, fcntl.LOCK_EX)
        verify_terminal(read(output / 'RECOVERY_SEGMENT.json')['terminal'])
        command = [PYTHON, '-B', str(Path(__file__).resolve()), '--action', 'supervise',
                   '--physical', str(plan['physical'])]
        with (output / 'SUPERVISOR.log').open('x') as log:
            process = subprocess.Popen(command, stdin=subprocess.DEVNULL, stdout=log, stderr=subprocess.STDOUT,
                cwd=plan['source_root'], env=family['environment'](plan['source_root']), start_new_session=True)
        write(output / 'DISPATCHED.json', dict(pid=process.pid, command=command, no_retry=True, started_unix=time.time()))
        return monitor(output, process)
    finally:
        os.close(lock)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--action', required=True,
        choices=('stage', 'preflight', 'branch-cpu', 'dispatch', 'supervise', 'contained'))
    parser.add_argument('--physical', required=True, type=int, choices=PHYSICALS)
    parser.add_argument('--policy')
    args = parser.parse_args()
    output = output_path(args.physical)
    if args.action == 'stage':
        result = stage(args.physical)
    elif args.action == 'preflight':
        result = preflight(output)
    elif args.action == 'branch-cpu':
        result = branch_cpu(output, json.loads(args.policy))
    elif args.action == 'contained':
        result = contained(output)
    elif args.action == 'dispatch':
        result = dispatch(output)
    else:
        try:
            wall, family, config, plan, original = launch_gate(output)
            result = family['supervise'](output)
        except BaseException as error:
            write(output / 'SUPERVISOR_FAILED.json', dict(error=repr(error), no_retry=True, observed_unix=time.time()))
            raise
    print(json.dumps(result, sort_keys=True))


if __name__ == '__main__':
    main()
