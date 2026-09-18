"""Stage only independent immutable-source copies for six authorized node5 arms."""

import hashlib
import json
from pathlib import Path
import subprocess
import time


ROOT = Path('/localhome/local-rohing/orch_r201_math_b_node5_20260918_attempt1')


def sha(path):
    with path.open('rb') as handle:
        return hashlib.file_digest(handle, 'sha256').hexdigest()


def files(root):
    return {str(path.relative_to(root)): sha(path) for path in sorted(root.rglob('*')) if path.is_file()}


def write(path, document):
    with path.open('x') as handle:
        json.dump(document, handle, sort_keys=True, indent=2)


def main():
    assignment_path = ROOT / 'R203_SCALE_ASSIGNMENT.json'
    assignment = json.loads(assignment_path.read_bytes())
    assert assignment['schema'] == 'R203_NODE5_ARM_ASSIGNMENT_V1'
    assert {arm['physical'] for arm in assignment['arms']} == {0, 2, 3, 4, 5, 6}
    assert assignment['source_checkpoint'] == 51 and assignment['source_optimizer_steps'] == 4908
    assert assignment['common_console_cut'] == 5846 and assignment['original52_never_used_as_clone_source']
    assert sha(ROOT / 'snapshot/MANIFEST.json') == assignment['shared_snapshot_manifest_sha256']
    paths = sorted((ROOT / 'life/stream/records').glob('[0-9]' * 20 + '.json'))
    head = json.loads(paths[-1].read_bytes())
    assert len(paths) == 5847 and head['index'] == 5846
    assert head['sha256'] == assignment['common_console_record_sha256']
    checkpoint = json.loads((ROOT / 'life/checkpoints/sleep_000051/COMMIT.json').read_bytes())
    assert checkpoint['optimizer_steps'] == 4908
    assert not (ROOT / 'life/checkpoints/sleep_000052').exists()
    assert len(list((ROOT / 'life/stream/inbox').glob('*.json'))) == 130
    source_hashes = {name: files(ROOT / name) for name in ('life', 'source', 'snapshot')}
    write(ROOT / 'R203_FIXED_COPY_BASIS.json', dict(observed_unix=time.time(),
        assignment_sha256=sha(assignment_path), source_hashes=source_hashes,
        checkpoint=51, optimizer_steps=4908, console_cut=5846, registered_inbox=130))
    receipts = []
    for arm in sorted(assignment['arms'], key=lambda item: item['physical'] != 3):
        destination = Path(arm['control_root'])
        if arm['physical'] == 3:
            assert destination == ROOT and arm['arm'] == 'MATH-B'
        else:
            assert destination.parent == ROOT.parent
            assert destination.name.startswith('orch_r203_') and '_node5_20260918_attempt1' in destination.name
            destination.mkdir(mode=0o700)
            for name in ('life', 'source', 'snapshot'):
                subprocess.run(['cp', '-a', '--reflink=auto', str(ROOT / name), str(destination / name)], check=True)
                assert files(destination / name) == source_hashes[name], 'independent_copy_hash_mismatch'
        receipt = dict(observed_unix=time.time(), status='COMMON_DATA_STAGED_NOT_R203_CONFIGURED_NOT_LAUNCHED',
            arm=arm['arm'], physical=arm['physical'], control_root=str(destination),
            new_life_root=str(destination / 'life'), gpu_uuid=arm['gpu_uuid'],
            common_source_root=str(ROOT), source_basis_sha256=sha(ROOT / 'R203_FIXED_COPY_BASIS.json'),
            source_checkpoint=51, source_optimizer_steps=4908, common_console_cut=5846,
            common_console_record_sha256=head['sha256'], registered_inbox=130,
            independent_file_copy_not_hardlinks=arm['physical'] != 3,
            runtime_basis='Existing R201 source only; tested R203 overlay still required',
            retirement_authority='R203 resource reallocation, no failure-science claim',
            old_identity_reference=arm['old_native'], old_live_root=arm['old_storage_root'],
            old_life_changed=False, retirements=0, launches=0, gpu_calls=0,
            original_C2_or_repo_reader_changed=False, new_human_messages=0)
        write(destination / 'R203_DATA_STAGED.json', receipt)
        receipts.append(receipt)
        print(json.dumps(dict(physical=arm['physical'], arm=arm['arm'], status=receipt['status'])), flush=True)
    assert all(files(ROOT / name) == expected for name, expected in source_hashes.items())
    write(ROOT / 'R203_FLEET_STAGED.json', dict(observed_unix=time.time(),
        status='SIX_COMMON_SOURCES_STAGED_WAITING_TESTED_R203_RUNTIME', arms=receipts,
        reserved_slots=[1, 7], no_live_inbox_replication=True, source52_not_used=True,
        original_C2_remains_paused=True, parent_autopublish_frozen=True,
        retirements=0, launches=0))


if __name__ == '__main__':
    main()
