"""Bounded public training receipts only; never inspect rows or selection scores."""

import datetime
import json
from pathlib import Path
import shlex
import subprocess


HERE = Path(__file__).resolve().parent
REMOTE = r'''
import datetime,json,pathlib,subprocess
result=dict(observed_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),arms=[])
for rank in [8,16]:
 root=pathlib.Path(f'/localhome/local-rohing/orch_r209_ovx5_allpair1m_rank{rank}_20260918_candidate1')
 row=dict(rank=rank,root=str(root),receipts={})
 names=['DISPATCH_ATTEMPT.json','CONFINEMENT_CPU.json','ADMISSION.json','OUTER_EXIT.json',
 'training/LOADED.json','training/PROGRESS_000001.json','training/PILOT_COMPLETE.json',
 'training/SUSTAINED_STARTED.json','training/COMPLETED.json']
 progress=sorted((root/'training').glob('PROGRESS_*.json'))
 if progress:names.append(str(progress[-1].relative_to(root)))
 for name in dict.fromkeys(names):
  path=root/name
  if path.exists():row['receipts'][name]=json.loads(path.read_bytes())
 if progress and 'training/PILOT_COMPLETE.json' in row['receipts']:
  current=json.loads(progress[-1].read_bytes());pilot=row['receipts']['training/PILOT_COMPLETE.json']
  finish=current['observed_unix']+(1000000-current['aggregate_comparisons'])/current['pairs_per_second']+pilot['selection_additional_seconds']
  row['rolling_eta']=dict(predicted_finish_if_current_contention_persisted_utc=datetime.datetime.fromtimestamp(finish,datetime.timezone.utc).isoformat(),aggregate_pairs_per_second=current['pairs_per_second'],temporary_diagnostic_contention_included=True,remaining_diagnostic_cost_not_separately_predicted=True,baseline_pilot_finish_utc=pilot['predicted_finish_utc'])
 row['diagnostics']={}
 for path in sorted((root/'checkpoint_diagnostics').glob('*/COMPLETE.json'))+sorted((root/'checkpoint_diagnostics').glob('*/FAILED.json')):
  row['diagnostics'][str(path.relative_to(root))]=json.loads(path.read_bytes())
 row['contrast_execution_metadata']={}
 for path in sorted((root/'checkpoint_diagnostics').glob('*/CONTRAST.private.json')):
  metadata=json.loads(path.read_bytes())
  row['contrast_execution_metadata'][path.parent.name]=dict(cases=metadata['cases'],contests=metadata['contests'],case_ids_sha256=metadata['case_ids_sha256'],scored=sum(record['status']=='SCORED' for record in metadata['records']),file_mtime_unix=path.stat().st_mtime)
 row['diagnostic_dispatch']={}
 for name in ['DIAGNOSTIC_ADMISSION.json','DIAGNOSTIC_OUTER_EXIT.json','checkpoint_diagnostics/WATCH_STARTED.json']:
  path=root/name
  if path.exists():row['diagnostic_dispatch'][name]=json.loads(path.read_bytes())
 result['arms'].append(row)
result['nvml']=subprocess.check_output(['nvidia-smi','--query-compute-apps=gpu_uuid,pid,used_gpu_memory','--format=csv,noheader'],text=True,timeout=15).strip().splitlines()
print(json.dumps(result))
'''


def save(path, document):
    content = json.dumps(document, indent=2, sort_keys=True) + '\n'
    patch = '*** Begin Patch\n*** Add File: ' + str(path) + '\n'
    patch += ''.join('+' + line + '\n' for line in content.splitlines()) + '*** End Patch\n'
    subprocess.run(['apply_patch'], input=patch, text=True, capture_output=True, check=True)


def main():
    result = subprocess.run(['bash', 'gpu/ovx5_ssh.sh', '/usr/bin/python3 -B -c ' + shlex.quote(REMOTE)],
        text=True, capture_output=True, check=True, timeout=35)
    document = json.loads(result.stdout)
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    target = HERE / ('R209_OBSERVATION_' + stamp + '.json')
    save(target, document)
    for arm in document['arms']:
        print(json.dumps(arm))
    print('SAVED', target)


if __name__ == '__main__':
    main()
