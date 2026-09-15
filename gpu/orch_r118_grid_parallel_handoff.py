"""Read-only prospective GRID boundary validation; never signals or arms actors."""

from copy import deepcopy
import os
from pathlib import Path
import signal
import time

from gpu import orch_r118_grid_shared_run as run
from gpu import orch_r118_parallel_consolidation as parallel


shared, require = run.shared, run.require
TERMINAL = 'R118_SHARED_REPAIR_TERMINAL.json'
SCHEMA = 'R118_GRID_PARALLEL_BOUNDARY_V1'


def reference(path):
    path = Path(path).resolve(strict=True)
    return dict(path=str(path), sha256=shared.sha(path))


def checked(item):
    path = parallel.checked_file(item['path'], item['sha256'])
    return shared.read(path)


def central_identity(identity):
    result = dict(boot_id=identity['boot_id'])
    for name in ('pid', 'start_ticks'):
        value = identity[name]
        require(type(value) is int or (type(value) is str and value.isascii() and value.isdigit()),
                'exact_decimal_process_identity')
        require(int(value) > 0, 'positive_process_identity')
        result[name] = int(value)
    return result


def inside(root, relative):
    path = Path(relative)
    require(not path.is_absolute() and '..' not in path.parts, 'relative_preserved_path')
    target = (root / path).resolve(strict=True)
    require(target.is_relative_to(root), 'preserved_path_escape')
    return target


def repaired_source(root, ready_reference):
    root = Path(root).resolve(strict=True)
    require(Path(ready_reference['path']).resolve() == root / 'shared_repair_v1/READY.json',
            'actual_repair_READY_not_original_failed_era')
    ready = checked(ready_reference)
    require(ready['root'] == str(root) and ready['terminal_filename'] == TERMINAL,
            'actual_repair_terminal_binding')
    bundle = Path(ready['bundle']).resolve(strict=True)
    manifest_path = bundle / 'MANIFEST.json'
    parallel.checked_file(manifest_path, ready['manifest_sha256'])
    manifest = shared.read(manifest_path)
    require(manifest['files']['orch_r118_grid_shared_repair.py'] == ready['source_sha256'],
            'actual_repaired_executable')
    for relative, digest in manifest['files'].items():
        parallel.checked_file(inside(bundle, relative), digest)
    frozen = Path(manifest['frozen_source']).resolve(strict=True)
    for relative, digest in manifest['frozen_files'].items():
        parallel.checked_file(inside(frozen, relative), digest)
    return ready


def committed(session):
    state = run.client.current(session)
    require(type(state['generation']) is int and state['generation'] > 0,
            'first_serial_sleep_must_be_COMMITTED')
    checkpoint = shared.checked_checkpoint(state['checkpoint'])
    document = shared.read(checkpoint['path'])
    require(document['complete'] is True and document['adapter'] == session['adapter']
            and document['optimizer_rng_sha256'] == checkpoint['optimizer_path_sha256'],
            'committed_adapter_and_owner_optimizer')
    folder = Path(session['shared_root']) / f"generation_{state['generation'] - 1:06d}/sleep"
    require(shared.read(folder / 'COMPLETE.json')['state'] == state,
            'complete_binds_current_state')
    require(not (folder / 'POST_COMMIT_FAILED.json').exists(), 'post_commit_failure_unresolved')
    return state


