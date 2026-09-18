"""Fixed-lifetime native R109 admission, generation, fit, and readout supervisor."""

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import signal
import socket
import subprocess
import sys
import time
from types import FunctionType

from gpu.orch_r109_l1_assets import sha
from gpu.orch_r109_l1_ops import HOSTS, root_for, identity
from gpu.orch_r109_l1_train import ROOT, read, write, sources
from organism_v6 import orch_r109_l1_policy as policy


PYTHON='/localhome/local-rohing/v2/venv/bin/python'


def freeze(node):
    from gpu.orch_math_rich_source import verify_archive
    from organism_v6 import orch_rich_hot_node1 as one
    from organism_v6 import orch_rich_hot_node2 as two
    from gpu.orch_l2_budget_readout_run import LEASE_END
    assert hashlib.sha256(socket.gethostname().encode()).hexdigest()==HOSTS[node]
    old=root_for(node,0)
    prepared=read(old/('PREPARED.json' if node=='node1' else 'PREPARE.json'))
    if node=='node1':
        from gpu.orch_rich_hot_node1_exhaustion_run import BUNDLE
        bundle=BUNDLE
    else:
        bundle=prepared['bundle']
    lifetime=policy.lifetime(time.time(),one.LEASE_END if node=='node1' else LEASE_END)
    source_count=verify_archive(ROOT/'source.tar',ROOT/'source')
    assert not (ROOT/'PLAN.json').exists()
    plan=dict(schema='R109_L1_NATIVE_V1',node=node,host_sha256=HOSTS[node],lifetime=lifetime,
        owned_physical=list(range(7)),forbidden_generation=[7],uuid_by_index=list(one.UUIDS if node=='node1' else two.UUIDS),
        model_dir=prepared['model_dir'],bundle=str(bundle),source_archive_sha256=sha(ROOT/'source.tar'),source_files=source_count,
        source_python_files={str(path.relative_to(ROOT/'source')):sha(path) for path in (ROOT/'source').rglob('*.py')},
        train_topology=dict(FULL=[0,1,2],CONTROL=[3]),updates_per_segment=128,max_segments=16,
        max_generation_calls_per_gpu=8192,max_generation_context=32768,max_new_tokens=8192,
        original_child_state=policy.CHILD,original_update=8932,anchor_manifest_sha256=policy.ANCHORS,
        source_labels=list(policy.LABELS),initial_ingestion_labels=list(policy.LABELS[:2]),
        fixed32_on_off_every_checkpoint=True,held_behavior_every_checkpoint=True,
        original_corpus_history='IMMUTABLE_REHEARSAL_NOT_RETROACTIVE_INGESTION',
        publisher='Main',allocation_commit='71e9aa56',frozen_unix=time.time())
    shutil.copyfile(old/'SERVICE_IDENTITY.json',ROOT/'SERVICE_IDENTITY.json')
    write(ROOT/'PLAN.json',plan)
    print(json.dumps(dict(plan_sha256=sha(ROOT/'PLAN.json'),source_files=source_count,lifetime=lifetime)))


def verify():
    plan=sources()
    assert hashlib.sha256(socket.gethostname().encode()).hexdigest()==plan['host_sha256']
    actual={str(path.relative_to(ROOT/'source')):sha(path) for path in (ROOT/'source').rglob('*.py')}
    assert actual==plan['source_python_files'],'exact_native_archive_python_inventory'
    receipt=read(ROOT/'PRE_GPU.json')
    assert receipt['plan_sha256']==sha(ROOT/'PLAN.json') and receipt['cpu_passed'] is True
    assert receipt['builder_line'].startswith('[Builder]')
    return plan


def scan(node,index):
    policy.allocation(node,index)
    if node=='node1':
        from gpu.orch_rich_hot_node1_scan import scan as scanner
    else:
        from gpu.orch_rich_hot_node2_scan import scan as scanner
    return scanner(index,ROOT/'SERVICE_IDENTITY.json')


