import hashlib
import json
from pathlib import Path
import shlex
import subprocess
import time


ROOT = Path(__file__).resolve().parent
BASE = ROOT.parent
REPO = ROOT.parents[3]


def read(path):
    return json.loads(path.read_text())


def ref(path):
    return dict(path=str(path), sha256=hashlib.sha256(path.read_bytes()).hexdigest())


def write(name, value):
    with (ROOT / name).open('x') as stream:
        json.dump(value, stream, sort_keys=True, indent=2)
        stream.write('\n')


batch = REPO / 'research_loop/workers/r167_object_survival/fleet_generation1/BATCH_PLAN.json'
row = next(life for life in read(batch)['lives'] if life['life_id'] == 'C2')
original_identity = dict(row['inventory_identity'])
row['inventory_identity'] = dict(pid=4077813, start_ticks='17169605', boot_id=None)
previous = read(BASE / 'train_attempt1/C2.json')['custody']['reads']
previous['metadata_bytes'] = read(BASE / 'closure_attempt1/C2.json')['cumulative_metadata_bytes']
owner_check = []
for life in read(BASE / 'INDEX.json')['lives']:
    if 'native_identity' in life:
        expected = dict(life['native_identity'])
        if life['life_id'] == 'C2':
            expected.update(pid=4077813, start_ticks='17169605')
        owner_check.append(dict(life_id=life['life_id'], native_identity=expected))
banach_path = REPO / 'research_loop/workers/r166_retelling_handoff_20260917/ACTIVATION4_OBSERVATION.jsonl'
latest = {}
for line in banach_path.read_text().splitlines():
    item = json.loads(line)
    latest[item['agent']] = item
projection = []
for name, item in latest.items():
    loaded = item.get('loaded')
    projection.append(dict(life_id=name, observed_unix=item['observed_unix'],
        loaded=None if not loaded else dict(index=loaded['index'], record=loaded['record'],
            native={key: loaded['native'].get(key) for key in ['pid', 'start_ticks', 'cwd']},
            metadata={key: loaded['document'].get(key) for key in ['loaded_unix', 'optimizer_steps', 'resume']})))
write('BANACH_METADATA_PROJECTION.json', dict(source=ref(banach_path), branches=projection,
    nested_anchor_inventory_omitted=True))
request = dict(lives=[row], previous={'C2': {'reads': previous}}, owner_check=owner_check,
               superseded_inventory_identity=original_identity, registry_unchanged=True)
write('REQUEST.json', request)
helper, extension = ROOT / 'native_custody.py', ROOT / 'finish_metadata.py'
payload = b"__name__ = 'custody_library'\n" + helper.read_bytes() + b'\n' + extension.read_bytes()
started = time.time()
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
write('ACQUISITION.json', dict(started_unix=started, finished_unix=time.time(), returncode=code,
    batch=ref(batch), helper=ref(helper), extension=ref(extension), launcher=ref(Path(__file__)),
    payload_sha256=hashlib.sha256(payload).hexdigest(), output=ref(ROOT / 'REMOTE.jsonl')))
for line in stdout.splitlines():
    value = json.loads(line)
    if 'owner_identity_check' in value:
        write('OWNER_IDENTITIES.json', value)
        for owner in value['owner_identity_check']:
            print(owner['life_id'], 'same_owner', owner['same_identity'])
    else:
        write('C2.json', value)
        custody = value['refreshed_custody']
        print(json.dumps(dict(life_id='C2', status=custody['status'],
            last_completed_sleep=custody.get('last_completed_sleep'), error=custody.get('error'),
            source_count=len(value.get('source_files', {})), source_matches=value.get('all_checked_pins_match'),
            cumulative_reads=custody['reads']), sort_keys=True))
