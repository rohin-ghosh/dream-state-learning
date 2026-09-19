"""Fresh Main-bound continuation of original batches 9-103, diagnostic repair only."""

import argparse
import base64
import json
from pathlib import Path
import subprocess

from prepare_continuation import CODE_FILES, FROZEN, HERE, ORIGINAL_MANIFEST_SHA, POLICY, canonical_bytes, frozen, original_state, prior, selected_remaining, write_once


OUTPUT = HERE / 'EXECUTION'
OLD_CALL = 'result=execute_batch(batch,expected_sha256=approved_sha256,root=ROOT,ledger=ledger,approval=approval)'
NEW_CALL = '''from scan_receipt import scan_with_receipt
result=execute_batch(batch,expected_sha256=approved_sha256,root=ROOT,ledger=ledger,approval=approval,
    writer_scan=lambda paths: scan_with_receipt(paths,ledger,approved_sha256))'''


def load_prepared():
    artifacts, original_manifest, original_batches, proof = original_state()
    entries, batches = selected_remaining(original_manifest, original_batches)
    raw = (HERE / 'MANIFEST.json').read_bytes()
    manifest = json.loads(raw)
    require = frozen.require
    require(raw == canonical_bytes(manifest) and manifest['original_manifest_sha256'] == ORIGINAL_MANIFEST_SHA
            and manifest['provenance'] == proof and manifest['batches'] == entries, 'exact_continuation_provenance_and_scope')
    require(manifest['policy'] == POLICY and manifest['permanent_excluded_selection_indices'] == list(range(41))
            and manifest['excluded_original_batch_ordinals'] == list(range(1, 9))
            and manifest['batch_count'] == 95 and manifest['groups'] == 474
            and manifest['paths'] == 3792 and manifest['replacements'] == 2844
            and manifest['execution_directory'] == str(OUTPUT), 'permanent_completed_exclusions_and_new_directory')
    require(set(manifest['source_files']) == set(CODE_FILES), 'exact_diagnostic_candidate_source_set')
    for name, checksum in manifest['source_files'].items():
        require(frozen.sha((HERE / name).read_bytes()) == checksum, 'continuation_source_changed:' + name)
    for entry, batch in zip(entries, batches):
        raw_batch = (HERE / entry['path']).read_bytes()
        require(raw_batch == canonical_bytes(batch) and frozen.sha(raw_batch) == entry['sha256'], 'unchanged_original_pending_batch_bytes')
    return artifacts, manifest, frozen.sha(raw), batches


def binding_template(manifest_sha):
    return dict(status='AWAITING_MAIN_BINDING_NOT_AUTHORIZED', manifest_sha256=manifest_sha,
                runner_sha256=frozen.sha(Path(__file__).read_bytes()),
                diagnostic_source_sha256=frozen.sha((HERE / 'scan_receipt.py').read_bytes()),
                original_manifest_sha256=ORIGINAL_MANIFEST_SHA, source_review_sha256=frozen.REVIEW_SHA,
                policy=POLICY, execution_scope='EXACT_ORIGINAL_BATCHES_9_THROUGH_103_ONLY',
                permanently_excluded_selection_indices=list(range(41)), batch_count=95,
                first_original_ordinal=9, last_original_ordinal=103, groups=474, paths=3792, replacements=2844,
                max_paths_per_batch=40, execution_directory=str(OUTPUT),
                no_automatic_retry=True, no_automatic_rollback=True, first_error_halts=True)


def validate_binding(raw, manifest_sha):
    binding = json.loads(raw)
    expected = dict(binding_template(manifest_sha), status='MAIN_REVIEWED_EXECUTION')
    frozen.require(all(key in binding and type(binding[key]) is type(value) and binding[key] == value
                       for key, value in expected.items()), 'fresh_Main_exact_diagnostic_continuation_binding_required')
    return binding


def remote_program(artifacts, batch, approval):
    frozen.require(9 <= batch['ordinal'] <= 103 and all(group['selection_index'] >= 41 for group in batch['groups']),
                   'no_completed_batch_or_canary_in_receiving_program')
    program = frozen.module_loader(artifacts)
    encoded = base64.b64encode((HERE / 'scan_receipt.py').read_bytes()).decode()
    program += 'module=types.ModuleType("scan_receipt");module.__file__="scan_receipt.py";sys.modules["scan_receipt"]=module\n'
    program += f'exec(compile(base64.b64decode({encoded!r}),module.__file__,"exec"),module.__dict__)\n'
    for name, value in [('batch', batch), ('approval', approval)]:
        encoded = base64.b64encode(canonical_bytes(value)).decode()
        program += f'{name}=json.loads(base64.b64decode({encoded!r}))\n'
    frozen.require(prior.REMOTE.count(OLD_CALL) == 1, 'exact_original_receiving_call_seam')
    return program + f"approved_sha256={approval['batch_sha256']!r}\n" + prior.REMOTE.replace(OLD_CALL, NEW_CALL)


