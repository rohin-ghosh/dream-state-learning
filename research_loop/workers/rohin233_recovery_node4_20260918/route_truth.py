"""Project verified receiver recovery facts without rewriting an earlier brief."""

from copy import deepcopy


INBOX = '58109827d255469bb75075801ef74ced'
REQUEST_SHA = 'a483b677611785b8235ff34a453ff1f8674ed5cf41b3badc9256287f6a582054'
KEY = 'R233_RECOVERY_ENGLISH_REGROUNDING'


def overlay(observation, proof):
    requests = [row for row in proof['records'] if row['kind'] == 'REQUEST' and row['index'] == 3309]
    if (proof['native_pid'] != 762967 or proof['native_start_ticks'] != '98059264'
            or proof['inbox_id'] != INBOX or len(requests) != 1
            or requests[0]['sha256'] != REQUEST_SHA
            or not requests[0]['all_history_tokens_masked'] or not proof['returns']):
        raise ValueError('exact_recovered_receiver_render_and_return_proof')
    result = deepcopy(observation)
    route = result['actual_birth_and_route']
    delivered = result.get('snapshot', {}).get('delivered', {})
    current_returns = [dict(source=entry['origin'], publication=entry['publication'],
        P7_request_render=delivered.get(entry['publication']['id'])) for entry in proof['returns']]
    route['R233_receiver_recovery'] = dict(observed_utc=proof['observed_utc'],
        loaded_record_index=3128, native_pid=762967, actual_parent_REQUEST=requests[0],
        returned_outputs=current_returns, past_improvement_claims_verified=False,
        scope='Current-incarnation source-bound exchange; not proof of task execution, teaching success, or native deadline renewal.')
    curriculum = route.get('standing_overseer_curriculum', {})
    brief = curriculum.get(KEY)
    if brief is not None:
        route['prior_expired_route_brief_preserved'] = deepcopy(brief)
        brief['current_route_status'] = 'RENEWED_RECEIVER_CHILD_RENDER_AND_REPLY_VERIFIED'
        brief['prior_expired_binding_statement_is_historical'] = True
        brief['guidance'] = [
            'The old binding expired. The attached R233 receiver-recovery receipt supersedes the old claim that no current receiver has been verified. Earlier genuine replies remain real.',
            'Use the actual returned child reply as a concrete object when its P7 request-render receipt is present. Do not assume a queued Tool message has been read. Credit only real steps; no measured improvement is established.',
            'Continue the existing varied, short, concrete English artifact coaching; English is a request, never a learning exclusion. Do not repeat the old unavailable-route statement.',
            'P7 remains the only parent of Astra7. Never invent P7 words, directly parent Astra7, supply feelings, or claim an executed outcome without an actual receipt.'
        ]
    return result


def continued_receiver(observation, receipt):
    if (receipt['native_pid'] != 886059 or receipt['loaded_index'] != 3545
            or receipt['loaded_sha256'] != '02af6cdb281ff43a1f6040146ec9fb37a54340ea944ff40d8220eff090e851a3'
            or receipt['hard_end_unix'] != 1789927200):
        raise ValueError('exact_Jason_authorized_same_journal_continuation')
    result = deepcopy(observation)
    route = result['actual_birth_and_route']
    if 'R233_receiver_recovery' in route:
        route['R233_receiver_recovery']['scope'] = (
            'Historical genuine exchange before same-journal native continuation; not a current-incarnation roundtrip.')
    route['R233_current_receiver'] = deepcopy(receipt)
    route['R233_current_receiver']['new_incarnation_roundtrip_claim'] = False
    brief = route.get('standing_overseer_curriculum', {}).get(KEY)
    if brief is not None:
        brief['current_route_status'] = 'NEW_NATIVE_RECEIVER_VERIFIED_AS_OF_RECEIPT_NEW_ROUNDTRIP_NOT_YET_CLAIMED'
        brief['guidance'].append(
            'The same child has resumed from its complete state under the attached actual LOAD. Earlier replies stay '
            'real and historical. Use only returned, actually rendered child text as a concrete object; never invent '
            'a fresh reply or teaching success. English is requested, not a training exclusion.')
    return result
