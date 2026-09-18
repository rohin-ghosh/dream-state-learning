"""Two sequential episodes followed by actual-causal-prefix LoRA replay."""

from copy import deepcopy
import json
import re

from organism_v6 import orch_math_feedback_uptake as history
from organism_v6 import orch_r107_parented_replay as replay


SCHEMA = 'ORCH_R108_GUIDED_V1'
CYCLES = 2
EPISODES = 2
STRONG = history.STRONG
CONTEXT = history.CONTEXT
INTERVENTIONS = ('perception', 'persistence', 'metacognition', 'curiosity',
    'goal_regulation', 'meta_goal_regulation', 'reflection', 'action_steering',
    'affective_value_regulation')
PARENTING = dict(style='training-wheels', horizon='long', tone='supportive', strength=STRONG)
PARENT_INSTRUCTION = (
    'Parent the failure in this actual child attempt, not the answer. Choose one intervention '
    'class: perception, persistence, metacognition, curiosity, goal_regulation, '
    'meta_goal_regulation, reflection, action_steering, affective_value_regulation. '
    'Help the child decide where effort belongs, what it missed, whether its strategy should '
    'change, or when enough thinking has occurred and action is appropriate. Do not prescribe '
    'the solution, answer, calculation, or a compulsory branch count. Ask for multi-angle '
    'perception rather than repeated prose. Return only a JSON object with intervention_class, '
    'guidance and rationale. Neither a changed answer nor more text proves learning.')
WAKE = (
    'Work on the task in your own words. You may keep thinking beyond the first plausible '
    'answer when there is a reason: notice what the evidence does and does not establish, '
    'and decide whether your current approach deserves more effort or a change. Do not '
    'repeat yourself or invent observations. Stop when the evidence is sufficient. '
    'Finish with a standalone FINAL: numeric answer when justified.')
REFLECT = (
    'Reflect on your actual attempt and continuation. Look at the same experience from '
    'different useful angles: what you noticed, missed, or changed, and what evidence made '
    'that change appropriate. Distinguish observations from speculation. Keep what could '
    'help on another task; do not repeat the solution, copy the parent, invent a realization, '
    'or add template slots. It is acceptable to report that the intervention did not help.')
require = history.require
digest = history.digest
text_sha = history.text_sha


def validate_task(task):
    require(task['split'] == 'TRAIN' and '_TRAIN_' in task['id'], 'train_only_task')
    require(isinstance(task['question'], str) and task['question'], 'task_question')


def validate_parent_payload(payload):
    require(set(payload) == {'schema', 'cycle', 'episode', 'task', 'child_state',
        'previous_own_reflections', 'instruction', 'parenting'}, 'parent_schema')
    require(payload['schema'] == SCHEMA and type(payload['cycle']) is int
        and 1 <= payload['cycle'] <= CYCLES and type(payload['episode']) is int
        and 1 <= payload['episode'] <= EPISODES, 'parent_cycle_episode')
    require(set(payload['task']) == {'id', 'question'}, 'public_task_schema')
    validate_task(dict(payload['task'], split='TRAIN'))
    state = payload['child_state']
    require(set(state) == {'adapter_sha256', 'call_sha256', 'trace', 'outcome'}, 'public_child_schema')
    require(all(re.fullmatch('[a-f0-9]{64}', state[key]) for key in
        ('adapter_sha256', 'call_sha256')), 'actual_child_state_hashes')
    require(isinstance(state['trace'], str), 'actual_child_trace')
    require(state['outcome'] in ('CORRECT', 'INCORRECT', 'NO_RESPONSE'), 'outcome_tag')
    require(payload['instruction'] == PARENT_INSTRUCTION and payload['parenting'] == PARENTING,
        'parent_instruction_policy_binding')
    require(len(payload['previous_own_reflections']) <= EPISODES, 'bounded_previous_own_records')
    for previous in payload['previous_own_reflections']:
        require(set(previous) == {'task_id', 'trace', 'source_record_sha256'}, 'previous_own_schema')
        require('_TRAIN_' in previous['task_id'] and isinstance(previous['trace'], str)
            and re.fullmatch('[a-f0-9]{64}', previous['source_record_sha256']), 'own_train_reflection')
    require(not re.search(r'_HELD_|reference_answer|sealed_score|retention_score|/localhome/|'
        r'/tmp/|api[_-]?key|PRIVATE KEY', json.dumps(payload), re.I), 'parent_visibility_violation')


