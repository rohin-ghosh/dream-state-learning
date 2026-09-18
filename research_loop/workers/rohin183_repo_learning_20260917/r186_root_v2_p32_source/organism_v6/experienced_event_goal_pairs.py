"""Source-grounded paired-goal lessons in four closed, disjoint namespaces.

Pure capture/replay and encoding with a caller-supplied tokenizer. The frozen
hop bytecode is privately bound to each master, never globally monkeypatched.
Replay establishes consistency, not native actor identity; callers bind actors
and source artifacts. TRAIN needs both worlds and all 48 actual child turns.
PROBE worlds can be collected/evaluated but never admitted to lesson fitting.
"""

from copy import deepcopy
from functools import lru_cache
from types import FunctionType

from organism_v6 import experienced_event_two_hop as hop
from organism_v6 import experienced_event_two_hop_lesson as lesson


PREFIX = 'ASTRA-GOALPAIR-20260914-V1'
TRAIN_MASTERS = tuple(PREFIX + '-TRAIN-' + suffix for suffix in ('A', 'B'))
PROBE_MASTERS = tuple(PREFIX + '-PROBE-' + suffix for suffix in ('A', 'B'))
MASTERS = TRAIN_MASTERS + PROBE_MASTERS
SCHEMA = 'DEV_EXPERIENCED_EVENT_GOAL_PAIRS_V1'
TASK_INDEXES = (0, 1, 2, 3)
GOAL_PAIRS = ((0, 2), (1, 3))
PROTOCOL = lesson.PROTOCOL
MAX_CALLS = MAX_ROWS = 48
MAX_WORLD_CALLS = 24
MAX_CONTEXT = lesson.MAX_CONTEXT
MAX_NEW_TOKENS = lesson.MAX_NEW_TOKENS
TARGET_EOT = lesson.TARGET_EOT
LOSS_POLICY = deepcopy(lesson.LOSS_POLICY)
CLAIM = 'PAIRED_GOAL_SOURCE_USE_ON_FIXED_INSTANCES_NOT_GENERAL_PLANNING_OR_H1_H2'
require = hop.require
document_sha256 = hop.document_sha256
native = lesson.native


@lru_cache(maxsize=4)
def _runtime(master):
    """Use original hop function code with private, single-master globals."""
    require(type(master) is str and master in MASTERS, 'closed_goal_pair_master_required')
    namespace = dict(hop.__dict__, MASTER=master, TRANSFER_MASTER=master)
    for name, function in hop.__dict__.items():
        if isinstance(function, FunctionType) and function.__globals__ is hop.__dict__:
            defaults = (master,) if name == 'build_world' else function.__defaults__
            bound = FunctionType(function.__code__, namespace, function.__name__, defaults, function.__closure__)
            bound.__kwdefaults__ = function.__kwdefaults__
            namespace[name] = bound
    return namespace


def _old_ids(old_ids):
    require(type(old_ids) in (set, frozenset, list, tuple)
            and all(type(value) is str and value for value in old_ids), 'explicit_old_identifier_set_required')
    return sorted(set(old_ids))


def identifiers(world):
    return {value for edge in world['edges'] for value in edge.values()}


def build_world(master, *, old_ids=()):
    world = _runtime(master)['build_world'](master)
    require(identifiers(world).isdisjoint(_old_ids(old_ids)), 'goal_pair_old_identifier_collision')
    return world


def build_worlds(*, old_ids=()):
    """Two TRAIN and two PROBE worlds; all identifiers mutually disjoint."""
    seen = set(_old_ids(old_ids))
    worlds = {}
    for split, masters in (('TRAIN', TRAIN_MASTERS), ('PROBE', PROBE_MASTERS)):
        worlds[split] = []
        for master in masters:
            world = build_world(master, old_ids=seen)
            seen.update(identifiers(world))
            worlds[split].append(world)
    return worlds


def validate_world(world, *, old_ids=()):
    require(type(world) is dict and world == build_world(world.get('master'), old_ids=old_ids),
            'fixed_goal_pair_world_required')
    return deepcopy(world)


def build_tasks(world):
    world = validate_world(world)
    return _runtime(world['master'])['build_tasks'](world)


