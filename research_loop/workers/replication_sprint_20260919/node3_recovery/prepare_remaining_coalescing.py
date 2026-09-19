"""Propose bounded remaining batches after the exact canary; never execute them."""

from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path

from assess_hardlinks import require
from prepare_coalescing_canary import ASSESSMENT_SHA256, file_pin
from retired_coalescer import digest
from run_approved_canary import APPROVED_SHA256


HERE = Path(__file__).resolve().parent


def group_paths(group):
    return [entry['path'] for inode in [group['canonical'], *group['replacement_inodes']]
        for entry in inode['paths']]


def partition_remaining(assessment, canary, completion):
    require(digest(canary) == APPROVED_SHA256, 'exact_authorized_canary')
    require(completion['status'] == 'CANARY_COMPLETE_ALL_PATHS_VERIFIED'
        and completion['ssh_exit'] == 0 and completion['batch_sha256'] == APPROVED_SHA256,
        'verified_canary_completion_required')
    result = completion['result']
    expected_paths = {path for group in canary['groups'] for path in group_paths(group)}
    require(len(expected_paths) == 9 and result['replacements'] == 6
        and {entry['path'] for entry in result['verified_paths']} == expected_paths,
        'all_nine_canary_paths_and_six_replacements')
    completed_groups = {digest(group) for group in canary['groups']}
    require(completed_groups <= {digest(group) for group in assessment['groups']},
        'canary_was_from_reviewed_eligibility')
    remaining = [group for group in assessment['groups'] if digest(group) not in completed_groups]
    ordered = sorted(remaining, key=lambda group:
        (-group['potential_allocated_bytes_freed'], group['canonical']['paths'][0]['path']))
    chunks, current = [], []
    current_size = 0
    for group in ordered:
        paths = group_paths(group)
        require(len(paths) <= 40 and not expected_paths.intersection(paths), 'remaining_groups_disjoint_and_bounded')
        if current_size + len(paths) > 40:
            chunks.append(current)
            current, current_size = [], 0
        current.append(deepcopy(group))
        current_size += len(paths)
    if current:
        chunks.append(current)
    all_paths = [path for chunk in chunks for group in chunk for path in group_paths(group)]
    require(len(all_paths) == len(set(all_paths)), 'no_path_reused_between_batches')
    require(sum(group['potential_allocated_bytes_freed'] for chunk in chunks for group in chunk)
        + sum(group['potential_allocated_bytes_freed'] for group in canary['groups'])
        == assessment['eligible_allocated_bytes_potential'], 'complete_original_allocation_accounting')
    return chunks


def write_once(path, value):
    encoded = json.dumps(value, sort_keys=True, separators=(',', ':')).encode()
    with path.open('xb') as output:
        output.write(encoded)
        output.flush()
        os.fsync(output.fileno())
    descriptor = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)
    return hashlib.sha256(encoded).hexdigest()


def main():
    require(file_pin('HARDLINK_ELIGIBLE_PATHS.json')['sha256'] == ASSESSMENT_SHA256,
        'unchanged_original_assessment')
    assessment = json.loads((HERE / 'HARDLINK_ELIGIBLE_PATHS.json').read_bytes())
    canary = json.loads((HERE / 'HARDLINK_CANARY_PROPOSAL.json').read_bytes())
    completion = json.loads((HERE / 'CANARY_EXECUTION_VERIFIED.json').read_bytes())
    chunks = partition_remaining(assessment, canary, completion)
    for entry in canary['source_code_and_tests']:
        require(file_pin(entry['path'])['sha256'] == entry['sha256'], 'reviewed_code_changed')
    destination = HERE / 'remaining_coalescing_proposal'
    destination.mkdir(exist_ok=False)
    records = []
    for ordinal, groups in enumerate(chunks, start=1):
        batch = deepcopy(canary)
        batch.update(schema='NODE3_RETIRED_REMAINING_BATCH_PROPOSAL_V1',
            execution_status='REQUIRES_SEPARATE_MAIN_REVIEW', ordinal=ordinal, groups=groups,
            max_paths=sum(len(group_paths(group)) for group in groups),
            completed_canary=file_pin('CANARY_EXECUTION_VERIFIED.json'),
            canary_ledger=file_pin('CANARY_EXECUTION_LEDGER.jsonl'),
            fresh_backup_recheck=file_pin('CANARY_BACKUP_RECHECK.json'))
        path = destination / f'BATCH_{ordinal:04d}.json'
        checksum = write_once(path, batch)
        require(checksum == digest(batch), 'exact_batch_file_hash')
        records.append(dict(ordinal=ordinal, path=str(path.relative_to(HERE)), sha256=checksum,
            groups=len(groups), paths=batch['max_paths'],
            replacements=sum(len(inode['paths']) for group in groups for inode in group['replacement_inodes']),
            potential_allocated_bytes=sum(group['potential_allocated_bytes_freed'] for group in groups)))
    index = dict(schema='NODE3_RETIRED_REMAINING_BATCHES_REVIEW_V1',
        utc=datetime.now(timezone.utc).isoformat(), status='PROPOSAL_ONLY_NOT_AUTHORIZED_OR_EXECUTED',
        source_manifest_sha256=canary['source_manifest_sha256'],
        original_eligibility=file_pin('HARDLINK_ELIGIBLE_PATHS.json'),
        completed_canary=file_pin('CANARY_EXECUTION_VERIFIED.json'),
        excluded_completed_canary_sha256=APPROVED_SHA256,
        archive_sha256=canary['archive_sha256'], archive_destination=canary['archive_destination'],
        coalescer_source=file_pin('retired_coalescer.py'),
        proposal_builder=file_pin('prepare_remaining_coalescing.py'),
        proposal_builder_tests=file_pin('test_prepare_remaining_coalescing.py'),
        proposal_cpu_evidence=file_pin('CPU_TESTS_REMAINING_PROPOSAL.txt'),
        batches=records, batch_count=len(records), max_paths_per_batch=40,
        groups=sum(entry['groups'] for entry in records), paths=sum(entry['paths'] for entry in records),
        replacements=sum(entry['replacements'] for entry in records),
        potential_allocated_bytes=sum(entry['potential_allocated_bytes'] for entry in records),
        ordering='descending allocated savings per indivisible group, canonical-path tie break',
        actual_remaining_batches_executed=0, current_owner_available_bytes=completion['result']['owner_available_bytes_after'],
        required_before_execution=['Main approval of exact selected batch hashes or this exact index',
            'fresh hash/metadata/link/writer checks for every original path',
            'durable remote acknowledgements and halt on any error',
            'retain verified archive/manifest and all original paths'],
        note='These proposals neither launch recovery nor relax original admission, confinement, lease, or pending-sleep requirements.')
    checksum = write_once(HERE / 'HARDLINK_REMAINING_PROPOSAL.json', index)
    print(json.dumps(dict(status=index['status'], index_sha256=checksum,
        index_path='HARDLINK_REMAINING_PROPOSAL.json', batch_count=len(records),
        groups=index['groups'], paths=index['paths'], replacements=index['replacements'],
        potential_allocated_bytes=index['potential_allocated_bytes'], first_three_batches=records[:3]), indent=2))


if __name__ == '__main__':
    main()
