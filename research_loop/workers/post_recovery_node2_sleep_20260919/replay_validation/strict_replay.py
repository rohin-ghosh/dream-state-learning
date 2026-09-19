"""Pure receipt comparison, not replay execution, journal recovery or state proof."""

import argparse
import hashlib
import json
import math
import os
import stat


CASE_SCHEMA = 'POST_COMPLETE_STRICT_REPLAY_CASE_V1'
STREAM_SCHEMA = 'R125_CONTINUAL_STREAM_V1'
JOURNAL_SCHEMA = 'R125_STREAM_JOURNAL_V1'
SLEEP_KINDS = ('SLEEP_REQUEST', 'SLEEP_RECIPE', 'TARGET_ELIGIBILITY')
UPDATE_KEYS = {'optimizer_step', 'losses', 'source_sha256', 'finished_unix'}
LOSS_KEYS = {'kind', 'mean_loss', 'objective_weight', 'target_tokens'}


class ReplayDivergence(ValueError):
    pass


def require(condition, reason):
    if not condition:
        raise ReplayDivergence(reason)


def canonical(value):
    try:
        encoded = json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()
    except (ValueError, TypeError, OverflowError, RecursionError) as error:
        raise ReplayDivergence('finite_acyclic_JSON_required') from error
    pending = [value]
    while pending:
        current = pending.pop()
        require(type(current) in (dict, list, str, int, float, bool, type(None)), 'JSON_types_only')
        if type(current) is dict:
            require(all(type(key) is str for key in current), 'JSON_string_keys_only')
            pending.extend(current.values())
        elif type(current) is list:
            pending.extend(current)
        elif type(current) is float:
            require(math.isfinite(current), 'finite_JSON_numbers_only')
    return encoded


def digest(value):
    return hashlib.sha256(canonical(value)).hexdigest()


def valid_sha(value):
    return type(value) is str and len(value) == 64 and all(letter in '0123456789abcdef' for letter in value)


def same(expected, actual, reason):
    require(canonical(expected) == canonical(actual), reason)


def finite_number(value):
    return type(value) in (int, float) and math.isfinite(value)


def record(envelope, kind, journal_id):
    require(type(envelope) is dict and set(envelope) == {'record', 'intent'}, 'record_and_intent_required')
    value = envelope['record']
    require(type(value) is dict and set(value) == {'schema', 'journal_id', 'index', 'kind', 'document',
        'previous_sha256', 'sha256'}, 'exact_original_record_shape')
    require(value['schema'] == JOURNAL_SCHEMA and value['kind'] == kind and value['journal_id'] == journal_id
        and type(value['index']) is int and value['index'] >= 0 and valid_sha(value['previous_sha256'])
        and valid_sha(value['sha256']) and type(value['document']) is dict, 'original_record_binding')
    require(value['sha256'] == digest({key: item for key, item in value.items() if key != 'sha256'}),
        'original_record_hash')
    same(dict(schema=JOURNAL_SCHEMA, journal_id=journal_id, index=value['index'],
        previous_sha256=value['previous_sha256'], record_sha256=value['sha256']),
        envelope['intent'], 'original_record_intent')
    return value


def snapshot(document):
    require(type(document) is dict and set(document) == {'state', 'sha256'}
        and document['sha256'] == digest(document['state']), 'saved_working_state_hash')
    state = document['state']
    require(type(state['rows']) is list and type(state['sleep_frontier']) is int
        and 0 <= state['sleep_frontier'] <= len(state['rows']), 'saved_row_frontier')
    return state


def validate_update(document):
    require(type(document) is dict and set(document) == UPDATE_KEYS, 'exact_UPDATE_schema_no_unknown_fields')
    require(type(document['optimizer_step']) is int and document['optimizer_step'] > 0
        and valid_sha(document['source_sha256']) and finite_number(document['finished_unix']), 'UPDATE_step_source_time')
    require(type(document['losses']) is list and document['losses'], 'ordered_nonempty_UPDATE_losses')
    for loss in document['losses']:
        require(type(loss) is dict and set(loss) == LOSS_KEYS, 'exact_loss_schema_no_unknown_fields')
        require(type(loss['kind']) is str and bool(loss['kind']) and finite_number(loss['mean_loss'])
            and loss['mean_loss'] >= 0 and finite_number(loss['objective_weight'])
            and 0 < loss['objective_weight'] <= 1 and type(loss['target_tokens']) is int
            and loss['target_tokens'] > 0, 'valid_loss_receipt_values')


