"""Separately bounded R109 BASE CODE cadence lives; no old quota reset."""

import argparse
from collections import Counter
import json
import os
from pathlib import Path
import subprocess
import time

from gpu import orch_r108_code_parent_run as prior
from gpu import orch_r108_code_parent_r109_scan as admission
from organism_v6 import orch_r108_code_parent_r109 as policy


ROOT=Path('/localhome/local-rohing/orch_r108_code_parent_r110_20260915_attempt1')
LANE='campaign_code_parent'
QUEUE='code_parent_queue'
read,write,sha,common=prior.read,prior.write,prior.sha,prior.common


def verify(root,arm):
    config=policy.allocation(arm)
    policy.require(root==ROOT and root.resolve()==root and common.host_identity()==config['host_sha256'], 'exact_r109_root_host')
    for relative,expected in read(root/'SOURCE_SHA256.json').items():
        path=Path(relative)
        policy.require(not path.is_absolute() and '..' not in path.parts and sha(root/'source'/path)==expected,'frozen_r109_source')
    return config


def lifetime(config,lease_end):
    hard=min(policy.HARD_END,lease_end-21600)
    return dict(started_unix=policy.START,native_deadline_unix=hard-120,hard_deadline_unix=hard,
        lease_end_unix=lease_end,gpu_hours_cap=8,native_cap=config['native_cap'],parent_cap=config['parent_cap'])


def check_lifetime(value,arm,now):
    config=policy.allocation(arm)
    policy.require(value==lifetime(config,value['lease_end_unix'])
        and value['started_unix']<=now<value['native_deadline_unix'], 'fixed_r109_lifetime_no_reset')


def prepare(root,arm):
    config=verify(root,arm)
    policy.require(os.environ.get('CUDA_VISIBLE_DEVICES')=='' and not (root/'READY.json').exists(),'fresh_cpu_prepare')
    inputs=read(root/'DEPLOY_INPUTS.json')
    policy.require(inputs['arm']==arm and read(root/'CPU_TESTS.json')['passed'] is True,'bound_arm_cpu')
    tasks=policy.tasks(arm)
    cohort=policy.validate_cohort(tasks,read(root/'EXCLUSIONS.json'),arm)
    metadata,context=prior.anchors.common.metadata(inputs['model_dir'])
    policy.require(context>=policy.CONTEXT,'original_context_support')
    tokenizer=prior.anchors.common.native.source.native.load_local_tokenizer(inputs['model_dir'])
    lengths=[len(tokenizer.apply_chat_template(policy.messages(task),tokenize=True,add_generation_prompt=True,return_dict=False)) for task in tasks]
    policy.require(max(lengths)+2048<=policy.CONTEXT,'initial_full_prompt_bounds')
    engine=prior.Engine(inputs['model_dir'],tokenizer,device='cpu',check=lambda label:None)
    base=dict(base_sha256=engine.loaded_base_sha256,no_adapter=prior.assert_no_adapter(engine.model),runtime=engine.runtime,
        native_calls=0,updates=0)
    del engine
    bound=lifetime(config,inputs['lease_end_unix'])
    check_lifetime(bound,arm,time.time())
    write(root/'COHORT_PRIVATE.json',tasks)
    write(root/'RESERVATIONS.json',policy.schedule(tasks,arm))
    write(root/'LIFETIME.json',bound)
    write(root/'BASE_CPU_IDENTITY.json',base)
    (root/LANE).mkdir(exist_ok=False)
    (root/LANE/QUEUE).mkdir()
    ready=dict(schema=policy.VERSION,arm=arm,config=config,base_sha256=policy.BASE_SHA,model_dir=inputs['model_dir'],
        model_metadata=metadata,cohort=cohort,parent_files=read(root/'PROVIDER_FILES.json'),
        context=policy.CONTEXT,output_cap=2048,thought_segment1_cap=512,
        principles_sha256=sha(root/'PARENTING_PRINCIPLES.md'),
        files={name:sha(root/name) for name in ('SOURCE_SHA256.json','DEPLOY_INPUTS.json','CPU_TESTS.json',
            'COHORT_PRIVATE.json','RESERVATIONS.json','LIFETIME.json','BASE_CPU_IDENTITY.json','EXCLUSIONS.json','PROVIDER_FILES.json','PARENTING_PRINCIPLES.md')},
        no_adapter=True,updates=0,automatic_fit=False,retained_weight_learning_claim=False)
    write(root/'READY.json',ready)
    write(root/LANE/'READY.json',ready)
    return dict(ready_sha256=sha(root/'READY.json'),lifetime=bound,config=config,base_cpu=base,cohort=cohort)


