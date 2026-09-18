import hashlib
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import time

BASE = Path('/localhome/local-rohing')
AUTHORITY = BASE / 'orch_r166_retelling_operator_20260917_activation5/EVENT_CONDITIONAL_AUTHORITY.json'
SOURCE_PINS = {
    'gpu/orch_r166_retelling_handoff.py': '655e72c553c934538b47e12987ffb9d493505f668721e0c432275b4617233681',
    'tests/test_orch_r166_retelling_handoff.py': 'a6ae913da890680b387d5b3568bea97667988777b8254493909c80316b9b5660',
    'gpu/orch_r166_corrected_retelling.py': '9277b09ca3f312bd7afa8bbcfc94f883940652c4199fe686c2ed47d73a992bcc',
    'tests/test_orch_r166_corrected_retelling.py': 'b6f4ef8a65c09fa93b9b9fa705fd73f6f0ee589375eafa75024aa1f91f88132e',
    'gpu/orch_r157_community_wall_extension.py': '7e0fcf8c35b72fc6fa01738446d51d8fe9e996afefae66236dd2d5c47d6a2419',
}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(path, value):
    with path.open('x') as stream:
        stream.write(json.dumps(value, sort_keys=True, indent=2, allow_nan=False) + '\n')
        stream.flush()
        os.fsync(stream.fileno())
        os.fchmod(stream.fileno(), 0o444)


assert socket.gethostname().split('.')[0] == '[REDACTED_HOST]'
assert len(sys.argv) == 3
authority_sha, event_text = sys.argv[1:]
assert sha(AUTHORITY) == authority_sha
authority = json.loads(AUTHORITY.read_text())
event = json.loads(event_text)
agent = event['agent']
assert agent in authority['ready_sha256']
assert event['status'] == authority['event_status']
assert event['deadline_unix'] == authority['event_deadline_unix']
assert 0 <= time.time() - event['observed_unix'] <= authority['event_max_age_seconds']
assert time.time() < authority['event_deadline_unix']
root = BASE / ('orch_r166_retelling_' + agent + '_20260917_activation5')
source = root / 'source'
assert sha(root / 'readiness/READY.json') == authority['ready_sha256'][agent] == event['ready_sha256']
for relative, expected in SOURCE_PINS.items():
    assert sha(source / relative) == expected, relative
for name in ('MAIN_GO.json', 'MAIN_EVENT_DISPATCH_ONCE', 'MAIN_DISPATCH_INTENT.json', 'MAIN_DISPATCH.json', 'MAIN_EXECUTE.log', 'ACTIVATE_ONCE'):
    assert not (root / name).exists(), 'no_retry_' + name
os.environ['CUDA_VISIBLE_DEVICES'] = ''
os.environ['PYTHONDONTWRITEBYTECODE'] = '1'
sys.path.insert(0, str(source))
from gpu import orch_r166_retelling_handoff as handoff

ready = handoff.saved.read(root / 'readiness/READY.json')
binding = ready['required_GO_binding']
assert binding == event['required_GO_binding']
assert binding['max_wait_seconds'] == binding['max_pause_seconds'] == 600
assert binding['hard_end_unix'] == authority['hard_end_unix']
request, config, plan = handoff.verify_request(root)
assert handoff.saved.reference(root / 'REQUEST.json') == binding['request']
assert handoff.saved.digest(request['pair']) == binding['pair_sha256']
assert handoff.saved.digest(request['source_files']) == binding['source_manifest_sha256']
handoff.saved.bound(binding['plan'])
handoff.saved.bound(binding['cpu_proof'])
for process in request['pair'].values():
    handoff.saved.same(process)
    fields = Path('/proc', str(process['pid']), 'stat').read_text().rsplit(')', 1)[1].split()
    assert fields[0] not in ('T', 't', 'Z', 'X')
boundary = handoff.saved.saved_boundary(plan['root'])
assert boundary and boundary['reference'] == event['boundary']
assert boundary['index'] >= binding['earliest_boundary_index']
metadata = handoff.saved.readout(plan['root'], config, plan, boundary, request['pair']['actor'])
assert metadata and metadata['request'] == event['readout']['request']
assert metadata['identity'] == event['readout']['identity']
assert handoff.saved.saved_boundary(plan['root']) == boundary
assert time.time() < authority['event_deadline_unix']
assert 0 <= time.time() - event['observed_unix'] <= authority['event_max_age_seconds']
(root / 'MAIN_EVENT_DISPATCH_ONCE').mkdir()
trigger = dict(authority=dict(path=str(AUTHORITY), sha256=authority_sha), event=event,
    reverified_unix=time.time(), boundary=boundary['reference'], readout=metadata,
    no_pause_before_execute=True, no_retry=True)
write(root / 'MAIN_EVENT_TRIGGER.json', trigger)
now = time.time()
go = dict(schema='R166_SAVED_BOUNDARY_MAIN_GO_V1', issuer='Main', decision='GO', binding=binding,
    not_before_unix=now, expires_unix=min(now + 1800, binding['hard_end_unix']))
handoff.validate_go(go, binding, now)
go_path = root / 'MAIN_GO.json'
write(go_path, go)
command = [str(handoff.saved.PYTHON), '-B', '-m', handoff.MODULE, 'execute', '--output', str(root),
    '--main-go', str(go_path), '--main-go-sha256', sha(go_path)]
intent = dict(agent=agent, command=command, ready_sha256=authority['ready_sha256'][agent],
    go_sha256=sha(go_path), go=go, authority_sha256=authority_sha, trigger_sha256=sha(root / 'MAIN_EVENT_TRIGGER.json'),
    observed_unix=time.time(), no_retry=True)
write(root / 'MAIN_DISPATCH_INTENT.json', intent)
print(json.dumps(dict(intent, status='GO_AND_INTENT_DURABLE_BEFORE_SINGLE_DISPATCH')), flush=True)
assert time.time() < authority['event_deadline_unix']
assert handoff.saved.saved_boundary(plan['root']) == boundary, 'window_closed_no_dispatch_no_retry'
environment = handoff.saved.environment(source)
assert environment['CUDA_VISIBLE_DEVICES'] == ''
with (root / 'MAIN_EXECUTE.log').open('x') as log:
    process = subprocess.Popen(command, cwd=source, env=environment, stdin=subprocess.DEVNULL,
        stdout=log, stderr=subprocess.STDOUT, start_new_session=True, close_fds=True)
ticks = Path('/proc', str(process.pid), 'stat').read_text().rsplit(')', 1)[1].split()[19]
receipt = dict(intent, pid=process.pid, start_ticks=ticks, observed_unix=time.time(),
    status='CPU_OPERATOR_DISPATCHED_NOT_NATIVE_LOADED')
write(root / 'MAIN_DISPATCH.json', receipt)
print(json.dumps(receipt), flush=True)
