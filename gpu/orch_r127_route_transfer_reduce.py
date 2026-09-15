"""CPU-only descriptive reduction of normalized fresh public route episodes."""

import hashlib
import json
import random
import re
import statistics
from collections import Counter


CONDITIONS = ('SEED', 'GUIDED_C2', 'GUIDED_C4', 'GUIDED_C6',
              'UNPARENTED_C2', 'UNPARENTED_C4', 'UNPARENTED_C6')
SECONDARY = ('task_completed', 'correct')
UNKNOWN = ('supplied_evidence_content_use', 'environment_feedback_reaction')
INTERPRETATION = (
    'OBSERVATIONAL_SYSTEMS_COMPARISON_NOT_ISOLATED_PARENTING_CONTENT_EFFECT'
)


def require(condition, message):
    if not condition:
        raise ValueError(message)


def document_sha256(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'),
                                     allow_nan=False).encode()).hexdigest()


def checked_hash(value, name):
    require(isinstance(value, str) and re.fullmatch('[0-9a-f]{64}', value) is not None,
            'missing_or_invalid_hash:' + name)
    return value


def count_or_missing(value, name):
    require(value is None or (type(value) is int and value >= 0), 'invalid_count:' + name)
    return value


def bool_or_missing(value, name):
    require(value is None or type(value) is bool, 'invalid_boolean:' + name)
    return None if value is None else int(value)


def complete_sum(values):
    return None if any(value is None for value in values) else sum(values)


def read_feedback(capture, final_messages):
    prefix = capture['messages']
    if final_messages[:len(prefix)] != prefix:
        return None
    suffix = final_messages[len(prefix):len(prefix) + 2]
    response = capture.get('response')
    if not isinstance(response, dict) or len(suffix) != 2:
        return None
    if suffix[0] != dict(role='assistant', content=response.get('raw')):
        return None
    feedback = suffix[1]
    if feedback.get('role') != 'user' or not isinstance(feedback.get('content'), str):
        return None
    return feedback['content']


def episode_metrics(record):
    """Use every capture, including rejected reads and missing responses."""
    captures = record['captures']
    commands = [capture['command'] for capture in captures]
    read_attempts = [command[len('READ EVENT '):] for command in commands
                     if isinstance(command, str) and command.startswith('READ EVENT ')]
    first_route = next((index for index, command in enumerate(commands)
                        if isinstance(command, str) and command.startswith('ROUTE ')), None)
    prefix = commands[:first_route] if first_route is not None else []
    reads_before_route = sum(isinstance(command, str) and command.startswith('READ EVENT ')
                            for command in prefix) if first_route is not None else None
    errors = [None if 'error' not in capture else int(capture['error'] is not None)
              for capture in captures]
    accepted_reads = [command[len('READ EVENT '):] for capture, command in zip(captures, commands)
                      if isinstance(command, str) and command.startswith('READ EVENT ')
                      and 'error' in capture and capture['error'] is None]
    accepted_read_count = len(accepted_reads) if all(value is not None for value in errors) else None
    if accepted_read_count is not None:
        require(record['reads'] == accepted_reads, 'accepted_read_trace_mismatch')
    feedback = [read_feedback(capture, record['messages']) for capture in captures
                if isinstance(capture['command'], str) and capture['command'].startswith('READ EVENT ')
                and 'error' in capture and capture['error'] is None]
    unavailable_reads = (None if accepted_read_count is None or any(value is None for value in feedback)
                         else sum(value == 'MEMORY UNAVAILABLE' for value in feedback))
    supplied_reads = None if unavailable_reads is None else accepted_read_count - unavailable_reads
    responses = [capture.get('response') for capture in captures]
    prompt_tokens, generated_tokens, text_tokens, truncated, terminal = [], [], [], [], []
    for response in responses:
        if response is None:
            prompt_tokens.append(None)
            generated_tokens.append(None)
            text_tokens.append(None)
            truncated.append(None)
            terminal.append(None)
            continue
        require(isinstance(response, dict), 'response_object_required')
        prompt_tokens.append(count_or_missing(response.get('prompt_tokens'), 'prompt_tokens'))
        token_ids = response.get('token_ids')
        require(token_ids is None or (isinstance(token_ids, list)
                and all(type(token) is int and token >= 0 for token in token_ids)), 'invalid_token_ids')
        generated_tokens.append(None if token_ids is None else len(token_ids))
        text_tokens.append(count_or_missing(response.get('generated_text_tokens'), 'generated_text_tokens'))
        truncated.append(bool_or_missing(response.get('truncated'), 'truncated'))
        terminal.append(bool_or_missing(response.get('terminal'), 'terminal'))
    reason = record.get('terminal_reason')
    require(reason in (None, 'reached_goal', 'dead_end', 'actor_call_cap', 'capture_error'),
            'unknown_canonical_terminal_reason')
    metrics = dict(
        action_calls=len(captures),
        read_attempts=len(read_attempts),
        repeated_read_attempts=sum(count - 1 for count in Counter(read_attempts).values()),
        accepted_reads=accepted_read_count,
        unavailable_memory_reads=unavailable_reads,
        supplied_memory_reads=supplied_reads,
        route_attempts=sum(isinstance(command, str) and command.startswith('ROUTE ') for command in commands),
        reads_before_first_route=reads_before_route,
        any_read_before_first_route=None if reads_before_route is None else int(reads_before_route > 0),
        rejected_action_calls=complete_sum(errors),
        missing_responses=sum(response is None for response in responses),
        prompt_tokens=complete_sum(prompt_tokens),
        generated_tokens_including_eos=complete_sum(generated_tokens),
        generated_text_tokens=complete_sum(text_tokens),
        truncated_responses=complete_sum(truncated),
        terminal_responses=complete_sum(terminal),
        task_completed=None if reason is None else int(reason in ('reached_goal', 'dead_end')),
        correct=bool_or_missing(record.get('correct'), 'correct'),
        supplied_evidence_content_use=None,
        environment_feedback_reaction=None,
    )
    coverage = {name: dict(observed=sum(value is not None for value in values),
                           missing=sum(value is None for value in values), total=len(values))
                for name, values in (('action_error', errors), ('prompt_tokens', prompt_tokens),
                                     ('generated_tokens_including_eos', generated_tokens),
                                     ('generated_text_tokens', text_tokens), ('truncated', truncated),
                                     ('terminal', terminal))}
    return dict(metrics=metrics, coverage=coverage, terminal_reason=reason)


