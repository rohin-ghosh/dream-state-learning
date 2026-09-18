"""Bounded read-only TRAIN suffix verification from Main's exact record anchor."""

import json
from pathlib import Path
import time

from gpu import orch_r133_programme_parent as parent
from gpu import orch_r153_community_parents as community
from gpu import orch_r167_parent_takeover as files


ROOT = Path(__file__).resolve().parents[3]
STAGE = Path(__file__).resolve().parent
OUTPUT = STAGE/'MANUAL_C1_CUSTODY_ATTEMPT2'


def main():
    publication = json.loads(files.read_file(OUTPUT/'PUBLICATION.json'))['publication']
    intent = json.loads(files.read_file(OUTPUT/'MANUAL_PUBLICATION_INTENT.json'))
    started = json.loads(files.read_file(OUTPUT/'PARENT_RESUMED.json'))
    config = json.loads(files.read_file(started['config']['path']))
    basis = json.loads(files.read_file(intent['sourcebasis']['path']))
    assert files.sha(intent['sourcebasis']['path']) == intent['sourcebasis']['sha256']
    child = json.loads(files.read_file(OUTPUT/'PREFLIGHT.json'))['child_and_source']['child']
    script = '''import hashlib,json,os,re,stat,time
from pathlib import Path
from gpu.orch_r125_stream_console import _open_stream_directory
from gpu.orch_r125_stream_journal import _decode,_digest,SCHEMA
from gpu import orch_r127_pilot_transcript as transcript
root=ROOT;anchor=ANCHOR;publication=PUBLICATION;intent=INTENT;child=CHILD
process=Path('/proc')/str(child['pid']);fields=(process/'stat').read_text().rsplit(')',1)[1].split()
assert fields[19]==child['start_ticks'] and fields[0] not in ('Z','X','T','t')
used=0;previous=None;journal_id=None;inbox={};ingested=None;rendered=[];kinds={};requests=[]
start=int(Path(anchor['path']).stem)
with _open_stream_directory(root,'records') as (directory,unused):
 names=[]
 with os.scandir(directory) as entries:
  for scanned,entry in enumerate(entries,1):
   assert scanned<=401024
   if re.fullmatch(r'[0-9]{20}[.]json',entry.name):names.append(entry.name)
 names.sort();assert names and len(names)<=100000
 assert [int(name[:20]) for name in names]==list(range(len(names)))
 end=len(names);assert 0<=start<end and end-start<=4096
 for index in range(start,end):
  name=f'{index:020d}.json'
  descriptor=os.open(name,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK,dir_fd=directory)
  with os.fdopen(descriptor,'rb') as stream:
   before=os.fstat(stream.fileno());assert stat.S_ISREG(before.st_mode)
   assert before.st_size<=16777216 and used+before.st_size<=134217728
   raw=stream.read(before.st_size+1);after=os.fstat(stream.fileno())
  current=os.stat(name,dir_fd=directory,follow_symlinks=False)
  assert len(raw)==before.st_size and len({(entry.st_dev,entry.st_ino,entry.st_size,entry.st_mtime_ns)
      for entry in (before,after,current)})==1
  used+=len(raw);record=_decode(raw)
  assert record['schema']==SCHEMA and record['index']==index
  assert _digest({key:value for key,value in record.items() if key!='sha256'})==record['sha256']
  if index==start:
   assert hashlib.sha256(raw).hexdigest()==anchor['sha256'] and len(raw)==anchor['bytes']
   journal_id=record['journal_id']
  else:assert record['previous_sha256']==previous and record['journal_id']==journal_id
  previous=record['sha256'];kind=record['kind'];document=record['document']
  kinds[kind]=kinds.get(kind,0)+1
  if kind=='INBOX' and document['message']['id']==publication['id']:
   assert ingested is None
   entry=transcript._inbox(document)
   assert entry['inbox_source_sha256']==publication['sha256'] and entry['speaker']=='Astra'
   assert hashlib.sha256(entry['text'].encode()).hexdigest()==intent['text_sha256']
   inbox[publication['id']]=entry
   ingested=dict(record_index=index,record_sha256=record['sha256'])
  elif kind=='REQUEST':
   assert document['split']=='TRAIN' and document['render_receipt']['all_history_tokens_masked'] is True
   visible,ambiguous=transcript._visible(document['messages'],inbox)
   requests.append(dict(record_index=index,segment=document['segment']))
   if publication['id'] in visible:
    assert not ambiguous
    rendered.append(dict(record_index=index,record_sha256=record['sha256'],segment=document['segment'],
      publication_id=publication['id'],inbox_sha256=publication['sha256'],text_sha256=intent['text_sha256'],
      all_history_tokens_masked=True,speaker='Astra'))
print(json.dumps(dict(status='RENDERED' if rendered else 'INGESTED_NOT_RENDERED' if ingested else 'PUBLISHED_NOT_INGESTED_IN_VERIFIED_SUFFIX',
 observed_unix=time.time(),bytes_read_this_poll=used,start_index=start,end_index_exclusive=end,
 anchor=anchor,verified_suffix_head_sha256=previous,journal_id=journal_id,kinds=kinds,requests=requests,
 ingested=ingested,rendered=rendered,child=dict(pid=child['pid'],start_ticks=fields[19],state=fields[0]),
 verification_scope='exact_Main_anchor_and_contiguous_suffix_not_fresh_full_history_audit')))
'''.replace('ROOT', repr(config['root'])).replace('ANCHOR', repr(basis['record_ref'])).replace(
        'PUBLICATION', repr(publication)).replace('INTENT', repr(dict(text_sha256=intent['text_sha256']))).replace(
        'CHILD', repr(child))
    result = parent.remote(ROOT, config, script)
    observed = files.identity(started['successor']['pid'])
    assert observed['argv'] == started['command'] and observed['start_ticks'] == started['successor']['start_ticks']
    result['parent_identity'] = observed
    path = OUTPUT/('RENDER_OBSERVATION_'+str(time.time_ns())+'.json')
    community.write(path, result)
    print(json.dumps(dict(path=str(path), sha256=files.sha(path), observation=result), indent=2))


if __name__ == '__main__':
    main()
