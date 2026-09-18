import base64
import hashlib
import json
from pathlib import Path
import shlex
import subprocess


directory = Path(__file__).resolve().parent
worker = directory.parent
repository = worker.parents[2]
root = '/localhome/local-rohing/orch_r159_matched_evaluation_20260917_attempt1'
summary = json.loads((directory/'COPY_SUMMARY.json').read_text())
authority_path = worker/'MAIN_SLEEP6_SOURCE_COPY_AUTHORITY_20260917.json'
authority_raw = authority_path.read_bytes()
assert hashlib.sha256(authority_raw).hexdigest() == 'c55f64ad16f62e76fe7e4d584e85692e841d29a0ea541fdbbf85178cee9f3cd3'
archive = directory/'SLEEP6.private.tar'
with archive.open('rb') as stream:
    assert hashlib.file_digest(stream,'sha256').hexdigest() == summary['archive_sha256']
assert archive.stat().st_size == summary['archive_bytes'] and archive.stat().st_size*2 <= 1073741824
transfer = '''
import hashlib, os, socket, sys, time
from pathlib import Path
assert socket.gethostname() == '[REDACTED_HOST]' and time.time() < 1789646400
stage = Path(ROOT)/'preparation/sleep6_copy_generation1'
stage.mkdir(mode=0o700, parents=True, exist_ok=False)
digest = hashlib.sha256()
size = 0
path = stage/'SLEEP6.private.tar'
with path.open('xb') as output:
    while True:
        data = sys.stdin.buffer.read(1024*1024)
        if not data:
            break
        size += len(data)
        assert size <= EXPECTED_BYTES
        digest.update(data)
        output.write(data)
    output.flush()
    os.fsync(output.fileno())
assert size == EXPECTED_BYTES and digest.hexdigest() == EXPECTED_SHA
path.chmod(0o400)
'''.replace('ROOT',repr(root)).replace('EXPECTED_BYTES',str(summary['archive_bytes'])).replace('EXPECTED_SHA',repr(summary['archive_sha256']))
with archive.open('rb') as source, (directory/'TRANSFER.stderr').open('xb') as errors:
    subprocess.run(['bash', str(repository/'gpu/ovx_ssh.sh'), 'python3 -B -c '+shlex.quote(transfer)],
        stdin=source, stdout=subprocess.DEVNULL, stderr=errors, timeout=180, check=True)
