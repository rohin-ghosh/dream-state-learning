"""Prospective old-CODE lease capacity contract; never mutates or launches actors."""

from copy import deepcopy
import hashlib
import json

from organism_v6 import orch_r108_code_parent_r109 as original


SCHEMA = 'R124_OLD_CODE_LEASE_CAPACITY_V1'
FIRST_NEW_CYCLE = 101
CHUNK_CYCLES = 64
MAX_CHUNKS = 64
NATIVE_PER_CYCLE = 15
PARENT_PER_CYCLE = 2
ALLOCATIONS = {'ovx2': (3, 4, 5, 6), 'a40r': (4, 5, 6)}


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'),
        allow_nan=False).encode()).hexdigest()


def validate_reference(reference):
    require(isinstance(reference, dict) and set(reference) == {'path', 'sha256'}
        and isinstance(reference['path'], str) and reference['path'].startswith('/')
        and isinstance(reference['sha256'], str) and len(reference['sha256']) == 64
        and all(character in '0123456789abcdef' for character in reference['sha256']), 'absolute_hash_reference')


def capacity(plan, plan_reference):
    validate_reference(plan_reference)
    require(plan['wrapper'] in ALLOCATIONS and plan['physical'] in ALLOCATIONS[plan['wrapper']],
        'seven_allocated_old_CODE_forks_only')
    require(plan['cycle_limit'] == 100 and plan['first_cycle'] == 27
        and plan['ancestry']['native_cap'] == 1500 and plan['ancestry']['parent_cap'] == 500,
        'actual_finite_predecessor_contract')
    require(plan['optimizer_updates'] == 0 and plan['parent_wait_seconds'] == 0
        and plan['parent_cadence'] == 'EPISODE' and plan['parent_ttl_seconds'] == 600,
        'same_readonly_nonblocking_loop')
    require(plan['hard_end_unix'] == plan['lease_end_unix'] - 21600
        and plan['train_end_unix'] == plan['hard_end_unix'] - 120, 'actual_existing_lease_wall')
    require((plan['adapter'] is None) == (plan['wrapper'] == 'a40r'), 'preserve_BASE_vs_gen1_forks')
    return dict(schema=SCHEMA, predecessor=deepcopy(plan_reference), root=plan['root'],
        wrapper=plan['wrapper'], physical=plan['physical'], gpu_uuid=plan['gpu_uuid'],
        model_source=deepcopy(plan['adapter']), optimizer_updates=0,
        first_new_cycle=FIRST_NEW_CYCLE, chunk_cycles=CHUNK_CYCLES, max_chunks=MAX_CHUNKS,
        last_new_cycle=FIRST_NEW_CYCLE + CHUNK_CYCLES * MAX_CHUNKS - 1,
        prospective_native_increment=CHUNK_CYCLES * MAX_CHUNKS * NATIVE_PER_CYCLE,
        prospective_parent_increment=CHUNK_CYCLES * MAX_CHUNKS * PARENT_PER_CYCLE,
        original_native_cap=1500, original_parent_cap=500,
        counters='ACTUAL_ANCESTRY_PLUS_ALL_PREDECESSOR_CHARGES_THEN_NEW_CHARGES',
        train_end_unix=plan['train_end_unix'], hard_end_unix=plan['hard_end_unix'],
        first_transition='NATURAL_COMPLETE_C100_ONLY', current_actor_mutation=False,
        activation_ready=False, authority='PROSPECTIVE_CPU_CONTRACT_ONLY',
        no_zero_reload_gap_claim=True, no_manual_admission_wait_planned=True,
        provider_ttl_seconds=600, parent_wait_seconds=0,
        novelty_claim='EXACT_CONTENT_DISJOINT_VARIANTS_NOT_NEW_SKILL_OR_BENCHMARK')


