import hashlib
import json
from pathlib import Path
import shlex
import subprocess
import time


ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[3]
BANACH = REPO / 'research_loop/workers/r166_retelling_handoff_20260917'


def read(path):
    return json.loads(path.read_text())


def ref(path):
    return dict(path=str(path), sha256=hashlib.sha256(path.read_bytes()).hexdigest())


def pair(value):
    return {key: value[key] for key in ['path', 'sha256']}


def write(name, value):
    with (ROOT / name).open('x') as stream:
        json.dump(value, stream, indent=2, sort_keys=True)
        stream.write('\n')


batch_path = REPO / 'research_loop/workers/r167_object_survival/fleet_generation1/BATCH_PLAN.json'
life = next(row for row in read(batch_path)['lives'] if row['life_id'] == 'C5')
historical_identity = dict(life['inventory_identity'])
continuity = read(BANACH / 'C5_RECOVERY2_CONTINUITY.json')
preflight = read(BANACH / 'C5_RECOVERY2_PREFLIGHT.json')
go = read(BANACH / 'C5_RECOVERY2_MAIN_GO.json')
post_loaded = read(BANACH / 'C5_RECOVERY2_POST_LOADED_METADATA.json')
retelling = read(BANACH / 'C5_RECOVERY2_RETELLING_RESPONSE_STATUS.json')
exposure = json.loads((BANACH / 'C5_RECOVERY2_EXPOSURE_OBSERVATION.jsonl').read_text().splitlines()[-1])
life['inventory_identity'] = {key: continuity['native'][key] for key in ['pid', 'start_ticks']}
metadata_refs = dict(config=pair(continuity['config']), plan=pair(continuity['plan']),
    go=dict(path=go['go_path'], sha256=go['go_sha256']), request=pair(preflight['request']),
    ready=pair(preflight['ready']), custody=pair(go['go']['binding']['recovery_custody']),
    retirement=pair(continuity['files']['RECOVERY_EXECUTION.json']['content']['prior_retirement']),
    proof=pair(continuity['files']['control/SAVED_PROOF.json']), saved_commit=pair(post_loaded['checkpoint']),
    policy=pair(continuity['files']['control/EFFECTIVE_POLICY.json']),
    launch=pair(continuity['files']['attempt/LAUNCH.json']),
    prepared=pair(continuity['files']['control/PREPARED.json']), execution=pair(continuity['files']['RECOVERY_EXECUTION.json']))
record_refs = {'2899': pair(go['go']['binding']['boundary']), '2900': pair(continuity['loaded']),
               '2907': pair(exposure['invocation']['record']), '2908': pair(exposure['exposure']['request']),
               '2909': pair(retelling['response']), '2910': pair(retelling['committed'])}
for triple in exposure['committed_own_segments']:
    for key in ['request', 'response', 'committed']:
        record_refs[str(triple[key + '_index'])] = pair(triple[key])
request = dict(life=life, historical_registry_identity=historical_identity,
    expected_runtime_source=continuity['native']['cwd'], metadata_refs=metadata_refs, record_refs=record_refs)
write('REQUEST.json', request)
helpers = [ROOT / name for name in ['native_custody.py', 'source_metadata.py', 'recovery_metadata.py']]
payload = b"__name__ = 'custody_library'\n" + helpers[0].read_bytes() + b'\n' + helpers[1].read_bytes()
payload += b"\n__name__ = 'c5_collector'\n" + helpers[2].read_bytes()
provenance = dict(started_unix=time.time(), registry=ref(batch_path), helpers=[ref(path) for path in helpers],
    payload_sha256=hashlib.sha256(payload).hexdigest(), launcher=ref(Path(__file__)),
    upstream=[ref(BANACH / name) for name in ['C5_RECOVERY2_CONTINUITY.json', 'C5_RECOVERY2_PREFLIGHT.json',
        'C5_RECOVERY2_MAIN_GO.json', 'C5_RECOVERY2_POST_LOADED_METADATA.json',
        'C5_RECOVERY2_RETELLING_RESPONSE_STATUS.json', 'C5_RECOVERY2_EXPOSURE_OBSERVATION.jsonl']],
    CPU=ref(ROOT / 'CPU.log'), timeout_seconds=180)
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
                  registry_unchanged=ref(batch_path) == provenance['registry'])
write('ACQUISITION.json', provenance)
for line in stdout.splitlines():
    record = json.loads(line)
    write(record['kind'].upper() + '.json', record['document'])
    value = record['document']
    print(json.dumps(dict(kind=record['kind'], status=value['status'], native_identity=value.get('native_identity'),
        last_completed_sleep=value.get('last_completed_sleep'), birth_matches=value.get('registry_plan_birth_context_matches'),
        source_files=len(value.get('source_files', {})), source_matches=value.get('all_checked_pins_match'),
        error=value.get('error'), reads=value.get('reads')), sort_keys=True))
print('transport_returncode', code)
