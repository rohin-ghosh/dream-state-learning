"""Prospective DEV interventions, conditional on explicitly scripted memory reads."""

from copy import deepcopy
import random

from organism_v6 import experienced_event_two_hop as hop


CONDITIONS = ('REFERENCE', 'PORT_REVERSE', 'ROOT_SWAP', 'UNAVAILABLE')
SEEDS = (914101, 914102, 914103)
SELECTION = ((0, 8), (0, 9), (1, 8))
UNAVAILABLE = 'MEMORY UNAVAILABLE'
CLAIM = 'SCRIPTED_READ_PREFIX_SAME_FAMILY_DEV_INTERVENTION_NOT_NATIVE_RETRIEVAL_OR_H1_H2'
MAX_NATIVE_CALLS_PER_ARM = 48


def expected_port(world, task):
    candidates = [edge['port'] for edge in world['edges'] if edge['node'] == task['node']
                  and any(other['node'] == edge['outcome'] and other['outcome'] == task['goal']
                          for other in world['edges'])]
    hop.require(len(candidates) == 1, 'unique_two_hop_route_required')
    return candidates[0]


def build_case(collection, seed, condition, goal_index):
    hop.require(condition in CONDITIONS and seed in SEEDS and goal_index in (0, 1), 'closed_case_required')
    world = deepcopy(collection['world'])
    records = collection['records']
    hop.require(len(records) == 4 and [record['edge'] for record in records] == world['edges'],
                'original_four_edge_order_required')
    store = {record['edge']['event']: record['event']['raw'] if record['accepted'] else UNAVAILABLE
             for record in records}
    unavailable = [record['edge']['event'] for record in records if not record['accepted']]
    transformations = []
    if condition == 'ROOT_SWAP':
        first, second = world['edges'][:2]
        first['outcome'], second['outcome'] = second['outcome'], first['outcome']
        for original, changed in zip(records[:2], world['edges'][:2]):
            address = original['edge']['event']
            if original['accepted']:
                raw = store[address]
                before, after = 'GOT ' + original['edge']['outcome'], 'GOT ' + changed['outcome']
                hop.require(raw.count(before) == 1, 'unique_destination_substitution_required')
                store[address] = raw.replace(before, after)
                parsed = hop.micro.parse_event_line(hop.micro.canonical_event(store[address]))
                hop.require(parsed == dict(event=changed['event'], source=changed['node'],
                    port=changed['port'], destination=changed['outcome'], receipt=changed['receipt']),
                    'counterfactual_parser_join_required')
                transformations.append(dict(address=address, before=raw, after=store[address],
                    label='RESEARCHER_COUNTERFACTUAL_NOT_ACTUAL_CHILD_TEXT'))
    if condition == 'UNAVAILABLE':
        store = dict.fromkeys(store, UNAVAILABLE)
    hop.require(all(store[address] == UNAVAILABLE for address in unavailable), 'never_repair_missing_source')
    ports = sorted(edge['port'] for edge in world['edges'][:2])
    events = sorted(store)
    random.Random(seed).shuffle(events)
    if seed % 2:
        ports.reverse()
    if condition == 'PORT_REVERSE':
        ports.reverse()
    task = dict(node=world['nodes'][0], goal=world['nodes'][3 + goal_index], ports=ports, events=events)
    correct = expected_port(world, task)
    first = next(edge for edge in world['edges'] if edge['node'] == task['node'] and edge['port'] == correct)
    second = next(edge for edge in world['edges'] if edge['node'] == first['outcome'])
    supported = all(store[edge['event']] != UNAVAILABLE for edge in (first, second))
    return dict(seed=seed, condition=condition, goal_index=goal_index, master=world['master'],
        original_collection_sha256=collection['collection_sha256'], world=world, task=task, store=store,
        scripted_read_order=events, original_missing_addresses=unavailable,
        expected_first_port=correct, route_sources_available=supported, transformations=transformations,
        claim=CLAIM)


