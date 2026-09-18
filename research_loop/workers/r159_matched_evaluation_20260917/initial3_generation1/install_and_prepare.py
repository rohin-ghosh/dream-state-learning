import base64
import hashlib
import json
from pathlib import Path
import subprocess
import tarfile


DIRECTORY = Path(__file__).resolve().parent
WORKER = DIRECTORY.parent
REPOSITORY = WORKER.parents[2]
REMOTE = '/localhome/local-rohing/orch_r159_matched_evaluation_20260917_attempt1'


def read(path):
    return json.loads(Path(path).read_bytes())


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    authority_path = WORKER / 'MAIN_INITIAL3_SOURCE_COPY_AUTHORITY_20260917.json'
    assert sha(authority_path) == '254067adeef94d3947953bf6f45db8218f2135fbdd502925951a656139396f26'
    authority = read(authority_path)
    custody = read(DIRECTORY / 'CUSTODY_PREPARED.json')
    ready = read(WORKER / 'runtime_generation3/NODE2_READINESS.json')
    runtime = read(WORKER / 'runtime_generation3/REPAIR_METADATA.json')
    allowlist = read(WORKER / 'candidate5_initial3_templates/COPY_ALLOWLIST.template.json')
    archive = DIRECTORY / 'INITIAL3.private.tar'
    expected_files = {}
    for item in allowlist['items']:
        prefix = f"{item['arm']}/checkpoints/initial/"
        expected_files[prefix+'COMMIT.json'] = authority['initial_commits'][item['arm']]
        expected_files.update({prefix+'adapter/'+name: checksum for name, checksum in item['expected_adapter_files'].items()})
    with tarfile.open(archive) as stream:
        members = stream.getmembers()
        assert len(members) == 12 and {item.name for item in members} == set(expected_files)
        assert all(item.isfile() and not item.issym() and not item.islnk() for item in members)
        assert sum(item.size for item in members) <= authority['adapter_copy_bytes_maximum']
        for item in members:
            assert hashlib.sha256(stream.extractfile(item).read()).hexdigest() == expected_files[item.name]
    metadata = {}
    for relative, item in custody['metadata_files'].items():
        raw = Path(item['local_path']).read_bytes()
        assert hashlib.sha256(raw).hexdigest() == item['sha256']
        metadata[relative] = base64.b64encode(raw).decode()
    candidates = {arm: read(WORKER / f'candidate5_initial3_templates/{arm}/CANDIDATE.template.json')
                  for arm in authority['allowed_arms']}
    payload = dict(metadata=metadata, expected_files=expected_files, archive_sha256=sha(archive),
        custody=custody, ready=ready, runtime=runtime, candidates=candidates,
        main_authority_sha256=sha(authority_path))
    ssh = ['bash', str(REPOSITORY / 'gpu/ovx_ssh.sh')]
    target = REMOTE + '/preparation/initial3_copy_generation1'
    with archive.open('rb') as source, (DIRECTORY / 'TRANSFER.stderr').open('xb') as errors:
        subprocess.run(ssh + [f"umask 077; set -eC; mkdir '{target}'; cat > '{target}/INITIAL3.private.tar'"],
                       stdin=source, stdout=subprocess.DEVNULL, stderr=errors, check=True, timeout=180)
    program = '''
import base64, hashlib, json, os, shutil, socket, sys, tarfile, time
from pathlib import Path
payload = PAYLOAD
root = Path('/localhome/local-rohing/orch_r159_matched_evaluation_20260917_attempt1')
runtime = root/'preparation/runtime_generation3'
stage = root/'preparation/initial3_copy_generation1'
archive = stage/'INITIAL3.private.tar'
assert socket.gethostname() == '[REDACTED_HOST]' and time.time() < 1789632000
sys.path.insert(0, str(runtime/'source'))
from gpu import orch_r159_matched_evaluation as evaluator
from gpu import orch_r130_benchmark_sidecar as sidecar
def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def ref(path):
    return dict(path=str(path), sha256=sha(path))
def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    with path.open('x') as stream:
        json.dump(value, stream, sort_keys=True, indent=2)
        stream.write('\\n')
    path.chmod(0o400)
def raw_write(path, raw):
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    with path.open('xb') as stream:
        stream.write(raw)
    path.chmod(0o400)
manifest = json.loads((runtime/'SOURCE_MANIFEST.json').read_bytes())
assert sha(runtime/'SOURCE_MANIFEST.json') == payload['runtime']['source_manifest']['sha256']
evaluator.validate_sources(dict(source_root=str(runtime/'source'), sources=manifest['sources']))
assert sha(archive) == payload['archive_sha256']
with tarfile.open(archive) as stream:
    members = stream.getmembers()
    assert len(members) == 12 and {item.name for item in members} == set(payload['expected_files'])
    assert all(item.isfile() and not item.islnk() and not item.issym() for item in members)
    assert sum(item.size for item in members) <= 536870912
extracted = stage/'extracted'
receipt = sidecar.extract_regular_archive(archive, extracted, payload['archive_sha256'])
assert receipt['files'] == payload['expected_files']
inputs = root/'inputs/candidate5'
assert not inputs.exists()
inputs.mkdir(parents=True, mode=0o700)
for relative, encoded in payload['metadata'].items():
    path = inputs/relative
    assert path.is_relative_to(inputs) and '..' not in Path(relative).parts
    raw_write(path, base64.b64decode(encoded, validate=True))
assert sha(inputs/'shared/MAIN_SOURCE_COPY_AUTHORITY.json') == payload['main_authority_sha256']
assert sha(inputs/'SOURCE_OWNER_AUTHORITY.json') == payload['custody']['source_owner_authority']['sha256']
assert sha(inputs/'TIMESTAMP_CUSTODY.json') == payload['custody']['timestamp_custody']['sha256']
for relative, expected in payload['expected_files'].items():
    parts = Path(relative).parts
    destination = inputs/parts[0]/'initial'/Path(*parts[3:])
    source = extracted/relative
    raw_write(destination, source.read_bytes())
    assert sha(destination) == expected
plan_ref = payload['runtime']['plan']
plan = evaluator.validate_plan(plan_ref)
control = root/'control/candidate5_initial3_runtime3'
assert not control.exists()
control.mkdir(parents=True, mode=0o700)
ready = payload['ready']
assert sha(ready['old_terminal']['path']) == ready['old_terminal']['sha256']
try:
    current = sidecar.identity(ready['old_terminal_identity']['pid'])
except (FileNotFoundError, ProcessLookupError):
    current = None
assert current != ready['old_terminal_identity']
assert sha(ready['python']) == ready['python_sha256'] and os.access(ready['python'], os.X_OK)
assert sha(ready['service']['path']) == ready['service']['sha256']
assert 1789632000 <= ready['existing_lease_end_unix']-21600
node_authority = dict(schema=evaluator.SCHEMA, node='node2', campaign_sha256=plan_ref['sha256'],
    hard_end_unix=1789632000, lease_end_unix=ready['existing_lease_end_unix'], physical_slots=[0,1])
write(control/'NODE2_AUTHORITY.proposed.json', node_authority)
gpu_checks = {}
for physical in (0,1):
    report = sidecar.scan(dict(physical=physical, gpu_uuid=sidecar.DEVICES[physical],
                             service_path=ready['service']['path']))
    gpu_checks[str(physical)] = dict(clear=report['clear'], blocking_reasons=report['blocking_reasons'],
        scanner_euid=report['scanner_euid'], gpu_uuid=report['gpu']['uuid'], observed_unix=time.time())
write(control/'READINESS.json', dict(devices=gpu_checks, old_controller_identity_gone=True,
    no_lock_acquired=True, service_sha256=ready['service']['sha256'], observed_unix=time.time()))
base = dict(schema=evaluator.SCHEMA, campaign=plan_ref, campaign_root=str(root),
    source_root=str(runtime/'source'), sources=manifest['sources'], model_dir=ready['model_dir'],
    python=ready['python'], python_sha256=ready['python_sha256'], hard_end_unix=1789632000,
    lease_end_unix=ready['existing_lease_end_unix'], source_read_end_unix=1789632000,
    source_owner_authority=ref(inputs/'SOURCE_OWNER_AUTHORITY.json'), old_terminal=ready['old_terminal'],
    old_terminal_identity=ready['old_terminal_identity'], cpu_gate=payload['runtime']['cpu_gate'],
    node2_authority=ref(control/'NODE2_AUTHORITY.proposed.json'), service_path=ready['service']['path'])
candidate_refs = {}
for arm, candidate in payload['candidates'].items():
    directory = inputs/arm
    commit = directory/'initial/COMMIT.json'
    checkpoint_manifest = dict(schema=evaluator.native.MANIFEST_SCHEMA, adapter_path=str(directory/'initial/adapter'),
        commit_path=str(commit), commit_sha256=sha(commit))
    write(directory/'MANIFEST.json', checkpoint_manifest)
    custody = dict(schema=evaluator.SCHEMA, cohort_sha256=candidate['cohort']['sha256'],
        source_root=str(Path(candidate['source_commit_path']).parents[2]),
        source_commit_path=candidate['source_commit_path'], commit_sha256=sha(commit),
        manifest_sha256=sha(directory/'MANIFEST.json'), checkpoint_boundary=0,
        source_owner_authority=base['source_owner_authority'], timestamp_custody=ref(inputs/'TIMESTAMP_CUSTODY.json'),
        source_read_end_unix=1789632000, adapter_only=True, optimizer_rng_read=False,
        history_read=False, source_written=False)
    write(directory/'SOURCE_CUSTODY.json', custody)
    candidate.update(manifest=ref(directory/'MANIFEST.json'), source_custody=ref(directory/'SOURCE_CUSTODY.json'))
    write(directory/'CANDIDATE.json', candidate)
    candidate_refs[arm] = ref(directory/'CANDIDATE.json')
    evaluator.candidate_check(dict(base, candidate=candidate_refs[arm]), plan)
write(control/'BUILDER.json', dict(status='CPU_AND_PROVENANCE_PASS', campaign=plan_ref,
    cpu_gate=base['cpu_gate'], created_unix=time.time(), candidate_checks_passed=3,
    source_owner_authority=base['source_owner_authority'], readiness=ref(control/'READINESS.json'),
    gpu_execution_authorized=False))
base['builder'] = ref(control/'BUILDER.json')
configurations = {}
for arm, physical in (('parented_learning',0), ('parented_frozen',1), ('unparented_learning',0)):
    config = dict(base, candidate=candidate_refs[arm], physical=physical, gpu_uuid=sidecar.DEVICES[physical])
    write(control/f'{arm}.EXECUTION.proposed.json', config)
    configurations[arm] = ref(control/f'{arm}.EXECUTION.proposed.json')
ledger = evaluator.ledger_status(root, plan_ref['sha256'])
assert ledger['reserved'] == ledger['calls_charged'] == 0
result = dict(status='INITIAL3_COPIED_CPU_CANDIDATE_CHECKS_PASS_NO_GPU_GO',
    configurations=configurations, candidate_refs=candidate_refs, source_owner_authority=base['source_owner_authority'],
    timestamp_custody=ref(inputs/'TIMESTAMP_CUSTODY.json'), builder=base['builder'],
    node2_authority=base['node2_authority'], readiness=ref(control/'READINESS.json'), devices=gpu_checks,
    source_manifest=payload['runtime']['source_manifest'], cpu_gate=base['cpu_gate'], plan=plan_ref,
    archive=ref(archive), archive_files_verified=len(receipt['files']), copied_payload_bytes=sum(item.size for item in members),
    metadata_input_bytes=sum(len(base64.b64decode(value)) for value in payload['metadata'].values()),
    old_terminal=ready['old_terminal'], old_controller_identity_gone=True, lease_end_unix=ready['existing_lease_end_unix'],
    hard_end_unix=1789632000, latest_dispatch_strictly_before_unix=1789632000-3615,
    full_execution_GO_validation=False, no_optimizer_rng_payload_read=True, no_held_contents_read=True,
    source_written=False, model_calls=0, new_ledger=ledger, observed_unix=time.time())
write(control/'COPY_AND_CPU_RECEIPT.json', result)
print(json.dumps(dict(receipt=result, receipt_ref=ref(control/'COPY_AND_CPU_RECEIPT.json'),
    configurations={arm: json.loads(Path(reference['path']).read_bytes()) for arm, reference in configurations.items()}), sort_keys=True))
'''.replace('PAYLOAD', repr(payload), 1)
    with (DIRECTORY / 'INSTALL.stderr').open('xb') as errors:
        completed = subprocess.run(ssh + ['/localhome/local-rohing/v2/venv/bin/python -B -'],
            input=program.encode(), stdout=subprocess.PIPE, stderr=errors, check=True, timeout=180)
    with (DIRECTORY / 'INSTALL_RETURN.json').open('xb') as stream:
        stream.write(completed.stdout)
    result = json.loads(completed.stdout)
    for name, value in [('COPY_AND_CPU_RECEIPT.json', result['receipt']), ('REMOTE_RECEIPT_REF.json', result['receipt_ref'])]:
        with (DIRECTORY / name).open('x') as stream:
            json.dump(value, stream, indent=2, sort_keys=True)
            stream.write('\n')
    for arm, config in result['configurations'].items():
        with (DIRECTORY / f'{arm}.EXECUTION.proposed.json').open('x') as stream:
            json.dump(config, stream, indent=2, sort_keys=True)
            stream.write('\n')
    print(json.dumps(result['receipt'], sort_keys=True))


if __name__ == '__main__':
    main()
