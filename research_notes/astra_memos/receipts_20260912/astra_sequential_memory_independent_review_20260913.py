"""Offline independent sequential-memory audit; no model/native imports or writes outside owned JSON."""
import argparse
import ast
from collections import Counter
import copy
import datetime as dt
import hashlib
import json
import math
from pathlib import Path, PurePosixPath
import random
import re
import tarfile
import xml.etree.ElementTree as ET

CAPSULE = Path('/tmp/astra_sequential_memory_seed0_pair_attempt2_terminal_20260913T0000Z.tgz')
CAPSULE_SHA = 'c63437c47918603d5b784544bcae85e7febc93ec7516677eaa9a3608b78b2fb0'
PLAN_SHA = '9e53c716373c2458586ff7b6a72d0fe5822d41d5a0129057e2a4e805acab8b49'
SOURCE = '5a1f300fed4b7f1ef54524869c2bf11509e965ca'
OUTPUT = Path('/tmp/astra_sequential_memory_independent_review_20260913.json')
STATES = ('S0', 'R1', 'NEW_ONLY1', 'R2', 'NEW_ONLY2')
PARENTS = {'R1':'S0', 'NEW_ONLY1':'S0', 'R2':'R1', 'NEW_ONLY2':'NEW_ONLY1'}
STEPS = {'S0':400, 'R1':720, 'NEW_ONLY1':720, 'R2':1040, 'NEW_ONLY2':1040}
COLORS = {'blue', 'green', 'red', 'yellow'}
COLOR_ORDER = ('blue', 'green', 'red', 'yellow')
ADDITION_IDS = tuple('train-addition-'+suffix for suffix in ('011','039','055','029','048','000','052','017','036','046','063','019','057','030','012','015'))
CHAT_HEAD = '<|im_start|>system\nYou are Qwen, created by Alibaba Cloud. You are a helpful assistant.<|im_end|>\n<|im_start|>user\n'
CHAT_TAIL = '<|im_end|>\n<|im_start|>assistant\n'


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(payload):
    return hashlib.sha256(payload).hexdigest()


def encoded(value, pretty=True):
    return (json.dumps(value, sort_keys=True, indent=2 if pretty else None, ensure_ascii=False, allow_nan=False)+'\n').encode()


def unique(pairs):
    result = {}
    for key,value in pairs:
        require(key not in result, 'duplicate JSON key')
        result[key] = value
    return result


def decode(payload):
    return json.loads(payload, object_pairs_hook=unique)


def flattened(value):
    if isinstance(value,dict):
        return [item for child in value.values() for item in flattened(child)]
    if isinstance(value,list):
        return [item for child in value for item in flattened(child)]
    return [value]


def load_capsule():
    require(sha(CAPSULE.read_bytes()) == CAPSULE_SHA, 'Main capsule pin')
    files = {}
    with tarfile.open(CAPSULE) as archive:
        members = archive.getmembers()
        require(len(members) <= 2000 and sum(member.size for member in members) < 100*1024*1024, 'metadata bounds')
        for member in members:
            require(member.isfile() and member.name.removeprefix('seed0_pair_attempt2/') not in files and '\\' not in member.name
                and all(part not in ('', '.', '..') for part in member.name.split('/'))
                and member.name.startswith('seed0_pair_attempt2/'), 'unsafe member')
            require(PurePosixPath(member.name).suffix not in ('.safetensors','.bin','.pt','.pth','.pyc','.pyo'), 'weights/bytecode present')
            files[member.name.removeprefix('seed0_pair_attempt2/')] = archive.extractfile(member).read()
    return files