def snapshot(root, *, session, cycle, ready_reference, native_identity):
    root = Path(root).resolve(strict=True)
    require(session['branch'] in ('F4', 'A4') and session['branch_root'] == str(root),
            'owned_grid_session')
    ready = repaired_source(root, ready_reference)
    loaded = shared.read(root / 'shared_repair_v1/LOADED.json')
    require(loaded['process'] == [native_identity['boot_id'], native_identity['pid'],
                                 native_identity['start_ticks']], 'actual_repaired_native_identity')
    state = committed(session)
    complete_path = root / 'cycles' / f'{cycle:04d}' / 'CYCLE_COMPLETE.json'
    boundary = run.capture_boundary(root, complete_path)
    complete = shared.read(complete_path)
    require(complete['shared_generation'] == session['generation'] and
            complete['shared_checkpoint_sha256'] == session['checkpoint_sha256'],
            'cycle_completed_on_committed_child')
    reloaded_path = root / 'shared_cycles' / f'{cycle:04d}' / 'RELOADED.json'
    reloaded = shared.read(reloaded_path)
    require(reloaded['generation'] == session['generation'] and
            reloaded['checkpoint_sha256'] == session['checkpoint_sha256'] and
            reloaded['resident_reload'] is True, 'actual_resident_reload_required')
    dev = root / 'readouts' / f'{cycle:04d}' / 'dev'
    started, finished = shared.read(dev / 'STARTED.json'), shared.read(dev / 'COMPLETE.json')
    binding = run.client.call_binding(session)
    require(finished['status'] == 'COMPLETE' and finished['scope'] == 'dev' and
            finished['cycle'] == cycle and finished['fresh_process'] is True and
            finished['parent_calls'] == finished['optimizer_steps'] == 0 and
            finished['carry_access'] is False and finished['readout_open_excluded'] is True and
            started['parent'] is False and started['carry_access'] is False and
            started['pid'] != native_identity['pid'] and
            started['shared_child'] == finished['shared_child'] == binding and
            started['started_unix'] <= finished['finished_unix'] <= complete['finished_unix'],
            'fresh_parent_free_completed_DEV_required')
    common = Path(session['shared_root'])
    generation = session['generation']
    require(not (common / f'generation_{generation:06d}' / f"{session['branch']}.json").exists(),
            'next_generation_already_submitted_no_replay')
    require(not (common / f'generation_{generation:06d}/sleep/START.json').exists(),
            'current_generation_sleep_already_started')
    require(not (root / 'shared_cycles' / f'{cycle + 1:04d}' / 'COLLECTION.json').exists(),
            'next_cycle_already_started')
    submitted_path = root / 'shared_cycles' / f'{cycle:04d}' / 'SUBMITTED.json'
    submitted = shared.read(submitted_path)
    require(Path(submitted['packet']['path']).resolve() == root / 'shared_cycles' /
            f'{cycle:04d}' / 'PACKET.json', 'own_exact_packet_path')
    packet = checked(submitted['packet'])
    previous = common / f'generation_{generation - 1:06d}' / f"{session['branch']}.json"
    previous_document = shared.read(previous)
    require(submitted['submission']['path'] == str(previous) and
            submitted['submission']['sha256'] == shared.sha(previous), 'actual_submission_receipt')
    require(packet['cycle'] == cycle and packet['session']['generation'] == generation - 1 and
            previous_document['generation'] == generation - 1 and
            previous_document['branch'] == session['branch'] and
            packet['rows'] == previous_document['rows'] and
            packet['episode_ids'] == previous_document['episode_ids'], 'exact_previous_submission')
    paths = [root / name for name in ('CONFIG.json', 'SHARED_ACTIVATION.json',
             'SHARED_TERMINAL.json', 'shared_repair_v1/READY.json', 'shared_repair_v1/LOADED.json',
             'LEDGER.jsonl', 'CARRY.json')]
    paths += [complete_path, reloaded_path, submitted_path, Path(submitted['packet']['path']),
              Path(boundary['train_complete']['path']), dev / 'STARTED.json', dev / 'COMPLETE.json']
    for folder in ('parent_queue', 'parent_received', 'triples'):
        paths.extend(sorted((root / folder).rglob('*.json')))
    if (root / TERMINAL).exists():
        paths.append(root / TERMINAL)
    preserved = dict(boundary['captures'])
    preserved.update({str(path.relative_to(root)): shared.sha(path) for path in paths})
    result = dict(schema=SCHEMA, status='SETTLED_OBSERVATION_NOT_RELEASE', root=str(root),
        branch=session['branch'], session=deepcopy(session), completed_cycle=cycle, next_cycle=cycle + 1,
        state_sha256=shared.sha(common / 'STATE.json'), repaired_ready=ready_reference,
        terminal_filename=TERMINAL, identity=deepcopy(native_identity), preserved_files=preserved,
        settled_inventory={folder: sorted(str(path.relative_to(root)) for path in
            (root / folder).rglob('*.json')) for folder in ('parent_queue', 'parent_received', 'triples')},
        previous_submission=reference(previous), bounds=ready['bounds'],
        native_used=boundary['native_charged'], parent_used=boundary['parent_charged'],
        rng_provenance='PREDECESSOR_RANK_RNG_NOT_SAVED_NO_RESTORE_CLAIM',
        activation_authorized=False, source_era='REPAIRED_SERIAL_TO_PROSPECTIVE_PARALLEL')
    validate_snapshot(result)
    require(state == run.client.current(session), 'state_changed_during_snapshot')
    return result


def validate_snapshot(document):
    require(document['schema'] == SCHEMA and document['activation_authorized'] is False,
            'observation_never_activation')
    root = Path(document['root']).resolve(strict=True)
    require(document['terminal_filename'] == TERMINAL, 'do_not_use_old_FAILED_terminal')
    repaired_source(root, document['repaired_ready'])
    for name, digest in document['preserved_files'].items():
        parallel.checked_file(inside(root, name), digest)
    for folder, expected in document['settled_inventory'].items():
        require(sorted(str(path.relative_to(root)) for path in (root / folder).rglob('*.json')) == expected,
                'parent_or_triple_arrived_after_snapshot')
    checked(document['previous_submission'])
    committed(document['session'])
    parallel.checked_file(Path(document['session']['shared_root']) / 'STATE.json',
                          document['state_sha256'])
    require(document['next_cycle'] == document['completed_cycle'] + 1, 'cursor_must_advance_once')
    if document.get('recovery_mode') == 'PENDING_CONSOLIDATION':
        validate_pending(document)
    else:
        require(not (root / 'shared_cycles' / f"{document['next_cycle']:04d}" / 'COLLECTION.json').exists(),
                'cursor_became_busy')
    if document.get('recovery_mode') == 'CRASHED_POSTCOMMIT':
        validate_recovery(document)
    return document


