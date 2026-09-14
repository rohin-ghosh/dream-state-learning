"""Pure guided cue collection with external retained EVENT text, not a fit.

The teacher sees only public chat. External lookup is not a parametric reader.
Native generation/provenance and any later training decision belong to callers.
Evaluation-identity exclusion here applies to this new cue corpus only; it makes
no decision about replay of prior training EVENTs in a future retention study.
"""

from hashlib import sha256
import json

from organism_v6 import experienced_event_microloop as micro
from organism_v6 import experienced_event_read_route as controller


GUIDANCE = (
    '\n\nTeacher strategy for this training collection only: '
    'Consult the listed EVENT records before committing a ROUTE. '
    'Compare each returned EVENT AT (source node) with the public task NODE and '
    'its GOT with the public GOAL. Choose its DID port only when both match. '
    'Use only the listed addresses and ports, within the public call limits. '
    'Output only the permitted command, without explanation.'
)
DEFAULT_TEACHING_MODE = 'fixed_guidance_v1'
PUBLIC_FEEDBACK_MODE = 'public_feedback_v1'
PUBLIC_FEEDBACK_PREFIX = (
    '\n\nPublic-feedback teacher inference (not compiler or autonomous child inference): '
)
CLAIM = 'EXTERNAL_TEXT_GUIDED_CUE_PARTIAL_LOOP_NOT_PARAMETRIC_READER_EVIDENCE'
EVALUATION_MASTER = 'ASTRA-EXPERIENCED-EVENT-MICROLOOP-20260914-A1'
require = micro._require


def _bytes(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=True, allow_nan=False,
                      separators=(',', ':')).encode('ascii')


def _identities(bank):
    return {fact[key] for fact in bank for key in ('world', 'event', 'node', 'port', 'outcome', 'receipt')}


def validate_memory(bank, raw_memory_by_address):
    """Check all four sourced EVENTs; final LF count alone is ignored for checking."""
    micro._check_bank(bank)
    require(not _identities(bank).intersection(_identities(micro.build_bank(EVALUATION_MASTER))),
            'new_cue_bank_must_exclude_original_evaluation_identities')
    require(type(raw_memory_by_address) is dict
            and set(raw_memory_by_address) == {fact['event'] for fact in bank}, 'exact_four_memory_addresses_required')
    for fact in bank:
        raw = raw_memory_by_address[fact['event']]
        observed = micro.parse_event_line(micro.canonical_event(raw))
        require(observed == dict(event=fact['event'], source=fact['node'], port=fact['port'],
            destination=fact['outcome'], receipt=fact['receipt']), 'source_memory_not_grounded')


def _check_public_messages(messages):
    require(type(messages) is list and len(messages) >= 2
            and messages[0] == dict(role='system', content=controller.PUBLIC_SYSTEM)
            and all(type(message) is dict and set(message) == {'role', 'content'}
                    and type(message['content']) is str for message in messages)
            and all(message['role'] in ('user', 'assistant') for message in messages[1:]),
            'unassisted_public_messages_required')
    require(all(GUIDANCE not in message['content'] for message in messages), 'teacher_in_public_history')
    require(all(PUBLIC_FEEDBACK_PREFIX not in message['content'] for message in messages),
            'teacher_in_public_history')


def public_feedback(messages):
    """Bounded teacher inference from public task and raw READ results only."""
    _check_public_messages(messages)
    require(len(messages) in (2, 4, 6) and messages[1]['role'] == 'user',
            'malformed_public_feedback_history')
    lines = messages[1]['content'].split('\n')
    require(len(lines) == 5 and lines[0] == 'ROUTE TASK'
            and all(line.startswith(label + ' ') for line, label in
                    zip(lines[1:], ('NODE', 'GOAL', 'PORTS', 'EVENTS'))),
            'malformed_public_feedback_task')
    task = dict(node=lines[1][5:], goal=lines[2][5:],
                ports=lines[3][6:].split(','), events=lines[4][7:].split(','))
    controller._check_task(task)
    addresses = set()
    observed = None
    for offset in range(2, len(messages), 2):
        action, memory = messages[offset:offset + 2]
        require(action['role'] == 'assistant' and memory['role'] == 'user'
                and memory['content'].startswith('MEMORY RESULT\n'),
                'malformed_public_feedback_history')
        command = controller.parse_command(action['content'])
        require(command['kind'] == 'READ' and command['value'] in task['events']
                and command['value'] not in addresses, 'invalid_public_feedback_read')
        addresses.add(command['value'])
        observed = micro.parse_event_line(micro.canonical_event(memory['content'][14:]))
        require(observed['event'] == command['value'] and observed['port'] in task['ports'],
                'invalid_public_feedback_record')
    if observed is None:
        advice = 'Initial instruction: READ EVENT ' + task['events'][0]
    elif observed['source'] == task['node'] and observed['destination'] == task['goal']:
        advice = ('Returned EVENT AT matches NODE and GOT matches GOAL. '
                  'Use that record DID: ROUTE ' + observed['port'])
    else:
        mismatches = []
        if observed['source'] != task['node']:
            mismatches.append('AT ' + observed['source'] + ' does not match NODE ' + task['node'])
        if observed['destination'] != task['goal']:
            mismatches.append('GOT ' + observed['destination'] + ' does not match GOAL ' + task['goal'])
        unread = [address for address in task['events'] if address not in addresses]
        require(bool(unread), 'public_feedback_no_unread_address_after_mismatch')
        advice = 'Mismatch: ' + '; '.join(mismatches) + '. Read unread listed address: READ EVENT ' + unread[0]
    return PUBLIC_FEEDBACK_PREFIX + advice