def chunk_registry(chunk, excluded_ids=(), excluded_prompts=(), excluded_questions=()):
    require(type(chunk) is int and 0 <= chunk < MAX_CHUNKS, 'bounded_chunk_ordinal')
    start = FIRST_NEW_CYCLE + chunk * CHUNK_CYCLES
    rows = []
    for cycle in range(start, start + CHUNK_CYCLES):
        for offset in range(6):
            parameter = 3 + (cycle * 7 + offset) % 17
            question, reference = original.prior.specification((cycle + offset) % 10, parameter)
            marker = 1000 + cycle * 6 + offset
            scalar = (cycle + offset) % 10 in (0, 2, 5, 7)
            question += (f' Finally, add {marker} to the numeric result.' if scalar
                else f' Finally, append the marker {marker} to the resulting list.')
            reference = '(' + reference + ') + ' + (str(marker) if scalar else '[' + str(marker) + ']')
            prompt = ('The only named argument is values, a list of integers with length at most 12. '
                + question + '\nReturn the requested bounded expression over values.')
            values = [[], [0], [-parameter-2, parameter+3],
                [parameter, -parameter, 1, 1, parameter+1, -1], [3, 0, -4, 12, 3, -4],
                [parameter+2, parameter+4, -parameter-5, 0, parameter+2, 2, 1]]
            split = 'TRAIN' if offset < 2 else 'HELD'
            task = dict(task_id=f'R124_CODE_{split}_C{cycle:05d}_E{offset+1}', split=split,
                cycle=cycle, slot=offset+1, family='code', cohort=SCHEMA, prompt=prompt,
                question=question, paired_task_key=f'C{cycle:05d}_E{offset+1}',
                prompt_sha256=original.digest(prompt), question_sha256=original.prior.question_hash(question),
                reference_expression=reference, tests=[dict(arguments=dict(values=sample),
                    expected=original.prior.gym.evaluate(reference, dict(values=sample))) for sample in values])
            task['content_sha256'] = original.digest(task)
            rows.append(task)
    for field, excluded in (('task_id', excluded_ids), ('prompt_sha256', excluded_prompts),
                            ('question_sha256', excluded_questions)):
        actual = [row[field] for row in rows]
        require(len(set(actual)) == len(actual) and not set(actual).intersection(excluded),
            'new_content_disjoint:' + field)
    return rows


def chunk_manifest(chunk, rows):
    require(len(rows) == CHUNK_CYCLES * 6 and all(row['cohort'] == SCHEMA for row in rows),
        'complete_fixed_chunk')
    start = FIRST_NEW_CYCLE + chunk * CHUNK_CYCLES
    require(sorted(set(row['cycle'] for row in rows)) == list(range(start, start + CHUNK_CYCLES)),
        'exact_chunk_cycle_order')
    return dict(schema=SCHEMA, chunk=chunk, first_cycle=start, last_cycle=start+CHUNK_CYCLES-1,
        registry_sha256=digest(rows), ordered_content_sha256=digest([row['content_sha256'] for row in rows]),
        train_tasks=sum(row['split'] == 'TRAIN' for row in rows),
        held_tasks=sum(row['split'] == 'HELD' for row in rows),
        native_slots=CHUNK_CYCLES*NATIVE_PER_CYCLE, parent_slots=CHUNK_CYCLES*PARENT_PER_CYCLE,
        raw_registry_node_only=True, training_only_parent_registry=True)


def settled_handoff(contract, boundary):
    require(contract['schema'] == SCHEMA, 'capacity_contract')
    require(boundary['terminal_status'] == 'COMPLETE' and boundary['completed_cycle'] == 100
        and boundary['latest_charged_cycle'] == 100 and boundary['native_inflight'] == 0,
        'no_partial_cycle_or_failed_native_resume')
    require(boundary['actor_exited'] is True and boundary['guard_exited'] is True
        and boundary['readonly_verified'] is True, 'actual_natural_release_and_weight_verification')
    for name in ('terminal', 'cycle_complete', 'context', 'ledger_manifest', 'after'):
        validate_reference(boundary[name])
    require(boundary['context_cycle'] == 100 and boundary['all_charges_preserved'] is True,
        'latest_actual_context_and_all_charges')
    for name in ('native_used', 'parent_used'):
        require(type(boundary[name]) is int and boundary[name] >= 0, 'actual_cumulative_charge_count')
    require(boundary['native_used'] <= contract['original_native_cap']
        and boundary['parent_used'] <= contract['original_parent_cap'], 'no_retrospective_cap_increase')
    for reference in boundary['pending_parent_references']:
        validate_reference(reference)
    return dict(first_cycle=FIRST_NEW_CYCLE, carried_native_used=boundary['native_used'],
        carried_parent_used=boundary['parent_used'],
        new_absolute_native_cap=boundary['native_used']+contract['prospective_native_increment'],
        new_absolute_parent_cap=boundary['parent_used']+contract['prospective_parent_increment'],
        context=deepcopy(boundary['context']), previous_ledger=deepcopy(boundary['ledger_manifest']),
        pending_parent_references=deepcopy(boundary['pending_parent_references']),
        parent_requests_reissued=0, native_calls_replayed=0,
        requires_fresh_exact_admission=True, shared_optimizer=False)
