from copy import deepcopy
import json
from pathlib import Path
import subprocess
import sys
from types import SimpleNamespace

import pytest

from gpu import orch_r111_grid_recover as recovery
from gpu import orch_r111_grid_atomic_broker as broker


@pytest.fixture
def replay(tmp_path):
    rows=[dict(kind='NATIVE',number=9,reserved_unix=1,cadence='segment',cycle=2,phase='train',
        purpose='proposal',task_id='task',split='TRAIN'),dict(kind='PARENT',number=4,reserved_unix=2,
        cadence='segment',task_id='task')]
    (tmp_path/'LEDGER.jsonl').write_text(''.join(json.dumps(row)+'\n' for row in rows))
    call=dict(status='COMPLETE',task_id='task',split='TRAIN',purpose='proposal',messages=[{'text':'saved'}],
        base_sha256='base',adapter=None,started_unix=1,finished_unix=2,
        response=dict(raw='saved response',requested_generation_cap=384))
    (tmp_path/'calls').mkdir();(tmp_path/'calls/N00009.json').write_text(json.dumps(call))
    spend_calls=[]
    old=SimpleNamespace(spend=lambda *args:spend_calls.append(args) or 10,
        write=lambda path,value:recovery.write_new(path,value))
    return recovery.Replay(tmp_path,old,'segment',2),call,spend_calls


def test_saved_calls_reused_no_model_or_parent_dispatch(replay):
    value,call,charges=replay
    detail={key:call[key] for key in ('purpose','task_id','split')}
    detail.update(cadence='segment',cycle=2,phase='train')
    assert value.spend(value.root,'NATIVE',detail)==9
    engine=SimpleNamespace(generate=lambda *args,**kwargs:pytest.fail('old model call repeated'))
    assert value.generate(engine,call['messages'],max_new_tokens=384)==call['response']
    assert value.spend(value.root,'PARENT',dict(cadence='segment',task_id='task'))==4
    assert charges==[]
    assert value.spend(value.root,'NATIVE',detail)==10 and len(charges)==1


def test_cached_prompt_or_reservation_mismatch_fails_closed(replay):
    value,call,charges=replay
    with pytest.raises(ValueError,match='sequence_mismatch'):
        value.spend(value.root,'PARENT',{})
    value.spend(value.root,'NATIVE',dict(cadence='segment',cycle=2,phase='train'))
    with pytest.raises(ValueError,match='saved_prompt'):
        value.generate(None,[{'text':'new'}],max_new_tokens=384)
    assert charges==[]


def test_old_call_bytes_preserved_despite_new_clock(replay):
    value,call,unused=replay
    path=value.root/'calls/N00009.json';before=path.read_bytes()
    started=deepcopy(call);started['status']='STARTED';started['started_unix']=99
    value.write(path,started)
    finished=deepcopy(call);finished.update(started_unix=99,finished_unix=100)
    value.write(path,finished)
    assert path.read_bytes()==before
    finished['response']['raw']='changed'
    with pytest.raises(ValueError,match='same_saved_response'):
        value.write(path,finished)


def test_existing_step_divergence_never_overwritten(replay):
    value,unused,charges=replay
    path=value.root/'step.json';path.write_text('{"state":1}')
    with pytest.raises(ValueError,match='immutable_reconstructed'):
        value.write(path,{'state':2})
    assert json.loads(path.read_text())=={'state':1}


def test_atomic_response_is_complete_and_cannot_overwrite(tmp_path):
    path=tmp_path/'P0001.response.json'
    payload=b'{"status":"COMPLETE","message":"complete body"}'
    result=subprocess.run([sys.executable,'-c',broker.ATOMIC_WRITE,str(path)],input=payload,capture_output=True)
    assert result.returncode==0 and path.read_bytes()==payload
    again=subprocess.run([sys.executable,'-c',broker.ATOMIC_WRITE,str(path)],input=b'{}',capture_output=True)
    assert again.returncode!=0 and path.read_bytes()==payload


def test_unknown_native_call_is_not_retried(replay):
    value,call,charges=replay
    call['status']='STARTED';(value.root/'calls/N00009.json').write_text(json.dumps(call))
    with pytest.raises(ValueError,match='cannot_retry_unknown'):
        value.spend(value.root,'NATIVE',dict(cadence='segment',cycle=2,phase='train'))
    assert not charges


def test_new_call_start_complete_and_first_milestone(replay):
    value,call,unused=replay
    value.original_write=lambda path,record:path.write_text(json.dumps(record))
    path=value.root/'calls/N00010.json'
    started=deepcopy(call);started['status']='STARTED'
    value.write(path,started)
    value.write(path,call)
    assert json.loads(path.read_text())['status']=='COMPLETE'
    milestone=json.loads((value.output/'FIRST_NEW_NATIVE.json').read_text())
    assert milestone['call']==recovery.ref(path)
    assert milestone['new_model_call'] and milestone['old_calls_retried']==0