def pending_snapshot(root, *, session, cycle, ready_reference, native_identity, output):
    root, output = Path(root).resolve(strict=True), Path(output).resolve()
    require(output.is_relative_to(root) and not output.exists(), 'new_own_pending_cursor')
    require(session['branch'] in ('F4', 'A4') and session['branch_root'] == str(root), 'owned_grid_session')
    ready = repaired_source(root, ready_reference)
    loaded = shared.read(root / 'shared_repair_v1/LOADED.json')
    require(loaded['process'] == [native_identity['boot_id'], native_identity['pid'],
                                 int(native_identity['start_ticks'])], 'actual_repaired_native_identity')
    state = committed(session)
    require(state['generation'] == session['generation'] and state['checkpoint'] == session['checkpoint'],
            'exact_pending_canonical_child')
    prior_cycle = cycle - 1
    prior = root / 'cycles' / f'{prior_cycle:04d}' / 'CYCLE_COMPLETE.json'
    completed = shared.read(prior)
    require(completed['shared_generation'] == session['generation'] and
            completed['shared_checkpoint_sha256'] == session['checkpoint_sha256'], 'prior_cycle_on_canonical_child')
    reloaded_path = root / 'shared_cycles' / f'{prior_cycle:04d}' / 'RELOADED.json'
    reload = shared.read(reloaded_path)
    require(reload['resident_reload'] is True and reload['generation'] == session['generation'] and
            reload['checkpoint_sha256'] == session['checkpoint_sha256'], 'prior_actual_canonical_reload')
    dev = root / 'readouts' / f'{prior_cycle:04d}' / 'dev'
    started, finished = shared.read(dev / 'STARTED.json'), shared.read(dev / 'COMPLETE.json')
    require(finished['status'] == 'COMPLETE' and finished['fresh_process'] is True and
            finished['scope'] == 'dev' and finished['cycle'] == prior_cycle and
            finished['parent_calls'] == finished['optimizer_steps'] == 0 and finished['carry_access'] is False and
            finished['readout_open_excluded'] is True and started['parent'] is False and
            started['carry_access'] is False and started['pid'] != native_identity['pid'] and
            started['shared_child'] == finished['shared_child'] == run.client.call_binding(session) and
            started['started_unix'] <= finished['finished_unix'] <= completed['finished_unix'],
            'genuine_prior_fresh_DEV_not_pending_cycle_fake')
    rows = run.read_ledger(root)
    require(rows and all(row['cycle'] <= cycle for row in rows), 'no_later_charged_cycle')
    for kind in ('NATIVE', 'PARENT'):
        numbers = [row['number'] for row in rows if row['kind'] == kind]
        require(numbers == list(range(1, len(numbers) + 1)), 'preserve_contiguous_charged_cursors')
    for row in rows:
        require(row['kind'] in ('NATIVE', 'PARENT'), 'known_ledger_charge')
        if row['cycle'] != cycle:
            continue
        if row['kind'] == 'PARENT':
            require(shared.read(root / 'parent_received' / f'P{row["number"]:04d}.json').get('disposition')
                    is not None, 'pending_parent_unsettled')
        else:
            require(row['split'] == 'TRAIN' and not row.get('attached_readout'), 'only_TRAIN_before_pending_sleep')
            capture = shared.read(root / 'calls' / f'N{row["number"]:05d}.json')
            require(capture['status'] == 'COMPLETE' and all(capture[name] == row[name] for name in
                ('number', 'cycle', 'task_id', 'split', 'purpose')), 'pending_TRAIN_must_be_terminal')
    train = shared.read(root / 'cycles' / f'{cycle:04d}' / 'TRAIN_COMPLETE.json')
    require(len(train['outcomes']) == 2 and len({item['task_id'] for item in train['outcomes']}) == 2 and
            all(item['split'] == 'TRAIN' for item in train['outcomes']) and
            train['carry'] == shared.read(root / 'CARRY.json'), 'pending_exact_two_completed_episodes_and_carry')
    submitted_ref = reference(root / 'shared_cycles' / f'{cycle:04d}' / 'SUBMITTED.json')
    submitted = checked(submitted_ref)
    current = Path(session['shared_root']) / f"generation_{session['generation']:06d}"
    accepted_ref = reference(current / f"{session['branch']}.json")
    require(submitted['submission']['path'] == accepted_ref['path'] and
            submitted['submission']['sha256'] == accepted_ref['sha256'], 'exact_pending_COMMON_submission')
    packet, accepted = checked(submitted['packet']), checked(accepted_ref)
    require(Path(submitted['packet']['path']) == root / 'shared_cycles' / f'{cycle:04d}' / 'PACKET.json' and
            packet['cycle'] == cycle and packet['session']['generation'] == accepted['generation'] ==
            session['generation'] and accepted['branch'] == session['branch'] and
            accepted['checkpoint_sha256'] == session['checkpoint_sha256'] and
            packet['rows'] == accepted['rows'] and packet['episode_ids'] == accepted['episode_ids'] and
            len(set(accepted['episode_ids'])) == len(accepted['episode_ids']) == 2 and accepted['rows'],
            'exact_pending_original_packet')
    require(not (current / 'sleep/START.json').exists() and
            not (root / 'shared_cycles' / f'{cycle + 1:04d}' / 'COLLECTION.json').exists() and
            not (root / 'cycles' / f'{cycle:04d}' / 'CYCLE_COMPLETE.json').exists(),
            'pending_before_sleep_not_completed_or_later_cycle')
    folders = ('calls', 'readout_calls', 'sealed_readout_calls', 'parent_queue', 'parent_received', 'triples')
    paths = [root / name for name in ('CONFIG.json', 'SHARED_ACTIVATION.json', 'SHARED_TERMINAL.json',
        'shared_repair_v1/READY.json', 'shared_repair_v1/LOADED.json', 'LEDGER.jsonl', 'CARRY.json')]
    if (root / TERMINAL).exists():
        paths.append(root / TERMINAL)
    paths += [path for folder in folders for path in sorted((root / folder).rglob('*.json'))]
    for selected in (prior_cycle, cycle):
        paths += list((root / 'cycles' / f'{selected:04d}').glob('*.json'))
        paths += list((root / 'shared_cycles' / f'{selected:04d}').glob('*.json'))
    paths += [dev / 'STARTED.json', dev / 'COMPLETE.json']
    preserved = {str(path.relative_to(root)): shared.sha(path) for path in paths}
    native_used, parent_used = (sum(row['kind'] == kind for row in rows) for kind in ('NATIVE', 'PARENT'))
    cursor = dict(schema='R118_PENDING_CONSOLIDATION_CURSOR_V1', root=str(root), branch=session['branch'],
        generation=session['generation'], checkpoint_sha256=session['checkpoint_sha256'],
        completed_train_cycle=cycle, cycle=cycle, next_cycle=cycle + 1,
        accepted_submission=accepted_ref, submitted=submitted_ref, native_used=native_used, parent_used=parent_used,
        inflight_native_calls=[], inflight_parent_calls=[], action='RESUME_PENDING_PARALLEL_BOUNDARY_BEFORE_NEW_CALLS',
        replay_train=False, resubmit=False)
    train_ref = reference(root / 'cycles' / f'{cycle:04d}' / 'TRAIN_COMPLETE.json')
    pending_doc = dict(schema='R118_SETTLED_PENDING_CONSOLIDATION_V1', status='SETTLED_PENDING_CONSOLIDATION',
        root=str(root), branch=session['branch'], generation=session['generation'],
        checkpoint_sha256=session['checkpoint_sha256'], cycle=cycle, episode_ids=accepted['episode_ids'],
        episode_completions=[dict(episode_id=episode_id, status='COMPLETE', evidence=train_ref)
                             for episode_id in accepted['episode_ids']], rows=submitted['packet'],
        terminal_calls=[dict(reference(root / 'calls' / f'N{row["number"]:05d}.json'), status='COMPLETE')
                        for row in rows if row['kind'] == 'NATIVE' and row['cycle'] == cycle],
        submission=accepted_ref, trained=False, replay_calls=False)
    pending_path = output.with_name('PENDING_CONSOLIDATION.json')
    require(not pending_path.exists(), 'new_pending_disposition_no_overwrite')
    shared.write(pending_path, pending_doc)
    shared.write(output, cursor)
    preserved[str(output.relative_to(root))] = shared.sha(output)
    preserved[str(pending_path.relative_to(root))] = shared.sha(pending_path)
    result = dict(schema=SCHEMA, status='SETTLED_PENDING_CONSOLIDATION_NOT_RELEASE', root=str(root),
        branch=session['branch'], session=deepcopy(session), completed_cycle=cycle, next_cycle=cycle + 1,
        state_sha256=shared.sha(Path(session['shared_root']) / 'STATE.json'), repaired_ready=ready_reference,
        terminal_filename=TERMINAL, identity=deepcopy(native_identity), preserved_files=preserved,
        settled_inventory={folder: sorted(str(path.relative_to(root)) for path in (root / folder).rglob('*.json'))
                           for folder in folders}, previous_submission=accepted_ref, bounds=ready['bounds'],
        native_used=native_used, parent_used=parent_used, activation_authorized=False,
        recovery_mode='PENDING_CONSOLIDATION', pending_submission=submitted_ref,
        owner_boundary=dict(committed_checkpoint_sha256=session['checkpoint_sha256'],
            mounted_checkpoint_sha256=session['checkpoint_sha256'], canonical_reload_required=True,
            settled_pending_consolidation=reference(pending_path),
            settled_cursor=reference(output)), rng_provenance='PREDECESSOR_RANK_RNG_NOT_SAVED_NO_RESTORE_CLAIM')
    validate_snapshot(result)
    return result


