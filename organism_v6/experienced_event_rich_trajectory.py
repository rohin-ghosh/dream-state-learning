"""Actual rich action captures and three paired supervision views; no fitting.

Four independent shards each have four TRAIN worlds and one untouched PROBE.
The frozen hop runtime executes only a strictly extracted action. Native raw
responses remain separate from projected action traces. Replay proves internal
consistency, not actor identity, loaded state, or natural-language truth.
Complete grounded episodes retain paired candidates even in partial shards;
the fixed planned-task manifest distinguishes failures from unattempted tasks.
"""

from copy import deepcopy
from functools import lru_cache
import hashlib
import re
from types import FunctionType

from organism_v6 import experienced_event_goal_pairs as goal


PREFIX = 'ASTRA-RICH-20260914-V1'
SHARDS = tuple(range(4))
FORMS = ('TERSE', 'RICH', 'RICH_ACTION_ONLY')
SCHEMA = 'DEV_EXPERIENCED_EVENT_RICH_TRAJECTORY_V1'
CRITIQUE_SCHEMA = 'DEV_EXPERIENCED_EVENT_RICH_CRITIQUES_V1'
MAX_CONTEXT = 2048
MAX_NEW_TOKENS = CRITIQUE_MAX_NEW_TOKENS = 512
ACTION_MAX_NEW_TOKENS = 160
EXPOSE_CALLS = 40
TEACH_CALLS = MAX_ROWS = 96
CRITIQUE_CALLS = 16
MAX_CALLS = TEACH_CALLS + CRITIQUE_CALLS
TOTAL_COLLECTION_CALLS = EXPOSE_CALLS + MAX_CALLS
TOTAL_ROWS = 384
CAPS = dict(expose_calls=40, rich_calls=96, critique_calls=16, total_collection_calls=152,
            max_context=2048, rich_max_new_tokens=512, critique_max_new_tokens=512,
            exposure_max_new_tokens=160, baseline_max_new_tokens=160)
TARGET_EOT = goal.TARGET_EOT
PARENT_GUIDANCE = goal.lesson.PARENT_GUIDANCE
PUBLIC_SYSTEM = (
    'Use the public CURRENT, GOAL, PORTS and EVENT addresses. One action per turn; '
    'wait for real feedback. READ EVENT <listedaddress> reads actual memory. '
    'ROUTE <listedport> commits at CURRENT; never route a node. At most four '
    'distinct reads and two routes, six turns total. Output either one command '
    'or RATIONALE\\n<explanation>\\nACTION\\n<one command> using actual LF separators. '
    'Only the action is executable. Explain only available public observations. '
    'Label forecasts with PREDICTION: ; a prediction is not an observed outcome.'
)
ARTICULATION = (
    'Produce the RATIONALE/ACTION envelope. Explain which available observations '
    'matter to the goal and the next action; use detail where useful, not padding. '
    'Include a nonempty PREDICTION: line about the next public reply. Never claim '
    'an unseen EVENT or receipt as observed. Do not copy this guidance.'
)
CRITIQUE_SYSTEM = (
    'Review this public action history. Identify an observed inconsistency or an '
    'unsupported inference, distinguish observations from predictions, and suggest '
    'one next check. You have no private state or teacher plan. Your critique is '
    'unreviewed candidate data, not a success label. Do not invent outcomes.'
)
PROTOCOL = dict(public_system=PUBLIC_SYSTEM, articulation=ARTICULATION, critique_system=CRITIQUE_SYSTEM)
STRICT_V1 = 'STRICT_V1'
ACTION_FIRST_V2 = 'ACTION_FIRST_V2'
ACTION_FIRST_PROTOCOL = dict(
    public_system=PUBLIC_SYSTEM.replace(
        'Label forecasts with PREDICTION: ; a prediction is not an observed outcome.',
        'Describe expected feedback as an expectation, not an observed outcome. '
        'Natural language is welcome; a PREDICTION: heading is optional.'),
    articulation=(
        'Produce the RATIONALE/ACTION envelope. Before a READ, identify what is '
        'still unknown and why to inspect it; never claim an unread EVENT as observed. '
        'Before a ROUTE, relate actually observed edges and the current node to '
        'the requested goal and chosen action. Describe the next expected feedback '
        'as a forecast, not an observation; a literal PREDICTION: heading is optional. '
        'Use useful detail, not padding. Do not invent receipts or copy this guidance.'),
    critique_system=CRITIQUE_SYSTEM)
