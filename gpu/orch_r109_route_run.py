"""Bounded resident R110 route lives; no automatic replay or quota reset."""

import argparse
from datetime import datetime, timezone
import fcntl
import json
import os
from pathlib import Path
import subprocess
import time

from gpu import astra_portable_actor_bundle as portable
from gpu import orch_math_pipeline_l2_run as common
from gpu import orch_r109_route_engine as native_engine
from gpu import orch_r109_route_scan as admission
from gpu.orch_rich_hot_node3_base107_engine import assert_no_adapter
from gpu.orch_r107_route_parent_long_protocol import parse as parse_parent
from organism_v6 import orch_r109_route as policy


write, read, sha = common.write, common.read, common.sha
ROOT_PREFIX = '/localhome/local-rohing/orch_r109_route_20260915_'
MODEL = '/localhome/local-rohing/.cache/huggingface/hub/models--Qwen--Qwen2.5-7B-Instruct/snapshots/a09a35458c702b33eeacc393d103063234e8bc28'
BUNDLE = '/tmp/astra_portable_37ec_20260914_attempt1'
BUNDLE_SHA = '5e675c309b202625a6ddf1d36c1a58f51ef656985821cec1cd6123424d927469'
END = datetime(2026,9,15,17,2,tzinfo=timezone.utc).timestamp()
LEASES = {'node1':datetime(2026,9,19,tzinfo=timezone.utc).timestamp(), 'a100':1790463900}


class BoundReached(Exception):
    pass


def verify(root, lane):
    policy.allocation(lane)
    policy.require(str(root).startswith(ROOT_PREFIX) and root.resolve() == root, 'unique_native_root')
    policy.require(common.host_identity() == policy.HOSTS[policy.LANES[lane]['host']]['sha256'], 'hashed_host')
    for relative, expected in read(root/'SOURCE_SHA256.json').items():
        policy.require(sha(root/'source'/relative) == expected, 'frozen_source:'+relative)
    policy.require(sha(root/'source'/policy.PRINCIPLES_PATH) == policy.PRINCIPLES_SHA, 'principles_snapshot')


def reserve(root, lane, kind, detail):
    cap = policy.NATIVE_CAP if kind == 'NATIVE' else policy.parent_cap(lane)
    with (root/'RESERVATIONS.jsonl').open('a+') as stream:
        fcntl.flock(stream,fcntl.LOCK_EX)
        stream.seek(0)
        count = sum(json.loads(line)['kind'] == kind for line in stream if line.strip())
        if count >= cap:
            raise BoundReached(kind+'_cap')
        row = dict(lane=lane,kind=kind,number=count+1,reserved_unix=time.time(),**detail)
        stream.write(json.dumps(row,sort_keys=True)+'\n')
        stream.flush()
        os.fsync(stream.fileno())
    return row


