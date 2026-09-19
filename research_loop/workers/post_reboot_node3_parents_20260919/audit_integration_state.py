"""Read-only live authority/state cuts; explicitly not an admission/drain barrier."""

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import time

from transport_preflight import HERE, SCORER, SHARED, inspect, remote


REMOTE = '''
from pathlib import Path
import hashlib,json,os,stat,sys,time
value=json.load(sys.stdin)
root=Path(value['root'])
def sha(raw): return hashlib.sha256(raw).hexdigest()
def file_ref(path):
 raw=path.read_bytes()
 return dict(path=str(path),sha256=sha(raw),bytes=len(raw)),json.loads(raw)
def canonical(value): return json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode()
def socket_ref(path):
 path=Path(path)
 metadata=path.stat()
 return dict(path=str(path),is_socket=stat.S_ISSOCK(metadata.st_mode),inode=metadata.st_ino,
  device=metadata.st_dev,uid=metadata.st_uid,mode=oct(stat.S_IMODE(metadata.st_mode)),
  queue_count_not_observed=True)
processes=[]
for pid,expected in [(499900,'10094999'),(502015,'10101591'),(448173,'9898014')]:
 proc=Path('/proc',str(pid))
 fields=(proc/'stat').read_text().rsplit(')',1)[1].split()
 assert fields[19]==expected and fields[0] not in ('Z','X'),'live_incarnation_changed'
 arguments=(proc/'cmdline').read_bytes().split(b'\\0')
 config_path=Path(os.fsdecode(arguments[arguments.index(b'--config')+1]))
 reference,config=file_ref(config_path)
 processes.append(dict(pid=pid,start_ticks=fields[19],uid=proc.stat().st_uid,
  command_sha256=sha((proc/'cmdline').read_bytes()),config_reference=reference,
  deadline_unix=config['deadline_unix'],source_root=str(root/'source') if pid==499900 else None))
 if pid==499900: scorer_config=config
manifest_ref=scorer_config['source_manifest']
manifest_raw=Path(manifest_ref['path']).read_bytes()
assert sha(manifest_raw)==manifest_ref['sha256'],'original_source_manifest_changed'
manifest=json.loads(manifest_raw)
for relative,expected in manifest.items():
 path=root/'source'/relative
 assert path.is_file() and not path.is_symlink() and sha(path.read_bytes())==expected,'immutable_scorer_source_changed'
renew=Path('/localhome/local-rohing/orch_r233_lease_renewal_20260918/attempt2/shared2')
routes=[]
for directory in (renew,root):
 config_ref,config=file_ref(directory/'BRIDGE_CONFIG.private.json')
 target_ref,target=file_ref(directory/'bridge/TARGET.json')
 routes.append(dict(config_reference=config_ref,target_reference=target_ref,
  endpoint=socket_ref(config['endpoint']),target=socket_ref(target['socket']),
  runtime_queue_or_drain_API=False))
cuts=[]
for ordinal in range(2):
 sessions=[]
 for identifier,output in sorted(scorer_config['outputs'].items()):
  output=Path(output)
  state_ref,state=file_ref(output/'SESSION_STATE.private.json')
  attempts=[]
  for attempt in sorted((output/'attempts').iterdir()):
   if not attempt.is_dir(): continue
   retained={name:sha((attempt/name).read_bytes()) for name in ('REQUEST.json','BEFORE.json','RESULT.json','AFTER.json')
    if (attempt/name).is_file()}
   item=dict(identifier=attempt.name,files=retained,complete_files=all(name in retained for name in ('REQUEST.json','BEFORE.json','RESULT.json','AFTER.json')))
   if (attempt/'REQUEST.json').is_file():
    request=json.loads((attempt/'REQUEST.json').read_bytes())
    item['origin']=request['request']['origin'];item['request_unix']=request.get('unix')
   attempts.append(item)
  ledger=root/'epochs'/identifier
  epoch_files={path.name:sha(path.read_bytes()) for path in sorted(ledger.glob('*.json'))}
  last_state=sha((output/'SESSION_STATE.private.json').read_bytes())
  sessions.append(dict(session_id=identifier,output=str(output),state_reference=state_ref,
   stable_state_during_read=last_state==state_ref['sha256'],phase=state['phase'],source_mode=state['source_mode'],
   life_root=state['life_root'],session_binding_sha256=sha(canonical(state['session_binding'])),
   game_sha256=sha(canonical(state['game'])),policy_sha256=sha(canonical(state['policy'])),
   seen_count=len(state['seen']),seen=sorted(state['seen']),seen_sha256=sha(canonical(sorted(state['seen']))),
   attempts=attempts,epoch_directory=str(ledger),epoch_files=epoch_files))
 cuts.append(dict(unix=time.time(),sessions=sessions))
 if ordinal==0: time.sleep(2)
print(json.dumps(dict(unix=time.time(),processes=processes,
 boot_id=Path('/proc/sys/kernel/random/boot_id').read_text().strip(),source_manifest=manifest_ref,
 verified_source_files=len(manifest),source_manifest_entries=manifest,routes=routes,
 scorer_socket=socket_ref(root/'sockets/native.sock'),cuts=cuts,
 admission_closed=False,drained=False,kernel_backlog_observed=False,synthetic_requests=0,
 reason='Live admissions remain open; stable durable snapshots do not prove no queued or in-flight requests.')))
'''