require = goal.require
document_sha256 = goal.document_sha256
identifiers = goal.identifiers
_ID = re.compile(r'\b[NPER]_[A-Z2-7]{10}\b')


@lru_cache(maxsize=4)
def runtime(shard):
    """Private goal world/action API; collection below replaces old lesson API."""
    require(type(shard) is int and shard in SHARDS, 'fixed_rich_shard_required')
    prefix = PREFIX + '-SHARD-' + str(shard)
    trained = tuple(prefix + '-TRAIN-' + suffix for suffix in ('A', 'B', 'C', 'D'))
    probes = (prefix + '-PROBE-A',)
    namespace = dict(goal.__dict__, PREFIX=prefix, TRAIN_MASTERS=trained,
                     PROBE_MASTERS=probes, MASTERS=trained + probes, CAPS=deepcopy(CAPS))
    for name, function in goal.__dict__.items():
        original = function.__wrapped__ if name == '_runtime' else function
        if isinstance(original, FunctionType) and original.__globals__ is goal.__dict__:
            bound = FunctionType(original.__code__, namespace, original.__name__, original.__defaults__, original.__closure__)
            bound.__kwdefaults__ = original.__kwdefaults__
            namespace[name] = lru_cache(maxsize=5)(bound) if name == '_runtime' else bound
    for name in ('collect_lessons', 'replay_lessons', 'encode_rows'):
        namespace.pop(name)
    return namespace


def validate_registry(*, old_ids=()):
    seen = set(goal._old_ids(old_ids))
    registry = {}
    for shard in SHARDS:
        worlds = runtime(shard)['build_worlds'](old_ids=seen)
        for world in worlds['TRAIN'] + worlds['PROBE']:
            seen.update(identifiers(world))
        registry[shard] = worlds
    return registry


def build_worlds(shard, *, old_ids=()):
    runtime(shard)
    return validate_registry(old_ids=old_ids)[shard]


def _for_world(world):
    require(type(world) is dict, 'rich_world_required')
    for shard in SHARDS:
        if world.get('master') in runtime(shard)['MASTERS']:
            return runtime(shard)
    raise ValueError('closed_rich_world_required')


def collect_world(world, generate, *, old_ids=()):
    return _for_world(world)['collect_world'](world, generate, old_ids=old_ids)


def replay_collection(collection, *, old_ids=()):
    require(type(collection) is dict, 'rich_collection_required')
    return _for_world(collection.get('world'))['replay_collection'](collection, old_ids=old_ids)


def project_action(raw):
    """Exact UTF-8 byte and character spans; never scan for or repair commands."""
    require(type(raw) is str and raw.startswith('RATIONALE\n') and '\r' not in raw,
            'exact_rationale_action_envelope_required')
    require(raw.count('\nACTION\n') == 1 and '\nRATIONALE\n' not in raw, 'single_action_delimiter_required')
    rationale, action = raw[len('RATIONALE\n'):].split('\nACTION\n')
    require(bool(rationale.strip()), 'nonempty_rationale_required')
    goal.hop.commands.parse_command(action)
    start = len('RATIONALE\n') + len(rationale) + len('\nACTION\n')
    return dict(raw_sha256=hashlib.sha256(raw.encode('utf-8')).hexdigest(),
        rationale=rationale, action=action, rationale_span=[len('RATIONALE\n'), start - len('\nACTION\n')],
        action_span=[start, len(raw)],
        rationale_byte_span=[len('RATIONALE\n'), len(raw[:start - len('\nACTION\n')].encode('utf-8'))],
        action_byte_span=[len(raw[:start].encode('utf-8')), len(raw.encode('utf-8'))])