def compare_update(original, recomputed, expected_step):
    require(type(expected_step) is int and expected_step > 0, 'typed_expected_optimizer_step')
    validate_update(original)
    validate_update(recomputed)
    require(original['optimizer_step'] == expected_step, 'contiguous_committed_optimizer_prefix')
    same({key: value for key, value in original.items() if key != 'finished_unix'},
        {key: value for key, value in recomputed.items() if key != 'finished_unix'}, 'UPDATE_behavioral_divergence')
    return dict(optimizer_step=expected_step, original_finished_unix=original['finished_unix'],
        replay_finished_unix=recomputed['finished_unix'],
        timing_differs=canonical(original['finished_unix']) != canonical(recomputed['finished_unix']))


def compare_generation(request, receipt, replay, checkpoint, decoder):
    require(type(replay) is dict and set(replay) == {'request', 'model_response'}, 'exact_generation_replay_shape')
    same(request, replay['request'], 'exact_logical_REQUEST_divergence_including_state_and_original_time')
    logical_request = {key: value for key, value in request.items() if key != 'resume_state'}
    require(request['schema'] == STREAM_SCHEMA and request['split'] == 'TRAIN'
        and request['retry_allowed'] is False and request['parent_wait_seconds'] == 0,
        'original_nonretry_TRAIN_request')
    require(type(request['prompt_tokens']) is int and request['prompt_tokens'] >= 0
        and finite_number(request['started_unix']) and type(request.get('training_eligible', True)) is bool,
        'typed_request_count_time_and_training_policy')
    require(type(receipt) is dict and set(receipt) == {'schema', 'request_sha256', 'response',
        'finished_unix', 'raw_saved_before_validation'} and receipt['schema'] == STREAM_SCHEMA
        and receipt['request_sha256'] == digest(logical_request) and receipt['raw_saved_before_validation'] is True
        and finite_number(receipt['finished_unix']), 'exact_original_RESPONSE_REQUEST_link')
    require(request['model_state_sha256'] == digest(checkpoint['checkpoint_sha256']), 'checkpoint_reference_model_identity')
    saved = snapshot(request['resume_state'])
    require(saved['pending'] == receipt['request_sha256']
        and saved['model_state_sha256'] == request['model_state_sha256'], 'pending_request_state_identity')
    response = receipt['response']
    required = {'raw', 'token_ids', 'terminal', 'truncated', 'prompt_tokens', 'prompt_token_ids_sha256',
        'adapter_state_sha256', 'base_sha256', 'decoder'}
    require(type(response) is dict and set(response) == required, 'complete_model_receipt_only_no_partial_or_unknown_calls')
    require(type(request['max_new_tokens']) is int and request['max_new_tokens'] > 0
        and type(response['token_ids']) is list and 0 < len(response['token_ids']) <= request['max_new_tokens']
        and all(type(token) is int and token >= 0 for token in response['token_ids'])
        and type(response['raw']) is str and type(response['terminal']) is bool and type(response['truncated']) is bool
        and not (response['terminal'] and response['truncated'])
        and (not response['truncated'] or len(response['token_ids']) == request['max_new_tokens']), 'exact_bounded_generation_tokens')
    require(type(response['prompt_tokens']) is int and response['prompt_tokens'] == request['prompt_tokens']
        and valid_sha(response['prompt_token_ids_sha256'])
        and response['adapter_state_sha256'] == checkpoint['adapter_state_sha256']
        and response['base_sha256'] == checkpoint['base_sha256'], 'original_prompt_and_actual_model_receipt')
    same(decoder, response['decoder'], 'original_decoder_binding')
    same(response, replay['model_response'], 'generation_token_text_prompt_model_decoder_divergence')
    return digest(receipt)


