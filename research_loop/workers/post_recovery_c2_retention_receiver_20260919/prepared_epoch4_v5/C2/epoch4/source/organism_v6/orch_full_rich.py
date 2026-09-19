"""Finite rich-trajectory screen in the existing two-hop grammar, without fitting."""

from copy import deepcopy
import re
from types import FunctionType

from organism_v6 import experienced_event_two_hop as hop
from organism_v6 import orch_replication as readout


MASTERS = tuple(f'ORCH-FULL-RICH-20260914-TRAIN-V1-WORLD-{index}' for index in range(8))
STATES = ('FULL_TARGET', 'NEW_TRAJECTORY_LOSS_OFF', 'ORIGINAL37EC')
SOURCE_CAP = 64
TRAJECTORY_CAP = 96
TOTAL_CAP = 352
MAX_NEW_TOKENS = 512
MAX_CONTEXT = 2048
RUBRIC = ('specific_read_evidence', 'goal_connection', 'checkable_expectation',
          'action_last', 'substantive_first_person', 'no_unsupported_claim')
SYSTEM = (
    'Use the public task and actual conversation. Identifiers are opaque and case-sensitive. '
    'There are at most six turns, four distinct memory reads, and two committed routes. '
    'A READ returns actual stored text; a ROUTE commits a currently listed port and returns '
    'the actual public receipt and new CURRENT/PORTS. Arrival at GOAL ends the episode. '
    'Never simulate a response or another turn. Finish every turn with exactly one action '
    'on its last line: READ EVENT <listedaddress> or ROUTE <listedport>. No STOP or retry.'
)
GUIDANCE = (
    'Write 150–400 generated tokens of substantive first-person reasoning on EVERY turn. '
    'Name the specific evidence actually read, explain its relevance to the goal, state a '
    'checkable expectation for the next observation, and put your action last. Before '
    'the first READ, acknowledge that no stored evidence has been read and explain what '
    'you intend to learn; do not invent evidence. After feedback, revise any mistaken '
    'expectation explicitly. Be concise within this range; do not pad or add headings '
    'as a substitute for grounded reasoning. Use only actual supplied evidence.'
)
digest = hop.document_sha256


def runtime(master):
    hop.require(master in MASTERS, 'frozen_training_master_required')
    namespace = dict(hop.__dict__, MASTER=master, TRANSFER_MASTER=master)
    for name, function in hop.__dict__.items():
        if isinstance(function, FunctionType) and function.__globals__ is hop.__dict__:
            defaults = (master,) if name == 'build_world' else function.__defaults__
            namespace[name] = FunctionType(function.__code__, namespace, name, defaults, function.__closure__)
    return namespace


def cohort(exclusions=()):
    seen, worlds = set(exclusions), []
    for master in MASTERS:
        world = runtime(master)['build_world'](master)
        identifiers = {value for edge in world['edges'] for value in edge.values()}
        hop.require(not identifiers.intersection(seen), 'archival_namespace_collision')
        seen.update(identifiers)
        worlds.append(world)
    return dict(worlds=worlds, episode_denominator=16, world_denominator=8,
                split='TRAIN_SCREEN_NO_FIT', ordering='ASCENDING_ONLY')


def tasks(world):
    return [task for index, task in enumerate(runtime(world['master'])['build_tasks'](world)) if index in (0, 2)]


def collect(frozen, generate, emit):
    collections, store = [], {}
    for index, world in enumerate(frozen['worlds']):
        document = runtime(world['master'])['collect_world'](world, generate)
        runtime(world['master'])['replay_collection'](document)
        collections.append(document)
        for record in document['records']:
            if record['accepted']:
                store[record['edge']['event']] = record['event']['raw']
        emit(f'WORLD_{index:02d}.json', document)
    return dict(collections=collections, store=store, store_sha256=digest(store),
                cohort_sha256=digest(frozen), accepted_events=len(store), event_denominator=32,
                model_calls=sum(document['model_calls'] for document in collections))


def verify_source(frozen, document):
    hop.require(document['cohort_sha256'] == digest(frozen) and len(document['collections']) == 8,
                'source_cohort_mismatch')
    store = {}
    for world, collection in zip(frozen['worlds'], document['collections']):
        hop.require(collection['world'] == world, 'source_world_mismatch')
        runtime(world['master'])['replay_collection'](collection)
        for record in collection['records']:
            if record['accepted']:
                store[record['edge']['event']] = record['event']['raw']
    hop.require(store == document['store'] and digest(store) == document['store_sha256'], 'raw_store_changed')
    return store