def _protocol(protocol):
    protocol = deepcopy(PROTOCOL if protocol is None else protocol)
    require(type(protocol) is dict and set(protocol) == set(PROTOCOL)
            and all(type(value) is str and value for value in protocol.values()), 'explicit_rich_protocol_required')
    return protocol


def _public(student, protocol):
    messages = deepcopy(student)
    messages[0] = dict(role='system', content=protocol['public_system'])
    return messages


def _coach(student, step, store, protocol):
    messages = deepcopy(student)
    sources = ''
    if step['command'].startswith('ROUTE '):
        observed = '\n'.join(message['content'] for message in student[1:])
        for address in step['source_events']:
            require(store[address] in observed, 'routing_source_must_already_be_public')
            sources += 'CAPTURED SOURCE EVENT (raw)\n' + store[address] + '\n'
    messages[-1]['content'] += ('\n\n' + PARENT_GUIDANCE + '\n'
        'Source-informed researcher instruction, not child-discovered planning.\n'
        + protocol['articulation'] + '\n' + sources
        + 'Execute only this next command, then wait for actual feedback:\n' + step['command'])
    return messages


def _validate_generation(outcome, messages):
    require(outcome['error'] is None, 'rich_native_callback_error')
    response = outcome['response']
    raw = goal.hop._generation(response, messages)
    if 'token_ids' in response:
        require(type(response['token_ids']) is list and 0 < len(response['token_ids']) <= MAX_NEW_TOKENS
                and all(type(token) is int and token >= 0 for token in response['token_ids']), 'rich_token_bound')
    if 'prompt_tokens' in response:
        require(type(response['prompt_tokens']) is int and 0 < response['prompt_tokens'] <= MAX_CONTEXT,
                'rich_context_bound')
    return raw


def _grounding(projection, student):
    seen = set(_ID.findall('\n'.join(message['content'] for message in student[1:])))
    mentioned = set(_ID.findall(projection['rationale']))
    require(mentioned <= seen, 'rationale_unseen_public_identifier')
    require(all(marker not in projection['rationale'] for marker in
                (PARENT_GUIDANCE, 'CAPTURED SOURCE EVENT (raw)', 'Execute only this next command')),
            'rationale_parent_guidance_echo')
    predictions = [line for line in projection['rationale'].splitlines()
                   if line.startswith('PREDICTION: ') and line[len('PREDICTION: '):].strip()]
    require(bool(predictions), 'explicit_prediction_line_required')
    return dict(seen_ids=sorted(seen), mentioned_ids=sorted(mentioned), prediction_lines=predictions,
                factual_truth_verified=False)


def _critique_messages(episode, protocol):
    history = '\n\n'.join(message['role'].upper() + '\n' + message['content']
                           for message in episode['messages'][1:])
    return [dict(role='system', content=protocol['critique_system']),
            dict(role='user', content='PUBLIC ACTION HISTORY\n' + history + '\n\nGive one grounded critique.')]