def material_audit(read, digest, plan):
    candidate, native = read('inputs/material/candidate.json'), read('inputs/material/token_audit.json')
    original = read('inputs/original_teach.json')['corpus']
    require(digest('inputs/original_teach.json') == '2d12bb35d44279c3412323472bb716581c9ed57a966bb829290a49c4d799de7c', 'original material bytes')
    for name, expected in plan['material']['files'].items():
        require(digest('inputs/material/'+name) == expected, 'material file seal')
    require(sha(encoded(candidate)) == native['candidate_sha256'] == plan['material']['candidate_sha256'], 'candidate identity')
    banks = candidate['banks']
    require(set(banks) == {'M0','B1','B2'}, 'three banks required')
    events = {row['id']:row for row in candidate['source_records']}
    require(len(events) == len(candidate['source_records']), 'duplicate event')
    labels = {}
    for bank,rows in banks.items():
        require(len(rows) == 16 and Counter(row['response'] for row in rows) == {color:4 for color in COLORS}, 'balanced bank')
        for row in rows:
            event = events[row['source_event_ids'][0]]
            require(event['device'] == row['device'] and event['color'] == row['response'] and row['device'] not in labels, 'unique truth join')
            labels[row['device']] = row['response']
        if bank != 'M0':
            domain = {'B1':'sequential-authored-bank-one-20260912','B2':'sequential-authored-bank-two-20260912'}[bank]
            permutation = sorted(range(16), key=lambda index:sha(f'{domain}:{index:02d}'.encode()))
            mapping = {index:COLOR_ORDER[position%4] for position,index in enumerate(permutation)}
            require([row['device'] for row in rows] == [f'device-{(100 if bank=="B1" else 200)+index:03d}' for index in range(16)], 'bank key domain')
            require([row['response'] for row in rows] == [mapping[index] for index in range(16)], 'fixed mapping algorithm')
    original_memory = {}
    for item in original:
        if item['view'] == 'memory':
            device = re.search(r'device-\d{3}',item['spans'][0][0])[0]
            original_memory[device] = item['spans'][1][0]
    require({row['device']:row['response'] for row in banks['M0']} == original_memory, 'old bank changed')
    arithmetic = {row['case_id']:row for row in candidate['cycles']['1']['R'] if row['kind']=='addition'}
    require(set(arithmetic) == set(ADDITION_IDS), 'selected arithmetic sources changed')
    additions = [arithmetic[key] for key in ADDITION_IDS]
    summaries = {}
    for cycle in ('1','2'):
        for arm in ('R','NEW_ONLY'):
            state = arm+cycle
            rows = candidate['cycles'][cycle][arm]
            require(len(rows)==128, '128 rows per fit')
            expected_ids = []
            for color_index,color in enumerate(COLOR_ORDER):
                current = [row for row in banks['B'+cycle] if row['response']==color]
                old = [row for row in banks['M0'] if row['response']==color]
                replay = old*2 if cycle=='1' else old+[row for row in banks['B1'] if row['response']==color]
                for occurrence in range(8):
                    group = color_index*8+occurrence
                    expected_ids.extend(row['case_id'] for row in (current[occurrence%4], additions[(2*group)%16],
                        replay[occurrence] if arm=='R' else current[(occurrence+1)%4], additions[(2*group+1)%16]))
            require([row['case_id'] for row in rows] == expected_ids, 'fixed allocation/layout')
            fit = native['fits'][cycle][arm]
            corpus = read(f'inputs/material/cycle{cycle}_{arm}.json')['corpus']
            reconstructed = []
            for index,(row,receipt) in enumerate(zip(rows,fit['rows'],strict=True)):
                group = f'sequential-v1-c{cycle}-g{index//4:02d}'
                require(row['batch_group']==group and row['batch_slot']==index%4, 'ordered four-row group')
                expected = dict(group=group, order=index%4, view=row['kind'],
                    spans=[[CHAT_HEAD+row['context']+CHAT_TAIL,False,'context'],[row['response'],True,'authored_birth_target']],
                    meta=dict(source_event_ids=row['source_event_ids'],sequential_memory=dict(
                        protocol='AUTHORED_SEQUENTIAL_MEMORY_FIXED_BUDGET_V1',record_id=row['id'],bank=row['bank'],
                        source_record_id=row['source_record_id'],source_row_index=row['source_row_index'],
                        source_row_sha256=row['source_row_sha256'],authored_not_child=True)))
                reconstructed.append(expected)
                if row['source_row_index'] is not None:
                    orig = original[row['source_row_index']]
                    require(orig['spans']==expected['spans'] and orig['meta']['source_event_ids']==row['source_event_ids'], 'original source/render/target changed')
                    baseline = native['original_selected_native_rows'][str(row['source_row_index'])]
                    require(all(receipt[key]==value for key,value in baseline.items()), 'original native prefix/mask changed')
                require(receipt['response']==row['response'] and receipt['rendered_context']==expected['spans'][0][0], 'native row labels/prefix')
                require(receipt['input_ids']==receipt['prefix_token_ids']+receipt['target_with_eos']
                    and receipt['target_with_eos']==receipt['response_token_ids']+[native['eos_token_id']]
                    and receipt['labels']==[-100]*len(receipt['prefix_token_ids'])+receipt['target_with_eos'], 'stored causal target mask/EOS')
                require(receipt['input_tokens']==len(receipt['input_ids']) and receipt['context_tokens']==len(receipt['prefix_token_ids'])
                    and receipt['target_tokens']==len(receipt['target_with_eos']), 'native lengths')
                require(receipt['raw_context_utf8_sha256']==sha(row['context'].encode()) and receipt['raw_target_utf8_sha256']==sha(row['response'].encode()), 'row byte joins')
                if row['kind']=='memory':
                    require(row['response']==labels[row['device']] and receipt['target_tokens']==2, 'memory truth/EOS targets')
            require(reconstructed==corpus and sha(encoded({'corpus':corpus}))==fit['corpus_sha256'], 'corpus byte reconstruction')
            updates,exposures=[],Counter()
            for epoch in range(10):
                order=list(range(32));random.Random(epoch).shuffle(order)
                for batch,group_index in enumerate(order):
                    indices=list(range(group_index*4,group_index*4+4));batchrows=[rows[index] for index in indices];receipts=[fit['rows'][index] for index in indices]
                    require(len({row['case_id'] for row in batchrows})==4 and Counter(row['kind'] for row in batchrows)=={'memory':2,'addition':2}, 'batch composition')
                    targets=sum(row['target_tokens'] for row in receipts);inputs=sum(row['input_tokens'] for row in receipts);width=max(row['input_tokens'] for row in receipts)
                    updates.append(dict(epoch=epoch,batch=batch,update_index=len(updates)+1,group=batchrows[0]['batch_group'],item_indices=indices,
                        source_ids=[row['case_id'] for row in batchrows],row_target_tokens=[row['target_tokens'] for row in receipts],
                        target_tokens_by_kind={kind:sum(receipt['target_tokens'] for row,receipt in zip(batchrows,receipts) if row['kind']==kind) for kind in ('memory','addition')},
                        target_tokens=targets,input_tokens=inputs,context_tokens=inputs-targets,padded_width=width,padded_input_slots=4*width,
                        padding_slots=4*width-inputs,masked_slots=4*width-targets))
                    exposures.update(row['case_id'] for row in batchrows)
            require(updates==fit['schedule']['updates'] and dict(exposures)==fit['schedule']['source_presentations'], 'seed0 native schedule differs')
            total={key:sum(row[key] for row in updates) for key in fit['schedule']['total']}
            require(total==fit['schedule']['total'] and all(total[key]==value for key,value in fit['ten_epochs'].items()), 'scheduled totals')
            dose=candidate['manifest']['dose_per_fact_per_fit'][cycle][arm]
            require(all(exposures[row['case_id']]==(40 if row['kind']=='addition' else dose[row['bank']]) for row in rows), 'per-fact dose')
            summaries[state]=dict(schedule_sha256=sha(encoded(updates)),totals=total,per_epoch=fit['per_epoch'],dose=dose,
                source_presentations=dict(exposures),target_by_kind={kind:sum(row['target_tokens_by_kind'][kind] for row in updates) for kind in ('memory','addition')})
        left,right=(native['fits'][cycle][arm] for arm in ('R','NEW_ONLY'))
        require(all(first['target_with_eos']==second['target_with_eos'] and first['raw_target_utf8_sha256']==second['raw_target_utf8_sha256']
            and first['context_tokens']==second['context_tokens'] for first,second in zip(left['rows'],right['rows'],strict=True)), 'paired target IDs/bytes/lengths')
        require(left['schedule']['total']==right['schedule']['total'], 'paired native aggregate compute differs')
    cases=read('inputs/material/readout_cases.json')
    require(cases==candidate['readout_cases']==plan['template']['cases'] and len(cases)==len({row['id'] for row in cases})==128, 'readout membership')
    require(Counter((row.get('bank'),row.get('surface')) for row in cases if row['kind']!='addition')=={(bank,surface):16 for bank in banks for surface in ('exact','dev')}, 'all banks/surfaces')
    return labels,summaries


