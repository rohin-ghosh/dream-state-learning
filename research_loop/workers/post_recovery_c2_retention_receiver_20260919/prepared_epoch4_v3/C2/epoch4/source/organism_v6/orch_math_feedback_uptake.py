"""Prospective two-round TRAIN interaction; no model calls or quality admission."""

import json
import re

from organism_v6 import orch_math_pipeline_l2 as source


SCHEMA = 'ORCH_MATH_FEEDBACK_UPTAKE_V1'
CYCLES = 2
EPISODES = 2
HELD_PER_CYCLE = 8
RETENTION = 48
NATIVE_CAP = CYCLES * (EPISODES * 3 + HELD_PER_CYCLE) + RETENTION
PARENT_CAP = CYCLES * 2
WALL_SECONDS = 90 * 60
GPU_HOURS = 1.5
STRONG = 'openai/openai/gpt-6-astra'
GENERATION = source.GENERATION
CONTEXT = source.CONTEXT
PURPOSES = ('experience', 'check', 'revision')
digest = source.digest
text_sha = source.text_sha
WAKE = source.WAKE
PARENTING = dict(style='training-wheels', horizon='long', tone='supportive', strength=STRONG)
ROUND_INSTRUCTIONS = {
    1: ('Guide a concrete child-performed check of each recorded attempt. Ask the child to state '
        'what would conflict with its conclusion, perform the check, and let an actual conflict '
        'interrupt that conclusion. Do not supply the answer or a worked solution. A check may '
        'fail; do not certify it merely because it is described.'),
    2: ('Respond to the actual child check, including any repetition, contradiction, missing check '
        'or error. Guide a fresh child revision and own reflection grounded in that record. '
        'Ask which evidence changed or failed to change the conclusion and a future usable check. '
        'Do not supply an answer, pretend feedback was followed, or endorse an incorrect attempt.'),
}
CHILD_INSTRUCTIONS = {
    'check': ('Use the recorded TRAIN history and guidance to perform a check yourself. State '
        'what you expect, calculate or examine it, and say whether it conflicts with your '
        'conclusion. If it conflicts, stop and acknowledge the unresolved conclusion. Do not '
        'claim an unperformed check succeeded. Finish with FINAL: numeric answer if justified.'),
    'revision': ('Revise in your own voice using your actual attempt, check, and new guidance. '
        'This is also your own reflection: explain what you tried, what you rejected or retained '
        'and why, what remains unresolved, and a usable next-time check. Incorrect prior '
        'utterances are negative examples, not facts. Do not copy teacher lessons or invent '
        'observations. Finish with FINAL: numeric answer if justified.'),
}


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def record(task, purpose, response=None, error=None):
    require(task['split'] == 'TRAIN' and purpose in PURPOSES, 'train_source_required')
    require((response is None) != (error is None), 'exactly_response_or_error')
    if response is not None:
        require(isinstance(response['raw'], str), 'raw_child_text_required')
        require(response.get('input_truncated') is False, 'no_silent_input_truncation')
        outcome = source.judge(task, response)
    else:
        outcome = dict(status='NO_RESPONSE', correct=False)
    return dict(task_id=task['id'], purpose=purpose, response=response, error=error,
        outcome=outcome, target_sha256=text_sha(response['raw']) if response else None)


def public_record(call):
    return dict(purpose=call['purpose'], trace=call['response']['raw'] if call['response'] else '',
        outcome=dict(call['outcome']), native_error=call['error'] is not None,
        source_record_sha256=digest(call))


def verify_record(task, call):
    require(call['task_id'] == task['id'], 'source_task_mismatch')
    require(call == record(task, call['purpose'], call['response'], call['error']), 'source_record_mismatch')


def parent_payload(tasks, records, cycle, round_number, previous=()):
    require(1 <= cycle <= CYCLES and round_number in (1, 2), 'cycle_or_round')
    expected = PURPOSES[:round_number]
    require(len(tasks) == EPISODES and len({task['id'] for task in tasks}) == EPISODES, 'two_episodes')
    episodes = []
    for task in tasks:
        require(task['split'] == 'TRAIN', 'parent_train_only')
        history = records[task['id']]
        require(tuple(call['purpose'] for call in history) == expected, 'actual_round_history_required')
        for call in history:
            verify_record(task, call)
        episodes.append(dict(task_id=task['id'], question=task['question'],
            records=[public_record(call) for call in history]))
    payload = dict(schema=SCHEMA, cycle=cycle, round=round_number, episodes=episodes,
        previous_own_reflections=list(previous), instruction=ROUND_INSTRUCTIONS[round_number],
        parenting=dict(PARENTING), child_context=CONTEXT, child_generation_budget=GENERATION)
    validate_parent_payload(payload)
    return payload