def _collect(shard, collections, old_ids, protocol, invoke, *, with_critiques=True, execution_policy=STRICT_V1):
    require(type(execution_policy) is str and execution_policy in (STRICT_V1, ACTION_FIRST_V2),
            'known_rich_execution_policy_required')
    action_first = execution_policy == ACTION_FIRST_V2
    bound = runtime(shard)
    old_ids = goal._old_ids(old_ids)
    validate_registry(old_ids=old_ids)
    protocol = _protocol(ACTION_FIRST_PROTOCOL if action_first and protocol is None else protocol)
    require(type(collections) in (list, tuple) and len(collections) == 4, 'four_rich_train_collections_required')
    collections = [replay_collection(collection, old_ids=old_ids) for collection in collections]
    require(tuple(collection['master'] for collection in collections) == bound['TRAIN_MASTERS'],
            'ordered_rich_train_only_no_probe')
    captures, critiques, episodes, summaries = [], [], [], []
    attempts = [dict(episode_id=collection['master'] + '/task/' + str(task_index),
        world_index=world_index, task_index=task_index, master=collection['master'],
        source_sha256=collection['collection_sha256'], attempted=False, complete=False,
        status='not_attempted_source_incomplete', call_indexes=[], episode_sha256=None)
        for world_index, collection in enumerate(collections) for task_index in goal.TASK_INDEXES]
    for world_index, collection in enumerate(collections):
        world_episodes = []
        if collection['ready']:
            store = bound['exact_text_store'](collection)
            for case in bound['build_cases'](collection)['cases']:
                first_call = len(captures)
                plan = case['plan']

                def actor(student):
                    call_index = len(captures)
                    episode_call = call_index - first_call
                    require(episode_call < 6 and call_index < TEACH_CALLS, 'rich_actor_call_cap')
                    public = _public(student, protocol)
                    guided = _coach(public, plan[episode_call], store, protocol)
                    capture = dict(call_index=call_index, native_call_index=call_index + len(critiques),
                        world_index=world_index, task_index=case['task_index'], episode_call_index=episode_call,
                        master=collection['master'], source_sha256=collection['collection_sha256'],
                        student_prefix=public, messages=guided, projection=None, grounding=None, validation_error=None,
                        **deepcopy(invoke('rich', guided)))
                    if action_first:
                        capture.update(execution_error=None, content_findings=[], prediction_label_present=None,
                                       content_review_status='UNREVIEWED')
                    try:
                        raw = _validate_generation(capture, guided)
                        capture['projection'] = project_action(raw)
                        if action_first:
                            capture['prediction_label_present'] = any(line.startswith('PREDICTION:')
                                for line in capture['projection']['rationale'].splitlines())
                            try:
                                capture['grounding'] = _grounding(capture['projection'], public)
                            except ValueError as error:
                                capture['content_findings'].append(dict(type=type(error).__name__, message=str(error)))
                        else:
                            capture['grounding'] = _grounding(capture['projection'], public)
                        return dict(raw=capture['projection']['action'], terminal=True, truncated=False)
                    except Exception as error:
                        capture['validation_error'] = dict(type=type(error).__name__, message=str(error))
                        if action_first:
                            capture['execution_error'] = deepcopy(capture['validation_error'])
                        raise
                    finally:
                        captures.append(goal.hop._seal(capture, 'call_sha256'))

                episode = bound['run_episode'](collection['world'], case['task'], actor, store.__getitem__)
                actual = captures[first_call:]
                matches = len(actual) == 6 and all(capture['validation_error'] is None
                    and capture['projection']['action'].rstrip('\n') == step['command']
                    for capture, step in zip(actual, plan))
                complete = (matches and episode['reached_goal'] and episode['route_calls'] == 2
                            and episode['memory_calls'] == 4 and episode['terminal_reason'] == 'reached_goal')
                attempt = attempts[world_index * 4 + case['task_index']]
                entry = dict(episode_id=attempt['episode_id'], world_index=world_index,
                    task_index=case['task_index'], master=collection['master'],
                    episode=episode, call_indexes=list(range(first_call, len(captures))), complete=complete,
                    failure=None if complete else episode['terminal_reason'])
                if action_first:
                    entry.update(action_complete=complete, content_review_status='UNREVIEWED')
                attempt.update(attempted=True, complete=complete, status='complete' if complete else 'failed',
                    call_indexes=list(entry['call_indexes']), episode_sha256=episode['episode_sha256'])
                episodes.append(entry)
                world_episodes.append(episode)
                if with_critiques:
                    messages = _critique_messages(episode, protocol)
                    critique = dict(critique_index=len(critiques), native_call_index=len(captures) + len(critiques),
                        world_index=world_index, task_index=case['task_index'], master=collection['master'],
                        episode_sha256=episode['episode_sha256'], messages=messages, validation_error=None,
                        candidate_only=True, reviewed=False, controls_selection=False,
                        **deepcopy(invoke('critique', messages)))
                    try:
                        require(bool(_validate_generation(critique, messages).strip()), 'nonempty_critique_required')
                    except Exception as error:
                        critique['validation_error'] = dict(type=type(error).__name__, message=str(error))
                    critiques.append(goal.hop._seal(critique, 'critique_sha256'))
        summaries.append(bound['summarize_pairs'](collection, world_episodes) if world_episodes else None)
    ready = len(captures) == TEACH_CALLS and len(episodes) == CRITIQUE_CALLS and all(entry['complete'] for entry in episodes)
    complete_episodes = sum(entry['complete'] for entry in episodes)
    candidate_count = complete_episodes * 6
    evidence = dict(schema=SCHEMA, phase='combined' if with_critiques else 'teach',
        shard=shard, masters=list(bound['TRAIN_MASTERS']), old_ids=old_ids,
        protocol=protocol, collections=collections, captures=captures, critiques=critiques, episodes=episodes,
        summaries=summaries, attempts=attempts, planned_task_count=CRITIQUE_CALLS, attempted_task_count=len(episodes),
        complete_episode_count=complete_episodes, candidate_row_count=candidate_count,
        candidate_policy='EVERY_COMPLETE_GROUNDED_TRAIN_EPISODE', complete_corpus=ready,
        ready=ready, primary_rows_ready=bool(candidate_count), candidate_rows_ready=bool(candidate_count), fit_ready=False, fits=0,
        model_calls=len(captures) + len(critiques), rich_calls=len(captures), critique_calls=len(critiques),
        expected_rich_calls=TEACH_CALLS, expected_critique_calls=CRITIQUE_CALLS if with_critiques else 0,
        state_binding='NATIVE_CALLER_REQUIRED', rationale_truth_verified=False,
        status='RICH_DATA_READY_NO_FIT' if ready else
               ('RICH_PARTIAL_CANDIDATES_NO_FIT' if candidate_count else 'RICH_DATA_INCOMPLETE_NO_FIT'))
    if action_first:
        evidence.update(execution_policy=ACTION_FIRST_V2, action_complete_count=complete_episodes,
            candidate_policy='EVERY_ACTION_COMPLETE_TRAIN_EPISODE_UNREVIEWED',
            candidate_only=True, reviewed=False, content_review_status='UNREVIEWED',
            status='ACTION_FIRST_CANDIDATES_UNREVIEWED_NO_FIT')
    return goal.hop._seal(evidence, 'evidence_sha256')