payload = dict(summary=summary, authority=base64.b64encode(authority_raw).decode())
program = '''
import base64, hashlib, json, os, socket, sys, tarfile, time
from pathlib import Path
payload = PAYLOAD
root = Path('/localhome/local-rohing/orch_r159_matched_evaluation_20260917_attempt1')
runtime = root/'preparation/runtime_generation3'
source = runtime/'source'
stage = root/'preparation/sleep6_copy_generation1'
archive = stage/'SLEEP6.private.tar'
inputs = root/'inputs/candidate5_sleep6_generation1'
control = root/'control/candidate5_sleep6_runtime3_generation1'
assert socket.gethostname() == '[REDACTED_HOST]' and time.time() < 1789646400
sys.path.insert(0,str(source))
from gpu import orch_r159_matched_evaluation as evaluator
from gpu import orch_r130_benchmark_sidecar as sidecar
def ref(path):
    return evaluator.ref(path)
def read(path):
    return evaluator.read(path)
def write(path,value):
    return evaluator.write(path,value)
assert evaluator.sha(evaluator.__file__) == '100e952409e9e76eb143db2d8f5a504ea8120593e52f85b56f19b07fd7d0bafc'
assert evaluator.sha(runtime/'SOURCE_MANIFEST.json') == '9a85e4cda65a517c779baea2dc393390936b90f199fe31947dab65c16fe45fa3'
manifest = read(runtime/'SOURCE_MANIFEST.json')
assert all(evaluator.sha(source/name) == checksum for name,checksum in manifest['sources'].items())
before = evaluator.ledger_status(root,evaluator.ORIGINAL_PLAN_SHA256)
assert before['calls_charged'] == 168 and before['reserved'] == before['completed'] == 3
assert before['failed'] == before['unresolved'] == 0
assert not inputs.exists() and not control.exists()
with tarfile.open(archive) as stream:
    members = stream.getmembers()
    assert len(members) == 25 and all(member.isfile() for member in members)
    captured = json.loads(stream.extractfile('R159_CAPTURE_RECEIPT.json').read())
    expected = {name:value['sha256'] for name,value in captured['allowlist'].items()}
    expected['R159_CAPTURE_RECEIPT.json'] = payload['summary']['receipt_sha256']
    assert len({member.name for member in members}) == 25 and {member.name for member in members} == set(expected)
    assert sum(member.size for member in members) < 536870912
extracted = sidecar.extract_regular_archive(archive,inputs,payload['summary']['archive_sha256'])
assert extracted['files'] == expected
for relative in expected:
    (inputs/relative).chmod(0o400)
authority_raw = base64.b64decode(payload['authority'],validate=True)
authority_sha = hashlib.sha256(authority_raw).hexdigest()
assert authority_sha == 'c55f64ad16f62e76fe7e4d584e85692e841d29a0ea541fdbbf85178cee9f3cd3'
with (inputs/'MAIN_SLEEP6_SOURCE_COPY_AUTHORITY.json').open('xb') as stream:
    stream.write(authority_raw)
(inputs/'MAIN_SLEEP6_SOURCE_COPY_AUTHORITY.json').chmod(0o400)
authority = json.loads(authority_raw)
assert captured['authority_sha256'] == authority_sha
old_source = root/'inputs/candidate5/SOURCE_OWNER_AUTHORITY.json'
owner = read(old_source)
assert ref(old_source)['sha256'] == 'b1d9c6cb745ec89fdd6c778df6a4278bdd1920bb9da6816604a86455395e5758'
owner.update(read_end_unix=1789646400, observed_unix=captured['captured_unix'],
    prior_source_owner_authority=ref(old_source),
    main_sleep_copy_authority=ref(inputs/'MAIN_SLEEP6_SOURCE_COPY_AUTHORITY.json'),
    sleep_boundary_capture=ref(inputs/'R159_CAPTURE_RECEIPT.json'),
    authorized_sleep_commits=authority['selected_commits'],
    new_evaluator_enrollment_authorized=False, new_gpu_execution_authorized=False)
write(inputs/'SOURCE_OWNER_AUTHORITY.json',owner)
template = read(root/'control/candidate5_initial3_runtime3/parented_learning.EXECUTION.proposed.json')
evaluator.validate_sources(template)
plan = evaluator.validate_plan(template['campaign'])
old = evaluator.OLD_ROOT
scheduler_path = old/'SCHEDULER_R158_20260917T0416Z.json'
assert evaluator.sha(scheduler_path) == 'fb9281e6a0c90f26b2ef30c1a4ba2215e419b0029e87b0cfa794e97b96bc8a0e'
scheduler = read(scheduler_path)
assert scheduler['lease_end_unix'] == template['lease_end_unix'] == 1789980180
assert 1789646400 <= scheduler['lease_end_unix']-21600
assert evaluator.ref(template['old_terminal']['path']) == template['old_terminal']
assert sidecar.gone(template['old_terminal_identity'])
assert evaluator.sha(template['python']) == template['python_sha256'] and os.access(template['python'],os.X_OK)
assert template['python'] == scheduler['python']
assert evaluator.sha(template['service_path']) == scheduler['service_sha256']
service = read(template['service_path'])
assert sidecar.identity(service['pid']) == {name:service[name] for name in ('pid','uid','boot_id','start_ticks')}
control.mkdir(mode=0o700,parents=True,exist_ok=False)
locks = Path('/proc/locks').read_text().splitlines()
devices = {}
for physical in (0,1):
    report = sidecar.scan(dict(physical=physical,gpu_uuid=sidecar.DEVICES[physical],service_path=template['service_path']))
    path = control/f'PHYSICAL{physical}_READINESS.private.json'
    write(path,dict(label='NEW_PROSPECTIVE_READINESS_NOT_DISPATCH_ADMISSION',observed_unix=time.time(),report=report))
    lock_path = old/f'physical{physical}.lock'
    info = lock_path.stat()
    matched = []
    for line in locks:
        for token in line.split():
            pieces = token.split(':')
            if len(pieces) == 3:
                try:
                    if (int(pieces[0],16),int(pieces[1],16),int(pieces[2])) == (os.major(info.st_dev),os.minor(info.st_dev),info.st_ino):
                        matched.append(line)
                except ValueError:
                    pass
    devices[str(physical)] = dict(clear=report['clear'],blocking_reasons=report['blocking_reasons'],
        gpu=report['gpu'],scanner_euid=report['scanner_euid'],scan=ref(path),
        lock_path=str(lock_path),lock_inode=info.st_ino,kernel_lock_entries=matched,lock_acquired=False)
readiness = dict(status='READONLY_CURRENT_SCHEDULER_LEASE_AND_SERVICE_VERIFIED',old_scheduler=ref(scheduler_path),
    existing_lease_end_unix=scheduler['lease_end_unix'], proposed_hard_end_unix=1789646400,
    six_hour_margin_satisfied=True,service=ref(template['service_path']),python_sha256=template['python_sha256'],
    old_controller_gone=True,devices=devices,ledger=before,observed_unix=time.time(),lease_extension=False,
    source_manifest=ref(runtime/'SOURCE_MANIFEST.json'),source_files_verified=len(manifest['sources']))
write(control/'READINESS.json',readiness)
node_authority = dict(schema=evaluator.SCHEMA,node='node2',campaign_sha256=template['campaign']['sha256'],
    hard_end_unix=1789646400,lease_end_unix=scheduler['lease_end_unix'],physical_slots=[0,1])
write(control/'NODE2_AUTHORITY.proposed.json',node_authority)
base = dict(template,hard_end_unix=1789646400,source_read_end_unix=1789646400,
    source_owner_authority=ref(inputs/'SOURCE_OWNER_AUTHORITY.json'),node2_authority=ref(control/'NODE2_AUTHORITY.proposed.json'))
candidates = {}
for selected,commit_sha in authority['selected_commits'].items():
    arm,checkpoint_name = selected.split('/')
    milestone = int(checkpoint_name.removeprefix('sleep_'))
    assert arm in ('parented_learning','unparented_learning') and milestone in (1,2,4)
    checkpoint = inputs/arm/'checkpoints'/checkpoint_name
    candidate_dir = inputs/'custody'/arm/checkpoint_name
    source_commit = str(Path(authority['source_root'])/arm/'checkpoints'/checkpoint_name/'COMMIT.json')
    assert evaluator.sha(checkpoint/'COMMIT.json') == commit_sha
    checkpoint_manifest = dict(schema=evaluator.native.MANIFEST_SCHEMA,adapter_path=str(checkpoint/'adapter'),
        commit_path=str(checkpoint/'COMMIT.json'),commit_sha256=commit_sha)
    write(candidate_dir/'MANIFEST.json',checkpoint_manifest)
    custody = dict(schema=evaluator.SCHEMA,cohort_sha256=authority['cohort_sha256'],source_root=str(Path(authority['source_root'])/arm),
        source_commit_path=source_commit,commit_sha256=commit_sha,manifest_sha256=evaluator.sha(candidate_dir/'MANIFEST.json'),
        checkpoint_boundary=milestone,source_owner_authority=base['source_owner_authority'],
        timestamp_custody=owner['timestamp_custody'],source_read_end_unix=1789646400,
        adapter_only=True,optimizer_rng_read=False,history_read=False,source_written=False)
    write(candidate_dir/'SOURCE_CUSTODY.json',custody)
    candidate = read(root/'inputs/candidate5'/arm/'CANDIDATE.json')
    candidate.update(milestone=milestone,source_commit_path=source_commit,
        manifest=ref(candidate_dir/'MANIFEST.json'),source_custody=ref(candidate_dir/'SOURCE_CUSTODY.json'))
    write(candidate_dir/'CANDIDATE.proposed.json',candidate)
    key = arm+'_'+str(milestone)
    candidates[key] = ref(candidate_dir/'CANDIDATE.proposed.json')
    evaluator.candidate_check(dict(base,candidate=candidates[key]),plan)
    assert not (root/'ledger'/(key+'.RESERVED.json')).exists() and not (root/'attempts'/key).exists()
write(control/'BUILDER.json',dict(status='CPU_AND_PROVENANCE_PASS',campaign=base['campaign'],cpu_gate=base['cpu_gate'],
    created_unix=time.time(),candidate_checks_passed=6,source_owner_authority=base['source_owner_authority'],
    copy_capture=ref(inputs/'R159_CAPTURE_RECEIPT.json'),readiness=ref(control/'READINESS.json'),
    gpu_execution_authorized=False,enrollment_authorized=False,raw_snapshots_not_qualified_fit=True))
base['builder'] = ref(control/'BUILDER.json')
configs = {}
for key,reference in candidates.items():
    physical = 0 if key.startswith('parented_learning_') else 1
    configuration = dict(base,candidate=reference,physical=physical,gpu_uuid=sidecar.DEVICES[physical])
    path = control/(key+'.EXECUTION.proposed.json')
    write(path,configuration)
    evaluator.validate_sources(configuration)
    evaluator.candidate_check(configuration,plan)
    configs[key] = ref(path)
schedule = dict(status='PROPOSAL_ONLY_NO_MAIN_GO',source_authority=ref(inputs/'MAIN_SLEEP6_SOURCE_COPY_AUTHORITY.json'),
    hard_end_unix=1789646400,latest_dispatch_strictly_before_unix=1789642785,
    full_job_window_seconds=3615,call_cap=672,checkpoint_cap=12,already_charged=168,prospective_calls=336,
    waves=[dict(milestone=milestone,proposed_start_utc=start,slots={str(physical):configs[arm+'_'+str(milestone)]
        for physical,arm in enumerate(('parented_learning','unparented_learning'))})
        for milestone,start in ((1,'2026-09-17T07:45:00Z'),(2,'2026-09-17T08:50:00Z'),(4,'2026-09-17T09:55:00Z'))],
    requirements=['new exact Main enrollment/GPU GO','each previous own slot key terminal and exact identities released',
        'fresh unchanged full privileged admission; no waived reasons','new once markers and captured actual reports',
        'no post-sampling retry; no assumed parallel-admission success'],
    original_wrapper_expired_must_not_reuse=True,frozen_controls_missing=True)
write(control/'SCHEDULE.proposed.json',schedule)
after = evaluator.ledger_status(root,evaluator.ORIGINAL_PLAN_SHA256)
assert after == before
for relative,checksum in expected.items():
    assert evaluator.sha(inputs/relative) == checksum
output = dict(status='SIX_COPIED_AND_CPU_PROPOSED_NO_ENROLLMENT_NO_GPU',configurations=configs,candidates=candidates,
    source_owner_authority=ref(inputs/'SOURCE_OWNER_AUTHORITY.json'),timestamp_custody=owner['timestamp_custody'],
    builder=ref(control/'BUILDER.json'),node2_authority=ref(control/'NODE2_AUTHORITY.proposed.json'),
    readiness=readiness,schedule=ref(control/'SCHEDULE.proposed.json'),runtime_cpu_gate=base['cpu_gate'],
    campaign=base['campaign'],freeze=plan['freeze'],archive=ref(archive),capture=ref(inputs/'R159_CAPTURE_RECEIPT.json'),
    copied_files=24,adapter_payload_bytes=payload['summary']['source_adapter_bytes'],
    all_two_hop_bytes=payload['summary']['all_two_hop_bytes'],candidate_checks_passed=6,
    full_execution_GO_validation=False,ledger_unchanged=True,ledger=after,observed_unix=time.time())
write(control/'PREPARATION_RECEIPT.json',output)
print(json.dumps(output,sort_keys=True))
'''.replace('PAYLOAD',repr(payload),1)
with (directory/'PREPARE.stderr').open('xb') as errors:
    completed = subprocess.run(['bash',str(repository/'gpu/ovx_ssh.sh'),'/localhome/local-rohing/v2/venv/bin/python -B -'],
        input=program.encode(),stdout=subprocess.PIPE,stderr=errors,timeout=300,check=True)
with (directory/'PREPARATION_RECEIPT.json').open('xb') as output:
    output.write(completed.stdout)
metadata = json.loads(completed.stdout)
print(json.dumps({key:metadata[key] for key in ('status','configurations','source_owner_authority','builder','node2_authority',
    'schedule','candidate_checks_passed','ledger','observed_unix')},sort_keys=True))
