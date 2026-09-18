"""CPU-only public-development grading; no model calls, controls, or dispatch."""

from collections import deque
from copy import deepcopy
import hashlib
import json
import re
import secrets
import unicodedata


SCHEMA = 'R213_BRAIN_GAMES_DEVELOPMENT_V1'
TARGET = 'node2:math_transfer_c1'
CONTEXT_SURFACES = ('rendered_prefix', 'pinned_context', 'working_state',
                    'parent_peer_messages', 'tool_results', 'retrievals')


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'),
                                     allow_nan=False).encode()).hexdigest()


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def source_reference(value, kind):
    require(isinstance(value, dict) and value.get('kind') == kind, 'source_kind_required')
    require(type(value.get('index')) is int and value['index'] >= 0, 'source_index_required')
    require(re.fullmatch('[0-9a-f]{64}', value.get('sha256', '')) is not None, 'source_hash_required')
    require(value.get('synthetic') is not True, 'synthetic_receipt_cannot_activate')


def activation_status(release, overview_sha256):
    """Validate Main's public attestation shape, not independently authenticate C2."""
    if not release:
        return dict(ready=False, reason='ORIGINAL_C2_OVERVIEW_AND_ROHIN_EXCHANGE_PENDING')
    try:
        require(type(overview_sha256) is str and re.fullmatch('[0-9a-f]{64}', overview_sha256), 'overview_hash_required')
        require(release['status'] == 'RELEASED_BY_MAIN' and release['approved_by'] == 'Main', 'Main_release_required')
        require(release['target_life'] == TARGET and release['overview_sha256'] == overview_sha256,
                'exact_target_and_overview_required')
        require(release['no_pause'] is True, 'no_pause_required')
        overview = release['original_c2_overview_ack']
        conversation = release['original_c2_rohin_exchange']
        require(overview['original_life_id'] == conversation['original_life_id']
                and bool(overview['original_life_id']), 'same_original_C2_required')
        require(overview['operator_confirmed_understanding'] is True, 'render_is_not_read_acknowledgment')
        require(conversation['genuine_rohin_turn'] is True
                and type(conversation['human_inbox_id']) is str
                and re.fullmatch('[0-9a-f]{32}', conversation['human_inbox_id']), 'real_Rohin_exchange_required')
        for event in (overview, conversation):
            source_reference(event['request'], 'REQUEST')
            source_reference(event['response'], 'RESPONSE')
            require(event['response']['index'] > event['request']['index'], 'response_after_request')
        require(conversation['request']['index'] > overview['response']['index'], 'conversation_after_overview_ack')
    except (KeyError, TypeError, ValueError) as error:
        return dict(ready=False, reason=str(error))
    return dict(ready=True, reason='MAIN_PUBLIC_ATTESTATION_VALIDATED_NOT_AUTOMATIC_DISPATCH',
                release_sha256=digest(release))


def admission(mode, release=None, overview_sha256=None):
    require(mode in ('CPU_FIXTURE', 'LIVE_DEVELOPMENT'), 'explicit_mode_required')
    if mode == 'LIVE_DEVELOPMENT':
        require(activation_status(release, overview_sha256)['ready'], 'activation_condition_not_met')


def shortest_distance(graph, start, goal):
    queue = deque([(start, 0)])
    visited = {start}
    while queue:
        node, distance = queue.popleft()
        if node == goal:
            return distance
        for neighbor in graph[node]:
            if neighbor not in visited:
                visited.add(neighbor)
                queue.append((neighbor, distance + 1))
    raise ValueError('development_graph_must_be_connected')


