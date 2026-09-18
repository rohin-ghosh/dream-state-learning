"""New R109 experiment resuming8932 with native rehearsal and BASE anchors."""

import argparse
from dataclasses import asdict
from datetime import timedelta
import json
import os
from pathlib import Path
import time
from types import SimpleNamespace

from gpu import orch_guided_native as native
from gpu import orch_combined_l1_continual_run as previous
from gpu.orch_l2_shared_run import legacy_encode
from gpu.orch_math_rich_source import verify_archive
from gpu.orch_r109_l1_assets import sha
from organism_v6 import orch_r109_l1_policy as policy
from organism_v6 import orch_combined_l1_continual as storage


ROOT=Path('/localhome/local-rohing/orch_r109_l1_20260915')
ANCHOR_ROOT=Path('/localhome/local-rohing/orch_r107_base_anchors_20260915_attempt1')
write=storage.atomic_json


def read(path):
    return json.loads(Path(path).read_text())


def sources():
    plan=read(ROOT/'PLAN.json')
    assert sha(ROOT/'source.tar')==plan['source_archive_sha256']
    assert verify_archive(ROOT/'source.tar',ROOT/'source')==plan['source_files']
    assert time.time()<plan['lifetime']['native_deadline_unix']
    return plan


def prepare():
    assert os.environ.get('CUDA_VISIBLE_DEVICES')==''
    plan=sources()
    assets=read(ROOT/'ASSETS_MANIFEST.json')
    assert all(sha(ROOT/'input'/name)==digest for name,digest in assets['files'].items())
    checkpoint=ROOT/'input/checkpoint'
    commit=read(checkpoint/'COMMIT.json')
    assert commit['metadata']['update']==8932 and commit['metadata']['adapter']['state_sha256']==policy.CHILD
    assert sha(ANCHOR_ROOT/'ANCHOR_MANIFEST.json')==policy.ANCHORS
    adapter=dict(commit['metadata']['adapter'],path=str(checkpoint/'adapter'))
    native.bridge.AdapterIdentity.from_document(adapter).verify()
    from safetensors.torch import load_file
    tensors=load_file(str(checkpoint/'adapter/adapter_model.safetensors'),device='cpu')
    mounted={name.replace('.lora_A.','.lora_A.default.').replace('.lora_B.','.lora_B.default.'):value for name,value in tensors.items()}
    assert native.state_hash(mounted)==policy.CHILD
    previous.common.portable.verify_base_files(plan['bundle'],plan['model_dir'],expected_manifest_sha256=previous.BUNDLE_SHA)
    tokenizer=native.source.native.load_local_tokenizer(plan['model_dir'])
    from gpu.orch_r107_base_anchors_inventory import build_inventory
    inventory,anchor_receipt=build_inventory(ANCHOR_ROOT,tokenizer,2048,expected_manifest_sha256=policy.ANCHORS)
    legacy=legacy_encode(ROOT/'input/prior',tokenizer)
    corpus=read(ROOT/'input/prior/CORPORA/000013.json')
    assert sha(ROOT/'input/prior/CORPORA/000013.json')==commit['metadata']['corpus_sha256']
    prior=previous.encode_corpus(corpus['rows'],tokenizer,{})
    anchors=[entry['encoded'] for family in inventory.values() for entry in family]
    assert len(legacy)==222 and len(prior)==3635 and len(anchors)==42
    from organism_v6 import orch_r107_capability as capability
    held=read(ROOT/'input/prior/LEGACY_READOUT.json')['held']
    assert held['split']=='HELD'
    serialized=json.dumps(corpus['rows'])
    assert all(task['id'] not in serialized and task['prompt'] not in serialized for task in capability.tasks())
    encoded={key:[asdict(row) for row in rows] for key,rows in [('legacy',legacy),('prior',prior),('anchor',anchors)]}
    assert all(len(row['input_ids'])==len(row['labels']) and len(row['input_ids'])<=2048
               and any(label!=-100 for label in row['labels']) for rows in encoded.values() for row in rows)
    write(ROOT/'ENCODED.json',encoded)
    write(ROOT/'ANCHOR_INVENTORY_RECEIPT.json',anchor_receipt)
    write(ROOT/'PREPARED.json',dict(status='PASS',plan_sha256=sha(ROOT/'PLAN.json'),adapter=adapter,
        encoded_sha256=sha(ROOT/'ENCODED.json'),counts={key:len(value) for key,value in encoded.items()},
        fixed32_suite_sha256=capability.digest(capability.tasks()),held_behavior_sha256=policy.digest(held),
        checkpoint_commit_sha256=sha(checkpoint/'COMMIT.json'),source_archive_sha256=plan['source_archive_sha256'],
        assets_manifest_sha256=sha(ROOT/'ASSETS_MANIFEST.json'),anchor_manifest_sha256=policy.ANCHORS,
        no_parent_targets=True,held_excluded=True,model_loaded=False,observed_unix=time.time()))
    print(json.dumps(read(ROOT/'PREPARED.json')))


