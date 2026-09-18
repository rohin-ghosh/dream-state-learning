"""Read only own process/provenance/TRAIN event metadata, never readout contents."""

import hashlib
import json
import os
from pathlib import Path
import time


ROOT=Path('/localhome/local-rohing/orch_r183_repo_learning_20260917/birth1')


def main():
    files={}
    names=['SERVICES_SPAWNED.json','control/OUTER_STARTED.json','control/CONFINEMENT_CPU.json',
        'control/PRE_SERVICE_ADMISSION.json','control/CONFINEMENT_CHILD.json','control/LAUNCH.json',
        'control/FAILED.json','control/OUTER_FAILED.json','control/EXIT.json','control/OUTER_EXIT.json',
        'tool_receipts/STARTED.json','tool_receipts/FIRST_TURN.json','tool_receipts/EXIT.json']
    names.extend(str(path.relative_to(ROOT)) for path in sorted((ROOT/'tool_receipts').glob('COMPLETE_*.json'))[:4])
    names.extend(str(path.relative_to(ROOT)) for path in sorted((ROOT/'tool_receipts').glob('REJECTED_*.json'))[:4])
    names.extend(str(path.relative_to(ROOT)) for path in sorted((ROOT/'tool_receipts').glob('ACTION_*.json'))[:4])
    for name in names:
        path=ROOT/name
        if path.exists() and path.stat().st_size<=1024*1024:
            raw=path.read_bytes()
            document=json.loads(raw)
            if name=='control/PRE_SERVICE_ADMISSION.json':
                report=document['report']
                document=dict(verified_unix=document['verified_unix'],guard_sha256=document['guard_sha256'],
                    scanner_euid=report['scanner_euid'],clear=report['clear'],blocking_reasons=report['blocking_reasons'],gpu=report['gpu'])
            if name.startswith('tool_receipts/ACTION_'):
                document={key:value for key,value in document.items() if key not in ('content','paths')}
            files[name]=dict(sha256=hashlib.sha256(raw).hexdigest(),document=document)
    processes=[]
    for directory in Path('/proc').glob('[0-9]*'):
        try:
            command=(directory/'cmdline').read_bytes().split(b'\0')
            if any(b'orch_r183_repo_learning_20260917/birth1/' in part for part in command) and command:
                fields=(directory/'stat').read_text().rsplit(')',1)[1].split()
                processes.append(dict(pid=int(directory.name),startticks=fields[19],state=fields[0],
                    cmdline=[part.decode(errors='replace') for part in command if part]))
        except (OSError,ValueError):
            pass
    events=[]
    for path in sorted((ROOT/'life/stream/records').glob('[0-9]'*20+'.json'))[:32]:
        if path.stat().st_size>4*1024*1024:
            break
        record=json.loads(path.read_bytes())
        doc=record['document']
        event=dict(index=record['index'],kind=record['kind'],sha256=record['sha256'])
        if record['kind']=='LOADED':
            event.update({key:doc[key] for key in ('pid','loaded_unix','resume','optimizer_steps')})
        events.append(event)
    print(json.dumps(dict(observed_unix=time.time(),files=files,processes=processes,TRAIN_events=events,
        readout_contents_opened=False),sort_keys=True))


if __name__=='__main__':
    main()
