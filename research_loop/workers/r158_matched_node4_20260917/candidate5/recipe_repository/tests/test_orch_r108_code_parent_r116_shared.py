from copy import deepcopy
from pathlib import Path
from types import SimpleNamespace
import time

import pytest

from gpu import orch_r108_code_parent_r116_shared as client
from gpu import orch_r108_code_parent_r116_shared_run as lifecycle
from gpu import orch_r108_code_parent_r116_shared_ready as readiness


coordinator = client.coordinator


def reference(folder):
    output = {}
    for field in ('path', 'optimizer_path'):
        path = folder/(field+'.json')
        coordinator.write(path, dict(adapter={}, source_process=['cpu', 7, 9]))
        output[field] = str(path)
        output[field+'_sha256'] = coordinator.sha(path)
    return output


def response(messages=None):
    return dict(messages=messages or [{'role':'user', 'content':'CPU task'}],
        raw='thought', prompt_tokens=2, token_ids=[7, 9], terminal=True,
        truncated=False, input_truncated=False)


@pytest.fixture
def setup(tmp_path_factory, monkeypatch):
    tmp_path = tmp_path_factory.mktemp('code_shared')
    specs = {branch:dict(root=str(tmp_path/branch), train_ids=[branch+'-one', branch+'-two'])
        for branch in coordinator.BRANCHES}
    initial = reference(tmp_path/'initial')
    old_path = tmp_path/'F1/old.json'
    old = dict(task_id='F1-one', phase='episode', response=response())
    coordinator.write(old_path, old)
    history = client.causal.replay_row(old, old_path, coordinator.sha(old_path))
    prior = dict(optimizer_steps=113, child_token_exposures=None, anchor_token_exposures=700)
    common = tmp_path/'common'
    coordinator.initialize(common, specs, initial, prior_metrics=prior,
        initial_history={'F1':[history]}, excluded_ids=['DEV1', 'FINAL1'])
    bounds = dict(started_unix=100, hard_deadline_unix=time.time()+3600,
        lease_end_unix=time.time()+7200, native_cap=100, parent_cap=100, cycles=20)
    adoption = tmp_path/'ADOPTION.json'
    coordinator.write(adoption, dict(checkpoint=initial, prior_metrics=prior,
        branch_bounds={branch:bounds for branch in ('F3','A3')}))
    plans = {}
    for branch, slot in [('F3',2), ('A3',6)]:
        root = tmp_path/branch
        cohort = dict(TRAIN=[dict(task_id=value, split='TRAIN',content_sha256='a'*64) for value in specs[branch]['train_ids']],
            DEV=[dict(task_id='DEV1', split='DEV')], FINAL=[dict(task_id='FINAL1', split='FINAL')])
        coordinator.write(root/'COHORT.json', cohort)
        plans[branch] = dict(bounds, physical=slot, gpu_uuid='CPU_ONLY', life_id=branch,
            model_dir=str(tmp_path),cohort_sha256=client.run.policy.digest(cohort),shared_learner=dict(branch=branch, root=str(common),
                config_sha256=coordinator.sha(common/'CONFIG.json'), adoption_path=str(adoption),
                adoption_sha256=coordinator.sha(adoption)))
        coordinator.write(root/'PLAN.json', plans[branch])
    monkeypatch.setenv('CUDA_VISIBLE_DEVICES','CPU_ONLY')
    session = client.Session(tmp_path/'F3', plans['F3'])
    session.loaded = True
    return SimpleNamespace(root=tmp_path/'F3', common=common, session=session,
        plans=plans, initial=initial, old=old_path, history=history, prior=prior)


def driver(setup, before=None, fail=False):
    class Engine:
        def generate(self, messages, *, max_new_tokens):
            if before:
                before()
            if fail:
                raise RuntimeError('operational')
            return response(messages)

    return client.Driver(setup.root, Engine(), setup.session)


@pytest.mark.parametrize('phase', ['episode','reflection','presleep','open_turn','open_observation'])
def test_actual_generation_and_checkpoint_written_before_dispatch(setup, phase):
    path = setup.root/'reservations/CAPTURE.json'

    def inspect():
        stored = coordinator.read(path)
        assert stored['status'] == 'STARTED'
        assert type(stored['shared_generation']) is int and stored['shared_generation'] == 0
        assert stored['shared_checkpoint_sha256'] == setup.initial['path_sha256']
        assert stored['shared_learner'] == setup.session.capture_binding()
        assert stored['task_id'] == 'F3-one' and stored['split'] == 'TRAIN'

    actor = driver(setup, inspect)
    call = actor.capture('CAPTURE', dict(task_id='F3-one', split='TRAIN'), phase, 1,
        [{'role':'user','content':'Actual environment feedback'}], 128)
    row = client.replay_row(call, path, coordinator.sha(path), spec=setup.session.spec,
        exclusions=['DEV1','FINAL1'], generation=0, checkpoint_sha256=setup.initial['path_sha256'])
    assert row['student_prefix'] == call['response']['messages']
    assert actor.cycle_sources[1] == [path]
    assert row['source_generated_token_ids'] == [7,9]