def collect_world(world, generate, *, old_ids=()):
    world = validate_world(world, old_ids=old_ids)
    return _runtime(world['master'])['collect_world'](world, generate)


def replay_collection(collection, *, old_ids=()):
    require(type(collection) is dict and type(collection.get('world')) is dict, 'goal_pair_collection_required')
    world = validate_world(collection['world'], old_ids=old_ids)
    return _runtime(world['master'])['replay_collection'](collection)


def exact_text_store(collection):
    verified = replay_collection(collection)
    return _runtime(verified['master'])['exact_text_store'](verified)


def run_episode(world, task, actor, memory):
    world = validate_world(world)
    return _runtime(world['master'])['run_episode'](world, task, actor, memory, protocol=PROTOCOL)


def replay_episode(world, task, episode):
    world = validate_world(world)
    require(episode.get('protocol') == PROTOCOL, 'goal_pair_turnbound_required')
    return _runtime(world['master'])['replay_episode'](world, task, episode)


def build_cases(collection):
    """Parent-only source plans; task displays never contain these witnesses."""
    collection = replay_collection(collection)
    store = exact_text_store(collection)
    cases = [dict(task_index=index, task=task, plan=lesson._plan(task, store))
             for index, task in enumerate(build_tasks(collection['world']))]
    for first_index, second_index in GOAL_PAIRS:
        first, second = cases[first_index], cases[second_index]
        require(first['task']['goal'] != second['task']['goal']
                and {key: value for key, value in first['task'].items() if key != 'goal'}
                == {key: value for key, value in second['task'].items() if key != 'goal'},
                'opposite_goals_identical_display_required')
        require({first['plan'][4]['command'], second['plan'][4]['command']}
                == {'ROUTE ' + port for port in first['task']['ports']}, 'opposite_source_first_ports_required')
    return hop._seal(dict(schema=SCHEMA, source_sha256=collection['collection_sha256'], cases=cases), 'cases_sha256')


def summarize_pairs(collection, episodes):
    """Strict within-world paired endpoints, not population inference."""
    cases = build_cases(collection)['cases']
    require(type(episodes) in (list, tuple) and len(episodes) == 4, 'all_four_goal_pair_episodes_required')
    scores = []
    for case, episode in zip(cases, episodes):
        verified = replay_episode(collection['world'], case['task'], episode)
        scores.append(_runtime(collection['master'])['score_episode'](collection['world'], case['task'], verified))
    pairs = []
    for indexes in GOAL_PAIRS:
        source_ports = [cases[index]['plan'][4]['command'].split(' ', 1)[1] for index in indexes]
        actual_ports = [episodes[index]['routes'][0]['port'] if episodes[index]['routes'] else None for index in indexes]
        both = all(scores[index]['correct'] for index in indexes)
        distinct = actual_ports == source_ports and len(set(actual_ports)) == 2
        commits = all(scores[index]['legal_routes'] == 2 for index in indexes)
        pairs.append(dict(task_indexes=list(indexes), both_goals_correct=both,
            distinct_source_correct_first_ports=distinct, two_legal_commits=commits,
            source_first_ports=source_ports, actual_first_ports=actual_ports,
            correct=both and distinct and commits))
    return dict(individual=dict(correct=sum(score['correct'] for score in scores), denominator=4),
        paired=dict(correct=sum(pair['correct'] for pair in pairs), denominator=2), pairs=pairs, scores=scores, claim=CLAIM)