def validate(root,arm):
    verify(root,arm)
    ready=read(root/'READY.json')
    policy.require(ready['arm']==arm and ready['config']==policy.allocation(arm),'ready_arm')
    for name,expected in ready['files'].items():
        policy.require(sha(root/name)==expected,'prepared_input_drift')
    check_lifetime(read(root/'LIFETIME.json'),arm,time.time())
    publication=read(root/'PUBLICATION.json')
    policy.require(publication['ready_sha256']==sha(root/'READY.json') and publication['own_cpu_tests_passed'] is True
        and publication['dated_builder_publication'] and publication['board_allocation'],'published_before_dispatch')
    return ready


def begin(root,task,phase):
    selected=next((row for row in read(root/'RESERVATIONS.json') if row['task_id']==task['task_id'] and row['phase']==phase),None)
    policy.require(selected is not None,'fixed_reservation_required')
    path=root/LANE/'cells'/(selected['cell_id']+'.json')
    path.parent.mkdir(exist_ok=True)
    record=dict(selected,status='STARTED',started_unix=time.time())
    with path.open('x') as stream:
        json.dump(record,stream,sort_keys=True)
        stream.flush()
        os.fsync(stream.fileno())
    return path,record


def generate(root,engine,task,phase,messages,check):
    check('native_dispatch')
    path,record=begin(root,task,phase)
    try:
        tokens=engine.tokenizer.apply_chat_template(messages,tokenize=True,add_generation_prompt=True,return_dict=False)
        is_reflection=phase.startswith(('reflection','meta_child'))
        cap=min(512 if phase=='segment1' else getattr(engine,'reflection_cap',2048) if is_reflection else 2048,
            policy.prior.token_budget(len(tokens)))
        response=engine.generate(messages,max_new_tokens=cap,reflection=is_reflection)
        if phase=='segment1':
            outcome=dict(failure_class='observable_work_in_progress',scored_as_final=False,
                terminal=response['terminal'],truncated=response['truncated'],generated_tokens=len(response['token_ids']))
        elif is_reflection:
            outcome=dict(failure_class='own_reflection_unreviewed',reflection_guard=response.get('reflection_guard'))
        else:
            outcome=policy.outcome(task,response)
        record.update(response=response,outcome=outcome,status='COMPLETE')
    except BaseException as error:
        record.update(status='FAILED',error_type=type(error).__name__)
        raise
    finally:
        record['finished_unix']=time.time()
        write(path,record)
    return record


def parent(root,arm,task,segment,records,memory,lessons,check,payload=None):
    check('parent_dispatch')
    path,record=begin(root,task,('meta_parent' if task['slot']==0 else 'parent')+str(segment))
    identifier=f'GUIDED_SLEEP_C{task["cycle"]}_P{task["slot"]}_S{segment}'
    request=root/LANE/QUEUE/(identifier+'.request.json')
    payload=payload if payload is not None else policy.parent_payload(arm,task,segment,records,memory,lessons)
    policy.validate_parent_payload(payload)
    write(request,dict(id=identifier,payload=payload,payload_sha256=policy.digest(payload),ready_sha256=sha(root/'READY.json')))
    until=min(time.time()+300,read(root/'LIFETIME.json')['native_deadline_unix'])
    response=request.with_name(identifier+'.response.json')
    try:
        while not response.exists():
            check('parent_wait')
            policy.require(time.time()<until,'parent_timeout_no_retry')
            time.sleep(2)
        result=read(response)
        policy.require(result['status']=='COMPLETE' and result['request_sha256']==sha(request),'actual_astra_request_join')
        directory=Path(result['archive']['remote_root'])
        policy.require(directory.is_relative_to(root/'parent_transcripts'/LANE),'own_native_archive')
        for name,expected in result['archive']['files'].items():
            policy.require(not Path(name).is_absolute() and '..' not in Path(name).parts and sha(directory/name)==expected,'archive_hash')
        plan=prior.parse_parent(read(directory/'RAW_RESPONSE.json'),[task['task_id']])
        policy.require(plan==result['plan']==read(directory/'PLAN.json'),'actual_astra_response')
        record.update(status='COMPLETE',lesson=policy.prior.parent_lesson(plan,task),result=result,
            declared_intervention_classes=policy.declared_classes(plan),classes_are_self_declared_not_semantic_audit=True)
        record['declared_behavior_operation']=policy.declared_operation(plan)
    except BaseException as error:
        record.update(status='FAILED',error_type=type(error).__name__)
        raise
    finally:
        record['finished_unix']=time.time()
        write(path,record)
    return record


