"""Bounded incremental TRAIN-only feed for this new child's local parent."""

import json
from pathlib import Path
import sys


ROOT=Path('/localhome/local-rohing/orch_r183_repo_learning_20260917/birth1')
sys.path.insert(0,str(ROOT/'source'))
from gpu.orch_r125_stream_console import _open_stream_directory,_read_record
from gpu.orch_r125_stream_journal import _digest


def collect(root,cursor,previous,journal_id,waiting):
    path=Path(root)/'stream/JOURNAL.json'
    if not path.exists():
        return dict(ready=False)
    journal=json.loads(path.read_bytes())
    if journal_id is not None and journal_id!=journal['journal_id']:
        raise ValueError('same_actual_journal_identity')
    index=cursor
    head=_digest(journal) if index==0 else previous
    events=[]
    responses=0
    charged=0
    seen_waiting=False
    rendered=None
    with _open_stream_directory(root,'records') as (directory,unused):
        if index:
            anchor=_read_record(directory,index-1)
            if anchor is None or anchor['sha256']!=head:
                raise ValueError('previous_cursor_anchor_changed')
        for unused in range(64):
            candidate=Path(root)/'stream/records'/f'{index:020d}.json'
            if not candidate.exists():
                break
            size=candidate.stat().st_size
            if size>16*1024**2:
                raise ValueError('parent_single_record_budget')
            if charged+size>16*1024**2:
                break
            charged+=size
            record=_read_record(directory,index)
            if record['previous_sha256']!=head or record['journal_id']!=journal['journal_id']:
                raise ValueError('parent_incremental_chain')
            document=record['document']
            reference=dict(record_index=index,record_sha256=record['sha256'])
            if record['kind']=='RESPONSE':
                responses+=1
                events.append(dict(actor='child',text=document['response']['raw'][:6000],**reference))
            elif record['kind']=='INBOX':
                message=document['message']
                if message['split']!='TRAIN' or message['actor'] not in ('parent','environment'):
                    raise ValueError('parent_only_train_operational_events')
                events.append(dict(actor=message['actor'],speaker=message.get('speaker'),text=message['text'][:6000],**reference))
                if waiting and message['id']==waiting['id']:
                    seen_waiting=True
            elif record['kind']=='REQUEST' and waiting:
                if seen_waiting or waiting.get('registered'):
                    if any('Astra: '+waiting['message'] in item['content'] for item in document['messages']):
                        rendered=dict(inbox_id=waiting['id'],**reference)
            head=record['sha256']
            index+=1
    return dict(ready=True,journal_id=journal['journal_id'],cursor=index,previous=head,events=events[-8:],
        new_responses=responses,bytes_charged=charged,waiting_registered=seen_waiting,rendered=rendered)


if __name__=='__main__':
    state=json.loads(sys.argv[1])
    print(json.dumps(collect(ROOT/'life',**state),sort_keys=True))
