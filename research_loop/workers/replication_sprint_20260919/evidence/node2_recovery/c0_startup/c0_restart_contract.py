"""Validate a declared checkpoint restart without claiming resident continuity."""

from copy import deepcopy
import hashlib
import json


SCHEMA = 'NODE2_ENOSPC_PENDING_SLEEP_RESTART_V2'
ROW_POLICY = 'R227_ALL_AUTHENTIC_CHILD_ROWS_V1'


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def digest(value):
    raw = json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()
    return hashlib.sha256(raw).hexdigest()


def authenticate(record, kind):
    require(record['kind'] == kind, 'wrong_record_kind')
    require(record['sha256'] == digest({key: value for key, value in record.items()
        if key != 'sha256'}), 'record_integrity')
    require(type(record['index']) is int and record['index'] >= 0, 'record_index')
    return record['document']


def saved_state(document):
    saved = document['resume_state']
    require(saved['sha256'] == digest(saved['state']), 'saved_state_integrity')
    return saved['state']


def reference(record):
    return dict(index=record['index'], sha256=record['sha256'])


def prepare(complete, pending, updates, *, life, new_presentations,
            row_policy, hard_end_unix, recipe, eligibility, head):
    require(life in ('C0', 'Astra7'), 'only_named_interrupted_node2_lives')
    require(row_policy == ROW_POLICY, 'all_authentic_child_rows_required')
    require(type(new_presentations) is int and new_presentations > 0,
        'unchanged_positive_presentation_count_required')
    completed = authenticate(complete, 'SLEEP_COMPLETE')
    requested = authenticate(pending, 'SLEEP_REQUEST')
    prior = saved_state(completed)
    current = saved_state(requested)
    require(complete['journal_id'] == pending['journal_id']
        and complete['index'] < pending['index'], 'same_ordered_journal')
    require(completed['status'] == 'COMPLETE' and prior['pending'] is None,
        'durable_complete_required')
    checkpoint = completed['checkpoint']
    require(completed['checkpoint_sha256'] == checkpoint['checkpoint_sha256']
        and checkpoint['optimizer_steps'] == completed['total_optimizer_steps'],
        'committed_checkpoint_binding')
    require(prior['model_state_sha256'] == digest(checkpoint['checkpoint_sha256'])
        and current['model_state_sha256'] == prior['model_state_sha256'],
        'same_durable_model_state')
    frontier = prior['sleep_frontier']
    require(type(frontier) is int and frontier == len(prior['rows'])
        and current['sleep_frontier'] == frontier, 'durable_sleep_frontier')
    require(current['rows'][:frontier] == prior['rows'], 'historical_rows_unchanged')
    require(current['sleep_receipts'] == prior['sleep_receipts'],
        'no_uncommitted_sleep_promoted')
    require(current['experiment'] == prior['experiment'] == checkpoint['experiment'],
        'experiment_unchanged')
    require(current['deadline_unix'] == prior['deadline_unix'] == hard_end_unix,
        'deadline_unchanged')
    require(requested['cycle'] == completed['cycle'] + 1, 'next_sleep_only')
    rows = current['rows'][frontier:]
    sources = [row['source_sha256'] for row in rows]
    require(bool(rows) and len(set(sources)) == len(sources),
        'distinct_pending_authentic_rows')
    require(current['pending'] == 'sleep:' + digest(sources),
        'pending_sleep_rows_binding')
    schedule = authenticate(recipe, 'SLEEP_RECIPE')
    targets = authenticate(eligibility, 'TARGET_ELIGIBILITY')
    authenticate(head, 'UPDATE')
    require(schedule['new_presentations'] == new_presentations
        and schedule['new_rows'] == len(rows) and schedule['selected_old_rows'] == 0
        and schedule['policy'] == 'R181_NEW_ONLY_V1', 'original_recorded_recipe_required')
    require(all(document['learn_row_policy'] == row_policy
        and document['active_semantic_filters'] == []
        and document['semantic_row_exclusion'] is False for document in (schedule, targets)),
        'recorded_all_authentic_rows_policy_required')
    require(targets['new_row_sha256'] == sources and targets['rehearsal_row_sha256'] == []
        and targets['excluded'] == [] and targets['raw_modified'] is False,
        'recorded_targets_preserve_every_pending_row')
    require(0 < len(updates) <= len(rows) * new_presentations,
        'interrupted_training_receipt_count')
    require(updates[-1] == head, 'complete_update_suffix_through_supplied_head_required')
    previous = pending
    for record in (recipe, eligibility, *updates):
        require(record['journal_id'] == complete['journal_id']
            and record['index'] == previous['index'] + 1
            and record['previous_sha256'] == previous['sha256'],
            'contiguous_authenticated_sleep_tail')
        previous = record
    for offset, update in enumerate(updates, 1):
        document = authenticate(update, 'UPDATE')
        require(document['optimizer_step'] == checkpoint['optimizer_steps'] + offset,
            'recorded_optimizer_step_sequence')
        require(document['source_sha256'] in sources, 'pending_rows_only')
    contract = dict(schema=SCHEMA, life=life, journal_id=complete['journal_id'],
        complete=reference(complete), pending_sleep=reference(pending),
        recipe=reference(recipe), eligibility=reference(eligibility), old_head=reference(head),
        recorded_updates=[reference(update) for update in updates],
        checkpoint_sha256=deepcopy(checkpoint['checkpoint_sha256']),
        durable_optimizer_steps=checkpoint['optimizer_steps'],
        pending_cycle=requested['cycle'], pending_rows=len(rows),
        pending_row_sha256=sources, retained_rows=len(current['rows']),
        preserved_state=deepcopy(pending['document']['resume_state']),
        new_presentations=new_presentations, row_policy=row_policy,
        hard_end_unix=hard_end_unix,
        replay_mode='RESTART_FULL_PENDING_SLEEP_FROM_DURABLE_CHECKPOINT',
        rng_origin='DURABLE_COMPLETE_NOT_UNSAVED_POST_GENERATION_STATE',
        recorded_uncheckpointed_updates=len(updates),
        actual_uncheckpointed_compute_not_fully_known=True,
        extra_recovery_compute_must_be_recorded_separately=True,
        exact_resident_continuity_claimed=False,
        historical_generation_or_tool_reexecution=False,
        historical_rows_or_receipts_rewritten=False,
        binary_checkpoint_verification_required=True,
        full_journal_tail_verification_required=True,
        fresh_filesystem_head_match_required=True,
        failed_artifact_preservation_required=True,
        fresh_original_admission_required=True,
        execution_authorized=False)
    return dict(contract=contract, sha256=digest(contract))