def run(binding_path):
    artifacts, manifest, checksum, batches = load_prepared()
    binding_raw = Path(binding_path).read_bytes()
    binding = validate_binding(binding_raw, checksum)
    from retired_coalescer import DurableLedger
    repo = next(path for path in HERE.parents if (path / 'gpu/ovx_ssh.sh').is_file())
    OUTPUT.mkdir(mode=0o700)
    frozen.fsync_directory(HERE)
    write_once(OUTPUT / 'MAIN_BINDING.json', binding_raw)
    write_once(OUTPUT / 'MANIFEST.json', canonical_bytes(manifest))
    completed = []
    previous = manifest['provenance']['completed_batches'][-1]['final_chain']
    for entry, batch in zip(manifest['batches'], batches):
        directory = OUTPUT / f"BATCH_{entry['ordinal']:04d}"
        directory.mkdir(mode=0o700)
        frozen.fsync_directory(OUTPUT)
        approval = dict(binding, batch_sha256=entry['sha256'], batch_ordinal=entry['ordinal'],
                        parent_binding_raw_sha256=frozen.sha(binding_raw), previous_batch_completion_sha256=previous,
                        preserved_original_batch9_failed_chain=manifest['provenance']['failed_batch9_final_chain'],
                        ledger_path=str(directory / 'LEDGER.jsonl'))
        write_once(directory / 'DERIVED_BINDING.json', canonical_bytes(approval))
        ledger = DurableLedger(directory / 'LEDGER.jsonl')
        try:
            with (directory / 'SSH.stderr').open('x') as errors:
                process = subprocess.Popen(['bash', str(repo / 'gpu/ovx_ssh.sh'),
                                            frozen.encoded_command(remote_program(artifacts, batch, approval))],
                                           stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=errors,
                                           text=True, bufsize=1)
                status, last = frozen.relay_acknowledgements(process, ledger)
            frozen.require(status == 0 and last is not None
                           and last['kind'] == 'REMAINING_BATCH_COMPLETE_ALL_PATHS_VERIFIED',
                           'continuation_first_error_halts_no_retry_or_further_batches')
            receipt = dict(ordinal=entry['ordinal'], ssh_exit=status, batch_sha256=entry['sha256'],
                           ledger_sha256=ledger.previous, ledger_records=ledger.sequence, completion=last)
            write_once(directory / 'VERIFIED.json', canonical_bytes(receipt))
            completed.append(dict(ordinal=entry['ordinal'], ledger_sha256=ledger.previous,
                                  selected_allocated_bytes_released=last['document']['selected_allocated_bytes_released']))
            previous = ledger.previous
            print(json.dumps(dict(original_batch_complete=entry['ordinal'], last_original_ordinal=103,
                                  owner_available_bytes=last['document']['owner_available_bytes_after'])), flush=True)
        except BaseException as error:
            write_once(directory / 'HALTED.json', canonical_bytes(dict(error_type=type(error).__name__, error=str(error),
                       last_durable_sequence=ledger.sequence, last_durable_sha256=ledger.previous,
                       completed_new_batches=completed, original_completed_1_through_8_not_replayed=True,
                       no_retry=True, no_rollback=True, no_further_batches=True)))
            raise
        finally:
            ledger.close()
    write_once(OUTPUT / 'VERIFIED.json', canonical_bytes(dict(status='EXACT_BATCHES_9_THROUGH_103_VERIFIED',
               manifest_sha256=checksum, completed=completed, canary_and_original_batches_1_through_8_replayed=False,
               selected_allocated_bytes_released=sum(row['selected_allocated_bytes_released'] for row in completed))))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    choice = parser.add_mutually_exclusive_group(required=True)
    choice.add_argument('--binding', type=Path)
    choice.add_argument('--print-binding-template', action='store_true')
    args = parser.parse_args()
    if args.print_binding_template:
        unused_artifacts, unused_manifest, checksum, unused_batches = load_prepared()
        print(json.dumps(binding_template(checksum), sort_keys=True, indent=2))
    else:
        run(args.binding)


if __name__ == '__main__':
    main()
