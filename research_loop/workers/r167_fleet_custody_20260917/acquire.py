import base64
import hashlib
import json
from pathlib import Path
import subprocess
import time


ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[2]


def pin(path):
    return dict(path=str(path), sha256=hashlib.sha256(path.read_bytes()).hexdigest())


def save(name, value):
    with (ROOT / name).open('x') as stream:
        json.dump(value, stream, indent=2, sort_keys=True)
        stream.write('\n')


def main():
    batch_path = REPO / 'research_loop/workers/r167_object_survival/fleet_generation1/BATCH_PLAN.json'
    api_path = REPO / 'research_loop/workers/r167_object_survival/FLEET_PROSPECTIVE_API.md'
    wrapper = REPO / 'gpu/ovx3_ssh.sh'
    source = ROOT / 'collect_metadata.py'
    batch = json.loads(batch_path.read_bytes())
    wanted = ['C1', 'C2', 'C3', 'C4', 'continual_run1', 'pilot', 'repo_reader']
    rows = {row['life_id']: row for row in batch['lives']}
    spec = dict(lives=[rows[name] for name in wanted], batch_plan_sha256=pin(batch_path)['sha256'],
                collector_sha256=pin(source)['sha256'])
    save('ACQUISITION_SPEC.json', spec)
    provenance = dict(started_unix=time.time(), batch=pin(batch_path), api=pin(api_path),
                      wrapper=pin(wrapper), collector=pin(source), launcher=pin(Path(__file__)),
                      c5_status='PENDING_BANACH_EXACT_RECOVERY_RELEASE', remote_timeout_seconds=180)
    argument = base64.b64encode(json.dumps(spec).encode()).decode()
    try:
        result = subprocess.run(['bash', str(wrapper), 'python3 -B - ' + argument],
                                input=source.read_bytes(), capture_output=True, timeout=180)
        stdout, stderr, returncode = result.stdout, result.stderr, result.returncode
    except subprocess.TimeoutExpired as error:
        stdout, stderr, returncode = error.stdout or b'', error.stderr or b'', 'LOCAL_WRAPPER_TIMEOUT'
    with (ROOT / 'REMOTE_METADATA.jsonl').open('xb') as stream:
        stream.write(stdout)
    with (ROOT / 'TRANSPORT.stderr').open('xb') as stream:
        stream.write(stderr)
    provenance.update(finished_unix=time.time(), returncode=returncode,
                      output=pin(ROOT / 'REMOTE_METADATA.jsonl'), stderr=pin(ROOT / 'TRANSPORT.stderr'),
                      batch_unchanged=pin(batch_path) == provenance['batch'],
                      api_unchanged=pin(api_path) == provenance['api'])
    save('ACQUISITION.json', provenance)
    for line in stdout.splitlines():
        receipt = json.loads(line)
        save(receipt['life_id'] + '.json', receipt)
        findings = receipt['findings']
        native = findings.get('current_native', {})
        frontier = findings.get('frontier_metadata', {})
        print(json.dumps(dict(life_id=receipt['life_id'], bytes=receipt['metadata_bytes_read'],
            native=native.get('native_identity'), initial='initial_checkpoint' in findings,
            source_matches=native.get('all_declared_source_pins_match'),
            latest_sleep=frontier.get('latest_sleep_directory'),
            sleep_envelope=bool(frontier.get('observed_sleep_complete')),
            errors=receipt['missing_reasons'][:-3]), sort_keys=True))
    print(json.dumps(dict(returncode=returncode, stderr_bytes=len(stderr), output_bytes=len(stdout))))


if __name__ == '__main__':
    main()
