"""Prospective, append-only math capacity overlays for genuine safe boundaries."""

from copy import deepcopy
import hashlib
import json
import math
from pathlib import Path
import time


SCHEMA = 'MATH_R120_LEASE_HEADROOM_V1'
BLOCK_CYCLES = 4096
REFILL_BEFORE_CYCLES = 16
SCHEDULES = {
    'BASE_R110': dict(episodes=2, native_per_cycle=16, parent_per_cycle=8,
                     safe_boundary='BASE_SAVED_CONTEXT_AND_READOUT'),
    'SHARED_F2_A2': dict(episodes=2, native_per_cycle=26, parent_per_cycle=6,
                        safe_boundary='SHARED_COMMITTED_RELOADED_DEV_SETTLED'),
}


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def digest(document):
    return hashlib.sha256(json.dumps(document, sort_keys=True, separators=(',', ':'),
                                    allow_nan=False).encode()).hexdigest()


def reference(path):
    path = Path(path).resolve(strict=True)
    return dict(path=str(path), sha256=hashlib.sha256(path.read_bytes()).hexdigest())


def checked(binding):
    require(set(binding) == {'path', 'sha256'} and reference(binding['path']) == binding,
            'exact_immutable_reference')
    return json.loads(Path(binding['path']).read_text())


def integer(value):
    return type(value) is int and value >= 0


def validate_limits(limits, used):
    require(set(limits) == {'cycles', 'native', 'parent'} and
            set(used) == {'native', 'parent'}, 'explicit_cumulative_limits')
    require(all(integer(value) for value in (*limits.values(), *used.values())), 'integer_counts_not_bool')
    require(limits['cycles'] > 0 and all(used[key] <= limits[key] for key in used), 'existing_counts_within_limits')


def propose(*, family, root, original_limits, used, next_cycle, clock_reference,
            train_end_unix, hard_end_unix, historical_binding, now=None):
    now = time.time() if now is None else now
    require(family in SCHEDULES and Path(root).is_absolute(), 'owned_family_root')
    validate_limits(original_limits, used)
    require(integer(next_cycle) and next_cycle > 0, 'genuine_next_cycle')
    require(all(type(value) in (int, float) and math.isfinite(value)
                for value in (now, train_end_unix, hard_end_unix)) and
            now < train_end_unix < hard_end_unix, 'same_live_lease_clock')
    schedule = SCHEDULES[family]
    extra = max(BLOCK_CYCLES, math.ceil((train_end_unix - now) / 60) * 4)
    cycles = max(original_limits['cycles'], next_cycle - 1) + extra
    effective = dict(cycles=cycles,
        native=max(original_limits['native'], used['native']) + extra * schedule['native_per_cycle'],
        parent=max(original_limits['parent'], used['parent']) + extra * schedule['parent_per_cycle'])
    return dict(schema=SCHEMA, status='PROSPECTIVE_NOT_YET_ADOPTED', family=family, root=str(root),
        original_limits=deepcopy(original_limits), effective_limits=effective,
        cumulative_used_at_proposal=deepcopy(used), next_cycle_at_proposal=next_cycle,
        clock=deepcopy(clock_reference), train_end_unix=train_end_unix, hard_end_unix=hard_end_unix,
        historical_binding=deepcopy(historical_binding), schedule=deepcopy(schedule),
        additional_cycle_capacity=extra, refill_before_cycles=REFILL_BEFORE_CYCLES,
        sizing='four_times_one_minute_cycles_through_lease_at_least4096; sizing_not_measured_throughput',
        quota_exhaustion_is_life_end=False, refill_at_safe_boundary=True,
        no_new_control=True, no_replay=True, original_final_quota_changed=False,
        shared_startup_files_changed=False, source_cohort_extension_required=True,
        constructed_unix=now)


def validate_boundary(proposal, boundary, *, now=None):
    now = time.time() if now is None else now
    require(proposal['schema'] == SCHEMA and proposal['family'] in SCHEDULES, 'known_headroom_schema')
    require(now < proposal['train_end_unix'], 'actual_lease_training_cutoff')
    require(boundary['root'] == proposal['root'] and
            boundary['kind'] == proposal['schedule']['safe_boundary'], 'genuine_family_safe_boundary')
    require(boundary['inflight_native'] == boundary['inflight_parent'] == boundary['inflight_optimizer'] == 0,
            'no_inflight_or_partial_boundary')
    require(boundary['next_cycle'] == boundary['completed_cycle'] + 1 and
            boundary['next_cycle'] >= proposal['next_cycle_at_proposal'], 'settled_monotonic_cursor')
    require(boundary['readout_complete'] is True and boundary['context_saved'] is True,
            'actual_saved_context_and_finished_readout')
    require(boundary['counters_before'] == boundary['counters_after'] and
            all(integer(boundary['counters_before'][key]) and
                boundary['counters_before'][key] >= value
                for key, value in proposal['cumulative_used_at_proposal'].items()),
            'no_counter_mutation_or_reset')
    require(boundary['clock'] == proposal['clock'] and
            boundary['hard_end_unix'] == proposal['hard_end_unix'], 'no_wall_extension')
    require(boundary['current_source'] and boundary['context_reference'] and boundary['readout_reference'],
            'actual_source_context_readout_refs_required')
    if proposal['family'] == 'SHARED_F2_A2':
        require(boundary['committed_generation'] == boundary['mounted_generation'] >= 1 and
                boundary['committed_checkpoint_sha256'] == boundary['mounted_checkpoint_sha256'],
                'committed_reloaded_same_child')
        require(boundary['optimizer_owner'] == 'F1' and boundary['local_optimizer_steps'] == 0,
                'same_single_shared_optimizer')
        require(boundary.get('common_extension_reference') and
                boundary.get('common_extension_coordinated') is True, 'Main_common_safe_boundary_not_startup_repin')
    return deepcopy(boundary['counters_before'])


