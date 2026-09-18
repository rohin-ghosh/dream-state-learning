"""Read-only CODE custody for two settled episodes awaiting consolidation."""

from copy import deepcopy
from pathlib import Path

from gpu import orch_r118_code_parallel_handoff as handoff


io, require = handoff.io, handoff.require
MODE = 'SETTLED_PENDING_CONSOLIDATION'
ACTION = 'RESUME_PENDING_PARALLEL_BOUNDARY_BEFORE_NEW_CALLS'


def scheduled(root, cycle, episode_ids):
    root = Path(root)
    calls, sources, completions = [], [], []
    expected_task = None

    def slot(identifier, kind):
        path = root / 'reservations' / (identifier + '.json')
        require(path.exists(), 'pending_missing_scheduled_slot')
        row = io.read(path)
        terminal = ('COMPLETE', 'FAILED') if kind == 'NATIVE' else ('COMPLETE', 'SILENT', 'MISSING', 'FAILED')
        require(row['id'] == identifier and row['cycle'] == cycle and row['split'] == 'TRAIN'
            and row['kind'] == kind and row['status'] in terminal, 'pending_slot_not_terminal_TRAIN')
        calls.append(dict(handoff.ref(path), status=row['status']))
        if kind == 'NATIVE' and row['status'] == 'COMPLETE':
            require(row['task_id'] == expected_task, 'pending_source_exact_scheduled_episode')
            sources.append(handoff.ref(path))
        return row

    for index, episode_id in enumerate(episode_ids):
        expected_task = episode_id
        start = len(calls)
        prefix = f'C{cycle:03d}_E{index}'
        first = slot(prefix + '_ORIGINAL', 'NATIVE')
        if first['status'] == 'COMPLETE':
            slot(prefix + '_PARENT', 'PARENT')
            slot(prefix + '_REFLECTION', 'NATIVE')
            triple = root / 'triples' / (prefix + '.json')
            require(triple.exists() and io.read(triple)['task_id'] == episode_id
                and io.read(triple)['cycle'] == cycle, 'pending_episode_triple_missing_or_wrong')
            opened = slot(prefix + '_OPEN', 'NATIVE')
            if opened['status'] == 'COMPLETE':
                environment = root / 'environment' / (prefix + '_OPEN.json')
                require(environment.exists(), 'pending_OPEN_environment_missing')
                observed = io.read(environment)
                require(observed['source_call_sha256'] == io.sha(root / 'reservations' / (prefix + '_OPEN.json'))
                    and observed['split'] == 'TRAIN' and observed['attached_evaluation'] is False,
                    'pending_OPEN_environment_binding')
                if observed['observation']['status'] != 'NO_ENVIRONMENT_ACTION':
                    slot(prefix + '_OPEN_OBSERVE', 'NATIVE')
                parent = slot(prefix + '_OPEN_PARENT', 'PARENT')
                if parent.get('guidance'):
                    slot(prefix + '_OPEN_REFLECTION', 'NATIVE')
        completions.append(dict(episode_id=episode_id, status='COMPLETE',
            scheduled_calls=deepcopy(calls[start:]), completion_means='SCHEDULE_SETTLED_NOT_CORRECTNESS'))
    meta = slot(f'C{cycle:03d}_META', 'NATIVE')
    if meta['status'] == 'COMPLETE':
        parent = slot(f'C{cycle:03d}_META_PARENT', 'PARENT')
        if parent.get('guidance'):
            slot(f'C{cycle:03d}_META_REFLECTION', 'NATIVE')
    require({item['path'] for item in calls} == {str(path.resolve()) for path in
        (root / 'reservations').glob(f'C{cycle:03d}_*.json')}, 'pending_unexpected_cycle_slot')
    return calls, sources, completions


