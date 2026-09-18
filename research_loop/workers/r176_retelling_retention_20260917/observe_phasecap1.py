"""Finite, metadata-only observations of the two already-invoked cells; never relaunch."""

from datetime import datetime, timezone
import json
import os
from pathlib import Path
import shlex
import subprocess
import time

import preparation_io as common


WORKER = Path(__file__).resolve().parent
MAX_OBSERVATIONS = 48
PER_OBSERVATION_BYTES = 128 * 1024
REMOTE = '''import hashlib,json,os,pathlib,sys,time
os.umask(0o077)
request=json.loads(sys.stdin.buffer.read(131072))
base=pathlib.Path('/localhome/local-rohing/orch_r176_retelling_retention_20260917_generation1')
root=base/'main_phasecap1_monitor1'/('%03d'%request['index'])
root.mkdir(parents=True,mode=0o700,exist_ok=False)
used=request['transport_bytes'];sequence=0
def write(path,value):
 raw=json.dumps(value,sort_keys=True,separators=(',',':')).encode()
 with path.open('xb') as stream:stream.write(raw);stream.flush();os.fsync(stream.fileno())
def charge(path,size):
 global used,sequence
 assert used+size<=request['per_observation_bytes']
 write(root/('READ_%04d.json'%sequence),{'path':str(path),'bytes':size,
  'authority':request['metadata_allowance']['reference'],'status':'CHARGED_BEFORE_READ_NO_REFUND'})
 used+=size;sequence+=1
def read(path):
 assert path==path.resolve() and path.is_relative_to(base)
 with path.open('rb',buffering=0) as stream:
  size=os.fstat(stream.fileno()).st_size
  assert size<=32768
  charge(path,size);raw=stream.read(size);assert len(raw)==size
 return json.loads(raw)
def exists_document(path):return read(path) if path.is_file() else None
def live(pid):
 path=pathlib.Path('/proc')/str(pid)/'stat'
 try:
  charge(path,4096)
  with path.open('rb',buffering=0) as stream:raw=stream.read(4096)
  assert len(raw)<4096
  fields=raw.decode().rsplit(')',1)[1].split()
  return fields[0] not in ('Z','X')
 except FileNotFoundError:return False
write(root/'REQUEST.json',request)
rows=[]
for controller in request['controllers']:
 execution=controller['execution'];config=read(pathlib.Path(execution['path']))
 key='C2_sleep000033_'+config['condition'];attempt=base/'attempts'/key
 reservation=exists_document(base/'ledger'/(key+'.RESERVED.json'))
 terminal=exists_document(base/'ledger'/(key+'.TERMINAL.json'))
 refusal=exists_document(attempt/'REFUSED.json')
 launched=exists_document(attempt/'TIMEOUT.json')
 complete=exists_document(attempt/'sealed/COMPLETE.json')
 controller_alive=live(controller['controller_pid'])
 native_timeout_alive=live(launched['identity']['pid']) if launched else False
 if reservation:assert reservation['execution']==execution and reservation['calls_charged']==3
 if complete:assert complete['execution']==execution and complete['calls']==3 and complete['status']=='COMPLETE'
 if terminal:assert terminal['calls_charged']==3 and terminal['status'] in ('COMPLETE','FAILED_CHARGED_NO_RETRY')
 fully_complete=bool(terminal and terminal['status']=='COMPLETE' and complete)
 status='COMPLETE' if fully_complete else ('FAILED_CHARGED_NO_RETRY' if terminal else
  ('ADMISSION_REFUSED_NO_RETRY' if refusal else ('RUNNING_OR_PREFLIGHT' if controller_alive or native_timeout_alive
   else 'EXITED_WITHOUT_COMPLETE_TERMINAL_NO_RETRY')))
 rows.append({'execution_sha256':execution['sha256'],'status':status,'controller_alive':controller_alive,
  'native_timeout_alive':native_timeout_alive,'admitted':bool(reservation),'native_launched':bool(launched),
  'calls_charged':reservation['calls_charged'] if reservation else 0,
  'completed_validated_calls':3 if fully_complete else 0,
  'generation_response_artifacts_present_not_read':sum((attempt/'sealed'/(str(position)+'.RAW.private.json')).is_file() for position in range(3)),
  'generation_call_intent_artifacts_present_not_read':sum((attempt/'sealed'/(str(position)+'.RESERVED.private.json')).is_file() for position in range(3)),
  'model_load_precharge_present':(attempt/'MODEL_LOAD_PRECHARGE.json').is_file(),
  'execution_terminal_present':bool(terminal),'attempt_once_present':(attempt/'ONCE.json').is_file()})
complete_jobs=sum(row['status']=='COMPLETE' for row in rows)
result={'schema':'R176_PHASECAP1_PUBLIC_EXECUTION_OBSERVATION_V1','observed_unix':time.time(),
 'scope':'ONLY_FIXED_C2_SLEEP33_TWO_CONDITIONS_SIX_CALLS','controllers_started':2,
 'controllers_alive':sum(row['controller_alive'] for row in rows),'admitted_jobs':sum(row['admitted'] for row in rows),
 'native_jobs_launched':sum(row['native_launched'] for row in rows),'native_timeout_processes_alive':sum(row['native_timeout_alive'] for row in rows),
 'completed_condition_jobs':complete_jobs,'completed_validated_calls':sum(row['completed_validated_calls'] for row in rows),
 'paired_checkpoints_complete':int(complete_jobs==2),'calls_charged':sum(row['calls_charged'] for row in rows),
 'generation_response_artifacts_present_not_read':sum(row['generation_response_artifacts_present_not_read'] for row in rows),
 'generation_call_intent_artifacts_present_not_read':sum(row['generation_call_intent_artifacts_present_not_read'] for row in rows),
 'missing_completed_condition_jobs':2-complete_jobs,'uncompleted_validated_calls':6-3*complete_jobs,
 'failed_or_refused_jobs':sum(row['status'] in ('FAILED_CHARGED_NO_RETRY','ADMISSION_REFUSED_NO_RETRY','EXITED_WITHOUT_COMPLETE_TERMINAL_NO_RETRY') for row in rows),
 'all_starts_terminal_or_exited':all(row['status']!='RUNNING_OR_PREFLIGHT' for row in rows),
 'model_load_precharges_present':sum(row['model_load_precharge_present'] for row in rows),
 'rows':rows,'metadata_charged_bytes':used,'no_retries':True,'provider_calls':0,
 'other_cells_started':0,'private_text_maps_scores_read':False,'absolute_end_unix':1789673400}
write(root/'PUBLIC_METADATA.json',result)
print(json.dumps(result,sort_keys=True))
'''


