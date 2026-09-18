"""Collect only public pilot counts, timings, device and provenance receipts."""

import datetime
import json
from pathlib import Path
import shlex
import subprocess


HERE = Path(__file__).resolve().parent
REMOTE = r'''
import datetime,json,pathlib,subprocess
root=pathlib.Path('/localhome/local-rohing/orch_r207_ovx5_widegap1m_20260918_candidate1')
result=dict(observed_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),host='[REDACTED_HOST]',root=str(root),receipts={})
for name in ['DISPATCH_STARTED.json','CONFINEMENT_CPU.json','ADMISSION.json','RECEIVING_CPU.json','candidate1/LOADED.json','candidate1/PILOT_COMPLETE.json','OUTER_EXIT.json']:
 if (root/name).exists():result['receipts'][name]=json.loads((root/name).read_bytes())
progress=sorted((root/'candidate1').glob('PROGRESS_*.json')) if (root/'candidate1').exists() else []
if progress:result['latest_progress']=json.loads(progress[-1].read_bytes())
result['compute_processes']=subprocess.check_output(['nvidia-smi','--query-compute-apps=gpu_uuid,pid,used_gpu_memory','--format=csv,noheader'],text=True,timeout=12).strip().splitlines()
result['private_rows_or_scores_read']=False
print(json.dumps(result))
'''


def main():
    result = subprocess.run(['bash', 'gpu/ovx5_ssh.sh', '/usr/bin/python3 -B -c ' + shlex.quote(REMOTE)],
        capture_output=True, text=True, timeout=30, check=True)
    document = json.loads(result.stdout)
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    path = HERE / ('PILOT_OBSERVATION_' + stamp + '.json')
    patch = '*** Begin Patch\n*** Add File: ' + str(path) + '\n'
    patch += ''.join('+' + line + '\n' for line in json.dumps(document, indent=2, sort_keys=True).splitlines()) + '*** End Patch\n'
    subprocess.run(['apply_patch'], input=patch, text=True, capture_output=True, check=True)
    print(json.dumps(dict(path=str(path), observed_utc=document['observed_utc'],
        loaded=document['receipts'].get('candidate1/LOADED.json'), progress=document.get('latest_progress'),
        complete=document['receipts'].get('candidate1/PILOT_COMPLETE.json'), exit=document['receipts'].get('OUTER_EXIT.json'))))


if __name__ == '__main__':
    main()
