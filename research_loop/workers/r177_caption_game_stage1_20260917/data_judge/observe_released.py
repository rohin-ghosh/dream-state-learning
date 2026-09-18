"""Bounded safe operational receipt retrieval through the sanctioned wrapper."""

import argparse
import json
from pathlib import Path
import shlex
import subprocess
import time

from gpu import ny_caption_data as data


def observe(version):
    data.require(version in (1, 2, 3, 4, 5, 6, 7, 8, 9, 10), 'existing_owned_attempt_only')
    remote = f'/localhome/local-rohing/orch_r177_ampere_judge_20260917/released_all_v{version}'
    code = '''import hashlib,json,os,time
from pathlib import Path
root=Path(ROOT)
names=['CPU_PROCESS_STARTED.json','CPU_TESTS.json','CPU_GATE.json','CPU_FAILURE.json','CONFINEMENT_CPU_PROOF.json',
 'TRAIN_CONFINEMENT_PROOF.json','ADMISSION.json','DISPATCH_STARTED.json',
 'training/TRAINING_STARTED.json','training/FIRST_OPTIMIZER_STEP.json','training/FAILED.json',
 'training/PUBLIC_SCORING_REPORT.json','COMPLETED.json']
progress=sorted((root/'training/progress').glob('*.json'))
if progress: names.append(str(progress[-1].relative_to(root)))
receipts={}
for name in names:
 path=root/name
 if not path.is_file(): continue
 assert path.stat().st_size<=65536
 raw=path.read_bytes()
 receipts[name]=dict(path=str(path),sha256=hashlib.sha256(raw).hexdigest(),body=json.loads(raw))
dispatch=receipts.get('DISPATCH_STARTED.json',{}).get('body',{})
process={}
if dispatch:
 pid=dispatch['pid']; path=Path('/proc')/str(pid)
 try:
  fields=(path/'stat').read_text().split(') ')[1].split()
  process=dict(pid=pid,state=fields[0],startticks=fields[19],identity_matches=fields[19]==dispatch['process_startticks'])
  descriptors=[]
  for item in (path/'fd').iterdir():
   try:
    target=os.readlink(item)
    if target.startswith('/dev/nvidia'): descriptors.append(target)
   except FileNotFoundError: pass
  process['GPU_descriptors']=sorted(set(descriptors))
 except FileNotFoundError: process=dict(pid=pid,live=False)
print(json.dumps(dict(remote_root=str(root),observed_unix=time.time(),receipts=receipts,process=process)))
'''.replace('ROOT', repr(remote), 1)
    command = 'python3 -B -c '+shlex.quote(code)
    repo = Path(__file__).resolve().parents[4]
    result = subprocess.run(['bash', str(repo/'gpu/a40r_ssh.sh'), command], capture_output=True,
        timeout=30, check=True)
    data.require(len(result.stdout) <= 512*1024, 'bounded_operational_receipts_only')
    observation = json.loads(result.stdout)
    root = Path(__file__).resolve().parent
    reference = data.private_write(root/'evidence'/f'RECEIVING_V{version}_OBSERVATION_{time.time_ns()}.json', observation)
    print(json.dumps(dict(observation=reference, remote_root=remote, process=observation['process'],
        receipt_names=list(observation['receipts']), latest_progress=next((row['body'] for name,row in observation['receipts'].items()
            if name.startswith('training/progress/')), None),
        first_optimizer=observation['receipts'].get('training/FIRST_OPTIMIZER_STEP.json'),
        training_started=observation['receipts'].get('training/TRAINING_STARTED.json'),
        completed=observation['receipts'].get('COMPLETED.json'))))
    return observation


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--version', type=int, required=True)
    arguments = parser.parse_args()
    observe(arguments.version)
