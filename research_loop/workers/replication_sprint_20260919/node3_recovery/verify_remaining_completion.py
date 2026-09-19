"""Independently reconcile final retired-only receipts with the authorized index."""

from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path

from retired_coalescer import digest
from run_approved_remaining import INDEX_SHA256, load_payload


HERE = Path(__file__).resolve().parent


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def verify_chain(path):
    previous = '0' * 64
    counts = Counter()
    postchecks = {}
    last = None
    sequence = 0
    with path.open() as source:
        for line in source:
            entry = json.loads(line)
            require(entry['sequence'] == sequence and entry['previous_sha256'] == previous,
                'contiguous_durable_ledger')
            require(entry['sha256'] == digest({key: value for key, value in entry.items()
                if key != 'sha256'}), 'durable_event_content_hash')
            if entry['kind'] == 'REMAINING_BATCH_POSTCHECK':
                ordinal = entry['document']['ordinal']
                require(ordinal not in postchecks, 'no_duplicate_batch_postchecks')
                postchecks[ordinal] = entry
            counts[entry['kind']] += 1
            sequence += 1
            previous = entry['sha256']
            last = entry
    return dict(previous=previous, counts=counts, postchecks=postchecks, last=last, sequence=sequence)


def main():
    payload = load_payload()
    require(not (HERE / 'REMAINING_EXECUTION_HALTED.json').exists(), 'halted_execution_requires_review')
    receipt_path = HERE / 'REMAINING_EXECUTION_VERIFIED.json'
    receipt = json.loads(receipt_path.read_bytes())
    require(receipt['status'] == 'REMAINING_COMPLETE_ALL_PATHS_VERIFIED'
        and receipt['index_sha256'] == INDEX_SHA256 and receipt['ssh_exit'] == 0,
        'actual_success_not_cumulative_progress')
    chain = verify_chain(HERE / 'REMAINING_EXECUTION_LEDGER.jsonl')
    require(chain['sequence'] == receipt['ledger_records']
        and chain['previous'] == receipt['ledger_final_sha256'], 'exact_final_durable_receipt')
    require(chain['last']['kind'] == receipt['status']
        and chain['last']['document'] == receipt['result'], 'final_all_path_receipt_matches_ledger')
    require(chain['counts']['REPLACEMENT_VERIFIED'] == 3189
        and chain['counts']['REMAINING_BATCH_POSTCHECK'] == 125
        and chain['counts']['REMAINING_HALTED_NO_RETRY'] == 0, 'all_expected_operations_verified')
    require(set(chain['postchecks']) == set(range(1, 126)), 'all_exact_batch_ordinals')
    final = receipt['result']
    require(final['verified_remaining_paths'] == 4845 and final['verified_prior_canary_paths'] == 9
        and final['original_paths_removed'] == 0
        and final['file_content_or_required_metadata_changed'] is False, 'all_path_integrity_not_counts_only')
    final_batches = {document['ordinal']: document for document in final['final_batch_verifications']}
    require(len(final_batches) == 125, 'exact_final_batch_verifications')
    for binding in payload['index']['batches']:
        ordinal = binding['ordinal']
        postcheck = chain['postchecks'][ordinal]
        saved = json.loads((HERE / 'remaining_execution_receipts' / f'BATCH_{ordinal:04d}_VERIFIED.json').read_bytes())
        require(saved == postcheck and saved['document']['batch_sha256'] == binding['sha256'],
            'postchecks_bound_to_authorized_batch')
        document = saved['document']
        require(document['replacements'] == binding['replacements'], 'authorized_replacements_only')
        require(digest(document['verified_paths']) == document['verified_paths_sha256'],
            'full_postcheck_path_document_hash')
        require(final_batches[ordinal]['verified_paths_sha256'] == document['verified_paths_sha256']
            and final_batches[ordinal]['path_count'] == document['path_count'],
            'final_all_path_reverification_matches_original_postcheck')
    output = dict(utc=datetime.now(timezone.utc).isoformat(),
        status='INDEPENDENT_LOCAL_FINAL_LEDGER_AND_ALL_PATH_RECEIPTS_VERIFIED',
        index_sha256=INDEX_SHA256, ledger_records=chain['sequence'],
        ledger_final_sha256=chain['previous'], final_receipt_sha256=hashlib.sha256(receipt_path.read_bytes()).hexdigest(),
        batches=125, remaining_replacements=3189, remaining_paths=4845, prior_canary_paths=9,
        owner_available_bytes=final['owner_available_bytes_after'],
        owner_available_blocks=final['owner_available_blocks_after'],
        filesystem_block_bytes=final['filesystem_block_bytes'],
        observed_filesystem_free_delta=final['filesystem_free_bytes_delta'],
        inode_allocations_replaced=final['confirmed_replaced_inode_allocated_bytes'],
        original_pathnames_removed=0, namespace_or_GPU_operations=False,
        scope='All reviewed coalesced paths rehashed remotely; this is not a second full archive restoration.')
    with (HERE / 'REMAINING_COMPLETION_INDEPENDENT_AUDIT.json').open('x') as stream:
        json.dump(output, stream, sort_keys=True, indent=2)
        stream.flush()
        os.fsync(stream.fileno())
    print(json.dumps(output, sort_keys=True))


if __name__ == '__main__':
    main()
