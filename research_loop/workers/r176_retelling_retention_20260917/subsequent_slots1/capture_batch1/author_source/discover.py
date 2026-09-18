"""Bounded exact operational pointers for the other five already frozen C2 slots."""

import json
from pathlib import Path
import sys
import time

import preparation_io as common


SOURCE = Path('/localhome/local-rohing/orch_r153_community_C2_20260916_attempt1/life')
ROOTS = [Path('/localhome/local-rohing/orch_r167_fleet_20260917_generation2'),
    Path('/localhome/local-rohing/orch_r172_forward_probes_20260917_generation1')]
CUSTODY = ROOTS[1]/'source_controls/C2/FRESH_CUSTODY.json'
CUSTODY_SHA = '0bcf2d69cfeecc3cec6b4c5ab8436fa2a62d6220dd337d82a172ed1fd0d667fc'


def validate_pointer(document,sleep):
    common.require(document['life_id']=='C2' and document['sleep']==sleep and sleep in range(34,39)
        and document['source_root']==str(SOURCE),'same_fixed_C2_checkpoint')
    common.require(document['commit']['path']==str(SOURCE/f'checkpoints/sleep_{sleep:06d}/COMMIT.json'),
        'exact_fixed_COMMIT_path')
    record = Path(document['record']['path'])
    common.require(record.parent==SOURCE/'stream/records' and len(record.stem)==20 and record.stem.isdigit()
        and record.suffix=='.json' and document['intent']['path']==str(record.with_suffix('.intent.json')),
        'paired_exact_record_and_intent')
    for field in ('commit','record','intent'):
        checksum = document[field]['sha256']
        common.require(isinstance(checksum,str) and len(checksum)==64 and
            all(character in '0123456789abcdef' for character in checksum),'exact_pointer_hashes')
    return {field:document[field] for field in ('life_id','sleep','source_root','commit','record','intent')}


def main():
    operation = common.REMOTE/'subsequent_slots1/discovery1'
    request = json.loads((operation/'REQUEST.json').read_bytes())
    common.write(operation/'ONCE.json',dict(started_unix=time.time(),model_calls=0,provider_calls=0))
    paths = [root/'lives/C2/boundaries'/f'{sleep:06d}.json' for root in ROOTS for sleep in range(34,39)]
    reader = common.Reader(operation,{'metadata':request['allowance']},paths+[CUSTODY])
    custody,custody_ref,unused = reader.document(CUSTODY,CUSTODY_SHA)
    rows = []
    for sleep in range(34,39):
        found = []
        for root in ROOTS:
            path = root/'lives/C2/boundaries'/f'{sleep:06d}.json'
            if path.is_file():
                raw = reader.raw(path,limit=128*1024)
                pointer = validate_pointer(json.loads(raw),sleep)
                found.append(dict(pointer=pointer,metadata=dict(path=str(path),sha256=common.sha(raw))))
        completed = custody.get('completed_boundary',{})
        if completed.get('cycle') == sleep:
            pointer = dict(life_id='C2',sleep=sleep,source_root=str(SOURCE),
                commit=completed['checkpoint']['reference'],record=completed['record']['record'],
                intent=completed['record']['intent'])
            found.append(dict(pointer=validate_pointer(pointer,sleep),metadata=custody_ref))
        if found:
            common.require(all(row['pointer']==found[0]['pointer'] for row in found),'conflicting_existing_checkpoint_pointers')
            rows.append(dict(life_id='C2',sleep=sleep,status='BOUND_OPERATIONAL_POINTER_NOT_NEW_CAPTURE',
                pointer=found[0]['pointer'],evidence=[row['metadata'] for row in found]))
        else:
            rows.append(dict(life_id='C2',sleep=sleep,status='MISSING_BOUND_COMPLETED_RECORD_POINTER_NO_REPLACEMENT'))
    result = dict(status='FIXED_C2_FOLLOWUP_POINTER_DISCOVERY_COMPLETE',rows=rows,observed_unix=time.time(),
        model_calls=0,provider_calls=0,adapter_reads=0,TRAIN_payload_reads=0,
        metadata_bytes_read=reader.actual['metadata'],read_count=reader.sequence)
    common.write(operation/'PUBLIC_METADATA.json',result)
    print(json.dumps(result,sort_keys=True))


if __name__=='__main__':
    main()
