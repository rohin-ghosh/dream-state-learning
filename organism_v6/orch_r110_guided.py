"""R110: score-blind behavioral guidance and loss on actual child outputs.

Presleep uses episode='presleep' and the last TRAIN task as its queue anchor.
records accepts a task-id mapping or a flat sequence of the cycle's six records.
For parent/continuation calls the mapping also contains presleep_initial.
encode_presleep_record returns a replay row, not tokenized data; the unchanged
native causal-prefix encoder masks every prefix token. No ingestion occurs here.
"""

from copy import deepcopy
import hashlib
import json
from pathlib import Path
import re

from organism_v6 import orch_math_feedback_uptake as history
from organism_v6 import orch_r107_parented_replay as replay
from organism_v6 import orch_r108_guided as previous_policy


SCHEMA = 'ORCH_R110_GUIDED_V1'
CYCLES = 64
EPISODES = 2
PARENTS_PER_CYCLE = 3
PARENT_CAP = CYCLES * PARENTS_PER_CYCLE
WALL_SECONDS = 8 * 60 * 60
WALL_END_UNIX = 1789491720.0
COLLECTION_CALLS_PER_CYCLE = 8
READOUT_CALLS_PER_CYCLE = 72
NATIVE_CALLS_PER_CYCLE_CAP = 80
NATIVE_CAP = CYCLES * NATIVE_CALLS_PER_CYCLE_CAP
MAX_PREVIOUS = PARENT_CAP
STRONG = history.STRONG
CONTEXT = history.CONTEXT
INTERVENTIONS = previous_policy.INTERVENTIONS
PARENTING = deepcopy(previous_policy.PARENTING)
require, digest, text_sha = history.require, history.digest, history.text_sha
PRINCIPLES_RELATIVE = 'research_notes/PARENTING_PRINCIPLES_ROHIN_2026-09-15.md'
PRINCIPLES_PATH = Path(__file__).resolve().parents[1] / PRINCIPLES_RELATIVE
PRINCIPLES_SHA256 = 'b7f4d6baef8158b41533d15acf0f7c924b4bc1e875a30d6ca31f874b5e1c589d'
PRINCIPLES_TEXT = PRINCIPLES_PATH.read_text()
require(hashlib.sha256(PRINCIPLES_PATH.read_bytes()).hexdigest() == PRINCIPLES_SHA256,
    'pinned_rohin_principles_required')
PRINCIPLES_BINDING = dict(path=PRINCIPLES_RELATIVE, sha256=PRINCIPLES_SHA256)
PARENT_INSTRUCTION = (
    'Guide the behavior visible in this actual child TRAIN experience. Decide what behavior '
    'to add, stop, or shift: attention, perception, effort, strategy, persistence, curiosity, '
    'goal regulation, reflection, or action. Guidance is scheduled for every episode, never '
    'triggered by failure, correctness, a score, or a grade. No oracle feedback is available. '
    'Help the child notice what warrants continuing, changing direction, or stopping; do not '
    'supply an answer, worked solution, invented observation, compulsory method count, or '
    'fixed-length template. Return only JSON with intervention_class, guidance and rationale. '
    'Choose intervention_class from: ' + ', '.join(INTERVENTIONS) + '. '
    'Neither an echoed instruction nor a changed answer demonstrates functional learning.')
PRESLEEP_PARENT_INSTRUCTION = (
    'Before the child writes its presleep reflection, provide pure metacognitive guidance '
    'about how it should examine its own cycle. Identify behavior to add, stop, or shift in '
    'attention, effort allocation, perception, self-monitoring, or goal regulation. Do not '
    'solve, grade, correct, or restate task answers. Do not use failure, correctness, or scores '
    'as an intervention trigger. The child must reflect after this intervention; do not write '
    'that reflection for it. Return only JSON with intervention_class, guidance and rationale. '
    'Choose intervention_class from: ' + ', '.join(INTERVENTIONS) + '. '
    'Do not invent a realization, observation, branch count, or evidence of benefit.')
PARENT_INSTRUCTION += '\n\nCOMMON ROHIN PARENTING PRINCIPLES:\n' + PRINCIPLES_TEXT
PRESLEEP_PARENT_INSTRUCTION += '\n\nCOMMON ROHIN PARENTING PRINCIPLES:\n' + PRINCIPLES_TEXT
WAKE = (
    'Work on the task in your own words. Notice what deserves attention, whether continued '
    'effort is useful, and whether to add, stop, or shift your current behavior. Ground your '
    'work in available observations, without invented checks or compulsory branching. '
    'Finish with a standalone FINAL: numeric answer when justified.')
