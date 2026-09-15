"""R109 fixed-code cadence arms over observable generated TRAIN segments."""

from copy import deepcopy
from functools import lru_cache
import json

from organism_v6 import orch_r108_code_parent as prior


VERSION = 'R110_BASE_CODE_METACOGNITIVE_DIALOGUE_V1'
START = 1789462920
HARD_END = 1789491720
CYCLES = 100
BASE_SHA, CONTEXT, OUTPUT, STOP_SHA = prior.BASE_SHA, prior.CONTEXT, prior.OUTPUT, prior.STOP_SHA
require, digest, outcome = prior.require, prior.digest, prior.outcome
CLASSES = ('perception', 'metacognition', 'persistence', 'curiosity', 'reflection', 'goals', 'affect')
ARMS = {
    'a100_segment': dict(wrapper='a100', index=0, uuid=prior.GPU_UUID, host_sha256=prior.HOST_SHA,
        cadence='EVERY_GENERATED_SEGMENT', native_cap=1700, parent_cap=700, reflection_cap=2048,
        style='Persistent perceptual/metacognitive calibration: distinguish observation from inference, '
            'notice limitations, redirect relevant questions, and ground reflection. Support persistence, goals and affect without solving.'),
    'node3_episode': dict(wrapper='ovx2', index=4, uuid='GPU-f484c608-a2d4-0c26-dee1-a06cc5ae69e4',
        host_sha256='3e10ebcb89f013079c1e088fa82820188b1a805b879ebb85a7ffeb689e7b86e9',
        cadence='EPISODE', native_cap=1500, parent_cap=500, reflection_cap=512,
        style='Persistent goal-regulated curiosity and effort: retain the actual goal, notice unproductive '
            'strategies, judge whether to persist or redirect, and support affect. Ground reflection and perception without solving.')}


def allocation(arm):
    require(arm in ARMS, 'only_allocated_r109_code_arms')
    return ARMS[arm]


@lru_cache(maxsize=2)
def frozen_tasks(arm):
    allocation(arm)
    result = []
    for cycle in range(1, CYCLES+1):
        for offset in range(6):
            parameter = 3+(cycle*7+offset)%17
            question, reference = prior.specification((cycle+offset)%10, parameter)
            marker = 1000+cycle*6+offset
            environment_values = [[], [0], [-parameter-2,parameter+3],
                [parameter,-parameter,1,1,parameter+1,-1], [3,0,-4,12,3,-4],
                [parameter+2,parameter+4,-parameter-5,0,parameter+2,2,1]]
            scalar = (cycle+offset)%10 in (0,2,5,7)
            question += f' Finally, add {marker} to the numeric result.' if scalar else f' Finally, append the marker {marker} to the resulting list.'
            reference = '('+reference+') + '+(str(marker) if scalar else '['+str(marker)+']')
            prompt = 'The only named argument is values, a list of integers with length at most 12. '+question+'\nReturn the requested bounded expression over values.'
            split = 'TRAIN' if offset<2 else 'HELD'
            row = dict(task_id=f'R109_CODE_{arm}_{split}_C{cycle:03d}_E{offset+1}', split=split,
                cycle=cycle, slot=offset+1, family='code', cohort=VERSION, prompt=prompt, question=question,
                paired_task_key=f'C{cycle:03d}_E{offset+1}', prompt_sha256=digest(prompt),
                question_sha256=prior.question_hash(question), reference_expression=reference,
                tests=[dict(arguments=dict(values=values), expected=prior.gym.evaluate(reference,dict(values=values)))
                    for values in environment_values])
            row['content_sha256'] = digest(row)
            result.append(row)
    return tuple(result)


def tasks(arm):
    return deepcopy(list(frozen_tasks(arm)))


def validate_cohort(rows, exclusions, arm):
    require(rows == tasks(arm), 'fixed_600_task_arm')
    old = prior.tasks()
    denied = set(exclusions['task_ids']) | {row['task_id'] for row in old}
    denied_prompts = set(exclusions['prompt_hashes']) | {row['prompt_sha256'] for row in old}
    denied_questions = set(exclusions['question_hashes']) | {row['question_sha256'] for row in old}
    require(len(rows)==600 and len({row['prompt_sha256'] for row in rows})==600
        and not denied.intersection(row['task_id'] for row in rows)
        and not denied_prompts.intersection(row['prompt_sha256'] for row in rows)
        and not denied_questions.intersection(row['question_sha256'] for row in rows), 'fresh_registered_code_tasks')
    return dict(train=200, held=400, prompt_count=600, exclusions_sha256=digest(exclusions),
        prospective_pair_same_prompts=True, same_split_across_arms=True,
        exact_exclusion_not_semantic_independence=True)


