"""Read-only native identity, inbox inode and public journal-head evidence."""

import json
from pathlib import Path
import shlex
import subprocess
import time

from console_baseline import read, ref, require, write


HERE = Path(__file__).resolve().parent
R179 = HERE.parents[1] / 'r179_context_survival_20260917/node5'
REMOTE = '''import hashlib,json,os
from pathlib import Path
def inode(path):
 info=Path(path).stat()
 return [info.st_dev,info.st_ino]
rows=[]
for item in ITEMS:
 row=dict(item)
 try:
  process=Path('/proc')/str(item['pid'])
  fields=(process/'stat').read_text().rsplit(')',1)[1].split()
  args=(process/'cmdline').read_bytes().rstrip(b'\\0').decode().split('\\0')
  assert process.stat().st_uid==2524 and 'gpu.orch_r125_continual_guard' in args and 'native' in args
  row.update(state=fields[0],start_ticks=fields[19],uid=2524,cwd=os.readlink(process/'cwd'),argv_sha256=hashlib.sha256((process/'cmdline').read_bytes()).hexdigest())
  if '--config' in args:
   config_path=Path(args[args.index('--config')+1]); config=json.loads(config_path.read_bytes())
   row['guard']=dict(path=str(config_path),sha256=hashlib.sha256(config_path.read_bytes()).hexdigest(),keys=sorted(config))
  logical=Path(item['logical_root']); stored=Path(item['storage_root'])
  mounted=process/'root'/logical.relative_to('/')
  row['inodes']=dict(host_logical=inode(logical),host_storage=inode(stored),native_logical=inode(mounted))
  row['inbox_fds']=[]
  for descriptor in (process/'fd').iterdir():
   try:
    target=os.readlink(descriptor)
    if target.endswith('/stream/inbox'):
     row['inbox_fds'].append(dict(fd=int(descriptor.name),target=target,inode=inode(descriptor)))
   except FileNotFoundError: pass
  row['host_storage_inbox_inode']=inode(stored/'stream/inbox')
  row['route_matches_open_native_inbox']=len(row['inbox_fds'])==1 and row['inbox_fds'][0]['inode']==row['host_storage_inbox_inode']
  records=sorted((stored/'stream/records').glob('[0-9]'*20+'.json'))
  if records:
   path=records[-1]; raw=path.read_bytes(); record=json.loads(raw)
   row['head']={key:record[key] for key in ('index','kind','journal_id','sha256')}
   row['head'].update(file_sha256=hashlib.sha256(raw).hexdigest(),mtime_unix=path.stat().st_mtime)
  row['process_cpu_ticks']=dict(user=fields[11],system=fields[12])
 except (FileNotFoundError,PermissionError,AssertionError,ValueError,KeyError) as error:
  row.update(error_type=type(error).__name__,error=str(error)[:180])
 rows.append(row)
print(json.dumps(dict(rows=rows,no_signals=True,no_inbox_writes=True,no_sealed_readouts=True)))
'''


def main():
    preparation = read(R179 / 'PREPARATION_1789664527216450780.json')
    historical = read(R179 / 'ROLLOUT_METADATA_1789676961309273600.json')
    by_label = {row['label']: row for row in historical['rows']}
    items = []
    for row in preparation['rows']:
        if row['label'] == 'C2':
            continue
        observed = by_label[row['label']]
        pid = observed.get('loaded', {}).get('pid') or row['identity']['pid']
        items.append(dict(label=row['label'], pid=pid, logical_root=row['logical_root'], storage_root=row['storage_root']))
    script = REMOTE.replace('ITEMS', repr(items))
    result = subprocess.run(['bash', str(HERE.parents[3] / 'gpu/ovx3_ssh.sh'),
        'python3 -B -c ' + shlex.quote(script)], capture_output=True, text=True, timeout=35)
    require(result.returncode == 0, 'read_only_route_probe_failed')
    document = json.loads(result.stdout)
    document.update(observed_unix=time.time(), preparation=ref(R179 / 'PREPARATION_1789664527216450780.json'),
                    PID_source=ref(R179 / 'ROLLOUT_METADATA_1789676961309273600.json'))
    receipt = HERE / ('LIVE_ROUTE_STATUS_' + str(time.time_ns()) + '.json')
    write(receipt, document)
    print(json.dumps(dict(receipt=ref(receipt), rows=[{key:row.get(key) for key in
        ('label','pid','state','route_matches_open_native_inbox','head','error_type','error')} for row in document['rows']])))


if __name__ == '__main__':
    main()