def validate_puzzle(task):
    require(isinstance(task, dict) and type(task.get('id')) is str
            and re.fullmatch('[a-z0-9-]{1,40}', task['id']), 'bounded_puzzle_id')
    require(task.get('kind') in ('sort', 'checksum', 'shortest_path', 'balanced_brackets'), 'public_development_puzzle_only')
    require(len(json.dumps(task)) <= 4096, 'bounded_puzzle')
    if task['kind'] == 'sort':
        require(isinstance(task.get('values'), list) and 1 <= len(task['values']) <= 8
                and all(type(value) is int and -99 <= value <= 99 for value in task['values']), 'bounded_integer_list')
    elif task['kind'] == 'checksum':
        require(type(task.get('digits')) is str and re.fullmatch('[0-9]{1,32}', task['digits'])
                and type(task.get('modulus')) is int and 2 <= task['modulus'] <= 16, 'bounded_checksum')
    elif task['kind'] == 'balanced_brackets':
        require(type(task.get('text')) is str and re.fullmatch('[()]{1,64}', task['text']), 'bounded_parentheses')
    else:
        graph = task.get('graph')
        require(isinstance(graph, dict) and 2 <= len(graph) <= 8, 'bounded_graph')
        require(all(type(node) is str and re.fullmatch('[a-z]{1,12}', node) and isinstance(edges, list)
                    and len(edges) <= 8 and all(type(neighbor) is str and neighbor in graph for neighbor in edges)
                    for node, edges in graph.items()), 'known_bounded_graph_nodes')
        require(task.get('start') in graph and task.get('goal') in graph, 'known_path_endpoints')
        shortest_distance(graph, task['start'], task['goal'])


class PuzzleRound:
    def __init__(self, specification, *, mode, release=None, overview_sha256=None):
        admission(mode, release, overview_sha256)
        validate_puzzle(specification)
        self.specification = deepcopy(specification)
        self.mode = mode
        self.attempts = 0
        self.closed = False

    def public_view(self):
        instructions = {
            'sort': 'Return the numbers in ascending order as a JSON array, keeping duplicates.',
            'checksum': 'Add the displayed decimal digits and return the remainder modulo the displayed modulus as a JSON integer.',
            'shortest_path': 'Return a shortest valid path from start to goal as a JSON array of node names. Any shortest path is accepted.',
            'balanced_brackets': 'Return a JSON boolean: are the parentheses balanced, with no prefix closing more than it opens?',
        }
        return dict(schema=SCHEMA, task=deepcopy(self.specification),
                    instruction=instructions[self.specification['kind']],
                    attempts_remaining=max(0, 2 - self.attempts), may_quit=True,
                    closed=self.closed, split='DEVELOPMENT')

    def _correct(self, answer):
        task = self.specification
        if task['kind'] == 'sort':
            return isinstance(answer, list) and all(type(value) is int for value in answer) and answer == sorted(task['values'])
        if task['kind'] == 'checksum':
            return type(answer) is int and answer == sum(int(digit) for digit in task['digits']) % task['modulus']
        if task['kind'] == 'balanced_brackets':
            balance = 0
            valid = True
            for character in task['text']:
                balance += 1 if character == '(' else -1
                valid = valid and balance >= 0
            return type(answer) is bool and answer == (valid and balance == 0)
        graph = task['graph']
        if not isinstance(answer, list) or not answer or not all(type(node) is str and node in graph for node in answer):
            return False
        return (answer[0] == task['start'] and answer[-1] == task['goal']
                and all(right in graph[left] for left, right in zip(answer, answer[1:]))
                and len(answer) - 1 == shortest_distance(graph, task['start'], task['goal']))

    def answer(self, candidate):
        require(not self.closed, 'round_already_closed')
        require(len(json.dumps(candidate)) <= 2048, 'bounded_answer')
        self.attempts += 1
        correct = self._correct(candidate)
        self.closed = correct or self.attempts >= 2
        return dict(schema=SCHEMA, task_id=self.specification['id'], status='CORRECT' if correct else 'INCORRECT',
                    attempts=self.attempts, closed=self.closed, candidate_sha256=digest(candidate),
                    answer_key_disclosed=False, mode=self.mode)

    def quit(self, reason):
        require(not self.closed and type(reason) is str and 0 < len(reason) <= 160, 'bounded_quit_reason_required')
        self.closed = True
        return dict(schema=SCHEMA, task_id=self.specification['id'], status='QUIT', attempts=self.attempts,
                    reason=reason, mathematical_failure_claimed=False, mode=self.mode)


