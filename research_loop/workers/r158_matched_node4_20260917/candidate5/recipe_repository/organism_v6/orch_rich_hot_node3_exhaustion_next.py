"""Prospectively frozen, previously unseen displays for continuous supply."""

from copy import deepcopy
from itertools import permutations

from organism_v6 import orch_rich_hot_node3_exhaustion as previous


PHASE = 'ROHIN100_ROUTE_EXHAUSTION_NEXT_2304'
original = previous.original
validate = previous.validate
arm = previous.arm
guidance = previous.guidance
episode = previous.episode
MAX_CALLS = 2304
MAX_SLOT_CALLS = 768


def tasks(world, index):
    arm(index)
    originals = previous.previous.tasks(world)
    old = {original.digest(task) for task in originals}
    candidates = []
    for events in permutations(sorted(originals[0]['events'])):
        for ports in (originals[0]['ports'], list(reversed(originals[0]['ports']))):
            for template in (originals[0], originals[2]):
                task = dict(deepcopy(template), ports=list(ports), events=list(events))
                if original.digest(task) not in old:
                    candidates.append(task)
    result = candidates[36 + (index - 3) * 16:36 + (index - 2) * 16]
    original.hop.require(len(result) == 16, 'remaining_unseen_display_pool')
    return result


def roster(cohort):
    rows = [dict(index=index, arm=arm(index), world_index=world_index, task=task,
                 task_id='route-train-display-' + original.digest(task))
            for index in (3, 4, 5) for world_index, world in enumerate(cohort['worlds'])
            for task in tasks(world, index)]
    prior = {row['task_id'] for row in previous.roster(cohort)['tasks']}
    ids = {row['task_id'] for row in rows}
    original.hop.require(len(rows) == len(ids) == 384 and not ids.intersection(prior),
                         'new_distinct_displays_no_exhaustion_regeneration')
    return dict(phase_version=PHASE, tasks=rows, maximum_calls=MAX_CALLS,
                new_independent_worlds=False, source_policy='UNCHANGED_TRAIN_CHILD_EVENTS')