REFLECT = (
    'Reflect on what you actually did and noticed in this experience. What behavior did you '
    'add, stop, shift, or retain, and why? Distinguish your own observations from parent advice '
    'and speculation. It is acceptable that the advice changed nothing; do not manufacture '
    'a realization or proof of benefit.')
PRESLEEP_REFLECT = (
    'Now write your own presleep reflection on this cycle, using the metacognitive guidance. '
    'Consider how attention, effort, perception, and goals influenced what you did. Describe '
    'what to add, stop, shift, or retain and what actual experience supports that choice. '
    'This is metacognition, not another task solution or a correctness report. Do not invent '
    'events or claim that repeating advice proves you learned it.')


def validate_task(task):
    previous_policy.validate_task(task)
    require('_HELD_' not in task['id'], 'train_only_task')


def validate_previous(previous):
    require(isinstance(previous, (list, tuple)) and len(previous) <= MAX_PREVIOUS,
        'bounded_previous_own_records')
    for item in previous:
        require(isinstance(item, dict) and set(item) == {'task_id', 'trace', 'source_record_sha256'},
            'previous_own_schema')
        require(isinstance(item['task_id'], str) and '_TRAIN_' in item['task_id']
            and '_HELD_' not in item['task_id'] and isinstance(item['trace'], str)
            and isinstance(item['source_record_sha256'], str)
            and re.fullmatch('[a-f0-9]{64}', item['source_record_sha256']), 'own_train_reflection')


def validate_parent_payload(payload):
    require(isinstance(payload, dict) and set(payload) == {'schema', 'cycle', 'episode', 'task',
        'child_state', 'previous_own_reflections', 'instruction', 'parenting'}, 'parent_schema')
    require(payload['schema'] == SCHEMA and type(payload['cycle']) is int
        and 1 <= payload['cycle'] <= CYCLES, 'parent_cycle')
    episode = payload['episode']
    require((type(episode) is int and 1 <= episode <= EPISODES) or episode == 'presleep',
        'parent_episode_or_presleep')
    require(isinstance(payload['task'], dict) and set(payload['task']) == {'id', 'question'},
        'public_task_schema')
    validate_task(dict(payload['task'], split='TRAIN'))
    state = payload['child_state']
    require(isinstance(state, dict) and set(state) == {'adapter_sha256', 'call_sha256', 'trace'},
        'score_blind_child_schema')
    require(all(isinstance(state[key], str) and re.fullmatch('[a-f0-9]{64}', state[key])
        for key in ('adapter_sha256', 'call_sha256')), 'actual_child_state_hashes')
    require(isinstance(state['trace'], str), 'actual_child_trace')
    instruction = PRESLEEP_PARENT_INSTRUCTION if episode == 'presleep' else PARENT_INSTRUCTION
    require(payload['instruction'] == instruction and payload['parenting'] == PARENTING,
        'parent_instruction_policy_binding')
    validate_previous(payload['previous_own_reflections'])
    require(not re.search(r'_HELD_|reference_answer|sealed_score|retention_score|'
        r'/localhome/|/tmp/|api[_-]?key|PRIVATE KEY', json.dumps(payload), re.I),
        'parent_visibility_violation')
    if episode == 'presleep':
        context = json.loads(state['trace'])
        require(isinstance(context, dict) and set(context) == {'episodes', 'presleep_initial'},
            'presleep_initial_and_episode_context')
        initial = context['presleep_initial']
        require(isinstance(initial, dict) and set(initial) == {'trace', 'source_record_sha256'}
            and isinstance(initial['trace'], str) and isinstance(initial['source_record_sha256'], str)
            and re.fullmatch('[a-f0-9]{64}', initial['source_record_sha256']),
            'actual_initial_presleep_trace')
        public = context['episodes']
        require(isinstance(public, list) and len(public) == EPISODES, 'two_public_presleep_episodes')
        for item in public:
            require(isinstance(item, dict) and set(item) == {'task', 'records'}, 'presleep_episode_schema')
            require(set(item['task']) == {'id', 'question'}, 'public_task_schema')
            validate_task(dict(item['task'], split='TRAIN'))
            require([record['purpose'] for record in item['records']]
                == ['experience', 'check', 'revision'], 'complete_presleep_episode')
            for record in item['records']:
                require(set(record) == {'purpose', 'trace', 'source_record_sha256'}
                    and isinstance(record['trace'], str)
                    and isinstance(record['source_record_sha256'], str)
                    and re.fullmatch('[a-f0-9]{64}', record['source_record_sha256']),
                    'score_blind_presleep_record')
        require(len({item['task']['id'] for item in public}) == EPISODES
            and public[-1]['task'] == payload['task'], 'last_train_task_presleep_anchor')


