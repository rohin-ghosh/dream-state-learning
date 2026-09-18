"""One bounded resource-only receiver observation, through the sanctioned wrapper."""

import json
import os

import prep_common as common
import prepare


SCRIPT = r'''
import hashlib,json,os,stat,time
from pathlib import Path
root=Path('/localhome/local-rohing/orch_r167_fleet_20260917_generation2')
used=0
def read(path):
 global used
 path=Path(path)
 assert path==path.resolve() and path.stat().st_size<=262144
 used+=path.stat().st_size
 assert used<=3*1024**2
 return json.loads(path.read_bytes())
boot=Path('/proc/sys/kernel/random/boot_id').read_text().strip()
def live(identity):
 try:
  path=Path('/proc')/str(identity['pid'])
  fields=(path/'stat').read_text().rsplit(')',1)[1].split()
  return fields[0] not in ('Z','X') and fields[19]==str(identity['start_ticks']) and identity['boot_id']==boot and (identity.get('uid') is None or path.stat().st_uid==identity['uid'])
 except (FileNotFoundError,ProcessLookupError):return False
owners=[]
paths=[root/name/'CONTROLLER_LAUNCH.json' for name in ('gpu_takeover_20260917t1403z','gpu_unused_off_generation1')]
paths+=list(root.glob('attempts/*/sealed/PROCESS.json'))
paths+=list(root.glob('attempts/*/LAUNCH.json'))
paths+=list(root.glob('launches/*/INITIATOR.json'))
paths+=list(root.glob('launches/*/WRAPPER.json'))
for path in paths:
 if path.exists():
  document=read(path)
  if 'identity' in document:
   identity=document['identity']
   owners.append(dict(path=str(path),identity=identity,live=live(identity)))
unresolved=[]
for path in root.glob('ledger/*.RESERVED.json'):
 key=path.name.removesuffix('.RESERVED.json')
 if not any((root/'ledger'/(key+'.'+status+'.json')).exists() for status in ('COMPLETE','FAILED')):
  unresolved.append(dict(reservation_path=str(path),native_identity_recorded=(root/'attempts'/key/'sealed/PROCESS.json').exists(),timeout_identity_recorded=(root/'attempts'/key/'LAUNCH.json').exists()))
other=[]
proc_bytes=0
for directory in Path('/proc').iterdir():
 if not directory.name.isdigit():continue
 try:
  if directory.stat().st_uid!=os.getuid():continue
  raw=(directory/'cmdline').read_bytes()
  proc_bytes+=len(raw)
  assert proc_bytes<=1024**2
  cwd=os.readlink(directory/'cwd')
  if str(root).encode() in raw or cwd.startswith(str(root)):
   fields=(directory/'stat').read_text().rsplit(')',1)[1].split()
   if fields[0] not in ('Z','X'):
    other.append(dict(pid=int(directory.name),start_ticks=fields[19],boot_id=boot,argv_sha256=hashlib.sha256(raw).hexdigest(),cwd=cwd))
 except (FileNotFoundError,ProcessLookupError,PermissionError):pass
runtime=read(root/'gpu_takeover_20260917t1403z/RUNTIME.json')['common']
resource={key:runtime[key] for key in ('python','python_sha256','model_dir','service_path','service_sha256','lease')}
lease=read(resource['lease']['path'])
assert hashlib.sha256(Path(resource['lease']['path']).read_bytes()).hexdigest()==resource['lease']['sha256']
source=root/'gpu_takeover_20260917t1403z/source'
source_files=[path for path in source.rglob('*') if path.is_file() and path.suffix in ('.py','.json')]
result=dict(status='RESOURCE_ONLY_NO_MODEL_CALLS',observed_unix=time.time(),owners=owners,
 live_bound_owners=sum(row['live'] for row in owners),matching_old_root_live_processes=other,
 old_reserved_without_terminal_count=len(unresolved),unresolved_ownership_metadata=unresolved,
 missing_controller_launch_records=[str(path) for path in paths[:2] if not path.exists()],
 runtime_resource=resource,lease=lease,receiving_template_source=str(source),
 receiving_template_file_count=len(source_files),receiving_template_stat_bytes=sum(path.stat().st_size for path in source_files),
 metadata_file_bytes_read=used,proc_bytes_read=proc_bytes,source_content_bytes_read=0,
 sealed_response_or_score_reads=0,signals_sent=0,provider_calls=0,gpu_calls=0)
print(json.dumps(result,sort_keys=True))
'''


def main():
    os.umask(0o077)
    scope,proposal,ledger=prepare.setup()
    ledger.reserve('receiver_resource_observation1','_campaign','metadata',4*prepare.MIB,discovery=True)
    result=json.loads(prepare.wrapper('ovx','receiver_resource_observation1','python3 -B -',SCRIPT.encode()))
    reference=common.write(prepare.PREP/'RECEIVER_RESOURCE_OBSERVATION_01.json',result)
    print(json.dumps(dict(status=result['status'],observed_unix=result['observed_unix'],
        bound_identity_records=len(result['owners']),live_bound_owners=result['live_bound_owners'],
        matching_old_root_live_processes=len(result['matching_old_root_live_processes']),
        old_reserved_without_terminal_count=result['old_reserved_without_terminal_count'],
        missing_controller_launch_records=len(result['missing_controller_launch_records']),
        receiving_template_files=result['receiving_template_file_count'],receiving_template_stat_bytes=result['receiving_template_stat_bytes'],
        evidence=reference,signals_sent=0,gpu_calls=0)))


if __name__=='__main__':
    main()