def parent_payload(task, original, adapter_sha256, cycle, episode, previous=()):
    validate_task(task)
    require(original['task_id'] == task['id'] and original['purpose'] == 'experience', 'actual_original')
    payload = dict(schema=SCHEMA, cycle=cycle, episode=episode,
        task=dict(id=task['id'], question=task['question']),
        child_state=dict(adapter_sha256=adapter_sha256, call_sha256=digest(original),
            trace=original['response']['raw'], outcome=original['outcome']['status']),
        previous_own_reflections=deepcopy(list(previous)), instruction=PARENT_INSTRUCTION,
        parenting=deepcopy(PARENTING))
    validate_parent_payload(payload)
    return payload


def validate_plan(plan, tasks):
    require(len(tasks) == 1, 'single_sequential_episode_parent')
    validate_task(tasks[0])
    require(set(plan) == {'intervention_class', 'guidance', 'rationale'}, 'intervention_plan_schema')
    require(plan['intervention_class'] in INTERVENTIONS, 'intervention_class')
    require(all(isinstance(plan[key], str) and plan[key].strip()
        for key in ('guidance', 'rationale')), 'actual_intervention_text')


def messages(task, purpose, records=(), plan=None, previous=()):
    validate_task(task)
    require(purpose in ('experience', 'check', 'revision'), 'child_purpose')
    result = [dict(role='system', content=WAKE), dict(role='user', content=task['question'])]
    if previous:
        result[0]['content'] += '\nYOUR EARLIER TRAIN REFLECTIONS (unverified):\n' + json.dumps(list(previous))
    if purpose == 'experience':
        require(not records and plan is None, 'original_without_parent')
        return result
    validate_plan(plan, [task])
    require([record['purpose'] for record in records] ==
        (['experience'] if purpose == 'check' else ['experience', 'check']), 'sequential_episode_history')
    for record in records:
        history.verify_record(task, record)
        result.append(dict(role='assistant', content=record['response']['raw']))
        result.append(dict(role='user', content='Final-answer-only TRAIN outcome: '
            + record['outcome']['status'] + '. Intermediate reasoning is not verified.'))
    result.append(dict(role='user', content='PARENT INTERVENTION (' + plan['intervention_class']
        + '): ' + plan['guidance'] + '\n' + (REFLECT if purpose == 'revision' else
        'Continue yourself. Decide whether the intervention changes what you do and why; '
        'do not copy it or pretend it helped. Finish with FINAL: numeric answer if justified.')))
    return result


def replay_rows(task, records, plan):
    validate_plan(plan, [task])
    require([record['purpose'] for record in records] == ['experience', 'check', 'revision'],
        'complete_sequential_episode')
    rows = []
    for position, record in enumerate(records):
        history.verify_record(task, record)
        response = record['response']
        require(response and response['messages'] and response['input_truncated'] is False,
            'uncropped_native_source')
        require(type(response['terminal']) is bool and type(response['truncated']) is bool
            and not (response['terminal'] and response['truncated']), 'completion_flags')
        target = response['raw']
        if position:
            teacher = plan['guidance']
            fragments = [teacher] + [fragment for fragment in re.split(r'(?<=[.!?])\s+|\n+', teacher)
                if len(fragment.split()) >= 8]
            require(all(not fragment or fragment not in target or fragment in records[0]['response']['raw']
                for fragment in fragments), 'teacher_text_in_target')
        rows.append(dict(episode_id=task['id'], kind=record['purpose'], outcome=record['outcome']['status'],
            target=target, target_sha256=text_sha(target), source_record_sha256=digest(record),
            student_prefix=deepcopy(response['messages']), source_prompt_sha256=digest(response['messages']),
            source_prompt_tokens=response['prompt_tokens'], source_generated_token_ids=list(response['token_ids']),
            append_eos=response['terminal'], continuation_only=not response['terminal'],
            replay_mode=replay.MODE, teacher_in_prefix=position > 0, own_reflection=position == 2,
            objective='actual_child_continuation_SFT_not_unlikelihood', observed_fact_endorsement=False,
            source_outcome_is_metadata_only=True, r108_schema=SCHEMA))
    return rows


def intervention_triple(task, records, plan, adapter_sha256, parent_receipt):
    validate_plan(plan, [task])
    require([record['purpose'] for record in records] == ['experience', 'check', 'revision'],
        'completed_intervention_triple')
    for record in records:
        history.verify_record(task, record)
    return dict(schema=SCHEMA, task_id=task['id'], child_adapter_sha256=adapter_sha256,
        before_record_sha256=digest(records[0]), parent_plan=deepcopy(plan),
        parent_receipt=deepcopy(parent_receipt), after_record_sha256=digest(records[1]),
        reflection_record_sha256=digest(records[2]),
        generated_tokens=[len(record['response']['token_ids']) for record in records],
        functional_change='UNASSESSED', helpfulness='UNASSESSED',
        outcome_change=[record['outcome']['status'] for record in records[:2]],
        outcome_change_is_not_functional_change=True)
