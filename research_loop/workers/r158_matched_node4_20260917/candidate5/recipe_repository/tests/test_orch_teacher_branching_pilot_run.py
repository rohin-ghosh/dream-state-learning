"""Teacher runner/guardian CPU tests; all process/model operations are mocked."""

from contextlib import nullcontext
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import signal
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from gpu import orch_teacher_branching_pilot_run as run
from gpu import orch_teacher_branching_pilot_guard as guard


def allocation():
    return dict(status='ALLOCATED', authorized_by='Main', experiment='TEACHER_DISTILLATION_DOSE4', node='node1',
        devices=deepcopy(guard.DEVICES), prepare_sha256='prepared', manifest_sha256=run.MANIFEST_SHA,
        max_seconds=7200, gpu_hours=4, readout_calls=224, updates_per_cell=56,
        lease_end_unix=guard.node.LEASE_END)


def test_exact_handoff_pins_recipe_and_masks():
    assert run.sha(run.interface.__file__) == run.INTERFACE_SHA
    assert run.sha(run.pilot.__file__) == run.POLICY_SHA
    contract = run.contract()
    assert contract['teacher_rows'] == 16 and contract['updates_per_cell'] == 56
    assert contract['max_calls'] == 224 and contract['seconds'] == 7200
    assert contract['initial_state'] == run.pilot.STATE
    assert contract['recipe']['seed'] == 8203 and contract['recipe']['learning_rate'] == 3e-5
    assert sum(run.LIMITS.values()) == 112
    assert 2 * sum(run.LIMITS[key] * run.CAPS[key] for key in run.LIMITS) == 539648
    assert run.replay_arm('FULL') == 'FULL_TARGET'
    assert run.replay_arm('OFF') == 'NEW_TRAJECTORY_LOSS_OFF'


@pytest.mark.parametrize('key,value', [('status','CANDIDATE'),('authorized_by','Builder'),('node','A100'),
    ('experiment','CONTINUAL'),('prepare_sha256','other'),('manifest_sha256','other'),
    ('max_seconds',7201),('gpu_hours',5),('readout_calls',225),('updates_per_cell',224),
    ('lease_end_unix',guard.node.LEASE_END+1),('devices',{'FULL':dict(index=0,uuid='unknown')})])
def test_no_candidate_or_changed_allocation(key,value):
    with pytest.raises(ValueError):
        guard.allocation_fields(dict(allocation(),**{key:value}),'prepared')


def test_allocation_exact_uuid_and_lease_margin():
    guard.allocation_fields(allocation(),'prepared')
    assert guard.DEVICES['FULL']['index'] == 4 and guard.DEVICES['OFF']['index'] == 5
    assert guard.node.MINORS[4:6] == (7,6)
    started = guard.node.LEASE_END - 21600 - 10000
    clock = guard.lifetime(allocation(),started)
    assert clock['hard_deadline_unix'] == started+7200
    short = guard.lifetime(allocation(),guard.node.LEASE_END-21600-1000)
    assert short['hard_deadline_unix'] == guard.node.LEASE_END-21600
    with pytest.raises(ValueError,match='lease_margin'):
        guard.lifetime(allocation(),guard.node.LEASE_END-21600-10)


def test_missing_main_allocation_never_scans_or_launches(tmp_path,monkeypatch):
    monkeypatch.setattr(run,'owned_root',lambda root:None)
    monkeypatch.setattr(run,'validate_inputs',lambda root:dict(status='CPU_READY_NOT_ALLOCATED'))
    monkeypatch.setattr(guard.scanner,'host',lambda:None)
    spawn=Mock(side_effect=AssertionError('must_not_launch'))
    monkeypatch.setattr(guard.subprocess,'Popen',spawn)
    with pytest.raises(FileNotFoundError):
        guard.guard(tmp_path,'notallocated')
    assert not spawn.called and not (tmp_path/'LIFETIME.json').exists()


def test_single_shared_clock_cannot_restart(tmp_path,monkeypatch):
    monkeypatch.setattr(run,'owned_root',lambda root:None)
    monkeypatch.setattr(run,'validate_inputs',lambda root:{})
    monkeypatch.setattr(guard,'validate_allocation',lambda *args:allocation())
    (tmp_path/'LIFETIME.json').write_text('{"preserved":true}')
    with pytest.raises(ValueError,match='no_restart'):
        guard.guard(tmp_path,'registered')
    assert json.loads((tmp_path/'LIFETIME.json').read_text()) == {'preserved':True}