def snapshot(root, common, *, children=()):
    root, common = Path(root).resolve(strict=True), Path(common).resolve(strict=True)
    require(not children and not handoff.final.prior_final_attempts(root), 'pending_children_or_FINAL_attempt')
    charged, train = handoff.ledger(root)
    require(train and all(row['status'] in ('COMPLETE', 'FAILED', 'MISSING', 'SILENT') for path, row in train)
        and handoff.parents_settled(root, train), 'pending_inflight_or_unpublished_parent')
    for path in (root / 'reservations').glob('R*.json'):
        if '_FINAL_' not in path.name:
            require(io.read(path)['status'] in ('COMPLETE', 'FAILED'), 'pending_unsettled_readout')
    cycle = max(row['cycle'] for path, row in train)
    output = root / 'shared_cycles' / f'C{cycle:03d}'
    require(cycle > 1 and not (output / 'SHARED_SLEEP.json').exists()
        and not (root / 'cycles' / f'C{cycle:03d}_COMPLETE.json').exists(), 'pending_only_untrained_cycle')
    state = io.read(common / 'STATE.json')
    generation = state['generation']
    require(type(generation) is int and generation > 0, 'pending_committed_generation_required')
    current = common / f'generation_{generation:06d}'
    require(not (current / 'sleep' / 'START.json').exists(), 'pending_running_or_failed_sleep')
    previous_sleep = root / 'shared_cycles' / f'C{cycle - 1:03d}' / 'SHARED_SLEEP.json'
    previous_complete = root / 'cycles' / f'C{cycle - 1:03d}_COMPLETE.json'
    committed = io.read(common / f'generation_{generation - 1:06d}' / 'sleep' / 'COMPLETE.json')
    require(io.read(previous_sleep)['state'] == state
        and io.read(previous_complete)['shared_generation'] == generation
        and committed['state'] == state and committed['same_optimizer'] is True, 'pending_previous_actual_commit')
    dev = handoff.readout_settled(root, cycle - 1)
    require(dev is not None and handoff.checked(dev['binding'])['state'] == state
        and handoff.checked(dev['binding'])['checkpoint'] == state['checkpoint'], 'pending_previous_DEV_unsettled')
    branch = {2: 'F3', 6: 'A3'}[io.read(root / 'PLAN.json')['physical']]
    config = io.read(common / 'CONFIG.json')
    require(state['config_sha256'] == io.sha(common / 'CONFIG.json'), 'pending_config_binding')
    registry = handoff.previous.client.run.policy.tasks('TRAIN')
    episode_ids = [task['task_id'] for task in registry[(cycle - 1) * 2:cycle * 2]]
    require(len(episode_ids) == len(set(episode_ids)) == 2, 'pending_exact_two_scheduled_episodes')
    calls, sources, completions = scheduled(root, cycle, episode_ids)
    submitted_path = output / 'SHARED_SUBMISSION.json'
    unfinished = [path for path in root.glob('shared_cycles/*/SHARED_SUBMISSION.json')
        if not (path.parent / 'SHARED_SLEEP.json').exists()]
    require(unfinished == [submitted_path], 'pending_only_one_unfinished_cycle')
    submitted = io.read(submitted_path)
    require(Path(submitted['path']) == current / (branch + '.json'), 'pending_exact_common_submission_path')
    submission = handoff.checked(submitted)
    require(submission['branch'] == branch and submission['generation'] == generation
        and submission['checkpoint_sha256'] == state['checkpoint']['path_sha256']
        and submission['episode_ids'] == episode_ids, 'pending_submission_identity')
    rows = submission['rows']
    require(rows and [dict(path=row['source_call_path'], sha256=row['source_call_sha256']) for row in rows] == sources,
        'pending_exact_ordered_completed_native_sources')
    require({row['episode_id'] for row in rows} == set(episode_ids), 'pending_both_episode_rows_required')
    for row in rows:
        io.validate_row(row, config['branches'][branch], config['excluded_ids'], generation=generation,
            checkpoint_sha256=state['checkpoint']['path_sha256'])
    old_sources = {row['source_call_sha256'] for row in config.get('initial_history', {}).get(branch, [])}
    for previous_generation in range(generation):
        old = io.read(common / f'generation_{previous_generation:06d}' / (branch + '.json'))
        old_sources.update(row['source_call_sha256'] for row in old['rows'])
    require(not old_sources.intersection(row['source_call_sha256'] for row in rows), 'pending_no_already_trained_rows')
    settings = [(row['finished_unix'], path, row) for path, row in train if row.get('reflection_settings')]
    require(settings, 'pending_actual_reflection_carry')
    unused, carry_path, carry_row = max(settings, key=lambda item: item[0])
    preserved = dict(charged['preserved'])
    for path in (root / 'PLAN.json', root / 'COHORT.json', root / 'SHARED_ACTIVATION.json',
                 previous_sleep, previous_complete, submitted_path):
        preserved[str(path.relative_to(root))] = io.sha(path)
    for folder in ('parent_queue', 'parent_claude', 'triples', 'environment'):
        for path in (root / folder).rglob('*'):
            if path.is_file():
                preserved[str(path.relative_to(root))] = io.sha(path)
    preserved.update(dev['preserved'])
    for reference in (dev['complete'], dev['binding']):
        preserved[str(Path(reference['path']).relative_to(root))] = reference['sha256']
    return dict(kind=MODE, cycle=cycle, next_cycle=cycle + 1, state=state,
        state_reference=handoff.ref(common / 'STATE.json'), dev=dev, preserved_files=preserved,
        charges={key: charged[key] for key in ('native_used', 'parent_used')},
        carry=dict(reflection_settings=deepcopy(carry_row['reflection_settings']), source=handoff.ref(carry_path)),
        train_registry_sha256=handoff.previous.client.run.policy.digest(registry), charged_replay=False,
        all_pending_DEV_settled=True, pending=dict(branch=branch, submission=handoff.ref(submitted['path']),
            local_submission=handoff.ref(submitted_path), episode_ids=episode_ids, terminal_calls=calls,
            episode_completions=completions))


