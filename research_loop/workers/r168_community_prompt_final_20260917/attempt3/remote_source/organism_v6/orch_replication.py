"""Prospectively named probes and independently implemented bounded readout."""

from copy import deepcopy
from types import FunctionType

from organism_v6 import experienced_event_two_hop as source_api


MASTERS = tuple(f'ORCH-REPLICATION-20260914-BLIND-V1-WORLD-{index}' for index in range(8))
PAIRS = ((0, 2), (1, 3))
STATES = ('ORIGINAL37EC', 'FULL_TARGET', 'NEW_TRAJECTORY_LOSS_OFF')
UNAVAILABLE = 'MEMORY UNAVAILABLE'
CALL_CAP = 240
SOURCE_CAP = 64
MAX_NEW_TOKENS = 160
MAX_CONTEXT = 2048
digest = source_api.document_sha256


def runtime(master):
    if master not in MASTERS:
        raise ValueError('unfrozen_master')
    namespace = dict(source_api.__dict__, MASTER=master, TRANSFER_MASTER=master)
    for name, function in source_api.__dict__.items():
        if isinstance(function, FunctionType) and function.__globals__ is source_api.__dict__:
            defaults = (master,) if name == 'build_world' else function.__defaults__
            namespace[name] = FunctionType(function.__code__, namespace, name, defaults, function.__closure__)
    return namespace


def cohort(old_ids=()):
    seen = set(old_ids)
    worlds = []
    for master in MASTERS:
        world = runtime(master)['build_world'](master)
        identifiers = {value for edge in world['edges'] for value in edge.values()}
        if seen.intersection(identifiers):
            raise ValueError('namespace_collision')
        seen.update(identifiers)
        worlds.append(world)
    return dict(worlds=worlds, pairs=[list(pair) for pair in PAIRS], world_denominator=8,
                pair_denominator=16, goal_denominator=32, condition='OWN_TEXT', teaching=False)


def tasks(world):
    root = world['nodes'][0]
    ports = sorted(edge['port'] for edge in world['edges'] if edge['node'] == root)
    addresses = sorted(edge['event'] for edge in world['edges'])
    return [dict(node=root, goal=goal, ports=ports[::direction], events=addresses[::direction])
            for goal in world['nodes'][3:] for direction in (1, -1)]


def collect(frozen, generate, emit):
    collections = []
    store = {}
    for index, world in enumerate(frozen['worlds']):
        collection = runtime(world['master'])['collect_world'](world, generate)
        runtime(world['master'])['replay_collection'](collection)
        collections.append(collection)
        for record in collection['records']:
            if record['accepted']:
                store[record['edge']['event']] = record['event']['raw']
        emit(f'WORLD_{index:02d}.json', collection)
    return dict(collections=collections, store=store, store_sha256=digest(store),
                accepted_events=len(store), event_denominator=32,
                cohort_sha256=digest(frozen), model_calls=sum(item['model_calls'] for item in collections))


def verify_source(frozen, document):
    if len(document['collections']) != 8 or document['cohort_sha256'] != digest(frozen):
        raise ValueError('source_cohort_mismatch')
    store = {}
    for world, collection in zip(frozen['worlds'], document['collections']):
        if collection['world'] != world:
            raise ValueError('source_world_mismatch')
        verified = runtime(world['master'])['replay_collection'](collection)
        for record in verified['records']:
            if record['accepted']:
                store[record['edge']['event']] = record['event']['raw']
    if store != document['store'] or digest(store) != document['store_sha256']:
        raise ValueError('source_raw_bytes_changed')
    if len(store) != document['accepted_events'] or document['event_denominator'] != 32:
        raise ValueError('source_denominator_changed')
    return store


def display(current, task, ports):
    return (f"ROUTE TASK\nCURRENT {current}\nGOAL {task['goal']}\n"
            f"PORTS {','.join(ports)}\nEVENTS {','.join(task['events'])}")


def response_text(response):
    if not isinstance(response, dict) or not isinstance(response.get('raw'), str):
        raise ValueError('malformed_response')
    if response.get('terminal') is not True or response.get('truncated') is not False:
        raise ValueError('nonterminal_or_truncated')
    return response['raw']


