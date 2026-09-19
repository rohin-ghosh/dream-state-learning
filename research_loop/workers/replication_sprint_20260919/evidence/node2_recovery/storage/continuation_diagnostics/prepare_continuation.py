"""Prepare exact original batches 9-103; preserve and exclude every completed group."""

from collections import Counter
import json
from pathlib import Path
import sys


HERE = Path(__file__).resolve().parent
PRIOR = HERE.parent / 'coalescence_remaining'
sys.path.insert(0, str(PRIOR))
import run_remaining as prior
from prepare_remaining import canonical_bytes, write_once
from verify_completed_canary import FROZEN, frozen, local_proof


ORIGINAL_MANIFEST_SHA = 'c2459e89f63bfb2edad0c8d1f626e963a86d9a547a2a5884969cd9e41c14f9a1'
ORIGINAL_RUNNER_SHA = '1772f50e1909ab9559e331554e141ed951e4d1bc19d887da2a93d6c16d250b93'
POLICY = 'DURABLE_RAW_SCAN_BEFORE_UNCHANGED_ADMISSION_V1'
CODE_FILES = ('scan_receipt.py', 'prepare_continuation.py', 'run_continuation.py', 'test_scan_receipt.py', 'test_continuation.py')
RAW_DIAGNOSIS = 'RAW_SCAN_20260919T154546_585004Z.json'
RAW_DIAGNOSIS_SHA = '6bc14bdc362375dec3c8ec9f54cdf8b75b0a3f1cedec08ce0545ee030353a42b'


def checked_chain(raw):
    events = [json.loads(line) for line in raw.splitlines()]
    previous = '0' * 64
    for ordinal, event in enumerate(events):
        unsigned = {key: value for key, value in event.items() if key != 'sha256'}
        checksum = frozen.sha(canonical_bytes(unsigned))
        frozen.require(event['sequence'] == ordinal and event['previous_sha256'] == previous
                       and event['sha256'] == checksum, 'exact_original_execution_chain')
        previous = checksum
    return events, previous


def original_state():
    artifacts, manifest, checksum, batches = prior.load_prepared()
    require = frozen.require
    require(checksum == ORIGINAL_MANIFEST_SHA and frozen.sha((PRIOR / 'run_remaining.py').read_bytes()) == ORIGINAL_RUNNER_SHA,
            'unchanged_previous_scope_and_runner')
    completed = []
    for entry, batch in zip(manifest['batches'][:8], batches[:8]):
        directory = PRIOR / 'EXECUTION' / f"BATCH_{entry['ordinal']:04d}"
        raw = (directory / 'VERIFIED.json').read_bytes()
        receipt = json.loads(raw)
        ledger_raw = (directory / 'LEDGER.jsonl').read_bytes()
        events, chain = checked_chain(ledger_raw)
        require(receipt['ssh_exit'] == 0 and receipt['batch_sha256'] == entry['sha256']
                and receipt['ledger_records'] == len(events) and receipt['ledger_sha256'] == chain
                and receipt['completion'] == events[-1]
                and events[-1]['kind'] == 'REMAINING_BATCH_COMPLETE_ALL_PATHS_VERIFIED', 'completed_batch_must_never_replay')
        expected_paths = {row['path'] for group in batch['groups'] for inode in [group['canonical'], *group['replacement_inodes']]
                          for row in inode['paths']}
        document = events[-1]['document']
        require(len(document['paths']) == len(expected_paths) == entry['paths']
                and {row['path'] for row in document['paths']} == expected_paths
                and document['replacements'] == entry['replacements'], 'all_completed_paths_verified')
        completed.append(dict(ordinal=entry['ordinal'], batch_sha256=entry['sha256'],
                              receipt_sha256=frozen.sha(raw), ledger_raw_sha256=frozen.sha(ledger_raw), final_chain=chain,
                              excluded_selection_indices=[group['selection_index'] for group in batch['groups']]))
    failed_directory = PRIOR / 'EXECUTION/BATCH_0009'
    failed = {name: frozen.sha((failed_directory / name).read_bytes())
              for name in ['LEDGER.jsonl', 'HALTED.json', 'DERIVED_BINDING.json', 'SSH.stderr']}
    events, failed_chain = checked_chain((failed_directory / 'LEDGER.jsonl').read_bytes())
    require(len(events) == 2 and events[-1]['kind'] == 'BATCH_REJECTED_NO_MUTATION'
            and events[-1]['document']['stage'] == 'ADMISSION'
            and events[-1]['document']['batch_sha256'] == manifest['batches'][8]['sha256'], 'original_batch9_admission_only_failure')
    diagnosis_raw = (HERE.parent / 'batch9_diagnosis' / RAW_DIAGNOSIS).read_bytes()
    require(frozen.sha(diagnosis_raw) == RAW_DIAGNOSIS_SHA, 'exact_fresh_readonly_identity_evidence')
    diagnosis = json.loads(diagnosis_raw)
    require(diagnosis['all_target_metadata_unchanged'] is True and diagnosis['coalescence_attempted'] is False,
            'diagnosis_is_not_historical_success')
    proof = dict(completed_canary=local_proof(), completed_batches=completed, failed_batch9_artifacts=failed,
                 failed_batch9_final_chain=failed_chain, fresh_readonly_diagnosis_sha256=RAW_DIAGNOSIS_SHA,
                 fresh_diagnostics_do_not_recover_original_failed_scan=True)
    return artifacts, manifest, batches, proof


