"""Separate fixed-slot captures; original C2 birth and slot-local TRAIN witness."""

import json
import os
from pathlib import Path
import sys
import time

import preparation_io as common
from c2_capture import record
from discover import SOURCE, validate_pointer


BASE = 'a2367093892219a833eea1bc7b3e0e2069bcaecad335df357809679d272f4992'
PRIOR = common.REMOTE/'source_capture2/capture'
PRIOR_SHA = 'c7ec6afb15ebf082f78867fd2f459441b2a22a300b2e9c982ef455e26d2896de'


def validate_sleep(document,commit,context,sleep):
    common.require(sleep in range(34,39) and document['kind']=='SLEEP_COMPLETE','fixed_followup_sleep_only')
    body = document['document']
    state = body['resume_state']
    common.require(body['cycle']==sleep and body['status']=='COMPLETE' and body['checkpoint']==commit,
        'fixed_sleep_original_COMMIT_join')
    common.require(state['sha256']==common.digest(state['state']) and
        state['state']['model_state_sha256']==common.digest(commit['checkpoint_sha256']), 'completed_state_binding')
    common.require(state['state']['pending'] is None and len(state['state']['sleep_receipts'])==sleep and
        state['state']['sleep_frontier']==len(state['state']['rows']) and
        state['state']['sleep_receipts'][-1]=={field:value for field,value in body.items() if field!='resume_state'},
        'complete_sleep_no_pending_updates')
    history = state['state']['history']
    common.require(all(history[field]==context[field] for field in context),'original_not_living_birth_context')
    common.require(all(event.get('split')=='TRAIN' and event.get('origin')=='TRAIN_COLLECTION'
        for event in history['events']), 'selected_checkpoint_TRAIN_only')
    return history