def test_full224_call_budget_failed_reservations_not_refunded(tmp_path):
    clock=dict(hard_deadline_unix=run.time.time()+1000)
    for cell in run.CELLS:
        for family,count in run.LIMITS.items():
            for position in range(count):
                path,record=run.reserve(tmp_path,cell,family,[dict(role='user',content='fixture')],dict(position=position),clock)
                assert record['status']=='RESERVED'
            with pytest.raises(ValueError):
                run.reserve(tmp_path,cell,family,[],{},clock)
    ledger=[json.loads(line) for line in (tmp_path/'CALL_LEDGER.jsonl').read_text().splitlines()]
    assert len(ledger)==224 and sum(entry['cap'] for entry in ledger)==539648
    assert len({entry['position'] for entry in ledger})==224


def test_expired_deadline_and_foreign_family_spend_nothing(tmp_path):
    with pytest.raises(ValueError,match='deadline'):
        run.reserve(tmp_path,'FULL','math',[],{},dict(hard_deadline_unix=0))
    with pytest.raises(ValueError,match='bucket'):
        run.reserve(tmp_path,'FULL','parent',[],{},dict(hard_deadline_unix=1e20))
    assert not (tmp_path/'CALL_LEDGER.jsonl').exists()


def test_strict_admission_preserves_failure_no_pid_waiver(tmp_path,monkeypatch):
    snapshot=dict(scanner_euid=0,clear=False,blocking_reasons=['active_compute'],
        created_utc=datetime.now(timezone.utc).isoformat())
    monkeypatch.setattr(guard.scanner,'scan',lambda *args:snapshot)
    monkeypatch.setattr(guard.scanner,'evaluate',lambda *args:['active_compute'])
    with pytest.raises(ValueError,match='no_waiver'):
        guard.admission(tmp_path,'FULL','fit',dict(config=dict(service_identity='/native/service')))
    assert run.read(tmp_path/'FULL_fit_ADMISSION.json') == snapshot


def test_signal_only_exact_own_identity(monkeypatch):
    child=SimpleNamespace(pid=123,poll=lambda:None)
    expected=dict(pid=123,uid=os.getuid(),pgid=123,sid=123,start_ticks='one')
    sent=Mock()
    monkeypatch.setattr(guard.os,'killpg',sent)
    monkeypatch.setattr(guard,'identity',lambda pid:dict(expected,start_ticks='reused'))
    with pytest.raises(ValueError,match='exact_owned'):
        guard.signal_owned(child,expected,signal.SIGTERM)
    assert not sent.called
    monkeypatch.setattr(guard,'identity',lambda pid:expected)
    assert guard.signal_owned(child,expected,signal.SIGTERM)
    sent.assert_called_once_with(123,signal.SIGTERM)


def test_math_prompt_is_minimal_without_exhaustion_or_teacher():
    messages=run.default_math_messages(dict(question='How many apples?'))
    assert len(messages)==2 and messages[-1]==dict(role='user',content='How many apples?')
    assert 'at least' not in messages[0]['content'].lower()
    assert not any(word in json.dumps(messages).lower() for word in ('branch','method','teacher','exhaust'))


def test_original_question_check_request_preserved_not_unelicited():
    task=dict(question='Solve x + 3 = 5 and check your result.')
    before=deepcopy(task)
    messages=run.default_math_messages(task)
    metadata=run.math_prompt_metadata(task)
    assert task==before and messages[-1]['content']==task['question']
    assert 'check' not in messages[0]['content'].lower()
    assert metadata['prompt_condition']=='MINIMAL_SYSTEM_TASK_CHECK_REQUEST_PRESERVED'
    assert metadata['spontaneous_branching_claim'] is False
    assert run.math_prompt_metadata(dict(question='What is 2+3?'))['prompt_condition']=='MINIMAL_SYSTEM_ORIGINAL_TASK_PRESERVED'


def evidence(text,part):
    start=text.index(part)
    return dict(start=start,end=start+len(part),text=part)