@pytest.mark.parametrize('split,origin', [('DEV',None), ('FINAL',None), ('TRAIN','DEV')])
def test_held_and_readout_attached_open_never_replayed(setup, split, origin):
    actor = driver(setup)
    call = actor.capture('READOUT_OPEN', dict(task_id='F3-one',split=split), 'open_observation', 1,
        [{'role':'user','content':'readout'}],128,evaluation_origin=origin)
    assert actor.cycle_sources == {} and call['routes']['sleep'] is False
    assert 'shared_generation' not in call


@pytest.mark.parametrize('field,value', [('shared_generation',None),('shared_generation',True),
    ('shared_generation',1),('shared_checkpoint_sha256','b'*64)])
def test_missing_or_wrong_actual_binding_rejected_without_rewriting(setup, field, value):
    call = dict(kind='NATIVE', status='COMPLETE', split='TRAIN', phase='episode',
        task_id='F3-one', response=response(), **setup.session.capture_metadata())
    call[field] = value
    path = setup.root/'invalid.json'
    coordinator.write(path,call)
    digest = coordinator.sha(path)
    with pytest.raises(ValueError):
        client.replay_row(call,path,digest,spec=setup.session.spec,exclusions=[],generation=0,
            checkpoint_sha256=setup.initial['path_sha256'])
    assert coordinator.sha(path) == digest


def test_failure_preserved_not_submitted_or_retried(setup):
    actor = driver(setup,fail=True)
    task = dict(task_id='F3-one',split='TRAIN')
    call = actor.capture('FAILED',task,'episode',1,[],128)
    assert call['status'] == 'FAILED' and call['shared_generation'] == 0
    assert actor.cycle_sources == {}
    with pytest.raises(ValueError, match='no_call_retry'):
        actor.capture('FAILED',task,'episode',1,[],128)


def test_nonowner_barrier_reload_preserves_counters_and_F1_history(setup):
    actor = driver(setup)
    for index, identifier in enumerate(setup.session.spec['train_ids']):
        actor.capture('C'+str(index),dict(task_id=identifier,split='TRAIN'),'episode',1,[],128)
    initial_bytes = setup.old.read_bytes()
    next_ref = reference(setup.root.parent/'next')
    reloads=[]

    def finish(seconds):
        old = coordinator.read(setup.common/'STATE.json')
        metrics = dict(optimizer_steps=257,child_token_exposures=514,anchor_token_exposures=257)
        state = dict(old,generation=1,checkpoint=next_ref)
        for key,value in metrics.items():
            state[key] = None if old[key] is None else old[key]+value
            state['shared_'+key] = old['shared_'+key]+value
        coordinator.write(setup.common/'generation_000000/sleep/COMPLETE.json',dict(state=state,metrics=metrics))
        coordinator.write(setup.common/'STATE.json',state,replace=True)

    result = actor.finish_cycle(1,setup.session.spec['train_ids'],lambda phase:None,
        pause=finish,reload_call=lambda engine,checkpoint:reloads.append(checkpoint),
        train_call=lambda *args:pytest.fail('CODE must never train'))
    assert reloads == [next_ref] and result['local_optimizer_steps'] == 0
    assert result['adopted_plus_shared_totals']['optimizer_steps'] == 370
    assert result['adopted_plus_shared_totals']['child_token_exposures'] is None
    assert setup.session.capture_metadata()['shared_generation'] == 1
    assert setup.old.read_bytes() == initial_bytes
    assert coordinator.read(setup.common/'CONFIG.json')['initial_history']['F1'] == [setup.history]


def test_original_lifetime_and_optimizer_owner_cannot_change(setup):
    plan = deepcopy(setup.plans['F3'])
    plan['native_cap'] += 1
    with pytest.raises(ValueError,match='bounds_no_reset'):
        client.Session(setup.root,plan)
    with pytest.raises(ValueError,match='optimizer_only'):
        setup.session.sleep(None,object(),[],[],['F3-one','F3-two'],setup.root/'bad',None,lambda phase:None)


def test_shared_decoder_forbids_trainable_or_missing_adapter():
    model = SimpleNamespace(peft_config={'default':{}},parameters=lambda:iter([SimpleNamespace(requires_grad=False)]))
    client.readonly_shared(model)
    model.parameters = lambda:iter([SimpleNamespace(requires_grad=True)])
    with pytest.raises(ValueError,match='no_local_training'):
        client.readonly_shared(model)
    model.peft_config = {}
    with pytest.raises(ValueError,match='one_shared_adapter'):
        client.readonly_shared(model)