def reflection(root,engine,task,segment,records,intervention,memory,check):
    messages=[dict(role='system',content=policy.prior.REFLECTION_SYSTEM),dict(role='user',content=json.dumps(dict(
        actual_train_prompt=task['prompt'],actual_own_segments=[row['response']['raw'] for row in records],
        actual_parent_message=intervention['lesson'],prior_own_reflection=memory),sort_keys=True))]
    return generate(root,engine,task,'reflection'+str(segment),messages,check)


def save_triple(root,arm,task,segment,before,intervention,reflection_row,after):
    value=policy.prior.triple(task,before,intervention,reflection_row,after)
    value.update(arm=arm,cadence=policy.allocation(arm)['cadence'],segment=segment,
        declared_intervention_classes=intervention['declared_intervention_classes'],
        declared_behavior_operation=intervention.get('declared_behavior_operation','UNDECLARED'),
        classes_are_self_declared_not_semantic_audit=True,
        reflection_is_continuation=task['slot']==0,semantic_compiler_used=False)
    write(root/LANE/f'TRIPLE_C{task["cycle"]:03d}_E{task["slot"]}_S{segment}.json',value)


def meta_dialogue(root,arm,engine,cycle,before,memory,lessons,check,parent_call):
    task=policy.meta_task(arm,cycle)
    dialogue=[]
    initial_sha=policy.digest(memory)
    for round_number in range(1,4):
        payload=policy.meta_payload(arm,task,round_number,memory,dialogue,lessons)
        intervention=parent_call(root,arm,task,round_number,[],memory,lessons,check,payload=payload)
        lessons.append(intervention['lesson'])
        messages=[dict(role='system',content='Pure metacognitive context-distillation dialogue. Reflect on importance, '
            'how you allocated effort, context leaving, your self/capability perception, reflections and your own '
            'context-based learning system. Carry useful prior learning while remaining honest about uncertainty. '
            'Do not solve the CODE task, invent experience, or claim weight learning: weights are frozen. '
            'No semantic compiler, fixed format, minimum length or padding.'),dict(role='user',content=json.dumps(dict(
                own_prior_context_reflection=memory,actual_dialogue=dialogue,actual_parent=intervention['lesson']),sort_keys=True))]
        child=generate(root,engine,task,'meta_child'+str(round_number),messages,check)
        save_triple(root,arm,task,round_number,before,intervention,child,child)
        dialogue.append(dict(parent=intervention['lesson'],child=child['response']['raw']))
        before=child
        memory=child['response']['raw']
    write(root/LANE/f'CONTEXT_DISTILLATION_C{cycle:03d}.json',dict(status='COMPLETE',parent_rounds=3,child_rounds=3,
        own_context=memory,before_context_sha256=initial_sha,after_context_sha256=policy.digest(memory),
        reflection_cap=engine.reflection_cap,semantic_compiler_used=False,weight_updates=0,
        continuous_resident=True,context_distillation_not_weight_sleep=True,finished_unix=time.time()))
    return memory