def load_plan(arm,checkpoint,training):
    plan=sources()
    prepared=read(ROOT/'PREPARED.json')
    assert prepared['plan_sha256']==sha(ROOT/'PLAN.json')
    assert sha(ROOT/'ENCODED.json')==prepared['encoded_sha256']
    commit=storage.verify_checkpoint(checkpoint)['metadata']
    identity=native.bridge.AdapterIdentity.from_document(dict(commit['adapter'],path=str(checkpoint/'adapter')))
    binding=native.bridge.StageBinding(ROOT.name+'_'+arm,native.bridge.ARMS[2],0,
        'training' if training else 'sealed_readout',identity,False,not training,sha(ROOT/'PREPARED.json'))
    proxy=SimpleNamespace(binding=lambda unused:binding,
        contract=SimpleNamespace(manifest=lambda unused:dict(recipe=previous.common.RECIPE)),
        lineage=SimpleNamespace(arm=native.bridge.ARMS[2]))
    return plan,prepared,commit,identity,binding,proxy


def train(arm,index,rank,world_size,segment,resume):
    plan,prepared,commit,identity,binding,proxy=load_plan(arm,resume,True)
    assert plan['train_topology'][arm][rank]==index and len(plan['train_topology'][arm])==world_size
    uuid=plan['uuid_by_index'][index]
    assert os.environ['CUDA_VISIBLE_DEVICES']==uuid
    check=lambda label:previous.common.check_deadline(plan['lifetime'],label)
    loaded=native.load_training(proxy,model_dir=plan['model_dir'],device='cuda:0',gpu_uuid=uuid,
        context=native.StageContext(),check=check)
    torch=loaded.engine.torch
    torch.distributed.init_process_group('gloo',init_method=f'tcp://[REDACTED_ADDRESS]:{29630+(arm=="CONTROL")}',
        rank=rank,world_size=world_size,timeout=timedelta(minutes=5))
    loaded.optimizer.load_state_dict(torch.load(resume/'optimizer.pt',map_location='cuda:0',weights_only=False))
    previous.restore_rng(torch,torch.load(resume/f'rank{rank}.pt',map_location='cpu',weights_only=False))
    parameters={name:value for name,value in loaded.engine.model.named_parameters() if native.is_lora(name)}
    assert native.state_hash(parameters)==identity.state_sha256
    encoded=read(ROOT/'ENCODED.json')
    output=ROOT/'fit'/arm/f'segment{segment:03d}'
    output.mkdir(parents=True,exist_ok=True)
    write(output/f'RANK{rank}_LOADED.json',dict(update=commit['update'],state_sha256=identity.state_sha256,
        optimizer_restored=True,rng_restored=True,global_cursor_preserved=True,process=loaded.process,uuid=uuid,
        original_training_history_unchanged=True,observed_unix=time.time()))
    start=commit['update']
    end=start+plan['updates_per_segment']
    state=dict(update=start,prior_checkpoint_commit_sha256=sha(resume/'COMMIT.json'),
        lifetime=plan['lifetime'],source_labels=list(policy.LABELS[:2]),r109_exposures={},arm=arm,
        inherited_exposure_counts=commit.get('exposure_counts',commit.get('inherited_exposure_counts')),
        inherited_supervised_tokens=commit.get('supervised_tokens',commit.get('inherited_supervised_tokens')),
        r109_supervised_tokens=commit.get('r109_supervised_tokens',0))
    with (output/f'RANK{rank}_LOSSES.jsonl').open('x') as log:
        for update in range(start+1,end+1):
            check('R109_optimizer_boundary')
            selections=policy.batch_positions(update,len(encoded['prior']),len(encoded['anchor']))
            rows=[encoded[label][position] for label,position in selections]
            positions=storage.rank_positions(rank,world_size)
            reference=sum(label!=-100 for row in rows for label in row['labels'][1:])
            maximum=max(len(rows[position]['input_ids']) for position in positions)
            inputs=[]
            labels=[]
            masks=[]
            for position in positions:
                row=rows[position]
                length=len(row['input_ids'])
                inputs.append(row['input_ids']+[loaded.engine.tokenizer.pad_token_id]*(maximum-length))
                target=row['labels'] if not (arm=='CONTROL' and selections[position][0]=='anchor') else [-100]*length
                labels.append(target+[-100]*(maximum-length))
                masks.append([1]*length+[0]*(maximum-length))
            local_active=sum(label!=-100 for row in labels for label in row[1:])
            assert local_active>0
            tensors={name:torch.tensor(value,dtype=torch.long,device=loaded.engine.device)
                     for name,value in dict(input_ids=inputs,labels=labels,attention_mask=masks).items()}
            loaded.optimizer.zero_grad(set_to_none=True)
            with torch.autocast(device_type='cuda',dtype=torch.bfloat16):
                loss=loaded.engine.model(**tensors,use_cache=False).loss*(local_active/reference)
            assert bool(torch.isfinite(loss))
            loss.backward()
            assert all(value.grad is not None for value in parameters.values())
            gradient=torch.cat([value.grad.reshape(-1) for value in parameters.values()]).cpu()
            torch.distributed.all_reduce(gradient,op=torch.distributed.ReduceOp.SUM)
            assert bool(torch.isfinite(gradient).all())
            gradient=gradient.to(loaded.engine.device)
            offset=0
            for parameter in parameters.values():
                size=parameter.numel()
                parameter.grad.copy_(gradient[offset:offset+size].view_as(parameter))
                offset+=size
            loaded.optimizer.step()
            state['update']=update
            log.write(json.dumps(dict(update=update,loss=loss.item(),selections=selections,
                local_active=local_active,reference_tokens=reference,finished_unix=time.time()))+'\n')
            log.flush()
            for label,position in selections:
                state['r109_exposures'][label]=state['r109_exposures'].get(label,0)+1
            state['r109_supervised_tokens']+=reference-(sum(label!=-100 for label in rows[2]['labels'][1:]) if arm=='CONTROL' else 0)
    destination=ROOT/'fit'/arm/'checkpoints'/f'{state["update"]:09d}'
    staging=destination.with_suffix('.pending')
    if rank==0:
        staging.mkdir(parents=True,exist_ok=False)
    torch.distributed.barrier()
    torch.save(previous.rng_state(torch),staging/f'rank{rank}.pt')
    if rank==0 and world_size==1:
        torch.save(previous.rng_state(torch),staging/'rank1.pt')
    hashes=[None]*world_size
    torch.distributed.all_gather_object(hashes,native.state_hash(parameters))
    assert len(set(hashes))==1
    if rank==0:
        loaded.engine.verify_base()
        torch.save(loaded.optimizer.state_dict(),staging/'optimizer.pt')
        loaded.engine.model.save_pretrained(staging/'adapter',safe_serialization=True,save_embedding_layers=False)
        adapter=native.bridge.AdapterIdentity(str(destination/'adapter'),hashes[0],policy.BASE,
            tuple((path.name,sha(path)) for path in sorted((staging/'adapter').iterdir()) if path.is_file()))
        state.update(adapter=adapter.document(),source_sha256=plan['source_archive_sha256'],
            optimizer_preserved=True,rng_per_rank=True,world_size=world_size,saved_unix=time.time())
        storage.commit_checkpoint(staging,destination,state)
        write(output/'COMPLETE.json',dict(checkpoint=str(destination),commit_sha256=sha(destination/'COMMIT.json'),
            update=state['update'],adapter=adapter.document(),readout_required=True))
    torch.distributed.barrier()
    torch.distributed.destroy_process_group()


