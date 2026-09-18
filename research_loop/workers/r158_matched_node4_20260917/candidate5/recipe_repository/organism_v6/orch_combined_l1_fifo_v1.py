"""CPU-only prospective scheduler; not imported by any native training driver."""

from copy import deepcopy
import re

from organism_v6.orch_combined_l1_continual import digest


VERSION = 'COMBINED_L1_FUTURE_FIFO_STABLE_REHEARSAL_V1'


def require(condition, message):
    if not condition:
        raise ValueError(message)


def valid_hash(value):
    return isinstance(value, str) and re.fullmatch(r'[0-9a-f]{64}', value) is not None


def validate(state):
    require(state['schema'] == VERSION, 'scheduler_version')
    count = 222 + len(state['corpus_targets'])
    require(type(state['update']) is int and state['update'] >= state['activation_update'], 'scheduler_cursor')
    require(len(state['exposure_counts']) == count, 'count_shape')
    require(all(type(value) is int and value >= 0 for value in state['exposure_counts']), 'nonnegative_counts')
    require(sum(state['exposure_counts']) == 4 * state['update'], 'logical_count_conservation')
    ring, deferred, queue = state['rehearsal_ring'], state['deferred_rehearsal'], state['fifo']
    require(ring and 0 <= state['rehearsal_cursor'] < len(ring), 'rehearsal_cursor')
    inventory = ring + deferred + queue
    require(len(set(inventory)) == len(inventory) and set(inventory) == set(range(210, count)),
            'no_lost_or_duplicate_ticket')
    require(all(row >= state['initial_row_count'] and state['exposure_counts'][row] == 0 for row in queue),
            'future_unpresented_only')
    require(all(state['exposure_counts'][row] >= 1 for row in deferred), 'deferred_first_exposure_required')
    require(len({entry['batch_id'] for entry in state['batches']}) == len(state['batches']), 'duplicate_batch')


def start(*, update, corpus_targets, corpus_version, exposure_counts, paired_anchor):
    require(type(update) is int and update >= 0, 'positive_anchor_update')
    require(corpus_targets and all(valid_hash(value) for value in corpus_targets), 'bound_target_hashes')
    require(set(paired_anchor) == {'FULL', 'OFF'} and all(valid_hash(value) for value in paired_anchor.values()),
            'paired_durable_commit_hashes')
    row_count = 222 + len(corpus_targets)
    ring = list(range(210, row_count))
    state = dict(schema=VERSION, activation_update=update, update=update,
        initial_row_count=row_count, paired_anchor=deepcopy(paired_anchor),
        corpus_version=corpus_version, corpus_targets=list(corpus_targets),
        exposure_counts=list(exposure_counts), activation_exposure_counts=list(exposure_counts),
        rehearsal_ring=ring, rehearsal_cursor=(2 * update) % len(ring),
        deferred_rehearsal=[], fifo=[], batches=[], first_future_presentations={})
    validate(state)
    return state


def ingest(state, *, batch_id, manifest_sha256, native_receipt_sha256,
           corpus_targets, corpus_version, origin, parenting_experience, teacher_source):
    validate(state)
    require(origin == 'L1_EXTERNAL_GENERATION' and parenting_experience is False and teacher_source is False,
            'external_qualified_intake_only')
    require(isinstance(batch_id, str) and re.fullmatch(r'[A-Za-z0-9_-]{1,100}', batch_id), 'safe_batch_id')
    require(valid_hash(manifest_sha256) and valid_hash(native_receipt_sha256), 'native_admission_bindings')
    binding = digest(dict(batch_id=batch_id, manifest_sha256=manifest_sha256,
        native_receipt_sha256=native_receipt_sha256, corpus_targets=corpus_targets, corpus_version=corpus_version))
    for previous in state['batches']:
        if previous['batch_id'] == batch_id:
            require(previous['binding'] == binding, 'batch_rebound')
            return state
    old_count = len(state['corpus_targets'])
    require(corpus_targets[:old_count] == state['corpus_targets'], 'unchanged_corpus_prefix')
    require(type(corpus_version) is int and corpus_version > state['corpus_version'], 'advancing_corpus_version')
    new_targets = corpus_targets[old_count:]
    require(all(valid_hash(value) for value in new_targets), 'bound_target_hashes')
    require(len(set(new_targets)) == len(new_targets) and not set(new_targets).intersection(state['corpus_targets']),
            'upstream_whole_corpus_dedup_required')
    updated = deepcopy(state)
    rows = list(range(222 + old_count, 222 + len(corpus_targets)))
    updated['fifo'].extend(rows)
    updated['exposure_counts'].extend([0] * len(rows))
    updated['corpus_targets'] = list(corpus_targets)
    updated['corpus_version'] = corpus_version
    updated['batches'].append(dict(batch_id=batch_id, binding=binding, added_rows=rows,
        ingested_at_update=state['update'], manifest_sha256=manifest_sha256,
        native_receipt_sha256=native_receipt_sha256,
        queue_ahead=len(state['fifo']), final_first_exposure_update_bound=state['update'] + len(updated['fifo'])))
    validate(updated)
    return updated