def cycles(root,arm,engine,check,parent_call=parent):
    memory,lessons='',[]
    config=policy.allocation(arm)
    engine.reflection_cap=config['reflection_cap']
    tasks=read(root/'COHORT_PRIVATE.json')
    for cycle in range(1,policy.CYCLES+1):
        held=[]
        for task in [row for row in tasks if row['cycle']==cycle]:
            if task['split']=='HELD':
                row=generate(root,engine,task,'held',policy.messages(task,memory),check)
                held.append(dict(task_id=task['task_id'],outcome=row['outcome'],parent_free=True,
                    direct_parent_text=False,own_train_reflection_carried=True,sealed_from_parent=True))
                continue
            messages=policy.messages(task,memory)+[dict(role='user',content='Generate one bounded work-in-progress reasoning segment about this task. Stop after that observable segment; you will continue. A final answer is not required yet. Do not invent branches or pad.')]
            first=generate(root,engine,task,'segment1',messages,check)
            messages += [dict(role='assistant',content=first['response']['raw'])]
            early_parent=early_reflection=None
            if config['cadence']=='EVERY_GENERATED_SEGMENT':
                early_parent=parent_call(root,arm,task,1,[first],memory,lessons,check)
                lessons.append(early_parent['lesson'])
                early_reflection=reflection(root,engine,task,1,[first],early_parent,memory,check)
                messages += [dict(role='user',content='Actual parent guidance:\n'+early_parent['lesson']+
                    '\nYour own reflection:\n'+early_reflection['response']['raw'])]
            messages += [dict(role='user',content='Continue with your second observable reasoning segment and your attempted solution. Final nonempty line: {"expression":"..."}.')]
            second=generate(root,engine,task,'segment2',messages,check)
            if early_parent:
                save_triple(root,arm,task,1,first,early_parent,early_reflection,second)
            intervention=parent_call(root,arm,task,2,[first,second],memory,lessons,check)
            lessons.append(intervention['lesson'])
            reflected=reflection(root,engine,task,2,[first,second],intervention,memory,check)
            messages += [dict(role='assistant',content=second['response']['raw']),dict(role='user',content=
                'Actual parent guidance:\n'+intervention['lesson']+'\nYour own reflection:\n'+reflected['response']['raw']+
                '\nContinue this TRAIN task. Retain or revise your solution. Final nonempty line: {"expression":"..."}.')]
            continuation=generate(root,engine,task,'continuation',messages,check)
            save_triple(root,arm,task,2,second,intervention,reflected,continuation)
            memory=reflected['response']['raw']
            if task['slot']==2:
                memory=meta_dialogue(root,arm,engine,cycle,reflected,memory,lessons,check,parent_call)
        engine.verify_base()
        write(root/LANE/f'CYCLE_{cycle:03d}_COMPLETE.json',dict(cycle=cycle,status='COMPLETE',finished_unix=time.time(),
            held=held,train_episodes=2,no_adapter=prior.assert_no_adapter(engine.model),updates=0))
        status(root,arm)


def status(root,arm):
    lane=root/LANE
    cells=[read(path) for path in (lane/'cells').glob('*.json')]
    counts=Counter((row['kind'],row['status']) for row in cells)
    classes=Counter(label for row in cells for label in row.get('declared_intervention_classes',[]))
    operations=Counter(row['declared_behavior_operation'] for row in cells if 'declared_behavior_operation' in row)
    tokens=Counter()
    for row in cells:
        tokens[row['phase']]+=len(row.get('response',{}).get('token_ids',[]))
    value=dict(observed_unix=time.time(),arm=arm,native_started=sum(row['kind']=='NATIVE' for row in cells),
        parent_started=sum(row['kind']=='PARENT' for row in cells),native_complete=counts['NATIVE','COMPLETE'],
        parent_complete=counts['PARENT','COMPLETE'],cycles_complete=len(list(lane.glob('CYCLE_*_COMPLETE.json'))),
        triples=len(list(lane.glob('TRIPLE_*.json'))),declared_intervention_classes=dict(classes),
        declared_behavior_operations=dict(operations),generated_tokens_by_phase=dict(tokens),
        context_distillation_cycles=len(list(lane.glob('CONTEXT_DISTILLATION_*.json'))),
        semantic_helpfulness='UNREVIEWED',updates=0,retained_weight_learning_claim=False)
    write(lane/'STATUS.json',value)
    return value


def native(root,arm):
    ready=validate(root,arm)
    config=policy.allocation(arm)
    policy.require(os.environ.get('CUDA_VISIBLE_DEVICES')==config['uuid'],'exact_uuid_cvd')
    lane=root/LANE
    write(lane/'NATIVE_REQUEST.json',dict(process=common.process_identity(Path('/proc')/str(os.getpid())),
        started_unix=time.time(),ready_sha256=sha(root/'READY.json'),arm=arm))
    bound=read(root/'LIFETIME.json')
    engine,failure,finalized=None,None,False
    def check(label):
        policy.require(time.time()<(bound['hard_deadline_unix']-30 if finalized else bound['native_deadline_unix']), 'fixed_bound:'+label)
    try:
        tokenizer=prior.anchors.common.native.source.native.load_local_tokenizer(ready['model_dir'])
        engine=prior.Engine(ready['model_dir'],tokenizer,device='cuda:0',check=check)
        write(lane/'BEFORE.json',dict(base_sha256=engine.loaded_base_sha256,no_adapter=prior.assert_no_adapter(engine.model),updates=0,
            ready_unix=time.time(),runtime=engine.runtime))
        cycles(root,arm,engine,check)
    except BaseException as error:
        failure=error
    finally:
        finalized=True
        try:
            policy.require(engine is not None,'loaded_base_required')
            engine.verify_base()
            policy.require(prior.anchors.common.metadata(ready['model_dir'])[0]==ready['model_metadata'],'after_metadata')
            write(lane/'AFTER.json',dict(status='PASS',base_sha256=policy.BASE_SHA,no_adapter=prior.assert_no_adapter(engine.model),updates=0))
        except BaseException as error:
            failure=failure or error
            write(lane/'AFTER.json',dict(status='FAILED',error_type=type(error).__name__))
        value=status(root,arm)
        value.update(status='FAILED' if failure else 'COMPLETE',error_type=type(failure).__name__ if failure else None)
        write(lane/('FAILED.json' if failure else 'COMPLETE.json'),value)
    if failure:
        raise failure