def schedule(rows, arm):
    config = allocation(arm)
    phases = ['segment1']
    if config['cadence']=='EVERY_GENERATED_SEGMENT':
        phases += ['parent1','reflection1']
    phases += ['segment2','parent2','reflection2','continuation']
    result = [dict(cell_id=task['task_id']+'_'+phase, task_id=task['task_id'], cycle=task['cycle'],
        slot=task['slot'], phase=phase, kind='PARENT' if phase.startswith('parent') else 'NATIVE')
        for task in rows for phase in (phases if task['split']=='TRAIN' else ['held'])]
    for cycle in range(1,CYCLES+1):
        task=meta_task(arm,cycle)
        for round_number in range(1,4):
            for prefix in ('meta_parent','meta_child'):
                phase=prefix+str(round_number)
                result.append(dict(cell_id=task['task_id']+'_'+phase,task_id=task['task_id'],cycle=cycle,slot=0,
                    phase=phase,kind='PARENT' if prefix=='meta_parent' else 'NATIVE'))
    require(sum(row['kind']=='NATIVE' for row in result)==config['native_cap']
        and sum(row['kind']=='PARENT' for row in result)==config['parent_cap'], 'fixed_new_r109_quota')
    return result


def messages(task, memory=''):
    system = prior.SYSTEM+ ('\n\nYour own latest TRAIN reflection, not a new observation:\n'+memory if memory else '')
    return [dict(role='system',content=system),dict(role='user',content=task['prompt'])]


def parent_instructions(arm):
    return ('You are the genuine supportive Astra parent. ADD, STOP or SHIFT behavior and cognition '
        'as relevant to this child; parenting is NOT failure-gated or score-driven. Scores are background '
        'and are not supplied here. Work from actual observed child text. Do not invent failure, '
        'success, experience, capability, selfhood, learning or emotions. No answers, code, pseudocode, '
        'worked solutions, test outputs, tools, held inputs or teacher targets. Maintain relevant '
        'perception/metacognition/persistence/curiosity/reflection/goals/affect coaching over time. '
        'For META_DIALOGUE, discuss only metacognition: importance, allocation of effort, context '
        'leaving, self/capability perception, reflections, and the child own context-based learning '
        'system. Do not solve the CODE task or prescribe correctness. This arm has frozen weights; '
        'do not claim a weight update. Help the child distill its own context without a semantic '
        'compiler. Return only the requested JSON plan.\nPersistent registered style: '+allocation(arm)['style']+(
        '\nTRAIN segment1 is an observable work-in-progress reasoning unit, not necessarily an answer. '
        'Do not label an intentionally unfinished segment as a failed final answer. Segment2 is an attempted answer. '
        'Maintain relevant parenting classes over time. Within your rationale string, optionally encode a JSON object '
        'with behavior_operation (ADD, STOP or SHIFT), intervention_classes (subset of perception, metacognition, persistence, curiosity, reflection, goals, affect), '
        'evidence, and intended_change. These declarations are intentions, not proof of semantic effect. '
        'Only natural-language coaching, no code, backticks, pseudocode, worked answers or test outputs.'))


def parent_payload(arm, task, segment, records, memory, prior_lessons):
    payload = dict(split='TRAIN', mode='CODE_SEGMENT', arm=arm, cycle=task['cycle'], episode_index=task['slot'], segment=segment,
        cadence=allocation(arm)['cadence'], episodes=[dict(task_id=task['task_id'], public_experience=dict(
            prompt=task['prompt'], generated_segments=[dict(raw=row['response']['raw'],
                terminal=row['response']['terminal'],
                truncated=row['response']['truncated']) for row in records]))],
        prior_own_reflection=memory, prior_parent_lessons=list(prior_lessons[-4:]))
    validate_parent_payload(payload)
    return payload


