"""Prospective observable-segment cadence; frozen-weight contextual parenting."""

import json
import re

from organism_v6 import orch_math_feedback_uptake_base as base
from organism_v6 import orch_math_feedback_uptake_r108 as previous


require = base.require
digest = base.digest
SCHEMA = 'MATH_R109_OBSERVABLE_TRAIN_SEGMENTS_V1'
DEVICES = {
    0: 'GPU-0ee6f753-c61e-e18a-8aea-acccd3042939',
    1: 'GPU-71e5a3e2-e9c8-5caf-70d8-73794ac34821',
    2: 'GPU-41a86250-88eb-ed8a-ddfe-9d6f93515da1',
}
HOST_SHA = previous.HOST_SHA
CADENCES = {0: 'every_thought', 1: 'every_episode', 2: 'every_100_thoughts'}
CYCLES = 96
NATIVE_CAP = CYCLES * 14
PARENT_CAPS = {0: 576, 1: 192, 2: 5}
CLASSES = ('perception', 'persistence', 'metacognition', 'curiosity',
    'goal_meta_goal_regulation', 'reflection', 'action_steering', 'affective_value',
    'self_perception', 'surprise', 'regret', 'confidence_regulation')
INSTRUCTION = ('Coach the actual sourced child thinking, not the correct answer. The child has '
    'frozen weights; learning here means contextual behavior, not weight updates. Pester and '
    'remind when useful, but preserve productive rumination. Consider perception, persistence, '
    'metacognitive effort allocation, curiosity, goals and meta-goals, multi-angle reflection, '
    'action steering, affective values, self-perception, surprise, regret and confidence '
    'regulation. Ground any intervention in this observed difficulty, never invent feelings '
    'or observations. Do not prescribe a solution, branch count, or decorative surprise. '
    'Incorrect attempts are recorded negative examples, not endorsed facts. Help the child '
    'notice conflicts, choose relevant questions and revise its approach. Give concise '
    'usable next-turn coaching; guidance plus episode guidance must total at most 200 words. '
    'No tools, hidden answers, external resources, or claims of semantic improvement.')


def due(index, completed_train_segments):
    require(index in DEVICES and type(completed_train_segments) is int
        and 1 <= completed_train_segments <= CYCLES * 6, 'bounded_observable_segment')
    interval = {0: 1, 1: 3, 2: 100}[index]
    return completed_train_segments % interval == 0


def budget(index):
    require(index in DEVICES, 'allocated_base_lane')
    return dict(cycles=CYCLES, sequential_episodes_per_cycle=2,
        train_segments_per_episode=3, thought_definition='one_completed_generated_TRAIN_segment',
        hidden_cot_count=False, cadence=CADENCES[index], native_calls=NATIVE_CAP,
        parent_calls=PARENT_CAPS[index], held_per_cycle=8, retries=0,
        max_wall_seconds=28800, max_gpu_hours=8, adapter=None, optimizer=None,
        weight_writes=0, new_control_arms=0)


def make_cohort(index, identifiers, questions):
    require(index in DEVICES and identifiers and questions, 'complete_registry_needed')
    seen_ids, seen_questions = set(identifiers), set(questions)
    cohort = dict(schema=SCHEMA, train=[], held=[], excluded_ids=sorted(seen_ids),
        excluded_question_sha256=sorted(seen_questions))
    for cycle in range(1, CYCLES + 1):
        for split, count, destination in (('TRAIN', 2, 'train'), ('HELD', 8, 'held')):
            group = []
            for position in range(count):
                for nonce in range(10000):
                    task = base.history.source.make_task(f'R109_NODE3_{index}_{split}', cycle, position + nonce * 1000)
                    task['split'] = split
                    if task['id'] not in seen_ids and task['question_sha256'] not in seen_questions:
                        seen_ids.add(task['id'])
                        seen_questions.add(task['question_sha256'])
                        group.append(task)
                        break
                else:
                    raise ValueError('fresh_pool_exhausted')
            cohort[destination].append(group)
    return cohort


def parent_payload(index, cycle, segment, task, records):
    require(due(index, segment), 'only_scheduled_parent')
    require(task['split'] == 'TRAIN' and 1 <= cycle <= CYCLES, 'train_scope')
    for record in records:
        base.history.verify_record(task, record)
    payload = dict(schema=SCHEMA, index=index, cycle=cycle, segment=segment,
        cadence=CADENCES[index], instruction=INSTRUCTION, classes=list(CLASSES),
        episodes=[dict(task_id=task['id'], question=task['question'],
            records=[base.history.public_record(record) for record in records])])
    validate_parent_payload(payload)
    return payload


def validate_parent_payload(payload):
    require(set(payload) == {'schema', 'index', 'cycle', 'segment', 'cadence',
        'instruction', 'classes', 'episodes'}, 'private_parent_schema')
    require(payload['schema'] == SCHEMA and payload['instruction'] == INSTRUCTION,
        'exact_parent_contract')
    index = payload['index']
    require(due(index, payload['segment']) and payload['cadence'] == CADENCES[index], 'cadence_binding')
    require(1 <= payload['cycle'] <= CYCLES and payload['classes'] == list(CLASSES), 'cycle_classes')
    require(len(payload['episodes']) == 1, 'current_episode_only')
    episode = payload['episodes'][0]
    require(set(episode) == {'task_id', 'question', 'records'} and '_TRAIN_' in episode['task_id'], 'train_only')
    require(1 <= len(episode['records']) <= 3, 'actual_history_bound')
    require([record['purpose'] for record in episode['records']] ==
        list(base.history.PURPOSES[:len(episode['records'])]), 'ordered_sourced_history')
    for record in episode['records']:
        require(set(record) == {'purpose', 'trace', 'outcome', 'native_error', 'source_record_sha256'}, 'record_visibility')
        require(set(record['outcome']) <= {'status', 'correct', 'parsed_answer', 'final_parseable', 'terminal', 'truncated'}, 'oracle_excluded')
        require(record['outcome']['status'] in ('CORRECT', 'INCORRECT', 'NO_RESPONSE'), 'truthful_outcome')
        require(record['outcome']['correct'] == (record['outcome']['status'] == 'CORRECT'), 'outcome_consistency')
        require(re.fullmatch('[a-f0-9]{64}', record['source_record_sha256']) is not None, 'source_hash')
    require(not re.search(r'_HELD_|reference_answer|sealed_score|retention_score|/tmp/|/localhome/|api[_-]?key|PRIVATE KEY',
        json.dumps(payload), re.I), 'parent_visibility')


def messages(task, records=(), purpose='experience', teacher='', memory=None):
    require(not teacher or purpose != 'held', 'held_parent_free')
    result = base.messages(task, records, purpose, '', memory)
    if teacher:
        result[0]['content'] += '\nPRIVATE PARENT GUIDANCE:\n' + teacher
    if purpose == 'revision':
        result[0]['content'] += '\n' + previous.REFLECTION
    return result


def validate_plan(plan, task_id):
    require(set(plan) == {'guidance', 'order', 'episode_guidance', 'rationale'}, 'plan_schema')
    require(plan['order'] == [task_id] and set(plan['episode_guidance']) == {task_id}, 'plan_task')
    require(all(isinstance(text, str) for text in (plan['guidance'], plan['rationale'], plan['episode_guidance'][task_id])), 'plan_text')
    require(len((plan['guidance'] + ' ' + plan['episode_guidance'][task_id]).split()) <= 200, 'bounded_guidance_no_clipping')
    return plan['guidance'] + '\n' + plan['episode_guidance'][task_id]
