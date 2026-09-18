"""R107 persistence and functional control; two slots, no prescribed shape."""

from types import FunctionType, SimpleNamespace

from organism_v6 import orch_rich_hot_node3_r106 as previous
from organism_v6 import orch_rich_hot_node1_exhaustion as exhaustion


PHASE = 'R107_NODE3_REFILL_1536_V1'
MAX_CALLS = 1536
MAX_SLOT_CALLS = 768
original = previous.original
validate = previous.validate
display = previous.display
PERSISTENCE = (
    'Do not settle automatically at the first adequate answer. Decide what '
    'further reasoning would most improve the solution, then pursue that work '
    'using only the available evidence. Continue in depth where the task '
    'warrants it; stop when further work would only repeat or pad. '
    'Do not fabricate observations, manufacture disagreement, or force surprise. '
    'Before a memory read do not claim to know its contents. Use actual returned '
    'evidence rather than simulated results. Finish with the single next '
    'READ EVENT or ROUTE action required by the system.'
)
META = (
    'When you recognize a limitation in your current reasoning or a more useful '
    'direction, use that realization to decide where your cognitive effort goes '
    'and change what you do next. Merely announcing a realization or adding '
    'a check heading is not enough. Follow through on the useful next reasoning '
    'step and let actual evidence guide continuation or stopping. '
    'There is no required number of branches, methods, checks, or realizations.'
)


def arm(index):
    original.hop.require(type(index) is int and index in (4, 5), 'only_owned_node3_4_5_main_owns_3')
    return 'R107_PERSISTENCE_ONLY' if index == 4 else 'R107_PERSISTENCE_FUNCTIONAL_META'


def guidance(index):
    return PERSISTENCE if arm(index) == 'R107_PERSISTENCE_ONLY' else PERSISTENCE + '\n' + META


def tasks(world, index):
    arm(index)
    return previous.tasks(world, index)


def roster(cohort):
    rows = [dict(index=index, arm=arm(index), world_index=world_index, task=task,
                 task_id='route-train-display-' + original.digest(task))
            for index in (4, 5) for world_index, world in enumerate(cohort['worlds'])
            for task in tasks(world, index)]
    original.hop.require(len(rows) == len({row['task_id'] for row in rows}) == 256, '256_distinct_displays')
    return dict(phase_version=PHASE, tasks=rows, maximum_calls=MAX_CALLS,
                new_independent_worlds=False, source_policy='UNCHANGED_TRAIN_CHILD_EVENTS')


def episode(world, task, generate, store, index):
    readout = SimpleNamespace(**dict(vars(original.readout), display=display))
    namespace = dict(original.episode.__globals__, GUIDANCE=guidance(index), readout=readout)
    function = FunctionType(original.episode.__code__, namespace, original.episode.__name__)
    return function(world, task, generate, store)


def assess(response):
    result = exhaustion.assess(response)
    result.update(diagnostic_version='R107_PERSISTENCE_FUNCTIONAL_CONTROL',
                  semantic_persistence_beyond_first_adequate=None,
                  functional_metarealisation_to_changed_continuation=None,
                  semantic_departure_return_count=None, semantic_terminal_check_count=None,
                  semantic_method_count=None, self_report_is_not_functional_control=True,
                  semantic_status='UNREVIEWED')
    return result
