"""Single exact C2 sleep33 preparation; never loads a model or calls a provider."""

import json
import os
from pathlib import Path
import sys
import time

import preparation_io as common


SOURCE = Path('/localhome/local-rohing/orch_r153_community_C2_20260916_attempt1/life')
CUSTODY = Path('/localhome/local-rohing/orch_r172_forward_probes_20260917_generation1/source_controls/C2/FRESH_CUSTODY.json')
CUSTODY_SHA = '0bcf2d69cfeecc3cec6b4c5ab8436fa2a62d6220dd337d82a172ed1fd0d667fc'
COMMIT = SOURCE/'checkpoints/sleep_000033/COMMIT.json'
COMMIT_SHA = '38067e8619851f556e49b3e3c26f307fd1b4abfd700fcb64d4cdde18a91dc70f'
RECORD = SOURCE/'stream/records/00000000000000003741.json'
RECORD_SHA = '9414fd58eae837f06363983f82e0f8930534343d89752a7c546161985248684c'
BASE = 'a2367093892219a833eea1bc7b3e0e2069bcaecad335df357809679d272f4992'


def custody_plan_path(custody):
    reference = custody['registry_birth_plan']
    path = Path(reference['path'])
    common.require(path.is_absolute() and '..' not in path.parts and
        path.is_relative_to('/localhome/local-rohing') and path.name == 'PLAN.json' and
        isinstance(reference['sha256'],str) and len(reference['sha256']) == 64,
        'custody_bound_original_plan_reference')
    return path


def record(reader, path, checksum, journal):
    document, reference, raw = reader.document(path, checksum)
    intent, intent_ref, intent_raw = reader.document(path.with_suffix('.intent.json'))
    common.require(document['schema'] == journal['schema'] and document['journal_id'] == journal['journal_id']
        and document['sha256'] == common.digest({key:value for key,value in document.items() if key != 'sha256'}),
        'record_content_binding')
    common.require(intent == dict(schema=document['schema'], journal_id=document['journal_id'],
        index=document['index'], previous_sha256=document['previous_sha256'], record_sha256=document['sha256']),
        'record_intent_binding')
    return document, dict(record=reference, intent=intent_ref), raw, intent_raw


def validate_sleep(document, commit, context):
    common.require(document['kind'] == 'SLEEP_COMPLETE', 'exact_completed_sleep_kind')
    body = document['document']
    state = body['resume_state']
    common.require(body['cycle'] == 33 and body['status'] == 'COMPLETE' and body['checkpoint'] == commit,
        'fixed_sleep_COMMIT_join')
    common.require(state['sha256'] == common.digest(state['state']) and
        state['state']['model_state_sha256'] == common.digest(commit['checkpoint_sha256']), 'resume_state_binding')
    common.require(len(state['state']['sleep_receipts']) == 33 and
        state['state']['sleep_frontier'] == len(state['state']['rows']) and
        state['state']['sleep_receipts'][-1] == {key:value for key,value in body.items() if key != 'resume_state'},
        'complete_sleep_frontier_receipt')
    history = state['state']['history']
    common.require(all(history[field] == context[field] for field in context), 'completed_original_birth')
    common.require(all(event.get('split') == 'TRAIN' and event.get('origin') == 'TRAIN_COLLECTION'
        for event in history['events']), 'TRAIN_only_bound_witness')
    return history


