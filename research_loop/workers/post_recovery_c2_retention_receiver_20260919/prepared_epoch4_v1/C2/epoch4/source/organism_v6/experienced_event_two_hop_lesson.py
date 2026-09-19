"""Bounded researcher-coached child trajectories on the exposed DEV graph.

The parent is algorithmic/source-informed instruction, not child planning.
Only actual child turns from both complete strict episodes become sleep rows.
Hashes and replay establish internal consistency, not actor authentication;
the caller binds the native actor and original collection artifacts. No fit,
model scoring, clean-transfer claim, or H1/H2 evidence is produced here.
"""

from copy import deepcopy

from gpu import astra_pchain2_native as native
from organism_v6 import experienced_event_two_hop as hop


SCHEMA = 'DEV_EXPERIENCED_EVENT_TWO_HOP_LESSON_V1'
DEV = 'DEV'
PROTOCOL = 'turnbound'
TASK_INDEXES = (0, 2)
MAX_CALLS = 12
MAX_ROWS = 12
MAX_CONTEXT = 2048
MAX_NEW_TOKENS = hop.MAX_NEW_TOKENS
TARGET_EOT = '<|im_end|>'
LOSS_POLICY = dict(prefix='MASK_ALL', assistant='TRAIN', eot='TRAIN', suffix='MASK_ALL')
PARENT_GUIDANCE = 'PARENT PROCEDURAL GUIDANCE'
require = hop.require
document_sha256 = hop.document_sha256


def _same(actual, expected, reason):
    require(document_sha256(actual) == document_sha256(expected), reason)


def _plan(task, store):
    records = {address: hop.micro.parse_event_line(hop.micro.canonical_event(raw))
               for address, raw in store.items()}
    require(all(record['event'] == address for address, record in records.items()),
            'source_address_drift')
    paths = [(first, second) for first in records.values() for second in records.values()
             if first['source'] == task['node'] and first['destination'] == second['source']
             and second['destination'] == task['goal'] and first['event'] != second['event']]
    require(len(paths) == 1, 'unique_source_supported_two_hop_path_required')
    first, second = paths[0]
    steps = [dict(command='READ EVENT ' + address, source_events=[address]) for address in task['events']]
    steps += [dict(command='ROUTE ' + first['port'], source_events=[first['event'], second['event']]),
              dict(command='ROUTE ' + second['port'], source_events=[second['event']])]
    return steps


def _coached_messages(student, step, store):
    require(type(student) is list and student[-1]['role'] == 'user', 'last_student_user_required')
    messages = deepcopy(student)
    sources = ''.join('CAPTURED SOURCE EVENT (raw)\n' + store[address] + '\n'
                      for address in step['source_events'])
    messages[-1]['content'] += (
        '\n\n' + PARENT_GUIDANCE + '\n'
        'Algorithmic/source-informed researcher-prepared instruction; not child planning.\n'
        'Read the four public EVENT addresses in display order before routing. '
        'For routing, join captured GOT to AT, ending at the public GOAL; use DID ports, not nodes.\n'
        + sources + 'Execute only this next command, then wait for actual feedback:\n' + step['command'])
    return messages


