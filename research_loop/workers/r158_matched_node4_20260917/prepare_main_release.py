import hashlib
import json
from pathlib import Path

from gpu.orch_r158_matched_node4 import REPAIR_FILES, SCOPE


base = Path('research_loop/workers/r158_matched_node4_20260917').resolve()
status = json.loads((base / 'CANDIDATE2_RECEIVING_STATUS.json').read_text())
remote = Path(status['remote_base']) / 'main_release'
output = base / 'main_release'
output.mkdir(exist_ok=False)


def checksum(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def save(name, value):
    with (output / name).open('x') as stream:
        json.dump(value, stream, indent=2, sort_keys=True)
        stream.write('\n')


reviews = [Path('research_loop/workers/R158_MATCHED_CAPACITY_ENV_REVIEW.md').resolve(),
           Path('research_loop/workers/R158_MATCHED_ENV_REPAIR_REVIEW.md').resolve()]
assert '**APPROVE — E1 and E2 repairs only' in reviews[1].read_text()
assert '**APPROVE the bounded R1–R3 capacity repairs' in reviews[0].read_text()
receiving = json.loads((base / 'CANDIDATE2_RECEIVING_CPU.json').read_text())
inventory = receiving['source_inventory']
files = {name: checksum(name) for name in REPAIR_FILES}
for name in ('gpu/orch_r158_matched_node4.py', 'tests/test_orch_r158_matched_node4.py'):
    files[name] = checksum(name)
assert all(inventory[name] == value for name, value in files.items())
for review in reviews:
    with (output / review.name).open('xb') as stream:
        stream.write(review.read_bytes())
note = base / 'MAIN_RELEASE_NOTE.md'
with (output / note.name).open('xb') as stream:
    stream.write(note.read_bytes())
save('APPROVED_REPAIRS.json', dict(schema='R158_MATCHED_REPAIR_REVIEW_V1', status='PASS',
    issuer='Main', freeze_allowed=True, review_disposition='APPROVED_FOR_FREEZE',
    review_receipts=[dict(path=str(remote / review.name), sha256=checksum(review)) for review in reviews],
    capacity_consumer_fixed=True, deadline_cleanup_fixed=True, failure_receipts_fixed=True,
    files=files, tests=dict(exit_code=0, passed=receiving['passed'], logs=receiving['logs']),
    approved_scope=SCOPE, new_human_ratification_claimed=False, GPU_launch_permitted_without_phase_GO=False))
save('INTAKE.json', dict(requested_scope=SCOPE, classification='STANDING_AUTHORIZED_NON_MATERIAL',
    changes_invariants=False, new_human_ratification_claimed=False))
save('PUBLICATION.json', dict(posted=True, git_commit_or_push=False,
    note_path=str(remote / note.name), note_sha256=checksum(note)))
save('MANIFEST.json', {path.name: checksum(path) for path in sorted(output.iterdir())})
print(json.dumps(dict(local=str(output), remote=str(remote),
                     files={path.name: checksum(path) for path in sorted(output.iterdir())}), sort_keys=True))
