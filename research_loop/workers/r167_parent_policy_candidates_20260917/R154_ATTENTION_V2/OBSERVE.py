"""Read-only bounded parent phases and child tail counts, never publication replay."""

import hashlib
import json
from pathlib import Path
import time

from gpu import orch_r133_programme_parent as parent


STAGE = Path(__file__).resolve().parent
ROOT = STAGE/'ROLLOUT'
REPOSITORY = STAGE.parents[3]


def phases():
    results = []
    for branch in ('C1','C3','C2','C4','C5'):
        directory = ROOT/branch
        transfer = json.loads((directory/'LEDGER_TRANSFER.json').read_bytes())
        inherited = {entry['attempt'] for entry in transfer['attempts']}
        started = json.loads((directory/'STARTED.json').read_bytes())
        process = Path('/proc')/str(started['successor']['pid'])
        fields = (process/'stat').read_text().rsplit(')',1)[1].split()
        argv = (process/'cmdline').read_bytes().rstrip(b'\0').decode().split('\0')
        assert fields[19] == started['successor']['start_ticks'] and argv == started['command']
        fresh = []
        for attempt in sorted((directory/'parent').glob('parent_*')):
            if attempt.name in inherited:
                continue
            entry = dict(attempt=attempt.name)
            for name in ('SOURCE.json','PROMPT.json','RESULT.json','DELIVERED.json'):
                path = attempt/name
                if not path.exists():
                    continue
                assert path.stat().st_size <= 16*1024*1024
                raw = path.read_bytes()
                document = json.loads(raw)
                entry[name] = dict(path=str(path),sha256=hashlib.sha256(raw).hexdigest())
                if name == 'SOURCE.json':
                    entry['response_count'] = document['response_count']
                elif name == 'PROMPT.json':
                    entry['marker_present'] = 'ROHIN154_EXISTING_PARENTED_ATTENTION_ALLOCATION_V2' in document['instruction']
                elif name == 'RESULT.json':
                    entry.update(status=document['status'], publication=document.get('publication'),
                        error_type=document.get('error_type'))
                elif name == 'DELIVERED.json':
                    entry['rendered'] = document
            fresh.append(entry)
        log = directory/'PARENT.log'
        assert log.stat().st_size <= 1024*1024
        results.append(dict(branch=branch,pid=started['successor']['pid'],state=fields[0],
            reserved_response_count=transfer['reserved_response_count'],
            next_due_response_count=max([transfer['reserved_response_count']]+[entry.get('response_count',0) for entry in fresh])+3,
            fresh_attempts=fresh,log_tail=log.read_text()[-1200:]))
    return results


def tail_counts():
    children = {branch:json.loads((ROOT/branch/'PREFLIGHT.json').read_bytes())['child']
                for branch in ('C1','C3','C2','C4','C5')}
    config = json.loads((STAGE/'C1_2417126/CONFIG.json').read_bytes())
    script = '''import json,os,re,stat,time
from pathlib import Path
from gpu.orch_r125_stream_journal import _decode,_digest,SCHEMA
from gpu.orch_r125_stream_console import _open_stream_directory
children=CHILDREN
results=[]
for branch,child in children.items():
 process=Path('/proc')/str(child['pid']); fields=(process/'stat').read_text().rsplit(')',1)[1].split()
 assert fields[19]==child['start_ticks'] and fields[0] not in ('Z','X','T','t')
 used=0; previous=None; found=None; head=None
 with _open_stream_directory(child['root'],'records') as (directory,unused):
  names=[]
  with os.scandir(directory) as entries:
   for scanned,entry in enumerate(entries,1):
    assert scanned<=401024
    if re.fullmatch(r'[0-9]{20}[.]json',entry.name): names.append(entry.name)
  names.sort();assert len(names)<=100000
  assert [int(name[:20]) for name in names]==list(range(len(names)))
  for name in reversed(names[-4096:]):
   descriptor=os.open(name,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK,dir_fd=directory)
   with os.fdopen(descriptor,'rb') as stream:
    before=os.fstat(stream.fileno());assert stat.S_ISREG(before.st_mode) and before.st_size<=67108864 and used+before.st_size<=268435456
    raw=stream.read(before.st_size+1);after=os.fstat(stream.fileno())
   nowstat=os.stat(name,dir_fd=directory,follow_symlinks=False)
   assert len({(item.st_dev,item.st_ino,item.st_size,item.st_mtime_ns) for item in (before,after,nowstat)})==1 and len(raw)==before.st_size
   record=_decode(raw);used+=len(raw)
   assert record['schema']==SCHEMA and record['index']==int(name[:20]) and record['sha256']==_digest({key:value for key,value in record.items() if key!='sha256'})
   if previous is not None: assert previous==record['sha256']
   previous=record['previous_sha256']
   if head is None: head=dict(index=record['index'],kind=record['kind'],mtime_unix=before.st_mtime,optimizer_step=record['document'].get('optimizer_step'))
   document=record['document']; checkpoint=document.get('state',document.get('resume_state'))
   if isinstance(checkpoint,dict) and 'state' in checkpoint and 'sha256' in checkpoint:
    assert checkpoint['sha256']==_digest(checkpoint['state'])
    state=checkpoint['state']
    if 'rows' in state:
     found=dict(branch=branch,pid=child['pid'],start_ticks=child['start_ticks'],native_state=fields[0],journal_id=record['journal_id'],record_index=record['index'],record_sha256=record['sha256'],kind=record['kind'],record_mtime_unix=before.st_mtime,committed_rows=len(state['rows']),sleep_frontier=state['sleep_frontier'],pending=state['pending'] is not None,source_bytes=used,observed_unix=time.time(),head=head,basis='bounded_authoritative_tail_checkpoint_not_fresh_full_chain_audit')
     break
 assert found is not None
 results.append(found)
print(json.dumps(dict(children=results,source_bytes=sum(item['source_bytes'] for item in results))))
'''.replace('CHILDREN',repr(children))
    return parent.remote(REPOSITORY,config,script)


def main():
    report = dict(observed_unix=time.time(),parents=phases())
    try:
        report['tail_counts'] = tail_counts()
    except Exception as error:
        report['tail_error'] = dict(type=type(error).__name__,message=str(error))
    path = ROOT/('OBSERVATION_'+str(time.time_ns())+'.json')
    parent.write(path,report)
    print(json.dumps(dict(path=str(path),sha256=hashlib.sha256(path.read_bytes()).hexdigest(),report=report),indent=2))


if __name__ == '__main__':
    main()
