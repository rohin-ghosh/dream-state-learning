"""Prepare only the 514 already archived groups not executed by the canary."""

from copy import deepcopy
import json
import os
from pathlib import Path

from verify_completed_canary import FROZEN, HERE, TRANSPORT_SHA, frozen, local_proof


CODE_FILES = ('prepare_remaining.py', 'run_remaining.py', 'test_remaining.py', 'verify_completed_canary.py')
CANARY_RECEIPT_SHA = '5e459d9eb1c9296a76b7007fd2982238998549112902d21c605726802182cc08'


def canonical_bytes(document):
    return json.dumps(document, sort_keys=True, separators=(',', ':')).encode()


def group_paths(group):
    return [entry['path'] for inode in [group['canonical'], *group['replacement_inodes']]
            for entry in inode['paths']]


def plan_batches(assessment, canary, completion):
    require = frozen.require
    require(frozen.sha(canonical_bytes(canary)) == frozen.CANARY_SHA, 'exact_original_canary')
    require(canonical_bytes(assessment) == canonical_bytes(json.loads(frozen.frozen_artifacts()['GROUPS.json'])),
            'exact_original_515_group_selection')
    require(completion['ssh_exit'] == 0 and completion['ledger_records'] == 24
            and completion['completion']['kind'] == 'CANARY_COMPLETE_ALL_PATHS_VERIFIED'
            and completion['completion']['document']['replacements'] == 6, 'successful_canary_only')
    excluded = {path for group in canary['groups'] for path in group_paths(group)}
    require({row['path'] for row in completion['completion']['document']['paths']} == excluded,
            'all_canary_paths_verified')
    require(len(assessment['groups']) == 515 and assessment['groups'][0] == canary['groups'][0],
            'exact_canary_group_zero')
    remaining = assessment['groups'][1:]
    paths = [path for group in remaining for path in group_paths(group)]
    require(len(paths) == len(set(paths)) == 4112 and not excluded.intersection(paths),
            'exact_514_groups_disjoint_from_canary')
    batches = []
    for offset in range(0, len(remaining), 5):
        batch = deepcopy(canary)
        groups = remaining[offset:offset + 5]
        batch.update(schema='NODE2_REMAINING_LOCK_HELD_BATCH_PROPOSAL_V1', ordinal=len(batches) + 1,
                     groups=groups, max_paths=sum(len(group_paths(group)) for group in groups),
                     execution_status='REQUIRES_NEW_MAIN_MANIFEST_BINDING',
                     completed_canary_receipt_sha256=CANARY_RECEIPT_SHA,
                     excluded_canary_canonical_sha256=frozen.CANARY_SHA)
        require(batch['max_paths'] <= 40 and all(group['selection_index'] != 0 for group in groups),
                'bounded_batch_canary_excluded')
        batches.append(batch)
    require(len(batches) == 103, 'exact_bounded_remaining_count')
    return batches


def write_once(path, raw):
    with path.open('xb') as target:
        target.write(raw)
        target.flush()
        os.fsync(target.fileno())
    frozen.fsync_directory(path.parent)


def main():
    proof = local_proof()
    frozen.require(proof['receipt_sha256'] == CANARY_RECEIPT_SHA, 'exact_canary_receipt')
    artifacts = frozen.frozen_artifacts()
    completion = json.loads((FROZEN / 'CANARY_EXECUTION/VERIFIED.json').read_bytes())
    batches = plan_batches(json.loads(artifacts['GROUPS.json']), json.loads(artifacts['CANARY.json']), completion)
    entries = []
    for batch in batches:
        name = f"BATCH_{batch['ordinal']:04d}.json"
        raw = canonical_bytes(batch)
        write_once(HERE / name, raw)
        entries.append(dict(path=name, ordinal=batch['ordinal'], sha256=frozen.sha(raw), groups=len(batch['groups']),
                            paths=batch['max_paths'], replacements=sum(len(inode['paths']) for group in batch['groups']
                            for inode in group['replacement_inodes']), potential_allocated_bytes=sum(
                            group['potential_allocated_bytes_freed'] for group in batch['groups'])))
    manifest = dict(schema='NODE2_REMAINING_EXACT_MANIFEST_V1', status='PREPARED_NOT_AUTHORIZED_OR_EXECUTED',
                    source_review_sha256=frozen.REVIEW_SHA, frozen_transport_sha256=TRANSPORT_SHA,
                    completed_canary=proof, excluded_canary_canonical_sha256=frozen.CANARY_SHA,
                    writer_locks_sha256=json.loads(artifacts['CANARY.json'])['writer_locks_sha256'],
                    source_files={name: frozen.sha((HERE / name).read_bytes()) for name in CODE_FILES},
                    batches=entries, batch_count=len(entries), groups=514, paths=4112, replacements=3084,
                    max_paths_per_batch=40, potential_allocated_bytes=sum(row['potential_allocated_bytes'] for row in entries),
                    execution_directory=str(HERE / 'EXECUTION'),
                    ledger_pattern=str(HERE / 'EXECUTION/BATCH_NNNN/LEDGER.jsonl'),
                    no_automatic_retry=True, no_automatic_rollback=True,
                    gpu_or_native_actions=False, canary_reexecution=False,
                    c0_launch_authorized=False, original_archive_retained=True)
    write_once(HERE / 'MANIFEST.json', canonical_bytes(manifest))
    print(json.dumps(dict(manifest_sha256=frozen.sha(canonical_bytes(manifest)),
                          batch_count=103, groups=514, paths=4112, replacements=3084,
                          potential_allocated_bytes=manifest['potential_allocated_bytes']), sort_keys=True))


if __name__ == '__main__':
    main()
