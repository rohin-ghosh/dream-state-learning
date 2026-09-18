"""Read-only bounded device census with no infrastructure address publication."""

import json
from pathlib import Path
import subprocess


REMOTE = '''import csv,hashlib,io,json,pathlib,subprocess,time
raw=subprocess.check_output(['nvidia-smi','--query-gpu=index,uuid,name,memory.total,memory.used,utilization.gpu','--format=csv,noheader,nounits'],text=True)
apps=subprocess.check_output(['nvidia-smi','--query-compute-apps=gpu_uuid,pid','--format=csv,noheader,nounits'],text=True)
owners={}
for row in csv.reader(io.StringIO(apps)):
    if len(row)!=2: continue
    gpu,pid=row[0].strip(),int(row[1].strip())
    stat=pathlib.Path('/proc')/str(pid)/'stat'
    value=stat.read_text() if stat.exists() else None
    owners.setdefault(gpu,[]).append(dict(pid=pid,proc_present=value is not None,
        start_ticks=value.rsplit(')',1)[1].split()[19] if value else None))
rows=[]
for row in csv.reader(io.StringIO(raw)):
    fields=[item.strip() for item in row]
    physical=int(fields[0]);processes=owners.get(fields[1],[])
    rows.append(dict(physical=physical,model=fields[2],memory_total_mib=int(fields[3]),
        memory_used_mib=int(fields[4]),gpu_utilization_percent=int(fields[5]),processes=processes,
        protected_by_allocation=physical in range(6),
        empty_at_observation=not processes and int(fields[4])<100))
print(json.dumps(dict(schema='R233_READ_ONLY_CAPACITY_CENSUS_V1',unix=time.time(),
    rows=rows,source_output_sha256=hashlib.sha256((raw+apps).encode()).hexdigest(),
    allocation_candidate_devices=[6,7],dispatch_performed=False,signals=[])))
'''


def main():
    result = subprocess.run(['bash', 'gpu/ovx4_ssh.sh', 'python3 -B -'],
        input=REMOTE, text=True, capture_output=True, timeout=30)
    if result.returncode:
        raise RuntimeError('read_only_capacity_query_failed')
    receipt = json.loads(result.stdout)
    path = Path(__file__).resolve().parent / 'CAPACITY_OBSERVATION.json'
    path.write_text(json.dumps(receipt, indent=2) + '\n')
    print(json.dumps(receipt))


if __name__ == '__main__':
    main()
