"""Create a hash-bound proposal only; no source-node mutation or execution approval."""

from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path

from assess_hardlinks import ROOT, require
from retired_coalescer import digest


HERE = Path(__file__).resolve().parent
SOURCE_MANIFEST_SHA256 = '9086338288c21d3100d6312e9a5ec4a828b3f1acda5737dc1c99c2ccae438268'
ASSESSMENT_SHA256 = 'bc567674a60cce3eec9dc66d48399477f018c6d085755e7e5ea545bd30ee9c73'
ARCHIVE_SHA256 = '7861165f2b5235352c92cf22ab894482c4c63a62dcb4d7f1d0435cbea69dacc9'
DESTINATION = '/localhome/local-rohing/node3_retired_archive_copy_20260919T133405Z_ws6'


def select_canary(assessment, copy_receipt, restore_receipt):
    require(assessment['manifest_sha256'] == SOURCE_MANIFEST_SHA256,
        'exact_reviewed_source_manifest')
    require(copy_receipt['status'] == 'ALL_ARCHIVE_MEMBERS_STREAM_RESTORED_AND_VERIFIED'
        and copy_receipt['manifest_sha256'].split()[0] == SOURCE_MANIFEST_SHA256
        and copy_receipt['archive_sha256'].split()[0] == ARCHIVE_SHA256
        and copy_receipt['destination_root'] == DESTINATION,
        'exact_verified_archive_copy')
    require(restore_receipt['status'] == 'FULL_FILESYSTEM_RESTORE_BYTES_LINKS_MODE_MTIME_XATTRS_VERIFIED'
        and restore_receipt['root'] == DESTINATION
        and restore_receipt['members'] == copy_receipt['members'] == assessment['manifest_rows']
        and restore_receipt['source_root_untouched'] is True
        and restore_receipt['source_delete_or_remap'] is False,
        'full_filesystem_restore_required')
    ordered = sorted(assessment['groups'], key=lambda group:
        (group['metadata']['size'], group['canonical']['paths'][0]['path']))
    require(len(ordered) >= 3, 'three_reviewed_groups_required')
    selected = deepcopy(ordered[:3])
    paths = [entry['path'] for group in selected
        for inode in [group['canonical'], *group['replacement_inodes']] for entry in inode['paths']]
    require(len(paths) == len(set(paths)) <= 40, 'bounded_unique_canary_paths')
    require(all(inode['links_outside_eligible_set'] == 0 for group in selected
        for inode in [group['canonical'], *group['replacement_inodes']]), 'no_external_links')
    return selected


def file_pin(name):
    payload = (HERE / name).read_bytes()
    return dict(path=name, bytes=len(payload), sha256=hashlib.sha256(payload).hexdigest())


def write_once(name, value):
    payload = json.dumps(value, sort_keys=True, separators=(',', ':')).encode()
    with (HERE / name).open('xb') as output:
        output.write(payload)
        output.flush()
        os.fsync(output.fileno())
    descriptor = os.open(HERE, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)
    return hashlib.sha256(payload).hexdigest()


def main():
    assessment = json.loads((HERE / 'HARDLINK_ELIGIBLE_PATHS.json').read_bytes())
    require(file_pin('HARDLINK_ELIGIBLE_PATHS.json')['sha256'] == ASSESSMENT_SHA256,
        'reviewed_eligibility_bytes_unchanged')
    copy_receipt = json.loads((HERE / 'ARCHIVE_COPY_VERIFIED.json').read_bytes())
    restore_receipt = json.loads((HERE / 'ARCHIVE_FULL_RESTORE_VERIFIED.json').read_bytes())
    groups = select_canary(assessment, copy_receipt, restore_receipt)
    cpu_name = 'CPU_TESTS_FINAL_IMPLEMENTATION.txt'
    require((HERE / cpu_name).read_text().rstrip().endswith('\nOK'), 'successful_cpu_test_receipt_required')
    source_names = ['retired_coalescer.py', 'assess_hardlinks.py', 'prepare_coalescing_canary.py',
        'test_retired_coalescer.py', 'test_assess_hardlinks.py', 'test_prepare_coalescing_canary.py']
    paths = [entry['path'] for group in groups
        for inode in [group['canonical'], *group['replacement_inodes']] for entry in inode['paths']]
    batch = dict(schema='NODE3_RETIRED_CANARY_PROPOSAL_V1',
        execution_status='REQUIRES_SEPARATE_MAIN_REVIEW', archive_verified=True,
        filesystem_restore_verified=True, source_manifest_sha256=SOURCE_MANIFEST_SHA256,
        eligible_assessment=file_pin('HARDLINK_ELIGIBLE_PATHS.json'),
        root=str(ROOT), original_host='ipp2-ovx-p6-09', original_uid=2524,
        archive_destination=DESTINATION, archive_sha256=ARCHIVE_SHA256,
        archive_copy_receipt=file_pin('ARCHIVE_COPY_VERIFIED.json'),
        archive_full_restore_receipt=file_pin('ARCHIVE_FULL_RESTORE_VERIFIED.json'),
        source_code_and_tests=[file_pin(name) for name in source_names],
        cpu_evidence=file_pin(cpu_name), accepted_metadata_differences=['inode', 'ctime', 'nlink', 'atime'],
        groups=groups, max_paths=len(paths),
        ledger_policy='remote worker waits for VM/destination fsync acknowledgement before each mutation',
        original_owner_metadata='preserved in verified archive and source manifest; destination owner differs',
        automatic_retry=False, automatic_rollback=False)
    checksum = write_once('HARDLINK_CANARY_PROPOSAL.json', batch)
    require(checksum == digest(batch), 'file_hash_equals_canonical_batch_hash')
    review = dict(status='IMPLEMENTED_AND_CPU_TESTED_NOT_APPROVED_FOR_EXECUTION',
        utc=datetime.now(timezone.utc).isoformat(), proposal_sha256=checksum,
        proposal_path='HARDLINK_CANARY_PROPOSAL.json', groups=len(groups), paths=len(paths),
        replacements=sum(len(inode['paths']) for group in groups for inode in group['replacement_inodes']),
        potential_allocated_bytes=sum(group['potential_allocated_bytes_freed'] for group in groups),
        source_manifest_sha256=SOURCE_MANIFEST_SHA256, eligible_assessment_sha256=ASSESSMENT_SHA256,
        archive_sha256=ARCHIVE_SHA256, archive_destination=DESTINATION,
        source_mutations=0, reclaimed_bytes=0,
        execution_requires='Main review of exact proposal hash after complete archive and full restore',
        cpu_evidence=batch['cpu_evidence'])
    write_once('HARDLINK_CANARY_REVIEW.json', review)
    print(json.dumps(review, indent=2, sort_keys=True))


if __name__ == '__main__':
    main()
