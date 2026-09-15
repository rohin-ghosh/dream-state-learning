"""Non-material postcommit crash disposition: no eval replay or fabricated completion."""

import argparse
from collections import Counter
import fcntl
import os
from pathlib import Path
import time
import json

from gpu import orch_r118_route_parallel_boundary as boundary
from gpu import orch_r111_shared_cutoff as old_cutoff


SCHEMA = 'R118_ROUTE_CRASHED_POSTCOMMIT_V1'
MODE = 'CRASHED_POSTCOMMIT_MISSING_READOUT'
DIRECTORY = 'R118_POSTCOMMIT_CRASH_BOUNDARY_V1'
require, read, sha, ref, bound, write = (boundary.require, boundary.read, boundary.sha,
    boundary.ref, boundary.bound, boundary.write)


def absent(identity):
    try:
        current = old_cutoff.identity(identity['pid'])
        state = (Path('/proc') / str(identity['pid']) / 'stat').read_text().rsplit(')', 1)[1].split()[0]
        return state in ('Z', 'X') or any(current[key] != identity[key] for key in
            ('pid', 'uid', 'start_ticks', 'boot_id', 'command_sha256'))
    except (FileNotFoundError, ProcessLookupError):
        return True


def verify_owned_release(root, plan, control_reference, release_reference):
    control, release = bound(control_reference), bound(release_reference)
    branch = plan['shared_learner']['branch']
    spec = control['routes'][branch]
    require(spec['root'] == str(root) and spec['plan'] == ref(root / 'PLAN.json')
            and spec['uuid'] == plan['uuid'], 'actual_old_cutoff_root_PLAN_UUID')
    require(Path(release_reference['path']) == Path(control['directory']) / branch / 'DISPOSITION.json',
            'actual_cutoff_disposition_path')
    require(release['status'] == 'RELEASED' and release['reason'] == 'PEER_CANNOT_COMPLETE_BARRIER'
            and release['no_fake_terminal'] is True, 'actual_postcommit_cutoff_release')
    source = Path(control['source']['path'])
    require(source.is_absolute() and not source.is_symlink() and ref(source) == control['source'],
            'exact_original_cutoff_source_bytes')
    processes = release['processes']
    require(sum(item['role'] == 'actor' for item in processes) == 1
            and sum(item['role'] == 'supervisor' for item in processes) == 1, 'exact_owned_pair')
    for item in processes:
        require(item['role'] in ('actor', 'supervisor', 'readout') and item['identity']['uid'] == os.getuid(),
                'owned_process_roles_and_uid')
        require(absent(item['identity']), 'recorded_process_still_alive_no_capture_or_signal')
        if item['role'] in ('actor', 'supervisor'):
            expected = spec['initial_actor' if item['role'] == 'actor' else 'supervisor']
            require(all(item['identity'][key] == expected[key] for key in
                ('pid', 'uid', 'start_ticks', 'boot_id', 'command_sha256')), 'actual_control_identity')
    for directory in Path('/proc').iterdir():
        if not directory.name.isdigit():
            continue
        try:
            if directory.stat().st_uid != os.getuid():
                continue
            arguments = (directory / 'cmdline').read_bytes().split(b'\0')
            if str(root).encode() not in arguments:
                continue
            for module in (boundary.MODULE, boundary.SUCCESSOR):
                if module.encode() in arguments:
                    position = arguments.index(module.encode())
                    require(arguments[position + 1] not in (b'run', b'supervise', b'readout'),
                            'another_route_actor_live_no_capture_or_signal')
        except (FileNotFoundError, ProcessLookupError):
            continue
    return processes


def file_inventory(root, directories):
    files = []
    for directory in directories:
        if not directory.exists():
            continue
        for path in sorted(directory.rglob('*')):
            if path.is_file():
                require(not path.is_symlink() and path.resolve().is_relative_to(root), 'owned_raw_path_only')
                files.append(path)
    return files


