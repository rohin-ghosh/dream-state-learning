from copy import deepcopy
import pytest
from gpu import orch_r118_grid_l2_candidate_audit as audit


def pair():
    messages=[dict(role='user',content='Inspect the blocked neighbor.')]
    before=dict(status='COMPLETE',split='TRAIN',task_id='train',cycle=1,base_sha256='base',finished_unix=1.)
    after=dict(before,started_unix=3.,messages=messages,response=dict(messages=messages,raw='INSPECT: 0,1',
        token_ids=[1,2],prompt_tokens=10,terminal=True,truncated=False))
    parent=dict(observed_unix=2.,disposition=dict(status='COMPLETE',guidance=messages[0]['content']))
    return before,after,parent


def test_exact_child_target_and_masked_parent():
    before,after,parent=pair()
    row=audit.validate_pair(before,after,parent,{'train'},{'held'})
    assert row['target']==after['response']['raw'] and row['student_prefix']==after['messages']
    assert row['prefix_labels']=='ALL_MINUS_100_INCLUDING_PARENT_AND_PRIOR_CHILD'
    assert row['trainingAllowed'] is False


@pytest.mark.parametrize('key,value',[('split','DEV'),('split','FINAL'),('attached_readout',True),
    ('evaluation_origin',True),('task_id','held'),('adapter',{'changed':True})])
def test_excludes_held_and_state_change(key,value):
    before,after,parent=pair();after[key]=value
    with pytest.raises(ValueError): audit.validate_pair(before,after,parent,{'train'},{'held'})


def test_missing_parent_not_advice_success():
    before,after,parent=pair();parent['disposition']['status']='MISSING'
    with pytest.raises(ValueError): audit.validate_pair(before,after,parent,{'train'},{'held'})


def test_parent_must_be_exact_causal_prefix():
    before,after,parent=pair();parent=deepcopy(parent);parent['disposition']['guidance']='Invented guidance'
    with pytest.raises(ValueError): audit.validate_pair(before,after,parent,{'train'},{'held'})


def test_original_native_prefix_is_top_level_without_duplicate_response_messages():
    before,after,parent=pair();del after['response']['messages']
    assert audit.validate_pair(before,after,parent,{'train'},{'held'})['student_prefix']==after['messages']


def test_duplicate_response_prefix_mismatch_rejected():
    before,after,parent=pair();after['response']['messages']=[dict(role='user',content='Wrong')]
    with pytest.raises(ValueError): audit.validate_pair(before,after,parent,{'train'},{'held'})