def _rehearsal(state):
    row = state['rehearsal_ring'][state['rehearsal_cursor']]
    state['rehearsal_cursor'] += 1
    if state['rehearsal_cursor'] == len(state['rehearsal_ring']):
        state['rehearsal_ring'].extend(state['deferred_rehearsal'])
        state['deferred_rehearsal'] = []
        state['rehearsal_cursor'] = 0
    return row


def plan(state):
    validate(state)
    proposed = deepcopy(state)
    update = state['update'] + 1
    fifo_row = None
    if proposed['fifo']:
        fifo_row = proposed['fifo'].pop(0)
        proposed['deferred_rehearsal'].append(fifo_row)
        trajectories = [_rehearsal(proposed), fifo_row]
        proposed['first_future_presentations'][str(fifo_row)] = update
    else:
        trajectories = [_rehearsal(proposed), _rehearsal(proposed)]
    rows = [(update - 1) % 128, 128 + (update - 1) % 82] + trajectories
    require(len(set(rows)) == 4, 'distinct_whole_row_batch')
    for row in rows:
        proposed['exposure_counts'][row] += 1
    proposed['update'] = update
    validate(proposed)
    return dict(schema=VERSION, before_sha256=digest(state), update=update, rows=rows,
                fifo_first_row=fifo_row, next_state=proposed, after_sha256=digest(proposed))


def commit_after_optimizer(state, proposed, *, actual_update):
    require(proposed['before_sha256'] == digest(state), 'stale_or_duplicate_optimizer_commit')
    require(actual_update == state['update'] + 1 == proposed['update'], 'actual_optimizer_update_required')
    require(proposed == plan(state), 'bound_plan_drift')
    return deepcopy(proposed['next_state'])


def checkpoint(state, *, native_update, native_exposure_counts, native_file_hashes, native_world_size):
    validate(state)
    require(native_update == state['update'] and native_exposure_counts == state['exposure_counts'],
            'native_checkpoint_cursor_or_counts_drift')
    require(type(native_world_size) is int and 1 <= native_world_size <= 3, 'native_world_size')
    required = {'adapter/adapter_config.json', 'adapter/adapter_model.safetensors', 'optimizer.pt'}
    required.update(f'rank{rank}.pt' for rank in range(native_world_size))
    require(required <= native_file_hashes.keys() and
            all(valid_hash(value) for value in native_file_hashes.values()), 'adapter_optimizer_rng_file_bindings')
    body = dict(schema=VERSION, state=deepcopy(state), native_file_hashes=deepcopy(native_file_hashes),
                native_world_size=native_world_size)
    return dict(body=body, sha256=digest(body))


def restore(receipt, *, expected_sha256, native_update, native_exposure_counts, native_file_hashes, native_world_size):
    require(receipt['sha256'] == expected_sha256 == digest(receipt['body']), 'checkpoint_hash_drift')
    state = receipt['body']['state']
    require(checkpoint(state, native_update=native_update, native_exposure_counts=native_exposure_counts,
                       native_file_hashes=native_file_hashes, native_world_size=native_world_size) == receipt,
            'native_state_binding_drift')
    return deepcopy(state)