def capture(request,slot,operation):
    pointer = validate_pointer(slot['pointer'],slot['sleep'])
    sleep = pointer['sleep']
    originals = ['BIRTH.private.json','evidence/BIRTH_RECORD.private.json','evidence/BIRTH_INTENT.json',
        'evidence/ORIGINAL_PLAN.private.json','evidence/JOURNAL.json','evidence/INITIAL_COMMIT.json','evidence/CUSTODY.json']
    paths = [PRIOR/'COMPLETE.json']+[PRIOR/name for name in originals]+[Path(pointer[field]['path'])
        for field in ('commit','record','intent')]+[SOURCE/'stream/records/00000000000000000000.json']
    reader = common.Reader(operation,slot['allowances'],paths)
    common.write(operation/'ONCE.json',dict(life_id='C2',sleep=sleep,started_unix=time.time(),model_calls=0,provider_calls=0))
    try:
        prior,prior_ref,prior_raw = reader.document(PRIOR/'COMPLETE.json',PRIOR_SHA)
        inherited = {}
        for name in originals:
            raw = reader.raw(PRIOR/name)
            common.require(common.sha(raw)==prior['files'][name]['sha256'],'immutable_original_birth_custody_copy')
            inherited[name] = raw
        context = json.loads(inherited['BIRTH.private.json'])
        common.require(set(context)=={'system_prompt','birth_prompt'},'original_birth_only_fields')
        birth,birth_ref,birth_raw = reader.document(SOURCE/'stream/records/00000000000000000000.json',
            prior['files']['evidence/BIRTH_RECORD.private.json']['sha256'])
        common.require(birth_raw==inherited['evidence/BIRTH_RECORD.private.json'] and birth['index']==0 and
            birth['kind']=='COMMITTED' and birth['document']['kind']=='BIRTH','actual_original_BIRTH_not_activation')
        initial = birth['document']['state']
        common.require(initial['sha256']==common.digest(initial['state']) and not initial['state']['rows'] and
            all(initial['state']['history'][field]==context[field] for field in context),'untouched_original_birth_state')
        plan = json.loads(inherited['evidence/ORIGINAL_PLAN.private.json'])
        common.require(plan['root']==str(SOURCE) and all(plan[field]==context[field] for field in context),'original_plan_birth_join')
        initial_commit = json.loads(inherited['evidence/INITIAL_COMMIT.json'])
        common.require(initial_commit['base_sha256']==BASE and initial_commit['optimizer_steps']==0 and
            common.digest(initial_commit['checkpoint_sha256'])==initial['state']['model_state_sha256'],'initial_model_state_join')
        commit,commit_ref,commit_raw = reader.document(pointer['commit']['path'],pointer['commit']['sha256'])
        adapter = SOURCE/f'checkpoints/sleep_{sleep:06d}/adapter'
        common.require(commit['schema']=='R125_NATIVE_CONTINUITY_V1' and commit['base_sha256']==BASE and
            commit['adapter_path']==str(adapter) and common.digest(commit['adapter_files'])==commit['checkpoint_sha256']['adapter'],
            'same_native_base_adapter_inventory')
        journal = json.loads(inherited['evidence/JOURNAL.json'])
        document,boundary_ref,record_raw,intent_raw = record(reader,Path(pointer['record']['path']),pointer['record']['sha256'],journal)
        common.require(document['index']==int(Path(pointer['record']['path']).stem) and
            boundary_ref['intent']['sha256']==pointer['intent']['sha256'],'exact_record_index_intent_join')
        history = validate_sleep(document,commit,context,sleep)
        inventory = commit['adapter_files']
        common.require({'adapter_config.json','adapter_model.safetensors'}<=set(inventory)<=
            {'adapter_config.json','adapter_model.safetensors','README.md'}, 'exact_adapter_only_inventory')
        common.require({path.name for path in adapter.iterdir()}==set(inventory) and
            sum((adapter/name).lstat().st_size for name in inventory)<=128*common.MIB,'complete_bounded_adapter_files')
        destination = operation/'capture'
        destination.mkdir(mode=0o700,exist_ok=False)
        files = {}
        for name,checksum in sorted(inventory.items()):
            path = adapter/name
            reader.allowed_paths.add(path)
            raw = reader.raw(path,'adapter',128*common.MIB)
            common.require(common.sha(raw)==checksum,'fixed_source_adapter_hash')
            files['adapter/'+name] = common.write(destination/'adapter'/name,raw)
        for name,raw in inherited.items():
            files[name] = common.write(destination/name,raw)
        files['COMMIT.original.json'] = common.write(destination/'COMMIT.original.json',commit_raw)
        files['MANIFEST.json'] = common.write(destination/'MANIFEST.json',dict(schema='R130_CHECKPOINT_MANIFEST_V1',
            adapter_path='adapter',commit_path='COMMIT.original.json',commit_sha256=commit_ref['sha256']))
        files['evidence/SLEEP_RECORD.private.json'] = common.write(destination/'evidence/SLEEP_RECORD.private.json',record_raw)
        files['evidence/SLEEP_INTENT.json'] = common.write(destination/'evidence/SLEEP_INTENT.json',intent_raw)
        witnesses = [dict(event_index=index,text=event['text'],text_sha256=common.sha(event['text'].encode()))
            for index,event in enumerate(history['events']) if event.get('actor')=='child']
        files['TRAIN_WITNESSES.private.json'] = common.write(destination/'TRAIN_WITNESSES.private.json',
            dict(witnesses=witnesses,context=context,parent_access=False,source_record=pointer['record'],
                lexical='NOT_APPLIED_NONCOVERAGE_NOT_NEGATIVE'))
        files['BOUNDARY.json'] = common.write(destination/'BOUNDARY.json',dict(life_id='C2',sleep=sleep,
            source_root=str(SOURCE),commit=commit_ref,record=boundary_ref,birth=birth_ref,context_sha256=common.digest(context),
            original_custody_capture=prior_ref,live_process_reobserved=False,
            custody_kind='ARCHIVED_SOURCE_COMMIT_AND_COMPLETED_RECORD_WITH_PRIOR_VERIFIED_ORIGINAL_BIRTH',
            new_living_context_used=False,observed_unix=time.time()))
        complete = common.write(destination/'COMPLETE.json',dict(status='FIXED_C2_FOLLOWUP_SOURCE_CAPTURE_VERIFIED',
            life_id='C2',sleep=sleep,scope_sha256=common.SCOPE_SHA,proposal_sha256=common.PINS['PROPOSAL.json'],
            slots_sha256=common.PINS['SLOTS.json'],files=files,original_capture_allowance=slot['allowances']['adapter'],
            observed_unix=time.time(),parent_access=False,model_calls=0,provider_calls=0,optimizer_rng_read=False))
        result = dict(status='FIXED_C2_FOLLOWUP_SOURCE_CAPTURE_VERIFIED',life_id='C2',sleep=sleep,
            complete=complete,observed_unix=time.time(),model_calls=0,provider_calls=0,
            actual_bytes=reader.actual,charged_bytes=reader.charged,read_count=reader.sequence,
            original_birth_verified=True,slot_local_witness_frozen=True,live_process_reobserved=False,
            receiving_verified=False,execution_authorized=False)
    except Exception as error:
        result = dict(status='FAILED_FIXED_CAPTURE_PRESERVED_NO_RETRY',life_id='C2',sleep=sleep,
            reason=str(error) if isinstance(error,ValueError) else 'FIXED_CAPTURE_FAILURE',error_type=type(error).__name__,
            actual_bytes=reader.actual,charged_bytes=reader.charged,observed_unix=time.time(),model_calls=0,provider_calls=0)
    common.write(operation/'PUBLIC_METADATA.json',result)
    return result


def main():
    os.umask(0o077)
    root = common.REMOTE/'subsequent_slots1/capture_batch1'
    request = json.loads((root/'REQUEST.json').read_bytes())
    common.require(request['scope_sha256']==common.SCOPE_SHA,'same_bounded_preparation_scope')
    for name,checksum in request['source_pins'].items():
        common.require(common.sha((root/'source'/name).read_bytes())==checksum,'frozen_new_capture_source')
    common.write(root/'ONCE.json',dict(started_unix=time.time(),fixed_slots=[slot['sleep'] for slot in request['slots']],
        model_calls=0,provider_calls=0))
    rows = []
    for slot in request['slots']:
        operation = root/f"C2_{slot['sleep']:06d}"
        operation.mkdir(mode=0o700,exist_ok=False)
        rows.append(capture(request,slot,operation))
    result = dict(status='FIXED_CAPTURE_BATCH_TERMINAL',rows=rows,observed_unix=time.time(),model_calls=0,provider_calls=0)
    common.write(root/'PUBLIC_METADATA.json',result)
    print(json.dumps(result,sort_keys=True))


if __name__=='__main__':
    main()