def validate_pending(document):
    session = document['session']
    root, cycle = Path(document['root']), document['completed_cycle']
    current = Path(session['shared_root']) / f"generation_{session['generation']:06d}"
    require(not (current / 'sleep/START.json').exists() and
            not (root / 'shared_cycles' / f'{cycle + 1:04d}' / 'COLLECTION.json').exists(),
            'pending_boundary_became_busy')
    submitted = checked(document['pending_submission'])
    require(Path(submitted['submission']['path']) == current / f"{session['branch']}.json" and
            submitted['submission']['sha256'] == shared.sha(current / f"{session['branch']}.json"),
            'pending_accepted_submission_unchanged')
    cursor = checked(document['owner_boundary']['settled_cursor'])
    require(cursor['action'] == 'RESUME_PENDING_PARALLEL_BOUNDARY_BEFORE_NEW_CALLS' and
            cursor['generation'] == session['generation'] and cursor['next_cycle'] == cycle + 1 and
            cursor['submitted'] == document['pending_submission'] and cursor['resubmit'] is False and
            cursor['replay_train'] is False, 'pending_cursor_never_recollects')
    pending = checked(document['owner_boundary']['settled_pending_consolidation'])
    require(pending['cycle'] == cycle and pending['generation'] == session['generation'] and
            pending['submission']['sha256'] == submitted['submission']['sha256'] and
            pending['trained'] is False and pending['replay_calls'] is False, 'exact_untrained_pending_disposition')