def panel_audit(state,read,digest,files,plan,labels,adapter_files,adapter):
    root=f'run/panels/{state}/';data=root+'run/data/'
    prepared=read(root+'plan.json');reduced=read(root+'reduction.json')
    require(digest(root+'plan.json')==read(root+'plan.sha256.json')['sha256'], 'panel seal')
    require(prepared['adapter']==adapter and prepared['adapter_files']==adapter_files and prepared['model_files']==plan['model_files']
        and prepared['device']==plan['device'], 'loaded state identity')
    require(all(prepared[key]==plan['template'][key] for key in ('cases','requests','native_inputs','source_hashes')), 'readout interface changed')
    identity=read(data+'identity.json')
    require(identity==dict(backend=prepared['identity'],model_files=plan['model_files'],adapter_files=adapter_files), 'capture identity')
    for name,expected in read(data+'manifest.json')['files'].items():require(digest(data+name)==expected,'capture file hash')
    require(read(data+'backend.cleanup.json')['closed'], 'backend cleanup')
    process=read(root+'run/worker/process.json');supervision=read(root+'run/worker/supervision.json');ready=read(data+'backend.ready.json')
    require(ready['pid']==process['pid'] and 0<=ready['ready']-process['started']<=180, 'load readiness')
    rows=[];previous=ready['ready']
    for case,request,native in zip(prepared['cases'],prepared['requests'],prepared['native_inputs'],strict=True):
        sent=read(data+'calls/'+request['call_id']+'.request.json');received=read(data+'calls/'+request['call_id']+'.response.json');response=received['response']
        require(sent['request']==request and sent['identity']==prepared['identity'] and request['case_id']==case['id'] and request['prompt']==case['context'],'raw request')
        require(sent['prompt_sha256']==sha(encoded(request['prompt'],False)) and received['response_sha256']==sha(encoded(response,False)),'raw hash')
        require(previous<=sent['started']<=received['ended']<=process['started']+supervision['reserved_seconds'] and received['ended']-sent['started']<=120,'raw clocks')
        previous=received['ended']
        require(response['rendered_prompt']==CHAT_HEAD+case['context']+CHAT_TAIL==native['rendered_prompt'] and response['prompt_token_ids']==native['prompt_token_ids'],'causal input/render')
        require(request['seed']==20260912 and request['temperature']==0 and request['max_tokens']==64 and len(response['output_token_ids'])<=64,'generation recipe')
        if case['kind']=='addition':
            match=re.fullmatch(r'Add (\d+) and (\d+)\.\nSubmit the sum using ACT: <integer>\.',request['prompt']);require(match is not None,'arithmetic case')
            expected=int(match[1])+int(match[2]);score=arithmetic_score(response['text'],expected)
        else:
            expected=labels[case['device']];template='Which color does the log assign to {device}?' if case['surface']=='exact' else 'Recall the logged color of {device}.'
            require(request['prompt']==template.format(device=case['device']),'memory query surface')
            score=memory_score(response['text'],expected)
        require(expected==case['expected'],'independent truth differs')
        rows.append(dict(case_id=case['id'],kind=case['kind'],bank=case.get('bank'),surface=case.get('surface'),device=case.get('device'),
            expected=expected,raw_text=response['text'],prompt=request['prompt'],**score,input_tokens=len(response['prompt_token_ids']),
            output_tokens=len(response['output_token_ids']),output_ids_sha256=sha(encoded(response['output_token_ids'])),seconds=received['ended']-sent['started'],
            finish_reason=response['finish_reason'],cap_hit=len(response['output_token_ids'])==64))
    require(len(rows)==128 and sum(name.startswith(data+'calls/') for name in files)==256,'128 complete calls')
    arithmetic=[row for row in rows if row['kind']=='addition']
    counts=dict(total=128,memory={bank:{surface:dict(total=16,correct=sum(row['correct'] for row in rows if row['bank']==bank and row['surface']==surface),
        invalid=sum(not row['valid'] for row in rows if row['bank']==bank and row['surface']==surface)) for surface in ('exact','dev')} for bank in ('M0','B1','B2')},
        addition=dict(total=32,correct_action=sum(row['correct_action'] for row in arithmetic),adherence=sum(row['adherence'] for row in arithmetic)))
    discrepancies=[]
    if counts!=reduced['counts']:discrepancies.append('aggregate counts differ')
    stored={row['case_id']:row for row in reduced['rows']};require(len(stored)==128,'stored rows cardinality')
    for row in rows:
        if any(row[key]!=value for key,value in stored[row['case_id']].items()):discrepancies.append('case '+row['case_id'])
    cost=dict(requests=128,native_input_tokens=sum(row['input_tokens'] for row in rows),native_output_tokens=sum(row['output_tokens'] for row in rows),
        generation_seconds=sum(row['seconds'] for row in rows),output_token_ceiling=8192)
    usage=read(data+'usage.json');require(len(usage)==1,'unexpected generation role')
    require(all(math.isclose(value,next(iter(usage.values()))[key],abs_tol=1e-7) for key,value in cost.items()),'raw cost mismatch')
    surface_discordance={bank:[dict(device=exact['device'],exact=exact['raw_text'],dev=dev['raw_text'],expected=exact['expected'])
        for exact in rows if exact['bank']==bank and exact['surface']=='exact'
        for dev in rows if dev['bank']==bank and dev['surface']=='dev' and dev['device']==exact['device'] and exact['raw_text']!=dev['raw_text']] for bank in ('M0','B1','B2')}
    return dict(counts=counts,rows=rows,discrepancies=discrepancies,cost=cost,surface_discordance=surface_discordance,
        arithmetic_format={key:sum(row[key] for row in arithmetic) for key in ('action_valid','prediction_valid','predict_before_act')},
        caps=sum(row['cap_hit'] for row in rows),finish_reasons=dict(Counter(row['finish_reason'] for row in rows)),
        output_lengths=dict(Counter(row['output_tokens'] for row in rows)),
        adapter_files=adapter_files,worker_seconds=supervision['reserved_seconds'],backend_ready_seconds=ready['ready']-process['started'])