def _check_teaching_mode(teaching_mode):
    require(teaching_mode in (DEFAULT_TEACHING_MODE, PUBLIC_FEEDBACK_MODE), 'unknown_teaching_mode')


def guided_messages(messages, *, teaching_mode=DEFAULT_TEACHING_MODE):
    """Public-only transform; the default retains the exact legacy message view."""
    _check_teaching_mode(teaching_mode)
    _check_public_messages(messages)
    guided = controller._copy(messages)
    guided[0]['content'] += GUIDANCE
    if teaching_mode == PUBLIC_FEEDBACK_MODE:
        guided[0]['content'] += public_feedback(messages)
    return guided


class TeacherGuidedActor:
    """Count every attempted callback and preserve both message views."""

    def __init__(self, actor, *, teaching_mode=DEFAULT_TEACHING_MODE):
        _check_teaching_mode(teaching_mode)
        self.actor = actor
        self.teaching_mode = teaching_mode
        self.calls = []

    def __call__(self, messages):
        guided = guided_messages(messages, teaching_mode=self.teaching_mode)
        record = dict(call_index=len(self.calls), public_messages=controller._copy(messages),
                      guided_messages=controller._copy(guided), response=None, error=None)
        if self.teaching_mode != DEFAULT_TEACHING_MODE:
            record['teaching_mode'] = self.teaching_mode
        self.calls.append(record)
        try:
            response = self.actor(controller._copy(guided))
            if type(response) is dict:
                record['available_generation'] = {key: response.get(key) if type(response.get(key))
                    in (str, bool, int, type(None)) else None for key in ('raw', 'terminal', 'truncated')}
            record['response'] = controller._copy(response)
            return controller._copy(record['response'])
        except Exception as error:
            record['error'] = dict(type=type(error).__name__, message=str(error))
            raise


def teacher_guided_actor(native_actor, *, teaching_mode=DEFAULT_TEACHING_MODE):
    return TeacherGuidedActor(native_actor, teaching_mode=teaching_mode)


def _failure_kind(episode):
    reason = episode['terminal_reason']
    if reason.endswith(('_callback_error', '_invalid_response', '_non_json_response')) or reason in (
            'transition_error', 'invalid_outcome'):
        return 'infrastructure_failure'
    if reason.endswith('_nonterminal_or_truncated'):
        return 'generation_failure'
    if episode['reached_goal']:
        return 'selected' if episode['memory_calls'] >= 1 else 'reached_goal_without_read'
    return 'policy_failure'