def recovery_snapshot(root, *, session, cycle, ready_reference, native_identity, guard_identity, output):
    root, output = Path(root).resolve(strict=True), Path(output).resolve()
    require(output.is_relative_to(root) and not output.exists(), 'new_own_recovery_evidence_directory')
    require(session['branch'] in ('F4', 'A4') and session['branch_root'] == str(root), 'owned_grid_session')
    ready = repaired_source(root, ready_reference)
    loaded = shared.read(root / 'shared_repair_v1/LOADED.json')
    require(loaded['process'] == [native_identity['boot_id'], native_identity['pid'],
                                 int(native_identity['start_ticks'])], 'actual_repaired_native_identity')
    launch = shared.read(root / 'shared_repair_v1/CPU_LAUNCH.json')['identity']
    require(all(str(launch[key]) == str(guard_identity[key]) for key in ('boot_id', 'pid', 'start_ticks')),
            'actual_repaired_guard_identity')
    for identity in (native_identity, guard_identity):
        parallel.predecessor_released(central_identity(identity))
    terminal = root / TERMINAL
    require(shared.read(terminal)['status'] == 'FAILED', 'authentic_failed_repair_terminal_required')
    state = committed(session)
    require(state['generation'] == session['generation'] and state['checkpoint'] == session['checkpoint'],
            'recovery_exact_current_session')
    common = Path(session['shared_root'])
    current = common / f"generation_{session['generation']:06d}"
    require(not (current / f"{session['branch']}.json").exists() and
            not (current / 'sleep/START.json').exists(), 'no_current_generation_replay_or_discard')
    rows = run.read_ledger(root)
    require(rows and all(row['cycle'] <= cycle for row in rows), 'no_later_charged_cycle')
    require(not (root / 'shared_cycles' / f'{cycle + 1:04d}' / 'COLLECTION.json').exists(),
            'no_later_collection_to_discard')
    for kind in ('NATIVE', 'PARENT'):
        numbers = [row['number'] for row in rows if row['kind'] == kind]
        require(numbers == list(range(1, len(numbers) + 1)), 'preserve_contiguous_charged_cursors')
    for row in rows:
        require(row['kind'] in ('NATIVE', 'PARENT'), 'known_ledger_charge')
        if row['cycle'] != cycle:
            continue
        if row['kind'] == 'PARENT':
            require(shared.read(root / 'parent_received' / f'P{row["number"]:04d}.json').get('disposition')
                    is not None, 'no_pending_parent_claim_to_discard')
        elif row['split'] == 'TRAIN' and not row.get('attached_readout'):
            capture = shared.read(root / 'calls' / f'N{row["number"]:05d}.json')
            require(capture['status'] == 'COMPLETE' and all(capture[name] == row[name] for name in
                    ('number', 'cycle', 'task_id', 'split', 'purpose')), 'no_unfinished_TRAIN_recovery')
    train_path = root / 'cycles' / f'{cycle:04d}' / 'TRAIN_COMPLETE.json'
    train = shared.read(train_path)
    require(len(train['outcomes']) == 2 and len({item['task_id'] for item in train['outcomes']}) == 2
            and all(item['split'] == 'TRAIN' for item in train['outcomes']) and
            train['carry'] == shared.read(root / 'CARRY.json'), 'exact_completed_TRAIN_and_carry')
    submitted = shared.read(root / 'shared_cycles' / f'{cycle:04d}' / 'SUBMITTED.json')
    previous = common / f"generation_{session['generation'] - 1:06d}" / f"{session['branch']}.json"
    require(Path(submitted['submission']['path']) == previous and
            submitted['submission']['sha256'] == shared.sha(previous), 'exact_accepted_previous_submission')
    packet, accepted = checked(submitted['packet']), shared.read(previous)
    require(Path(submitted['packet']['path']) == root / 'shared_cycles' / f'{cycle:04d}' / 'PACKET.json' and
            packet['cycle'] == cycle and packet['session']['generation'] == session['generation'] - 1 and
            packet['rows'] == accepted['rows'] and packet['episode_ids'] == accepted['episode_ids'],
            'original_two_episode_packet_already_trained')
    dev = root / 'readouts' / f'{cycle:04d}' / 'dev'
    require(not (dev / 'COMPLETE.json').exists(), 'use_clean_boundary_for_completed_DEV')
    started = dev / 'STARTED.json'
    if started.exists():
        require(not Path(f"/proc/{shared.read(started)['pid']}").exists(), 'old_DEV_process_must_exit')
    paths = [root / name for name in ('CONFIG.json', 'SHARED_ACTIVATION.json', 'SHARED_TERMINAL.json',
        TERMINAL, 'shared_repair_v1/READY.json', 'shared_repair_v1/LOADED.json',
        'shared_repair_v1/CPU_LAUNCH.json', 'LEDGER.jsonl', 'CARRY.json')]
    folders = ('calls', 'readout_calls', 'sealed_readout_calls', 'parent_queue', 'parent_received', 'triples')
    paths += [path for folder in folders for path in sorted((root / folder).rglob('*.json'))]
    paths += list((root / 'cycles' / f'{cycle:04d}').glob('*.json'))
    paths += list((root / 'shared_cycles' / f'{cycle:04d}').glob('*.json'))
    paths += list((root / 'readouts' / f'{cycle:04d}').rglob('*.json'))
    evidence = [terminal] + ([started] if started.exists() else [])
    for path in (root / 'shared_repair_v1').glob('*.log'):
        paths.append(path)
        evidence.append(path)
    preserved = {str(path.relative_to(root)): shared.sha(path) for path in paths}
    native_used = sum(row['kind'] == 'NATIVE' for row in rows)
    parent_used = sum(row['kind'] == 'PARENT' for row in rows)
    disposition = dict(schema='R118_POSTCOMMIT_EVAL_DISPOSITION_V1', status='TERMINAL_POSTCOMMIT_EVALUATION',
        root=str(root), branch=session['branch'], generation=session['generation'],
        checkpoint_sha256=session['checkpoint_sha256'], accepted_submission=reference(previous),
        committed_sleep=reference(previous.parent / 'sleep/COMPLETE.json'), native_terminal=reference(terminal),
        evaluations=dict(DEV='FAILED' if started.exists() else 'NOT_ATTEMPTED', OPEN='NOT_ATTEMPTED'),
        evaluation_evidence=[reference(path) for path in evidence], replay_train=False)
    require(not any(row['cycle'] == cycle and row['purpose'].startswith('open') and
                    row.get('attached_readout') for row in rows if row['kind'] == 'NATIVE'),
            'OPEN_disposition_must_match_uncharged_boundary')
    cursor = dict(schema='R118_POSTCOMMIT_RECOVERED_CURSOR_V1', root=str(root), branch=session['branch'],
        accepted_generation=session['generation'] - 1, accepted_submission_sha256=shared.sha(previous),
        checkpoint_sha256=session['checkpoint_sha256'], completed_train_cycle=cycle, next_cycle=cycle + 1,
        native_used=native_used, parent_used=parent_used, pending_train_calls=[], pending_train_submissions=[],
        action='NEXT_NEW_CYCLE_AFTER_CANONICAL_BOOTSTRAP')
    shared.write(output / 'EVAL_DISPOSITION.json', disposition)
    shared.write(output / 'CURSOR.json', cursor)
    for name in ('EVAL_DISPOSITION.json', 'CURSOR.json'):
        preserved[str((output / name).relative_to(root))] = shared.sha(output / name)
    owner_boundary = dict(committed_checkpoint_sha256=session['checkpoint_sha256'],
        mounted_checkpoint_sha256=None, canonical_reload_required=True,
        postcommit_eval_disposition=reference(output / 'EVAL_DISPOSITION.json'),
        settled_cursor=reference(output / 'CURSOR.json'))
    result = dict(schema=SCHEMA, status='FAILED_EVAL_OBSERVATION_NOT_RELEASE', root=str(root),
        branch=session['branch'], session=deepcopy(session), completed_cycle=cycle, next_cycle=cycle + 1,
        state_sha256=shared.sha(common / 'STATE.json'), repaired_ready=ready_reference,
        terminal_filename=TERMINAL, identity=deepcopy(native_identity), guard_identity=deepcopy(guard_identity),
        preserved_files=preserved, settled_inventory={folder: sorted(str(path.relative_to(root)) for path in
            (root / folder).rglob('*.json')) for folder in folders}, previous_submission=reference(previous),
        bounds=ready['bounds'], native_used=native_used, parent_used=parent_used,
        activation_authorized=False, recovery_mode='CRASHED_POSTCOMMIT', owner_boundary=owner_boundary,
        rng_provenance='PREDECESSOR_RANK_RNG_NOT_SAVED_NO_RESTORE_CLAIM')
    validate_snapshot(result)
    return result