def annotation():
    text='Compute 2+3=5. Check: 5-3=2. Thus FINAL: 5.'
    result=dict(response_sha256=run.behavior.text_hash(text),full_output_read=True,reviewer='fixture-author',
        rubric_sha256=run.R106_SHA,departures_returns=[dict(main_line=evidence(text,'Compute 2+3=5.'),
            departure=evidence(text,'Check: 5-3=2.'),resumption=evidence(text,'Thus FINAL: 5.'),reason='check then return')],
        checks=[dict(evidence=evidence(text,'Check: 5-3=2.'),placement='TERMINAL',reason='check before final')],
        methods=[],coherence=dict(judgment='COHERENT',evidence=evidence(text,'Thus FINAL: 5.')))
    return text,result


def test_R106_check_branch_does_not_require_second_method():
    text,value=annotation()
    measured=run.author_annotation(text,value)
    assert measured['departures_returns']==1 and measured['methods']==0
    assert measured['terminal_checks']==1 and measured['mid_line_checks']==0
    assert not measured['training_allowed']


@pytest.mark.parametrize('change',['hash','span','order','duplicate','unread'])
def test_R106_bound_full_output_not_heading_count(change):
    text,value=annotation()
    if change=='hash': value['response_sha256']='wrong'
    if change=='span': value['checks'][0]['evidence']['text']='invented'
    if change=='order': value['departures_returns'][0]['resumption']=value['departures_returns'][0]['main_line']
    if change=='duplicate': value['departures_returns']*=2
    if change=='unread': value['full_output_read']=False
    with pytest.raises(ValueError): run.author_annotation(text,value)


def test_pending_semantics_not_zero_and_EOS_ceiling_exact():
    response=dict(raw='FINAL: 5',token_ids=[1,2,99],terminal=True,truncated=False)
    value=run.richness(response)
    assert value['tokens']['generated_tokens']==3 and value['tokens']['eos']
    assert value['R106']['departures_returns'] is None and value['R106']['methods'] is None
    assert not value['used_for_training']


class Loss:
    def __init__(self,value=1): self.value=value
    def __mul__(self,value): return Loss(self.value*value)
    def backward(self): pass
    def item(self): return self.value


@pytest.mark.parametrize('cell',['FULL','OFF'])
def test_actual_driver_executes_exact56_optimizer_updates_mocked_native(tmp_path,monkeypatch,cell):
    initial_path=tmp_path/'initial'; initial_path.mkdir()
    (initial_path/'weights').write_text('initial')
    identity=run.bridge.AdapterIdentity(str(initial_path),run.pilot.STATE,run.pilot.BASE,
                                      (('weights',run.sha(initial_path/'weights')),))
    prepared=dict(initial=identity.document(),model_dir='/mock/model',config=dict(manifest='unused'),
        totals=dict(full_reference=42207,full_active=42207,masked_reference=42207,masked_active=3839))
    (tmp_path/'PREPARE.json').write_text('{}')
    monkeypatch.setattr(run,'authorize_child',lambda *args:(prepared,dict(hard_deadline_unix=run.time.time()+1000),'mockUUID'))
    original_read=run.read
    monkeypatch.setattr(run,'read',lambda path:{} if str(path)=='unused' else original_read(path))
    layout=run.GoalReplayLayout(16,4)
    monkeypatch.setattr(run,'encoded_inputs',lambda *args:((),layout))
    monkeypatch.setattr(run.interface,'paired_batches',lambda *args:prepared['totals'])
    parameter=SimpleNamespace(grad=object())
    def save_model(path,**kwargs):
        path.mkdir(); (path/'weights').write_text('changed')
    model=Mock(side_effect=lambda **kwargs:SimpleNamespace(loss=Loss()))
    model.named_parameters=lambda:[('model.lora_A.default.weight',parameter)]
    model.save_pretrained=save_model
    optimizer=SimpleNamespace(zero_grad=Mock(),step=Mock(),state_dict=lambda:dict(steps=56))
    torch=SimpleNamespace(long='long',bfloat16='bf16',tensor=lambda values,**kwargs:values,
        autocast=lambda **kwargs:nullcontext(),isfinite=lambda value:SimpleNamespace(all=lambda:True),
        save=lambda value,path:path.write_text(json.dumps(value)))
    loaded=SimpleNamespace(engine=SimpleNamespace(torch=torch,model=model,device='mock',
        tokenizer=SimpleNamespace(pad_token_id=0),verify_base=Mock()),optimizer=optimizer,
        observed=identity,process=('mockboot',123,456))
    loader=Mock(return_value=loaded); monkeypatch.setattr(run.native,'load_training',loader)
    monkeypatch.setattr(run.native,'state_hash',lambda parameters:'1'*64)
    monkeypatch.setattr(run.native,'observe_adapter',lambda engine,saved:saved)
    def batch(encoded,unused,update,**kwargs):
        reference=753+int(update<=39)
        active=reference if cell=='FULL' else 68+int(update<=31)
        return layout.training_indexes(update),dict(input_ids=[[1]],labels=[[1]]),reference,active,active/reference
    monkeypatch.setattr(run.native,'training_batch',batch)
    run.fit(tmp_path,cell)
    complete=run.read(tmp_path/cell/'fit/COMPLETE.json')
    assert optimizer.step.call_count==56 and complete['updates']==56
    assert complete['reference_tokens']==42207 and complete['supervised_tokens']==(42207 if cell=='FULL' else 3839)
    assert complete['exposure_counts']==list(layout.presentation_counts())
    assert complete['training_generation_calls']==complete['parent_calls']==0
    assert not complete['continual_intake_allowed']
    assert run.read(tmp_path/cell/'fit/FIRST_UPDATE.json')['update']==1
    assert loader.call_args.kwargs['context']==run.native.StageContext()