def spawn(plan,index,module,arguments,label):
    policy.allocation(plan['node'],index)
    assert time.time()<plan['lifetime']['native_deadline_unix']
    report=scan(plan['node'],index)
    directory=ROOT/'admissions'
    directory.mkdir(exist_ok=True)
    write(directory/f'{label}_{time.time_ns()}.json',report)
    if not report['clear']:
        return None
    assert report['scanner_euid']==0 and report['gpu']['uuid']==plan['uuid_by_index'][index]
    log=(ROOT/(label+'.log')).open('x')
    child=subprocess.Popen([PYTHON,'-B','-u','-m',module,*arguments],cwd=ROOT/'source',
        stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,start_new_session=True,
        env=dict(os.environ,PYTHONPATH=str(ROOT/'source'),CUDA_VISIBLE_DEVICES=plan['uuid_by_index'][index],
            HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',PYTHONDONTWRITEBYTECODE='1',
            OMP_NUM_THREADS='1',MKL_NUM_THREADS='1',TOKENIZERS_PARALLELISM='false'))
    expected=identity(child.pid)
    write(ROOT/(label+'_LAUNCH.json'),dict(identity=expected,index=index,uuid=plan['uuid_by_index'][index],
        module=module,arguments=arguments,source_archive_sha256=plan['source_archive_sha256'],
        hard_deadline_unix=policy.END,started_unix=time.time()))
    log.close()
    return child,expected


def stop(child,expected,reason):
    if child.poll() is not None:
        return
    assert identity(child.pid)==expected and expected['uid']==os.getuid()
    descriptor=os.pidfd_open(child.pid)
    try:
        assert identity(child.pid)==expected
        write(ROOT/'stops'/f'{child.pid}_{time.time_ns()}.json',dict(identity=expected,reason=reason,observed_unix=time.time()))
        signal.pidfd_send_signal(descriptor,signal.SIGTERM)
        try:
            child.wait(timeout=30)
        except subprocess.TimeoutExpired:
            assert identity(child.pid)==expected
            signal.pidfd_send_signal(descriptor,signal.SIGKILL)
            child.wait(timeout=10)
    finally:
        os.close(descriptor)


def wait_all(plan,children,label):
    while any(child.poll() is None for child,expected in children):
        write(ROOT/'LIVE.json',dict(stage=label,observed_unix=time.time(),
            processes=[dict(identity=expected,returncode=child.poll()) for child,expected in children],
            fixed_hard_end=policy.END,ingestion_labels=plan['initial_ingestion_labels']))
        if time.time()>=policy.END-45:
            for child,expected in children:
                stop(child,expected,'FIXED_R109_HARD_END')
            raise TimeoutError('R109 fixed hard end')
        if any(child.poll() not in (None,0) for child,expected in children):
            for child,expected in children:
                stop(child,expected,'PEER_STAGE_FAILURE_PRESERVE_LAST_CHECKPOINT')
            raise RuntimeError('R109 native stage failed')
        time.sleep(5)
    assert all(child.returncode==0 for child,expected in children)


def wait_spawn(plan,index,module,arguments,label):
    while time.time()<policy.CUTOFF-600:
        result=spawn(plan,index,module,arguments,label)
        if result is not None:
            return result
        time.sleep(5)
    raise TimeoutError('No safely released device before fixed cutoff')