def validate_parent_payload(payload):
    require(set(payload) == {'schema', 'cycle', 'round', 'episodes', 'previous_own_reflections',
        'instruction', 'parenting', 'child_context', 'child_generation_budget'}, 'parent_schema')
    require(payload['schema'] == SCHEMA and 1 <= payload['cycle'] <= CYCLES, 'parent_version')
    require(payload['round'] in (1, 2), 'parent_round')
    require(payload['instruction'] == ROUND_INSTRUCTIONS[payload['round']], 'frozen_parent_instruction')
    require(payload['parenting'] == PARENTING, 'strong_parent_style_binding')
    require(payload['child_context'] == CONTEXT and payload['child_generation_budget'] == GENERATION, 'caps')
    require(len(payload['episodes']) == EPISODES, 'parent_episode_count')
    identifiers = []
    for episode in payload['episodes']:
        require(set(episode) == {'task_id', 'question', 'records'}, 'public_episode_schema')
        require('_TRAIN_' in episode['task_id'], 'parent_train_id')
        identifiers.append(episode['task_id'])
        require([call['purpose'] for call in episode['records']] == list(PURPOSES[:payload['round']]), 'parent_history')
        for call in episode['records']:
            require(set(call) == {'purpose', 'trace', 'outcome', 'native_error', 'source_record_sha256'}, 'public_record_schema')
            require(set(call['outcome']) <= {'status', 'correct', 'parsed_answer', 'final_parseable', 'terminal', 'truncated'}, 'outcome_schema')
            require(call['outcome']['status'] in ('CORRECT', 'INCORRECT', 'NO_RESPONSE'), 'outcome_status')
            require(call['outcome']['correct'] == (call['outcome']['status'] == 'CORRECT'), 'outcome_consistency')
            require(re.fullmatch('[a-f0-9]{64}', call['source_record_sha256']) is not None, 'source_hash')
    require(len(set(identifiers)) == EPISODES, 'duplicate_parent_episode')
    require(len(payload['previous_own_reflections']) <= EPISODES, 'previous_history_bound')
    for previous in payload['previous_own_reflections']:
        require(set(previous) == {'task_id', 'trace', 'source_record_sha256'}, 'previous_schema')
        require('_TRAIN_' in previous['task_id'], 'previous_train_only')
        require(re.fullmatch('[a-f0-9]{64}', previous['source_record_sha256']) is not None, 'previous_source_hash')
    require(not re.search(r'_HELD_|reference_answer|sealed_score|retention_score|/tmp/|/localhome/|api[_-]?key|PRIVATE KEY',
        json.dumps(payload), re.I), 'parent_visibility_violation')


def validate_plan(plan, tasks):
    require(set(plan) == {'guidance', 'order', 'episode_guidance', 'rationale'}, 'parent_plan_schema')
    identifiers = [task['id'] for task in tasks]
    require(len(plan['order']) == EPISODES and set(plan['order']) == set(identifiers), 'complete_parent_order')
    require(set(plan['episode_guidance']) == set(identifiers), 'both_episodes_guided')
    require(all(isinstance(value, str) for value in
        [plan['guidance'], plan['rationale'], *plan['episode_guidance'].values()]), 'parent_text_types')


def child_messages(task, history, purpose, plan=None):
    require(purpose in PURPOSES and task['split'] == 'TRAIN', 'child_purpose')
    require([call['purpose'] for call in history] == list(PURPOSES[:PURPOSES.index(purpose)]), 'child_history_order')
    if purpose == 'experience':
        require(plan is None, 'original_parent_free')
        return [dict(role='system', content=WAKE), dict(role='user', content=task['question'])]
    require(plan is not None, 'real_parent_required')
    teacher = plan['guidance'] + '\n' + plan['episode_guidance'][task['id']]
    messages = [dict(role='system', content=CHILD_INSTRUCTIONS[purpose] + '\nPRIVATE PARENT GUIDANCE:\n' + teacher),
        dict(role='user', content=task['question'])]
    for call in history:
        if call['response'] and call['response']['raw']:
            messages.append(dict(role='assistant', content=call['response']['raw']))
        messages.append(dict(role='user', content='RECORDED ' + call['purpose'].upper()
            + ' FINAL-ANSWER CHECK ONLY: ' + json.dumps(call['outcome'], sort_keys=True)
            + '. This does not verify intermediate reasoning or claimed checks.'))
    messages.append(dict(role='user', content=CHILD_INSTRUCTIONS[purpose]))
    return messages