def validate(plan, groups):
    """Validate content bindings, complete paired panels, and evaluation-only records."""
    require(isinstance(plan, dict) and isinstance(groups, dict), 'plan_and_groups_objects_required')
    require(set(plan.get('conditions', {})) == set(CONDITIONS) and set(groups) == set(CONDITIONS),
            'exact_seven_conditions_required')
    require(plan.get('evaluation_split') == 'fresh_public_held' and plan.get('prospective') is True,
            'prospective_fresh_public_held_only')
    source_hash = checked_hash(plan.get('source_store_sha256'), 'plan.source_store_sha256')
    require(type(plan.get('source_ready')) is bool, 'source_readiness_required')
    require(count_or_missing(plan.get('store_size'), 'store_size') is not None, 'source_store_size_required')
    initial_hash = checked_hash(plan.get('initial_state_sha256'), 'plan.initial_state_sha256')
    tasks = {}
    worlds = {}
    for task in plan.get('tasks', []):
        world_id, task_id = task.get('world_id'), task.get('task_id')
        require(isinstance(world_id, str) and bool(world_id) and isinstance(task_id, str)
                and bool(task_id), 'nonempty_world_and_task_ids_required')
        key = (world_id, task_id)
        require(key not in tasks, 'duplicate_planned_task')
        checked_hash(task.get('task_sha256'), 'plan.task_sha256')
        checked_hash(task.get('initial_prompt_sha256'), 'plan.initial_prompt_sha256')
        tasks[key] = task
        worlds.setdefault(world_id, []).append(key)
    require(bool(tasks) and all(len(keys) == 2 for keys in worlds.values()), 'two_tasks_per_world_required')
    require(len({task['task_sha256'] for task in tasks.values()}) == len(tasks),
            'duplicate_task_content_in_panel')
    if 'world_count' in plan:
        require(type(plan['world_count']) is int and plan['world_count'] == len(worlds), 'world_count_mismatch')
    indexed = {}
    for condition in CONDITIONS:
        checkpoint = plan['conditions'][condition]
        expected_hash = checked_hash(checkpoint.get('checkpoint_state_sha256'), 'plan.checkpoint_state_sha256')
        expected_cycle = 0 if condition == 'SEED' else int(condition[-1])
        require(type(checkpoint.get('cycle')) is int and checkpoint['cycle'] == expected_cycle,
                'fixed_checkpoint_cycle_required')
        require(count_or_missing(checkpoint.get('updates'), 'updates') is not None,
                'historical_update_dose_required')
        if condition == 'SEED':
            require(expected_hash == initial_hash and checkpoint['updates'] == 0,
                    'seed_is_fixed_initial_adapter_not_live_baseline')
        require(isinstance(groups[condition], list), 'episode_list_required')
        indexed[condition] = {}
        for record in groups[condition]:
            key = (record.get('world_id'), record.get('task_id'))
            require(key in tasks, 'unexpected_task')
            require(key not in indexed[condition], 'duplicate_episode')
            require(record.get('condition') == condition, 'condition_mismatch')
            require(record.get('trainingAllowed') is False and record.get('parent_messages') == [],
                    'evaluation_only_parent_free_required')
            for field, expected in (('task_sha256', tasks[key]['task_sha256']),
                                    ('initial_prompt_sha256', tasks[key]['initial_prompt_sha256']),
                                    ('source_store_sha256', source_hash),
                                    ('checkpoint_state_sha256', expected_hash)):
                require(checked_hash(record.get(field), field) == expected, field + '_mismatch')
            require(isinstance(record.get('task'), dict)
                    and document_sha256(record['task']) == record['task_sha256'], 'task_content_hash_mismatch')
            captures = record.get('captures')
            require(isinstance(captures, list) and 1 <= len(captures) <= 6,
                    'full_nonempty_canonical_capture_trace_required')
            require(type(record.get('actor_calls')) is int and record['actor_calls'] == len(captures),
                    'actor_call_trace_count_mismatch')
            require(isinstance(record.get('reads'), list) and isinstance(record.get('routes'), list)
                    and isinstance(record.get('messages'), list), 'canonical_episode_lists_required')
            for index, capture in enumerate(captures):
                require(isinstance(capture, dict) and isinstance(capture.get('messages'), list)
                        and bool(capture['messages']), 'capture_messages_required')
                require('command' in capture and (capture['command'] is None
                        or isinstance(capture['command'], str)), 'capture_command_required')
                require(not capture.get('parent_messages'), 'capture_parent_present')
                require('turn' not in capture or capture['turn'] == index, 'capture_order_mismatch')
            require(document_sha256(captures[0]['messages']) == record['initial_prompt_sha256'],
                    'initial_prompt_content_hash_mismatch')
            indexed[condition][key] = record
        require(set(indexed[condition]) == set(tasks), 'missing_episode_panel')
    return indexed, worlds


