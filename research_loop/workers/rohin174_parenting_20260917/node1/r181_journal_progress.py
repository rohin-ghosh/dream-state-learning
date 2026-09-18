"""Bounded node1 metadata observer for both R181 source revisions; no control."""

import importlib.util
import json
import os
from pathlib import Path
import shlex
import subprocess
import time

from inventory_node1 import HERE, digest, require
from parent_custody import write


REMOTE = r'''
import hashlib,json,os,re,stat,time
from pathlib import Path
root=Path('/localhome/local-rohing/orch_r181_node1_20260917');charged=0;rows=[]
def digest(value):
 return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()
def read(path,maximum=4*1024*1024):
 global charged
 assert path.resolve()==path and not path.is_symlink()
 metadata=path.lstat();assert stat.S_ISREG(metadata.st_mode) and metadata.st_size<=maximum
 assert charged+metadata.st_size<=256*1024*1024;charged+=metadata.st_size
 with path.open('rb') as stream:
  before=os.fstat(stream.fileno());assert (before.st_dev,before.st_ino,before.st_size)==(metadata.st_dev,metadata.st_ino,metadata.st_size)
  raw=stream.read(metadata.st_size+1);after=os.fstat(stream.fileno())
 assert len(raw)==metadata.st_size and before.st_mtime_ns==after.st_mtime_ns
 return json.loads(raw),hashlib.sha256(raw).hexdigest()
for lane in range(2,8):
 original=root/'lanes'/('lane'+str(lane));revision=root/'journal_overlay'
 if lane==5:revision=revision/'brain'
 directory=revision/'lanes'/('lane'+str(lane));staged,unused=read(directory/'STAGED.json');armed,unused=read(directory/'ARMED.json')
 overlay_loaded=(directory/'LOADED_RECEIPT.json').exists();actual=directory if overlay_loaded else original
 row=dict(physical=lane,waiter_pid=armed['operator_pid'],waiter_alive=Path('/proc',str(armed['operator_pid'])).exists(),
          staged_source=staged['source_root'],overlay_loaded=overlay_loaded,loaded=None,recipes=[],completed=None,following_request=None,failures=[])
 for path in directory.glob('FAILURE_*.json'):
  document,sha=read(path);row['failures'].append(dict(path=str(path),sha256=sha,document=document))
 if not (actual/'LOADED_RECEIPT.json').exists():rows.append(row);continue
 loaded,unused=read(actual/'LOADED_RECEIPT.json');row['loaded']=loaded
 current,unused=read(actual/'STAGED.json');guard,unused=read(Path(current['new_config']))
 row['actual_source']=current['source_root'];row['source_pins']=guard['source_pins']
 row['actor_alive']=Path('/proc',str(loaded['actor_pid'])).exists()
 if row['actor_alive']:
  fields=(Path('/proc',str(loaded['actor_pid']))/'stat').read_text().rsplit(') ',1)[1].split()
  row['actor_alive']=fields[19]==str(loaded['actor_start_ticks']) and fields[0] not in ('Z','X')
 records=Path(current['old_plan']['root'])/'stream/records';assert not records.is_symlink()
 paths=sorted(path for path in records.iterdir() if re.fullmatch(r'[0-9]{20}\.json',path.name))
 complete_history=None
 for path in paths[-128:]:
  metadata=path.lstat();assert stat.S_ISREG(metadata.st_mode)
  length=min(metadata.st_size,4096);assert charged+length<=256*1024*1024;charged+=length
  with path.open('rb') as stream:stream.seek(metadata.st_size-length);tail=stream.read(length)
  matches=list(re.finditer(rb',\s*"index"\s*:',tail));assert matches
  reference=json.loads(b'{'+tail[matches[-1].start()+1:])
  assert set(reference)=={'index','journal_id','kind','previous_sha256','schema','sha256'}
  kind=reference['kind']
  wanted=kind=='SLEEP_RECIPE' or (row['recipes'] and kind=='SLEEP_COMPLETE') or (complete_history is not None and kind=='REQUEST' and row['following_request'] is None)
  if not wanted:continue
  record,file_sha=read(path,64*1024*1024);document=record['document']
  assert record['sha256']==digest({key:value for key,value in record.items() if key!='sha256'})
  receipt=dict(index=record['index'],record_sha256=record['sha256'],file_sha256=file_sha,path=str(path),mtime_ns=metadata.st_mtime_ns)
  if kind=='SLEEP_RECIPE':
   if document['policy']=='R181_NEW_ONLY_V1' and document['selected_old_rows']==0:
    row['recipes'].append(dict(receipt,document=document))
  elif kind=='SLEEP_COMPLETE' and row['completed'] is None:
   state=document['resume_state']['state'];assert document['status']=='COMPLETE' and state['pending'] is None
   assert document['resume_state']['sha256']==digest(state) and document['cycle']>loaded['saved_cycle']
   complete_history=state['history'];row['completed']=dict(receipt,cycle=document['cycle'],history_sha256=digest(complete_history),
        history_events=len(complete_history['events']),new_row_sha256=document.get('new_row_sha256'),optimizer_steps=document.get('optimizer_steps'))
  elif kind=='REQUEST':
   history=document['resume_state']['state']['history']
   assert document['resume_state']['sha256']==digest(document['resume_state']['state'])
   row['following_request']=dict(receipt,history_sha256=digest(history),history_events=len(history['events']),
      completed_events_preserved=history['events'][:len(complete_history['events'])]==complete_history['events'],
      view_operations_unchanged=history['operations']==complete_history['operations'])
 rows.append(row)
print(json.dumps(dict(rows=rows,observed_unix=time.time(),bytes_charged=charged,sealed_reads=0,
 coverage='last128 record metadata; selected records self-hash checked; no full chain/intents audit; no raw text export')))
'''


