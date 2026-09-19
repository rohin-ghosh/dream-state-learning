"""Offline node-3 pending-sleep repair contract; never launches or clears state."""

from collections import Counter
from copy import deepcopy
import hashlib
import json
from pathlib import Path


SCHEMA = 'NODE3_ENOSPC_PENDING_SLEEP_CANDIDATE_V1'
ROW_POLICY = 'R227_ALL_AUTHENTIC_CHILD_ROWS_V1'
HARD_END = 1790272800
ROOT = Path('/localhome/local-rohing/orch_r205_node3_20260918')
ORIGINAL_GPUS = {
    'r213_math_b_fork': (2, 'GPU-41a86250-88eb-ed8a-ddfe-9d6f93515da1'),
    'r213_math_c': (4, 'GPU-f484c608-a2d4-0c26-dee1-a06cc5ae69e4'),
    'r213_r226_caption_observation_fork': (0, 'GPU-0ee6f753-c61e-e18a-8aea-acccd3042939'),
    'r213_r226_caption_perspective_fork': (3, 'GPU-e1277146-04f2-c38f-d1ae-1a98132f907e'),
    'r213_r226_caption_revision_fork': (5, 'GPU-bc211959-642d-664b-3581-42a0dbe434e9'),
    'r213_r226_caption_selfderive_fork': (6, 'GPU-1a83d900-1e95-c7b4-9b12-8117399697f8'),
    'r213_r226_caption_unparented_fork': (7, 'GPU-319224de-e668-1822-d80b-4b24d15968ae'),
}
OBSERVED_BOUNDARIES = {
    'r213_math_b_fork': (9476, 9505, 9555),
    'r213_math_c': (8937, 8966, 8976),
    'r213_r226_caption_observation_fork': (10269, 10317, 10397),
    'r213_r226_caption_perspective_fork': (10789, 10833, 10856),
    'r213_r226_caption_revision_fork': (9991, 10040, 10085),
    'r213_r226_caption_selfderive_fork': (9292, 9340, 9411),
    'r213_r226_caption_unparented_fork': (10102, 10148, 10156),
}


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True,
        separators=(',', ':'), allow_nan=False).encode()).hexdigest()


def relocated_execution_plan(original, source_root):
    destination = Path(source_root)
    require(destination.is_absolute() and '..' not in destination.parts, 'absolute_staged_source')
    execution = dict(deepcopy(original), source_root=str(destination))
    startup = original.get('startup_context')
    if startup is not None:
        require(type(startup) is dict and set(startup) == {'version', 'path', 'sha256'},
            'exact_original_startup_descriptor')
        old_root, old_path = Path(original['source_root']), Path(startup['path'])
        require(old_root.is_absolute() and old_path.is_absolute()
            and '..' not in old_root.parts and '..' not in old_path.parts,
            'original_startup_unredirected_path')
        require(old_path.is_relative_to(old_root) and old_path != old_root,
            'original_startup_inside_original_source')
        execution['startup_context'] = dict(startup,
            path=str(destination / old_path.relative_to(old_root)))
    return execution


def reference(record):
    return dict(index=record['index'], sha256=record['sha256'])


def authenticate(record, kind):
    require(record['kind'] == kind, 'wrong_record_kind')
    require(type(record['index']) is int and record['index'] >= 0, 'record_index')
    require(record['sha256'] == digest({key: value for key, value in record.items()
        if key != 'sha256'}), 'record_integrity')
    return record['document']


def saved_state(document):
    saved = document['resume_state']
    require(saved['sha256'] == digest(saved['state']), 'saved_state_integrity')
    return saved['state']