def committed_train(root, plan):
    common = Path(plan['shared_learner']['root'])
    state, common_complete = boundary.committed(common)
    require(state['generation'] == 1, 'only_first_committed_shared_sleep_recovery')
    require(not (common / 'generation_000001' / (plan['shared_learner']['branch']+'.json')).exists(),
            'unsettled_new_generation_TRAIN_submission')
    require(state['config_sha256'] == sha(common / 'CONFIG.json')
            == plan['shared_learner']['config_sha256'], 'unchanged_common_configuration')
    paths = sorted(root.glob('cycle_*/SHARED_SLEEP.json'))
    require(paths, 'actual_branch_shared_sleep_required')
    cycle = paths[-1].parent
    receipt, start, sleep = read(paths[-1]), read(cycle / 'START.json'), read(cycle / 'SLEEP.json')
    number, index = start['cycle'], sleep['sleeps']
    require(cycle.name == f'cycle_{number:04d}' and receipt['status'] == 'COMPLETE'
            and receipt['state'] == state and receipt['branch'] == plan['shared_learner']['branch'],
            'actual_local_committed_sleep_no_optimizer_replay')
    checkpoint = cycle / 'checkpoint/CHECKPOINT.json'
    wrapper, canonical = read(checkpoint), read(state['checkpoint']['path'])
    require(canonical.get('complete') is True, 'canonical_checkpoint_complete')
    require(wrapper['complete'] is True and wrapper['shared_checkpoint'] == state['checkpoint']
            and wrapper['cycle'] == number and wrapper['sleeps'] == index,
            'exact_canonical_local_wrapper')
    require(wrapper['adapter'] == canonical['adapter']
            and canonical['optimizer_rng_sha256'] == state['checkpoint']['optimizer_path_sha256'],
            'canonical_adapter_optimizer_rng_binding')
    from organism_v6.orch_guided_bridge import AdapterIdentity
    AdapterIdentity.from_document(canonical['adapter'])
    require(sleep['checkpoint_sha256'] == sha(checkpoint) == read(root / 'OWN_CARRY.json')['checkpoint_sha256'],
            'saved_carry_from_committed_checkpoint')
    reference = read(cycle / 'SHARED_SUBMISSION.json')
    expected = common / 'generation_000000' / (plan['shared_learner']['branch'] + '.json')
    require(reference['generation'] == 0 and reference['path'] == str(expected)
            and reference['sha256'] == sha(expected), 'actual_generation_zero_submission')
    submission = read(expected)
    require(submission['generation'] == 0 and submission['branch'] == plan['shared_learner']['branch']
            and submission['checkpoint_sha256'] == bound(common_complete)['source_checkpoint']['path_sha256'],
            'trained_generation_zero_lineage')
    rows = read(cycle / 'ROWS.json')
    require(rows == submission['rows'] and len(set(submission['episode_ids'])) == 2, 'exact_original_two_episode_rows')
    config = read(common / 'CONFIG.json')
    for row in rows:
        boundary.shared.validate_row(row, config['branches'][submission['branch']], config['excluded_ids'],
                                     generation=0, checkpoint_sha256=submission['checkpoint_sha256'])
    encoding = common / 'generation_000000/sleep/ENCODING.json'
    rejected = {row['source'] for row in read(encoding)['rejected'] if row['kind'] == 'NEW'}
    accepted = [row['source_call_sha256'] for row in rows if row['source_call_sha256'] not in rejected]
    return dict(state=state, common_complete=common_complete, cycle=cycle, number=number, sleep=index,
                submission=ref(expected), encoding=ref(encoding), accepted_train_hashes=accepted,
                rejected_train_hashes=[row['source_call_sha256'] for row in rows if row['source_call_sha256'] in rejected])


