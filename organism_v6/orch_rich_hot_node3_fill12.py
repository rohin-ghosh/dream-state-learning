"""Prospectively bounded temporary fillers on explicitly released slots1/2."""

from datetime import datetime

from organism_v6 import orch_rich_hot_node1_exhaustion as exhaustion


PHASE = 'ROHIN100_NODE3_FILL12_512_CALLS'
DISPATCH_CUTOFF = datetime.fromisoformat('2026-09-15T05:18:00+00:00').timestamp()
HARD_END = datetime.fromisoformat('2026-09-15T05:23:00+00:00').timestamp()
MAX_SLOT_CALLS = 256
MAX_CALLS = 512


def condition(index):
    exhaustion.require(index in (1, 2), 'only_explicitly_released_node3_1_2')
    return 'ORIGINAL_RICH' if index == 1 else 'LIGHT_BRANCH'


def messages(task, index):
    return exhaustion.messages(task, condition(index))


def can_dispatch(now, slot_calls, total_calls, release_requested=False):
    return (not release_requested and now < DISPATCH_CUTOFF
            and slot_calls < MAX_SLOT_CALLS and total_calls < MAX_CALLS)


def protocol():
    return dict(phase_version=PHASE, indices=[1, 2], arms={str(index): exhaustion.arm(condition(index))
        for index in (1, 2)}, maximum_calls=MAX_CALLS, maximum_calls_per_slot=MAX_SLOT_CALLS,
        prior_aggregate_ceiling=2768, new_aggregate_ceiling=3280, quota_reset=False,
        dispatch_cutoff_unix=DISPATCH_CUTOFF, hard_deadline_unix=HARD_END,
        early_release='explicit canonical READY request, complete own task then exact receipt',
        requested_output=16384, context=32768, raw_storage='GENERATION_NODE_ONLY',
        tasks='UNCHANGED_ORIGINAL_INTENSITY_256_TRAIN_COHORT_NEW_EXHAUSTION_TREATMENT',
        no_training=True, no_automatic_reclaim=True)