def validate_recovery(document):
    root = Path(document['root'])
    for identity in (document['identity'], document['guard_identity']):
        parallel.predecessor_released(central_identity(identity))
    require(shared.read(root / TERMINAL)['status'] == 'FAILED', 'authentic_failed_terminal_retained')
    envelope = dict(root=str(root), next_cycle=document['next_cycle'], preserved_files=document['preserved_files'],
                    bounds=dict(native_used=document['native_used'], parent_used=document['parent_used']))
    common = document['session']['shared_root']
    parallel.postcommit_evaluation_boundary(common, document['branch'], dict(boundary=document['owner_boundary']),
        envelope, shared.read(Path(common) / 'CONFIG.json'), committed(document['session']))


def release_crashed(*, authorization, boundary_reference, output, clock=time.time):
    boundary = checked(boundary_reference)
    require(boundary.get('recovery_mode') == 'CRASHED_POSTCOMMIT', 'crashed_only_no_actor_signals')
    validate_snapshot(boundary)
    document = checked(authorization)
    require(document['schema'] == 'R118_GRID_PARALLEL_DRAIN_V1' and
            document['status'] == 'MAIN_ALL8_COORDINATED_GO' and set(document['branches']) == set(shared.BRANCHES),
            'Main_all8_release_not_candidate')
    require(document['issued_unix'] <= clock() < document['expires_unix'] <= run.grid.TRAIN_END,
            'bounded_future_release')
    own = document['branches'][boundary['branch']]
    require(own['root'] == boundary['root'] and own['ready'] == boundary['repaired_ready'] and
            own['generation'] == boundary['session']['generation'] and
            own['checkpoint_sha256'] == boundary['session']['checkpoint_sha256'] and
            own['bounds'] == boundary['bounds'] and own['native_identity'] == boundary['identity'] and
            own['guard_identity'] == boundary['guard_identity'], 'exact_authorized_crashed_branch')
    root = Path(boundary['root'])
    require(Path(output).resolve().is_relative_to(root), 'release_under_own_root')
    release = dict(status='RELEASED', root=str(root), boundary=boundary_reference,
        release=reference(root / TERMINAL), terminal_status='FAILED', not_natural_completion=False,
        predecessor_identity=boundary['identity'], guard_identity=boundary['guard_identity'],
        next_cycle=boundary['next_cycle'], authorization=authorization, released_unix=clock(),
        original_FAILED_preserved=True, parent_claims_discarded=0, calls_replayed=0, rng_restored=False,
        bounds=dict(train_end_unix=boundary['bounds']['train_end_unix'],
            hard_end_unix=boundary['bounds']['hard_end_unix'], native_used=boundary['native_used'],
            native_cap=boundary['bounds']['max_native_calls'], parent_used=boundary['parent_used'],
            parent_cap=boundary['bounds']['max_parent_calls']),
        predecessors=[central_identity(boundary['identity']), central_identity(boundary['guard_identity'])],
        preserved_files=boundary['preserved_files'])
    shared.write(Path(output) / 'RELEASE.json', release)
    return release