def memory_score(text, expected):
    answer = text.strip().lower()
    if answer.endswith('.'):
        answer = answer[:-1]
    valid = answer in COLORS
    return dict(normalized=answer, answer=answer if valid else None, valid=valid,
                correct=valid and answer == expected)

def arithmetic_score(text, expected):
    matches = {}
    for label in ('ACT', 'PREDICT'):
        values = []
        for index, line in enumerate(text.splitlines()):
            if re.match(r'^[ \t]*' + label + r'\b', line):
                match = re.fullmatch(r'[ \t]*' + label + r':[ \t]*([+-]?[0-9]+)[ \t]*', line)
                values.append((index, int(match[1]) if match else None))
        matches[label] = values
    acts, predicts = matches['ACT'], matches['PREDICT']
    action_valid = len(acts) == 1 and acts[0][1] is not None
    prediction_valid = len(predicts) == 1 and predicts[0][1] is not None
    first_act = acts[0][1] if acts else None
    first_predict = predicts[0][1] if predicts else None
    before = bool(action_valid and prediction_valid and predicts[0][0] < acts[0][0])
    correct = action_valid and first_act == expected
    return dict(act_count=len(acts), predict_count=len(predicts), first_act=first_act,
                first_predict=first_predict, action_valid=action_valid, prediction_valid=prediction_valid,
                correct_action=correct, predict_before_act=before,
                adherence=bool(correct and before and first_predict == expected))


