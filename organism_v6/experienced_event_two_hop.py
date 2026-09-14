"""Scheduled connected EVENT exposure and a zero-fit, continuous DEV rollout.

The native caller binds the actor, adapter, files and condition. This module
neither loads models nor trains. Public tasks contain no path witnesses; only
committed actions expose environment outcomes. Supplied text must come from
the captured child EVENTs, never from the evaluator's edge descriptions.
"""

import hashlib
import json

from organism_v6 import experienced_event_microloop as micro
from organism_v6 import experienced_event_read_route as commands


MASTER = 'ASTRA-EVENT-CONTEXT-TWOHOP-20260914-V1'
SCHEMA = 'DEV_EXPERIENCED_EVENT_TWO_HOP_V1'
COLLECTION_SCHEMA = 'DEV_EXPERIENCED_EVENT_TWO_HOP_COLLECTION_V1'
EPISODE_SCHEMA = 'DEV_EXPERIENCED_EVENT_TWO_HOP_EPISODE_V1'
SERIALIZATION = 'FINAL_LF_ONLY'
MAX_COLLECTION_CALLS = 8
MAX_ACTOR_CALLS = 6
MAX_READS = 4
MAX_ROUTES = 2
MAX_CONTEXT = 2048
MAX_NEW_TOKENS = 160
require = micro._require
PUBLIC_SYSTEM = (
    'Use the public task and conversation. Identifiers are opaque and case-sensitive. '
    'Output exactly READ EVENT <listedaddress> or ROUTE <listedport>, optionally followed '
    'by LF characters, with no other text. You have at most six actor calls, four distinct '
    'memory reads, and two committed routes. A READ returns the reader\'s actual text. '
    'A ROUTE commits a port at CURRENT and returns the actual new CURRENT and available '
    'PORTS. GOAL remains the same final destination throughout. Arrival at GOAL ends '
    'the episode automatically. There is no retry or STOP command.'
)
COLLECTION_SYSTEM = (
    'This is a researcher-scheduled public action exposure, not autonomous exploration. '
    'Identifiers are opaque and case-sensitive. Execute only the offered ROUTE, then '
    'record only the actual public receipt. Do not invent, infer, rename or repair identifiers.'
)
TURNBOUND_SYSTEM = PUBLIC_SYSTEM + (
    ' Output exactly one command per assistant turn, then wait for the actual memory '
    'or environment response. Never simulate that response or output another turn. '
    'A ROUTE command must use a port identifier from the current PORTS list, never a node.'
)
PROTOCOLS = {'original': PUBLIC_SYSTEM, 'turnbound': TURNBOUND_SYSTEM}


def _copy(value):
    return json.loads(json.dumps(value, allow_nan=False))


def document_sha256(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=True, allow_nan=False,
                                    separators=(',', ':')).encode('ascii')).hexdigest()


def _seal(value, key):
    return dict(value, **{key: document_sha256(value)})


def build_world():
    """Exactly A->B, A->C, B->G0, C->G1; all public IDs are opaque."""
    nodes = [micro._opaque(MASTER, 'N', index) for index in range(5)]
    edges = [dict(event=micro._opaque(MASTER, 'E', index), node=nodes[start],
                  port=micro._opaque(MASTER, 'P', index), outcome=nodes[end],
                  receipt=micro._opaque(MASTER, 'R', index))
             for index, (start, end) in enumerate(((0, 1), (0, 2), (1, 3), (2, 4)))]
    return dict(schema=SCHEMA, master=MASTER, nodes=nodes, edges=edges)


def validate_world(world):
    require(world == build_world(), 'fixed_connected_world_required')
    return _copy(world)


def build_tasks(world):
    """Goal-major: G0/order0, G0/order1, G1/order0, G1/order1.

    Each order is shared across goals; order1 reverses both root ports and the
    globally sorted address list. No display position encodes a target class.
    """
    validate_world(world)
    ports = sorted(edge['port'] for edge in world['edges'] if edge['node'] == world['nodes'][0])
    events = sorted(edge['event'] for edge in world['edges'])
    return [dict(node=world['nodes'][0], goal=goal,
                 ports=list(ports if order == 0 else reversed(ports)),
                 events=list(events if order == 0 else reversed(events)))
            for goal in world['nodes'][3:] for order in range(2)]


def _invoke(callback, argument):
    response = None
    try:
        response = callback(_copy(argument))
        return dict(response=_copy(response), error=None)
    except Exception as error:
        available = response if type(response) is str else None
        if type(response) is dict:
            available = {key: response.get(key) for key in ('raw', 'terminal', 'truncated')
                         if type(response.get(key)) in (str, bool, type(None))}
        return dict(response=available, error=dict(type=type(error).__name__, message=str(error)))


def _generation(response, messages=None):
    require(type(response) is dict and type(response.get('raw')) is str
        and type(response.get('terminal')) is bool and type(response.get('truncated')) is bool,
        'invalid_generation')
    require(response['terminal'] and not response['truncated'], 'nonterminal_or_truncated')
    if messages is not None and 'messages' in response:
        require(response['messages'] == messages, 'generation_prompt_drift')
    return response['raw']


