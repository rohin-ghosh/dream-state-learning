"""R109 budgets, observable cadence, natural release and no hidden thought claims."""

from copy import deepcopy
import json
import os
from pathlib import Path
from types import SimpleNamespace

import pytest

from gpu import orch_r108_code_parent_r109_run as run
from gpu import orch_r108_code_parent_r109_broker as broker
from gpu import orch_r108_code_parent_registry as registry
from organism_v6 import orch_r108_code_parent_r109 as policy


@pytest.mark.parametrize('arm',tuple(policy.ARMS))
def test_frozen600_tasks_all_reference_cases_and_caps(arm):
    tasks=policy.tasks(arm)
    assert policy.validate_cohort(tasks,registry.collect([]),arm)['train']==200
    assert len(tasks)==600
    config=policy.allocation(arm)
    schedule=policy.schedule(tasks,arm)
    assert len(schedule)==len({row['cell_id'] for row in schedule})==config['native_cap']+config['parent_cap']
    for task in tasks:
        response=dict(raw=json.dumps(dict(expression=task['reference_expression'])),terminal=True,truncated=False,token_ids=[11,1])
        assert policy.outcome(task,response)['passed']


def test_matched_prompts_and_splits_across_arms():
    first,second=(policy.tasks(arm) for arm in policy.ARMS)
    assert [(row['prompt'],row['split'],row['paired_task_key']) for row in first]==[
        (row['prompt'],row['split'],row['paired_task_key']) for row in second]
    assert not {row['task_id'] for row in first}&{row['task_id'] for row in second}
    assert not {row['prompt_sha256'] for row in first}&{row['prompt_sha256'] for row in policy.prior.tasks()}


@pytest.mark.parametrize('arm',tuple(policy.ARMS))
def test_one_cycle_actual_cadence_mock(tmp_path,arm,monkeypatch):
    tasks=policy.tasks(arm)[:6]
    (tmp_path/run.LANE).mkdir()
    run.write(tmp_path/'COHORT_PRIVATE.json',tasks)
    run.write(tmp_path/'RESERVATIONS.json',policy.schedule(policy.tasks(arm),arm))
    calls,parents=[],[]
    def generate(messages,**kwargs):
        calls.append(dict(messages=messages,**kwargs))
        return dict(messages=messages,raw='Actual own reflection' if kwargs['reflection'] else '{"expression":"values"}',
            token_ids=[11,1],terminal=True,truncated=False,reflection_guard=None)
    engine=SimpleNamespace(tokenizer=SimpleNamespace(apply_chat_template=lambda messages,**kwargs:[11,12]),
        generate=generate,verify_base=lambda:None,
        model=SimpleNamespace(named_parameters=lambda:[],parameters=lambda:[],modules=lambda:[]))
    def parent(root,arm,task,segment,records,memory,lessons,check,payload=None):
        payload=payload if payload is not None else policy.parent_payload(arm,task,segment,records,memory,lessons)
        policy.validate_parent_payload(payload)
        parents.append(payload)
        path,row=run.begin(root,task,('meta_parent' if task['slot']==0 else 'parent')+str(segment))
        row.update(status='COMPLETE',lesson='Notice your assumptions and return to the stated goal.',declared_intervention_classes=['metacognition'])
        run.write(path,row)
        return row
    monkeypatch.setattr(policy,'CYCLES',1)
    run.cycles(tmp_path,arm,engine,lambda label:None,parent_call=parent)
    expected=17 if arm=='a100_segment' else 15
    assert len(calls)==expected
    assert len(parents)==(7 if arm=='a100_segment' else 5)
    assert len(list((tmp_path/run.LANE).glob('TRIPLE_*.json')))==len(parents)
    assert sum(call['max_new_tokens']==512 for call in calls)==(2 if arm=='a100_segment' else 7)
    for payload in parents:
        assert 'HELD' not in json.dumps(payload) and 'expected' not in json.dumps(payload)
        assert 'failure_class' not in json.dumps(payload)
        if payload['mode']=='CODE_SEGMENT':
            assert len(payload['episodes'][0]['public_experience']['generated_segments'])==payload['segment']
    for path in (tmp_path/run.LANE/'cells').glob('*_held.json'):
        assert 'Actual parent guidance:' not in json.dumps(run.read(path)['response']['messages'])
    for path in (tmp_path/run.LANE).glob('TRIPLE_*.json'):
        assert run.read(path)['helpful'] is None
    with pytest.raises(FileExistsError):
        run.cycles(tmp_path,arm,engine,lambda label:None,parent_call=parent)
    assert len(calls)==expected


