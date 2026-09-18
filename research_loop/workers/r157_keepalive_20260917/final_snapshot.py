"""Verify applied identities and deadline bindings without reading evaluations."""

import hashlib
import json
from pathlib import Path
import subprocess


base = Path('research_loop/workers')
inputs = {
    'community': base / 'r157_community_wall_20260917/ALL_FIVE_APPLIED.json',
    'reader': base / 'r157_repo_reader_wall_20260917/APPLIED_CONTINUITY_20260917T025542Z.json',
    'run1': base / 'r157_keepalive_20260917/RUN1_APPLIED.json',
    'pilot': base / 'r157_keepalive_20260917/PILOT_APPLIED.json',
    'sidecars': base / 'r157_protected_parent_keepalive_20260917/ALL_OWNED_SIDECARS.json',
}
data = {name: json.loads(path.read_text()) for name, path in inputs.items()}
expected = {}
for name, life in data['community']['lives'].items():
    expected[name] = dict(pid=life['native_pid'], ticks=life['native_start_ticks'],
                         config=life['guard_path'], host_root=life['original_root'])
for name in ('run1', 'pilot'):
    life = data[name]
    expected[name] = dict(pid=life['pid'], ticks=life['start_ticks'],
                         config=life['control'] + '/GUARD.json', host_root=life['root'])
reader = data['reader']
identity = reader['processes']['native']
expected['repo_reader'] = dict(pid=identity['pid'], ticks=identity['start_ticks'],
    config=reader['control'] + '/GUARD.json', host_root=reader['host_root'])

remote = 'import hashlib,json,time\nfrom pathlib import Path\nexpected=' + repr(expected) + r'''
report={"observed_unix":time.time(),"learners":{}}
for name,item in expected.items():
    process=Path('/proc')/str(item['pid']); fields=process.joinpath('stat').read_text().rsplit(') ',1)[1].split()
    assert fields[19]==item['ticks'] and fields[0] not in ('Z','X')
    argv=process.joinpath('cmdline').read_bytes().rstrip(bytes([0])).decode().split(chr(0))
    assert argv[-3:]==['native','--config',item['config']]
    config=json.loads(Path(item['config']).read_text());plan_path=Path(config['plan_path'])
    assert hashlib.sha256(plan_path.read_bytes()).hexdigest()==config['plan_sha256']
    plan=json.loads(plan_path.read_text());budget_path=Path(config['lease_path']);budget=json.loads(budget_path.read_text())
    assert config['hard_end_unix']==plan['hard_end_unix']==budget['hard_end_unix']==1789776000
    assert hashlib.sha256(budget_path.read_bytes()).hexdigest()==config['lease_sha256']
    paths=sorted(path for path in (Path(item['host_root'])/'stream/records').glob('*.json') if len(path.stem)==20 and path.stem.isdecimal())
    latest=json.loads(paths[-1].read_text())
    report['learners'][name]=dict(item,state=fields[0],hard_end_unix=plan['hard_end_unix'],physical=plan['physical'],lease_budget_path=str(budget_path),lease_budget_sha256=config['lease_sha256'],latest={'index':latest['index'],'kind':latest['kind'],'mtime':paths[-1].stat().st_mtime})
print(json.dumps(report,sort_keys=True))
'''
result = subprocess.run(['bash', 'gpu/ovx3_ssh.sh', "python3 - <<'R157_VERIFY'\n" + remote + '\nR157_VERIFY'],
                        text=True, capture_output=True, timeout=45, check=True)
report = json.loads(result.stdout)
report['local_sidecars'] = {}
owners = dict(data['sidecars']['owners'])
parent = reader['reader_parent']
owners['repo_reader_parent'] = dict(pid=parent['resumed']['pid'], start_ticks=parent['start_ticks'],
    config=dict(path=str((base / 'r157_repo_reader_wall_20260917/PARENT/CONFIG.json').resolve()), sha256=parent['config_sha256']))
for name, owner in owners.items():
    process = Path('/proc') / str(owner['pid'])
    fields = process.joinpath('stat').read_text().rsplit(') ', 1)[1].split()
    assert fields[19] == owner['start_ticks'] and fields[0] not in ('Z', 'X')
    config_path = Path(owner['config']['path'])
    assert hashlib.sha256(config_path.read_bytes()).hexdigest() == owner['config']['sha256']
    config = json.loads(config_path.read_text())
    deadline = config.get('hard_end_unix', config.get('deadline_unix'))
    assert deadline == 1789776000
    argv = process.joinpath('cmdline').read_bytes().rstrip(b'\0').decode().split('\0')
    assert str(config_path) in argv
    report['local_sidecars'][name] = dict(pid=owner['pid'], start_ticks=fields[19], state=fields[0],
                                         hard_end_unix=deadline, config=owner['config'])
report.update(schema='R157_ALL_EIGHT_APPLIED_AND_LIVE_V1', decision='A', reset=False, relocation=False,
    provider_booking_claim=False, inputs={name: dict(path=str(path), sha256=hashlib.sha256(path.read_bytes()).hexdigest())
                                         for name, path in inputs.items()})
output = base / 'r157_keepalive_20260917/ALL_EIGHT_APPLIED.json'
with output.open('x') as stream:
    json.dump(report, stream, sort_keys=True, indent=2)
    stream.write('\n')
print(output, hashlib.sha256(output.read_bytes()).hexdigest())
print('Verified', len(report['learners']), 'learners;', len(report['local_sidecars']), 'local sidecars')
