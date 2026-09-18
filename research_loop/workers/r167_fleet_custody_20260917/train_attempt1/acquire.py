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
source = ROOT / 'native_custody.py'
upstream = REPO / 'research_loop/workers/r167_legacy_custody_20260917/native_custody.py'
wanted = ['C1', 'C2', 'C3', 'C4', 'continual_run1', 'pilot', 'repo_reader']
rows = {life['life_id']: life for life in json.loads(batch.read_text())['lives']}
for name in wanted:
    previous = json.loads((ROOT.parent / 'followup1' / (name + '.json')).read_text())
    rows[name]['prior_metadata_bytes'] = previous['cumulative_metadata_bytes']
request = dict(node='ovx3', lives=[rows[name] for name in wanted],
               helper_sha256=ref(source)['sha256'], batch_sha256=ref(batch)['sha256'])
write('REQUEST.json', request)
provenance = dict(started_unix=time.time(), batch=ref(batch), helper=ref(source), upstream=ref(upstream),
                  tests=ref(ROOT / 'test_native_custody.py'), launcher=ref(Path(__file__)),
                  timeout_seconds=180, TRAIN_bytes_cap_per_life=64 * 1024 ** 2,
                  TRAIN_file_bytes_cap=32 * 1024 ** 2, metadata_cap_per_life=32 * 1024 ** 2)
try:
    process = subprocess.run(['bash', str(REPO / 'gpu/ovx3_ssh.sh'),
                              'python3 -B - ' + shlex.quote(json.dumps(request))],
                             input=source.read_bytes(), capture_output=True, timeout=180)
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
    receipt = json.loads(line)
    value = receipt['custody']
    write(value['life_id'] + '.json', receipt)
    print(json.dumps({key: value.get(key) for key in ['life_id', 'status', 'last_completed_sleep',
        'registry_plan_birth_context_matches', 'queue_birth_binding_ready', 'reads', 'error']}, sort_keys=True))
print(json.dumps(dict(returncode=code, stderr_bytes=len(stderr))))