def fit_supervise():
    plan=verify()
    assert plan['node']=='node2'
    assert read(ROOT/'PREPARED.json')['status']=='PASS'
    from gpu.orch_r109_l1_ops import retire
    from gpu.orch_rich_hot_node2_exhaustion_v3_guard import closed
    for index in range(4):
        retire('node2',index)
    while not all(closed(root_for('node2',index),index) for index in range(4)):
        assert time.time()<policy.CUTOFF-1800
        time.sleep(2)
    write(ROOT/'PRIOR_TRAIN_SLOTS_PRESERVED.json',dict(indexes=list(range(4)),
        terminal_hashes={str(index):sha(root_for('node2',index)/f'shard{index}/TERMINAL.json') for index in range(4)},
        source_archive_sha256=sha(root_for('node2',0)/'source.tar'),all_reservations_resolved=True,
        all_frozen_states_unchanged=True,observed_unix=time.time()))
    resumes={arm:ROOT/'input/checkpoint' for arm in ('FULL','CONTROL')}
    for segment in range(plan['max_segments']):
        if time.time()>=policy.CUTOFF-1800:
            break
        children=[]
        try:
            for arm,indexes in plan['train_topology'].items():
                for rank,index in enumerate(indexes):
                    args=['train','--arm',arm,'--rank',str(rank),'--index',str(index),
                          '--world-size',str(len(indexes)),'--segment',str(segment),'--resume',str(resumes[arm])]
                    children.append(wait_spawn(plan,index,'gpu.orch_r109_l1_train',args,f'fit_{segment}_{arm}_{rank}'))
            wait_all(plan,children,f'FIT_{segment}')
            for arm in resumes:
                complete=read(ROOT/'fit'/arm/f'segment{segment:03d}'/'COMPLETE.json')
                resumes[arm]=Path(complete['checkpoint'])
            children=[]
            for index,(arm,condition) in enumerate([('FULL','ON'),('FULL','OFF'),('CONTROL','ON'),('CONTROL','OFF')]):
                args=['readout','--arm',arm,'--condition',condition,'--index',str(index),
                      '--segment',str(segment),'--resume',str(resumes[arm])]
                children.append(wait_spawn(plan,index,'gpu.orch_r109_l1_train',args,f'readout_{segment}_{arm}_{condition}'))
            wait_all(plan,children,f'FIXED32_AND_HELD_{segment}')
            summaries={arm:{condition:read(ROOT/'fit'/arm/f'segment{segment:03d}'/'readout'/condition/'COMPLETE.json')
                for condition in ('ON','OFF')} for arm in resumes}
            from organism_v6 import orch_r107_capability as capability
            for arm in resumes:
                records=[read(path) for path in sorted((ROOT/'fit'/arm/f'segment{segment:03d}'/'readout').glob('*/CAPABILITY_*.json'))]
                summary=capability.reduce_paired(records,checkpoint_sha256=summaries[arm]['ON']['checkpoint_state_sha256'],
                    base_sha256=policy.BASE,max_new_tokens=512)
                write(ROOT/'fit'/arm/f'segment{segment:03d}'/'PAIRED_FIXED32.json',summary)
            write(ROOT/'CHECKPOINT_HANDOFF.json',dict(segment=segment,checkpoints={arm:str(path) for arm,path in resumes.items()},
                readouts=summaries,scientific_claim='CONTROLLED_DIAGNOSTICS_NOT_ESTABLISHED_RETAINED_LEARNING',observed_unix=time.time()))
        finally:
            for child,expected in children:
                stop(child,expected,'SUPERVISOR_EXIT')
    write(ROOT/'FIT_SUPERVISOR_COMPLETE.json',dict(checkpoints={arm:str(path) for arm,path in resumes.items()},finished_unix=time.time()))