def prepare(complete, pending, suffix, *, life, plan_bytes, expected_plan_sha256):
    require(life in ORIGINAL_GPUS, 'only_seven_observed_node3_interrupted_sleeps')
    require(hashlib.sha256(plan_bytes).hexdigest() == expected_plan_sha256,
        'original_plan_bytes_required')
    plan = json.loads(plan_bytes)
    require((plan['physical'], plan['gpu_uuid']) == ORIGINAL_GPUS[life],
        'same_original_physical_gpu')
    require(plan['hard_end_unix'] == HARD_END < plan['lease_end_unix'],
        'same_original_wall_and_lease')
    require(plan['learn_row_policy'] == plan['think_act_learn']['learn_row_policy']
        == ROW_POLICY, 'all_authentic_child_rows')
    require(plan['new_presentations'] == 16 and plan['rehearsal_presentations'] == 0,
        'unchanged_sixteen_NEW_only_presentations')
    completed = authenticate(complete, 'SLEEP_COMPLETE')
    requested = authenticate(pending, 'SLEEP_REQUEST')
    prior, current = saved_state(completed), saved_state(requested)
    require(complete['journal_id'] == pending['journal_id']
        and complete['index'] < pending['index'], 'same_ordered_journal')
    require(completed['status'] == 'COMPLETE' and prior['pending'] is None,
        'durable_complete_required')
    checkpoint = completed['checkpoint']
    require(completed['checkpoint_sha256'] == checkpoint['checkpoint_sha256']
        and completed['total_optimizer_steps'] == checkpoint['optimizer_steps'],
        'committed_checkpoint_binding')
    require(prior['model_state_sha256'] == digest(checkpoint['checkpoint_sha256'])
        == current['model_state_sha256'], 'durable_not_unsaved_model_state')
    frontier = prior['sleep_frontier']
    require(type(frontier) is int and frontier == len(prior['rows'])
        and current['sleep_frontier'] == frontier, 'durable_sleep_frontier')
    require(current['rows'][:frontier] == prior['rows'], 'historical_rows_unchanged')
    require(current['sleep_receipts'] == prior['sleep_receipts'], 'no_uncommitted_sleep_promoted')
    require(current['experiment'] == prior['experiment'] == checkpoint['experiment'],
        'experiment_unchanged')
    require(current['deadline_unix'] == prior['deadline_unix'] == HARD_END,
        'deadline_unchanged')
    require(requested['cycle'] == completed['cycle'] + 1, 'next_sleep_only')
    rows = current['rows'][frontier:]
    sources = [row['source_sha256'] for row in rows]
    require(len(rows) == (3 if life.startswith('r213_math_') else 5),
        'original_pending_row_count')
    require(len(set(sources)) == len(sources)
        and current['pending'] == 'sleep:' + digest(sources), 'all_pending_rows_bound')
    require(bool(suffix), 'observed_sleep_suffix_required')
    previous = pending
    for record in suffix:
        authenticate(record, record['kind'])
        require(record['journal_id'] == complete['journal_id']
            and record['index'] == previous['index'] + 1
            and record['previous_sha256'] == previous['sha256'],
            'contiguous_authenticated_sleep_suffix')
        previous = record
    cursor = 0
    metrics = []
    if suffix[0]['kind'] == 'R227_TARGET_METRICS':
        metrics = [reference(suffix[0])]
        cursor = 1
    require(len(suffix) >= cursor + 3, 'recipe_eligibility_and_updates_required')
    recipe = authenticate(suffix[cursor], 'SLEEP_RECIPE')
    targets = authenticate(suffix[cursor + 1], 'TARGET_ELIGIBILITY')
    require(recipe['policy'] == 'R181_NEW_ONLY_V1'
        and recipe['new_presentations'] == 16 and recipe['new_rows'] == len(rows)
        and recipe['selected_old_rows'] == 0, 'original_sleep_recipe_required')
    require(all(document['learn_row_policy'] == ROW_POLICY
        and document['active_semantic_filters'] == []
        and document['semantic_row_exclusion'] is False for document in (recipe, targets)),
        'no_row_filters')
    require(targets['new_row_sha256'] == sources and targets['rehearsal_row_sha256'] == []
        and targets['excluded'] == [] and targets['raw_modified'] is False,
        'targets_preserve_all_pending_rows')
    updates = suffix[cursor + 2:]
    counts = Counter()
    for offset, update in enumerate(updates, 1):
        document = authenticate(update, 'UPDATE')
        require(document['optimizer_step'] == checkpoint['optimizer_steps'] + offset,
            'observed_optimizer_sequence_not_saved_state')
        require(document['source_sha256'] in sources, 'pending_rows_only')
        counts[document['source_sha256']] += 1
    require(0 < len(updates) <= len(rows) * 16 and max(counts.values()) <= 16,
        'original_presentation_budget')
    contract = dict(schema=SCHEMA, life=life, original_gpu=plan['physical'],
        journal_id=complete['journal_id'], original_plan_sha256=expected_plan_sha256,
        complete=reference(complete), pending_sleep=reference(pending), old_head=reference(suffix[-1]),
        diagnostic_records=metrics, recipe=reference(suffix[cursor]),
        eligibility=reference(suffix[cursor + 1]),
        preserved_state=deepcopy(requested['resume_state']),
        durable_checkpoint=deepcopy(checkpoint), pending_cycle=requested['cycle'],
        pending_rows=len(rows), retained_rows=len(current['rows']),
        pending_row_sha256=sources, recorded_unsaved_updates=len(updates),
        recovery_requires_full_new_updates=len(rows) * 16,
        recovery_optimizer_start=checkpoint['optimizer_steps'],
        recovery_optimizer_end=checkpoint['optimizer_steps'] + len(rows) * 16,
        hard_end_unix=HARD_END, row_policy=ROW_POLICY,
        rng_origin='LAST_DURABLE_COMPLETE_NOT_UNSAVED_POST_GENERATION_OR_SLEEP_RNG',
        exact_resident_continuity_claimed=False, historical_generation_or_tool_reexecution=False,
        row_filtering=False, no_retry_provenance_preserved=True, execution_authorized=False,
        required_before_execution=[
            'Persistent disk headroom; no deletion or reserve bypass',
            'All original journal bytes/intents audited, partial artifacts reconciled without loss',
            'Original paired-LEARN and pending-sleep startup integration, CPU tested',
            'Original source-bound fresh confinement/admission, PID/start and GPU recheck',
            'Durable adapter/optimizer/RNG tensor verification by original constructor',
            'Exclusive attempt ledger; new recovery compute and failed artifacts retained',
            'New durable COMMIT and matching SLEEP_COMPLETE plus paired LEARN',
            'Parents rebound using preserved ledgers only after actual receiver LOADED',
        ])
    return dict(contract=contract, sha256=digest(contract))