def _collect(collections, old_ids, invoke):
    old_ids = _old_ids(old_ids)
    build_worlds(old_ids=old_ids)
    require(type(collections) in (list, tuple) and len(collections) == 2, 'both_training_collections_required')
    collections = [replay_collection(collection, old_ids=old_ids) for collection in collections]
    require(tuple(collection['master'] for collection in collections) == TRAIN_MASTERS,
            'ordered_train_a_b_only_no_probe_lessons')
    captures, episodes, summaries = [], [], []
    for world_index, collection in enumerate(collections):
        world_episodes = []
        if collection['ready']:
            store = exact_text_store(collection)
            for case in build_cases(collection)['cases']:
                episode_call = 0
                plan = case['plan']

                def actor(student):
                    nonlocal episode_call
                    require(episode_call < 6 and len(captures) < MAX_CALLS, 'goal_pair_lesson_call_cap')
                    guided = lesson._coached_messages(student, plan[episode_call], store)
                    outcome = invoke(deepcopy(guided))
                    capture = dict(call_index=len(captures), world_index=world_index, master=collection['master'],
                        task_index=case['task_index'], episode_call_index=episode_call,
                        student_prefix=deepcopy(student), messages=guided, **deepcopy(outcome))
                    captures.append(hop._seal(capture, 'call_sha256'))
                    episode_call += 1
                    require(capture['error'] is None, 'goal_pair_callback_error')
                    response = capture['response']
                    if type(response) is dict:
                        if 'messages' in response:
                            lesson._same(response['messages'], guided, 'goal_pair_generation_prompt_drift')
                        if 'token_ids' in response:
                            require(type(response['token_ids']) is list and 0 < len(response['token_ids']) <= MAX_NEW_TOKENS
                                    and all(type(token) is int and token >= 0 for token in response['token_ids']),
                                    'goal_pair_generation_token_bound')
                        if 'prompt_tokens' in response:
                            require(type(response['prompt_tokens']) is int and 0 < response['prompt_tokens'] <= MAX_CONTEXT,
                                    'goal_pair_prompt_token_bound')
                        return {key: deepcopy(response[key]) for key in ('raw', 'terminal', 'truncated') if key in response}
                    return deepcopy(response)

                episode = run_episode(collection['world'], case['task'], actor, store.__getitem__)
                actual = [trace for trace in episode['traces'] if trace['kind'] == 'actor']
                matches = len(actual) == 6 and all(trace['error'] is None and type(trace['response']) is dict
                    and type(trace['response'].get('raw')) is str and trace['response']['raw'].rstrip('\n') == step['command']
                    for trace, step in zip(actual, plan))
                complete = (matches and episode['reached_goal'] and episode['terminal_reason'] == 'reached_goal'
                            and episode['route_calls'] == 2 and episode['memory_calls'] == 4)
                world_episodes.append(episode)
                episodes.append(dict(world_index=world_index, master=collection['master'], task_index=case['task_index'],
                    plan=plan, episode=episode, complete=complete,
                    failure=None if complete else ('actual_commands_differ_from_plan' if episode['reached_goal']
                                                  else episode['terminal_reason'])))
        summaries.append(summarize_pairs(collection, world_episodes) if world_episodes else None)
    ready = len(episodes) == 8 and len(captures) == MAX_CALLS and all(entry['complete'] for entry in episodes)
    return hop._seal(dict(schema=SCHEMA, collections=collections, old_ids=old_ids, protocol=PROTOCOL,
        task_indexes=list(TASK_INDEXES), episodes=episodes, captures=captures, summaries=summaries,
        expected_calls=MAX_CALLS, model_calls=len(captures), ready=ready, fit_ready=ready, fits=0,
        parent_present=True, parent_kind='ALGORITHMIC_SOURCE_INFORMED_RESEARCHER_INSTRUCTION', claim=CLAIM,
        status='GOAL_PAIR_LESSONS_READY_NO_FIT' if ready else 'GOAL_PAIR_LESSONS_INCOMPLETE_NO_FIT'), 'evidence_sha256')


def _rows(evidence):
    if not evidence['ready']:
        return []
    rows = []
    for capture in evidence['captures']:
        row = dict(schema=SCHEMA, row_index=len(rows), master=capture['master'], world_index=capture['world_index'],
            task_index=capture['task_index'], episode_call_index=capture['episode_call_index'],
            prefix=deepcopy(capture['student_prefix']), assistant=capture['response']['raw'],
            call_sha256=capture['call_sha256'], evidence_sha256=evidence['evidence_sha256'],
            target_eot=TARGET_EOT, loss_policy=deepcopy(LOSS_POLICY))
        if not rows:
            row['provenance'] = deepcopy(evidence)
        rows.append(hop._seal(row, 'row_sha256'))
    return rows