@pytest.mark.parametrize('arm',tuple(policy.ARMS))
def test_hard17_02_new_caps_no_reset(arm):
    config=policy.allocation(arm)
    bound=run.lifetime(config,policy.HARD_END+30000)
    run.check_lifetime(bound,arm,policy.START+1)
    assert bound['hard_deadline_unix']==policy.HARD_END and policy.HARD_END-policy.START==28800
    for key in ('started_unix','native_cap','parent_cap','hard_deadline_unix','gpu_hours_cap'):
        changed=dict(bound)
        changed[key]+=1
        with pytest.raises(ValueError):
            run.check_lifetime(changed,arm,policy.START+2)
    with pytest.raises(ValueError):
        run.check_lifetime(bound,arm,bound['native_deadline_unix'])


def test_live_predecessor_blocks_without_signal(tmp_path):
    previous=tmp_path/'prior'
    previous.mkdir()
    run.write(tmp_path/'DEPLOY_INPUTS.json',dict(previous_lane=str(previous)))
    assert run.previous_released(tmp_path) is False
    run.write(previous/'TERMINAL.json',dict(status='COMPLETE'))
    identity=run.common.process_identity(Path('/proc')/str(os.getpid()))
    run.write(previous/'LAUNCH.json',dict(identity=identity))
    assert run.previous_released(tmp_path) is False
    identity['start_ticks']=str(int(identity['start_ticks'])+1)
    run.write(previous/'LAUNCH.json',dict(identity=identity))
    assert run.previous_released(tmp_path) is True


@pytest.mark.parametrize('mutation',['held','oracle','cadence','segment','extra'])
def test_strict_r109_parent_visibility(mutation):
    task=policy.tasks('a100_segment')[0]
    record=dict(response=dict(raw='Actual work',terminal=True,truncated=False),outcome=dict(failure_class='observable_work_in_progress'))
    payload=policy.parent_payload('a100_segment',task,1,[record],'',[])
    if mutation=='held':payload['split']='HELD'
    elif mutation=='oracle':payload['episodes'][0]['public_experience']['tests']='secret'
    elif mutation=='cadence':payload['cadence']='EPISODE'
    elif mutation=='segment':payload['segment']=2
    else:payload['private']='secret'
    with pytest.raises(ValueError):policy.validate_parent_payload(payload)


def test_declared_classes_are_not_semantic_evidence():
    assert policy.declared_classes(dict(rationale='free prose'))==['UNDECLARED']
    assert policy.declared_classes(dict(rationale=json.dumps(dict(intervention_classes=['perception','reflection']))))==['perception','reflection']


@pytest.mark.parametrize('identifier',['GUIDED_SLEEP_C101_P1_S1','GUIDED_SLEEP_C1_P3_S1','GUIDED_SLEEP_C1_P1_S3'])
def test_parent_identifier_quota_bounds(tmp_path,identifier):
    with pytest.raises(ValueError):
        broker.process(None,tmp_path,tmp_path/broker.QUEUE/(identifier+'.request.json'),None,None,0,'','a100_segment')


def test_actual_local_numeric_proc_start_before_load():
    identity=run.common.process_identity(Path('/proc')/str(os.getpid()))
    assert identity['pid']==os.getpid()


def test_broker_wrapper_and_context_bound_to_arm(tmp_path,monkeypatch):
    monkeypatch.setattr(broker,'PRINCIPLES','Shared parenting principles fixture')
    assert broker.Store(tmp_path,tmp_path,'a100_segment').wrapper=='a100'
    assert broker.Store(tmp_path,tmp_path,'node3_episode').wrapper=='ovx2'
    previous=broker.transport.parent.INSTRUCTIONS
    with broker.parent_context('a100_segment'):
        assert 'metacognitive' in broker.transport.parent.INSTRUCTIONS
    assert broker.transport.parent.INSTRUCTIONS==previous


def test_meta_dialogue_has_no_scores_or_task_answers():
    task=policy.meta_task('a100_segment',1)
    payload=policy.meta_payload('a100_segment',task,1,'My own reflection',[],[])
    assert policy.validate_parent_payload(payload)==payload
    assert 'reference_expression' not in json.dumps(payload) and 'expected' not in json.dumps(payload)
    payload['episodes'][0]['public_experience']['score']=1
    with pytest.raises(ValueError):policy.validate_parent_payload(payload)


def test_parent_behavior_operations_are_self_declared_not_failure_gate():
    assert 'NOT failure-gated' in policy.parent_instructions('a100_segment')
    assert policy.declared_operation(dict(rationale='{"behavior_operation":"SHIFT"}'))=='SHIFT'
    assert policy.declared_operation(dict(rationale='Moved attention'))=='UNDECLARED'