def _rows(evidence):
    rows = {form: [] for form in FORMS}
    selected = [(entry['episode_id'], call_index) for entry in evidence['episodes'] if entry['complete']
                for call_index in entry['call_indexes']]
    for index, (episode_id, call_index) in enumerate(selected):
        capture = evidence['captures'][call_index]
        for form in FORMS:
            raw = capture['response']['raw']
            assistant = capture['projection']['action'] if form == 'TERSE' else raw
            row = dict(schema=SCHEMA, form=form, row_index=index, call_index=call_index, episode_id=episode_id,
                shard=evidence['shard'], master=capture['master'],
                world_index=capture['world_index'], task_index=capture['task_index'],
                episode_call_index=capture['episode_call_index'], prefix=deepcopy(capture['student_prefix']),
                assistant=assistant, call_sha256=capture['call_sha256'], source_sha256=capture['source_sha256'],
                evidence_sha256=evidence['evidence_sha256'], target_eot=TARGET_EOT,
                action_span=[0, len(assistant)] if form == 'TERSE' else capture['projection']['action_span'],
                supervision='ACTION_AND_EOT' if form == 'RICH_ACTION_ONLY' else 'ASSISTANT_AND_EOT')
            if evidence.get('execution_policy') == ACTION_FIRST_V2:
                row.update(execution_policy=ACTION_FIRST_V2, candidate_only=True, reviewed=False,
                           content_review_status='UNREVIEWED', fit_ready=False)
            if index == 0 and form == 'TERSE':
                row['provenance'] = deepcopy(evidence)
            rows[form].append(goal.hop._seal(row, 'row_sha256'))
    return rows