def episode(world, task, generate, store):
    current, ports = task['node'], list(task['ports'])
    messages = [dict(role='system', content=source_api.TURNBOUND_SYSTEM),
                dict(role='user', content=display(current, task, ports))]
    reads, routes, captures = [], [], []
    reason = 'actor_call_cap'
    for turn in range(6):
        capture = dict(turn=turn, messages=deepcopy(messages), response=None, error=None)
        captures.append(capture)
        try:
            capture['response'] = generate(deepcopy(messages))
            raw = response_text(capture['response'])
        except Exception as error:
            capture['error'] = dict(type=type(error).__name__, message=str(error))
            reason = 'generation_failure'
            break
        messages.append(dict(role='assistant', content=raw))
        command = raw.rstrip('\n')
        if command.startswith('READ EVENT '):
            address = command[len('READ EVENT '):]
            if address not in task['events'] or address in [entry['address'] for entry in reads] or len(reads) >= 4:
                reason = 'invalid_or_duplicate_read'
                break
            text = store.get(address, UNAVAILABLE)
            reads.append(dict(address=address, raw=text))
            messages.append(dict(role='user', content='MEMORY RESULT\n' + text))
        elif command.startswith('ROUTE '):
            port = command[len('ROUTE '):]
            if port not in ports or len(routes) >= 2:
                reason = 'invalid_route'
                break
            edge = next(edge for edge in world['edges'] if edge['node'] == current and edge['port'] == port)
            routes.append(dict(source=current, port=port, destination=edge['outcome'], receipt=edge['receipt']))
            current = edge['outcome']
            ports = sorted(edge['port'] for edge in world['edges'] if edge['node'] == current)
            messages.append(dict(role='user', content=display(current, task, ports)))
            if current == task['goal']:
                reason = 'reached_goal'
                break
            if not ports:
                reason = 'dead_end'
                break
        else:
            reason = 'invalid_command'
            break
    return dict(task=deepcopy(task), routes=routes, reads=reads, captures=captures,
                terminal_reason=reason, current=current, actor_calls=len(captures),
                correct=current == task['goal'] and len(routes) == 2, messages=messages)


def score(world, task, record):
    current = task['node']
    legal = True
    for route in record['routes']:
        matches = [edge for edge in world['edges'] if edge['node'] == current and edge['port'] == route['port']]
        if len(matches) != 1 or route != dict(source=current, port=matches[0]['port'],
                                              destination=matches[0]['outcome'], receipt=matches[0]['receipt']):
            legal = False
            break
        current = route['destination']
    valid = legal and len(record['routes']) == 2 and current == task['goal']
    if valid != record['correct']:
        raise ValueError('reported_score_disagrees_with_transitions')
    return valid


def summarize(world, records):
    if len(records) != 4:
        raise ValueError('fixed_four_goal_denominator')
    public_tasks = tasks(world)
    correct = [score(world, task, record) for task, record in zip(public_tasks, records)]
    pair_records = []
    for first, second in PAIRS:
        first_ports = [records[index]['routes'][0]['port'] if records[index]['routes'] else None
                       for index in (first, second)]
        both = correct[first] and correct[second] and len(set(first_ports)) == 2
        pair_records.append(dict(indexes=[first, second], correct=both, first_ports=first_ports))
    return dict(goals=sum(correct), goal_denominator=4, pairs=sum(item['correct'] for item in pair_records),
                pair_denominator=2, paired=pair_records)


def first_port(messages):
    public = next(message['content'] for message in reversed(messages)
                  if message['role'] == 'user' and message['content'].startswith('ROUTE TASK\n'))
    line = next(line for line in public.splitlines() if line.startswith('PORTS '))
    return dict(raw='ROUTE ' + line[6:].split(',')[0], terminal=True, truncated=False)


def evaluate(frozen, store, generate, emit):
    panels = []
    for world_index, world in enumerate(frozen['worlds']):
        records = []
        for task_index, task in enumerate(tasks(world)):
            record = episode(world, task, generate, store)
            records.append(record)
            emit(f'WORLD_{world_index:02d}_GOAL_{task_index}.json', record)
        panels.append(summarize(world, records))
    return dict(worlds=panels, pairs=sum(panel['pairs'] for panel in panels), pair_denominator=16,
                goals=sum(panel['goals'] for panel in panels), goal_denominator=32)


def compare(results, reference):
    if set(results) != set(STATES):
        raise ValueError('three_terminal_states_required')
    for result in results.values():
        if result['status'] != 'COMPLETE' or result['routing']['pair_denominator'] != 16:
            raise ValueError('incomplete_comparison')
    for field in ('cohort_sha256', 'store_sha256', 'protocol_sha256', 'prepare_sha256', 'source_commit'):
        if len({result[field] for result in results.values()}) != 1:
            raise ValueError('unmatched_' + field)
    full = results['FULL_TARGET']['routing']
    off = results['NEW_TRAJECTORY_LOSS_OFF']['routing']
    differences = [left['pairs'] - right['pairs'] for left, right in zip(full['worlds'], off['worlds'])]
    pairs = [(left['correct'], right['correct']) for left_world, right_world in zip(full['worlds'], off['worlds'])
             for left, right in zip(left_world['paired'], right_world['paired'])]
    return dict(states={state: dict(routing=result['routing'], retention=result['retention'], audit=result['audit'],
                                   calls=result['model_calls'], adapter_state=result['adapter_state_before'])
                        for state, result in results.items()}, reference=reference,
                full_minus_off_pairs=full['pairs'] - off['pairs'], world_pair_differences=differences,
                full_only_pairs=sum(left and not right for left, right in pairs),
                off_only_pairs=sum(right and not left for left, right in pairs),
                reference_margins={state: result['routing']['pairs'] - reference['pairs']
                                   for state, result in results.items()},
                independent_training_seed_replication=False, new_fits=0,
                claim='FRESH_FIXED_COHORT_READOUT_ON_ONE_EXPOSED_DEV_LINEAGE_ONLY')