def main():
    os.umask(0o077)
    common.validate_controls(WORKER)
    root = WORKER / 'execution_phasecap1/monitor1'
    root.mkdir(mode=0o700, exist_ok=False)
    launch = json.loads((WORKER / 'execution_phasecap1/PUBLIC_METADATA.json').read_bytes())
    common.require(launch['status'] == 'TWO_EXACT_RUNNER_STARTS_INVOKED', 'observe_existing_two_starts_only')
    ledger = common.Ledger(WORKER / 'preparation1/global_ledger')
    allowance = ledger.reserve('C2_phasecap1_monitor1_metadata', 'C2', 'metadata',
        MAX_OBSERVATIONS * PER_OBSERVATION_BYTES, discovery=True)
    storage = ledger.reserve('C2_phasecap1_monitor1_storage', '_campaign', 'storage', common.MIB)
    common.write(root / 'PRE_IO_SCOPE.json', dict(metadata_allowance=allowance, storage_allowance=storage,
        max_observations=MAX_OBSERVATIONS, per_observation_bytes=PER_OBSERVATION_BYTES,
        interval_seconds=20, no_model_provider_signals_or_relaunches=True))
    last = None
    for index in range(MAX_OBSERVATIONS):
        if time.time() >= common.END:
            break
        request = dict(index=index, controllers=launch['controllers'], metadata_allowance=allowance,
            per_observation_bytes=PER_OBSERVATION_BYTES, transport_bytes=0)
        for iteration in range(4):
            amount = len(common.canonical(request)) + len(REMOTE.encode())
            if amount == request['transport_bytes']:
                break
            request['transport_bytes'] = amount
        common.require(request['transport_bytes'] == len(common.canonical(request)) + len(REMOTE.encode()),
            'exact_finite_observation_transport')
        common.write(root / f'{index:03d}.PRECHARGE.json', dict(
            bytes=PER_OBSERVATION_BYTES, authority=allowance['reference'],
            status='FINITE_OBSERVATION_SLICE_PRECHARGED_NO_REFUND'))
        try:
            result = subprocess.run(['bash', str(WORKER.parents[2] / 'gpu/ovx_ssh.sh'),
                'python3 -c ' + shlex.quote(REMOTE)], input=common.canonical(request), capture_output=True, timeout=45)
            last = json.loads(result.stdout) if result.returncode == 0 else dict(
                status='OBSERVATION_FAILED_NO_AUTOMATIC_FOLLOWUP', returncode=result.returncode,
                stderr_sha256=common.sha(result.stderr), stderr_bytes=len(result.stderr))
        except subprocess.TimeoutExpired:
            last = dict(status='OBSERVATION_TIMEOUT_NO_AUTOMATIC_FOLLOWUP')
        common.write(root / f'{index:03d}.PUBLIC_METADATA.json', last)
        safe = {key: value for key, value in last.items() if key != 'rows'}
        print(json.dumps(safe, sort_keys=True), flush=True)
        if 'observed_unix' not in last or last['all_starts_terminal_or_exited']:
            break
        time.sleep(20)
    if last:
        reference = common.write(root / 'FINAL_PUBLIC_METADATA.json', last)
        observed = datetime.fromtimestamp(last.get('observed_unix', time.time()), timezone.utc).isoformat()
        status = '# R176 fixed C2 sleep33 execution status\n\nObserved UTC: ' + observed + '\n\n'
        for field in ('controllers_started', 'controllers_alive', 'admitted_jobs', 'native_jobs_launched',
                'completed_condition_jobs', 'completed_validated_calls', 'paired_checkpoints_complete',
                'calls_charged', 'generation_response_artifacts_present_not_read',
                'missing_completed_condition_jobs', 'failed_or_refused_jobs'):
            status += '- ' + field + ': ' + str(last.get(field, 'NOT_OBSERVED')) + '\n'
        status += '\nNo retries, other cells, provider calls, or private response/map/score disclosure.\n'
        status += 'Evidence: `' + reference['path'] + '` SHA256 `' + reference['sha256'] + '`.\n'
        common.write(WORKER / 'EXECUTION_PHASECAP1_STATUS_01.md', status.encode())


if __name__ == '__main__':
    main()