def selected_remaining(manifest, batches):
    entries = manifest['batches'][8:]
    selected = batches[8:]
    frozen.require(len(entries) == len(selected) == 95
                   and [entry['ordinal'] for entry in entries] == list(range(9, 104)), 'exact_original_batches_9_through_103')
    indices = [group['selection_index'] for batch in selected for group in batch['groups']]
    frozen.require(indices == list(range(41, 515)), 'permanent_exclusion_canary_and_completed_1_through_8')
    return entries, selected


def main():
    unused_artifacts, previous, batches, proof = original_state()
    entries, selected = selected_remaining(previous, batches)
    for entry, batch in zip(entries, selected):
        raw = (PRIOR / entry['path']).read_bytes()
        frozen.require(raw == canonical_bytes(batch) and frozen.sha(raw) == entry['sha256'], 'byte_identical_original_pending_batch')
        write_once(HERE / entry['path'], raw)
    manifest = dict(schema='NODE2_DIAGNOSTIC_CONTINUATION_V1', status='PREPARED_NOT_AUTHORIZED',
                    repair_class='NON_MATERIAL_DIAGNOSTIC_PRESERVATION_ONLY', policy=POLICY,
                    original_manifest_sha256=ORIGINAL_MANIFEST_SHA, original_runner_sha256=ORIGINAL_RUNNER_SHA,
                    source_review_sha256=frozen.REVIEW_SHA, unchanged_original_scanner_and_predicate=True,
                    unchanged_original_locks_path_content_metadata_guards=True, archive_scope_unchanged=True,
                    permanent_excluded_selection_indices=list(range(41)), excluded_original_batch_ordinals=list(range(1, 9)),
                    provenance=proof, source_files={name: frozen.sha((HERE / name).read_bytes()) for name in CODE_FILES},
                    batches=entries, first_original_ordinal=9, last_original_ordinal=103, batch_count=95,
                    groups=474, paths=3792, replacements=2844, max_paths_per_batch=40,
                    potential_allocated_bytes=sum(entry['potential_allocated_bytes'] for entry in entries),
                    execution_directory=str(HERE / 'EXECUTION'), no_automatic_retry=True, no_automatic_rollback=True,
                    first_error_halts=True, diagnostic_ledger_failure_blocks=True, c0_launch_authorized=False)
    raw = canonical_bytes(manifest)
    write_once(HERE / 'MANIFEST.json', raw)
    print(json.dumps(dict(manifest_sha256=frozen.sha(raw), batches=95, groups=474, paths=3792,
                         replacements=2844, potential_allocated_bytes=manifest['potential_allocated_bytes']), sort_keys=True))


if __name__ == '__main__':
    main()