def _validate_replay(reference, observed, reference_sha256):
    require(valid_sha(reference_sha256) and digest(reference) == reference_sha256, 'externally_pinned_reference_case')
    require(type(reference) is dict and set(reference) == {'schema', 'life_id', 'journal_id', 'source_pins', 'decoder',
        'complete', 'generations', 'sleep_inputs', 'updates'} and reference['schema'] == CASE_SCHEMA,
        'exact_reference_case_schema')
    require(type(observed) is dict and set(observed) == {'binding', 'generations', 'sleep_inputs', 'updates'}, 'exact_observed_trace_schema')
    require(type(reference['life_id']) is str and bool(reference['life_id'])
        and type(reference['journal_id']) is str and bool(reference['journal_id']), 'explicit_life_and_journal')
    pins = reference['source_pins']
    require(type(pins) is dict and pins and all(type(name) is str and name and valid_sha(value)
        for name, value in pins.items()), 'explicit_source_pins_required_not_source_execution_proof')
    for name, maximum in (('generations', 64), ('sleep_inputs', 3), ('updates', 4096)):
        require(type(reference[name]) is list and 0 < len(reference[name]) <= maximum
            and type(observed[name]) is list, 'bounded_explicit_replay_sequences')
    journal_id = reference['journal_id']
    complete = record(reference['complete'], 'SLEEP_COMPLETE', journal_id)
    document = complete['document']
    saved = snapshot(document['resume_state'])
    checkpoint = document['checkpoint']
    require(document['status'] == 'COMPLETE' and saved['pending'] is None
        and saved['sleep_frontier'] == len(saved['rows']) and type(checkpoint['optimizer_steps']) is int
        and checkpoint['optimizer_steps'] >= 0 and valid_sha(checkpoint['base_sha256'])
        and valid_sha(checkpoint['adapter_state_sha256']), 'complete_saved_checkpoint_not_unsaved_tail')
    require(set(checkpoint['checkpoint_sha256']) == {'adapter', 'optimizer', 'rng'}
        and all(valid_sha(value) for value in checkpoint['checkpoint_sha256'].values())
        and checkpoint['checkpoint_sha256']['optimizer'] == checkpoint['checkpoint_sha256']['rng']
        and saved['model_state_sha256'] == digest(checkpoint['checkpoint_sha256']), 'complete_model_optimizer_RNG_reference_binding')
    same(document['checkpoint_sha256'], checkpoint['checkpoint_sha256'], 'COMPLETE_checkpoint_reference_binding')
    same(dict(source_pins_sha256=digest(pins), checkpoint_reference_sha256=digest(checkpoint['checkpoint_sha256'])),
        observed['binding'], 'replay_declared_source_or_checkpoint_divergence_not_execution_proof')
    require(len(observed['generations']) == len(reference['generations']), 'all_logged_generations_required_no_extra_call')
    previous_index = complete['index']
    new_rows = []
    for expected, actual in zip(reference['generations'], observed['generations']):
        require(set(expected) == {'request', 'response'}, 'exact_original_generation_pair')
        requested = record(expected['request'], 'REQUEST', journal_id)
        returned = record(expected['response'], 'RESPONSE', journal_id)
        require(previous_index < requested['index'] and returned['index'] == requested['index'] + 1
            and returned['previous_sha256'] == requested['sha256'], 'ordered_adjacent_REQUEST_RESPONSE')
        source = compare_generation(requested['document'], returned['document'], actual, checkpoint, reference['decoder'])
        if requested['document'].get('training_eligible', True):
            new_rows.append((source, requested['document'], returned['document']['response']))
        previous_index = returned['index']
    require(len(reference['sleep_inputs']) == len(observed['sleep_inputs']) == 3, 'all_exact_sleep_inputs_required')
    selected = []
    for kind, expected, actual in zip(SLEEP_KINDS, reference['sleep_inputs'], observed['sleep_inputs']):
        entry = record(expected, kind, journal_id)
        require(entry['index'] > previous_index, 'ordered_sleep_inputs')
        same(dict(kind=kind, document=entry['document']), actual, 'sleep_input_recipe_row_or_working_state_divergence')
        selected.append(entry)
        previous_index = entry['index']
    pending = snapshot(selected[0]['document']['resume_state'])
    require(selected[0]['document']['cycle'] == document['cycle'] + 1
        and pending['sleep_frontier'] == saved['sleep_frontier']
        and pending['model_state_sha256'] == saved['model_state_sha256'], 'same_pending_sleep_frontier_and_model')
    same(saved['rows'], pending['rows'][:saved['sleep_frontier']], 'historical_rows_must_not_change_or_disappear')
    tail_rows = pending['rows'][saved['sleep_frontier']:]
    require(len(tail_rows) == len(new_rows), 'all_new_child_rows_preserved')
    for row, (source, request, response) in zip(tail_rows, new_rows):
        require(row['source_sha256'] == source and row['model_state_sha256'] == request['model_state_sha256'],
            'original_child_row_provenance_not_rewritten_with_replay_time')
        same(row['token_ids'], response['token_ids'], 'original_child_row_tokens')
        same(row['target'], response['raw'], 'original_child_row_text')
        same(row['prefix'], request['messages'], 'original_child_row_request')
    require(pending['pending'] == 'sleep:' + digest([row['source_sha256'] for row in tail_rows]), 'same_pending_sleep_token')
    require(len(reference['updates']) == len(observed['updates']), 'entire_committed_UPDATE_prefix_no_short_or_extra_replay')
    row_sources = {row['source_sha256'] for row in pending['rows']}
    previous = selected[-1]
    timing = []
    for offset, (expected, actual) in enumerate(zip(reference['updates'], observed['updates']), 1):
        entry = record(expected, 'UPDATE', journal_id)
        require(entry['index'] == previous['index'] + 1 and entry['previous_sha256'] == previous['sha256'],
            'contiguous_committed_UPDATE_record_prefix')
        require(entry['document']['source_sha256'] in row_sources, 'UPDATE_references_preserved_child_row')
        timing.append(compare_update(entry['document'], actual, checkpoint['optimizer_steps'] + offset))
        previous = entry
    return dict(schema='STRICT_REPLAY_BEHAVIORAL_CONSISTENCY_V1', status='MATCHED_LOGGED_RECEIPTS_ONLY',
        reference_sha256=reference_sha256, observed_sha256=digest(observed), source_pins_sha256=digest(pins), life_id=reference['life_id'],
        complete_index=complete['index'], complete_sha256=complete['sha256'],
        saved_optimizer_steps=checkpoint['optimizer_steps'], matched_generation_receipts=len(reference['generations']),
        preserved_new_row_sha256=[row['source_sha256'] for row in tail_rows],
        matched_UPDATE_receipts=len(timing), last_matched_optimizer_step=previous['document']['optimizer_step'],
        intentionally_excluded_UPDATE_fields=['finished_unix'], UPDATE_timing_comparisons=timing,
        exact_resident_continuity_claimed=False, optimizer_state_equivalence_proven=False,
        RNG_state_equivalence_proven=False, unlogged_rng_calls_excluded=False,
        checkpoint_binary_verification_performed=False, full_journal_verified=False,
        pending_sleep_reconciled=False, recovery_authorized=False, artifacts_modified=[])