def prepare(root,lane):
    policy.require(os.environ.get('CUDA_VISIBLE_DEVICES') == '', 'cpu_prepare_only')
    verify(root,lane)
    policy.require(not (root/'PREPARED.json').exists(), 'one_prepare')
    host = policy.LANES[lane]['host']
    lease = LEASES.get(host)
    if lease is None:
        lease_document = read(root/'LEASE.json')
        policy.require(lease_document['verified'] and lease_document['source_sha256'], 'verified_lease_required')
        policy.require(sha(root/'source'/lease_document['source_relative']) == lease_document['source_sha256'], 'inherited_lease_source')
        lease = lease_document['lease_end_unix']
    base = portable.verify_base_files(BUNDLE,MODEL,expected_manifest_sha256=BUNDLE_SHA)
    policy.require(base['expected_base_sha256'] == policy.BASE_SHA,'original_base')
    tokenizer = portable.source.native.load_local_tokenizer(MODEL)
    engine = native_engine.BaseEngine(MODEL,tokenizer,device='cpu',check=lambda phase:None)
    write(root/'BASE_CPU_IDENTITY.json',dict(base_sha256=engine.loaded_base_sha256,
        no_adapter=engine.no_adapter,runtime=engine.runtime,gpu_calls=0))
    del engine
    frozen = policy.cohort(set(read(root/'EXCLUSIONS.json')['identifiers']),lane)
    for split in ('train','held'):
        for group in frozen[split]:
            for task in group['tasks']:
                prompt = [dict(role='system',content=policy.SYSTEM),dict(role='user',content=policy.gym.readout.display(task['node'],task,task['ports']))]
                policy.token_budget(len(tokenizer.apply_chat_template(prompt,tokenize=True,add_generation_prompt=True,return_dict=False)))
    write(root/'COHORT.json',frozen)
    policy.require(read(root/'CPU_TESTS.json')['passed'],'own_cpu_tests')
    if policy.LANES[lane]['learned']:
        native_engine.seed.prepare(output=root/'SEED.json')
        from gpu import orch_r107_base_anchors_inventory as anchor
        anchor_root = Path('/localhome/local-rohing/orch_r107_base_anchors_20260915_attempt1')
        anchors = anchor.load_inventory(anchor_root,tokenizer,policy.CONTEXT)
        from gpu import orch_r108_guided_native as trainer
        trainer.validate_anchor_inventory(anchors)
        write(root/'ANCHORS.json',dict(root=str(anchor_root),manifest_sha256=anchor.MANIFEST_SHA,
            counts={family:len(rows) for family,rows in anchors.items()}))
    started = time.time()
    hard = min(END,started+28800,lease-21600)
    policy.require(hard > started+300,'remaining_lifetime')
    files = ['SOURCE_SHA256.json','EXCLUSIONS.json','COHORT.json','BASE_CPU_IDENTITY.json','CPU_TESTS.json',
             'PRIOR_LEDGERS.json','PROVIDER_FILES.json']
    if policy.LANES[lane]['learned']:
        files += ['SEED.json','ANCHORS.json']
    prepared = dict(lane=lane,files={name:sha(root/name) for name in files},base=base,
        model_dir=MODEL,config_sha256=sha(Path(MODEL)/'config.json'),started_unix=started,
        hard_deadline_unix=hard,native_deadline_unix=hard-120,lease_end_unix=lease,lease_margin_seconds=21600,
        max_gpu_hours=8,native_cap=policy.NATIVE_CAP,parent_cap=policy.parent_cap(lane),cycles=policy.CYCLES,
        reflection_turns=policy.REFLECTION_TURNS[lane],output_cap=policy.OUTPUT,context=policy.CONTEXT,
        no_quota_reset=True,principles_sha256=policy.PRINCIPLES_SHA,version=policy.VERSION,
        provider_files=read(root/'PROVIDER_FILES.json'),learned=policy.LANES[lane]['learned'])
    write(root/'PREPARED.json',prepared)
    campaign = root/('campaign_'+lane)
    campaign.mkdir(exist_ok=False)
    (campaign/'parent_queue').mkdir()
    write(campaign/'READY.json',dict(prepared,prepared_sha256=sha(root/'PREPARED.json')))
    print(json.dumps(dict(lane=lane,ready_sha256=sha(campaign/'READY.json'),hard_deadline_unix=hard,
        base_sha256=policy.BASE_SHA,principles_sha256=policy.PRINCIPLES_SHA)))


def parent(root,lane,cycle,episode,segments,messages,response,stage,check,mode='BEHAVIOR',turn=0):
    campaign = root/('campaign_'+lane)
    principles = (root/'source'/policy.PRINCIPLES_PATH).read_text()
    payload = policy.parent_payload(lane,cycle,episode,segments,messages,response,stage,principles,mode,turn)
    policy.require(not policy.identifiers(payload).intersection(policy.identifiers(read(root/'COHORT.json')['held'])), 'held_blind')
    check('parent_dispatch')
    intent = reserve(root,lane,'PARENT',dict(cycle=cycle,mode=mode,turn=turn))
    identifier = f"GUIDED_SLEEP_C{cycle}_P{intent['number']}"
    path = campaign/'parent_queue'/(identifier+'.request.json')
    write(path,dict(id=identifier,payload=payload,payload_sha256=policy.digest(payload),ready_sha256=sha(campaign/'READY.json')))
    response_path = path.with_name(identifier+'.response.json')
    deadline = time.time()+300
    while not response_path.exists():
        check('parent_wait')
        policy.require(time.time()<deadline,'parent_timeout_no_replay')
        time.sleep(1)
    result = read(response_path)
    policy.require(result['status']=='COMPLETE' and result['request_sha256']==sha(path)
        and result['principles_sha256']==policy.PRINCIPLES_SHA,'actual_parent_response_join')
    directory = Path(result['archive']['remote_root'])
    policy.require(directory.is_relative_to(root/'parent_transcripts'/campaign.name),'own_parent_archive')
    for name,expected in result['archive']['files'].items():
        policy.require(not Path(name).is_absolute() and '..' not in Path(name).parts and sha(directory/name)==expected,'archive_hash')
    plan = parse_parent(read(directory/'RAW_RESPONSE.json'),[payload['episodes'][0]['task_id']])
    policy.require(policy.validate_plan(plan)==result['plan']==read(directory/'PLAN.json'),'actual_plan')
    receipt = dict(intent,request_sha256=sha(path),response_sha256=sha(response_path),archive=result['archive'],
        observed_unix=time.time(),principles_sha256=policy.PRINCIPLES_SHA,behavior_change=None,
        class_semantic_verification=None,held_exposed=False)
    write(campaign/f"PARENT_{intent['number']:05d}.json",receipt)
    return plan['guidance']+'\n'+plan['episode_guidance'][payload['episodes'][0]['task_id']],receipt


