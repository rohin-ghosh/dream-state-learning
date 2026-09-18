from copy import deepcopy
import json
import os
from pathlib import Path
from types import SimpleNamespace

import pytest

from organism_v6 import orch_r109_grid as policy
from gpu import orch_r109_grid_run as run
from gpu import orch_r109_grid_broker as broker


@pytest.mark.parametrize('split',['TRAIN','HELD'])
@pytest.mark.parametrize('cycle',range(1,9))
@pytest.mark.parametrize('episode',[1,2])
def test_every_prospective_environment_solvable_without_mutation(split,cycle,episode):
    task = policy.task(split,cycle,episode)
    original = deepcopy(task)
    state = policy.initial(task)
    for action in policy.shortest_solution(task):
        state,unused = policy.transition(task,state,action)
    assert state['success'] and state['done'] and state['steps']<=16 and task == original
    with pytest.raises(ValueError,match='terminal_state'):
        policy.transition(task,state,'WAIT')


def test_grid_is_state_action_reward_not_math_and_hard_hides_unseen_cells():
    task = policy.task('TRAIN',1,2)
    state = policy.initial(task)
    observation = policy.observation(task,state)
    assert '?' in ''.join(observation['map']) and 'cells' not in observation
    after,reward = policy.transition(task,state,'INVALID')
    assert after['position'] == state['position'] and after['steps'] == 1
    assert reward['reward'] < 0 and reward['event'] == 'invalid_action'
    assert state['steps'] == 0


def test_door_needs_key_and_wall_collisions_consume_moves():
    task = dict(id='test',cells=['.D.G','.###','K...','....'],start=[0,0],max_steps=16,visibility='full')
    state = policy.initial(task)
    blocked,event = policy.transition(task,state,'RIGHT')
    assert event['event'] == 'blocked' and blocked['position'] == [0,0]
    state,_ = policy.transition(task,state,'DOWN'); state,_ = policy.transition(task,state,'DOWN')
    assert state['key']
    state,_ = policy.transition(task,state,'UP'); state,_ = policy.transition(task,state,'UP')
    state,event = policy.transition(task,state,'RIGHT')
    assert state['position'] == [0,1] and event['event'] == 'moved'


@pytest.mark.parametrize('raw,expected',[('ACTION: UP','UP'),('think\nACTION: RIGHT','RIGHT'),
    ('ACTION: UP\nACTION: DOWN','INVALID'),('ACTION: UP\nignore','INVALID'),
    ('rm -rf /','INVALID'),('{"action":"RIGHT"}','INVALID')])
def test_action_parser_never_executes_strings(raw,expected):
    assert policy.parse_action(raw) == expected


def test_cadence_is_explicit_proposals_not_hidden_thoughts():
    assert all(policy.intervene('segment',number,2) for number in range(1,257))
    assert [number for number in range(1,257) if policy.intervene('hundred_segments',number,2)] == [100,200]
    assert policy.intervene('episode',177,1) and not policy.intervene('episode',178,2)
    assert policy.bounds()['native_per_lane'] == 1858 and policy.bounds()['parent_per_lane'] == 298
    assert policy.HARD_END-policy.START_BOUND == 8*3600
    assert all(policy.HARD_END < spec['lease_end']-21600 for spec in policy.LANES.values())


def test_held_cannot_receive_parent_or_prior_life_context():
    task = policy.task('HELD',1,1); state = policy.initial(task)
    with pytest.raises(ValueError,match='held_parent_and_memory_free'):
        policy.child_messages(task,state,memory=['leak'])
    with pytest.raises(ValueError,match='parent_train_only'):
        policy.parent_payload(task,state,'proposal',[],[],'segment','supportive',1)
    assert len(policy.child_messages(task,state)) == 2


def test_parent_payload_contains_public_observation_not_hidden_map_or_gold():
    task = policy.task('TRAIN',1,2); state = policy.initial(task)
    payload = policy.parent_payload(task,state,'ACTION: WAIT',[],[],'segment','supportive',1)
    assert 'cells' not in json.dumps(payload) and 'gold' not in json.dumps(payload)
    assert '?' in ''.join(payload['observation']['map'])
    policy.validate_parent(payload,dict(speak=True,message='Consider what you know.',rationale='perception: visibility'))
    with pytest.raises(ValueError,match='explicit_intervention_class'):
        policy.validate_parent(payload,dict(speak=True,message='Try.',rationale='uncertified'))


