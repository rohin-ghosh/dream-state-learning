"""Resident R110 behavior parenting and pure pre-boundary metacognition."""

import hashlib
import json
from pathlib import Path
import re

from organism_v6 import orch_math_feedback_uptake_r109 as prior


base, previous = prior.base, prior.previous
require, digest = prior.require, prior.digest
DEVICES, HOST_SHA, CADENCES, CLASSES = prior.DEVICES, prior.HOST_SHA, prior.CADENCES, prior.CLASSES
SCHEMA = 'MATH_R110_RESIDENT_METACOGNITION_V1'
CYCLES = 96
NATIVE_CAP = 1536
PARENT_CAPS = {0: 768, 1: 288, 2: 103}
PRINCIPLES = ''
PRINCIPLES_SHA = ''
INSTRUCTION = ''
DISTILLATION_CAPS = {0: 2048, 1: 4096, 2: 4096}
BEHAVIOR = ('Add, stop or shift behavior regardless of correctness. Outcomes are background, '
    'never an intervention trigger or selection criterion. Work on effort allocation, '
    'self-capability perception, reflection and the child\'s own learning system. Before the '
    'reflection boundary, engage in pure metacognition and context distillation: what matters, '
    'what context is being left, what to retain alongside previous learning, self-perception '
    'and how the child learns. Do not coach a numeric answer or worked solution. Help behavior, '
    'not task success. No branch quotas, decorative surprise, invented feelings or observations. '
    'Give usable guidance plus episode guidance totaling at most 200 words. No tools.')


def bind_principles(path, expected):
    global PRINCIPLES, PRINCIPLES_SHA, INSTRUCTION
    data = Path(path).read_bytes()
    require(hashlib.sha256(data).hexdigest() == expected and len(data) > 100, 'exact_shared_principles')
    PRINCIPLES, PRINCIPLES_SHA = data.decode(), expected
    INSTRUCTION = PRINCIPLES + '\n\nR110 MATH EXECUTION CONTRACT:\n' + BEHAVIOR


def due(index, segment):
    require(index in DEVICES and type(segment) is int and 1 <= segment <= CYCLES * 8, 'observable_train_segment')
    position = (segment - 1) % 8 + 1
    mandatory_dialogue = position == 7
    scheduled = index == 0 or (index == 1 and position in (3, 6)) or (index == 2 and segment % 100 == 0)
    return mandatory_dialogue or scheduled


def budget(index):
    require(index in DEVICES, 'allocated_base_lane')
    return dict(cycles=CYCLES, sequential_episodes_per_cycle=2, native_calls=NATIVE_CAP,
        parent_calls=PARENT_CAPS[index], cadence=CADENCES[index], mandatory_pre_boundary_dialogue=True,
        cadence_and_mandatory_dialogue_counted_separately=True, train_segments_per_cycle=8,
        task_segments=6, metacognition_segments=2, held_per_cycle=8, retries=0,
        max_wall_seconds=28800, max_gpu_hours=8, adapter=None, optimizer=None, weight_writes=0,
        thought_definition='one_completed_generated_TRAIN_segment_including_metacognition',
        hidden_cot_count=False, distillation_generation_cap=DISTILLATION_CAPS[index],
        reflection_length_not_forced=True, new_control_arms=0)


def make_cohort(index, identifiers, questions):
    return prior.make_cohort(index, identifiers, questions)


def record(task, purpose, response=None, error=None):
    if not task.get('context_distillation'):
        return base.history.record(task, purpose, response, error)
    require(task['split'] == 'TRAIN' and purpose == 'revision', 'own_metacognition_only')
    require((response is None) != (error is None), 'response_or_failure')
    if response is not None:
        require(response.get('input_truncated') is False, 'uncropped_metacognition')
    return dict(task_id=task['id'], purpose=purpose, response=response, error=error,
        outcome=dict(status='NOT_SCORED_METACOGNITION' if response is not None else 'NO_RESPONSE', correct=False),
        target_sha256=base.history.text_sha(response['raw']) if response else None)


def parent_payload(index, cycle, segment, task, records):
    require(PRINCIPLES and due(index, segment), 'scheduled_bound_principles')
    for event in records:
        require(event == record(task, event['purpose'], event['response'], event['error']), 'sourced_record')
    payload = dict(schema=SCHEMA, index=index, cycle=cycle, segment=segment,
        cadence=CADENCES[index], instruction=INSTRUCTION, principles_sha256=PRINCIPLES_SHA,
        classes=list(CLASSES), pre_boundary_dialogue=(segment - 1) % 8 + 1 == 7,
        episodes=[dict(task_id=task['id'], question=task['question'],
            records=[base.history.public_record(event) for event in records])])
    validate_parent_payload(payload)
    return payload


