"""CPU full100-call seam, no retry and actual minimal engine response contract."""

from contextlib import nullcontext
import json
import os
from pathlib import Path
from types import SimpleNamespace

import pytest

from gpu import orch_r108_code_parent_run as runner
from gpu import orch_r108_code_parent_broker as broker
from gpu.orch_r108_code_parent_engine import Engine
from organism_v6 import orch_r108_code_parent as policy


class Values:
    def __init__(self, values):
        self.values=values
    def __getitem__(self,key):
        return Values(self.values[key[1]]) if isinstance(key,tuple) else Values(self.values)
    def tolist(self):
        return self.values


def test_actual_minimal_engine_response_and_prefix():
    engine=Engine.__new__(Engine)
    engine.device='cpu'
    engine.check=lambda phase:None
    engine.torch=SimpleNamespace(tensor=lambda values,**kwargs:Values(values[0]),long='long',
        ones_like=lambda values:values,inference_mode=nullcontext)
    engine.transformers=SimpleNamespace(GenerationConfig=lambda **kwargs:kwargs)
    engine.tokenizer=SimpleNamespace(apply_chat_template=lambda messages,**kwargs:[11,12],
        eos_token_id=99,pad_token_id=0,decode=lambda tokens,**kwargs:'{"expression":"values"}')
    engine.model=SimpleNamespace(named_parameters=lambda:[],parameters=lambda:[],modules=lambda:[],
        generate=lambda **kwargs:Values([11,12,13,99]))
    result=engine.generate([dict(role='user',content='task')],max_new_tokens=2048)
    assert result['terminal'] is True and result['token_ids']==[13,99]
    assert result['input_truncated'] is False and result['reflection_guard'] is None
    engine.model.generate=lambda **kwargs:Values([0,12,13,99])
    with pytest.raises(ValueError,match='prefix'):
        engine.generate([],max_new_tokens=2048)


def test_numeric_proc_identity_required_before_model_load():
    identity=runner.common.process_identity(Path('/proc')/str(os.getpid()))
    assert identity['pid']==os.getpid() and identity['uid']==os.getuid()
    with pytest.raises(ValueError):
        runner.common.process_identity(Path('/proc/self'))


@pytest.fixture
def prepared(tmp_path):
    (tmp_path/runner.LANE).mkdir()
    runner.write(tmp_path/'COHORT_PRIVATE.json',policy.tasks())
    runner.write(tmp_path/'RESERVATIONS.json',policy.schedule(policy.tasks()))
    return tmp_path


def test_full_ten_cycles_exact100_calls_no_oracle_or_held_parent(prepared):
    calls, parents=[],[]
    def generate(messages,**kwargs):
        calls.append(dict(messages=messages,**kwargs))
        return dict(messages=messages,raw='Actual own reflection' if kwargs['reflection'] else '{"expression":"values"}',
            token_ids=[11,1],terminal=True,truncated=False,reflection_guard=None)
    engine=SimpleNamespace(tokenizer=SimpleNamespace(apply_chat_template=lambda messages,**kwargs:[11,12]),
        generate=generate,verify_base=lambda:None,
        model=SimpleNamespace(named_parameters=lambda:[],parameters=lambda:[],modules=lambda:[]))
    def parent(root,task,original,memory,check):
        parents.append(policy.parent_payload(task,original,memory))
        path,record=runner.begin_cell(root,task,'parent')
        record.update(status='COMPLETE',lesson='Notice which constraint your reasoning did not address.')
        runner.write(path,record)
        return record
    runner.cycles(prepared,engine,lambda label:None,parent_call=parent)
    assert len(calls)==100 and len(parents)==20
    assert sum(call['reflection'] for call in calls)==20
    assert len(list((prepared/runner.LANE).glob('TRIPLE_*.json')))==20
    assert len(list((prepared/runner.LANE).glob('CYCLE_*_COMPLETE.json')))==10
    assert len(list((prepared/runner.LANE/'cells').glob('*.json')))==120
    for payload in parents:
        assert payload['split']=='TRAIN' and 'HELD' not in json.dumps(payload)
        assert 'expected' not in json.dumps(payload) and 'reference_expression' not in json.dumps(payload)
    for path in (prepared/runner.LANE/'cells').glob('*_held.json'):
        row=runner.read(path)
        assert 'Actual parent guidance:' not in json.dumps(row['response']['messages'])
    with pytest.raises(FileExistsError):
        runner.cycles(prepared,engine,lambda label:None,parent_call=parent)
    assert len(calls)==100


def test_failure_reservation_retained_no_retry(prepared):
    def fail(*args,**kwargs):
        raise RuntimeError('expected_test_failure')
    engine=SimpleNamespace(tokenizer=SimpleNamespace(apply_chat_template=lambda *args,**kwargs:[1,2]),generate=fail)
    task=policy.tasks()[0]
    with pytest.raises(RuntimeError):
        runner.generate(prepared,engine,task,'original',policy.messages(task),lambda label:None)
    row=runner.read(next((prepared/runner.LANE/'cells').glob('*.json')))
    assert row['status']=='FAILED' and row['error_type']=='RuntimeError'
    with pytest.raises(FileExistsError):
        runner.generate(prepared,engine,task,'original',policy.messages(task),lambda label:None)


def test_unreserved_call_and_held_parent_denied(prepared):
    with pytest.raises(ValueError,match='reserved'):
        runner.begin_cell(prepared,policy.tasks()[2],'parent')
    with pytest.raises(ValueError,match='reserved'):
        runner.begin_cell(prepared,policy.tasks()[0],'retry')


def test_broker_context_restores_shared_library_fields():
    previous=broker.transport.parent.policy.validate_parent_payload,broker.transport.parent.policy.digest,broker.transport.parent.INSTRUCTIONS
    with broker.parent_context():
        assert broker.transport.parent.policy.validate_parent_payload is policy.validate_parent_payload
        assert broker.transport.parent.INSTRUCTIONS==policy.PARENT_INSTRUCTIONS
    assert previous==(broker.transport.parent.policy.validate_parent_payload,broker.transport.parent.policy.digest,broker.transport.parent.INSTRUCTIONS)


@pytest.mark.parametrize('field,value', [('native_cap',101),('parent_cap',21),('gpu_hours_cap',3),
    ('hard_deadline_unix',7301),('native_deadline_unix',50),('lease_end_unix',8000),('started_unix',101)])
def test_lifetime_and_lease_cannot_expand(field,value):
    lifetime=dict(started_unix=100,native_deadline_unix=7180,hard_deadline_unix=7300,
        lease_end_unix=40000,gpu_hours_cap=2,native_cap=100,parent_cap=20)
    assert runner.validate_lifetime(lifetime,100)==lifetime
    lifetime[field]=value
    with pytest.raises(ValueError):
        runner.validate_lifetime(lifetime,100)


@pytest.mark.parametrize('identifier',['GUIDED_SLEEP_C0_P1','GUIDED_SLEEP_C11_P1','GUIDED_SLEEP_C1_P3','FROZEN_C1_P1'])
def test_broker_rejects_extra_quota_identifiers(tmp_path,identifier):
    with pytest.raises(ValueError,match='twenty'):
        broker.process(None,tmp_path,tmp_path/broker.QUEUE/(identifier+'.request.json'),None,None,0,'')
