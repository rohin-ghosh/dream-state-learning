from copy import deepcopy
from dataclasses import asdict

import pytest

from research_loop.workers.rohin221_continuous_caption_20260918.adopt_base_schedule import migrate
from research_loop.workers.rohin221_continuous_caption_20260918.controller import Plan
from research_loop.workers.rohin221_continuous_caption_20260918.scene_schedule import POLICY


def checkpoint():
    plan=asdict(Plan(condition='base',rule_sha256='a'*64))
    plan.pop('scene_schedule')
    backend=dict(identity=dict(base_sha256='actual-base',optimizer_created=False),kind='FROZEN',
        source=dict(loader=dict(path='/old/source.py',sha256='same-loader')))
    previous=dict(pending=None,stage='THINK',attempt=0,opportunity=25,completed_opportunities=24,
        binding=dict(plan=plan,scenes_sha256='scenes'),backend_state=backend,
        history=[dict(role='assistant',content='preserved')],events=[dict(actual='receipt')],generations=[1])
    binding=dict(previous['binding'],plan=dict(plan,scene_schedule=POLICY))
    actual=deepcopy(backend);actual['source']['loader']['path']='/new/source.py'
    return previous,binding,actual


def test_declared_schedule_adoption_retains_all_history_events_and_counter():
    previous,binding,backend=checkpoint()
    result=migrate(previous,binding,backend)
    for key in ['history','events','generations','opportunity','completed_opportunities']:
        assert result[key]==previous[key]
    assert result['source_adoptions'][0]['uninterrupted_process_claim'] is False
    assert previous['binding']['plan'].get('scene_schedule') is None


@pytest.mark.parametrize('fault',['pending','budget','model','source'])
def test_no_pending_loss_silent_budget_model_or_generation_source_change(fault):
    previous,binding,backend=checkpoint()
    if fault=='pending':previous['pending']=dict(kind='GENERATION')
    if fault=='budget':binding['plan']['act_tokens']+=1
    if fault=='model':backend['identity']['base_sha256']='different'
    if fault=='source':backend['source']['loader']['sha256']='different'
    with pytest.raises(ValueError):migrate(previous,binding,backend)


def test_large_real_feedback_window_preserves_full_state_and_actual_results(tmp_path):
    import json
    from types import SimpleNamespace
    from research_loop.workers.rohin221_continuous_caption_20260918.controller import Controller
    from research_loop.workers.rohin221_continuous_caption_20260918.freeform import extract_batches
    plan=Plan(condition='base',rule_sha256='a'*64,context_tokens=1024,scene_schedule=POLICY)
    backend=SimpleNamespace(kind='CPU_ONLY',state_receipt=lambda: {},
        count_tokens=lambda messages:sum(len(message['content'])//4 for message in messages))
    scorer=SimpleNamespace(binding=dict(rule_sha256=plan.rule_sha256,top_k=50,reference_count=64,
        relevance=True,novelty=True,condition=plan.condition))
    scenes=[dict(contest_id='scene',canonical_scene='A crib.')]
    with Controller(tmp_path,plan,backend,scorer,scenes,extract_batches) as controller:
        outcomes=[dict(ordinal=number,rank=number,accepted=number<=50,status='new_pixel' if number<=50 else 'rejected',
            contest_id='opaque-id',relevance_score=.123456789123,relevance_threshold=.0123456789,
            reference_count=64,top_k=50) for number in range(1,101)]
        controller.state['history']=[dict(role='assistant',content='actual output '*800),
            dict(role='user',content='Actual environment feedback (data): '+json.dumps(dict(outcomes=outcomes,parsed=100)))]
        before=deepcopy(controller.state['history'])
        messages,removed=controller.messages('THINK')
        assert backend.count_tokens(messages)<=plan.context_tokens
        assert controller.state['history']==before and removed==1
        feedback=next(message['content'] for message in messages if 'Budgeted truthful projection' in message['content'])
        document=json.loads(feedback.split(': ',1)[1])
        assert document['total_outcomes']==100 and document['omitted_outcomes']==92
        assert document['accepted']==50 and document['new_pixels']==50 and document['outcomes'][0]['rank']==1
