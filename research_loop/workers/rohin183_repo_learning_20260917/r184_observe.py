"""Only launch, checkpoint counters and first new R184 stage metadata."""
import hashlib,json,time
from pathlib import Path

base=Path('/localhome/local-rohing/orch_r153_r184_node2_20260917')
results={}
for label in ('explicit','brief'):
    root=base/(label+'1')
    if not root.exists():continue
    receipts={}
    for name in ('STARTED.json','control/LAUNCH.json','control/FAILED.json','control/OUTER_FAILED.json','control/EXIT.json'):
        path=root/name
        if path.exists():
            raw=path.read_bytes();document=json.loads(raw)
            document.pop('source_pins',None)
            receipts[name]=dict(sha256=hashlib.sha256(raw).hexdigest(),document=document)
    events=[]
    records=root/'raw/stream/records'
    for index in range(5129,5161):
        path=records/f'{index:020d}.json'
        if not path.exists():break
        record=json.loads(path.read_bytes());document=record['document']
        item=dict(index=index,kind=record['kind'],sha256=record['sha256'])
        item.update({key:value for key,value in document.items() if key in ('pid','loaded_unix','optimizer_steps','stage','trial_id','resume')})
        if record['kind']=='REQUEST':
            item['has_THINK_stage_notice']=any('THINK' in message['content'] for message in document['messages'])
        events.append(item)
    process=[]
    for directory in Path('/proc').glob('[0-9]*'):
        try:
            command=(directory/'cmdline').read_bytes().split(b'\0')
            if any(str(root).encode() in part for part in command):
                fields=(directory/'stat').read_text().rsplit(')',1)[1].split()
                process.append(dict(pid=int(directory.name),startticks=fields[19],state=fields[0],module=command[3].decode() if len(command)>3 else None))
        except (OSError,ValueError):pass
    results[label]=dict(receipts=receipts,new_TRAIN_events=events,processes=process)
print(json.dumps(dict(observed_unix=time.time(),copies=results),sort_keys=True))