def _rows_from_success(task, episode, calls, memory, transitions, episode_index, *,
                       teaching_mode=DEFAULT_TEACHING_MODE):
    """Replay actual captures to reconstruct student histories without the teacher."""
    _check_teaching_mode(teaching_mode)
    position = 0

    def captured_actor(messages):
        nonlocal position
        require(position < len(calls), 'missing_source_actor_call')
        call = calls[position]
        require(call['error'] is None and call['public_messages'] == messages
                and call.get('teaching_mode', DEFAULT_TEACHING_MODE) == teaching_mode
                and call['guided_messages'] == guided_messages(messages, teaching_mode=teaching_mode),
                'source_actor_message_mismatch')
        position += 1
        return controller._copy(call['response'])

    def external_read(address):
        return dict(raw=memory[address], terminal=True, truncated=False,
                    source='EXTERNAL_RETAINED_EVENT_TEXT_NOT_MODEL_GENERATION')

    replayed = controller.run_episode(task, captured_actor, external_read, lambda port: transitions[port])
    require(position == len(calls) and _bytes(replayed) == _bytes(episode), 'source_episode_replay_mismatch')
    require(replayed['reached_goal'] and replayed['memory_calls'] >= 1, 'read_and_reached_goal_required')
    traces = [trace for trace in replayed['traces'] if trace['kind'] == 'actor']
    require(len(traces) == len(calls), 'source_actor_count_mismatch')
    rows = []
    for trace, call in zip(traces, calls):
        response, prefix = call['response'], trace['messages']
        require(type(response) is dict and response.get('terminal') is True
                and response.get('truncated') is False and trace['raw'] == response.get('raw'),
                'valid_actual_generation_required')
        require(all(GUIDANCE not in message['content'] for message in prefix), 'teacher_forbidden_in_student_prefix')
        require(all(PUBLIC_FEEDBACK_PREFIX not in message['content'] for message in prefix),
                'teacher_forbidden_in_student_prefix')
        controller.parse_command(response['raw'])
        rows.append(dict(status='DRAFT_NOT_RELEASED', episode_index=episode_index,
            source_call_index=call['call_index'], prefix=controller._copy(prefix), assistant=response['raw'],
            target_eot='<|im_end|>', loss_policy=dict(prefix='MASK_ALL', assistant='TRAIN', eot='TRAIN')))
    return rows


def run_collection(bank, raw_memory_by_address, native_actor, *, teaching_mode=DEFAULT_TEACHING_MODE):
    """Collect four goal-paired attempts, at most 12 actor calls and 8 lookups.

    Inputs are a NEW four-fact bank and exact raw EVENT strings keyed by address.
    Validation precedes every actor call; this does not authenticate their native
    acquisition. All attempts/responses remain in the plain JSON result, including
    failures and successful no-read episodes. Infrastructure failures are explicit
    at collection level; selected rows are drafts, never automatic fit permission.
    Opt-in public_feedback_v1 records its mode on the result and source calls;
    absent mode keys retain the legacy fixed_guidance_v1 meaning and bytes.
    """
    validate_memory(bank, raw_memory_by_address)
    bank, memory = controller._copy(bank), controller._copy(raw_memory_by_address)
    teacher = teacher_guided_actor(native_actor, teaching_mode=teaching_mode)
    result = dict(claim=CLAIM, guidance=GUIDANCE, guidance_sha256=sha256(GUIDANCE.encode()).hexdigest(),
        bank=bank, bank_sha256=sha256(_bytes(bank)).hexdigest(), raw_memory_by_address=memory,
        memory_raw_sha256={address: sha256(raw.encode('utf-8')).hexdigest() for address, raw in memory.items()},
        planned_episodes=4, completed_episodes=0, episodes=[], actor_calls=teacher.calls, student_rows=[])
    if teaching_mode != DEFAULT_TEACHING_MODE:
        result['teaching_mode'] = teaching_mode

    def external_read(address):
        return dict(raw=memory[address], terminal=True, truncated=False,
                    source='EXTERNAL_RETAINED_EVENT_TEXT_NOT_MODEL_GENERATION')

    for episode_index, fact in enumerate(bank):
        task = controller.public_task(fact)
        transitions = {other['port']: other['outcome'] for other in bank if other['node'] == fact['node']}
        start = len(teacher.calls)
        episode = controller.run_episode(task, teacher, external_read, lambda port: transitions[port])
        end = len(teacher.calls)
        kind = _failure_kind(episode)
        record = dict(episode_index=episode_index, task=task, call_start=start, call_end=end,
                      episode=episode, classification=kind, selected=kind == 'selected')
        result['episodes'].append(record)
        result['completed_episodes'] += 1
        if record['selected']:
            result['student_rows'].extend(_rows_from_success(task, episode, teacher.calls[start:end],
                                                           memory, transitions, episode_index,
                                                           teaching_mode=teaching_mode))
    result.update(native_actor_calls=len(teacher.calls),
        physical_actor_calls=len(teacher.calls),
        external_memory_calls=sum(record['episode']['memory_calls'] for record in result['episodes']),
        reached_goal_episodes=sum(record['episode']['reached_goal'] for record in result['episodes']),
        selected_episodes=sum(record['selected'] for record in result['episodes']),
        selected_successes=sum(record['selected'] for record in result['episodes']),
        infrastructure_failures=sum(record['classification'] == 'infrastructure_failure' for record in result['episodes']))
    result['status'] = 'COLLECTION_FAILED_INFRASTRUCTURE' if result['infrastructure_failures'] else 'COLLECTION_COMPLETE_DRAFT_ONLY'
    result['student_rows_sha256'] = sha256(_bytes(result['student_rows'])).hexdigest()
    return controller._copy(result)
