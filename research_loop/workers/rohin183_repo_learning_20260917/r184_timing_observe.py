"""Bounded copy-stage timing and code-hash observation; no learner changes."""
import hashlib,json,time
from pathlib import Path


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream,'sha256').hexdigest()


base=Path('/localhome/local-rohing/orch_r153_r184_node2_20260917')
copies={}
for label in ('explicit','brief'):
    root=base/(label+'1')
    source=root/'source'
    expected=json.loads((root/'SOURCE.json').read_bytes())['source_pins']
    actual={str(path.relative_to(source)):sha(path) for path in source.rglob('*.py')}
    directory=root/'raw/stream/records'
    retained=sorted(directory.glob('[0-9]'*20+'.json'))
    selected={path.name:path for path in retained[-5:]}
    for index in (5129,5130,5131,5133,5135,5136,5138,5139,5141,5142,5144,5147):
        path=directory/f'{index:020d}.json'
        if path.exists():selected[path.name]=path
    events=[]; charged=0
    for path in sorted(selected.values()):
        size=path.stat().st_size
        if size>8*1024**2 or charged+size>48*1024**2:
            events.append(dict(path=str(path),skipped='bounded_metadata_reader_size'))
            continue
        charged+=size
        record=json.loads(path.read_bytes());document=record['document']
        event=dict(index=record['index'],kind=record['kind'],sha256=record['sha256'],file_persisted_mtime_unix=path.stat().st_mtime)
        for key in ('loaded_unix','started_unix','finished_unix','pid','optimizer_steps','optimizer_step','stage','trial_id','segment',
                    'policy','new_rows','new_presentations','selected_old_rows','anchor_lambda'):
            if key in document:event[key]=document[key]
        if record['kind']=='R184_STAGE':event['consolidation']=document.get('consolidation')
        if record['kind']=='R184_ACT':
            event['outcome']={key:value for key,value in document['outcome'].items()
                if key in ('status','executed','result_status','result_sha256','publication','error_type')}
        events.append(event)
    failures={}
    for name in ('control/FAILED.json','control/OUTER_FAILED.json','control/EXIT.json','control/OUTER_EXIT.json'):
        path=root/name
        if path.exists():failures[name]=dict(sha256=sha(path),document=json.loads(path.read_bytes()))
    native=next(item['pid'] for item in events if item.get('kind')=='LOADED')
    try:
        fields=Path('/proc',str(native),'stat').read_text().rsplit(')',1)[1].split()
        process=dict(pid=native,startticks=fields[19],state=fields[0],alive=True)
    except FileNotFoundError:
        process=dict(pid=native,alive=False)
    copies[label]=dict(base=str(root),source_pins_unchanged=actual==expected,source_file_count=len(actual),
        source_pin_file_sha256=sha(root/'SOURCE.json'),process=process,events=events,failures=failures,
        operational_record_bytes_read=charged,retained_record_count=len(retained),complete_episode_encoder_integrated=False)
print(json.dumps(dict(observed_unix=time.time(),copies=copies,source_changes=False,learner_signals=0),sort_keys=True))