def collect_lessons(collections, generate, *, old_ids=()):
    """Collect TRAIN-A then TRAIN-B, all four tasks each, without retries/repairs.

Flat captures preserve actual guided responses, prompt echoes and failures.
Only a complete two-world bundle emits rows. The first row carries the shared
replay evidence; encoding requires all 48 rows, never an isolated row subset.
"""
    require(callable(generate), 'generation_callback_required')
    evidence = _collect(collections, old_ids, lambda messages: hop._invoke(generate, messages))
    return hop._seal(dict(evidence, rows=_rows(evidence)), 'lesson_sha256')


def _replay_evidence(evidence):
    require(type(evidence) is dict and evidence.get('schema') == SCHEMA, 'goal_pair_lesson_required')
    captures = iter(deepcopy(evidence['captures']))

    def invoke(messages):
        capture = next(captures, None)
        require(capture is not None, 'missing_goal_pair_capture')
        lesson._same(capture['messages'], messages, 'goal_pair_coached_prompt_drift')
        return dict(response=capture['response'], error=capture['error'])

    verified = _collect(evidence['collections'], evidence['old_ids'], invoke)
    require(next(captures, None) is None, 'extra_goal_pair_capture')
    lesson._same(evidence, verified, 'goal_pair_evidence_replay_drift')
    return verified


def replay_lessons(document):
    require(type(document) is dict and document.get('schema') == SCHEMA, 'goal_pair_lesson_required')
    evidence = {key: deepcopy(value) for key, value in document.items() if key not in ('rows', 'lesson_sha256')}
    verified = _replay_evidence(evidence)
    rows = _rows(verified)
    lesson._same(document, hop._seal(dict(verified, rows=rows), 'lesson_sha256'), 'goal_pair_document_replay_drift')
    return rows


def encode_rows(rows, tokenizer):
    """Mask all student history and suffix; supervise actual assistant plus EOT."""
    require(type(rows) in (list, tuple) and len(rows) == MAX_ROWS, 'complete_48_goal_pair_rows_required')
    require(type(rows[0]) is dict and 'provenance' in rows[0], 'goal_pair_row_provenance_required')
    evidence = _replay_evidence(rows[0]['provenance'])
    lesson._same(list(rows), _rows(evidence), 'goal_pair_row_or_provenance_drift')
    require(tokenizer.eos_token == TARGET_EOT and type(tokenizer.eos_token_id) is int
            and native._encode(tokenizer, TARGET_EOT) == (tokenizer.eos_token_id,), 'exact_goal_pair_eot_required')
    encoded = []
    for row in rows:
        prefix = row['prefix']
        require([message['role'] for message in prefix] == ['system', 'user']
                + ['assistant', 'user'] * row['episode_call_index'], 'alternating_goal_pair_student_prefix_required')
        messages = prefix + [dict(role='assistant', content=row['assistant'])]
        context = tokenizer.apply_chat_template(prefix, tokenize=False, add_generation_prompt=True, return_dict=False)
        full = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=False, return_dict=False)
        require(full == context + row['assistant'] + TARGET_EOT + '\n', 'exact_goal_pair_template_boundary_required')
        prefix_ids = native._encode(tokenizer, context)
        target = native._encode(tokenizer, row['assistant'])
        suffix = native._encode(tokenizer, '\n')
        require(not set(tokenizer.all_special_ids).intersection(target), 'goal_pair_target_special_token_forbidden')
        supervised = target + (tokenizer.eos_token_id,)
        sequence = native._encode(tokenizer, full)
        require(sequence == prefix_ids + supervised + suffix and len(sequence) <= MAX_CONTEXT
                and len(supervised) <= MAX_NEW_TOKENS, 'untruncated_bounded_goal_pair_sequence_required')
        require(native._decode(tokenizer, sequence) == full and native._decode(tokenizer, prefix_ids) == context
                and native._decode(tokenizer, supervised) == row['assistant'] + TARGET_EOT
                and native._decode(tokenizer, suffix) == '\n', 'goal_pair_token_roundtrip_failed')
        require(tuple(tokenizer.apply_chat_template(messages, tokenize=True, add_generation_prompt=False,
            return_dict=False, truncation=False, padding=False)) == sequence, 'goal_pair_template_token_ids_mismatch')
        encoded.append(native.EncodedRow(sequence, (-100,) * len(prefix_ids) + supervised + (-100,) * len(suffix), supervised))
    return tuple(encoded)
