"""Read current native controls and safe boundary metadata for all eight lives."""

import json
from pathlib import Path
import shlex
import subprocess
import time

from activate_parent import read, reference, require, write


HERE = Path(__file__).resolve().parent
R179 = HERE.parents[1] / 'r179_context_survival_20260917/node5'
REMOTE = '''import hashlib,json,os,time
from pathlib import Path
def ref(path):
 raw=Path(path).read_bytes();return dict(path=str(path),sha256=hashlib.sha256(raw).hexdigest())
def tail(path):
 with Path(path).open('rb') as stream:
  stream.seek(max(0,Path(path).stat().st_size-4096));raw=stream.read()
 return json.loads(b'{'+raw[raw.rfind(b',"index":')+1:])
rows=[]
native_controls={}
for process in Path('/proc').iterdir():
 if not process.name.isdigit(): continue
 try:
  if process.stat().st_uid != 2524: continue
  args=(process/'cmdline').read_bytes().rstrip(b'\\0').decode().split('\\0')
  if args[:3] != ['/localhome/local-rohing/v2/venv/bin/python','-B','-m']: continue
  if 'gpu.orch_r125_continual_guard' not in args or 'native' not in args: continue
  config_path=Path(args[args.index('--config')+1]);config=json.loads(config_path.read_bytes())
  plan=json.loads(Path(config['plan_path']).read_bytes())
  native_controls.setdefault(plan['root'],[]).append(int(process.name))
 except (FileNotFoundError,PermissionError,ProcessLookupError): continue
for item in ITEMS:
 candidates=native_controls.get(item['logical_root'],[])
 if len(candidates)!=1:
  rows.append(dict(label=item['label'],blocked='actual_native_count_not_one',count=len(candidates)));continue
 item['pid']=candidates[0]
 process=Path('/proc')/str(item['pid']);fields=(process/'stat').read_text().rsplit(')',1)[1].split()
 args=(process/'cmdline').read_bytes().rstrip(b'\\0').decode().split('\\0')
 assert process.stat().st_uid==2524 and 'gpu.orch_r125_continual_guard' in args and 'native' in args
 config_path=Path(args[args.index('--config')+1]);config=json.loads(config_path.read_bytes());plan_path=Path(config['plan_path']);plan=json.loads(plan_path.read_bytes())
 root=Path(item['storage_root']);paths=sorted((root/'stream/records').glob('[0-9]'*20+'.json'));head=tail(paths[-1]);saved=None
 for path in reversed(paths):
  meta=tail(path)
  if meta['kind']=='SLEEP_COMPLETE':
   document=json.loads(path.read_bytes())['document'];checkpoint=document['checkpoint'];state=document['resume_state'];saved=dict(record=ref(path),record_sha256=meta['sha256'],index=meta['index'],cycle=document['cycle'],status=document['status'],state_sha256=state['sha256'],optimizer_steps=checkpoint['optimizer_steps'],adapter_sha256=checkpoint['adapter_state_sha256'],checkpoint_bundle=checkpoint['checkpoint_sha256']);break
 rows.append(dict(label=item['label'],physical=plan['physical'],logical_root=plan['root'],storage_root=str(root),
  identity=dict(pid=item['pid'],start_ticks=fields[19],uid=2524,state=fields[0],cwd=os.readlink(process/'cwd'),argv_sha256=hashlib.sha256((process/'cmdline').read_bytes()).hexdigest()),
  config_ref=ref(config_path),plan_ref=ref(plan_path),plan={key:plan.get(key) for key in ('root','source_root','gpu_uuid','physical','hard_end_unix','lease_end_unix','rehearsal_presentations','new_presentations')},
  native=ref(Path(plan['source_root'])/'gpu/orch_r125_continual_native.py'),head=head,head_mtime=paths[-1].stat().st_mtime,saved=saved,
  existing_handoff_root=str(config_path.parent),no_signals=True,observed_unix=time.time()))
print(json.dumps(dict(rows=rows,observed_unix=time.time(),no_sealed_readout=True)))
'''


def main():
    preparation = read(R179 / 'PREPARATION_1789664527216450780.json')
    observed = {row['label']: row for row in read(R179 / 'ROLLOUT_METADATA_1789676961309273600.json')['rows']}
    items = []
    for row in preparation['rows']:
        pid = observed[row['label']].get('loaded', {}).get('pid') if observed[row['label']].get('loaded') else None
        items.append(dict(label=row['label'], pid=pid or row['identity']['pid'], storage_root=row['storage_root'],
                          logical_root=row['logical_root']))
    response = subprocess.run(['bash', str(HERE.parents[3] / 'gpu/ovx3_ssh.sh'),
        'python3 -B -c ' + shlex.quote(REMOTE.replace('ITEMS', repr(items)))], capture_output=True, text=True, timeout=50)
    require(response.returncode == 0, 'read_only_native_inventory:' + response.stderr[-300:])
    document = json.loads(response.stdout)
    document.update(recipe='R181_NEW_ONLY_V1', new_presentations=16, rehearsal_presentations=0,
        directive='Rohin181 Main minimal canonical patch, next complete saved boundary; preserve optimizer/RNG/history; C2 first',
        C2='Prospective logged recipe amendment only; fixed172 parent messages/config untouched')
    path = HERE / ('R181_CURRENT_' + str(time.time_ns()) + '.json')
    write(path, document)
    print(json.dumps(dict(receipt=reference(path), rows=[row if row.get('blocked') else dict(label=row['label'],pid=row['identity']['pid'],
        source=row['plan']['source_root'],head=row['head'],saved_cycle=row['saved']['cycle'],saved_step=row['saved']['optimizer_steps']) for row in document['rows']])))


if __name__ == '__main__':
    main()