def previous_released(root):
    inputs=read(root/'DEPLOY_INPUTS.json')
    previous=Path(inputs['previous_lane'])
    if not (previous/'TERMINAL.json').exists():
        return False
    identities=[]
    if (previous/'ACTIVATION.json').exists():
        identities.append(read(previous/'ACTIVATION.json')['guardian'])
    for path in previous.glob('LAUNCH*.json'):
        value=read(path)
        if 'identity' in value:
            identities.append(value['identity'])
    for identity in identities:
        try:
            if common.process_identity(Path('/proc')/str(identity['pid']))==identity:
                return False
        except FileNotFoundError:
            pass
    return True


def guard(root,arm):
    ready=validate(root,arm)
    policy.require(os.environ.get('CUDA_VISIBLE_DEVICES')=='','cpu_guard_only')
    lane=root/LANE
    (lane/'GUARD_ONCE').mkdir(exist_ok=False)
    child=identity=None
    result='FAILED'
    bound=read(root/'LIFETIME.json')
    try:
        while not previous_released(root):
            policy.require(time.time()<bound['native_deadline_unix'],'natural_release_deadline')
            time.sleep(15)
        deadline=min(time.time()+600,bound['native_deadline_unix'])
        snapshot=None
        for attempt in range(200):
            policy.require(time.time()<deadline,'strict_admission_window')
            snapshot=admission.scan(root,arm)
            write(lane/f'ADMISSION_{attempt:03d}.json',snapshot)
            if snapshot['clear'] is True:
                break
            policy.require(prior.anchors.rescan.transient(snapshot),'real_ownership_block')
            time.sleep(3)
        policy.require(snapshot is not None and snapshot['clear'] is True and snapshot['scanner_euid']==0,'privileged_clear')
        write(lane/'ADMISSION.json',snapshot)
        with (lane/'native.log').open('x') as log:
            child=subprocess.Popen([common.PYTHON,'-B','-m','gpu.orch_r108_code_parent_r109_run','native','--root',str(root),'--arm',arm],
                cwd=root/'source',start_new_session=True,stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,
                env=dict(os.environ,CUDA_VISIBLE_DEVICES=ready['config']['uuid'],PYTHONPATH=str(root/'source'),
                    PYTHONDONTWRITEBYTECODE='1',HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',OMP_NUM_THREADS='1',MKL_NUM_THREADS='1'))
        identity=common.process_identity(Path('/proc')/str(child.pid))
        write(lane/'LAUNCH.json',dict(identity=identity,started_unix=time.time(),ready_sha256=sha(root/'READY.json'),
            admission_sha256=sha(lane/'ADMISSION.json'),arm=arm,uuid=ready['config']['uuid']))
        while child.poll() is None:
            policy.require(time.time()<bound['hard_deadline_unix']-30,'finite_hard_guard')
            time.sleep(2)
        policy.require(child.returncode==0 and (lane/'COMPLETE.json').exists(),'native_failure_no_retry')
        result='COMPLETE'
    except BaseException as error:
        write(lane/'GUARD_FAILED.json',dict(error_type=type(error).__name__,finished_unix=time.time()))
        raise
    finally:
        if child is not None:
            common.stop_owned(child,identity)
        write(lane/'TERMINAL.json',dict(status=result,finished_unix=time.time(),no_refill=True))


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('phase',choices=('prepare','native','guard','status'))
    parser.add_argument('--root',type=Path,required=True)
    parser.add_argument('--arm',choices=tuple(policy.ARMS),required=True)
    args=parser.parse_args()
    value=globals()[args.phase](args.root,args.arm)
    if value is not None:
        print(json.dumps(value,sort_keys=True))
