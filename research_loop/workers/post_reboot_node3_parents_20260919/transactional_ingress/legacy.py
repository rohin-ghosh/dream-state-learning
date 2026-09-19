"""Offline reconciliation and fail-closed verification of owner drain evidence."""

import argparse
import json
import os
import time

from ..projected_wire.contract import digest, is_sha, require
from ..projected_wire.custody import load_binding
from .relay import SESSIONS


REQUIRED_EDGES = {f'alias-{slot}' for slot in SESSIONS} | {
    'old-node-private-targets', 'reverse-ssh-channels', 'vm-proxy-listeners',
    'vm-shared-forward', 'scorer-bridge-448173', 'scorer-bridge-502015',
    'scorer-native-listener', 'scorer-base-listener'}
REQUIRED_ROLES = {'vm-proxy', 'bridge-448173', 'bridge-502015', 'scorer'}


def reconcile(cut):
    sessions = {item['session_id']: item for item in cut['scorer']['cuts'][-1]['sessions']}
    require(set(sessions) == set(SESSIONS.values()), 'all_five_original_sessions')
    grouped = {}
    for item in cut['host']['completed_transport_logs']:
        record = item['record']
        origin = record.get('origin')
        if not origin:
            key = ('UNATTRIBUTED', item['file_sha256'])
        else:
            key = (record['session_id'], origin['record_sha256'])
        grouped.setdefault(key, []).append(item)
    dispositions = []
    for (session, origin_sha256), logs in sorted(grouped.items()):
        state = sessions.get(session, {})
        attempts = [item for item in state.get('attempts', []) if item['identifier'] == origin_sha256]
        completed = len(attempts) == 1 and attempts[0]['complete_files'] and origin_sha256 in state.get('seen', [])
        dispatched = any(item['record'].get('dispatched') is True for item in logs)
        disposition = 'COMPLETE' if completed else ('UNKNOWN_NO_REPLAY' if dispatched or session == 'UNATTRIBUTED'
            else 'PREPARED_NEVER_DISPATCHED')
        dispositions.append(dict(session=session, origin_sha256=origin_sha256, disposition=disposition,
            transport_log_sha256=[item['file_sha256'] for item in logs],
            original_attempt_files=attempts[0]['files'] if completed else None,
            delivery_proved=False, scoring_success_claimed=False))
    return dict(schema='R233_LEGACY_PENDING_INVENTORY_V1', cut_unix=cut['unix'], cut_sha256=digest(cut),
        dispositions=dispositions, unenumerated_legacy_admissions=True,
        unenumerated_disposition='BLOCKS_DRAIN_UNTIL_AUTHENTICATED_ROUTE_AND_KERNEL_LIFETIME_PROOF',
        admission_closed=False, drain_proved=False, historical_replay_authorized=False)


def verify_drain(proof, expected_identity, *, now=None):
    now = time.time() if now is None else now
    require(proof['schema'] == 'R233_OWNER_LEGACY_DRAIN_V1', 'owner_drain_schema')
    require(proof['scorer_identity'] == expected_identity, 'exact_original_scorer_incarnation')
    require(proof['authority'] == 'OPERATOR_AUTHENTICATED_OWNER_CUSTODY', 'not_child_asserted_drain')
    require(0 <= now - proof['unix'] <= 110, 'fresh_drain_observation')
    require(is_sha(proof['source_witness_sha256']) and is_sha(proof['fence']['owner_evidence_sha256']),
        'bound_original_code_and_actual_fence_evidence')
    fence = proof['fence']
    require(set(fence['edges']) == REQUIRED_EDGES and all(value == 'CLOSED_TO_NEW_OLD_ROUTE_CONNECTIONS'
        for value in fence['edges'].values()), 'all_alias_private_retained_base_and_ssh_routes_fenced')
    require(fence['creator_capabilities_revoked'] is True and fence['supervisor_respawn_inhibited'] is True,
        'alias_switch_alone_is_not_a_legacy_fence')
    require(proof['unix'] >= fence['unix'], 'observations_after_fence')
    require(len(proof['observations']) == 2, 'two_complete_owner_observations')
    previous_unix = fence['unix']
    for observation in proof['observations']:
        require(previous_unix <= observation['unix'] <= proof['unix'], 'ordered_postfence_observations')
        previous_unix = observation['unix']
        require(observation['complete_socket_namespace_inventory'] is True
            and observation['observer_not_sandbox_ps'] is True, 'real_host_kernel_inventory_not_ps_absence')
        require(set(observation['processes']) == REQUIRED_ROLES, 'every_original_proxy_bridge_scorer')
        for role, process in observation['processes'].items():
            require(is_sha(process['raw_proc_capture_sha256']) and process['nonlistener_socket_fds'] == []
                and process['active_handler_threads'] == [] and process['enumeration_complete'] is True,
                'no_live_accepted_socket_or_handler_' + role)
            require(process['identity'] == proof['process_identities'][role], 'same_process_through_drain')
        require(observation['processes']['scorer']['identity'] == expected_identity, 'scorer_present_not_inferred_dead')
        require(set(observation['queues']) == REQUIRED_EDGES, 'all_retained_and_kernel_queued_paths')
        for edge, queue in observation['queues'].items():
            require(queue['pending_connections'] == 0 and queue['accepted_connections'] == 0
                and queue['pending_bytes'] == 0 and is_sha(queue['raw_kernel_or_channel_evidence_sha256'])
                and queue['enumeration_complete'] is True, 'empty_exact_kernel_or_ssh_channel_' + edge)
        require(observation['unattributed_old_route_channels'] == [], 'no_unattributed_child_ssh_channels')
    require(proof['all_sessions_complete'] is True and proof['unresolved_active_callbacks'] == [],
        'no_callback_continues_after_client_disconnect')
    require(is_sha(proof['state_closure_sha256']) and is_sha(proof['queue_dispositions_sha256']),
        'full_state_and_exact_pending_dispositions_bound')
    return dict(status='OWNER_EVIDENCE_VERIFIED_NOT_INDEPENDENT_KERNEL_OBSERVATION',
        drain_sha256=digest(proof), replay_authorized=False, state_closure_sha256=proof['state_closure_sha256'],
        queue_dispositions_sha256=proof['queue_dispositions_sha256'])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('operation', choices=['reconcile', 'verify'])
    parser.add_argument('--owner-file', required=True)
    parser.add_argument('--sha256', required=True)
    args = parser.parse_args()
    value = load_binding(args.owner_file, os.getuid(), args.sha256)
    result = reconcile(value) if args.operation == 'reconcile' else verify_drain(value, value['scorer_identity'])
    print(json.dumps(result, sort_keys=True, indent=2))


if __name__ == '__main__':
    main()