def _collect(world, invoke):
    records, captures = [], []

    def generate(messages, record_index, phase):
        require(len(captures) < MAX_COLLECTION_CALLS, 'collection_call_cap')
        outcome = invoke(_copy(messages))
        capture = dict(call_index=len(captures), record_index=record_index, phase=phase,
                       messages=_copy(messages), **_copy(outcome))
        captures.append(capture)
        require(capture['error'] is None, 'collection_callback_error')
        _generation(capture['response'], messages)
        return capture['response']

    for record_index, edge in enumerate(world['edges']):
        record = dict(edge=_copy(edge), action=None, transition=None, event=None, accepted=False, error=None)
        records.append(record)
        messages = [dict(role='system', content=COLLECTION_SYSTEM), dict(role='user', content=(
            f"EXPOSURE TASK\nCURRENT {edge['node']}\nPORTS {edge['port']}\n"
            'Execute the offered action: ROUTE <listedport>. Output only that command.'))]
        try:
            record['action'] = generate(messages, record_index, 'action')
            action = commands.parse_command(record['action']['raw'])
            require(action['kind'] == 'ROUTE' and action['value'] == edge['port'], 'unoffered_exposure_action')
            record['transition'] = dict(source=edge['node'], port=edge['port'], destination=edge['outcome'], receipt=edge['receipt'])
            messages += [dict(role='assistant', content=record['action']['raw']), dict(role='user', content=(
                micro.RECEIPT_WIRE.format(**record['transition'])
                + micro.EVENT_TEMPLATE.format(FRESH_EVENT_ID=edge['event'])))]
            record['event'] = generate(messages, record_index, 'event')
            canonical = micro.canonical_event(record['event']['raw'])
            require(micro.parse_event_line(canonical) == dict(event=edge['event'], **record['transition']),
                    'EVENT_not_grounded_in_actual_receipt')
            record.update(accepted=True, canonical_event=canonical,
                source_raw_sha256=hashlib.sha256(record['event']['raw'].encode('utf-8')).hexdigest(),
                canonical_sha256=hashlib.sha256(canonical.encode('utf-8')).hexdigest())
        except ValueError as error:
            record['error'] = dict(type=type(error).__name__, message=str(error))
    accepted = sum(record['accepted'] for record in records)
    return _seal(dict(schema=COLLECTION_SCHEMA, master=MASTER, world=_copy(world),
        world_sha256=document_sha256(world), ready=accepted == 4, records=records, captures=captures,
        accepted_events=accepted, event_denominator=4, model_calls=len(captures), fits=0,
        serialization=SERIALIZATION, new_material=True, parent_present=False,
        claim='RESEARCHER_SCHEDULED_FOUR_NEW_EDGE_EXPOSURES_NOT_AUTONOMOUS_EXPLORATION_NO_FIT',
        status='COLLECTION_READY_NO_FIT' if accepted == 4 else 'COLLECTION_INCOMPLETE_NO_FIT'), 'collection_sha256')


def collect_world(world, generate):
    """Attempt all four resets; valid ROUTE commits before the child EVENT call.

    generate(messages) returns the native raw/terminal/truncated dictionary.
    Every raw response/error remains in captures, including rejected attempts.
    No receipt or EVENT call is fabricated when an offered action is invalid.
    """
    world = validate_world(world)
    require(callable(generate), 'generation_callback_required')
    return _collect(world, lambda messages: _invoke(generate, messages))


def replay_collection(collection):
    """Return the full verified document, including failures; never compile rows."""
    require(type(collection) is dict and collection.get('schema') == COLLECTION_SCHEMA,
            'two_hop_collection_required')
    world = validate_world(collection['world'])
    captures = iter(_copy(collection['captures']))

    def invoke(messages):
        capture = next(captures, None)
        require(capture is not None and capture['messages'] == messages, 'collection_capture_prompt_drift')
        return dict(response=capture['response'], error=capture['error'])

    verified = _collect(world, invoke)
    require(next(captures, None) is None and verified == collection, 'collection_replay_drift')
    return verified


def exact_text_store(collection):
    """Only actual child raw EVENT text; no final-LF rewrite or template fallback."""
    verified = replay_collection(collection)
    require(verified['ready'], 'four_source_valid_child_events_required')
    return {record['edge']['event']: record['event']['raw'] for record in verified['records']}


def _public(current, goal, ports, events):
    return f"ROUTE TASK\nCURRENT {current}\nGOAL {goal}\nPORTS {','.join(ports)}\nEVENTS {','.join(events)}"