def _collect(collection, invoke):
    collection = hop.replay_collection(collection)
    world = collection['world']
    captures, episodes = [], []
    if collection['ready']:
        store = hop.exact_text_store(collection)
        tasks = hop.build_tasks(world)
        for episode_index, task_index in enumerate(TASK_INDEXES):
            task = tasks[task_index]
            plan = _plan(task, store)
            episode_call = 0

            def actor(student):
                nonlocal episode_call
                require(episode_call < len(plan) and len(captures) < MAX_CALLS, 'lesson_call_cap')
                guided = _coached_messages(student, plan[episode_call], store)
                outcome = invoke(deepcopy(guided))
                capture = dict(call_index=len(captures), episode_index=episode_index,
                    task_index=task_index, episode_call_index=episode_call,
                    student_prefix=deepcopy(student), messages=guided, **deepcopy(outcome))
                captures.append(hop._seal(capture, 'call_sha256'))
                episode_call += 1
                require(capture['error'] is None, 'lesson_callback_error')
                response = capture['response']
                if type(response) is dict:
                    if 'messages' in response:
                        _same(response['messages'], guided, 'lesson_generation_prompt_drift')
                    return {key: deepcopy(response[key]) for key in ('raw', 'terminal', 'truncated')
                            if key in response}
                return deepcopy(response)

            episode = hop.run_episode(world, task, actor, store.__getitem__, protocol=PROTOCOL)
            actual = [trace for trace in episode['traces'] if trace['kind'] == 'actor']
            matches = len(actual) == len(plan) and all(
                trace['error'] is None and type(trace['response']) is dict
                and type(trace['response'].get('raw')) is str
                and trace['response']['raw'].rstrip('\n') == step['command']
                for trace, step in zip(actual, plan))
            complete = (episode['reached_goal'] and episode['terminal_reason'] == 'reached_goal'
                        and episode['route_calls'] == 2 and episode['memory_calls'] == 4 and matches)
            episodes.append(dict(episode_index=episode_index, task_index=task_index,
                plan=plan, episode=episode, complete=complete,
                failure=None if complete else ('actual_commands_differ_from_plan'
                    if episode['reached_goal'] else episode['terminal_reason'])))
    ready = len(episodes) == 2 and all(item['complete'] for item in episodes) and len(captures) == MAX_CALLS
    return hop._seal(dict(schema=SCHEMA, split=DEV, protocol=PROTOCOL, collection=deepcopy(collection),
        source_sha256=collection['collection_sha256'], task_indexes=list(TASK_INDEXES),
        episodes=episodes, captures=captures, model_calls=len(captures), expected_calls=MAX_CALLS,
        ready=ready, fits=0, parent_present=True,
        parent_kind='ALGORITHMIC_SOURCE_INFORMED_RESEARCHER_PREPARED_NOT_CHILD_PLANNING',
        claim='EXPOSED_DEV_GRAPH_COACHED_ACTUAL_TRAJECTORIES_NOT_CLEAN_TRANSFER_OR_H1_H2',
        status='LESSONS_READY_NO_FIT' if ready else 'LESSONS_INCOMPLETE_NO_FIT'), 'evidence_sha256')


def _rows(evidence):
    if not evidence['ready']:
        return []
    rows = []
    for capture in evidence['captures']:
        episode = evidence['episodes'][capture['episode_index']]['episode']
        row = dict(schema=SCHEMA, split=DEV, row_index=len(rows),
            prefix=deepcopy(capture['student_prefix']), assistant=capture['response']['raw'],
            call_index=capture['call_index'], episode_index=capture['episode_index'],
            task_index=capture['task_index'], episode_call_index=capture['episode_call_index'],
            call_sha256=capture['call_sha256'], episode_sha256=episode['episode_sha256'],
            source_sha256=evidence['source_sha256'], target_eot=TARGET_EOT,
            loss_policy=deepcopy(LOSS_POLICY), provenance=deepcopy(evidence))
        rows.append(hop._seal(row, 'row_sha256'))
    return rows


def collect_lessons(collection, generate):
    """Capture both public order-0 tasks, without retry, repair, fitting or scoring.

    generate(deepcopy(coached_messages)) returns a native generation dictionary.
    document['captures'] is flat native call order, with zero-based call_index
    and messages/response/error matching the caller's saved CALL records.
    messages is the actual coached prompt; response retains the complete native
    dictionary, including its prompt echo and any additional metadata.
    The episode receives only raw/terminal/truncated; messages is omitted, never
    relabeled as the student prompt. Replay verifies this exact projection.
    Optional final LFs are protocol-legal and preserved in the target.
    Incomplete source collections invoke no actor.
    """
    require(callable(generate), 'generation_callback_required')
    evidence = _collect(collection, lambda messages: hop._invoke(generate, messages))
    return hop._seal(dict(evidence, rows=_rows(evidence)), 'lesson_sha256')