def _document(evidence):
    rows = _rows(evidence)
    return goal.hop._seal(dict(evidence, rows=rows, candidate_rows=rows), 'lesson_sha256')


def collect_lessons(shard, collections, generate, critique_generate, *, old_ids=(), protocol=None):
    """Four ordered TRAIN sources; callbacks receive messages, rich/critic cap 512.

    Main supplies native callback limits and optional exact protocol strings.
    Exposure/baseline callbacks use 160 separately. Critics never select rows.
    rows/candidate_rows retain every complete episode; ready/complete_corpus
    report all-96 accounting only. No candidate availability enables fitting.
    """
    require(callable(generate) and callable(critique_generate), 'actual_rich_and_critique_callbacks_required')
    evidence = _collect(shard, collections, old_ids, protocol,
        lambda kind, messages: goal.hop._invoke(generate if kind == 'rich' else critique_generate, messages))
    return _document(evidence)


def collect_teaching(shard, collections, generate, *, old_ids=(), protocol=None, execution_policy=STRICT_V1):
    """TEACH only; explicit v2 executes valid actions despite content findings.

    STRICT_V1 keeps its original protocol and exact serialized evidence. V2
    defaults to ACTION_FIRST_PROTOCOL; every retained row remains unreviewed.
    """
    require(callable(generate), 'actual_rich_callback_required')
    evidence = _collect(shard, collections, old_ids, protocol,
        lambda kind, messages: goal.hop._invoke(generate, messages), with_critiques=False,
        execution_policy=execution_policy)
    return _document(evidence)


def _replay_evidence(evidence):
    require(type(evidence) is dict and evidence.get('schema') == SCHEMA, 'rich_evidence_required')
    require(evidence.get('phase') in ('teach', 'combined'), 'known_rich_collection_phase_required')
    pending = dict(rich=iter(deepcopy(evidence['captures'])), critique=iter(deepcopy(evidence['critiques'])))

    def invoke(kind, messages):
        capture = next(pending[kind], None)
        require(capture is not None, 'missing_actual_rich_or_critique_capture')
        goal.lesson._same(capture['messages'], messages, 'rich_native_prompt_replay_drift')
        return dict(response=capture['response'], error=capture['error'])

    verified = _collect(evidence['shard'], evidence['collections'], evidence['old_ids'], evidence['protocol'], invoke,
                        with_critiques=evidence['phase'] == 'combined',
                        execution_policy=evidence.get('execution_policy', STRICT_V1))
    require(all(next(captures, None) is None for captures in pending.values()), 'extra_rich_or_critique_capture')
    goal.lesson._same(evidence, verified, 'rich_evidence_replay_drift')
    return verified


def replay_lessons(document):
    require(type(document) is dict and document.get('schema') == SCHEMA, 'rich_lesson_required')
    evidence = {key: deepcopy(value) for key, value in document.items()
                if key not in ('rows', 'candidate_rows', 'lesson_sha256')}
    verified = _replay_evidence(evidence)
    rows = _rows(verified)
    goal.lesson._same(document, _document(verified), 'rich_document_replay_drift')
    return rows


def replay_teaching(document):
    """Replay teaching-only evidence and return every retained paired candidate."""
    require(type(document) is dict and document.get('phase') == 'teach', 'teaching_only_document_required')
    return replay_lessons(document)