def inspect_snapshot(root, plan):
    proof = committed_train(root, plan)
    cycle, number, index = proof['cycle'], proof['number'], proof['sleep']
    require(not (cycle / 'COMPLETE.json').exists(), 'use_normal_boundary_for_completed_cycle')
    ledger = boundary.prior.ledger(root)
    require(boundary.prior.no_later_reservations(ledger, number, index), 'unsettled_later_charged_TRAIN_or_eval')
    train, parents, evaluations = [], [], []
    raw = file_inventory(root, [cycle, root / f'readout_{index:04d}',
                               root / 'open_readouts' / f'readout_{index:04d}'])
    paths = {}
    for path in raw:
        if path.name.startswith('CALL_') and path.suffix == '.json':
            require(path.name not in paths, 'unique_native_capture')
            paths[path.name] = path
    for entry in ledger:
        if entry.get('cycle') != number and entry.get('sleep') != index:
            continue
        if entry['kind'] == 'PARENT':
            path = root / 'parent_queue' / f'{entry["number"]:06d}_F1_C{number:04d}.observed.json'
            require(path.exists() and read(path).get('observed_unix') is not None, 'unsettled_charged_PARENT')
            parents.append(ref(path)); raw.append(path)
        elif entry['kind'] == 'NATIVE' and entry.get('cycle') == number:
            path = cycle / f'CALL_{entry["number"]:06d}.json'
            require(entry.get('phase') in ('experience', 'presleep', 'reflection', 'open_turn')
                    and path.exists() and read(path).get('finished_unix') is not None, 'unsettled_charged_TRAIN')
            train.append(ref(path))
        else:
            require(entry['kind'] == 'NATIVE' and entry.get('sleep') == index
                    and entry.get('phase') in ('readout', 'open_readout'), 'only_eval_may_be_interrupted')
            path = paths.get(f'CALL_{entry["number"]:06d}.json')
            evaluations.append(dict(number=entry['number'], phase=entry['phase'],
                capture=ref(path) if path else None,
                capture_finished=bool(path and read(path).get('finished_unix') is not None),
                charged_preserved=True, retry=False))
    require({row['sha256'] for row in train} == {row['source_call_sha256'] for row in read(cycle / 'ROWS.json')},
            'all_charged_TRAIN_accounted_in_original_submission')
    dispositions = {}
    for scope, directory in (('DEV', root / f'readout_{index:04d}'),
                             ('OPEN', root / 'open_readouts' / f'readout_{index:04d}')):
        complete = directory / 'COMPLETE.json'
        dispositions[scope] = dict(status='ORIGINAL_COMPLETE' if complete.exists() else 'MISSING',
            reason='EXISTING_RECEIPT' if complete.exists() else
                   ('INTERRUPTED_AFTER_SHARED_COMMIT' if directory.exists() else 'NOT_STARTED_BEFORE_CRASH'),
            complete=ref(complete) if complete.exists() else None,
            retry=False, counted_as_success=False)
    require(any(item['status'] == 'MISSING' for item in dispositions.values()), 'explicit_missing_readout_required')
    later = [path for path in root.glob('cycle_*/START.json') if read(path)['cycle'] > number]
    require(len(later) <= 1, 'at_most_one_empty_next_cursor')
    if later:
        require(read(later[0])['cycle'] == number+1 and {path.name for path in later[0].parent.iterdir()} == {'START.json'},
                'later_TRAIN_work_not_empty')
        raw.extend(later)
    for name in ('PLAN.json', 'RESERVATIONS.jsonl', 'OWN_CARRY.json', 'PENDING_TRIPLE.json',
                 'ACTOR_READY.json', 'PUBLICATION.json', 'ROHIN_GO.json'):
        if (root / name).exists():
            raw.append(root / name)
    raw.extend(root.glob('CRASH_*.json'))
    return dict(schema=SCHEMA, root=str(root), completed_cycle=number, next_cycle=number+1,
        cycle_completion_claimed=False, sleep=index, state=proof['state'], checkpoint=proof['state']['checkpoint'],
        common_complete=proof['common_complete'], submission=proof['submission'], encoding=proof['encoding'],
        accepted_train_hashes=proof['accepted_train_hashes'], rejected_train_hashes=proof['rejected_train_hashes'],
        trained_generation=0, generation_zero_resubmitted=False, charged=dict(Counter(row['kind'] for row in ledger)),
        missing_readouts=dispositions, eval_reservations=evaluations, parent_receipts=parents,
        empty_successor_start=ref(later[0]) if later else None,
        preserved_files={str(path.relative_to(root)): sha(path) for path in raw},
        no_pending_TRAIN=True, no_pending_calls=False, missing_eval_is_not_success=True,
        no_quota_reset=True, native_restore_status='REQUIRED_BEFORE_NEW_COLLECTION', observed_unix=time.time())


