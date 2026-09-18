"""R104/standing-builder treatment-only extension; not an R105 replay change."""

from copy import deepcopy

from organism_v6 import orch_route_parent_campaign as original
from organism_v6 import orch_route_parent_campaign_canonical as canonical
from organism_v6.orch_route_parent_campaign_canonical import (
    INITIAL_STATE, INITIAL_FILE, INITIAL_BATCH, GUIDANCE, REFLECTION,
    runtime, validate_initial, reflection_prefix, target_gate, require, digest,
    shared, rich, record_thinking_metrics,
)


ROOT = '/tmp/orch_route_parent_creative_backfill_20260915'
BASELINE_ROOT = canonical.ROOT
BASELINE_COHORT_SHA256 = '33a7eeb401732365e399ee080a2771c139e3a0ce4cf951216e06722058b4d1ba'
ARMS = ('GUIDED',)
SOURCE_ARM = 'PREEXISTING_CANONICAL_SOURCE'
BASELINE_FIRST = True
RECORD_PARENT_WAIT = True
CAMPAIGN_DEADLINE = canonical.CAMPAIGN_DEADLINE
CAPS = dict(canonical.CAPS, seconds=7200, cycles=4, source_calls=0,
            child_calls_per_lane=256, parent_calls_per_lane=48)
CELL = dict(style='creative', horizon='short', tone='supportive-positive',
            provider='openai/openai/gpt-6-astra')


def presentations_for_cycle(cycle):
    require(type(cycle) is int and 1 <= cycle <= 4, 'four_prospective_cycles_only')
    return 4 if cycle == 1 else 16


def cohort(exclusions):
    existing = canonical.cohort(exclusions)
    require(digest(existing) == BASELINE_COHORT_SHA256, 'exact_existing_canonical_cohort')
    selected = deepcopy(existing)
    selected.update(train=existing['train'][:4], held=existing['held'][:5],
        caps=deepcopy(CAPS), cell=deepcopy(CELL), schema='CREATIVE_BACKFILL_R104_V1',
        presentations_by_cycle=[4, 16, 16, 16],
        control_boundary='TREATMENT_ONLY_ANCHORED_TO_EXISTING_CANONICAL_BASELINE',
        authority='R104_AND_STANDING_BUILDER_NOT_R105_REPLAY_CHANGE')
    return selected


def parent_payload(payload):
    return original.parent_payload(payload, CELL)


def next_identity(initial, arm, cycle, previous_receipt=None):
    require(arm == 'GUIDED', 'no_new_control')
    presentations_for_cycle(cycle)
    return canonical.next_identity(initial, arm, cycle, previous_receipt)


def proposal():
    return dict(authority='R104_AND_STANDING_BUILDER_NOT_R105', root=ROOT,
        physical_index=1, arm='GUIDED', caps=deepcopy(CAPS), cell=deepcopy(CELL),
        initial_state=INITIAL_STATE, initial_file_sha256=INITIAL_FILE,
        baseline_cohort_sha256=BASELINE_COHORT_SHA256,
        selection='FIRST_FOUR_TRAIN_AND_FIRST_FIVE_READOUT_GROUPS_IN_EXISTING_FROZEN_ORDER',
        train_episodes=8, parent_free_readout_episodes=10, sequential_episodes_per_sleep=2,
        presentations_by_cycle=[4, 16, 16, 16], maximum_saved_updates=364,
        maximum_new_reflection_presentations=104, maximum_legacy_trajectory_presentations=624,
        parent_output_tokens_per_call=4096, parent_timeout_seconds=120, parent_retries=0,
        maximum_parent_output_tokens=48*4096, maximum_native_output_tokens=256*512,
        lifetime_seconds=7200, lifetime_starts='ONE_ACTIVATION_AFTER_NATURAL_OFF_RELEASE',
        no_automatic_budget_or_clock_reset=True, no_new_source_generation=True,
        replay='UNCHANGED_CANONICAL_OLD_MIX_NO_FADING_OR_PLASTICITY_CHANGE',
        no_yield='UNCHANGED_NO_VALID_REFLECTIONS_NOOP_NO_REHEARSAL_CLAIM',
        comparison_limits=['New treatment life begins from the original fixed adapter, not OFF C8.',
            'Existing baseline only; no new OFF, frozen-LoRA or NO_LORA control.',
            'Start-time offset, stochastic parent responses and admission yield confound pure style effects.',
            'Different checkpoint tasks preclude a same-task retention or clean causal dose-curve claim.',
            'Historical NO_LORA and adapter-seeded arms have different initial parameter states.'])


def validate_posted(posted, ready_sha256, proposal_sha256):
    require(posted.get('author') == 'Main' and posted.get('board_posted') is True
        and posted.get('ready_sha256') == ready_sha256
        and posted.get('proposal_sha256') == proposal_sha256
        and bool(posted.get('builder_receipt')), 'main_posted_exact_ready_and_builder_receipt_required')


def validate_completion(guard, sleep, readout, guardian_alive, child_alive):
    require(guard.get('status') == 'COMPLETE' and not guardian_alive and not child_alive,
            'natural_guardian_and_child_exit_required')
    for value, phase in ((sleep, 'sleep'), (readout, 'readout')):
        require(value.get('status') == 'COMPLETE' and value.get('arm') == 'UNPARENTED'
                and value.get('cycle') == 8 and value.get('phase') == phase, 'preserve_off_final_cycle')
    require(readout.get('parent_free') is True and sleep['output_adapter'] == readout['input_adapter']
            and sleep['process'] != readout['process']
            and guard['finished_unix'] >= readout['finished_unix'], 'preserved_fresh_final_readout_required')
