import argparse
import hashlib
import json
from pathlib import Path

from gpu.orch_r158_matched_node4 import REPAIR_FILES, SCOPE


def checksum(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--review-sha256', required=True)
    arguments = parser.parse_args()
    base = Path(__file__).resolve().parent
    repository = base.parents[2]
    cpu = json.loads((base / 'candidate5_inputs/CPU.json').read_bytes())
    remote = Path('/localhome/local-rohing/orch_r158_matched_node4_20260917_attempt5/main_release')
    review = repository / 'research_loop/workers/R158_TRANSIENT_SCAN_RECHECK_REVIEW.md'
    assert checksum(review) == arguments.review_sha256
    assert 'APPROVE' in review.read_text()
    files = {name: checksum(repository / name) for name in REPAIR_FILES}
    assert all(cpu['source_inventory'][name] == digest for name, digest in files.items())
    for name in ('gpu/orch_r158_matched_node4.py', 'tests/test_orch_r158_matched_node4.py'):
        assert files[name] in review.read_text()
    assert cpu['status'] == 'PASS' and cpu['exit_code'] == 0 and cpu['passed'] >= 800
    assert cpu['host'] == '[REDACTED_HOST]'
    for receipt in cpu['logs']:
        assert checksum(base / 'candidate5_inputs' / Path(receipt['path']).name) == receipt['sha256']
    reviews = [review, repository / 'research_loop/workers/R158_SAVED_INITIALIZER_RECOVERY_REVIEW.md',
        repository / 'research_loop/workers/R158_NODE4_CALLBACK_REPAIR_REVIEW.md',
        repository / 'research_loop/workers/R158_MATCHED_ENV_REPAIR_REVIEW.md',
        repository / 'research_loop/workers/R158_MATCHED_CAPACITY_ENV_REVIEW.md']
    assert files['gpu/orch_r150_matched_native.py'] in reviews[1].read_text()
    note = base / 'CANDIDATE5_MAIN_RELEASE_NOTE.md'
    output = base / 'candidate5_main_release'
    output.mkdir(exist_ok=False)
    for document in [*reviews, note]:
        with (output / document.name).open('xb') as stream:
            stream.write(document.read_bytes())

    def save(name, value):
        with (output / name).open('x') as stream:
            json.dump(value, stream, indent=2, sort_keys=True)
            stream.write('\n')

    save('APPROVED_REPAIRS.json', dict(schema='R158_MATCHED_REPAIR_REVIEW_V1', status='PASS',
        issuer='Main', freeze_allowed=True, review_disposition='APPROVED_FOR_FREEZE',
        review_receipts=[dict(path=str(remote / item.name), sha256=checksum(item)) for item in reviews],
        capacity_consumer_fixed=True, deadline_cleanup_fixed=True, failure_receipts_fixed=True,
        files=files, tests=dict(exit_code=0, passed=cpu['passed'], logs=cpu['logs']),
        approved_scope=SCOPE, new_human_ratification_claimed=False,
        GPU_launch_permitted_without_phase_GO=False))
    save('INTAKE.json', dict(requested_scope=SCOPE, classification='STANDING_AUTHORIZED_NON_MATERIAL',
        changes_invariants=False, new_human_ratification_claimed=False))
    save('PUBLICATION.json', dict(posted=True, git_commit_or_push=False,
        note_path=str(remote / note.name), note_sha256=checksum(note)))
    save('MANIFEST.json', {path.name: checksum(path) for path in sorted(output.iterdir())})
    print(json.dumps(dict(local=str(output), remote=str(remote),
        files={path.name: checksum(path) for path in sorted(output.iterdir())}), sort_keys=True))


if __name__ == '__main__':
    main()