def sleep_rows(task, history, teacher_rounds):
    require([call['purpose'] for call in history] == list(PURPOSES), 'all_rounds_recorded')
    require(all(call['response'] and call['response']['raw'] for call in history[1:]), 'actual_check_and_reflection_required')
    require(len(teacher_rounds) == 2, 'causal_teacher_rounds_required')
    rows = []
    for position, call in enumerate(history):
        verify_record(task, call)
        if not call['response'] or not call['response']['raw']:
            continue
        target = call['response']['raw']
        require(text_sha(target) == call['target_sha256'], 'source_target_mismatch')
        for round_index, teachers in enumerate(teacher_rounds[:position]):
            pre_parent_texts = [earlier['response']['raw'] for earlier in history[:round_index + 1] if earlier['response']]
            for teacher in teachers:
                fragments = [teacher] + [fragment for fragment in re.split(r'(?<=[.!?])\s+|\n+', teacher) if len(fragment.split()) >= 8]
                for fragment in fragments:
                    child_origin = any(fragment in earlier for earlier in pre_parent_texts)
                    require(not fragment or fragment not in target or child_origin, 'teacher_text_in_target')
        outcome = call['outcome']['status']
        context = ('SOURCED HISTORICAL CHILD UTTERANCE, NOT an endorsed solution. Task: ' + task['question']
            + '\nOriginal recorded outcome: ' + history[0]['outcome']['status']
            + '\nThis utterance kind: ' + call['purpose'] + '; final-answer outcome: ' + outcome
            + '. INCORRECT utterances are NEGATIVE EXAMPLES of a recorded past attempt, never correct solutions. '
            'Only the final numeric answer was checked; reasoning and reflection remain unverified. '
            'Reproduce the attributed historical utterance, not a teacher lesson.')
        rows.append(dict(episode_id=task['id'], kind=call['purpose'], outcome=outcome,
            original_outcome=history[0]['outcome']['status'], student_prefix=[dict(role='user', content=context)],
            target=target, target_sha256=text_sha(target), source_record_sha256=digest(call),
            own_reflection=call['purpose'] == 'revision', teacher_in_prefix=False,
            observed_fact_endorsement=False, semantic_admission='NOT_USED',
            objective='outcome_conditioned_historical_SFT_not_unlikelihood'))
    require(len(rows) >= 2, 'no_fabricated_missing_targets')
    return rows


def budget():
    return dict(cycles=CYCLES, episodes_per_cycle=EPISODES, original_calls=4, check_calls=4,
        own_revision_reflection_calls=4, fresh_held_calls=16, terminal_retention_calls=RETENTION,
        native_calls=NATIVE_CAP, parent_calls=PARENT_CAP, retries=0, gpus=1,
        max_wall_seconds=WALL_SECONDS, max_gpu_hours=GPU_HOURS)


def generation_budget(purpose, prompt_tokens, teacher_tokens=0):
    require(purpose in PURPOSES, 'generation_purpose')
    require(type(prompt_tokens) is int and 0 < prompt_tokens < CONTEXT, 'full_context_required')
    require(type(teacher_tokens) is int and 0 <= teacher_tokens <= 1024, 'parent_guidance_context_bound')
    reserve = 6144 if purpose == 'check' else 0
    cap = min(GENERATION, CONTEXT - prompt_tokens - reserve)
    require(cap > 0, 'full_two_round_context_does_not_fit_no_cropping')
    return dict(requested_generation_cap=GENERATION, effective_generation_cap=cap,
        reserved_for_revision=reserve, input_truncated=False)


def make_cohort(manifests):
    scopes = {'L1_ALL_SOURCE', 'L1_READOUT', 'L2_ALL_SOURCE', 'L2_READOUT', 'RETENTION'}
    require({manifest['scope'] for manifest in manifests} == scopes, 'complete_exclusion_registry_required')
    excluded_ids, excluded_questions = set(), set()
    for manifest in manifests:
        require(manifest['complete_pool'] is True, 'whole_pool_not_success_subset')
        require(manifest['ids'] and manifest['question_sha256'], 'nonempty_source_exclusions')
        excluded_ids.update(manifest['ids'])
        excluded_questions.update(manifest['question_sha256'])
    seen_ids, seen_questions = set(excluded_ids), set(excluded_questions)
    train, held = [], []
    for cycle in range(1, CYCLES + 1):
        for split, count, destination in (('TRAIN', EPISODES, train), ('HELD', HELD_PER_CYCLE, held)):
            group = []
            for position in range(count):
                for nonce in range(1000):
                    task = source.make_task('FEEDBACK_UPTAKE_' + split, cycle, position + nonce * 1000)
                    task['split'] = split
                    if task['id'] not in seen_ids and task['question_sha256'] not in seen_questions:
                        seen_ids.add(task['id'])
                        seen_questions.add(task['question_sha256'])
                        group.append(task)
                        break
                else:
                    raise ValueError('fresh_gym_pool_exhausted_no_substitution')
            destination.append(group)
    return dict(schema=SCHEMA, train=train, held=held, retention='EXISTING_FROZEN_48_MANIFEST_REQUIRED',
        source_manifests_sha256=digest(manifests), excluded_ids=sorted(excluded_ids),
        excluded_question_sha256=sorted(excluded_questions), c0_calls=0)