def validate_plan(plan, tasks):
    require(len(tasks) == 1, 'single_sequential_episode_parent')
    validate_task(tasks[0])
    require(isinstance(plan, dict) and set(plan) == {'intervention_class', 'guidance', 'rationale'},
        'intervention_plan_schema')
    require(plan['intervention_class'] in INTERVENTIONS, 'intervention_class')
    require(all(isinstance(plan[key], str) and plan[key].strip()
        for key in ('guidance', 'rationale')), 'actual_intervention_text')


def parent_payload(task, original, adapter_sha256, cycle, episode, previous=()):
    validate_task(task)
    require(type(episode) is int and 1 <= episode <= EPISODES, 'episode_parent_only')
    history.verify_record(task, original)
    require(original['purpose'] == 'experience' and original['response'] is not None, 'actual_original')
    payload = dict(schema=SCHEMA, cycle=cycle, episode=episode,
        task=dict(id=task['id'], question=task['question']),
        child_state=dict(adapter_sha256=adapter_sha256, call_sha256=digest(original),
            trace=original['response']['raw']), previous_own_reflections=deepcopy(list(previous)),
        instruction=PARENT_INSTRUCTION, parenting=deepcopy(PARENTING))
    validate_parent_payload(payload)
    return payload


def cycle_records(tasks, records):
    require(len(tasks) == EPISODES and len({task['id'] for task in tasks}) == EPISODES,
        'two_distinct_train_tasks')
    if isinstance(records, dict):
        require(set(records) in ({task['id'] for task in tasks},
            {task['id'] for task in tasks} | {'presleep_initial'}), 'exact_cycle_record_tasks')
        grouped = records
    else:
        require(isinstance(records, (list, tuple)) and len(records) == EPISODES * 3,
            'six_actual_episode_records')
        require({record['task_id'] for record in records} == {task['id'] for task in tasks},
            'exact_cycle_record_tasks')
        grouped = {task['id']: [record for record in records if record['task_id'] == task['id']]
            for task in tasks}
    public = []
    for task in tasks:
        validate_task(task)
        selected = grouped[task['id']]
        require([record['purpose'] for record in selected] == ['experience', 'check', 'revision'],
            'complete_presleep_episode')
        for record in selected:
            history.verify_record(task, record)
            require(record['response'] is not None, 'actual_child_response_required')
        public.append(dict(task=dict(id=task['id'], question=task['question']), records=[
            dict(purpose=record['purpose'], trace=record['response']['raw'],
                source_record_sha256=digest(record)) for record in selected]))
    return public


def presleep_payload(tasks, records, adapter_sha, cycle, previous=()):
    public = cycle_records(tasks, records)
    initial = presleep_initial(tasks[-1], records)
    context = dict(episodes=public, presleep_initial=dict(trace=initial['response']['raw'],
        source_record_sha256=digest(initial)))
    payload = dict(schema=SCHEMA, cycle=cycle, episode='presleep', task=deepcopy(public[-1]['task']),
        child_state=dict(adapter_sha256=adapter_sha, call_sha256=digest(records),
            trace=json.dumps(context, sort_keys=True, ensure_ascii=True)),
        previous_own_reflections=deepcopy(list(previous)), instruction=PRESLEEP_PARENT_INSTRUCTION,
        parenting=deepcopy(PARENTING))
    validate_parent_payload(payload)
    return payload


def messages(task, purpose, records=(), plan=None, previous=()):
    validate_task(task)
    validate_previous(previous)
    require(purpose in ('experience', 'check', 'revision'), 'child_purpose')
    if purpose == 'experience':
        require(not records and plan is None, 'original_without_parent')
        instruction = WAKE
        if previous:
            instruction += '\nYOUR EARLIER TRAIN REFLECTIONS (unverified):\n' + json.dumps(list(previous))
        return [dict(role='system', content=instruction), dict(role='user', content=task['question'])]
    validate_plan(plan, [task])
    require([record['purpose'] for record in records]
        == (['experience'] if purpose == 'check' else ['experience', 'check']), 'sequential_episode_history')
    for record in records:
        history.verify_record(task, record)
        require(record['response'] is not None, 'actual_child_response_required')
    last = records[-1]['response']
    result = deepcopy(last['messages'])
    result.append(dict(role='assistant', content=last['raw']))
    instruction = ('PARENT INTERVENTION (' + plan['intervention_class'] + '): ' + plan['guidance']
        + '\nContinue yourself. Decide what behavior to add, stop, shift, or retain and why. '
        'Finish with FINAL: numeric answer if justified.') if purpose == 'check' else REFLECT
    result.append(dict(role='user', content=instruction))
    return result


