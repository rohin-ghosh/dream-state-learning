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
    status = json.loads((base / 'CANDIDATE4_RECEIVING_STATUS.json').read_bytes())
    cpu = json.loads((base / 'candidate4_inputs/CPU.json').read_bytes())
    review = repository / 'research_loop/workers/R158_SAVED_INITIALIZER_RECOVERY_REVIEW.md'
    assert checksum(review) == arguments.review_sha256
    reviewed_text = review.read_text()
    assert 'APPROVE' in reviewed_text
    files = {name: checksum(repository / name) for name in REPAIR_FILES}
    assert all(cpu['source_inventory'][name] == digest for name, digest in files.items())
    assert all(files[name] == digest for name, digest in status['owned_files'].items())
    assert all(digest in reviewed_text for digest in status['owned_files'].values())
    assert cpu['status'] == 'PASS' and cpu['exit_code'] == 0 and cpu['passed'] == 800
    assert status['receiving_tests']['actual_profile_and_installed_passed'] == 4
    assert status['local_tests']['passed'] == 938
    for receipt in status['receiving_tests']['receipts'].values():
        assert checksum(receipt['path']) == receipt['sha256']
    assert checksum(status['local_tests']['log']['path']) == status['local_tests']['log']['sha256']
    output = base / 'candidate4_main_release'
    remote = Path(status['remote_base']) / 'main_release'
    note = base / 'CANDIDATE4_MAIN_RELEASE_NOTE.md'
    assert note.is_file()
    reviews = [review, repository / 'research_loop/workers/R158_NODE4_CALLBACK_REPAIR_REVIEW.md',
               repository / 'research_loop/workers/R158_MATCHED_ENV_REPAIR_REVIEW.md',
               repository / 'research_loop/workers/R158_MATCHED_CAPACITY_ENV_REVIEW.md']
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