def supervision(certificate, *, verify_identity=parallel.live_identity):
    require(certificate['branch'] in ('F4', 'A4'), 'grid_branch_only')
    native = certificate['identity']
    retained = certificate['retained_supervision']
    require(retained['native_identity'] == native and
            retained['owner_verified_safe_for_parallel'] is True, 'authentic_native_supervision')
    require(retained['guard_identity'] != native, 'separate_guard_process')
    for identity in (native, retained['guard_identity']):
        verify_identity(identity)
    guard = checked(retained['guard_binding'])
    require(guard['native_identity'] == native and
            guard['guard_identity'] == retained['guard_identity'] and
            guard['root'] == certificate['root'] and guard['terminal_filename'] == 'R118_GRID_PARALLEL_TERMINAL.json',
            'new_guard_must_bind_successor_not_predecessor')
    require(retained['final_identity_bindings'], 'FINAL_rebind_required')
    for item in retained['final_identity_bindings']:
        verify_identity(item['identity'])
        evidence = checked(item['evidence'])
        require(evidence['native_identity'] == native and evidence['root'] == certificate['root'] and
                evidence['timer_identity'] == item['identity'] and
                evidence['old_timer_retired'] is True and
                evidence['canonical_selection_schema'] == 'R118_FINAL_SELECTION_V1' and
                evidence['evaluation_only'] is True, 'authentic_FINAL_rebind_required')
    return retained


def candidate(output, *, sources):
    require(sources and all(Path(name).is_absolute() for name in sources), 'absolute_source_closure')
    files = {str(Path(name).resolve(strict=True)): shared.sha(name) for name in sources}
    document = dict(schema='R118_GRID_PARALLEL_CANDIDATE_V1', status='CPU_ONLY_NOT_ARMED',
        source_files=files, branches=['F4', 'A4'], activation_authorized=False,
        activation_blockers=['MAIN_ALL8_GO', 'COMMITTED_RELOADED_FRESH_DEV_SETTLED_CURSOR',
            'AUTHENTIC_SUCCESSOR_GUARD_AND_FINAL_REBIND', 'EXPLICIT_INITIAL_RANK_RNG_PROVENANCE'],
        predecessor_terminal=TERMINAL, optimizer_owner='F1', local_optimizer=None,
        serial_adamw_equivalent=False, parent_wait_seconds={'F4':600, 'A4':120},
        current_actors_changed=False, current_CONFIG_changed=False)
    shared.write(output, document)
    return reference(output)


