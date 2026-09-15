"""R108 perception and goal-regulation BASE treatments on node3 4/5."""

from types import SimpleNamespace

from organism_v6 import orch_math_feedback_uptake_node3 as prior


base = prior.base
HOST_SHA = prior.HOST_SHA
add_declared_question_hashes = prior.add_declared_question_hashes
DEVICES = {4: 'GPU-f484c608-a2d4-0c26-dee1-a06cc5ae69e4', 5: 'GPU-bc211959-642d-664b-3581-42a0dbe434e9'}
STYLES = {
    4: ('perception-calibration', 'Intervention classes: perception, metacognition, reflection. Use supportive long-horizon coaching on the actual sourced difficulty, not the answer. Distinguish observations from inferences, identify conflicting evidence, and invite a check that could change the interpretation. Do not prescribe a solution, method quota or fabricated uncertainty.'),
    5: ('goal-regulated-persistence', 'Intervention classes: persistence, curiosity, goal and meta-goal regulation, action steering, affective-value, reflection. Use supportive short-horizon coaching on the actual sourced difficulty, not the answer. Ask what next action serves the goal, whether the current subgoal still helps, and when to persist or change an unproductive strategy. Do not supply solutions, shame the child, impose endless effort or require decorative questions.')}
CLASSES = {4: ('perception','metacognition','reflection'),
    5: ('persistence','curiosity','goal_meta_goal_regulation','action_steering','affective_value','reflection')}
REFLECTION = ('Consider relevant alternative perceptions of the actual environment: what was observed, '
    'what was inferred, what conflicts with that interpretation, and what evidence changed or could '
    'change your next action. Preserve unresolved errors honestly. Do not invent another angle, '
    'method, question or experience merely to satisfy this request.')


def configured(index):
    base.require(index in DEVICES, 'only_allocated_node3_4_5')
    style, instruction = STYLES[index]
    namespace = SimpleNamespace(**vars(base))
    namespace.UUID = DEVICES[index]
    namespace.PHYSICAL = index
    namespace.NATIVE_CAP = 28
    namespace.PARENT_CAP = 4
    namespace.PARENT_INSTRUCTION = base.PARENT_INSTRUCTION + '\n' + instruction
    parenting = dict(style=style, horizon='long' if index == 4 else 'short', tone='supportive', strength=base.STRONG)
    def validate(payload):
        base.require(payload['parenting'] == parenting and payload['instruction'] == namespace.PARENT_INSTRUCTION, 'exact_r108_style')
        normalized = dict(payload, instruction=base.PARENT_INSTRUCTION,
            parenting=dict(style='persistent-curious', horizon='long', tone='supportive', strength=base.STRONG))
        base.validate_parent_payload(normalized)
    def payload(tasks, records, cycle, round_number, previous=()):
        result = base.parent_payload(tasks, records, cycle, round_number, previous)
        result['parenting'] = dict(parenting)
        result['instruction'] = namespace.PARENT_INSTRUCTION
        validate(result)
        return result
    def messages(task, records=(), purpose='experience', teacher='', memory=None):
        result = base.messages(task, records, purpose, teacher, memory)
        if purpose == 'revision':
            result[0]['content'] += '\n' + REFLECTION
            result[-1]['content'] += '\n' + REFLECTION
        return result
    namespace.messages = messages
    namespace.INTERVENTION_CLASSES = CLASSES[index]
    namespace.validate_parent_payload = validate
    namespace.parent_payload = payload
    namespace.options = lambda model_dir: SimpleNamespace(model_dir=model_dir, adapter_dir=None, phase='readout',
        device='cuda:0', gpu_uuid=DEVICES[index], expected_base_sha256=base.BASE_SHA)
    return namespace


def distinct_cohorts(identifiers, questions):
    identifiers, questions = set(identifiers), set(questions)
    result = {}
    scopes = ('L1_ALL_SOURCE','L1_READOUT','L2_ALL_SOURCE','L2_READOUT','RETENTION')
    for index in (4,5):
        cohort=base.history.make_cohort([dict(scope=scope,complete_pool=True,
            ids=sorted(identifiers),question_sha256=sorted(questions)) for scope in scopes])
        cohort.pop('retention')
        result[index]=cohort
        for group in cohort['train']+cohort['held']:
            for task in group:
                base.require(task['id'] not in identifiers and task['question_sha256'] not in questions,'fresh_distinct_task')
                identifiers.add(task['id'])
                questions.add(task['question_sha256'])
    return result


def lineage_triples(index,cycle,records,parent_bindings,child_identity):
    base.require(index in DEVICES and cycle in (1,2),'triple_scope')
    result=[]
    for task_id,history in records.items():
        base.require('_TRAIN_' in task_id,'train_triples_only')
        for round_number,before_index,after_index in ((1,0,1),(2,1,2)):
            if len(history)<=before_index:
                continue
            before=history[before_index]
            after=history[after_index] if len(history)>after_index else None
            result.append(dict(task_id=task_id,cycle=cycle,round=round_number,
                child_state=dict(identity=child_identity,source_record_sha256=base.digest(before),
                    outcome=before['outcome'],purpose=before['purpose']),
                parent_intervention=dict(classes=CLASSES[index],binding=parent_bindings.get(round_number)),
                subsequent_behavior=dict(source_record_sha256=base.digest(after) if after else None,
                    outcome=after['outcome'] if after else None,purpose=after['purpose'] if after else None,
                    status='RECORDED' if after else 'MISSING_OR_PENDING'),
                semantic_behavior_change='UNKNOWN_AUTHOR_REVIEW',helpfulness='UNKNOWN_AUTHOR_REVIEW',
                causal_effect_claim=False))
    return result
