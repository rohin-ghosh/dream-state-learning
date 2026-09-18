"""Read bounded process/config metadata without changing running lives."""

import hashlib
import json
from pathlib import Path
import subprocess
import time


root = Path(__file__).resolve().parent
source = root / 'ALL_EIGHT_APPLIED.json'
previous = json.loads(source.read_text())
remote = '''import hashlib,json,time
from pathlib import Path
def load(path):
    path=Path(path)
    if path.is_symlink() or path.stat().st_size>1048576:
        raise ValueError('bounded_regular_metadata_required')
    raw=path.read_bytes()
    return json.loads(raw),hashlib.sha256(raw).hexdigest()
report={'observed_unix':time.time(),'learners':{}}
for name,item in expected.items():
    try:
        process=Path('/proc')/str(item['pid'])
        fields=process.joinpath('stat').read_text().rsplit(') ',1)[1].split()
        if fields[19]!=item['ticks'] or fields[0] in ('Z','X'):
            raise ValueError('process_identity_or_liveness_mismatch')
        argv=process.joinpath('cmdline').read_bytes().rstrip(bytes([0])).decode().split(chr(0))
        if argv[-3:]!=['native','--config',item['config']]:
            raise ValueError('native_binding_mismatch')
        config,unused=load(item['config'])
        plan,plan_sha=load(config['plan_path'])
        budget,budget_sha=load(config['lease_path'])
        if plan_sha!=config['plan_sha256'] or budget_sha!=config['lease_sha256']:
            raise ValueError('plan_or_budget_hash_mismatch')
        if not config['hard_end_unix']==plan['hard_end_unix']==budget['hard_end_unix']==1789776000:
            raise ValueError('deadline_mismatch')
        paths=[path for path in (Path(item['host_root'])/'stream/records').glob('*.json')
               if len(path.stem)==20 and path.stem.isdecimal()]
        latest=max(paths)
        if latest.is_symlink():
            raise ValueError('journal_record_symlink')
        record={'index':int(latest.stem),'kind':None}
        if latest.stat().st_size<=1048576:
            record,unused=load(latest)
        report['learners'][name]={'status':'LIVE_VERIFIED','pid':item['pid'],
            'state':fields[0],'hard_end_unix':plan['hard_end_unix'],
            'latest_index':record['index'],'latest_kind':record['kind'],
            'latest_content_read':record['kind'] is not None,
            'latest_mtime':latest.stat().st_mtime}
    except (OSError,ValueError,KeyError) as error:
        report['learners'][name]={'status':'UNVERIFIED','error':str(error),'pid':item['pid']}
print(json.dumps(report,sort_keys=True))
'''
expected = {name: {key: value[key] for key in ('pid', 'ticks', 'config', 'host_root')}
            for name, value in previous['learners'].items()}
command = "python3 - <<'R157_RECHECK'\nexpected=" + repr(expected) + '\n' + remote + '\nR157_RECHECK'
result = subprocess.run(['bash', 'gpu/ovx3_ssh.sh', command], capture_output=True,
                        text=True, timeout=60, check=True)
report = json.loads(result.stdout)
report['local_sidecars'] = {}
for name, item in previous['local_sidecars'].items():
    try:
        process = Path('/proc') / str(item['pid'])
        fields = process.joinpath('stat').read_text().rsplit(') ', 1)[1].split()
        if fields[19] != item['start_ticks'] or fields[0] in ('Z', 'X'):
            raise ValueError('process_identity_or_liveness_mismatch')
        config_path = Path(item['config']['path'])
        if config_path.is_symlink() or config_path.stat().st_size > 1048576:
            raise ValueError('bounded_regular_metadata_required')
        raw = config_path.read_bytes()
        if hashlib.sha256(raw).hexdigest() != item['config']['sha256']:
            raise ValueError('sidecar_config_hash_mismatch')
        config = json.loads(raw)
        deadline = config.get('hard_end_unix', config.get('deadline_unix'))
        argv = process.joinpath('cmdline').read_bytes().rstrip(b'\0').decode().split('\0')
        if deadline != 1789776000 or str(config_path) not in argv:
            raise ValueError('sidecar_deadline_or_binding_mismatch')
        report['local_sidecars'][name] = dict(status='LIVE_VERIFIED', pid=item['pid'], hard_end_unix=deadline)
    except (OSError, ValueError, KeyError) as error:
        report['local_sidecars'][name] = dict(status='UNVERIFIED', pid=item['pid'], error=str(error))
report.update(schema='R157_POST_EXTENSION_LIVENESS_V2', source=str(source),
              source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
              script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
output = root / ('POST_EXTENSION_' + time.strftime('%Y%m%dT%H%M%SZ', time.gmtime()) + '.json')
with output.open('x') as stream:
    json.dump(report, stream, sort_keys=True, indent=2)
    stream.write('\n')
print(output)
print(hashlib.sha256(output.read_bytes()).hexdigest())
print(json.dumps({group: {name: entry['status'] for name, entry in report[group].items()}
                  for group in ('learners', 'local_sidecars')}, sort_keys=True))