def test_real_episode_triple_join_and_sequential_parenting():
    task = policy.task('TRAIN',1,1); events=[]; saved={}; counter=0
    def generate(spec,purpose,messages):
        nonlocal counter
        counter+=1; events.append(purpose)
        return dict(response=dict(raw='ACTION: WAIT',messages=messages),reference=dict(path=f'call{counter}',sha256=str(counter)))
    def ask(payload,reference):
        events.append('parent')
        return dict(plan=dict(speak=True,message='Think about progress.',rationale='persistence: stuck'))
    result=run.episode(task,'episode',[],0,generate,ask,saved.__setitem__,'supportive')
    assert events[:3] == ['proposal','parent','continuation']
    assert events[-1] == 'proposal' and result['steps'] == 16 and result['parent_calls'] == 1
    triple=result['triples'][0]
    assert triple['proposal']['path']=='call1' and triple['continuation']['path']=='call2'
    assert triple['actual_transition']['action']=='WAIT' and triple['functional_helpfulness']=='UNASSESSED'
    assert len([name for name in saved if name.startswith('STEPS/')]) == 16


def test_held_episode_never_calls_parent_or_reflection():
    task=policy.task('HELD',1,2); events=[]
    def generate(spec,purpose,messages):
        events.append(purpose)
        assert 'Parent guidance' not in json.dumps(messages) and 'earlier own TRAIN' not in json.dumps(messages)
        return dict(response=dict(raw='ACTION: WAIT'),reference=dict(path=str(len(events))))
    def forbidden(*args): raise AssertionError('parent_in_held')
    result=run.episode(task,'segment',[],0,generate,forbidden,lambda *args:None,'supportive')
    assert events==['proposal']*16 and result['parent_calls']==0


def test_reservation_never_refunds_failure(tmp_path,monkeypatch):
    monkeypatch.setattr(run.time,'time',lambda:policy.START_BOUND+60)
    for number in range(1,299): assert run.spend(tmp_path,'PARENT',dict(task='failed'))==number
    with pytest.raises(ValueError,match='absolute_call_budget'): run.spend(tmp_path,'PARENT',{})
    assert run.spend(tmp_path,'NATIVE',{})==1


def test_broker_rejects_held_and_foreign_call_references():
    task=policy.task('TRAIN',1,1)
    payload=policy.parent_payload(task,policy.initial(task),'ACTION: WAIT',[],[],'segment','supportive',1)
    request=dict(id='P0001',payload=payload,payload_sha256=policy.digest(payload),ready_sha256='bound',
        source_proposal=dict(path=str(broker.ROOT/'calls/N00001.json'),sha256='a'*64))
    assert broker.validate_request(request,'bound',{task['id']})=='P0001'
    request['source_proposal']['path']='/tmp/foreign.json'
    with pytest.raises(ValueError,match='source_native_call_scope'):
        broker.validate_request(request,'bound',{task['id']})
    with pytest.raises(ValueError,match='known_train_request_only'):
        broker.validate_request(request,'bound',set())


def test_roster_has_no_train_held_geometry_overlap():
    tasks=[task for groups in policy.roster().values() for group in groups for task in group]
    assert len(tasks)==32
    assert len({task['id'] for task in tasks})==32
    assert len({policy.digest({name:task[name] for name in ('cells','start','visibility')}) for task in tasks})==32


def test_nested_atomic_evidence_and_updates(tmp_path):
    path=tmp_path/'calls/N00001.json'
    run.write(path,dict(status='STARTED'))
    run.write(path,dict(status='COMPLETE'))
    assert run.read(path)==dict(status='COMPLETE') and not list(path.parent.glob('*.tmp'))