def remote_observation():
    results = []
    for life, (complete_index, pending_index, head_index) in OBSERVED_BOUNDARIES.items():
        root = ROOT / life
        active = json.loads((root / 'ACTIVE_RUNTIME.json').read_bytes())
        control = Path(active['control'])
        plan_bytes = (control / 'PLAN.json').read_bytes()
        guard = json.loads((control / 'GUARD.json').read_bytes())
        directory = root / 'raw' / 'stream' / 'records'
        def record_at(index):
            return json.loads((directory / f'{index:020d}.json').read_bytes())
        try:
            head = max(int(path.stem) for path in directory.glob('*.json')
                if path.stem.isdigit())
            require(head == head_index, 'observation_head_changed')
            envelope = prepare(record_at(complete_index), record_at(pending_index),
                [record_at(index) for index in range(pending_index + 1, head_index + 1)],
                life=life, plan_bytes=plan_bytes, expected_plan_sha256=guard['plan_sha256'])
            contract = envelope['contract']
            results.append(dict(life=life, contract_sha256=envelope['sha256'],
                status='OFFLINE_CONTRACT_VALIDATED_NOT_LAUNCH_READY',
                summary={key: value for key, value in contract.items()
                    if key not in ('preserved_state', 'durable_checkpoint')},
                preserved_state_sha256=contract['preserved_state']['sha256']))
        except (OSError, ValueError, KeyError) as error:
            results.append(dict(life=life, status='BLOCKED', error=str(error)))
    print(json.dumps(dict(schema=SCHEMA, read_only=True, results=results), indent=2, sort_keys=True))


if __name__ == '__main__':
    remote_observation()