def test_execution_commands_are_fresh_exec_and_bound_cells():
    for cell in run.CELLS:
        for phase in ('fit','readout'):
            cmd=guard.command(Path('/native/teacher'),cell,phase)
            assert cmd[:4]==[guard.PYTHON,'-B','-m',run.PROGRAM]
            assert cmd[-1]==cell and phase in cmd
    with pytest.raises(ValueError): guard.command(Path('/native'),'BASE','fit')


@pytest.mark.parametrize('fail_route',[False,True])
def test_readout_fresh_process_exact_caps_and_preserved_route_failure(tmp_path,monkeypatch,fail_route):
    from gpu import astra_goal_quality_train as old
    adapter=tmp_path/'adapter'; adapter.mkdir()
    (adapter/'weights').write_text('saved')
    identity=run.bridge.AdapterIdentity(str(adapter),'1'*64,run.pilot.BASE,
        (('weights',run.sha(adapter/'weights')),))
    fit=tmp_path/'FULL/fit'; fit.mkdir(parents=True)
    run.write(fit/'COMPLETE.json',dict(status='COMPLETE',updates=56,input_adapter='initial',
        output_adapter=identity.document(),process=['priorboot',12,34]))
    (tmp_path/'PREPARE.json').write_text('{}')
    tasks=[dict(id=str(position),question='What is 5? Check the result.',gold='5') for position in range(16)]
    run.write(tmp_path/'panel.json',dict(math_tasks=tasks,route_collections=['one','two']))
    run.write(tmp_path/'ready.json',dict(files={'SEALED_READOUT_INPUTS.json':dict(path=str(tmp_path/'panel.json'))}))
    run.write(tmp_path/'manifest.json',dict(legacy_refs={'LEGACY_READOUT.json':dict(path=str(tmp_path/'legacy.json'))}))
    run.write(tmp_path/'legacy.json',dict(old_bank=[dict(event='fact')],
        old_episodes=[dict(event=dict(raw='old'))],held={}))
    prepared=dict(initial='initial',model_dir='/mock/model',config=dict(
        interface_ready=str(tmp_path/'ready.json'),manifest=str(tmp_path/'manifest.json')))
    monkeypatch.setattr(run,'authorize_child',lambda *args:(prepared,
        dict(hard_deadline_unix=run.time.time()+1000),'mockUUID'))
    generated=[]
    def generate(messages,*,max_new_tokens):
        generated.append((messages,max_new_tokens))
        if fail_route and len(generated)==17:
            raise RuntimeError('preserve_route_failure')
        return dict(raw='FINAL: 5',token_ids=[5,99],terminal=True,truncated=False)
    loaded=SimpleNamespace(process=['newboot',56,78],observed=identity,
        engine=SimpleNamespace(generate=generate),verify_unchanged=Mock())
    loader=Mock(return_value=loaded)
    monkeypatch.setattr(run.native,'load_readout',loader)
    def routes(collections,generate,emit):
        for position in range(48):
            try:
                generate([dict(role='user',content='route')])
            except RuntimeError:
                pass
        return dict(actor_calls=48)
    monkeypatch.setattr(run.interface,'evaluate_routes',routes)
    def recall(events,generate,output,label):
        for position in range(32):
            generate([dict(role='user',content='memory')])
        return dict(count=32)
    def audit(held,generate,coached):
        for position in range(16):
            generate([dict(role='user',content='audit')])
        return dict(summary=dict(count=16))
    monkeypatch.setattr(old.memory,'recall',recall)
    monkeypatch.setattr(old.memory.audit,'collect_cases',audit)
    if fail_route:
        with pytest.raises(ValueError,match='generation_failures_preserved'):
            run.readout(tmp_path,'FULL')
        assert (tmp_path/'FULL/readout/FAILED.json').exists()
        assert not (tmp_path/'FULL/readout/COMPLETE.json').exists()
    else:
        run.readout(tmp_path,'FULL')
        result=run.read(tmp_path/'FULL/readout/COMPLETE.json')
        assert result['calls']==run.LIMITS and result['math_accuracy']['correct']==16
        assert result['math_richness']['author_semantics']=='PENDING_NOT_ZERO'
        assert set(result['elicitation_conditions'])=={'MINIMAL_SYSTEM_TASK_CHECK_REQUEST_PRESERVED'}
        assert not result['spontaneous_branching_claim']
        loaded.verify_unchanged.assert_called_once()
    assert loader.call_args.kwargs['predecessor_processes']==(('priorboot',12,34),)
    assert loader.call_args.kwargs['context']==run.native.StageContext()
    assert [cap for messages,cap in generated]==[4096]*64+[160]*48
    assert generated[0][0]==run.default_math_messages(tasks[0])
    assert len((tmp_path/'CALL_LEDGER.jsonl').read_text().splitlines())==112