def _collect_critiques(teaching, invoke):
    replay_teaching(teaching)
    critiques = []
    for entry in teaching['episodes']:
        require(len(critiques) < CRITIQUE_CALLS, 'rich_critique_call_cap')
        episode = entry['episode']
        messages = _critique_messages(episode, teaching['protocol'])
        critique = dict(critique_index=len(critiques), call_index=len(critiques), native_call_index=len(critiques),
            episode_id=entry['episode_id'], world_index=entry['world_index'], task_index=entry['task_index'],
            master=entry['master'], episode_sha256=episode['episode_sha256'],
            teaching_sha256=teaching['lesson_sha256'], messages=messages, validation_error=None,
            candidate_only=True, reviewed=False, controls_selection=False, **deepcopy(invoke(messages)))
        try:
            require(bool(_validate_generation(critique, messages).strip()), 'nonempty_critique_required')
        except Exception as error:
            critique['validation_error'] = dict(type=type(error).__name__, message=str(error))
        critiques.append(goal.hop._seal(critique, 'critique_sha256'))
    return goal.hop._seal(dict(schema=CRITIQUE_SCHEMA, phase='critique', shard=teaching['shard'],
        teaching=deepcopy(teaching), teaching_sha256=teaching['lesson_sha256'], critiques=critiques,
        planned_task_count=teaching['planned_task_count'], attempted_task_count=teaching['attempted_task_count'],
        expected_critique_calls=len(teaching['episodes']), model_calls=len(critiques), critique_calls=len(critiques),
        candidate_only=True, reviewed=False, controls_selection=False, fit_ready=False, fits=0,
        state_binding='NATIVE_CALLER_REQUIRED', status='CRITIQUE_CANDIDATES_ONLY'), 'critique_collection_sha256')


def collect_critiques(teaching, generate):
    """CRITIQUE process: one actual public-history call per attempted TRAIN episode."""
    require(callable(generate), 'actual_critique_callback_required')
    return _collect_critiques(teaching, lambda messages: goal.hop._invoke(generate, messages))


def replay_critiques(document):
    """Verify the saved teaching join and every actual critique, including failures."""
    require(type(document) is dict and document.get('schema') == CRITIQUE_SCHEMA, 'rich_critique_document_required')
    pending = iter(deepcopy(document['critiques']))

    def invoke(messages):
        critique = next(pending, None)
        require(critique is not None, 'missing_actual_critique_capture')
        goal.lesson._same(critique['messages'], messages, 'critique_public_prompt_replay_drift')
        return dict(response=critique['response'], error=critique['error'])

    verified = _collect_critiques(document['teaching'], invoke)
    require(next(pending, None) is None, 'extra_actual_critique_capture')
    goal.lesson._same(document, verified, 'critique_collection_replay_drift')
    return verified['critiques']


def compile_paired_rows(document):
    return replay_lessons(document)


