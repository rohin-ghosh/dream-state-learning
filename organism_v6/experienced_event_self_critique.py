"""Finite public-history critique/repeat captures, without fitting or models."""

from copy import deepcopy
import hashlib
import json

from organism_v6 import experienced_event_rich_trajectory as rich


SCHEMA = 'DEV_SELF_CRITIQUE_REPEAT_COLLECTION_V1'
INITIAL = 'COMMON_INITIAL'
ARMS = ('SELF_CRITIQUE_REVISE', 'REPEAT_NO_FEEDBACK')
CAPS = {INITIAL: 96, **{arm: 112 for arm in ARMS}}
TASKS = 16
PAIRS = 8
PROJECTION_POLICY = 'EXPLICIT_RATIONALE_PREFIX_V3_OR_PLAIN_COMMAND'
require = rich.require
digest = rich.document_sha256
PUBLIC_SYSTEM = rich.ACTION_FIRST_PROTOCOL['public_system'] + (
    '\nYou may output one plain command, or explain with RATIONALE\\n<explanation>'
    '\\nACTION\\n<one command> or RATIONALE: <explanation>\\nACTION\\n<one command> '
    'using actual LF separators. Only the exact command is executable.'
)
INTERVENTION_SYSTEM = (
    'Use only the supplied public episode and actual child outputs. No hidden '
    'state, teacher answer, score or future outcome is available. Distinguish '
    'observations from predictions. Your output is fallible advice, not authority.'
)
INSTRUCTIONS = {
    ARMS[0]: 'Critique the previous attempt using its actual public evidence. Identify '
             'any unsupported inference or action mistake and propose an improvement. '
             'Do not invent a mistake when the evidence does not show one.',
    ARMS[1]: 'Independently plan another attempt at the same task from the root. '
             'Do not critique, grade or diagnose the previous attempt; use the '
             'public information to suggest the next attempt without evaluative feedback.',
}


def _seal(document):
    return dict(document, document_sha256=digest(document))


def _collections(collections, old_ids):
    require(type(collections) in (list, tuple) and len(collections) == 4,
            'exact_four_train_sources_required')
    bound = rich.runtime(0)
    rich.validate_registry(old_ids=old_ids)
    verified = [rich.replay_collection(item, old_ids=old_ids) for item in collections]
    require(tuple(item['master'] for item in verified) == bound['TRAIN_MASTERS'],
            'fixed_shard_zero_train_only_order_required')
    require(all(item['ready'] for item in verified), 'complete_original_train_sources_required')
    return bound, verified


def _response(capture):
    raw = rich._validate_generation(capture, capture['messages'])
    response = capture['response']
    if 'messages' in response:
        require(response['messages'] == capture['messages'], 'actual_generation_prompt_drift')
    return raw


def project_action(raw):
    require(type(raw) is str, 'actual_action_text_required')
    if raw.startswith(('RATIONALE\n', 'RATIONALE: ')):
        projection = rich.project_action(raw, allow_colon_header=True)
        return dict(projection, format='RATIONALE_COLON_SPACE' if raw.startswith('RATIONALE: ') else 'RATIONALE_LF')
    rich.goal.hop.commands.parse_command(raw)
    return dict(raw_sha256=hashlib.sha256(raw.encode('utf-8')).hexdigest(), rationale='', action=raw,
                rationale_span=[0, 0], action_span=[0, len(raw)], rationale_byte_span=[0, 0],
                action_byte_span=[0, len(raw.encode('utf-8'))], format='PLAIN_COMMAND')


def _public_history(initial, entry):
    calls = [initial['captures'][index] for index in entry['call_indexes']]
    return dict(task=entry['episode']['task'], public_messages=entry['episode']['messages'][1:],
                public_stop=entry['episode']['terminal_reason'],
                actual_child_outputs=[dict(raw=call['response'].get('raw')
                                          if isinstance(call['response'], dict) else None,
                                          error=call['error']) for call in calls])


