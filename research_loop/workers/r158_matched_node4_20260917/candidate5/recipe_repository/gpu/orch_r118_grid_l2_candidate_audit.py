"""Bounded read-only selection of parented TRAIN continuations, never admission."""

import argparse
import hashlib
import json
from pathlib import Path
import time


ROOT = Path('/localhome/local-rohing/orch_r115_grid_pair_20260915/A4')
LABEL = 'PARENTED_DERIVED_L2_TRAIN_CANDIDATE'


def require(value, reason):
    if not value:
        raise ValueError(reason)


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def read(path):
    return json.loads(path.read_text())


def ref(path):
    return dict(path=str(path), sha256=hashlib.sha256(path.read_bytes()).hexdigest())


def validate_pair(before, after, parent, train_ids, held_ids):
    for call in (before, after):
        require(call['status'] == 'COMPLETE' and call['split'] == 'TRAIN'
            and not call.get('attached_readout') and not call.get('evaluation_origin'), 'TRAIN_only_no_attached_open')
        require(call['task_id'] in train_ids and call['task_id'] not in held_ids, 'frozen_TRAIN_roster_only')
    require(before['task_id'] == after['task_id'] and before['cycle'] == after['cycle'], 'same_task_cycle')
    require(before.get('adapter') == after.get('adapter')
        and before.get('shared_child') == after.get('shared_child')
        and before['base_sha256'] == after['base_sha256'], 'same_actual_child_state')
    guidance = parent['disposition'].get('guidance')
    require(parent['disposition']['status'] == 'COMPLETE' and isinstance(guidance, str) and guidance,
        'actual_native_consumed_parent')
    require(before['finished_unix'] <= parent['observed_unix'] <= after['started_unix'], 'causal_order')
    require(any(message['role'] == 'user' and message['content'] == guidance for message in after['messages']),
        'exact_parent_guidance_in_causal_prefix')
    response = after['response']
    require(response.get('messages', after['messages']) == after['messages'] and response['token_ids']
        and response['prompt_tokens'] > 0, 'actual_native_messages_tokens')
    require(response['raw'] != guidance, 'not_verbatim_parent_target')
    return dict(student_prefix=after['messages'], target=response['raw'],
        source_generated_token_ids=response['token_ids'], source_prompt_tokens=response['prompt_tokens'],
        append_eos=response['terminal'], continuation_only=not response['terminal'],
        prefix_labels='ALL_MINUS_100_INCLUDING_PARENT_AND_PRIOR_CHILD',
        target_labels='ONLY_EXACT_CURRENT_CHILD_NATIVE_TOKENS', source_label=LABEL,
        trainingAllowed=False, full_text_functional_review='PENDING',
        native_truncated=response['truncated'])


def collect(output, cutoff):
    require(output.is_absolute() and not output.exists(), 'new_node_only_audit_directory')
    train = read(ROOT/'TRAIN.json')
    held = read(ROOT/'DEV.json') + read(ROOT/'FINAL.json')
    train_ids, held_ids = {row['id'] for row in train}, {row['id'] for row in held}
    require(not train_ids & held_ids, 'TRAIN_DEV_FINAL_ID_disjoint')
    require(not {digest(row) for row in train} & {digest(row) for row in held}, 'task_content_disjoint')
    ledger = [json.loads(line) for line in (ROOT/'LEDGER.jsonl').read_text().splitlines() if line]
    calls = []
    for row in ledger:
        if row['kind'] != 'NATIVE' or row['split'] != 'TRAIN' or row.get('attached_readout'):
            continue
        path = ROOT/'calls'/f'N{row["number"]:05d}.json'
        if path.exists():
            call = read(path)
            if call['status'] == 'COMPLETE' and call['finished_unix'] <= cutoff:
                calls.append((path, call))
    candidates = []
    for row in ledger:
        if row['kind'] != 'PARENT':
            continue
        path = ROOT/'parent_received'/f'P{row["number"]:04d}.json'
        if not path.exists():
            continue
        parent = read(path)
        if parent['disposition']['status'] != 'COMPLETE' or parent['observed_unix'] > cutoff:
            continue
        same = [(path, call) for path, call in calls if call['task_id'] == row['task_id'] and call['cycle'] == row['cycle']]
        before = [(path, call) for path, call in same if call['finished_unix'] <= row['reserved_unix']]
        after = [(path, call) for path, call in same if call['started_unix'] >= parent['observed_unix']]
        if before and after:
            candidates.append((row, path, parent, max(before, key=lambda item:item[1]['number']),
                min(after, key=lambda item:item[1]['number'])))
    selected = candidates[-16:]
    output.mkdir(parents=True)
    cases=[]
    for row, parent_path, parent, before, after in selected:
        identifier=f'P{row["number"]:04d}'
        case=dict(case_id=identifier,task_id=row['task_id'],cycle=row['cycle'],phase=row['phase'],
            before=before[1]['response']['raw'],parent_guidance=parent['disposition']['guidance'],
            before_prefix=before[1]['messages'],
            bindings=dict(before=ref(before[0]),parent=ref(parent_path),request=parent['request'],
                response=parent['response'],continuation=ref(after[0])),
            child_identity=dict(base_sha256=after[1]['base_sha256'],adapter=after[1].get('adapter'),
                shared_child=after[1].get('shared_child')))
        try:
            case['row']=validate_pair(before[1],after[1],parent,train_ids,held_ids)
            case['mechanical_status']='PASS'
        except ValueError as error:
            case.update(mechanical_status='FAIL',reason=str(error),target=after[1]['response']['raw'])
        environments=[]
        for environment in (ROOT/'cycles'/f'{row["cycle"]:04d}').glob('*/*.json'):
            data=read(environment)
            if data.get('task_id')==row['task_id'] and 'environment_call' in data and not data.get('attached_readout'):
                if after[1]['finished_unix'] <= data['created_unix'] <= after[1]['finished_unix']+2:
                    environments.append(dict(reference=ref(environment),environment_call=data['environment_call']))
        case['immediate_environment']=environments
        destination=output/(identifier+'.json')
        with destination.open('x') as stream: json.dump(case,stream,indent=2,sort_keys=True)
        cases.append(dict(case_id=identifier,path=str(destination),sha256=ref(destination)['sha256'],
            mechanical_status=case['mechanical_status'],phase=row['phase'],cycle=row['cycle'],
            target_characters=len(after[1]['response']['raw']),source_call=ref(after[0])))
    manifest=dict(schema='R118_GRID_L2_CANDIDATE_AUDIT_V1',source_label=LABEL,source_root=str(ROOT),
        cutoff_unix=cutoff,selection='Latest up to16 completed native-consumed parent interventions with adjacent completed TRAIN child calls; fixed before full-text review',
        all_available_pairs=len(candidates),selected=cases,rosters={name:ref(ROOT/name) for name in ('TRAIN.json','DEV.json','FINAL.json')},
        raw_node_only=True,model_calls=0,provider_calls=0,trainingAllowed=False,automatic_admission=False,
        source=ref(Path(__file__)),created_unix=time.time())
    with (output/'MANIFEST.json').open('x') as stream: json.dump(manifest,stream,indent=2,sort_keys=True)
    print(json.dumps(manifest,sort_keys=True))


if __name__ == '__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--cutoff',type=float,required=True)
    args=parser.parse_args()
    collect(args.output,args.cutoff)