def encode_paired_rows(rows, tokenizer, *, document=None):
    """Verify all retained candidates, in six-row episodes, without enabling fit.

    Empty candidates require their full document because no row can carry the
    provenance. Nonempty candidates keep provenance in their first TERSE row.
    """
    require(type(rows) is dict and set(rows) == set(FORMS)
            and all(type(rows[form]) in (list, tuple) for form in FORMS), 'all_three_candidate_forms_required')
    row_count = len(rows['TERSE'])
    require(0 <= row_count <= MAX_ROWS and row_count % 6 == 0
            and all(len(rows[form]) == row_count for form in FORMS), 'paired_complete_episode_row_counts_required')
    if document is not None:
        verified_rows = replay_lessons(document)
    else:
        require(row_count > 0, 'empty_candidate_rows_require_document')
        require(type(rows['TERSE'][0]) is dict and 'provenance' in rows['TERSE'][0], 'candidate_provenance_required')
        verified_rows = _rows(_replay_evidence(rows['TERSE'][0]['provenance']))
    goal.lesson._same(rows, verified_rows, 'rich_paired_rows_replay_drift')
    if row_count == 0:
        return dict(encoded={form: () for form in FORMS}, ledger=[], equal_compute_claim=False, fits=0)
    native = goal.native
    require(tokenizer.eos_token == TARGET_EOT and type(tokenizer.eos_token_id) is int
            and native._encode(tokenizer, TARGET_EOT) == (tokenizer.eos_token_id,), 'exact_rich_eot_required')
    encoded, ledger = {form: [] for form in FORMS}, []
    for index in range(row_count):
        counts = {}
        for form in FORMS:
            row = rows[form][index]
            prefix, assistant = row['prefix'], row['assistant']
            context = tokenizer.apply_chat_template(prefix, tokenize=False, add_generation_prompt=True, return_dict=False)
            messages = prefix + [dict(role='assistant', content=assistant)]
            full = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=False, return_dict=False)
            require(full == context + assistant + TARGET_EOT + '\n', 'exact_rich_template_boundary_required')
            prefix_ids = native._encode(tokenizer, context)
            before_action = native._encode(tokenizer, assistant[:row['action_span'][0]])
            action_ids = native._encode(tokenizer, assistant[row['action_span'][0]:])
            assistant_ids = native._encode(tokenizer, assistant)
            suffix_ids = native._encode(tokenizer, '\n')
            eot = (tokenizer.eos_token_id,)
            sequence = native._encode(tokenizer, full)
            require(assistant_ids == before_action + action_ids and sequence == prefix_ids + assistant_ids + eot + suffix_ids,
                    'exact_rich_action_token_boundary_required')
            require(not set(tokenizer.all_special_ids).intersection(assistant_ids), 'rich_target_special_token_forbidden')
            limit = ACTION_MAX_NEW_TOKENS if form == 'TERSE' else MAX_NEW_TOKENS
            require(len(sequence) <= MAX_CONTEXT and len(assistant_ids) + 1 <= limit, 'untruncated_rich_sequence_required')
            require(native._decode(tokenizer, sequence) == full and native._decode(tokenizer, action_ids) == assistant[row['action_span'][0]:]
                    and native._decode(tokenizer, prefix_ids) == context and native._decode(tokenizer, suffix_ids) == '\n'
                    and native._decode(tokenizer, assistant_ids + eot) == assistant + TARGET_EOT, 'rich_token_roundtrip_failed')
            require(tuple(tokenizer.apply_chat_template(messages, tokenize=True, add_generation_prompt=False,
                return_dict=False, truncation=False, padding=False)) == sequence, 'rich_template_token_ids_mismatch')
            active = action_ids + eot if form == 'RICH_ACTION_ONLY' else assistant_ids + eot
            masked = len(prefix_ids) + (len(before_action) if form == 'RICH_ACTION_ONLY' else 0)
            encoded[form].append(native.EncodedRow(sequence, (-100,) * masked + active + (-100,) * len(suffix_ids), active))
            counts[form] = dict(input_tokens=len(sequence), active_tokens=len(active), action_tokens=len(action_ids),
                rationale_and_delimiter_tokens=len(before_action), eot_tokens=1, masked_tokens=len(sequence) - len(active))
        require(encoded['RICH'][-1].input_ids == encoded['RICH_ACTION_ONLY'][-1].input_ids, 'paired_rich_inputs_drift')
        ledger.append(dict(row_index=index, episode_id=rows['TERSE'][index]['episode_id'],
                           call_index=rows['TERSE'][index]['call_index'],
                           call_sha256=rows['TERSE'][index]['call_sha256'], forms=counts))
    return dict(encoded={form: tuple(values) for form, values in encoded.items()}, ledger=ledger,
                equal_compute_claim=False, fits=0)