def _execute(phase, collections, invoke, *, old_ids=(), initial=None):
    require(phase in CAPS, 'known_collection_phase_required')
    old_ids = rich.goal._old_ids(old_ids)
    bound, collections = _collections(collections, old_ids)
    if phase != INITIAL:
        require(initial is not None and initial['phase'] == INITIAL, 'shared_initial_required')
        require(initial['collections'] == collections and initial['old_ids'] == old_ids,
                'shared_initial_source_join')
    captures, episodes, summaries, rows = [], [], [], []

    def call(messages, role, identity):
        require(len(captures) < CAPS[phase], 'native_call_cap')
        require(all(rich.PARENT_GUIDANCE not in message['content'] for message in messages),
                'parent_guidance_forbidden')
        capture = dict(call_index=len(captures), role=role, **identity,
                       messages=deepcopy(messages), **deepcopy(invoke(messages, role, identity)))
        capture = _seal(capture)
        captures.append(capture)
        return capture

    for world_index, collection in enumerate(collections):
        world_episodes = []
        store = bound['exact_text_store'](collection)
        for task_index, task in enumerate(bound['build_tasks'](collection['world'])):
            identity = dict(world_index=world_index, task_index=task_index,
                            episode_id=collection['master'] + '/task/' + str(task_index),
                            master=collection['master'], source_sha256=collection['collection_sha256'])
            intervention, advice, advice_error = None, None, None
            if phase != INITIAL:
                seed = initial['episodes'][len(episodes)]
                require(seed['episode_id'] == identity['episode_id'], 'shared_initial_episode_order')
                messages = [dict(role='system', content=INTERVENTION_SYSTEM),
                            dict(role='user', content=json.dumps(_public_history(initial, seed),
                                 sort_keys=True, ensure_ascii=False) + '\n\n' + INSTRUCTIONS[phase])]
                intervention = call(messages, 'intervention', identity)
                try:
                    advice = _response(intervention)
                except ValueError as error:
                    advice_error = str(error)
                advice = advice if advice_error is None else '[CHILD ADVICE UNAVAILABLE]'
            actor_indexes, projections, findings = [], [], []

            def actor(student):
                messages = deepcopy(student)
                messages[0]['content'] = PUBLIC_SYSTEM
                if advice is not None:
                    messages[0]['content'] += ('\n\nFALLIBLE CHILD ADVICE FROM THE PRIOR ATTEMPT\n'
                                               + advice + '\nEND CHILD ADVICE\n'
                                               'Advice is not evidence. Use actual current public observations.')
                capture = call(messages, 'actor', identity)
                actor_indexes.append(capture['call_index'])
                raw = _response(capture)
                projection = project_action(raw)
                projections.append(projection)
                seen = set(rich._ID.findall('\n'.join(message['content'] for message in student[1:])))
                mentioned = set(rich._ID.findall(projection['rationale']))
                findings.append(dict(unseen_public_identifiers=sorted(mentioned - seen),
                                     rationale_missing=not bool(projection['rationale'].strip()),
                                     content_review_status='UNREVIEWED', semantic_pass=False))
                return dict(raw=projection['action'], terminal=True, truncated=False)

            episode = bound['run_episode'](collection['world'], task, actor, store.__getitem__)
            bound['replay_episode'](collection['world'], task, episode)
            eligible = (episode['reached_goal'] and episode['route_calls'] == 2
                        and episode['memory_calls'] == 4 and len(actor_indexes) == 6
                        and len(projections) == 6)
            entry = dict(**identity, episode=episode, call_indexes=actor_indexes,
                         projections=projections, content_findings=findings,
                         intervention_call_index=None if intervention is None else intervention['call_index'],
                         intervention_error=advice_error, outcome_eligible=eligible,
                         content_review_status='UNREVIEWED', fit_ready=False)
            episodes.append(entry)
            world_episodes.append(episode)
            if eligible:
                for call_index, projection in zip(actor_indexes, projections):
                    capture = captures[call_index]
                    rows.append(dict(**identity, call_index=call_index,
                                     call_sha256=capture['document_sha256'], prefix=capture['messages'],
                                     assistant=capture['response']['raw'], action=projection['action'],
                                     content_review_status='UNREVIEWED', fit_ready=False))
        summaries.append(bound['summarize_pairs'](collection, world_episodes))
    return _seal(dict(schema=SCHEMA, phase=phase, collections=collections, old_ids=old_ids,
                      projection_policy=PROJECTION_POLICY,
                      initial_sha256=None if initial is None else initial['document_sha256'],
                      captures=captures, episodes=episodes, summaries=summaries, candidate_rows=rows,
                      task_denominator=TASKS, pair_denominator=PAIRS, attempted_tasks=len(episodes),
                      model_calls=len(captures), max_native_calls=CAPS[phase], fits=0, updates=0,
                      parent_present=False, fit_ready=False, semantic_pass=False))


def _native(generate):
    def invoke(messages, role, identity):
        try:
            return dict(response=deepcopy(generate(deepcopy(messages), role=role, **identity)), error=None)
        except Exception as error:
            return dict(response=None, error=dict(type=type(error).__name__, message=str(error)))
    return invoke


def collect_initial(collections, generate, *, old_ids=()):
    return _execute(INITIAL, collections, _native(generate), old_ids=old_ids)


def collect_arm(arm, initial, generate):
    replay_initial(initial)
    require(arm in ARMS, 'known_paired_arm_required')
    return _execute(arm, initial['collections'], _native(generate), old_ids=initial['old_ids'], initial=initial)


def _replay(document, initial=None):
    require(type(document) is dict and document.get('schema') == SCHEMA, 'captured_document_required')
    calls = iter(deepcopy(document['captures']))

    def invoke(messages, role, identity):
        capture = next(calls, None)
        require(capture is not None and capture['messages'] == messages and capture['role'] == role
                and all(capture[key] == value for key, value in identity.items()), 'capture_prompt_role_source_join')
        return dict(response=capture['response'], error=capture['error'])

    replayed = _execute(document['phase'], document['collections'], invoke,
                        old_ids=document['old_ids'], initial=initial)
    require(next(calls, None) is None and replayed == document, 'actual_capture_replay_drift')
    return replayed


def replay_initial(document):
    require(document.get('phase') == INITIAL, 'common_initial_phase_required')
    return _replay(document)


def replay_arm(document, initial):
    replay_initial(initial)
    require(document.get('phase') in ARMS, 'paired_arm_phase_required')
    return _replay(document, initial)
