import hashlib
import json
from pathlib import Path
import subprocess
import time


base = Path('research_loop/workers/r157_keepalive_20260917')
source = base / 'ALL_EIGHT_APPLIED.json'
record = json.loads(source.read_text())
remote = 'import hashlib,json,time\nfrom pathlib import Path\nexpected=' + repr(record['learners']) + '''
result={"observed_unix":time.time(),"learners":{}}
for name,item in expected.items():
    observed={"pid":item["pid"],"root":item["host_root"]}
    try:
        process=Path("/proc")/str(item["pid"])
        fields=process.joinpath("stat").read_text().rsplit(") ",1)[1].split()
        assert fields[19]==item["ticks"] and fields[0] not in ("Z","X")
        config=json.loads(Path(item["config"]).read_text())
        for key,hash_key in (("lease_path","lease_sha256"),("plan_path","plan_sha256")):
            path=Path(config[key])
            assert hashlib.sha256(path.read_bytes()).hexdigest()==config[hash_key]
            assert json.loads(path.read_text())["hard_end_unix"]==1789776000
        assert config["hard_end_unix"]==1789776000
        paths=sorted(path for path in (Path(item["host_root"])/"stream/records").glob("*.json") if len(path.stem)==20 and path.stem.isdecimal())
        latest=json.loads(paths[-1].read_text())
        observed.update(status="LIVE_VERIFIED",hard_end_unix=1789776000,state=fields[0],latest_index=latest["index"],latest_kind=latest["kind"],latest_mtime=paths[-1].stat().st_mtime,previous_index=item["latest"]["index"])
    except Exception as error:
        observed.update(status="REQUIRES_INSPECTION",error=type(error).__name__+": "+str(error))
    result["learners"][name]=observed
print(json.dumps(result,sort_keys=True))
'''
response = subprocess.run(
    ['bash', 'gpu/ovx3_ssh.sh', "python3 - <<'VERIFY_APPLIED'\n" + remote + '\nVERIFY_APPLIED'],
    check=True, capture_output=True, text=True, timeout=60,
)
report = json.loads(response.stdout)
report['local_sidecars'] = {}
for name, item in record['local_sidecars'].items():
    observed = {'pid': item['pid']}
    try:
        process = Path('/proc') / str(item['pid'])
        fields = process.joinpath('stat').read_text().rsplit(') ', 1)[1].split()
        assert fields[19] == item['start_ticks'] and fields[0] not in ('Z', 'X')
        path = Path(item['config']['path'])
        assert hashlib.sha256(path.read_bytes()).hexdigest() == item['config']['sha256']
        config = json.loads(path.read_text())
        deadline = config.get('hard_end_unix', config.get('deadline_unix'))
        assert deadline == 1789776000
        observed.update(status='LIVE_VERIFIED', hard_end_unix=deadline)
    except Exception as error:
        observed.update(status='REQUIRES_INSPECTION', error=type(error).__name__ + ': ' + str(error))
    report['local_sidecars'][name] = observed
report.update(schema='R157_POST_EXTENSION_LIVENESS_V1', source=str(source), source_sha256=hashlib.sha256(source.read_bytes()).hexdigest())
output = base / ('POST_EXTENSION_' + time.strftime('%Y%m%dT%H%M%SZ', time.gmtime()) + '.json')
with output.open('x') as stream:
    json.dump(report, stream, indent=2, sort_keys=True)
    stream.write('\n')
print(json.dumps(report, indent=2, sort_keys=True))
print(output, hashlib.sha256(output.read_bytes()).hexdigest())
