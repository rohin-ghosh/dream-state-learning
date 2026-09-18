"""Non-dispatchable allocation-correction previews for the same saved pair."""

from copy import deepcopy
import hashlib
import json
from pathlib import Path


POLICY = 'R233_EXISTING_PAIR_ALLOCATION_PREVIEW_V1'
ROOT_NAMES = {0: 'orch_r231_curriculum_birth_20260918', 1: 'orch_r232_curriculum_frozen_20260918'}


def digest(document):
    return hashlib.sha256(json.dumps(document, sort_keys=True, separators=(',', ':'),
        allow_nan=False).encode()).hexdigest()


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def preview_plan(previous, saved, checkpoint, authority, source):
    physical = previous['physical']
    require(physical in ROOT_NAMES and previous['root'] ==
        '/localhome/local-rohing/' + ROOT_NAMES[physical] + '/raw', 'exact_existing_pair_identity')
    require(authority['schema'] == 'R233_EXISTING_PAIR_ALLOCATION_DATE_CORRECTION_V1'
        and authority['node_alias'] == 'ovx4' and authority['same_physical_pair'] is True
        and authority['physical_devices'] == [0, 1]
        and authority['gpu_uuids'][physical] == previous['gpu_uuid'], 'same_allocation_device_binding')
    require(authority['lease_purchase_or_extension_performed'] is False
        and authority['provider_exact_expiry_independently_verified'] is False,
        'user_date_authority_not_provider_or_purchase_claim')
    require(authority['lease_end_unix'] == 1790812800 and authority['hard_end_unix'] == 1790791200
        and authority['safety_margin_seconds'] == 21600
        and authority['hard_end_unix'] == authority['lease_end_unix'] - 21600, 'exact_corrected_six_hour_bound')
    state = saved['state']
    require(saved['sha256'] == digest(state) and state['pending'] is None
        and state['sleep_frontier'] == len(state['rows']) and state['sleep_receipts']
        and state['sleep_receipts'][-1]['status'] == 'COMPLETE', 'exact_complete_saved_state')
    require(state['model_state_sha256'] == digest(checkpoint['checkpoint_sha256']), 'same_model_working_state')
    require(previous['hard_end_unix'] == state['deadline_unix'] < authority['hard_end_unix'],
        'source_deadline_and_forward_extension_only')
    require(all(scope.get('learn_row_policy') == 'R227_ALL_AUTHENTIC_CHILD_ROWS_V1'
        for scope in (previous, previous['think_act_learn'])), 'same_authentic_row_policy')
    require(checkpoint['optimizer_steps'] == 0 if physical == 1 else checkpoint['optimizer_steps'] > 0,
        'same_frozen_or_learning_control')
    source = Path(source)
    require(source.is_absolute() and source != Path(previous['source_root']), 'separate_receiving_source')
    result = deepcopy(previous)
    result['source_root'] = str(source)
    result['startup_context']['path'] = str(source /
        Path(previous['startup_context']['path']).relative_to(previous['source_root']))
    result['hard_end_unix'] = authority['hard_end_unix']
    result['lease_end_unix'] = authority['lease_end_unix']
    result['authorized_wall_extension'] = dict(schema='R131_SAVED_STATE_WALL_EXTENSION_V1',
        previous_deadline_unix=state['deadline_unix'], previous_stream_sha256=saved['sha256'],
        new_deadline_unix=authority['hard_end_unix'], lease_end_unix=authority['lease_end_unix'],
        safety_margin_seconds=21600)
    return result