def publish(root, output, boundary):
    root, output = Path(root), Path(output)
    pending = boundary['pending']
    submission = handoff.checked(pending['submission'])
    rows_path = output / 'PENDING_ROWS.json'
    io.write(rows_path, submission['rows'])
    completions = []
    for index, completion in enumerate(pending['episode_completions']):
        path = output / f'EPISODE_{index}_SETTLED.json'
        io.write(path, completion)
        completions.append(dict(episode_id=completion['episode_id'], status='COMPLETE', evidence=handoff.ref(path)))
    common = dict(root=str(root), branch=pending['branch'], generation=boundary['state']['generation'],
        checkpoint_sha256=boundary['state']['checkpoint']['path_sha256'], cycle=boundary['cycle'])
    pending_path, cursor_path = output / 'PENDING.json', output / 'PENDING_CURSOR.json'
    io.write(pending_path, dict(schema='R118_SETTLED_PENDING_CONSOLIDATION_V1', status=MODE, **common,
        episode_ids=pending['episode_ids'], episode_completions=completions, rows=handoff.ref(rows_path),
        terminal_calls=[dict(item, status='MISSING' if item['status'] == 'SILENT' else item['status'])
            for item in pending['terminal_calls']], submission=pending['submission'], trained=False, replay_calls=False,
        SILENT_normalization='CENTRAL_TERMINAL_ENUM_ONLY_ORIGINAL_RESERVATION_UNCHANGED'))
    io.write(cursor_path, dict(schema='R118_PENDING_CONSOLIDATION_CURSOR_V1', **common,
        next_cycle=boundary['next_cycle'], **boundary['charges'], inflight_native_calls=[], inflight_parent_calls=[],
        action=ACTION))
    for path in [rows_path, pending_path, cursor_path] + [Path(item['evidence']['path']) for item in completions]:
        boundary['preserved_files'][str(path.relative_to(root))] = io.sha(path)
    boundary['pending_reference'], boundary['pending_cursor'] = handoff.ref(pending_path), handoff.ref(cursor_path)
    return boundary
