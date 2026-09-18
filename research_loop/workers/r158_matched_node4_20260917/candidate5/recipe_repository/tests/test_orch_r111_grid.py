from pathlib import Path

import pytest

from organism_v6 import orch_r111_grid as policy
from gpu import orch_r110_claude_broker as broker


ROOT = Path(__file__).resolve().parents[1]


def test_exact_v2_parent_text_and_open_child_prompts():
    plan,principles=policy.snapshots(ROOT)
    parent=policy.parent_fixed_text(plan)
    assert 'training-wheels, harsh' in parent and '[SILENT]' in parent
    assert policy.text_sha(principles)==policy.PRINCIPLES_SHA
    assert policy.PRESLEEP_PROMPT=='Talk freely with your parent about your experience and what is on your mind.'
    for prompt in (policy.PRESLEEP_PROMPT,policy.REFLECTION_PROMPT):
        assert '\n' not in prompt and ':' not in prompt and not any(char.isdigit() for char in prompt)


def test_frozen_fresh_cohort_and_both_halves_identical():
    first=policy.cohort();second=policy.cohort()
    assert first==second and len(first['HELD'])==8 and len(first['TRAIN'])==16
    tasks=first['TRAIN']+first['HELD']
    assert len({task['id'] for task in tasks})==24
    assert len({policy.digest({key:task[key] for key in ('cells','start','visibility')}) for task in tasks})==24
    for task in tasks:
        assert len(policy.game.shortest_solution(task))<=16
        assert task['task_sha256']==policy.digest({key:value for key,value in task.items() if key!='task_sha256'})
    assert [task['difficulty_rank'] for task in first['HELD']]==list(range(1,9))
    manifest=policy.manifest(ROOT)
    assert manifest['sleep_count']==0 and manifest['mode']=='CONTEXT_ONLY_FROZEN_BASE'
    assert manifest['lora'] is None and manifest['optimizer'] is None
    assert manifest['sleep0_readout_status'].startswith('NOT_RUN')


def test_no_outcome_in_public_environment():
    task=policy.cohort()['TRAIN'][0]
    state=policy.game.initial(task)
    observed=policy.public_observation(task,state)
    assert set(observed)=={'task_id','position','map','has_key','moves_remaining'}
    assert not set(observed).intersection(policy.FORBIDDEN_OUTCOMES)


def request():
    corpus=policy.cohort();task=corpus['TRAIN'][0]
    event=policy.public_event(0,'child','actual child', 'a'*64)
    return policy.queue_request('F4_C01_E1','F4_FABLE',1,0,'experience',task,[event],policy.digest(corpus),100)


def test_queue_exact_hubble_schema_and_train_exclusions():
    value=request();corpus=policy.cohort()
    config=dict(life_id='F4_FABLE',family='grid',train_tasks={task['id']:task['task_sha256'] for task in corpus['TRAIN']},
        excluded_task_ids=[task['id'] for task in corpus['HELD']],cohort_sha256=policy.digest(corpus))
    assert broker.validate_request(value,config)==value['payload']
    assert value['lane_deadline_unix']==220 and value['lane_deadline_unix']-30==190


def test_held_cannot_be_queued_to_parent():
    with pytest.raises(ValueError,match='TRAIN_parent_only'):
        policy.queue_request('id','F4_FABLE',1,0,'experience',policy.cohort()['HELD'][0],[], 'a'*64,100)


@pytest.mark.parametrize('status',['MISSING','SILENT','COMPLETE'])
def test_missing_silent_complete_all_continue(status):
    value=request()
    response=dict(status=status,plan=dict(speak=True,message='guidance'),request_sha256=policy.digest(value),
        payload_sha256=value['payload_sha256'],finished_unix=150,actual_model='claude-fable-5-1')
    result=policy.parent_disposition(value,response,151,'claude-fable-5-1')
    assert result['continue_life'] and result['status']==status
    assert result['guidance']==('guidance' if status=='COMPLETE' else None)


def test_late_and_absent_do_not_stop_or_reapply():
    value=request()
    assert policy.parent_disposition(value,None,220,'claude-fable-5-1')['status']=='MISSING'
    response=dict(status='COMPLETE',plan=dict(speak=True,message='guidance'),finished_unix=191)
    assert policy.parent_disposition(value,response,192,'claude-fable-5-1')['status']=='MISSING'


def test_wrong_parent_model_is_missing_not_substitution():
    value=request()
    response=dict(status='COMPLETE',plan=dict(speak=True,message='guidance'),request_sha256=policy.digest(value),
        payload_sha256=value['payload_sha256'],finished_unix=150,actual_model='wrong-model')
    assert policy.parent_disposition(value,response,151,'claude-fable-5-1')['status']=='MISSING'


def test_silence_window_never_authorizes_Fable():
    with pytest.raises(ValueError,match='explicit_watcher_GO'):
        policy.validate_fable_go(dict(authorized=True,authorization='30_MINUTE_SILENCE_ELAPSED'), 'a'*64,100000)
    policy.validate_fable_go(dict(authorized=True,authorization='WATCHER_RELAYED_ROHIN_GO',source_reference='Main explicit notice',
        config_sha256='a'*64,not_before_unix=99),'a'*64,100)


def test_fixed_decoder_and_no_sleep_claim():
    assert policy.DECODER['episode_total_new_tokens']>=4096
    assert policy.DECODER['context_limit']==16384 and policy.DECODER['no_repeat_ngram_size']==4
    assert policy.DECODER['held_batch_size']==8 and policy.DECODER['held_max_new_tokens']==2048
    assert not policy.DECODER['do_sample'] and not policy.DECODER['post_generation_deletion']


def test_release_remains_unarmed_without_receiver_ready():
    from gpu import orch_r111_grid_release as release
    with pytest.raises(ValueError,match='receiver_ready_required'):
        release.release()