def grow_before_cycle(proposal, *, used, next_cycle):
    """A successor calls this BEFORE old cap checks; it never zeroes usage."""
    require(set(used) == {'native', 'parent'} and all(integer(value) for value in used.values()), 'actual_cumulative_usage')
    require(integer(next_cycle) and next_cycle >= proposal['next_cycle_at_proposal'], 'monotonic_cycle')
    result = deepcopy(proposal)
    limits, schedule = result['effective_limits'], result['schedule']
    require(all(used[key] >= result['cumulative_used_at_proposal'][key] for key in used), 'no_usage_reset')
    while (limits['cycles'] - next_cycle + 1 < REFILL_BEFORE_CYCLES or
           any(limits[key] - used[key] < REFILL_BEFORE_CYCLES * schedule[key + '_per_cycle'] for key in used)):
        limits['cycles'] += BLOCK_CYCLES
        for key in used:
            limits[key] += BLOCK_CYCLES * schedule[key + '_per_cycle']
    result['cumulative_used_at_last_check'] = deepcopy(used)
    result['next_cycle_at_last_check'] = next_cycle
    return result


def commit_overlay(directory, proposal, boundary, cohort_reference, *, verify=checked, now=None):
    """Write only a new overlay after a verified boundary, never live CONFIG."""
    used = validate_boundary(proposal, boundary, now=now)
    clock_document = verify(proposal['clock'])
    declared_clock = clock_document.get('clock', clock_document)
    declared_train = declared_clock.get('train_end_unix', declared_clock.get('native_deadline_unix'))
    declared_hard = declared_clock.get('hard_end_unix', declared_clock.get('hard_deadline_unix'))
    require(declared_train == proposal['train_end_unix'] and declared_hard == proposal['hard_end_unix'],
            'actual_clock_bytes_not_just_matching_label')
    for name in ('current_source', 'context_reference', 'readout_reference'):
        verify(boundary[name])
    cohort = verify(cohort_reference)
    require(cohort['root'] == proposal['root'] and cohort['first_cycle'] <= boundary['next_cycle'] <= cohort['last_cycle'],
            'prospectively_frozen_next_cycle_available')
    require(cohort['train_per_cycle'] == 2 and cohort['prior_ids_excluded'] is True and
            cohort['question_hash_collisions'] == 0 and cohort['sealed_FINAL_in_parent_or_rows'] is False,
            'same_two_episode_source_visibility_contract')
    if proposal['family'] == 'SHARED_F2_A2':
        extension = verify(boundary['common_extension_reference'])
        require(extension['branch_root'] == proposal['root'] and
                extension['cohort'] == cohort_reference and extension['optimizer_owner'] == 'F1' and
                extension['clock'] == proposal['clock'], 'bound_Main_registry_extension')
    adopted = grow_before_cycle(proposal, used=used, next_cycle=boundary['next_cycle'])
    adopted.update(status='SAFE_BOUNDARY_OVERLAY_WRITTEN_NOT_ACTOR_ACTIVATION',
        boundary=deepcopy(boundary), cohort=deepcopy(cohort_reference), prior_proposal_sha256=digest(proposal))
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / ('HEADROOM_' + digest(adopted) + '.json')
    with path.open('x') as stream:
        json.dump(adopted, stream, sort_keys=True, indent=2, allow_nan=False)
    return reference(path)


def learned_lineage(*, historic_checkpoint, shared_checkpoint, base_context, optimizer_loaded=False):
    require(type(optimizer_loaded) is bool, 'explicit_actual_optimizer_status')
    if historic_checkpoint is not None:
        require(shared_checkpoint is None, 'do_not_silently_replace_historic_child')
        return dict(kind='HISTORIC_LEARNED_MATH_CONTINUATION', checkpoint=deepcopy(historic_checkpoint),
            context=deepcopy(base_context), optimizer_loaded=optimizer_loaded,
            label='ACTUAL_L2_WEIGHT_UPDATES_REQUIRE_WRITE_RECEIPTS' if optimizer_loaded else
                  'LEARNED_WEIGHTS_CONTEXTUAL_PARENTING_ELICITATION_ONLY', prior_learned_lineage_claim=True)
    require(shared_checkpoint is not None and base_context is not None and
            shared_checkpoint.get('generation') == 1 and shared_checkpoint.get('checkpoint_sha256') ==
            '43ce68acabb18f661ff929600239eb0a632981da841dd1182f886a85df78a02d',
            'explicit_authorized_gen1_plus_actual_BASE_context_fork')
    require(not optimizer_loaded, 'fork_does_not_inherit_F1_optimizer_ownership')
    return dict(kind='FORK_SHARED_GEN1_PLUS_RECORDED_BASE_MATH_CONTEXT',
        checkpoint=deepcopy(shared_checkpoint), context=deepcopy(base_context), optimizer_loaded=False,
        label='ELICITATION_ONLY_NO_LOCAL_LORA_UPDATES', prior_learned_lineage_claim=False,
        source_lineages_distinct=True)