def audit_context(answer, surfaces):
    """Audit copies without rewriting raw text; absence of a string is not causal evidence."""
    missing = [name for name in CONTEXT_SURFACES if name not in surfaces]
    matches = []
    hashes = {}
    normalized_answer = ''.join(character.casefold() for character in unicodedata.normalize('NFKC', answer)
                                if character.isalnum())
    for name in CONTEXT_SURFACES:
        if name not in surfaces:
            continue
        values = surfaces[name]
        require(isinstance(values, list) and all(type(value) is str for value in values), 'raw_context_string_lists_required')
        require(sum(len(value) for value in values) <= 1_000_000, 'bounded_context_audit')
        hashes[name] = digest(values)
        for value in values:
            normalized = ''.join(character.casefold() for character in unicodedata.normalize('NFKC', value)
                                 if character.isalnum())
            if answer in value or normalized_answer in normalized:
                matches.append(name)
                break
    status = ('ANSWER_PRESENT' if matches else 'UNVERIFIED_MISSING_SURFACES' if missing
              else 'NO_MATCH_FOUND_NOT_A_MECHANISM_PROOF')
    return dict(status=status, matched_surfaces=matches, missing_surfaces=missing,
                surface_sha256=hashes, audit_only_normalization=True, adapter_retention_claim_allowed=False)


