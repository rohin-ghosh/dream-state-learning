"""Prospectively frozen unseen displays in the existing TRAIN route worlds."""

from copy import deepcopy
from itertools import permutations

from organism_v6 import orch_rich_hot_node3_route as previous


PHASE = 'RICH_HOT_NODE3_ROUTE_V2_BATCH02_UNSEEN_DISPLAYS'
GUIDANCE = previous.GUIDANCE
original = previous.original
episode = previous.episode
validate = previous.validate


def tasks(world, index):
    original.hop.require(index in (3, 4, 5), 'only_owned_node3_slots')
    originals = previous.tasks(world)
    old = {original.digest(task) for task in originals}
    candidates = []
    for events in permutations(sorted(originals[0]['events'])):
        for ports in (originals[0]['ports'], list(reversed(originals[0]['ports']))):
            for template in (originals[0], originals[2]):
                task = dict(deepcopy(template), ports=list(ports), events=list(events))
                if original.digest(task) not in old:
                    candidates.append(task)
    chosen = candidates[(index - 3) * 5:(index - 2) * 5]
    original.hop.require(len(chosen) == 5, 'five_unseen_displays_per_world')
    return chosen


def roster(cohort):
    rows = [dict(index=index, world_index=world_index, task=task,
                 task_id='route-train-display-' + original.digest(task))
            for index in (3, 4, 5) for world_index, world in enumerate(cohort['worlds'])
            for task in tasks(world, index)]
    original.hop.require(len(rows) == len({row['task_id'] for row in rows}) == 120,
                         'distinct_new_displays_required')
    return dict(phase_version=PHASE, tasks=rows, maximum_calls=720,
                new_independent_worlds=False, source_policy='UNCHANGED_TRAIN_CHILD_EVENTS')
