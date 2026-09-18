"""Exhaustion treatments over new displays of replay-verified TRAIN worlds."""

from copy import deepcopy
from itertools import permutations
from types import FunctionType

from organism_v6 import orch_rich_hot_node3_route as previous
from organism_v6 import orch_rich_hot_node1_exhaustion as exhaustion


PHASE = 'ROHIN100_ROUTE_EXHAUSTION_V1'
original = previous.original
validate = previous.validate
GUIDANCE = exhaustion.instruction('EXHAUSTION_ONLY')


def arm(index):
    original.hop.require(index in (3, 4, 5), 'only_owned_node3_slots')
    return 'EXHAUSTION_ONLY' if index == 3 else 'EXHAUSTION_PLUS_STEERING'


def guidance(index):
    result = exhaustion.instruction(arm(index))
    if arm(index) == 'EXHAUSTION_PLUS_STEERING':
        result += '\n' + previous.GUIDANCE
    return result


def episode(world, task, generate, store, index):
    namespace = dict(original.episode.__globals__, GUIDANCE=guidance(index))
    function = FunctionType(original.episode.__code__, namespace, original.episode.__name__)
    return function(world, task, generate, store)


def tasks(world, index):
    arm(index)
    originals = previous.tasks(world)
    old = {original.digest(task) for task in originals}
    candidates = []
    for events in permutations(sorted(originals[0]['events'])):
        for ports in (originals[0]['ports'], list(reversed(originals[0]['ports']))):
            for template in (originals[0], originals[2]):
                task = dict(deepcopy(template), ports=list(ports), events=list(events))
                if original.digest(task) not in old:
                    candidates.append(task)
    return candidates[21 + (index - 3) * 5:21 + (index - 2) * 5]


def roster(cohort):
    rows = [dict(index=index, arm=arm(index), world_index=world_index, task=task,
                 task_id='route-train-display-' + original.digest(task))
            for index in (3, 4, 5) for world_index, world in enumerate(cohort['worlds'])
            for task in tasks(world, index)]
    original.hop.require(len(rows) == len({row['task_id'] for row in rows}) == 120,
                         'distinct_exhaustion_displays')
    return dict(phase_version=PHASE, tasks=rows, maximum_calls=720,
                new_independent_worlds=False, source_policy='UNCHANGED_TRAIN_CHILD_EVENTS')