def _replay_evidence(evidence):
    require(type(evidence) is dict and evidence.get('schema') == SCHEMA, 'two_hop_lesson_required')
    captures = iter(deepcopy(evidence['captures']))

    def invoke(messages):
        capture = next(captures, None)
        require(capture is not None, 'missing_lesson_call')
        _same(capture['messages'], messages, 'lesson_coached_prompt_drift')
        return dict(response=capture['response'], error=capture['error'])

    verified = _collect(evidence['collection'], invoke)
    require(next(captures, None) is None, 'unknown_lesson_call')
    _same(evidence, verified, 'lesson_evidence_replay_drift')
    return verified


def replay_lessons(document):
    """Rebuild source plan, guidance, callbacks, transitions and exact row targets."""
    require(type(document) is dict and document.get('schema') == SCHEMA, 'two_hop_lesson_required')
    evidence = {key: deepcopy(value) for key, value in document.items() if key not in ('rows', 'lesson_sha256')}
    verified = _replay_evidence(evidence)
    rows = _rows(verified)
    _same(document, hop._seal(dict(verified, rows=rows), 'lesson_sha256'), 'lesson_document_replay_drift')
    return rows


def encode_rows(rows, tokenizer):
    """Encode the complete verified corpus; mask all history and the suffix LF."""
    require(type(rows) in (list, tuple) and len(rows) == MAX_ROWS, 'complete_nonempty_lesson_corpus_required')
    require(type(rows[0]) is dict and 'provenance' in rows[0], 'lesson_row_provenance_required')
    evidence = _replay_evidence(rows[0]['provenance'])
    _same(list(rows), _rows(evidence), 'lesson_row_target_or_provenance_drift')
    require(tokenizer.eos_token == TARGET_EOT and type(tokenizer.eos_token_id) is int
            and native._encode(tokenizer, TARGET_EOT) == (tokenizer.eos_token_id,), 'exact_lesson_eot_required')
    encoded = []
    for row in rows:
        prefix = row['prefix']
        require([message['role'] for message in prefix] == ['system', 'user']
                + ['assistant', 'user'] * row['episode_call_index'], 'alternating_student_prefix_required')
        messages = prefix + [dict(role='assistant', content=row['assistant'])]
        context = tokenizer.apply_chat_template(prefix, tokenize=False, add_generation_prompt=True, return_dict=False)
        full = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=False, return_dict=False)
        require(full == context + row['assistant'] + TARGET_EOT + '\n', 'exact_lesson_template_boundary_required')
        prefix_ids = native._encode(tokenizer, context)
        target = native._encode(tokenizer, row['assistant'])
        suffix = native._encode(tokenizer, '\n')
        require(not set(tokenizer.all_special_ids).intersection(target), 'lesson_target_special_token_forbidden')
        supervised = target + (tokenizer.eos_token_id,)
        sequence = native._encode(tokenizer, full)
        require(sequence == prefix_ids + supervised + suffix and len(sequence) <= MAX_CONTEXT,
                'untruncated_exact_lesson_sequence_required')
        require(native._decode(tokenizer, sequence) == full
                and native._decode(tokenizer, prefix_ids) == context
                and native._decode(tokenizer, supervised) == row['assistant'] + TARGET_EOT
                and native._decode(tokenizer, suffix) == '\n', 'lesson_token_roundtrip_failed')
        require(tuple(tokenizer.apply_chat_template(messages, tokenize=True, add_generation_prompt=False,
            return_dict=False, truncation=False, padding=False)) == sequence, 'lesson_template_token_ids_mismatch')
        encoded.append(native.EncodedRow(sequence, (-100,) * len(prefix_ids) + supervised
                                       + (-100,) * len(suffix), supervised))
    return tuple(encoded)