def main():
    files=load_capsule()
    def read(name):return decode(files[name])
    def digest(name):return sha(files[name])
    plan=read('plan.json');terminal=read('run/terminal.json');release=read('run/main_release.json');launch=read('launch/launch.json')
    require(digest('plan.json')==PLAN_SHA==read('plan.sha256.json')['sha256']==terminal['plan_sha256']==launch['plan_sha256'],'global plan pin')
    require(plan['source_commit']==SOURCE==launch['source_commit'] and plan['states']==list(STATES) and plan['parents']==PARENTS and plan['cumulative_steps']==STEPS,'fixed lineage')
    require(plan['seed']==plan['parent_seed']==0 and plan['source_branch']=='FOUR_VIEW' and plan['total_calls']==640 and plan['total_workers']==9,'scope')
    require(not any(plan[key] for key in ('automatic_progression','outcome_selective_skips','confirmation_calls')) and plan['reduce_only_after_all_captures'],'no selection/confirmation')
    require(plan['pair_seconds']==5100 and plan['external_custody_seconds']==300 and plan['cleanup_seconds']==140,'bounds')
    require(terminal['status']=='COMPLETE' and terminal['error'] is None and all(terminal[key] for key in ('release_verified','deadline_met','continuous_reservation','worker_accounting_complete')),'complete terminal')
    require(not terminal['gate_evaluated'] and not terminal['budget_extended'] and not terminal['automatic_progression'],'no promotion')
    allowed=set(flattened(plan['source_hashes']))
    for name,payload in files.items():
        if name.startswith('inputs/code/'):
            for node in ast.walk(ast.parse(payload)) if name.endswith('.py') else ():
                if isinstance(node,ast.Constant) and isinstance(node.value,str) and re.fullmatch('[0-9a-f]{64}',node.value):allowed.add(node.value)
    archived_code={name:digest(name) for name in files if name.startswith('inputs/code/')}
    require(all(value in allowed for value in archived_code.values()),'unbound archived helper')
    require(digest('inputs/code/astra_sequential_memory_pair_20260912.py')==plan['source_hashes']['sequential_pair']==launch['script_sha256'],'driver source')
    for name,value in plan['source_hashes'].items():
        if 'inputs/code/'+name in files:require(digest('inputs/code/'+name)==value,'native code source pin')
    s0=plan['s0'];s0manifest=read('inputs/s0/train_manifest.json');s0fit=read('inputs/s0_provenance/1-fit-result.json')
    for index,(path,checksum) in enumerate(s0['provenance'].items()):require(digest(f'inputs/s0_provenance/{index}-{Path(path).name}')==checksum,'S0 provenance bytes')
    require(s0['parent_plan_sha256']==digest('inputs/s0_provenance/0-plan.json') and s0['seed']==0 and s0['branch']=='FOUR_VIEW','S0 original seed/arm')
    require(s0['parent']==s0fit['adapter'] and s0['parent_files']==s0fit['adapter_files'] and s0['model_files']==plan['model_files'],'S0 adapter/base binding')
    require(s0['state']==s0manifest['warm_start']['final_state'] and s0manifest['warm_start']['cumulative_steps']==400 and s0manifest['warm_start']['parent_cumulative_steps']==80,'S0 400-update lineage')
    require(s0fit['manifest_sha256']==digest('inputs/s0/train_manifest.json') and read('inputs/s0_provenance/2-terminal.json')['status']=='COMPLETE','S0 complete custody')
    inventories={'S0':s0['parent_files']};tensors={'S0':s0['state']};paths={'S0':s0['parent']}
    for name,checksum in inventories['S0'].items():
        if not name.endswith('.safetensors'):require(digest('inputs/s0/'+name)==checksum,'S0 metadata identity')
    labels,materials=material_audit(read,digest,plan)
    fits={};workers=[]
    for state in STATES[1:]:
        stage='run/'+state+'/';fit=read(stage+'fit-result.json');binding=read(stage+'input.json');manifest=read(stage+'adapter/train_manifest.json');warm=manifest['warm_start'];parent=PARENTS[state]
        require(fit==terminal['fits'][state] and fit['state']==state and fit['steps']==320 and fit['cumulative_steps']==STEPS[state],'fit terminal identity')
        require(fit['input_sha256']==digest(stage+'input.json') and fit['manifest_sha256']==digest(stage+'adapter/train_manifest.json'),'fit receipt seals')
        require(fit['parent']==binding['parent']==warm['parent_path']==paths[parent] and fit['parent_files']==binding['parent_files']==warm['parent_files']==warm['parent_files_after']==inventories[parent],'immediate immutable parent')
        require(binding['parent_state']==warm['source_state']==warm['initialized_state']==tensors[parent] and not warm['dtype_conversions'],'exact loaded initialization')
        require(warm['final_state']==fit['saved_state'] and set(warm['final_state'])==set(tensors[parent]) and len(warm['final_state'])==392,'saved tensor inventory')
        require(sum(math.prod(tensor['shape']) for tensor in fit['saved_state'].values())==manifest['lora']['trainable_params']==20185088,'adapter parameter count')
        changed=sum(warm['final_state'][name]['sha256']!=value['sha256'] for name,value in tensors[parent].items())
        require(changed>0 and all(warm['final_state'][name]['shape']==value['shape'] and warm['final_state'][name]['dtype']==value['dtype'] for name,value in tensors[parent].items()),'nonempty compatible adapter write')
        require(all(warm[key] for key in ('parent_unchanged','base_frozen','initialized_loaded_state_check')) and warm['adapter_count']==1,'isolation receipts')
        require(warm['phase_seed']==0 and warm['mode']=='WEIGHT_WARM_START_FRESH_OPTIMIZER' and warm['optimizer_initialization']=='fresh_per_write' and warm['optimizer_initial_state_entries']==0 and not warm['optimizer_state_restored'] and not warm['optimizer_state_saved'],'fresh seedmatched optimizer')
        require(warm['parent_cumulative_steps']==STEPS[parent] and warm['phase_steps']==320 and warm['cumulative_steps']==STEPS[state],'cumulative steps')
        require(manifest['config']==plan['config'] and manifest['base_model']==plan['model'] and manifest['steps']==manifest['micro_batches']==320 and manifest['epochs_run']==10,'fit recipe')
        require(not manifest['empty'] and manifest['nonfinite_batches']==0 and math.isfinite(manifest['final_loss']) and manifest['corpus']['n_items']==manifest['corpus']['n_encoded']==128 and manifest['corpus']['n_skipped_no_target']==0,'all native rows trained')
        require(manifest['train_tokens_seen']==66160 and manifest['tokens']['target']==1000 and manifest['tokens']['context']==5616 and manifest['tokens']['total']==6616,'native manifest totals')
        require(all(manifest['truncation'][key]==0 for key in ('items_truncated','context_tokens_dropped','target_tokens_dropped','items_split','segments_from_splits')),'no native truncation')
        require(binding['corpus_sha256']==manifest['corpus']['sha256']==plan['material']['files'][plan['material']['corpus_files'][state]],'trained material')
        require(warm['trainer_sha256']==plan['source_hashes']['train_adapter_v3.py'],'trainer source')
        for name,checksum in fit['adapter_files'].items():
            if not name.endswith('.safetensors'):require(digest(stage+'adapter/'+name)==checksum,'saved nonweight bytes')
        require(files[stage+'adapter/DONE'].strip()==b'ok','DONE receipt')
        inventories[state]=fit['adapter_files'];tensors[state]=fit['saved_state'];paths[state]=fit['adapter']
        fits[state]=dict(parent=parent,adapter=fit['adapter'],adapter_files=fit['adapter_files'],changed_tensors=changed,
            tensor_inventory_sha256=sha(encoded(fit['saved_state'])),steps=320,cumulative_steps=STEPS[state],train_seconds=manifest['train_seconds'],wall_seconds=manifest['wall_seconds'],final_loss=manifest['final_loss'],trainable_parameters=manifest['lora']['trainable_params'])
    panels={}
    for state in STATES:
        panels[state]=panel_audit(state,read,digest,files,plan,labels,inventories[state],paths[state])
        root='run/panels/'+state+'/';capture=read(root+'capture-result.json');reduction=read(root+'reduction.json');binding=read(root+'plan.json')['sequential_binding']
        require(capture==terminal['captured'][state] and capture['pairs']==128 and capture['status']=='CAPTURED_NOT_REDUCED' and capture['capture_sha256']==digest(root+'run/data/manifest.json') and capture['plan_sha256']==digest(root+'plan.json'),'captured complete identity')
        require(reduction==terminal['reductions'][state] and reduction['barrier']==terminal['captured'] and reduction['complete'] and not reduction['gate_evaluated'],'all-five-captures barrier')
        require(reduction['capture_sha256']==capture['capture_sha256'] and reduction['plan_sha256']==capture['plan_sha256'],'reduction inputs')
        require(binding['state']==state and binding['cumulative_steps']==STEPS[state] and binding['parent_seed']==binding['phase_seed']==0 and binding['source_branch']=='FOUR_VIEW' and binding['parent_plan_sha256']==s0['parent_plan_sha256'],'panel state/seed binding')
    worker_order=(('S0','run/panels/S0/run/worker/'),('R1 fit','run/R1/fit-worker/'),('R1','run/panels/R1/run/worker/'),('NEW_ONLY1 fit','run/NEW_ONLY1/fit-worker/'),('NEW_ONLY1','run/panels/NEW_ONLY1/run/worker/'),('R2 fit','run/R2/fit-worker/'),('R2','run/panels/R2/run/worker/'),('NEW_ONLY2 fit','run/NEW_ONLY2/fit-worker/'),('NEW_ONLY2','run/panels/NEW_ONLY2/run/worker/'))
    for label,root in worker_order:
        process=read(root+'process.json');receipt=read(root+'supervision.json')
        require(process['device']==receipt['device']==plan['device'] and process['timeout']==600 and process['pid']==process['pgid'],'worker ownership/bound')
        require(receipt['returncode']==0 and receipt['error'] is None and all(receipt[key] for key in ('ok','gpu_processes_absent','owned_group_empty','reservation_release_verified')),'successful owned cleanup')
        require(0<receipt['reserved_seconds']<=740 and process['started']>=terminal['started_monotonic'] and process['started']+receipt['reserved_seconds']<=terminal['started_monotonic']+terminal['reserved_seconds']+.01,'nested worker clocks')
        if workers:require(process['started']>=workers[-1]['ended_monotonic']-.01,'sequential workers overlap')
        workers.append(dict(label=label,pid=process['pid'],started_monotonic=process['started'],ended_monotonic=process['started']+receipt['reserved_seconds'],seconds=receipt['reserved_seconds']))
        if label.endswith(' fit'):require(receipt==read('run/'+label.removesuffix(' fit')+'/fit-result.json')['supervision'],'fit supervisor identity')
    require(math.isclose(sum(row['seconds'] for row in workers),terminal['worker_reserved_seconds'],abs_tol=1e-6),'worker cost sum')
    require(all(release[key] for key in ('controller_absent','full_release')) and release['device']==launch['device']==plan['device']=='0','full native release')
    for path,key in (('plan.json','plan_sha256'),('run/terminal.json','terminal_sha256'),('launch/launch.json','launch_sha256'),('run/main_release.xml','xml_sha256')):require(digest(path)==release[key],'release file pin')
    xml=ET.fromstring(files['run/main_release.xml']);gpus=xml.findall('gpu');require(len(gpus)==1,'release selected GPU')
    require(gpus[0].findtext('uuid')==release['gpu']['gpu_uuid']==launch['gpu']['gpu_uuid'] and not gpus[0].findall('processes/process_info') and gpus[0].findtext('fb_memory_usage/used')=='0 MiB' and gpus[0].findtext('utilization/gpu_util')=='0 %','vacant launch UUID')
    reservation=read('run/reservation.json')
    require(reservation['controller_pid']==terminal['controller_pid']==launch['pid']==launch['pgid'] and reservation['continuous_reservation'],'controller ownership')
    require(reservation['effective_deadline']==terminal['effective_deadline']==min(terminal['started']+5100,plan['deadline'],plan['real_lease_end']-plan['lease_margin_seconds']) and terminal['ended']<=terminal['effective_deadline'],'effective deadline')
    require(release['worker_reserved_seconds']==terminal['worker_reserved_seconds']<=release['controller_reserved_seconds']==terminal['reserved_seconds']<=release['full_reservation_seconds']<=5400,'nested full cost')
    launch_time=dt.datetime.fromisoformat(launch['started_utc']);observed=launch_time+dt.timedelta(seconds=release['full_reservation_seconds'])
    elapsed=[row['seconds'] for panel in panels.values() for row in panel['rows']]
    def percentile(values,fraction):
        ordered=sorted(values);position=(len(ordered)-1)*fraction;low=int(position)
        return ordered[low]+(ordered[min(low+1,len(ordered)-1)]-ordered[low])*(position-low)
    cost=dict(worker_seconds=terminal['worker_reserved_seconds'],controller_seconds=terminal['reserved_seconds'],full_reservation_seconds=release['full_reservation_seconds'],full_reservation_A40_minutes=release['full_reservation_seconds']/60,
        launch_utc=launch['started_utc'],terminal_utc=dt.datetime.fromtimestamp(terminal['ended'],dt.timezone.utc).isoformat(),release_xml_timestamp=xml.findtext('timestamp'),observed_release_utc_derived=observed.isoformat(),
        generation_calls=640,native_input_tokens=sum(panel['cost']['native_input_tokens'] for panel in panels.values()),native_output_tokens=sum(panel['cost']['native_output_tokens'] for panel in panels.values()),
        generation_seconds=sum(elapsed),call_p50_seconds=percentile(elapsed,.5),call_p95_seconds=percentile(elapsed,.95),percentile_method='linear interpolation over 640 archived per-call durations',
        total_fit_train_seconds=sum(fit['train_seconds'] for fit in fits.values()),total_fit_wall_seconds=sum(fit['wall_seconds'] for fit in fits.values()),backend_ready_seconds=sum(panel['backend_ready_seconds'] for panel in panels.values()),workers=workers)
    comparisons={}
    for cycle in ('1','2'):
        left,right=panels['R'+cycle],panels['NEW_ONLY'+cycle]
        comparisons[cycle]=dict(memory_R_minus_NEW_ONLY={bank:{surface:left['counts']['memory'][bank][surface]['correct']-right['counts']['memory'][bank][surface]['correct'] for surface in ('exact','dev')} for bank in ('M0','B1','B2')},arithmetic_R_minus_NEW_ONLY={key:left['counts']['addition'][key]-right['counts']['addition'][key] for key in ('correct_action','adherence')})
    transitions={}
    for state in STATES[1:]:
        before={row['case_id']:row for row in panels[PARENTS[state]]['rows']}
        transitions[state]={bank:{surface:dict(Counter(('correct' if before[row['case_id']]['correct'] else 'wrong')+'->'+('correct' if row['correct'] else 'wrong') for row in panels[state]['rows'] if row['bank']==bank and row['surface']==surface)) for surface in ('exact','dev')} for bank in ('M0','B1','B2')}
    discrepancies={state:panel['discrepancies'] for state,panel in panels.items() if panel['discrepancies']}
    output=dict(status='PASS' if not discrepancies else 'NEEDS_CORRECTION',scope='offline independent raw reduction; receipt-limited native custody',capsule=str(CAPSULE),capsule_sha256=CAPSULE_SHA,plan_sha256=PLAN_SHA,source_commit=SOURCE,metadata_files=len(files),file_sha256={name:digest(name) for name in files},source_hashes=plan['source_hashes'],archived_code=archived_code,base_model_files=plan['model_files'],
        s0=dict(parent=s0['parent'],parent_plan_sha256=s0['parent_plan_sha256'],provenance=s0['provenance'],adapter_files=s0['parent_files'],cumulative_steps=400,seed=0),materials=materials,fits=fits,panels=panels,contrasts=comparisons,immediate_parent_transitions=transitions,cost=cost,discrepancies=discrepancies,
        limitations=['No adjacent collector validation JSON supplied locally; outer user pin and complete safe internal inventory checked.', 'Excluded weights not rehashed or numerically loaded offline; native inventory and source/base/adapter equality are receipt-backed.', 'Authored color mappings, one seed, two surfaces, no new OFF, lexical panel or generalization/G3/parenting/freeze claim.', 'Equal updates, native token budgets and padding, unequal current-new-fact doses; not pure replay isolation.', 'Prior related replay/helper/raw-audit authorship; not a fresh-author or blinded audit. No current outcomes supplied by Main, but stored S0 counts seen during schema inspection.'])
    OUTPUT.write_bytes(encoded(output))
    print(json.dumps(dict(status=output['status'],files=len(files),counts={state:panel['counts'] for state,panel in panels.items()},cost=cost,contrasts=comparisons,discrepancies=discrepancies),indent=2))


if __name__=='__main__':
    main()