def test_guardian_fresh_fit_then_readout_lifecycle_without_native_launch(tmp_path,monkeypatch):
    monkeypatch.setenv('CUDA_VISIBLE_DEVICES','')
    monkeypatch.setattr(run,'owned_root',lambda root:None)
    monkeypatch.setattr(run,'validate_inputs',lambda root:{})
    (tmp_path/'PREPARE.json').write_text('{}')
    monkeypatch.setattr(guard,'validate_allocation',lambda *args:allocation())
    monkeypatch.setattr(guard.signal,'signal',lambda *args:None)
    monkeypatch.setattr(guard.time,'sleep',lambda seconds:None)
    scans=[]
    def admission(root,cell,phase,prepared):
        scans.append((cell,phase))
        return 'admitted'
    monkeypatch.setattr(guard,'admission',admission)
    launched=[]
    def spawn(command,**kwargs):
        cell=command[-1]; phase=command[command.index('--phase')+1]
        if phase=='fit':
            assert scans[:2]==[('FULL','fit'),('OFF','fit')]
        else:
            assert (tmp_path/f'{cell}_fit_EXIT.json').exists()
        assert kwargs['start_new_session'] and kwargs['env']['CUDA_VISIBLE_DEVICES']==guard.DEVICES[cell]['uuid']
        output=tmp_path/cell/phase; output.mkdir(parents=True)
        run.write(output/'COMPLETE.json',dict(status='COMPLETE'))
        launched.append((cell,phase))
        return SimpleNamespace(pid=100+len(launched),returncode=0,poll=lambda:0)
    monkeypatch.setattr(guard.subprocess,'Popen',spawn)
    monkeypatch.setattr(guard,'identity',lambda pid:dict(pid=pid,uid=os.getuid(),pgid=pid,sid=pid))
    sent=Mock(side_effect=AssertionError('exited_children_must_not_be_signaled'))
    monkeypatch.setattr(guard.os,'killpg',sent)
    assert guard.guard(tmp_path,'allocation')=='COMPLETE'
    assert launched==[('FULL','fit'),('OFF','fit'),('FULL','readout'),('OFF','readout')]
    terminal=run.read(tmp_path/'TERMINAL.json')
    assert terminal['actual_reserved_calls']==0 and not terminal['continual_changed']
    assert not sent.called