def host_identity(pid):
    root = Path('/proc', str(pid))
    fields = (root/'stat').read_text().rsplit(')', 1)[1].split()
    return dict(pid=pid, start_ticks=fields[19], state=fields[0],
        command_sha256=hashlib.sha256((root/'cmdline').read_bytes()).hexdigest())


def main():
    preflight = inspect()
    node = remote('ovx4_ssh.sh', REMOTE, dict(root=SCORER, shared=SHARED))
    started = json.loads((HERE/'TRANSPORT_STARTED.json').read_bytes())
    runtime = Path(started['runtime'])
    config_path = Path(started['output'])/'CONFIG.json'
    logs = []
    for path in sorted((runtime/'proxy').glob('TRANSPORT_*.json')):
        raw = path.read_bytes()
        logs.append(dict(path=str(path),file_sha256=hashlib.sha256(raw).hexdigest(),record=json.loads(raw)))
    result = dict(schema='R233_READ_ONLY_INTEGRATION_CUT_NOT_DRAIN_PROOF_V1', unix=time.time(),
        preflight=preflight, scorer=node,
        host=dict(boot_id=Path('/proc/sys/kernel/random/boot_id').read_text().strip(),
            processes=[host_identity(pid) for pid in (330973,399392,425470,459421)],
            controller_children=[host_identity(item['pid']) for item in started['children']],
            runtime=str(runtime),proxy_config=dict(path=str(config_path),
                sha256=hashlib.sha256(config_path.read_bytes()).hexdigest(),value=json.loads(config_path.read_bytes())),
            completed_transport_logs=logs,durable_admission_intents_available=False,
            in_flight_or_unaccepted_requests_not_enumerated=True),
        mutations=[],native_signals=[],scorer_signals=[],live_requests_sent=0,drain_proved=False)
    raw=json.dumps(result,indent=2,sort_keys=True)+'\n'
    name='INTEGRATION_CUT_'+str(time.time_ns())+'.json'
    (HERE/name).write_text(raw)
    (HERE/'INTEGRATION_CUT_LATEST.json').write_text(raw)
    previous={row['session_id']:row for row in node['cuts'][0]['sessions']}
    summaries=[]
    for row in node['cuts'][1]['sessions']:
        summaries.append(dict(session=row['session_id'],phase=row['phase'],seen=row['seen_count'],
            attempts=len(row['attempts']),incomplete=[item['identifier'] for item in row['attempts'] if not item['complete_files']],
            stable_across_cut=previous[row['session_id']]['state_reference']['sha256']==row['state_reference']['sha256'],
            epoch_files=len(row['epoch_files'])))
    print(json.dumps(dict(cut=name,utc=datetime.fromtimestamp(result['unix'],timezone.utc).isoformat(),
        processes=node['processes'],routes=node['routes'],sessions=summaries,
        completed_VM_transport_logs=len(logs),admission_closed=False,drain_proved=False),indent=2))


if __name__=='__main__':
    main()
