"""Frozen TRAIN-only richness treatments; raw outputs never imply admission."""

from organism_v6 import orch_math_rich as original
from organism_v6 import orch_rich_intensity as prior


CONDITIONS = ('original', 'light', 'hierarchical')
MAX_NEW_TOKENS = 8192
CONTEXT_LIMIT = 16384
MAX_CALLS = 2048
MAX_SECONDS = 12 * 3600
HOST_SHA256 = '3e10ebcb89f013079c1e088fa82820188b1a805b879ebb85a7ffeb689e7b86e9'
TASKS_SHA = prior.TASKS_SHA
BUNDLE_SHA = prior.BUNDLE_SHA
LIGHT = prior.LIGHT
SECOND_PASS = (
    'The assistant response above is your own first pass on the given task, '
    'not an external answer or a verified solution. Evaluate it hierarchically: '
    'identify the most consequential uncertainty, examine the relevant '
    'reasoning branches, and check your provisional conclusion against the '
    'given quantities. Pursue the useful next question raised by that check. '
    'Retain or revise your conclusion with task-specific reasons. Do not '
    'invent observations, manufacture disagreement, repeat, or pad. Stop '
    'when useful reasoning is complete. Finish with a separate line FINAL: '
    'followed by just the numeric answer.'
)


def allocation(index):
    if type(index) is not int or index not in range(6):
        raise ValueError('only_owned_node3_physical_0_to_5')
    return CONDITIONS[index // 2], index % 2


def context_check(prompt_tokens, cap=MAX_NEW_TOKENS):
    if type(cap) is not int or cap != MAX_NEW_TOKENS:
        raise ValueError('fixed_8192_new_token_cap_required')
    if not 0 < prompt_tokens <= CONTEXT_LIMIT - cap:
        raise ValueError('prompt_plus_completion_exceeds_16384_no_truncation')


def model_config_check(config):
    if (config.get('model_type') != 'qwen2'
            or config.get('max_position_embeddings', 0) < CONTEXT_LIMIT
            or config.get('architectures') != ['Qwen2ForCausalLM']):
        raise ValueError('local_frozen_qwen_config_context_mismatch')


def prompt(task, condition, kind, previous=None):
    if condition not in CONDITIONS:
        raise ValueError('unknown_condition')
    neutral = [dict(role='user', content=task['question'])]
    guidance = original.RICH_GUIDANCE if condition == 'original' else LIGHT
    if kind == 'rich':
        return [dict(role='system', content=guidance)] + neutral, neutral
    if previous is None:
        raise ValueError('own_first_pass_required')
    if kind == 'self_evaluation' and condition == 'hierarchical':
        return ([dict(role='system', content=LIGHT)] + neutral
                + [dict(role='assistant', content=previous),
                   dict(role='user', content=SECOND_PASS)]), neutral
    if kind == 'new_record' and condition != 'hierarchical':
        messages, student = original.prompt(task, 'record', previous)
        return messages, student
    raise ValueError('unfrozen_treatment_call')


def followup(condition, outcome_pass):
    if condition not in CONDITIONS:
        raise ValueError('unknown_condition')
    if condition == 'hierarchical':
        return 'self_evaluation'
    return 'new_record' if outcome_pass else None


def capture(task, kind, result, student):
    row = original.capture(task, kind, result, student)
    row.update(candidate=False, admitted=False, fit_ready=False,
               trainingAllowed=False, semantic_status='UNREVIEWED',
               legacy_150_400_contract_pass=row['token_contract_pass'],
               raw_supply_only=True, prospective_context_limit=CONTEXT_LIMIT)
    return row


def protocol():
    return dict(schema='RICH_HOT_NODE3_V1', conditions=list(CONDITIONS),
                tasks_sha256=TASKS_SHA, bundle_sha256=BUNDLE_SHA,
                denominator_per_condition=256, paired_shards_per_condition=2,
                max_new_tokens=MAX_NEW_TOKENS, context_limit=CONTEXT_LIMIT,
                maximum_calls=MAX_CALLS, maximum_seconds=MAX_SECONDS,
                assigned_gpu_hours_ceiling=72, maximum_this_batch_calls=1536,
                original_prompt=original.RICH_GUIDANCE, light_prompt=LIGHT,
                hierarchical_first_pass=LIGHT, second_pass=SECOND_PASS,
                followups={'original': 'own_record_only_if_original_oracle_pass',
                           'light': 'own_record_only_if_original_oracle_pass',
                           'hierarchical': 'own_second_pass_regardless_of_oracle'},
                followup_context_overflow='record_failure_no_truncation_no_retry',
                continuation='requires_new_prospective_freeze_same_global_budget_and_clock',
                no_automatic_budget_reset=True, no_semantic_review_before_calls=True,
                no_held_tasks=True, fits=0, updates=0, automatic_training=False,
                claim='TRAIN_DEV_RAW_SUPPLY_NOT_LEARNING_OR_TRANSFER')
