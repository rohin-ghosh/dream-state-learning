"""R106 refill: fixed unseen TRAIN displays, unchanged control, labelled META."""

from copy import deepcopy
from itertools import permutations
from types import FunctionType, SimpleNamespace

from organism_v6 import orch_rich_hot_node3_exhaustion_next as previous
from organism_v6 import orch_rich_hot_node3_route_next as batch02
from organism_v6 import orch_rich_hot_node3_route_batch03 as batch03
from organism_v6 import orch_rich_hot_node1_exhaustion as exhaustion


PHASE = 'R106_NODE3_REFILL_2304_V1'
MAX_CALLS = 2304
MAX_SLOT_CALLS = 768
original = previous.original
validate = previous.validate
META = (
    'Solve the task using only the evidence actually available. When useful, '
    'let your reasoning depart from its main line for a grounded check, '
    'side-observation, judgment, aside, or explicitly hypothetical what-if, '
    'then return to the task and explain what the departure changes or confirms. '
    'Do not force a departure, fabricate facts, invent observations, or pad. '
    'A branch is a departure and return, not a requirement for two methods. '
    'A terminal check is distinct from a mid-solution excursion; do not count '
    'ordinary next steps, connective words, or repeated arithmetic as branches. '
    'Method diversity, grounding, correctness, and useful branching are separate. '
    'Before a memory read do not claim to know its contents. Compare expectations '
    'with observations only after the actual result is supplied. '
    'Finish with the single next READ EVENT or ROUTE action required by the system.'
)


def arm(index):
    original.hop.require(type(index) is int and index in (3, 4, 5), 'only_owned_node3_3_4_5')
    return 'EXHAUSTION_ONLY' if index == 3 else 'R106_META_DEPARTURE_RETURN'


def guidance(index):
    return previous.guidance(3) if arm(index) == 'EXHAUSTION_ONLY' else META


def episode(world, task, generate, store, index):
    readout = SimpleNamespace(**dict(vars(original.readout), display=display))
    namespace = dict(original.episode.__globals__, GUIDANCE=guidance(index), readout=readout)
    function = FunctionType(original.episode.__code__, namespace, original.episode.__name__)
    return function(world, task, generate, store)


def display(current, task, ports):
    original.hop.require(task['display_variant'] == 'GOAL_FIRST_PUBLIC_FIELDS_V1', 'fixed_public_layout')
    return (f"ROUTE TASK\nGOAL {task['goal']}\nCURRENT {current}\n"
            f"PORTS {','.join(ports)}\nEVENTS {','.join(task['events'])}")


def tasks(world, index):
    arm(index)
    originals = previous.previous.previous.tasks(world)
    seen = {original.digest(task) for task in originals}
    for provider in (batch02, batch03, previous.previous, previous):
        for slot in (3, 4, 5):
            seen.update(original.digest(task) for task in provider.tasks(world, slot))
    candidates = []
    for template in originals:
        for events in permutations(sorted(template['events'])):
            for ports in permutations(template['ports']):
                task = dict(deepcopy(template), events=list(events), ports=list(ports),
                            display_variant='GOAL_FIRST_PUBLIC_FIELDS_V1')
                digest = original.digest(task)
                if digest not in seen:
                    candidates.append(task)
                    seen.add(digest)
    chosen = candidates[(index - 3) * 16:(index - 2) * 16]
    original.hop.require(len(chosen) == 16, 'insufficient_unseen_training_display_pool')
    return chosen


def roster(cohort):
    rows = [dict(index=index, arm=arm(index), world_index=world_index, task=task,
                 task_id='route-train-display-' + original.digest(task))
            for index in (3, 4, 5) for world_index, world in enumerate(cohort['worlds'])
            for task in tasks(world, index)]
    original.hop.require(len(rows) == len({row['task_id'] for row in rows}) == 384, '384_distinct_displays')
    return dict(phase_version=PHASE, tasks=rows, maximum_calls=MAX_CALLS,
                new_independent_worlds=False, source_policy='UNCHANGED_TRAIN_CHILD_EVENTS')


def assess(response):
    result = exhaustion.assess(response)
    result.update(branch_definition='R106_DEPARTURE_AND_RETURN',
                  semantic_departure_return_count=None, semantic_mid_solution_excursion_count=None,
                  semantic_terminal_check_count=None, semantic_method_count=None,
                  method_self_report_is_not_branch_count=True, semantic_status='UNREVIEWED')
    return result