def test_metacognition_is_long_child_parent_child_after_two_episodes():
    tasks=[policy.task('TRAIN',1,number) for number in (1,2)]
    results=[dict(history=[dict(own_trace='I waited without checking.')],final_state=policy.initial(task)) for task in tasks]
    events=[]; emitted={}
    def generate(task,purpose,messages):
        events.append(purpose)
        return dict(response=dict(raw='I should notice when waiting is not useful.'),reference=dict(path=purpose,sha256='a'*64))
    def ask(payload,reference):
        events.append('parent')
        assert payload['purpose']=='metacognition' and len(payload['executed_history'])==2
        return dict(plan=dict(speak=True,message='Notice when observation should change your effort.',rationale='metacognition: effort'))
    memory=run.metacognition(tasks,results,[],'episode','supportive',32,generate,ask,emitted.__setitem__)
    assert events==['metacognitive_reflection','parent','context_distillation']
    assert memory[0]['source']['path']=='context_distillation'
    assert emitted['METACOGNITIVE_TRIPLE.json']['weight_updates']==0


def test_resident_train_held_cycle_runs_without_reload_or_held_parent_leak(tmp_path,monkeypatch):
    monkeypatch.setattr(run,'validate',lambda *args:dict(model_dir='unused'))
    monkeypatch.setattr(run.time,'time',lambda:policy.START_BOUND+60)
    monkeypatch.setenv('CUDA_VISIBLE_DEVICES',policy.LANES['ovx']['uuid'])
    previous_read=Path.read_bytes
    monkeypatch.setattr(Path,'read_bytes',lambda path:('CUDA_VISIBLE_DEVICES='+policy.LANES['ovx']['uuid']).encode()+b'\0'
        if str(path)=='/proc/self/environ' else previous_read(path))
    monkeypatch.setattr(run,'assert_no_adapter',lambda model:True)
    monkeypatch.setattr(run.signal,'signal',lambda *args:None)
    run.write(tmp_path/'COHORT_PRIVATE.json',policy.roster())
    events=[]
    def generate(messages,max_new_tokens):
        events.append((messages,max_new_tokens))
        return dict(raw='ACTION: WAIT',messages=messages,prompt_tokens=12,token_ids=[1,2],terminal=True,truncated=False)
    engine=SimpleNamespace(tokenizer=SimpleNamespace(apply_chat_template=lambda *args,**kwargs:[1]*12),
        generate=generate,loaded_base_sha256=policy.BASE_SHA,no_adapter=True,runtime={},model=None,verify_base=lambda:None)
    calls=[]
    def parent(root,lane,payload,reference,check):
        calls.append(payload)
        return dict(plan=dict(speak=True,message='Consider your progress.',rationale='persistence: effort'))
    monkeypatch.setattr(run,'parent',parent)
    run.run(tmp_path,'ovx','episode',1,'train',shared_engine=engine)
    assert len(calls)==3 and calls[-1]['purpose']=='metacognition'
    trained=run.read(tmp_path/'episode/cycle01/train/COMPLETE.json')
    assert trained['r110_resident'] and not trained['fresh_process'] and len(trained['memory'])==1
    assert sum(cap==policy.REFLECTION_CAP for messages,cap in events)==2
    run.run(tmp_path,'ovx','episode',1,'held',shared_engine=engine)
    assert len(calls)==3
    held=run.read(tmp_path/'episode/cycle01/held/COMPLETE.json')
    assert held['held_parent_free'] and held['memory']==[] and not held['generation_KV_reused']


def test_native_frozen_base_contract_and_all_tokenizer_inputs():
    if os.environ.get('R109_NATIVE_CPU')!='1':pytest.skip('native cached base and tokenizer only')
    result=run.portable.verify_base_files(run.BUNDLE,run.MODEL,expected_manifest_sha256=run.BUNDLE_SHA)
    assert result['expected_base_sha256']==policy.BASE_SHA
    tokenizer=run.portable.source.native.load_local_tokenizer(run.MODEL)
    for groups in policy.roster().values():
        for tasks in groups:
            for task in tasks:
                messages=policy.child_messages(task,policy.initial(task))
                tokens=tokenizer.apply_chat_template(messages,tokenize=True,add_generation_prompt=True,return_dict=False)
                assert len(tokens)+policy.REFLECTION_CAP<policy.CONTEXT


def test_principles_exact_snapshot_and_proactive_scope():
    text=policy.principles()
    assert 'ADD a behaviour' in text and 'There is no compiler' in text
    assert 'never wait for failure' in policy.PARENT_SYSTEM