def quantile(values, probability):
    ordered = sorted(values)
    position = (len(ordered) - 1) * probability
    lower = int(position)
    upper = min(lower + 1, len(ordered) - 1)
    return ordered[lower] + (ordered[upper] - ordered[lower]) * (position - lower)


def paired_summary(differences, total_worlds, bootstrap_samples, seed):
    values = list(differences.values())
    result = dict(mean_difference=statistics.mean(values) if values else None,
                  paired_worlds=len(values), excluded_worlds=total_worlds - len(values),
                  world_differences=differences, ci95=None, standard_error=None,
                  uncertainty_unit='world', bootstrap_samples=bootstrap_samples, seed=seed)
    if len(values) < 2:
        result['uncertainty_status'] = 'INSUFFICIENT_PAIRED_WORLDS'
        return result
    result['standard_error'] = statistics.stdev(values) / len(values) ** 0.5
    generator = random.Random(seed)
    means = [statistics.mean(generator.choices(values, k=len(values))) for _ in range(bootstrap_samples)]
    result['ci95'] = [quantile(means, 0.025), quantile(means, 0.975)]
    result['uncertainty_status'] = 'DESCRIPTIVE_PAIRED_WORLD_PERCENTILE_BOOTSTRAP'
    return result


def compare(plan, groups, *, bootstrap_samples=2000, seed=0):
    """Compare condition -> normalized episode lists; perform no filesystem or model calls."""
    require(type(bootstrap_samples) is int and bootstrap_samples >= 100, 'bootstrap_samples_at_least_100')
    require(type(seed) is int, 'integer_bootstrap_seed_required')
    indexed, worlds = validate(plan, groups)
    world_ids = sorted(worlds)
    episodes, world_metrics, conditions = {}, {}, {}
    for condition in CONDITIONS:
        episodes[condition] = {key: episode_metrics(record) for key, record in indexed[condition].items()}
        metric_names = tuple(next(iter(episodes[condition].values()))['metrics'])
        world_metrics[condition] = {}
        summaries = {}
        for name in metric_names:
            per_world = {}
            for world_id in world_ids:
                values = [episodes[condition][key]['metrics'][name] for key in worlds[world_id]]
                per_world[world_id] = None if any(value is None for value in values) else statistics.mean(values)
            world_metrics[condition][name] = per_world
            observed = [value for value in per_world.values() if value is not None]
            episode_values = [entry['metrics'][name] for entry in episodes[condition].values()]
            summaries[name] = dict(mean=statistics.mean(observed) if observed else None,
                observed_episodes=sum(value is not None for value in episode_values),
                missing_episodes=sum(value is None for value in episode_values),
                complete_worlds=len(observed), excluded_worlds=len(worlds) - len(observed),
                role='SECONDARY' if name in SECONDARY else 'DESCRIPTIVE_BEHAVIOR_PROXY',
                status='UNKNOWN' if name in UNKNOWN else ('OBSERVED' if observed else 'UNAVAILABLE'))
        conditions[condition] = dict(checkpoint=dict(plan['conditions'][condition]),
            episodes=len(episodes[condition]), worlds=len(worlds), metrics=summaries,
            per_world=world_metrics[condition],
            terminal_reasons=dict(Counter(entry['terminal_reason'] or 'MISSING'
                                         for entry in episodes[condition].values())))
    contrasts = [(f'GUIDED_C{cycle}', f'UNPARENTED_C{cycle}') for cycle in (2, 4, 6)]
    contrasts += [(condition, 'SEED') for condition in CONDITIONS if condition != 'SEED']
    comparisons = {}
    for left, right in contrasts:
        metrics = {}
        for name in metric_names:
            differences = {world_id: world_metrics[left][name][world_id] - world_metrics[right][name][world_id]
                           for world_id in world_ids if world_metrics[left][name][world_id] is not None
                           and world_metrics[right][name][world_id] is not None}
            metrics[name] = paired_summary(differences, len(worlds), bootstrap_samples, seed)
        comparisons[left + '_minus_' + right] = dict(left=left, right=right, metrics=metrics)
    rows = [dict(condition=condition, world_id=key[0], task_id=key[1], **episodes[condition][key])
            for condition in CONDITIONS for key in sorted(episodes[condition])]
    return dict(schema='R127_ROUTE_TRANSFER_REDUCTION_V1', interpretation=INTERPRETATION,
        causal_claim=False, generalization='FRESH_WORLD_SAME_FAMILY_NOT_NEW_TASK_FAMILY',
        proxy_boundary='VALIDITY_REPETITION_EVIDENCE_ACCESS_NOT_LATENT_METACOGNITION',
        unknown_reasons=dict(supplied_evidence_content_use='Reading does not establish semantic use of supplied evidence.',
            environment_feedback_reaction='UNKNOWN: canonical episodes end on invalid commands; no recovery opportunity.'),
        uncertainty_boundary='Conditional on fixed checkpoints/store; not independent training-seed uncertainty. '
            'Pointwise descriptive intervals, not multiplicity-corrected tests. No across-checkpoint pooling.',
        seed_reference='ONE_FIXED_INITIAL_EVALUATION_CONDITION_REUSED_NOT_EXTRA_LIVE_BASELINE',
        plan_sha256=document_sha256(plan), normalized_groups_sha256=document_sha256(groups),
        source_store_sha256=plan['source_store_sha256'], world_count=len(worlds),
        source_ready=plan['source_ready'], store_size=plan['store_size'],
        source_boundary='Shared child-written accepted event text; failed source records stay unavailable. '
            'No world filtering. Source readiness is not evidence completeness; unavailable memory is not a learning effect.',
        tasks_per_world=2, conditions=conditions, comparisons=comparisons, episode_metrics=rows)