def main():
    repository = HERE.parents[3]
    helper = repository / 'research_loop/workers/r179_context_survival_20260917/node1/autonomy_node1.py'
    specification = importlib.util.spec_from_file_location('node1_existing_post', helper)
    posting = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(posting)
    directory = HERE / 'JOURNAL_OVERLAY_PROGRESS'
    directory.mkdir(mode=0o700)
    pins = {str(path): digest(path.read_bytes()) for path in (Path(__file__), helper)}
    deadline = time.monotonic() + 14400
    state = dict(posted=[])
    write(directory / 'STARTED.json', dict(pid=os.getpid(), source_pins=pins,
          deadline_unix=time.time()+14400, child_actions=0, provider_calls=0))
    while time.monotonic() < deadline:
        require(all(digest(Path(path).read_bytes()) == sha for path, sha in pins.items()), 'unchanged_observer')
        command = 'CUDA_VISIBLE_DEVICES= PYTHONDONTWRITEBYTECODE=1 python3 -c ' + shlex.quote(REMOTE)
        result = subprocess.run(['bash', str(repository / 'gpu/a100_ssh.sh'), command],
                                capture_output=True, text=True, timeout=90)
        output = directory / ('OBSERVATION_' + str(time.time_ns()) + '.json')
        write(output, dict(returncode=result.returncode, stdout=result.stdout, stderr=result.stderr,
                           observed_unix=time.time()))
        if result.returncode == 0:
            for row in json.loads(result.stdout)['rows']:
                for kind, evidence in (('journal-overlay-LOADED', row['loaded'] if row['overlay_loaded'] else None),
                        ('completed-new-only-sleep', row['completed']), ('following-REQUEST', row['following_request']),
                        ('handoff-failure', row['failures'])):
                    if evidence:
                        event = kind + ':' + str(row['physical'])
                        posting.post(directory, state, event, event,
                            'Metadata receipt `' + str(output.relative_to(repository)) + '`. Actual evidence: `'
                            + json.dumps(evidence, sort_keys=True) + '`. Recipe count' + str(len(row['recipes']))
                            + '; no sealed reads, no outcome inference; selected-record hashes, not full journal audit.')
        time.sleep(120)


if __name__ == '__main__':
    main()