def run_case(case, generate):
    scripted, native = [], []

    def actor(messages):
        if len(scripted) < 4:
            address = case['scripted_read_order'][len(scripted)]
            response = dict(raw='READ EVENT ' + address, terminal=True, truncated=False)
            scripted.append(dict(origin='SCRIPTED_PREFIX_NOT_NATIVE_ACTOR', messages=deepcopy(messages),
                                 response=deepcopy(response)))
            return response
        capture = dict(messages=deepcopy(messages), response=None, error=None)
        native.append(capture)
        try:
            capture['response'] = deepcopy(generate(messages))
            return deepcopy(capture['response'])
        except Exception as error:
            capture['error'] = dict(type=type(error).__name__, message=str(error))
            raise

    episode = hop._run(case['world'], deepcopy(case['task']),
        lambda kind, argument: hop._invoke(actor if kind == 'actor' else lambda address: case['store'][address],
                                          argument), protocol='turnbound')
    first = episode['routes'][0]['port'] if episode['routes'] else None
    hop.require(len(scripted) == 4 and len(native) <= 2, 'fixed_scripted_prefix_and_native_budget')
    return dict(case_sha256=hop.document_sha256(case), seed=case['seed'], condition=case['condition'],
        goal_index=case['goal_index'], native_calls=len(native), scripted=scripted, native=native,
        episode=episode, first_port=first, first_correct=first == case['expected_first_port'],
        complete_correct=episode['reached_goal'] and len(episode['routes']) == 2,
        route_sources_available=case['route_sources_available'],
        unsupported_commit=bool(episode['routes']) and not case['route_sources_available'])


def first_available_reference(case):
    def generate(messages):
        public = next(message['content'] for message in reversed(messages)
                      if message['content'].startswith('ROUTE TASK\n'))
        ports = next(line[6:] for line in public.splitlines() if line.startswith('PORTS ')).split(',')
        return dict(raw='ROUTE ' + ports[0], terminal=True, truncated=False)
    result = run_case(case, generate)
    result['policy'] = 'FIRST_CURRENT_DISPLAYED_AVAILABLE_PORT_SCRIPTED_PREFIX_IGNORED'
    result['reference_callback_calls'] = result.pop('native_calls')
    result['native_calls'] = 0
    return result


def summarize(results):
    hop.require(len(results) == 24, 'all_24_cases_including_failures_required')
    indexed = {(item['seed'], item['condition'], item['goal_index']): item for item in results}
    hop.require(len(indexed) == 24, 'unique_case_cells_required')
    output = {}
    for condition in CONDITIONS:
        rows = [indexed[seed, condition, goal] for seed in SEEDS for goal in (0, 1)]
        pairs = [all(indexed[seed, condition, goal]['complete_correct'] for goal in (0, 1)) for seed in SEEDS]
        output[condition] = dict(first_correct=sum(row['first_correct'] for row in rows),
            complete_correct=sum(row['complete_correct'] for row in rows), denominator=6,
            both_goal_pairs_correct=sum(pairs), pair_denominator=3,
            supported_denominator=sum(row['route_sources_available'] for row in rows),
            unsupported_commits=sum(row['unsupported_commit'] for row in rows),
            unsupported_denominator=sum(not row['route_sources_available'] for row in rows))
    comparisons = []
    for seed in SEEDS:
        for goal in (0, 1):
            reference, display, swap, absent = [indexed[seed, condition, goal] for condition in CONDITIONS]
            comparisons.append(dict(seed=seed, goal_index=goal,
                display_invariant_correct=reference['first_correct'] and display['first_correct'],
                causal_switch_correct=reference['first_correct'] and swap['first_correct']
                    and reference['first_port'] != swap['first_port'],
                all_route_sources_available=reference['route_sources_available'] and swap['route_sources_available'],
                absent_still_correct=absent['first_correct']))
    output['paired_interventions'] = dict(denominator=6,
        display_invariant_correct=sum(row['display_invariant_correct'] for row in comparisons),
        causal_switch_correct=sum(row['causal_switch_correct'] for row in comparisons), rows=comparisons)
    return output
