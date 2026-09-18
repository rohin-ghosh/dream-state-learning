"""Deadline-only same-state recovery of the already-ended ovx4 pair."""

from copy import deepcopy


POLICY = 'R233_OVX4_PAIR_DEADLINE_RECOVERY_V1'
SAFETY_MARGIN_SECONDS = 21600


def extend_plan(previous, checkpoint, source, deadline, lease_end):
    state = checkpoint['state']
    if state['pending'] is not None or state['sleep_frontier'] != len(state['rows']):
        raise ValueError('complete_saved_boundary_required')
    if not state['sleep_receipts'] or state['sleep_receipts'][-1]['status'] != 'COMPLETE':
        raise ValueError('completed_sleep_required')
    if not previous['hard_end_unix'] == state['deadline_unix'] < deadline <= lease_end - SAFETY_MARGIN_SECONDS:
        raise ValueError('bound_authorized_deadline_only')
    if lease_end != previous['lease_end_unix']:
        raise ValueError('no_physical_lease_extension')
    if previous['physical'] not in (0, 1):
        raise ValueError('pair_devices_only')
    if any(config.get('learn_row_policy') != 'R227_ALL_AUTHENTIC_CHILD_ROWS_V1'
           for config in (previous, previous['think_act_learn'])):
        raise ValueError('same_all_authentic_policy')
    from pathlib import Path
    result = deepcopy(previous)
    result['source_root'] = str(source)
    result['startup_context']['path'] = str(Path(source) /
        Path(previous['startup_context']['path']).relative_to(previous['source_root']))
    result['hard_end_unix'] = deadline
    result['authorized_wall_extension'] = dict(schema='R131_SAVED_STATE_WALL_EXTENSION_V1',
        previous_deadline_unix=state['deadline_unix'], previous_stream_sha256=checkpoint['sha256'],
        new_deadline_unix=deadline, lease_end_unix=lease_end, safety_margin_seconds=SAFETY_MARGIN_SECONDS)
    return result