def capture(root, authorization, cutoff_control, cutoff_release):
    root = Path(root).resolve(strict=True)
    permission, plan = bound(authorization), read(root / 'PLAN.json')
    require(permission.get('purpose') == MODE and permission.get('authorized') is True
            and permission.get('allow_missing_postcommit_readouts') is True
            and permission.get('no_train_replay') is True and permission.get('no_fake_complete') is True
            and permission.get('dispatch_authorized') is False and str(root) in permission['roots'],
            'Main_scoped_postcommit_disposition_not_dispatch_authority')
    require(plan['physical'] in boundary.prior.UUIDS
            and str(root) == boundary.prior.ROOT_TEMPLATE.format(plan['physical'])
            and plan['uuid'] == boundary.prior.UUIDS[plan['physical']], 'exact_owned_route_root_UUID')
    require(time.time() < min(boundary.TRAIN_END, plan['bounds']['hard_end_unix'],
                             plan['bounds']['lease_end_unix']-21600), 'original_lifetime')
    processes = verify_owned_release(root, plan, cutoff_control, cutoff_release)
    directory = root / DIRECTORY
    require(not directory.exists(), 'immutable_recovery_capture_no_overwrite')
    with (root / 'RESERVATIONS.jsonl').open('r') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        snapshot = inspect_snapshot(root, plan)
        require(snapshot['checkpoint']['path_sha256'] == permission['canonical_checkpoint_sha256'],
                'exact_Main_committed_checkpoint')
        terminals = sorted(root.glob('CRASH_*.json'))
        require(terminals and read(terminals[-1]).get('finished_unix') is not None,
                'actual_retained_native_crash_required')
        evaluations = {scope: ('COMPLETE' if entry['status']=='ORIGINAL_COMPLETE' else
                       ('NOT_ATTEMPTED' if entry['reason']=='NOT_STARTED_BEFORE_CRASH' else 'INTERRUPTED'))
                       for scope, entry in snapshot['missing_readouts'].items()}
        evidence = [ref(root/name) for name in snapshot['preserved_files']
                    if name.startswith((f"readout_{snapshot['sleep']:04d}/", 'open_readouts/'))]
        require(evidence, 'actual_interrupted_evaluation_evidence')
        disposition = dict(schema='R118_POSTCOMMIT_EVAL_DISPOSITION_V1', mode=MODE,
            status='TERMINAL_POSTCOMMIT_EVALUATION', branch=plan['shared_learner']['branch'], generation=1,
            root=str(root), authorization=authorization, cutoff_control=cutoff_control, cutoff_release=cutoff_release,
            checkpoint_sha256=snapshot['checkpoint']['path_sha256'], scopes=snapshot['missing_readouts'],
            committed_sleep=snapshot['common_complete'], accepted_submission=snapshot['submission'],
            native_terminal=ref(terminals[-1]), evaluations=evaluations, evaluation_evidence=evidence, replay_train=False,
            reservations=snapshot['eval_reservations'], process_identities=[item['identity'] for item in processes],
            replay=False, counted_as_success=False, captured_unix=time.time())
        write(directory / 'READOUT_DISPOSITION.json', disposition)
        cursor = dict(schema='R118_POSTCOMMIT_RECOVERED_CURSOR_V1', status='TRAIN_COMMITTED_EVAL_MISSING_CURSOR_SETTLED',
            root=str(root), trained_cycle=snapshot['completed_cycle'], next_cycle=snapshot['next_cycle'],
            branch=plan['shared_learner']['branch'], accepted_generation=0,
            accepted_submission_sha256=snapshot['submission']['sha256'],
            action='NEXT_NEW_CYCLE_AFTER_CANONICAL_BOOTSTRAP', completed_train_cycle=snapshot['completed_cycle'],
            pending_train_calls=[], pending_train_submissions=[],
            native_used=snapshot['charged'].get('NATIVE', 0), parent_used=snapshot['charged'].get('PARENT', 0),
            trained_generation=0, next_generation=1, checkpoint_sha256=snapshot['checkpoint']['path_sha256'],
            submission=snapshot['submission'], encoding=snapshot['encoding'],
            accepted_train_hashes=snapshot['accepted_train_hashes'], rejected_train_hashes=snapshot['rejected_train_hashes'],
            charged=snapshot['charged'], no_train_replay=True, optimizer_updates_replayed=0,
            original_cycle_COMPLETE_created=False, readout_disposition=ref(directory / 'READOUT_DISPOSITION.json'))
        write(directory / 'SETTLED_CURSOR.json', cursor)
        snapshot.update(recovery_mode=MODE, authorization=authorization,
            readout_disposition=ref(directory / 'READOUT_DISPOSITION.json'), settled_cursor=ref(directory / 'SETTLED_CURSOR.json'))
        for name in ('READOUT_DISPOSITION.json', 'SETTLED_CURSOR.json'):
            snapshot['preserved_files'][str((directory/name).relative_to(root))] = sha(directory/name)
        write(directory / 'BOUNDARY.json', snapshot)
        release = dict(schema=SCHEMA, mode=MODE, status='RELEASED', root=str(root), boundary=ref(directory/'BOUNDARY.json'),
            authorization=authorization, cutoff_control=cutoff_control, cutoff_disposition=cutoff_release,
            actor=next(item['identity'] for item in processes if item['role']=='actor'),
            supervisor=next(item['identity'] for item in processes if item['role']=='supervisor'),
            predecessors=[item['identity'] for item in processes], released_unix=bound(cutoff_release)['released_unix'],
            observed_unix=time.time(), signals_issued=0, gpu_free_not_inferred=True, original_bounds=plan['bounds'],
            no_quota_reset=True, no_replay=True, readouts_missing_not_success=True)
        write(directory / 'RELEASED.json', release)
    return ref(directory/'RELEASED.json')


