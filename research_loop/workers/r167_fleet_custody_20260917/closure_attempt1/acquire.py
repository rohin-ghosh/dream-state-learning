import hashlib
import json
from pathlib import Path
import shlex
import subprocess
import time


ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[3]


def ref(path):
    return dict(path=str(path), sha256=hashlib.sha256(path.read_bytes()).hexdigest())


def write(name, value):
    with (ROOT / name).open('x') as stream:
        json.dump(value, stream, sort_keys=True, indent=2)
        stream.write('\n')


batch = REPO / 'research_loop/workers/r167_object_survival/fleet_generation1/BATCH_PLAN.json'
wanted = ['C1', 'C2', 'C3', 'C4', 'continual_run1', 'pilot', 'repo_reader']
rows = {life['life_id']: life for life in json.loads(batch.read_text())['lives']}
previous = {name: json.loads((ROOT.parent / 'train_attempt1' / (name + '.json')).read_text())['custody']
            for name in wanted}
request = dict(lives=[rows[name] for name in wanted], previous={name: {'reads': value['reads']}
                                                            for name, value in previous.items()})
write('REQUEST.json', request)
helper = ROOT / 'native_custody.py'
extension = ROOT / 'finish_metadata.py'
payload = ("__name__ = 'custody_library'\n".encode() + helper.read_bytes() + b'\n' + extension.read_bytes())
provenance = dict(started_unix=time.time(), batch=ref(batch), helper=ref(helper), extension=ref(extension),
                  payload_sha256=hashlib.sha256(payload).hexdigest(), launcher=ref(Path(__file__)),
                  timeout_seconds=180)
try:
    process = subprocess.run(['bash', str(REPO / 'gpu/ovx3_ssh.sh'),
                              'python3 -B - ' + shlex.quote(json.dumps(request))],
                             input=payload, capture_output=True, timeout=180)
    stdout, stderr, code = process.stdout, process.stderr, process.returncode
except subprocess.TimeoutExpired as error:
    stdout, stderr, code = error.stdout or b'', error.stderr or b'', 'WRAPPER_TIMEOUT'
for name, raw in [('REMOTE.jsonl', stdout), ('TRANSPORT.stderr', stderr)]:
    with (ROOT / name).open('xb') as stream:
        stream.write(raw)
provenance.update(finished_unix=time.time(), returncode=code, output=ref(ROOT / 'REMOTE.jsonl'),
                  batch_unchanged=ref(batch) == provenance['batch'])
write('ACQUISITION.json', provenance)
for line in stdout.splitlines():
    value = json.loads(line)
    write(value['life_id'] + '.json', value)
    alias = value.get('alias_custody', {})
    print(json.dumps(dict(life_id=value['life_id'], source_count=len(value.get('source_files', {})),
        source_match=value.get('all_checked_pins_match'), error=value.get('error'),
        alias_status=alias.get('status'), alias_error=alias.get('error'),
        alias_sleep=alias.get('last_completed_sleep')), sort_keys=True))
print(json.dumps(dict(returncode=code, stderr_bytes=len(stderr))))
