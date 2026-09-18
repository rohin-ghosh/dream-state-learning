import datetime
import hashlib
import json
from pathlib import Path
import subprocess


script = r'''
import datetime, hashlib, json, os
from pathlib import Path
base = Path('/localhome/local-rohing')
control = base / 'orch_r157_repo_reader_wall_20260917_attempt2'
root = base / 'orch_r136_repo_reader_20260916_attempt1/recovery_r154_saved30_20260916_attempt2/run1'
def read(path):
    return json.loads(path.read_bytes())
def ref(path):
    return dict(path=str(path), sha256=hashlib.sha256(path.read_bytes()).hexdigest())
def record(index):
    return read(root / 'stream/records' / ('%020d.json' % index))
boundary = read(control / 'BOUNDARY.json')
saved, wall, loaded = record(3646), record(3647), record(3648)
prior, after = saved['document']['resume_state'], wall['document']['state']
diff = sorted(key for key in set(prior['state']) | set(after['state']) if prior['state'].get(key) != after['state'].get(key))
assert diff == ['deadline_unix']
assert after['state']['deadline_unix'] == 1789776000
assert loaded['document']['optimizer_steps'] == boundary['saved']['optimizer_steps'] == 3168
assert loaded['document']['adapter_sha256'] == boundary['saved']['adapter_state_sha256']
events = []
for path in sorted((root / 'stream/records').glob('*.json')):
    if not path.stem.isdigit() or int(path.stem) < 3646:
        continue
    event = read(path)
    metadata = {key:event['document'][key] for key in ('pid', 'resume', 'optimizer_steps', 'total_optimizer_steps', 'cycle',
        'adapter_sha256', 'loaded_unix', 'started_unix', 'finished_unix', 'deadline_unix') if key in event['document']}
    events.append(dict(index=int(path.stem), kind=event['kind'], record_sha256=event['sha256'], file=ref(path), metadata=metadata))
processes = {}
for role, pid, ticks in [('native',2611440,'14880066'),('timer',2611439,'14880066'),
                         ('supervisor',2611436,'14880012'),('broker',2611523,'14880170')]:
    proc = Path('/proc') / str(pid)
    fields = (proc / 'stat').read_text().rsplit(')',1)[1].split()
    assert fields[19] == ticks and fields[0] != 'Z'
    processes[role] = dict(pid=pid, start_ticks=ticks, state=fields[0], parent=int(fields[1]))
    if role == 'native':
        devices = sorted(set(os.readlink(path) for path in (proc / 'fd').iterdir() if 'nvidia' in os.readlink(path)))
        assert all(name in ('/dev/nvidia7', '/dev/nvidiactl', '/dev/nvidia-uvm') for name in devices)
        processes[role]['gpu_fds'] = devices
broker = control / 'broker'
cursors = sorted(broker.glob('CURSOR_*.json'))
intents = sorted(broker.glob('INTENT_*.json'))
pending_intents = [path.name for path in intents if not (broker / path.name.replace('INTENT_', 'READ_',1)).exists()]
consumed = broker / 'CONSUMED_00000000000000003497.json'
tools = base / 'orch_r157_repo_reader_tools_20260917t0247z'
print(json.dumps(dict(observed_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(), host_root=str(root),
    control=str(control), boundary=boundary['saved'], readout_complete_metadata=boundary['readout_complete'],
    wall_only_state_check=dict(changed_keys=diff, prior_state_sha256=prior['sha256'], new_state_sha256=after['sha256'],
        exact_saved_cycle=33, exact_optimizer_steps=3168, no_reset=True, not_saved30_rollback=True),
    processes=processes, events=events, receipts={name:ref(control/name) for name in ('BOUNDARY.json','BOUNDARY_CPU.json',
        'RETIRED.json','PLAN.json','GUARD.json','LEASE_BUDGET.json','LAUNCH.json','ADMISSION.json','CONTAINMENT_VERIFIED.json')},
    receiving_cpu=dict(file=ref(tools/'CPU_GATE.json'), metadata=read(tools/'CPU_GATE.json')),
    broker=dict(started=read(broker/'STARTED.json'), sandbox=read(broker/'SANDBOX_VERIFIED.json'),
        cursor=read(cursors[-1]), pending_intents=pending_intents,
        inherited_read3497_consumed=read(consumed) if consumed.exists() else None,
        reads=[ref(path) for path in sorted(broker.glob('READ_*.json'))],
        config=ref(control/'BROKER_CONFIG.json')),
    terminal_receipts=[path.name for path in control.glob('*EXIT*')] + [path.name for path in control.glob('*FAIL*')]
), sort_keys=True))
'''
repository = Path('/data/home/rohing/dream-state-orch')
result = subprocess.run(['bash', str(repository / 'gpu/ovx3_ssh.sh'),
    '/localhome/local-rohing/v2/venv/bin/python -B -'], input=script, text=True, capture_output=True, check=True)
receipt = json.loads(result.stdout)
evidence = repository / 'research_loop/workers/r157_repo_reader_wall_20260917'
parent = evidence / 'PARENT'
started = json.loads((parent / 'STARTED.json').read_bytes())
pid = started['pid']
fields = Path('/proc/' + str(pid) + '/stat').read_text().rsplit(')',1)[1].split()
assert fields[0] != 'Z'
resumed = json.loads((parent / ('RESUMED_' + str(pid) + '.json')).read_bytes())
assert resumed['hard_end_unix'] == 1789776000
spec = json.loads((parent / 'RESUME_SPEC.json').read_bytes())
preserved = all(hashlib.sha256((Path(spec['output']) / name).read_bytes()).hexdigest() == digest
                for name,digest in spec['before']['files'].items())
assert preserved
receipt['reader_parent'] = dict(resumed=resumed, start_ticks=fields[19], live_state=fields[0],
    all_prior_files_unchanged=preserved, preserved_file_count=len(spec['before']['files']),
    previous_owner_absent=not Path('/proc/1554590').exists(),
    source_sha256=hashlib.sha256((parent/'READER_PARENT.py').read_bytes()).hexdigest(),
    config_sha256=hashlib.sha256((parent/'CONFIG.json').read_bytes()).hexdigest())
receipt['local_cpu'] = dict(reader_tests=48, parent_tests=35)
path = evidence / ('APPLIED_CONTINUITY_' + datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ') + '.json')
with path.open('x') as stream:
    json.dump(receipt, stream, indent=2, sort_keys=True)
print(json.dumps(dict(path=str(path), sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
    observed_utc=receipt['observed_utc'], latest_event=receipt['events'][-1],
    broker_cursor=receipt['broker']['cursor'], inherited_consumed=receipt['broker']['inherited_read3497_consumed'],
    new_read_receipts=len(receipt['broker']['reads']), parent=receipt['reader_parent']), sort_keys=True))