def drain_at_settled_boundary(*, authorization, root, session, cycle, ready_reference,
                             output, pending=False, clock=time.time, pause=time.sleep):
    from gpu import orch_r118_grid_final_drain as process

    root = Path(root).resolve(strict=True)
    document = checked(authorization)
    require(document['schema'] == 'R118_GRID_PARALLEL_DRAIN_V1' and
            document['status'] == 'MAIN_ALL8_COORDINATED_GO' and
            set(document['branches']) == set(shared.BRANCHES), 'Main_all8_drain_not_candidate')
    require(document['issued_unix'] <= clock() < document['expires_unix'] <= run.grid.TRAIN_END,
            'bounded_future_drain')
    own = document['branches'][session['branch']]
    require(own['root'] == str(root) and own['ready'] == ready_reference and
            own['generation'] == session['generation'] and
            own['checkpoint_sha256'] == session['checkpoint_sha256'], 'exact_authorized_repaired_branch')
    ready = repaired_source(root, ready_reference)
    require(own['bounds'] == ready['bounds'], 'no_drain_budget_change')
    config = shared.read(root / 'CONFIG.json')
    manifest = shared.read(Path(ready['bundle']) / 'MANIFEST.json')
    plan = dict(branch_root=str(root), runtime=manifest['frozen_source'], uuid=config['uuid'])
    expected = own['native_identity']
    observed = process.inspect_owned(expected['pid'], plan)
    require(process.same_process(observed, expected), 'exact_authorized_native_no_PID_reuse')
    command = (Path('/proc') / str(expected['pid']) / 'cmdline').read_bytes().split(b'\0')
    require(b'resident' in command, 'drain_only_resident_not_guard_or_readout')
    guard = process.inspect_owned(own['guard_identity']['pid'], plan)
    require(process.same_process(guard, own['guard_identity']), 'authentic_repair_guard')
    native = {key:observed[key] for key in ('boot_id', 'pid', 'start_ticks')}
    native['start_ticks'] = int(native['start_ticks'])
    descriptor = os.pidfd_open(expected['pid'])
    held = False
    try:
        require(process.same_process(process.identity(expected['pid']), observed), 'same_native_after_pidfd')
        held = process.send(descriptor, observed, signal.SIGSTOP)
        require(held, 'native_exited_before_hold')
        for unused in range(100):
            if process.identity(expected['pid'])['state'] in ('T', 't'):
                break
            pause(.01)
        require(process.identity(expected['pid'])['state'] in ('T', 't'), 'native_hold_observed')
        try:
            if pending:
                boundary = pending_snapshot(root, session=session, cycle=cycle, ready_reference=ready_reference,
                    native_identity=native, output=Path(output) / 'PENDING_CURSOR.json')
            else:
                boundary = snapshot(root, session=session, cycle=cycle, ready_reference=ready_reference,
                                    native_identity=native)
        except (ValueError, FileNotFoundError) as error:
            return dict(status='NOT_SETTLED_RESUMED', reason=str(error), released=False)
        require(clock() < document['expires_unix'], 'drain_authorization_expired')
        shared.write(Path(output) / 'BOUNDARY.json', boundary)
        process.send(descriptor, observed, signal.SIGTERM)
        process.send(descriptor, observed, signal.SIGCONT)
        held = False
        for unused in range(100):
            if process.exited(descriptor):
                break
            pause(.1)
        require(process.exited(descriptor), 'owned_native_not_exited_no_foreign_signal_or_retry')
        terminal_path = root / TERMINAL
        for unused in range(100):
            if terminal_path.exists():
                break
            pause(.1)
        require(terminal_path.exists(), 'authentic_guard_terminal_pending')
        terminal = shared.read(terminal_path)
        require(terminal['status'] in ('COMPLETE', 'FAILED'), 'actual_guard_terminal_status')
        validate_snapshot(boundary)
        release = dict(status='RELEASED', root=str(root), boundary=reference(Path(output) / 'BOUNDARY.json'),
            release=reference(terminal_path), terminal_status=terminal['status'], not_natural_completion=True,
            predecessor_identity=observed, guard_identity=guard, next_cycle=boundary['next_cycle'],
            authorization=authorization, released_unix=clock(), original_FAILED_preserved=True,
            parent_claims_discarded=0, calls_replayed=0, rng_restored=False,
            bounds=dict(train_end_unix=boundary['bounds']['train_end_unix'],
                hard_end_unix=boundary['bounds']['hard_end_unix'], native_used=boundary['native_used'],
                native_cap=boundary['bounds']['max_native_calls'], parent_used=boundary['parent_used'],
                parent_cap=boundary['bounds']['max_parent_calls']),
            predecessors=[central_identity(record) for record in (observed, guard)],
            preserved_files=boundary['preserved_files'])
        shared.write(Path(output) / 'RELEASE.json', release)
        return release
    finally:
        if held and not process.exited(descriptor):
            process.send(descriptor, observed, signal.SIGCONT)
        os.close(descriptor)