def episode(world, task, generate, store):
    current, ports = task['node'], list(task['ports'])
    messages = [dict(role='system', content=SYSTEM + '\n\n' + GUIDANCE),
                dict(role='user', content=readout.display(current, task, ports))]
    reads, routes, captures = [], [], []
    reason = 'actor_call_cap'
    for turn in range(6):
        capture = dict(turn=turn, messages=deepcopy(messages), response=None, error=None,
                       prior_reads=deepcopy(reads), command=None)
        captures.append(capture)
        try:
            response = generate(deepcopy(messages))
            capture['response'] = deepcopy(response)
            raw = readout.response_text(response)
        except Exception as error:
            capture['error'] = dict(type=type(error).__name__, message=str(error))
            reason = 'generation_failure'
            break
        messages.append(dict(role='assistant', content=raw))
        lines = raw.rstrip().splitlines()
        match = re.fullmatch(r'(READ EVENT|ROUTE) ([^\s]+)', lines[-1]) if lines else None
        if not match:
            reason = 'invalid_final_action'
            break
        kind, value = match.groups()
        capture['command'] = dict(kind=kind, value=value)
        if kind == 'READ EVENT':
            if value not in task['events'] or value in [entry['address'] for entry in reads] or len(reads) >= 4:
                reason = 'invalid_or_duplicate_read'
                break
            text = store.get(value, readout.UNAVAILABLE)
            reads.append(dict(address=value, raw=text))
            messages.append(dict(role='user', content='MEMORY RESULT\n' + text))
        else:
            if value not in ports or len(routes) >= 2:
                reason = 'invalid_route'
                break
            edge = next(edge for edge in world['edges'] if edge['node'] == current and edge['port'] == value)
            route = dict(source=current, port=value, destination=edge['outcome'], receipt=edge['receipt'])
            routes.append(route)
            current = edge['outcome']
            ports = sorted(edge['port'] for edge in world['edges'] if edge['node'] == current)
            messages.append(dict(role='user', content=hop.micro.RECEIPT_WIRE.format(**route)
                            + '\n' + readout.display(current, task, ports)))
            if current == task['goal'] or not ports:
                reason = 'reached_goal' if current == task['goal'] else 'dead_end'
                break
    record = dict(task=deepcopy(task), routes=routes, reads=reads, captures=captures,
                  terminal_reason=reason, current=current, actor_calls=len(captures),
                  correct=current == task['goal'] and len(routes) == 2, messages=messages)
    readout.score(world, task, record)
    return record


def row_gate(episode_record, capture, review=None):
    response = capture.get('response') or {}
    tokens = response.get('generated_text_tokens', -1)
    eligible = bool(episode_record['correct'] and capture['prior_reads'] and
                    150 <= tokens <= 400 and response.get('terminal') is True and
                    response.get('truncated') is False and capture.get('command') is not None)
    reviewed = bool(review and review.get('raw_sha256') == digest(response.get('raw')) and
                    review.get('capture_sha256') == digest(capture) and
                    all(type(review.get(item)) is bool for item in RUBRIC) and review.get('rationale'))
    semantic = reviewed and all(review[item] for item in RUBRIC)
    return dict(eligible_for_semantic_review=eligible, semantic_status='PASS' if semantic else
                ('FAIL_SEMANTIC' if reviewed else 'UNRESOLVED' if eligible else 'FAIL_NECESSARY_CONDITIONS'),
                admitted=eligible and semantic,
                generated_text_tokens=tokens)


def student_row(capture):
    messages = deepcopy(capture['messages'])
    hop.require(messages[0]['content'] == SYSTEM + '\n\n' + GUIDANCE, 'parent_prompt_binding')
    messages[0]['content'] = SYSTEM
    messages.append(dict(role='assistant', content=capture['response']['raw']))
    return dict(messages=messages, target=capture['response']['raw'],
                loss_policy='FINAL_ASSISTANT_ONLY_ALL_PREFIX_MASKED', parent_guidance_removed=True)


def first_port(messages):
    public = next(message['content'].split('ROUTE TASK\n', 1)[1] for message in reversed(messages)
                  if message['role'] == 'user' and 'ROUTE TASK\n' in message['content'])
    line = next(line for line in public.splitlines() if line.startswith('PORTS '))
    return dict(raw='ROUTE ' + line[6:].split(',')[0], terminal=True, truncated=False)


def decision(summaries):
    full = summaries['FULL_TARGET']
    return 'POSITIVE' if (full['qualified_episodes'] >= 8 and full['qualified_worlds'] >= 4 and all(
        full['qualified_episodes'] - summaries[state]['qualified_episodes'] >= 4 and
        full['admitted_rows'] - summaries[state]['admitted_rows'] >= 8 and
        sum(first and not second for first, second in zip(full['qualified_mask'],
            summaries[state]['qualified_mask'])) >= 4 for state in STATES[1:])) else 'NULL'