def presleep_initial(task, records):
    require(isinstance(records, dict) and 'presleep_initial' in records,
        'initial_presleep_before_parent_required')
    initial = records['presleep_initial']
    require(initial['task_id'] == task['id'] and initial['purpose'] == 'revision',
        'initial_presleep_last_train_task')
    history.verify_record(task, initial)
    response = initial['response']
    require(response and response['messages'] and isinstance(response['raw'], str)
        and response['input_truncated'] is False, 'actual_initial_presleep_response')
    return initial


def presleep_messages(tasks, records, plan, previous=()):
    public = cycle_records(tasks, records)
    validate_previous(previous)
    if plan is not None:
        validate_plan(plan, [tasks[-1]])
        initial = presleep_initial(tasks[-1], records)['response']
        result = deepcopy(initial['messages'])
        result.append(dict(role='assistant', content=initial['raw']))
        result.append(dict(role='user', content='PRESLEEP PARENT INTERVENTION ('
            + plan['intervention_class'] + '): ' + plan['guidance'] + '\n' + PRESLEEP_REFLECT))
        return result
    require(not isinstance(records, dict) or 'presleep_initial' not in records,
        'initial_reflection_never_regenerated')
    context = dict(cycle_train_experiences=public, previous_own_reflections=deepcopy(list(previous)))
    return [dict(role='system', content='Write your own initial presleep reflection on this cycle. '
            'Consider what you noticed, how you allocated attention and effort, and what is worth '
            'carrying forward. Use actual experience, not a task grade or another task solution.'),
        dict(role='user', content=json.dumps(context, sort_keys=True, ensure_ascii=True))]


def replay_row(task, record, plan, kind, teacher_in_prefix):
    validate_task(task)
    if plan is not None:
        validate_plan(plan, [task])
    else:
        require(not teacher_in_prefix, 'parent_plan_required_for_continuation')
    require(record['task_id'] == task['id'], 'source_task_mismatch')
    response = record['response']
    require(response and response['messages'] and response['input_truncated'] is False,
        'uncropped_native_source')
    require(type(response['terminal']) is bool and type(response['truncated']) is bool
        and not (response['terminal'] and response['truncated']), 'completion_flags')
    target = response['raw']
    require(isinstance(target, str), 'raw_child_text_required')
    guidance = plan['guidance'] if plan is not None else ''
    fragments = [guidance] + [fragment for fragment in re.split(r'(?<=[.!?])\s+|\n+', guidance)
        if len(fragment.split()) >= 8]
    echo = any(fragment and fragment in target for fragment in fragments)
    return dict(episode_id=task['id'], kind=kind, outcome=record.get('outcome', {}).get('status', 'UNASSESSED'),
        target=target, target_sha256=text_sha(target), source_record_sha256=digest(record),
        student_prefix=deepcopy(response['messages']), source_prompt_sha256=digest(response['messages']),
        source_prompt_tokens=response['prompt_tokens'], source_generated_token_ids=list(response['token_ids']),
        append_eos=response['terminal'], continuation_only=not response['terminal'], replay_mode=replay.MODE,
        teacher_in_prefix=teacher_in_prefix, own_reflection=kind in ('revision', 'presleep', 'presleep_initial'),
        parent_echo_detected=echo, parent_echo_measurement='literal_overlap_not_semantic_endorsement',
        retain_actual_child_output=True, objective='actual_child_continuation_SFT_not_unlikelihood',
        observed_fact_endorsement=False, source_outcome_is_metadata_only=True,
        source_label='R110_SEPARATE_PARENTED_CHILD_CONTINUATION', r110_schema=SCHEMA)


def replay_rows(task, records, plan):
    require([record['purpose'] for record in records] == ['experience', 'check', 'revision'],
        'complete_sequential_episode')
    rows = []
    for position, record in enumerate(records):
        history.verify_record(task, record)
        rows.append(replay_row(task, record, plan, record['purpose'], position > 0))
    return rows


def encode_presleep_record(task, record, plan):
    require(record['purpose'] == 'revision', 'actual_validated_presleep_revision_record')
    history.verify_record(task, record)
    return replay_row(task, record, plan, 'presleep_initial' if plan is None else 'presleep', plan is not None)


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
        outcome_change_is_not_functional_change=True, parent_trigger='FIXED_SCHEDULE_NOT_OUTCOME',
        source_label='R110_SEPARATE_PARENTED_CHILD_CONTINUATION')
