"""Next TRAIN route batch over replay-verified, child-authored source events."""

from types import FunctionType

from organism_v6 import orch_full_rich as original
from organism_v6.orch_rich_hot_node1_prompt_v2 import BRANCH


PHASE = 'RICH_HOT_NODE3_ROUTE_V2_ROHIN98'
GUIDANCE = (
    'Explain the evidence actually available in this route task and why the next '
    'read or route is useful. Before any memory read, acknowledge that the stored '
    'event has not yet been observed. After a real memory or route result, check '
    'the expectation against that observation. Do not invent memory content, '
    'receipts, observations, or actions. Use only useful task-specific reasoning, '
    'without padding or a prescribed voice or length. ' + BRANCH +
    ' Finish with the single next READ EVENT or ROUTE action required by the system.'
)


def episode(world, task, generate, store):
    namespace = dict(original.episode.__globals__, GUIDANCE=GUIDANCE)
    function = FunctionType(original.episode.__code__, namespace, original.episode.__name__)
    return function(world, task, generate, store)


def tasks(world):
    return original.runtime(world['master'])['build_tasks'](world)


def validate(cohort, source):
    original.hop.require(cohort['split'] == 'TRAIN_SCREEN_NO_FIT', 'train_only_route_source')
    original.hop.require(all(world['master'] in original.MASTERS for world in cohort['worlds']), 'original_training_worlds_only')
    store = original.verify_source(cohort, source)
    original.hop.require(len(store) == 32, 'complete_existing_child_event_store')
    return store