def test_loader_binds_checkpoint_predecessor_and_nonreplacing_guard(setup, monkeypatch):
    observed = object()
    monkeypatch.setattr(client.native.bridge.AdapterIdentity,'from_document',lambda document:observed)
    checked=[]

    def load(binding, **kwargs):
        assert binding.cycle == 0 and binding.phase == 'collection'
        assert kwargs['predecessor_processes'] == (('cpu',7,9),)
        assert kwargs['check']('forward') is None
        return SimpleNamespace(optimizer=None,observed=observed,engine=object())

    monkeypatch.setattr(client.native,'load_stage',load)
    setup.session.load_engine(setup.plans['F3'],lambda phase:checked.append(phase) or {'plan':True})
    assert checked == ['forward']


def test_actual_two_episode_loop_submits_only_after_metacognition(setup, monkeypatch):
    actor = driver(setup)
    events=[]

    def episode(actual, task, ordinal, index):
        assert actual is actor
        events.append(('episode',task['task_id']))
        actual.capture('EP'+str(index),task,'episode',ordinal,[],128)
        return [dict(actor='child',text='My actual task work.')]

    def parent(*args):
        events.append(('parent',args[-1]))
        return 'Notice what you chose.'

    def finish(ordinal, ids, check):
        events.append(('barrier',ids))
        assert len(actor.cycle_sources[ordinal]) == 4
        return {'status':'COMPLETE'}

    monkeypatch.setattr(lifecycle.run,'episode',episode)
    monkeypatch.setattr(actor,'parent',parent)
    monkeypatch.setattr(actor,'finish_cycle',finish)
    tasks=coordinator.read(setup.root/'COHORT.json')['TRAIN']
    assert lifecycle.cycle(actor,tasks,1)['status'] == 'COMPLETE'
    assert events == [('episode','F3-one'),('episode','F3-two'),
        ('parent','presleep_metacognition'),('barrier',['F3-one','F3-two'])]


def test_pinned_fresh_evaluation_has_metadata_but_no_parent_or_replay(setup):
    actor=lifecycle.ReadoutDriver(setup.root,driver(setup).engine,setup.session)
    call=actor.capture('DEV_CAPTURE',dict(task_id='DEV1',split='DEV'),'open_observation',1,[],128,
        evaluation_origin='DEV')
    assert call['shared_generation'] == 0
    assert call['shared_checkpoint_sha256'] == setup.initial['path_sha256']
    assert not call['routes']['sleep'] and not call['routes']['parent']
    assert actor.sleep_buffer == []
    with pytest.raises(ValueError,match='evaluation_only'):
        actor.reserve('PARENT','PARENT',split='TRAIN',phase='episode',cycle=1)


def test_readout_schedule_freezes_reference_and_explicit_module(setup,monkeypatch):
    commands=[]
    monkeypatch.setattr(lifecycle.subprocess,'Popen',lambda command,**kwargs:commands.append(command) or object())
    lifecycle.schedule_readout(setup.root,setup.session,1,'DEV')
    stored=coordinator.read(setup.root/'shared_readout_bindings/C001_DEV.json')
    setup.session.state['generation']=5
    assert stored['state']['generation'] == 0
    assert commands[0][3] == 'gpu.orch_r108_code_parent_r116_shared_run'
    with pytest.raises(ValueError,match='no_initial'):
        lifecycle.schedule_readout(setup.root,setup.session,1,'ZERO')


def test_readiness_preserves_original_plan_and_never_initializes_shared(setup,tmp_path,monkeypatch):
    original=(setup.root/'PLAN.json').read_bytes()
    source=tmp_path/'candidate'
    for name in readiness.SOURCE_FILES:
        coordinator.write(source/name,{'CPU':'fixture'})
    tests=tmp_path/'CPU_TESTS.json'
    coordinator.write(tests,dict(passed=True,cuda_initialized=False,
        source_files={name:coordinator.sha(source/name) for name in readiness.SOURCE_FILES}))
    monkeypatch.setattr(readiness,'COMMON_ROOT',str(tmp_path/'not_initialized'))
    result=readiness.publish(setup.root,source,tests)
    assert result['branch'] == 'F3' and result['active_shared_client'] is False
    assert result['ready_for_initialization'] is True and result['optimizer_owner'] == 'F1'
    assert 'open_observation' in result['training_phases']
    assert set(result['excluded_ids']) == {'DEV1','FINAL1'}
    assert (setup.root/'PLAN.json').read_bytes() == original
    assert not Path(readiness.COMMON_ROOT).exists()


def test_activation_rejects_caps_reset(setup):
    original=setup.plans['F3']
    activation=dict(predecessor_plan_sha256=coordinator.sha(setup.root/'PLAN.json'),
        inherited_bounds={key:original[key] for key in client.BOUND_FIELDS},
        shared_learner=original['shared_learner'])
    coordinator.write(setup.root/'SHARED_ACTIVATION.json',activation)
    assert lifecycle.activation_plan(setup.root)['shared_learner'] == original['shared_learner']
    activation['inherited_bounds']['parent_cap']+=1
    coordinator.write(setup.root/'SHARED_ACTIVATION.json',activation,replace=True)
    with pytest.raises(ValueError,match='original_lifetime'):
        lifecycle.activation_plan(setup.root)
