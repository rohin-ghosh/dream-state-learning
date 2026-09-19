"""Small production-proof receipts and supplementary old-native filesystem checks."""

import json
import os
from pathlib import Path
import time

from remote_epoch4_stage import checksum, exact_native, read, require
from node_epoch4_probe import write_once
import native_view_probe as view


def source_object_view(proof, pid):
    root_descriptor = os.open(f'/proc/{pid}/root', os.O_RDONLY | os.O_DIRECTORY)
    try:
        for snapshot in proof['source_objects']['files']:
            path = Path(snapshot['path'])
            descriptor, chain = view.open_directory(root_descriptor, path.parent)
            try:
                require(chain == snapshot['chain'] and view.file_identity(os.stat(path.name,
                    dir_fd=descriptor, follow_symlinks=False)) == snapshot['identity'], 'same_each_source_and_epoch_object')
            finally:
                os.close(descriptor)
        for snapshot in proof['source_objects']['directories']:
            descriptor, chain = view.open_directory(root_descriptor, snapshot['path'])
            try:
                value = os.fstat(descriptor)
                identity = dict(zip(view.FILE_FIELDS, (value.st_dev, value.st_ino, value.st_size,
                    value.st_mtime_ns, value.st_ctime_ns, value.st_mode, value.st_nlink)))
                require(chain == snapshot['chain'] and identity == snapshot['identity'],
                    'same_each_immutable_source_directory')
            finally:
                os.close(descriptor)
    finally:
        os.close(root_descriptor)
    return dict(source_and_epoch_objects=len(proof['source_objects']['files']),
        immutable_source_directories=len(proof['source_objects']['directories']))


def finalize(request):
    require(os.environ.get('CUDA_VISIBLE_DEVICES') == '', 'CPU_only_receipt_audit')
    root = Path(request['checks_root'])
    observations = read(root / 'OBSERVATIONS.json')
    results = {}
    for life, observation in observations.items():
        before = exact_native(observation)
        directory = root / life
        produced = read(sorted(directory.glob('produce_*/RECEIPT.json'))[-1])['results'][0]['result']
        require(produced['status'] == 'CANDIDATE_NOT_AUTHORIZATION' and produced['journal_writes'] == 0,
            'actual_candidate_producer_receipt')
        producer_receipt = directory / 'PRODUCED.json'
        producer_receipt_sha = write_once(producer_receipt, produced)
        proof_raw = Path(produced['proof_path']).read_bytes()
        require(checksum(proof_raw) == produced['proof_sha256'], 'unchanged_original_production_proof')
        proof = json.loads(proof_raw)
        require(proof['binding']['source']['root'] == produced['source']
            and proof['binding']['journal_type'] == produced['family']['journal_type'], 'own_production_source_and_family')
        started = time.monotonic()
        object_view = source_object_view(proof, observation['native']['pid'])
        source_object_view(proof, observation['native']['pid'])
        object_view['seconds'] = time.monotonic() - started
        selected_ids = {record['inbox_document']['message']['id'] for record in proof['records']
            if record['header']['kind'] == 'INBOX'}
        scanned = read(sorted(directory.glob('read_*/RECEIPT.json'))[-1])['results'][0]['result']
        require(scanned['status'] == 'PRODUCTION_SOURCE_DIAGNOSTIC_READ_NOT_HANDOFF', 'successful_real_scan')
        results[life] = dict(producer_receipt=dict(path=str(producer_receipt), sha256=producer_receipt_sha),
            proof=dict(path=produced['proof_path'], sha256=produced['proof_sha256']),
            source_epoch=proof['binding']['source']['epoch'], selected_complete=proof['binding']['selection']['complete_index'],
            original_prefix_INBOX_registered=len(selected_ids), scanned_INBOX_registered=scanned['inbox_registered_count'],
            new_tail_INBOX_registered=scanned['inbox_registered_count'] - len(selected_ids),
            new_INBOX_files_during_scan=scanned['new_INBOX_file_count'],
            all_existing_INBOX_files_preserved=scanned['original_INBOX_files_unchanged'],
            sidecars=scanned['receipt']['sidecars'], supplementary_old_native_object_view=object_view,
            before=before, after=exact_native(observation), original_native_source_guard_unchanged=True,
            namespace_mode_used=scanned['receipt']['prefix_proof']['consumer_context']['mode'],
            new_consumer_admission_proven=False)
    receipt = dict(status='PAIR_PRODUCTION_SOURCE_PROOFS_AND_READS_NOT_ADMISSION', results=results,
        observed_unix=time.time(), native_signals=[], parent_actions=[], reservations=[], GPU_calls=0,
        journal_writes=0, full_proof_or_journal_transferred=False, receiving_admission_proven=False)
    write_once(root / 'FINAL_READONLY_RECEIPT.json', receipt)
    return receipt