def capture(request, operation):
    expected_identity = request['native_identity']
    process = Path('/proc')/str(expected_identity['pid'])
    birth_path = SOURCE/'stream/records/00000000000000000000.json'
    paths = {CUSTODY, COMMIT, RECORD, RECORD.with_suffix('.intent.json'), SOURCE/'stream/JOURNAL.json',
        birth_path, birth_path.with_suffix('.intent.json'), SOURCE/'checkpoints/initial/COMMIT.json',
        process/'stat', process/'cmdline', Path('/proc/sys/kernel/random/boot_id')}
    reader = common.Reader(operation, request['allowances'], paths)
    try:
        custody, custody_ref, custody_raw = reader.document(CUSTODY, CUSTODY_SHA)
        original_plan = custody_plan_path(custody)
        reader.allowed_paths.add(original_plan)
        first_stat = reader.proc(process/'stat').decode().rsplit(')',1)[1].split()
        argv = reader.proc(process/'cmdline')
        boot_id = reader.proc('/proc/sys/kernel/random/boot_id').decode().strip()
        identity = dict(pid=expected_identity['pid'], start_ticks=first_stat[19], boot_id=boot_id,
            argv_sha256=common.sha(argv), cwd=os.readlink(process/'cwd'), uid=process.stat().st_uid)
        common.require(all(identity[field] == expected_identity[field] for field in identity), 'exact_live_native_identity')
        common.require(first_stat[0] not in ('Z','X'), 'live_nonterminal_native')
        plan, plan_ref, plan_raw = reader.document(original_plan, custody['registry_birth_plan']['sha256'])
        journal, journal_ref, journal_raw = reader.document(SOURCE/'stream/JOURNAL.json', custody['journal']['sha256'])
        birth, birth_ref, birth_raw, birth_intent_raw = record(reader,birth_path,
            custody['initial_record']['record']['sha256'],journal)
        common.require(birth['index'] == 0 and birth['previous_sha256'] == common.digest(journal) and birth['kind'] == 'COMMITTED'
            and birth['document']['kind'] == 'BIRTH', 'original_birth_record')
        initial = birth['document']['state']
        common.require(initial['sha256'] == common.digest(initial['state']) and not initial['state']['rows'],
            'untouched_original_birth_state')
        context = {field:initial['state']['history'][field] for field in ('system_prompt','birth_prompt')}
        common.require(plan['root'] == str(SOURCE) and all(plan[field] == context[field] for field in context)
            and common.digest(context) == custody['birth_context_digest'], 'original_plan_context_join')
        initial_commit, initial_commit_ref, initial_commit_raw = reader.document(SOURCE/'checkpoints/initial/COMMIT.json',
            custody['initial_commit']['reference']['sha256'])
        common.require(initial_commit['optimizer_steps'] == 0 and initial_commit['base_sha256'] == BASE and
            common.digest(initial_commit['checkpoint_sha256']) == initial['state']['model_state_sha256'], 'birth_initial_COMMIT_join')
        commit, commit_ref, commit_raw = reader.document(COMMIT, COMMIT_SHA)
        common.require(commit['schema'] == 'R125_NATIVE_CONTINUITY_V1' and commit['base_sha256'] == BASE and
            commit['adapter_path'] == str(COMMIT.parent/'adapter') and
            common.digest(commit['adapter_files']) == commit['checkpoint_sha256']['adapter'], 'native_checkpoint_identity')
        document, boundary_ref, record_raw, intent_raw = record(reader, RECORD, RECORD_SHA, journal)
        history = validate_sleep(document, commit, context)
        destination = operation/'capture'
        destination.mkdir(mode=0o700)
        inventory = commit['adapter_files']
        common.require({'adapter_config.json','adapter_model.safetensors'} <= set(inventory) and
            all(Path(name).name == name and name not in ('.','..') and len(checksum) == 64
                for name,checksum in inventory.items()), 'exact_safe_adapter_inventory')
        adapter = COMMIT.parent/'adapter'
        common.require(set(path.name for path in adapter.iterdir()) == set(inventory), 'complete_adapter_inventory')
        common.require(sum((adapter/name).lstat().st_size for name in inventory) <= 128*common.MIB,
            'checkpoint_adapter_hard_cap')
        files = {}
        for name,checksum in sorted(inventory.items()):
            source = adapter/name
            reader.allowed_paths.add(source)
            raw = reader.raw(source, 'adapter', 128*common.MIB)
            common.require(common.sha(raw) == checksum, 'source_adapter_hash')
            files['adapter/'+name] = common.write(destination/'adapter'/name,raw)
        commit_copy = common.write(destination/'COMMIT.original.json',commit_raw)
        files['COMMIT.original.json'] = commit_copy
        files['MANIFEST.json'] = common.write(destination/'MANIFEST.json',dict(schema='R130_CHECKPOINT_MANIFEST_V1',
            adapter_path='adapter',commit_path='COMMIT.original.json',commit_sha256=commit_copy['sha256']))
        files['BIRTH.private.json'] = common.write(destination/'BIRTH.private.json',context)
        witnesses = [dict(event_index=index,text=event['text'],text_sha256=common.sha(event['text'].encode()))
            for index,event in enumerate(history['events']) if event.get('actor') == 'child']
        files['TRAIN_WITNESSES.private.json'] = common.write(destination/'TRAIN_WITNESSES.private.json',
            dict(witnesses=witnesses,context=context,parent_access=False,source_record=boundary_ref['record'],
                lexical='NOT_APPLIED_NONCOVERAGE_NOT_NEGATIVE'))
        private_sources = {'CUSTODY.json':custody_raw,'ORIGINAL_PLAN.private.json':plan_raw,'JOURNAL.json':journal_raw,
            'BIRTH_RECORD.private.json':birth_raw,'BIRTH_INTENT.json':birth_intent_raw,
            'INITIAL_COMMIT.json':initial_commit_raw,'SLEEP_RECORD.private.json':record_raw,'SLEEP_INTENT.json':intent_raw}
        for name, raw in private_sources.items():
            files['evidence/'+name] = common.write(destination/'evidence'/name,raw)
        last_stat = reader.proc(process/'stat').decode().rsplit(')',1)[1].split()
        common.require(last_stat[19] == first_stat[19] and last_stat[0] not in ('Z','X'), 'identity_stable_during_capture')
        boundary = dict(life_id='C2',sleep=33,commit=commit_ref,record=boundary_ref,original_birth=birth_ref,
            birth_plan=plan_ref,context_sha256=common.digest(context),custody=custody_ref,
            native_identity=identity,observed_unix=time.time(),source_root=str(SOURCE),parent_access=False)
        files['BOUNDARY.json'] = common.write(destination/'BOUNDARY.json',boundary)
        complete = common.write(destination/'COMPLETE.json',dict(status='FIXED_C2_SLEEP33_SOURCE_CAPTURE_VERIFIED',
            scope_sha256=common.SCOPE_SHA,proposal_sha256=common.PINS['PROPOSAL.json'],
            slots_sha256=common.PINS['SLOTS.json'],life_id='C2',sleep=33,files=files,
            original_capture_allowance=request['allowances']['adapter'],observed_unix=time.time(),
            model_calls=0,provider_calls=0,optimizer_rng_read=False,source_hash_reread=False,parent_access=False))
        return dict(status='FIXED_C2_SLEEP33_SOURCE_CAPTURE_VERIFIED',capture_complete=complete,
            source_path=str(destination),life_id='C2',sleep=33,model_calls=0,provider_calls=0,
            receiving_verified=False,execution_authorized=False,observed_unix=time.time(),
            charged_bytes=reader.charged,actual_bytes=reader.actual,read_count=reader.sequence,
            private_witness_frozen=True,original_birth_verified=True)
    except BaseException as error:
        return dict(status='FAILED_CAPTURE_PRESERVED_NO_RETRY',error_type=type(error).__name__,
            reason=str(error) if isinstance(error,ValueError) else 'SOURCE_CAPTURE_FAILURE',
            observed_unix=time.time(),life_id='C2',sleep=33,model_calls=0,provider_calls=0,
            charged_bytes=reader.charged,actual_bytes=reader.actual,read_count=reader.sequence)


def main():
    os.umask(0o077)
    operation = Path(__file__).resolve().parent.parent
    common.require(operation in (common.REMOTE/'source_capture1', common.REMOTE/'source_capture2'),
        'fixed_source_operation_path')
    request = json.loads((operation/'REQUEST.json').read_bytes())
    common.validate_controls(operation/'control')
    for name, checksum in request['source_pins'].items():
        common.require(common.sha((operation/'source'/name).read_bytes()) == checksum, 'source_code_pin')
    common.write(operation/'ONCE.json',dict(started_unix=time.time(),model_calls=0,provider_calls=0))
    result = capture(request, operation)
    common.write(operation/'PUBLIC_METADATA.json',result)
    print(json.dumps(result,sort_keys=True))
    return 0 if result['status'] == 'FIXED_C2_SLEEP33_SOURCE_CAPTURE_VERIFIED' else 2


if __name__ == '__main__':
    sys.exit(main())