def validate_parent_payload(payload):
    if payload.get('mode')=='META_DIALOGUE':
        return validate_meta_payload(payload)
    require(set(payload)=={'split','mode','arm','cycle','episode_index','segment','cadence','episodes',
        'prior_own_reflection','prior_parent_lessons'}, 'strict_r109_parent_fields')
    config=allocation(payload['arm'])
    require(payload['split']=='TRAIN' and payload['mode']=='CODE_SEGMENT' and payload['cadence']==config['cadence']
        and type(payload['cycle']) is int and 1<=payload['cycle']<=CYCLES
        and payload['episode_index'] in (1,2) and payload['segment'] in (1,2)
        and (payload['segment']==2 or config['cadence']=='EVERY_GENERATED_SEGMENT')
        and len(payload['episodes'])==1, 'actual_registered_cadence')
    episode=payload['episodes'][0]
    require(set(episode)=={'task_id','public_experience'}, 'public_episode_only')
    task=next((row for row in frozen_tasks(payload['arm']) if row['task_id']==episode['task_id']),None)
    require(task is not None and task['split']=='TRAIN' and task['cycle']==payload['cycle']
        and task['slot']==payload['episode_index'], 'train_only_episode_binding')
    public=episode['public_experience']
    require(set(public)=={'prompt','generated_segments'} and public['prompt']==task['prompt']
        and len(public['generated_segments'])==payload['segment'], 'no_oracle_held_fields')
    for row in public['generated_segments']:
        require(set(row)=={'raw','terminal','truncated'} and isinstance(row['raw'],str)
            and type(row['terminal']) is bool
            and type(row['truncated']) is bool, 'actual_observable_segment')
    require(isinstance(payload['prior_own_reflection'],str) and len(payload['prior_parent_lessons'])<=4
        and all(isinstance(text,str) for text in payload['prior_parent_lessons']), 'train_history_only')
    return payload


def declared_classes(plan):
    try:
        value=json.loads(plan['rationale'])
        classes=value['intervention_classes']
        require(isinstance(classes,list) and classes and all(label in CLASSES for label in classes), 'declared_classes')
        return sorted(set(classes))
    except (ValueError,KeyError,TypeError):
        return ['UNDECLARED']


def declared_operation(plan):
    try:
        value=json.loads(plan['rationale'])['behavior_operation']
        return value if value in ('ADD','STOP','SHIFT') else 'UNDECLARED'
    except (ValueError,KeyError,TypeError):
        return 'UNDECLARED'


def meta_task(arm,cycle):
    allocation(arm)
    require(type(cycle) is int and 1<=cycle<=CYCLES,'bounded_meta_cycle')
    return dict(task_id=f'R110_META_{arm}_C{cycle:03d}',cycle=cycle,slot=0,split='TRAIN',
        reference_expression='NO_CODE_REFERENCE_FOR_METACOGNITIVE_DIALOGUE')


def meta_payload(arm,task,round_number,memory,dialogue,lessons):
    payload=dict(split='TRAIN',mode='META_DIALOGUE',arm=arm,cycle=task['cycle'],episode_index=0,
        segment=round_number,cadence=allocation(arm)['cadence'],episodes=[dict(task_id=task['task_id'],
            public_experience=dict(own_context_reflection=memory,dialogue=deepcopy(dialogue),
                completed_train_episode_ids=[row['task_id'] for row in frozen_tasks(arm)
                    if row['cycle']==task['cycle'] and row['split']=='TRAIN']))],prior_parent_lessons=list(lessons[-4:]))
    validate_meta_payload(payload)
    return payload


def validate_meta_payload(payload):
    require(set(payload)=={'split','mode','arm','cycle','episode_index','segment','cadence','episodes','prior_parent_lessons'},'pure_meta_fields')
    config=allocation(payload['arm'])
    task=meta_task(payload['arm'],payload['cycle'])
    require(payload['split']=='TRAIN' and payload['mode']=='META_DIALOGUE' and payload['episode_index']==0
        and payload['segment'] in (1,2,3) and payload['cadence']==config['cadence'] and len(payload['episodes'])==1,'bounded_meta_round')
    episode=payload['episodes'][0]
    require(set(episode)=={'task_id','public_experience'} and episode['task_id']==task['task_id'],'meta_identity')
    public=episode['public_experience']
    require(set(public)=={'own_context_reflection','dialogue','completed_train_episode_ids'}
        and isinstance(public['own_context_reflection'],str) and len(public['dialogue'])==payload['segment']-1
        and public['completed_train_episode_ids']==[row['task_id'] for row in frozen_tasks(payload['arm'])
            if row['cycle']==payload['cycle'] and row['split']=='TRAIN'],'meta_no_scores_or_task_oracles')
    for exchange in public['dialogue']:
        require(set(exchange)=={'parent','child'} and all(isinstance(text,str) for text in exchange.values()),'actual_meta_dialogue')
    require(len(payload['prior_parent_lessons'])<=4 and all(isinstance(text,str) for text in payload['prior_parent_lessons']),'meta_train_history')
    return payload