def validate_parent_payload(payload):
    require(PRINCIPLES and set(payload) == {'schema', 'index', 'cycle', 'segment', 'cadence',
        'instruction', 'principles_sha256', 'classes', 'pre_boundary_dialogue', 'episodes'}, 'private_parent_schema')
    require(payload['schema'] == SCHEMA and payload['instruction'] == INSTRUCTION
        and payload['principles_sha256'] == PRINCIPLES_SHA, 'shared_principles_binding')
    require(due(payload['index'], payload['segment']) and payload['cadence'] == CADENCES[payload['index']], 'cadence_binding')
    require(1 <= payload['cycle'] <= CYCLES and payload['classes'] == list(CLASSES), 'cycle_classes')
    require(payload['pre_boundary_dialogue'] == ((payload['segment'] - 1) % 8 + 1 == 7), 'mandatory_dialogue_binding')
    require(len(payload['episodes']) == 1, 'one_sourced_episode')
    episode = payload['episodes'][0]
    require(set(episode) == {'task_id', 'question', 'records'} and '_TRAIN_' in episode['task_id'], 'train_only')
    require(1 <= len(episode['records']) <= 3, 'history_bound')
    for event in episode['records']:
        require(set(event) == {'purpose', 'trace', 'outcome', 'native_error', 'source_record_sha256'}, 'source_visibility')
        require(set(event['outcome']) <= {'status', 'correct', 'parsed_answer', 'final_parseable', 'terminal', 'truncated'}, 'no_oracle')
        require(event['outcome']['status'] in ('CORRECT', 'INCORRECT', 'NO_RESPONSE', 'NOT_SCORED_METACOGNITION'), 'truthful_outcome')
        require(event['outcome']['correct'] == (event['outcome']['status'] == 'CORRECT'), 'no_relabel')
        require(re.fullmatch('[a-f0-9]{64}', event['source_record_sha256']) is not None, 'source_hash')
    public = dict(payload, instruction='SHARED_PRINCIPLES_SNAPSHOT_OMITTED_FROM_VISIBILITY_SCAN')
    require(not re.search(r'_HELD_|reference_answer|sealed_score|retention_score|/tmp/|/localhome/|api[_-]?key|PRIVATE KEY',
        json.dumps(public), re.I), 'parent_visibility')


def messages(task, records=(), purpose='experience', teacher='', memory=None):
    if not task.get('context_distillation'):
        require(not teacher or purpose != 'held', 'parent_free_readout')
        result = base.messages(task, records, 'experience' if purpose == 'check' else purpose, '', memory)
        if teacher:
            result[0]['content'] += '\nPRIVATE PARENT GUIDANCE:\n' + teacher
        if purpose == 'check':
            result.append(dict(role='user', content='Continue in a way that serves your thinking, including acting if ready. Do not add a check or a different method merely because this is another turn.'))
        if purpose == 'revision':
            result[0]['content'] += '\n' + previous.REFLECTION
        return result
    require(purpose == 'revision', 'distillation_not_readout')
    system = ('This is pure metacognition and context-distillation dialogue before leaving a context, '
        'not another attempt to solve a task. Discuss what mattered, what to retain alongside '
        'previous learning, your effort allocation and perception of your capabilities, '
        'your reflection and your own learning system. Distinguish actual history from '
        'self-hypotheses; do not invent feelings, observations or improvement. Do not solve '
        'the task or give a numeric FINAL. Respond in your own voice, with useful detail, '
        'not padding or a teacher lesson. Preserve unresolved problems honestly.')
    if teacher:
        system += '\nPRIVATE PARENT GUIDANCE:\n' + teacher
    result = [dict(role='system', content=system), dict(role='user', content=task['question'])]
    for event in records:
        require(event == record(task, event['purpose'], event['response'], event['error']), 'actual_dialogue_history')
        if event['response']:
            result.append(dict(role='assistant', content=event['response']['raw']))
    if records:
        result.append(dict(role='user', content='Continue this metacognitive dialogue and distill a usable own context. Preserve relevant earlier learning rather than replacing it with a success story.'))
    return result


validate_plan = prior.validate_plan