def validate_replay(reference, observed, *, reference_sha256):
    try:
        return _validate_replay(reference, observed, reference_sha256)
    except (KeyError, TypeError, OverflowError, RecursionError) as error:
        raise ReplayDivergence('malformed_reference_or_replay') from error


def load_bounded(path):
    descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    with os.fdopen(descriptor, 'rb') as stream:
        before = os.fstat(stream.fileno())
        require(stat.S_ISREG(before.st_mode) and before.st_size <= 256 * 1024**2, 'bounded_case_file_not_a_journal_scan')
        raw = stream.read(before.st_size + 1)
        after = os.fstat(stream.fileno())
    require(len(raw) == before.st_size and (before.st_size, before.st_mtime_ns, before.st_ctime_ns)
        == (after.st_size, after.st_mtime_ns, after.st_ctime_ns), 'case_changed_during_read')
    def unique_keys(pairs):
        result = {}
        for key, value in pairs:
            require(key not in result, 'duplicate_JSON_key')
            result[key] = value
        return result
    return json.loads(raw, object_pairs_hook=unique_keys)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--reference', required=True)
    parser.add_argument('--reference-sha256', required=True, help='Canonical reference digest, not raw file hash')
    parser.add_argument('--observed', required=True)
    arguments = parser.parse_args()
    result = validate_replay(load_bounded(arguments.reference), load_bounded(arguments.observed),
        reference_sha256=arguments.reference_sha256)
    print(json.dumps(result, sort_keys=True, allow_nan=False))


if __name__ == '__main__':
    main()
