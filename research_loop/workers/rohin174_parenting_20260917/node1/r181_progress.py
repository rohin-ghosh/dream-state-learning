"""Bounded metadata-only first-LOADED/first-recipe reporter; no process or model control."""

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
root=Path('/localhome/local-rohing/orch_r181_node1_20260917');rows=[];charged=0
def read(path,maximum=4*1024*1024):
 global charged
 metadata=path.lstat();assert stat.S_ISREG(metadata.st_mode) and metadata.st_size<=maximum
 assert charged+metadata.st_size<=16*1024*1024;charged+=metadata.st_size
 raw=path.read_bytes();assert len(raw)==metadata.st_size
 return json.loads(raw),hashlib.sha256(raw).hexdigest()
for lane in range(2,8):
 directory=root/'lanes'/('lane'+str(lane));staged,unused=read(directory/'STAGED.json')
 row=dict(physical=lane,root=staged['old_plan']['root'],source_root=staged['source_root'],loaded=None,recipes=[],failures=[])
 if (directory/'LOADED_RECEIPT.json').exists():
  row['loaded'],row['loaded_receipt_sha256']=read(directory/'LOADED_RECEIPT.json')
  row['loaded_receipt_path']=str(directory/'LOADED_RECEIPT.json')
  guard,unused=read(Path(staged['new_config']));plan,unused=read(Path(guard['plan_path']))
  assert plan['rehearsal_presentations']==0 and plan['new_presentations']==16 and plan['anchor_lambda']==0.25
  row['plan_path']=guard['plan_path'];row['plan_sha256']=guard['plan_sha256']
  row['native_sha256']=guard['source_pins']['gpu/orch_r125_continual_native.py']
 for path in directory.glob('FAILURE_*.json'):
  failure,sha=read(path);row['failures'].append(dict(path=str(path),sha256=sha,document=failure))
 if row['loaded']:
  records=Path(row['root'])/'stream/records';assert not records.is_symlink()
  paths=sorted(path for path in records.iterdir() if re.fullmatch('[0-9]{20}\.json',path.name))
  for path in paths[-128:]:
   metadata=path.lstat();assert stat.S_ISREG(metadata.st_mode)
   length=min(metadata.st_size,4096);assert charged+length<=16*1024*1024;charged+=length
   with path.open('rb') as stream:stream.seek(metadata.st_size-length);tail=stream.read(length)
   matches=list(re.finditer(rb',\s*"index"\s*:',tail));assert matches
   record_meta=json.loads(b'{'+tail[matches[-1].start()+1:])
   assert set(record_meta)=={'index','journal_id','kind','previous_sha256','schema','sha256'}
   if record_meta['kind']=='SLEEP_RECIPE':
    record,file_sha=read(path,8192);document=record['document']
    assert document['policy']=='R181_NEW_ONLY_V1' and document['selected_old_rows']==0
    row['recipes'].append(dict(path=str(path),record_sha256=record['sha256'],file_sha256=file_sha,
                              mtime_ns=metadata.st_mtime_ns,document=document))
 rows.append(row)
print(json.dumps(dict(rows=rows,bytes_charged=charged,observed_unix=time.time(),sealed_reads=0)))
'''


def main():
    repository = HERE.parents[3]
    helper = repository / 'research_loop/workers/r179_context_survival_20260917/node1/autonomy_node1.py'
    specification = importlib.util.spec_from_file_location('existing_metadata_post', helper)
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    directory = HERE / 'R181_PROGRESS'
    directory.mkdir(mode=0o700)
    pins = {str(path): digest(path.read_bytes()) for path in (Path(__file__), helper)}
    state = dict(posted=[])
    write(directory / 'STARTED.json', dict(pid=os.getpid(), observed_unix=time.time(), deadline_unix=time.time()+14400,
          source_pins=pins, child_actions=0, provider_calls=0))
    deadline = time.monotonic() + 14400
    while time.monotonic() < deadline:
        require(all(digest(Path(path).read_bytes()) == expected for path, expected in pins.items()), 'unchanged_metadata_reporter')
        command = 'CUDA_VISIBLE_DEVICES= PYTHONDONTWRITEBYTECODE=1 python3 -c ' + shlex.quote(REMOTE)
        result = subprocess.run(['bash', str(repository / 'gpu/a100_ssh.sh'), command], capture_output=True, text=True, timeout=45)
        with (directory / 'OBSERVATIONS.jsonl').open('a') as stream:
            stream.write(json.dumps(dict(returncode=result.returncode, stdout=result.stdout, stderr=result.stderr,
                                        observed_unix=time.time())) + '\n')
        if result.returncode == 0:
            snapshot = json.loads(result.stdout)
            for row in snapshot['rows']:
                lane = str(row['physical'])
                if row['loaded']:
                    loaded = row['loaded']
                    module.post(directory, state, 'loaded:' + lane, 'R181 actual LOADED lane' + lane,
                        'Actual saved-boundary successor PID' + str(loaded['actor_pid']) + ', saved cycle' + str(loaded['saved_cycle'])
                        + ', optimizer steps' + str(loaded['optimizer_steps']) + '. Source `' + row['source_root']
                        + '`, native SHA `' + row['native_sha256'] + '`, plan SHA `' + row['plan_sha256']
                        + '`: rehearsal0/new16/anchor0.25. Exact LOADED record `' + loaded['record_sha256']
                        + '`, receipt `' + row['loaded_receipt_path'] + '` SHA `' + row['loaded_receipt_sha256']
                        + '`. Full checkpoint/optimizer/RNG/history custody is in the existing boundary receipts. '
                        + 'LOADED is not yet proof of a new sleep recipe or completed new-only sleep.')
                if row['recipes']:
                    recipe = row['recipes'][0]
                    write_path = directory / ('FIRST_SLEEP_RECIPE_LANE' + lane + '.json')
                    if not write_path.exists():
                        write(write_path, dict(recipe, native_sha256=row['native_sha256'], observed_unix=time.time()))
                    module.post(directory, state, 'recipe:' + lane, 'R181 first actual SLEEP_RECIPE lane' + lane,
                        'Actual recipe `' + recipe['path'] + '` record SHA `' + recipe['record_sha256']
                        + '`: ' + json.dumps(recipe['document'], sort_keys=True) + '. Native SHA `' + row['native_sha256']
                        + '`. Old rows remain saved but selected_old_rows=0 before encoding/training; new16x and anchors unchanged. '
                        + 'Recipe-start proof only, not completed updates or a scientific improvement claim. Local receipt `'
                        + str(write_path) + '`. No model, provider, signal or sealed-content actions by this observer.')
                for failure in row['failures']:
                    module.post(directory, state, 'failure:' + failure['sha256'], 'R181 handoff fault lane' + lane,
                                'Exact failure `' + failure['path'] + '` SHA `' + failure['sha256'] + '`: '
                                + json.dumps(failure['document'], sort_keys=True) + '. No automatic replay/retry by this observer.')
            if sum(event.startswith('recipe:') for event in state['posted']) == 6:
                break
        time.sleep(120)
    write(directory / 'FINISHED.json', dict(observed_unix=time.time(), posted=state['posted']))


if __name__ == '__main__':
    main()