def native(root,lane):
    verify(root,lane)
    policy.require(os.environ.get('CUDA_VISIBLE_DEVICES')==policy.allocation(lane),'uuid_cvd')
    campaign=root/('campaign_'+lane)
    output=campaign/'native'
    output.mkdir(exist_ok=False)
    ready=read(campaign/'READY.json')
    for name,expected in ready['files'].items():
        policy.require(sha(root/name)==expected,'prepared_binding')
    def check(phase):
        if time.time()>=ready['native_deadline_unix']:
            raise BoundReached('absolute_deadline:'+phase)
    counters=dict(native_completed=0,parent_completed=0,train_segments=0,train_episodes=0,held_episodes=0,
        sleeps=0,optimizer_updates=0,triples=0,semantic_verified_changes=None)
    state=dict(pending_parent=None,advice='',memory='',cycle_rows=[],old_rows=[],last_call=None)
    def status(phase):
        write(campaign/'STATUS.json',dict(counters,phase=phase,observed_unix=time.time(),pid=os.getpid(),
            uuid=policy.allocation(lane),version=policy.VERSION,hard_deadline_unix=ready['hard_deadline_unix']))
    try:
        loaded=document=anchors=None
        if ready['learned']:
            document=read(root/'SEED.json')
            loaded,provenance=native_engine.load_learned(document,policy.LANES[lane],root,check)
            engine=loaded.engine
            from gpu import orch_r107_base_anchors_inventory as anchor
            anchor_binding=read(root/'ANCHORS.json')
            anchors=anchor.load_inventory(Path(anchor_binding['root']),engine.tokenizer,policy.CONTEXT,
                expected_manifest_sha256=anchor_binding['manifest_sha256'])
            write(campaign/'SEED_RESTORED.json',provenance)
        else:
            tokenizer=portable.source.native.load_local_tokenizer(ready['model_dir'])
            engine=native_engine.BaseEngine(ready['model_dir'],tokenizer,device='cuda:0',check=check)
            assert_no_adapter(engine.model)
        write(campaign/'ACTOR_READY.json',dict(lane=lane,pid=os.getpid(),uuid=policy.allocation(lane),
            loaded_unix=time.time(),base_sha256=policy.BASE_SHA,learned=ready['learned'],
            no_adapter=not ready['learned'],principles_sha256=policy.PRINCIPLES_SHA))
        def ask(cycle,episode,messages,response,stage,mode='BEHAVIOR',turn=0):
            status('PARENT_'+mode)
            advice,receipt=parent(root,lane,cycle,episode,counters['train_segments'],messages,response,stage,check,mode,turn)
            counters['parent_completed']+=1
            state['pending_parent']=receipt
            state['advice']=advice
            return advice
        def generate(messages,purpose,task_id,cycle,episode=0):
            check('native_dispatch')
            actual=[dict(message) for message in messages]
            training=not purpose.startswith('held')
            if training and state['advice'] and purpose!='reflection':
                actual.append(dict(role='user',content='Private parenting about thinking, not a new observation:\n'+state['advice']))
            tokens=engine.tokenizer.apply_chat_template(actual,tokenize=True,add_generation_prompt=True,return_dict=False)
            cap=policy.token_budget(len(tokens))
            intent=reserve(root,lane,'NATIVE',dict(cycle=cycle,purpose=purpose,task_id=task_id))
            path=output/f"CALL_{intent['number']:06d}.json"
            row=dict(intent,task_id=task_id,messages=actual,input_tokens=len(tokens),effective_cap=cap,
                started_unix=time.time(),phase_version=policy.VERSION,base_sha256=policy.BASE_SHA,
                adapter_state=document['adapter'] if document else None,semantic_functional_change=None,trainingAllowed=False)
            write(path,row)
            status('NATIVE_'+purpose)
            try:
                response=native_engine.generate(engine,actual,reflection=purpose=='reflection')
                policy.require(response['input_truncated'] is False and response['full_prompt_prefix_verified'],'full_prefix_contract')
                row.update(response=response,finished_unix=time.time(),status='COMPLETE')
                write(path,row)
            except BaseException as error:
                row.update(status='FAILED',error=dict(type=type(error).__name__,message=str(error)),finished_unix=time.time())
                write(path,row)
                raise
            counters['native_completed']+=1
            state['last_call']=dict(path=str(path),sha256=sha(path),finished_unix=row['finished_unix'])
            if training:
                counters['train_segments']+=1
                if state['pending_parent']:
                    receipt=state['pending_parent']
                    write(campaign/'triples'/f"{receipt['number']:05d}.json",dict(parent=receipt,
                        subsequent_child_call=state['last_call'],behavior_change=None,diagnostic='UNKNOWN_PENDING_AUDIT',
                        no_outcome_criterion=True))
                    counters['triples']+=1
                    state['pending_parent']=None
                if ready['learned']:
                    state['cycle_rows'].append(native_engine.replay_row(row,path,sha(path)))
                if purpose!='reflection' and policy.due(policy.LANES[lane]['cadence'],counters['train_segments']):
                    ask(cycle,episode,actual,response['raw'],'GENERATED_NOT_YET_EXECUTED')
            status('NATIVE_COMPLETE')
            return response
        frozen=read(root/'COHORT.json')
        for cycle in range(1,policy.CYCLES+1):
            check('cycle')
            state['cycle_rows']=[]
            group=frozen['train'][cycle-1]
            source=policy.collect_source(group['world'],lambda messages:generate(messages,'train_source',f'TRAIN-SOURCE-{cycle}',cycle))
            write(output/f'TRAIN_SOURCE_C{cycle}.json',source)
            records=[]
            for episode,task in enumerate(group['tasks'],1):
                record=policy.episode(group['world'],task,lambda messages:generate(messages,'train_episode',task['task_id'],cycle,episode),source['store'],state['memory'])
                records.append(policy.public_record(record))
                write(output/f'TRAIN_C{cycle}_E{episode}.json',record)
                counters['train_episodes']+=1
                if policy.due(policy.LANES[lane]['cadence'],counters['train_segments'],episode_end=True):
                    ask(cycle,episode,record['messages'],'','COMPLETED_EPISODE')
            conversation=[dict(role='system',content=policy.REFLECTION_SYSTEM+'\nThis is a pure metacognitive context-distillation conversation before sleep, not a route action task.'),
                dict(role='user',content=json.dumps(dict(actual_train_episodes=records,own_prior_reflection=state['memory'],
                    focus='Discuss what mattered, what is leaving context, your attention and perception of your capabilities; reflect on how you learn.'),sort_keys=True))]
            for turn in range(1,policy.REFLECTION_TURNS[lane]+1):
                advice=ask(cycle,2,conversation,conversation[-1]['content'],'COMPLETED_EPISODE' if turn==1 else 'COMPLETED_REFLECTION',
                    'METACOGNITION_CONVERSATION',turn)
                conversation.append(dict(role='user',content=advice))
                response=generate(conversation,'reflection',f'TRAIN-REFLECTION-{cycle}-{turn}',cycle,2)
                conversation.append(dict(role='assistant',content=response['raw']))
                state['memory']=response['raw']
            write(output/f'CONVERSATION_C{cycle}.json',dict(messages=conversation,turns=policy.REFLECTION_TURNS[lane],
                all_child_calls_retained=True,no_semantic_compiler=True,principles_sha256=policy.PRINCIPLES_SHA))
            status('SLEEP')
            if ready['learned']:
                document,summary=native_engine.sleep(loaded,document,state['cycle_rows'],state['old_rows'],anchors,
                    campaign/'sleeps'/f'{cycle:04d}',min(time.time()+120,ready['native_deadline_unix']-60),check,write,sha)
                counters['optimizer_updates']+=summary['optimizer_updates']
                state['old_rows'].extend(state['cycle_rows'])
            else:
                assert_no_adapter(engine.model)
                write(campaign/'sleeps'/f'{cycle:04d}.json',dict(context_only=True,weight_updates=0,
                    own_reflection_sha256=policy.digest(state['memory']),no_retained_learning_claim=True))
            counters['sleeps']+=1
            write(campaign/f'CHECKPOINT_C{cycle}.json',dict(counters,own_memory=state['memory'],
                adapter=document,finished_unix=time.time(),resident_pid=os.getpid()))
            group=frozen['held'][cycle-1]
            source=policy.collect_source(group['world'],lambda messages:generate(messages,'held_source',f'HELD-SOURCE-{cycle}',cycle))
            write(output/f'HELD_SOURCE_C{cycle}.json',source)
            for episode,task in enumerate(group['tasks'],1):
                record=policy.episode(group['world'],task,lambda messages:generate(messages,'held_episode',task['task_id'],cycle),source['store'],state['memory'])
                write(output/f'HELD_C{cycle}_E{episode}.json',dict(record,parent_free=True,sealed_from_parent=True))
                counters['held_episodes']+=1
            engine.verify_base()
            status('CYCLE_COMPLETE')
        write(campaign/'COMPLETE.json',dict(counters,reason='cycle_cap',finished_unix=time.time()))
    except BoundReached as error:
        write(campaign/'COMPLETE.json',dict(counters,reason=str(error),partial_episode_preserved=True,finished_unix=time.time()))
    except BaseException as error:
        write(campaign/'FAILED.json',dict(counters,error=dict(type=type(error).__name__,message=str(error)),finished_unix=time.time()))
        raise