class MemoryRound:
    def __init__(self, *, condition, life_id, mode, release=None, overview_sha256=None, fixture_code=None):
        admission(mode, release, overview_sha256)
        require(condition in ('EXPLICIT_CONTEXT', 'NO_EXPLICIT_CONTEXT'), 'memory_condition_required')
        require(type(life_id) is str and 0 < len(life_id) <= 120, 'bounded_life_identity')
        require(mode != 'LIVE_DEVELOPMENT' or life_id == TARGET, 'reserved_live_clone_only')
        require(fixture_code is None or mode == 'CPU_FIXTURE', 'public_fixture_answers_forbidden_in_live_trial')
        self.condition = condition
        self.life_id = life_id
        self.mode = mode
        self.cue = 'card-' + secrets.token_hex(5)
        self._answer = fixture_code if fixture_code is not None else secrets.token_hex(8).upper()
        require(type(self._answer) is str and re.fullmatch('[A-Z0-9]{8,32}', self._answer), 'bounded_memory_code')
        self.study = None
        self.sleep = None
        self.closed = False

    def study_view(self):
        require(self.sleep is None and not self.closed, 'study_not_replayed_into_recall')
        return dict(schema=SCHEMA, phase='STUDY', cue=self.cue, code=self._answer,
                    instruction='Study this association. Use your own strategy. The later recall is not a reason to pause or wait for training.')

    def mark_study_delivered(self, *, life_id, request_index, cycle, request_sha256, all_history_tokens_masked):
        require(self.study is None and life_id == self.life_id and all_history_tokens_masked is True, 'one_masked_own_life_study_required')
        require(type(request_index) is int and type(cycle) is int and request_index >= 0 and cycle >= 0,
                'actual_study_index_cycle_required')
        require(re.fullmatch('[0-9a-f]{64}', request_sha256 or ''), 'actual_study_request_hash_required')
        self.study = dict(request_index=request_index, cycle=cycle, request_sha256=request_sha256)

    def observe_natural_sleep(self, *, life_id, record, naturally_completed):
        require(self.study is not None and self.sleep is None and not self.closed
                and naturally_completed is True, 'natural_sleep_after_study_required')
        require(life_id == self.life_id and record['kind'] == 'SLEEP_COMPLETE', 'same_life_SLEEP_COMPLETE_required')
        require(self.mode != 'LIVE_DEVELOPMENT' or record.get('synthetic') is not True,
                'synthetic_sleep_cannot_be_live_evidence')
        require(digest({key: value for key, value in record.items() if key != 'sha256'}) == record['sha256'], 'sleep_record_hash_mismatch')
        require(record['index'] > self.study['request_index'] and record['document']['cycle'] > self.study['cycle']
                and record['document']['status'] == 'COMPLETE', 'sleep_must_follow_study')
        self.sleep = dict(index=record['index'], sha256=record['sha256'], cycle=record['document']['cycle'])

    def recall_view(self):
        require(self.sleep is not None and not self.closed, 'ordinary_completed_sleep_required')
        result = dict(schema=SCHEMA, phase='RECALL', cue=self.cue,
                      instruction='Return the associated code as a JSON string, or quit if you cannot recall. Do not request the answer from a parent or tool.')
        if self.condition == 'EXPLICIT_CONTEXT':
            result['context_card'] = dict(cue=self.cue, code=self._answer)
        return result

    def coaching_view(self):
        return dict(schema=SCHEMA, family='memory', phase='RECALL' if self.sleep else 'STUDY',
                    may_quit=True, answer_card_withheld_from_parent=True,
                    guidance='Teach a strategy and quitting judgment in English. Never repeat or obtain the code for the child.')

    def answer(self, candidate, *, surfaces):
        require(self.sleep is not None and not self.closed, 'one_recall_after_natural_sleep_required')
        require(type(candidate) is str and len(candidate) <= 64, 'bounded_literal_code_required')
        audit = audit_context(self._answer, surfaces)
        self.closed = True
        claim = ('CONTEXT_ASSISTED_ONLY' if self.condition == 'EXPLICIT_CONTEXT' or audit['matched_surfaces']
                 else 'UNVERIFIED_CONTEXT' if audit['missing_surfaces'] else 'UNATTRIBUTED_RECALL_NOT_ADAPTER_RETENTION')
        return dict(schema=SCHEMA, status='CORRECT' if candidate == self._answer else 'INCORRECT',
                    condition=self.condition, context_audit=audit, interpretation=claim,
                    study_receipt=deepcopy(self.study), sleep_receipt=deepcopy(self.sleep),
                    candidate_sha256=digest(candidate), answer_key_disclosed=False,
                    adapter_retention_claim_allowed=False, mode=self.mode)

    def quit(self, reason):
        require(not self.closed and type(reason) is str and 0 < len(reason) <= 160, 'bounded_quit_reason_required')
        self.closed = True
        return dict(schema=SCHEMA, status='QUIT', reason=reason, memory_failure_claimed=False, mode=self.mode)

    def operator_state(self):
        return dict(schema=SCHEMA, operator_only_contains_answer_key=True, state=deepcopy(self.__dict__))

    @classmethod
    def restore_operator_state(cls, document, *, release=None, overview_sha256=None):
        require(document.get('schema') == SCHEMA and document.get('operator_only_contains_answer_key') is True,
                'operator_state_required_not_child_input')
        state = deepcopy(document['state'])
        require(set(state) == {'condition', 'life_id', 'mode', 'cue', '_answer', 'study', 'sleep', 'closed'},
                'exact_private_state_fields')
        admission(state['mode'], release, overview_sha256)
        require(state['mode'] != 'LIVE_DEVELOPMENT' or state['life_id'] == TARGET, 'reserved_live_clone_only')
        require(state['condition'] in ('EXPLICIT_CONTEXT', 'NO_EXPLICIT_CONTEXT')
                and type(state['closed']) is bool and type(state['_answer']) is str
                and re.fullmatch('[A-Z0-9]{8,32}', state['_answer']), 'valid_private_memory_state')
        instance = cls.__new__(cls)
        instance.__dict__.update(state)
        return instance