def readout(arm,index,condition,segment,resume):
    from gpu.orch_rich_hot_node2_exhaustion_v3 import Engine
    from gpu.orch_r107_capability_run import readonly_condition
    from organism_v6 import orch_r107_capability as capability
    from organism_v6 import experienced_event_reader_audit_lesson as behavior
    plan,prepared,commit,identity,binding,proxy=load_plan(arm,resume,False)
    uuid=plan['uuid_by_index'][index]
    assert os.environ['CUDA_VISIBLE_DEVICES']==uuid
    loaded=native.load_stage(binding,model_dir=plan['model_dir'],device='cuda:0',gpu_uuid=uuid,
        context=native.StageContext(),check=lambda label:previous.common.check_deadline(plan['lifetime'],label),engine_factory=Engine)
    output=ROOT/'fit'/arm/f'segment{segment:03d}'/'readout'/condition
    output.mkdir(parents=True,exist_ok=False)
    calls=[]
    with readonly_condition(loaded.engine.model,'LORA_'+condition):
        for task in capability.tasks():
            response=loaded.engine.generate(capability.messages(task),max_new_tokens=512)
            record=capability.capture(task,condition,response,checkpoint_sha256=identity.state_sha256,
                base_sha256=policy.BASE,lora_enabled=condition=='ON')
            write(output/f'CAPABILITY_{len(calls):03d}.json',record)
            calls.append(record)
        held=read(ROOT/'input/prior/LEGACY_READOUT.json')['held']
        assert policy.digest(held)==prepared['held_behavior_sha256']
        behavior_calls=[]
        def generate(messages):
            response=loaded.engine.generate(messages,max_new_tokens=160)
            write(output/f'BEHAVIOR_{len(behavior_calls):03d}.json',response)
            behavior_calls.append(response)
            return response
        result=behavior.collect_cases(held,generate,coached=False)
    loaded.verify_unchanged()
    write(output/'COMPLETE.json',dict(status='COMPLETE',condition=condition,capability_calls=len(calls),
        behavior_calls=len(behavior_calls),behavior=result['summary'],fixed32_suite_sha256=prepared['fixed32_suite_sha256'],
        checkpoint_state_sha256=identity.state_sha256,held_behavior_sha256=prepared['held_behavior_sha256'],
        parent_access=False,training_ingestion=False,base_and_adapter_unchanged=True,finished_unix=time.time()))


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('action',choices=['prepare','train','readout'])
    parser.add_argument('--arm',choices=['FULL','CONTROL'])
    parser.add_argument('--index',type=int)
    parser.add_argument('--rank',type=int,default=0)
    parser.add_argument('--world-size',type=int,default=1)
    parser.add_argument('--segment',type=int,default=0)
    parser.add_argument('--resume',type=Path)
    parser.add_argument('--condition',choices=['ON','OFF'])
    options=parser.parse_args()
    if options.action=='prepare':
        prepare()
    elif options.action=='train':
        train(options.arm,options.index,options.rank,options.world_size,options.segment,options.resume)
    else:
        readout(options.arm,options.index,options.condition,options.segment,options.resume)