def guard(root,lane):
    verify(root,lane)
    campaign=root/('campaign_'+lane)
    ready=read(campaign/'READY.json')
    publication=read(campaign/'PUBLICATION.json')
    policy.require(publication['ready_sha256']==sha(campaign/'READY.json') and publication['allocation_sha256']==sha(root/'ALLOCATION.md')
        and publication['dated_builder_publication'],'publication_before_gpu')
    child=identity=None
    outcome='FAILED'
    try:
        for attempt in range(90):
            policy.require(time.time()<ready['native_deadline_unix'],'admission_deadline')
            snapshot=admission.scan(lane,root/'SERVICE_IDENTITY.json')
            write(campaign/f'ADMISSION_{attempt:03d}.json',snapshot)
            if snapshot['clear']:
                break
            time.sleep(3)
        policy.require(snapshot['clear'] and snapshot['scanner_euid']==0,'strict_privileged_clear')
        with (campaign/'native.log').open('x') as log:
            child=subprocess.Popen([common.PYTHON,'-B','-m','gpu.orch_r109_route_run','native','--root',str(root),'--lane',lane],
                cwd=root/'source',start_new_session=True,stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,
                env=dict(os.environ,CUDA_VISIBLE_DEVICES=policy.allocation(lane),PYTHONPATH=str(root/'source'),
                    HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',PYTHONDONTWRITEBYTECODE='1',OMP_NUM_THREADS='1',MKL_NUM_THREADS='1',TOKENIZERS_PARALLELISM='false'))
            identity=common.process_identity(Path('/proc')/str(child.pid))
            write(campaign/'LAUNCH.json',dict(pid=child.pid,identity=identity,uuid=policy.allocation(lane),
                started_unix=time.time(),ready_sha256=sha(campaign/'READY.json')))
            while child.poll() is None:
                policy.require(time.time()<ready['hard_deadline_unix']-30,'hard_deadline')
                time.sleep(1)
            policy.require(child.returncode==0 and (campaign/'COMPLETE.json').exists(),'native_failure_no_replay')
            outcome='COMPLETE'
    except BaseException as error:
        write(campaign/'GUARDIAN_FAILED.json',dict(error=dict(type=type(error).__name__,message=str(error)),finished_unix=time.time()))
        raise
    finally:
        if child is not None:
            common.stop_owned(child,identity)
        write(campaign/'TERMINAL.json',dict(status=outcome,finished_unix=time.time(),automatic_refill=False))
        write(campaign/'RELEASE.json',admission.scan(lane,root/'SERVICE_IDENTITY.json'))


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('phase',choices=('prepare','native','guard'))
    parser.add_argument('--root',type=Path,required=True)
    parser.add_argument('--lane',choices=policy.LANES,required=True)
    args=parser.parse_args()
    globals()[args.phase](args.root,args.lane)