def generate(index):
    from gpu import orch_guided_native as native
    from gpu.orch_rich_hot_node2_exhaustion_v3 import Engine
    from organism_v6 import orch_rich_hot_node2_floor98 as roster
    from organism_v6 import orch_rich_hot_node2_supply as environment
    plan=verify()
    lane=policy.allocation(plan['node'],index)
    condition=policy.CONDITIONS[lane%len(policy.CONDITIONS)]
    commit=read(ROOT/'input/checkpoint/COMMIT.json')
    adapter=native.bridge.AdapterIdentity.from_document(dict(commit['metadata']['adapter'],path=str(ROOT/'input/checkpoint/adapter')))
    assert adapter.state_sha256==policy.CHILD
    assert os.environ['CUDA_VISIBLE_DEVICES']==plan['uuid_by_index'][index]
    binding=native.bridge.StageBinding(ROOT.name+f'_gen{index}',native.bridge.ARMS[1],0,'sealed_readout',adapter,
        False,True,sha(ROOT/'PLAN.json'))
    def check(label):
        if time.time()>=policy.CUTOFF:
            raise TimeoutError('fixed_generation_cutoff:'+label)
    loaded=native.load_stage(binding,model_dir=plan['model_dir'],device='cuda:0',gpu_uuid=plan['uuid_by_index'][index],
        context=native.StageContext(),check=check,engine_factory=Engine)
    directory=ROOT/'generation'/f'gpu{index}'
    directory.mkdir(parents=True,exist_ok=False)
    write(directory/'LOADED.json',dict(adapter=adapter.document(),process=loaded.process,condition=condition,
        source_label='R109_SELF_GENERATED_FUNCTIONAL',observed_unix=time.time()))
    document=read(ROOT/'TASKS.json')
    assert sha(ROOT/'TASKS.json')==read(ROOT/'GENERATION_READY.json')['tasks_sha256']
    count=0
    for batch in range(roster.MAX_BATCHES):
        for position in range(index%2,roster.TASKS_PER_BATCH,2):
            if time.time()>=policy.CUTOFF or count>=plan['max_generation_calls_per_gpu']-32:
                loaded.verify_unchanged()
                write(directory/'COMPLETE.json',dict(calls=count,status='BOUNDED_COMPLETE',finished_unix=time.time()))
                return
            task=roster.task_at(document,batch,position)
            task=dict(task,id=f'R109-{plan["node"]}-{index}-{task["id"]}',original_task_id=task['id'],source_reuse=True)
            stages={}
            def call(stage,messages):
                nonlocal count
                check('call')
                assert count<plan['max_generation_calls_per_gpu']
                tokens=loaded.engine.prompt_tokens(messages)
                cap=min(8192,32768-len(tokens))
                assert cap>0
                count+=1
                row=dict(task_id=task['id'],source_task_id=task['source_task_id'],family=task['family'],stage=stage,
                    condition=condition,source_label='R109_SELF_GENERATED_FUNCTIONAL',split='TRAIN',
                    source_state_sha256=adapter.state_sha256,source_archive_sha256=plan['source_archive_sha256'],
                    source_tasks_sha256=sha(ROOT/'TASKS.json'),messages=messages,started_unix=time.time(),
                    trainingAllowed=False,semantic_status='UNREVIEWED',parent_calls=0)
                write(directory/f'INTENT_{count:06d}.json',row)
                try:
                    response=loaded.engine.generate(messages,max_new_tokens=cap)
                    row.update(response=response,outcome=roster.outcome(task,response),finished_unix=time.time())
                    write(directory/f'CALL_{count:06d}.json',row)
                    return response
                except BaseException as error:
                    write(directory/f'FAILED_{count:06d}.json',dict(row,error_type=type(error).__name__,finished_unix=time.time()))
                    raise
            if task['family']=='route':
                world=task['payload']
                runtime=environment.runtime(world['master'])
                collection=runtime['collect_world'](world,lambda messages:call('exposure',messages))
                runtime['replay_collection'](collection)
                store={record['edge']['event']:record['event']['raw'] for record in collection['records'] if record['accepted']}
                namespace=dict(environment.route.__dict__,GUIDANCE=policy.GUIDANCE[condition])
                episode=FunctionType(environment.route.episode.__code__,namespace,'episode',environment.route.episode.__defaults__)
                tasks=[public for ordinal,public in enumerate(runtime['build_tasks'](world)) if ordinal in (0,2)]
                episodes=[episode(world,public,lambda messages:call('goal',messages),store) for public in tasks]
                write(directory/f'EPISODE_{batch:03d}_{position:02d}.json',dict(task=task,collection=collection,episodes=episodes,
                    observed_correct=sum(row['correct'] for row in episodes),denominator=2,semantic_status='UNREVIEWED'))
            else:
                response=call('draft',policy.generation_messages(task,condition))
                if condition!='ORDINARY_CONTROL':
                    call('continuation',policy.generation_messages(task,condition,response['raw']))
            write(directory/'PROGRESS.json',dict(calls=count,batch=batch,position=position,finished_unix=time.time(),
                condition=condition,qualified_rows=0,training_ingested=0))


def generation_supervise(index):
    plan=verify()
    policy.allocation(plan['node'],index)
    from gpu.orch_r109_l1_ops import retire
    old=root_for(plan['node'],index)
    expected=read(old/f'LAUNCH_{index}.json')['identity']
    if (Path('/proc')/str(expected['pid'])).exists():
        retire(plan['node'],index)
    if plan['node']=='node2':
        from gpu.orch_rich_hot_node2_exhaustion_v3_guard import closed
        while not closed(old,index):
            assert time.time()<policy.CUTOFF-600
            time.sleep(2)
    child=wait_spawn(plan,index,'gpu.orch_r109_l1_run',['generate','--index',str(index)],f'generation_{index}')
    try:
        wait_all(plan,[child],f'GENERATION_{index}')
    finally:
        stop(*child,'GENERATION_SUPERVISOR_EXIT')


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('action',choices=['freeze','fit-supervise','generation-supervise','generate'])
    parser.add_argument('--node',choices=['node1','node2'])
    parser.add_argument('--index',type=int)
    options=parser.parse_args()
    if options.action=='freeze':
        freeze(options.node)
    elif options.action=='fit-supervise':
        fit_supervise()
    elif options.action=='generation-supervise':
        generation_supervise(options.index)
    else:
        generate(options.index)