def validate_release(root, reference):
    root = Path(root).resolve(strict=True)
    release = bound(reference)
    require(release['schema'] == SCHEMA and release['mode'] == MODE and release['root'] == str(root)
            and release['status'] == 'RELEASED' and release['signals_issued'] == 0, 'actual_crashed_boundary_receipt')
    snapshot = bound(release['boundary'])
    bound(release['authorization'])
    bound(release['cutoff_disposition'])
    for name, digest in snapshot['preserved_files'].items():
        require(sha(root/name) == digest, 'preserved_crash_boundary_bytes')
    require(all(absent(identity) for identity in release['predecessors']), 'old_process_identity_must_remain_exited')
    state, unused = boundary.committed(read(root/'PLAN.json')['shared_learner']['root'])
    require(state == snapshot['state'], 'exact_committed_state_at_recovery')
    require(bound(snapshot['settled_cursor'])['no_train_replay'] is True
            and bound(snapshot['readout_disposition'])['counted_as_success'] is False, 'explicit_missing_not_complete')
    return snapshot


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('phase', choices=('capture', 'verify'))
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--authorization', type=Path)
    parser.add_argument('--cutoff-control', type=Path)
    parser.add_argument('--cutoff-release', type=Path)
    parser.add_argument('--release', type=Path)
    args = parser.parse_args()
    if args.phase == 'capture':
        result = capture(args.root, ref(args.authorization), ref(args.cutoff_control), ref(args.cutoff_release))
    else:
        snapshot = validate_release(args.root, ref(args.release))
        result = dict(status='VALID_CRASHED_POSTCOMMIT_BOUNDARY', next_cycle=snapshot['next_cycle'],
                      checkpoint=snapshot['checkpoint'], counted_as_readout_success=False)
    print(json.dumps(result, sort_keys=True))


if __name__ == '__main__':
    main()
