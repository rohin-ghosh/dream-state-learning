"""Bounded operational receipts only; never reads caption rows or pair plans."""

import argparse
import json
from pathlib import Path
import shlex
import subprocess
import time

from gpu import ny_caption_data as data


def observe(version):
    data.require(version == 'v1', 'registered_widegap_candidate_only')
    work = Path(__file__).resolve().parent
    root = '/localhome/local-rohing/orch_r177_ampere_judge_20260917/bt_widegap_'+version
    code = '''import hashlib,json,time
from pathlib import Path
root=Path(ROOT)
names=['CPU_PROCESS_STARTED.json','CPU_TESTS.json','CPU_GATE.json','PROBE_PROCESS_STARTED.json',
 'CONFINEMENT_CPU_PROOF.json','TRAIN_PROCESS_STARTED.json','TRAIN_CONFINEMENT_PROOF.json',
 'ADMISSION.json','DISPATCH_STARTED.json','COMPLETED.json','EXPERIMENT_BUDGET.json',
 'training/MEASURED_BUDGET_ADMISSION.json','training/FULL_POOL_SELECTION_REPORT.json','training/TRAINING_STARTED.json','training/FIRST_OPTIMIZER_STEP.json','training/PUBLIC_SCORING_REPORT.json']
names += [path.name for path in sorted(root.glob('FAILURE_*.json'))[:8]]
for folder in ('throughput','progress'):
 paths=sorted((root/'training'/folder).glob('*.json'))
 if paths: names.append(str(paths[-1].relative_to(root)))
output=dict(observed_unix=time.time(),root=str(root),files={},processes={})
for name in names:
 path=root/name
 if not path.exists(): continue
 size=path.stat().st_size
 if size>65536:
  output['files'][name]=dict(bytes=size,oversize_not_read=True)
  continue
 raw=path.read_bytes();record=json.loads(raw)
 output['files'][name]=dict(path=str(path),bytes=size,sha256=hashlib.sha256(raw).hexdigest(),content=record)
 if name.endswith('PROCESS_STARTED.json') or name=='DISPATCH_STARTED.json':
  pid=record['pid'];stat=Path('/proc')/str(pid)/'stat'
  status=dict(pid=pid,exists=stat.exists())
  if stat.exists():
   fields=stat.read_text().split(') ')[1].split()
   status.update(state=fields[0],startticks=fields[19],identity_matches=fields[19]==record.get('startticks',record.get('process_startticks')))
  output['processes'][name]=status
print(json.dumps(output,sort_keys=True))
'''.replace('ROOT', repr(root), 1)
    command = ['bash', str(work.parents[3]/'gpu/a40r_ssh.sh'), 'python3 -B -c '+shlex.quote(code)]
    result = subprocess.run(command, capture_output=True, timeout=30, check=True)
    data.require(len(result.stdout) <= 2*1024**2, 'bounded_metadata_observation')
    record = json.loads(result.stdout)
    reference = data.private_write(work/'evidence'/('WIDEGAP_'+version.upper()+'_OBSERVATION_'+str(time.time_ns())+'.json'), record)
    safe = {}
    for name, item in record['files'].items():
        content = item.get('content', {})
        safe[name] = dict(sha256=item.get('sha256'), bytes=item['bytes'],
            content={key: value for key, value in content.items() if key not in ('source_sha256', 'admission', 'properties', 'command', 'config')})
    print(json.dumps(dict(receipt=reference, observed_unix=record['observed_unix'], files=safe, processes=record['processes']), sort_keys=True))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--version', choices=('v1', 'v2'), required=True)
    observe(parser.parse_args().version)