def _run(world, task, invoke, protocol='original'):
    require(protocol in PROTOCOLS, 'known_two_hop_protocol_required')
    messages = [dict(role='system', content=PROTOCOLS[protocol]),
                dict(role='user', content=_public(task['node'], task['goal'], task['ports'], task['events']))]
    result = dict(schema=EPISODE_SCHEMA, world_sha256=document_sha256(world), task=_copy(task),
        task_sha256=document_sha256(task), fits=0, reached_goal=False, terminal_reason='actor_call_cap',
        current=task['node'], actor_calls=0, action_calls=0, memory_calls=0, route_calls=0,
        routes=[], traces=[], messages=messages)
    if protocol != 'original':
        result['protocol'] = protocol
    addresses = set()
    ports = list(task['ports'])

    def finish(reason):
        result['terminal_reason'] = reason
        return _seal(result, 'episode_sha256')

    def receive(kind, argument):
        trace = dict(kind=kind, **({'messages': _copy(argument)} if kind == 'actor' else {'address': argument}))
        trace.update(_copy(invoke(kind, _copy(argument))))
        result['traces'].append(trace)
        if trace['error'] is not None:
            return None, kind + '_callback_error'
        response = trace['response']
        if kind == 'memory' and type(response) is str:
            return response, None
        try:
            return _generation(response, argument if kind == 'actor' else None), None
        except ValueError as error:
            return None, kind + '_' + str(error)

    for unused in range(MAX_ACTOR_CALLS):
        result['actor_calls'] += 1
        result['action_calls'] += 1
        raw, error = receive('actor', messages)
        if error:
            return finish(error)
        messages.append(dict(role='assistant', content=raw))
        try:
            command = commands.parse_command(raw)
        except ValueError:
            return finish('invalid_command')
        result['traces'][-1]['command'] = command
        value = command['value']
        if command['kind'] == 'READ':
            if value not in task['events']:
                return finish('unsupported_address')
            if value in addresses:
                return finish('duplicate_address')
            if result['memory_calls'] >= MAX_READS:
                return finish('memory_call_cap')
            addresses.add(value)
            result['memory_calls'] += 1
            memory_raw, error = receive('memory', value)
            if error:
                return finish(error)
            messages.append(dict(role='user', content='MEMORY RESULT\n' + memory_raw))
            continue
        if value not in ports:
            return finish('invalid_route')
        if result['route_calls'] >= MAX_ROUTES:
            return finish('route_call_cap')
        edge = next(edge for edge in world['edges'] if edge['node'] == result['current'] and edge['port'] == value)
        transition = dict(kind='transition', source=result['current'], port=value,
                          destination=edge['outcome'], receipt=edge['receipt'], committed=True)
        result['traces'].append(_copy(transition))
        result['routes'].append(_copy(transition))
        result['route_calls'] += 1
        result['current'] = edge['outcome']
        ports = sorted(other['port'] for other in world['edges'] if other['node'] == result['current'])
        messages.append(dict(role='user', content=_public(result['current'], task['goal'], ports, task['events'])))
        if result['current'] == task['goal']:
            result['reached_goal'] = True
            return finish('reached_goal')
        if not ports:
            return finish('dead_end')
    return finish('actor_call_cap')


def run_episode(world, task, actor, memory, protocol='original'):
    """One conversation, <=4 distinct reads and <=2 actual committed routes.

    Actor returns a native generation dict. Memory returns either that shape or
    an exact raw string from the captured text store. Memory contents are never
    repaired, interpreted as environment state, or filtered for correctness.
    """
    world = validate_world(world)
    require(task in build_tasks(world), 'fixed_public_two_hop_task_required')
    require(callable(actor) and callable(memory), 'actor_and_memory_callbacks_required')
    return _run(world, _copy(task), lambda kind, argument: _invoke(actor if kind == 'actor' else memory, argument), protocol)


def replay_episode(world, task, record):
    """Reexecute captured callbacks; recompute all transitions, context and stops."""
    world = validate_world(world)
    require(task in build_tasks(world), 'fixed_public_two_hop_task_required')
    require(type(record) is dict and record.get('schema') == EPISODE_SCHEMA, 'two_hop_episode_required')
    callbacks = iter(_copy([trace for trace in record['traces'] if trace['kind'] in ('actor', 'memory')]))

    def invoke(kind, argument):
        trace = next(callbacks, None)
        require(trace is not None and trace['kind'] == kind and trace.get('messages' if kind == 'actor' else 'address') == argument,
                'episode_callback_or_prompt_drift')
        return dict(response=trace['response'], error=trace['error'])

    verified = _run(world, _copy(task), invoke, record.get('protocol', 'original'))
    require(next(callbacks, None) is None and verified == record, 'episode_replay_drift')
    return verified


def score_episode(world, task, record):
    """Offline only: strict success requires two legal arcs and final arrival."""
    verified = replay_episode(world, task, record)
    success = verified['reached_goal'] and verified['route_calls'] == 2
    return dict(correct=success, strict_success=success, reached_goal=verified['reached_goal'], denominator=1,
        legal_routes=verified['route_calls'], actor_calls=verified['actor_calls'], memory_calls=verified['memory_calls'],
        terminal_reason=verified['terminal_reason'], episode_sha256=verified['episode_sha256'])


episode_scoring = score_episode
