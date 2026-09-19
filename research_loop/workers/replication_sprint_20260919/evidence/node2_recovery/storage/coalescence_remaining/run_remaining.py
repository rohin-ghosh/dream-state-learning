"""Sequential bounded batches using the unchanged canary kernel and durable ACK relay."""

import argparse
import base64
import json
from pathlib import Path
import subprocess

from prepare_remaining import CODE_FILES, CANARY_RECEIPT_SHA, canonical_bytes, plan_batches, write_once
from verify_completed_canary import FROZEN, HERE, TRANSPORT_SHA, frozen, local_proof


OUTPUT = HERE / 'EXECUTION'
REMOTE = '''
import os,sys
from pathlib import Path
from node2_scope import ROOT,require
from retired_coalescer import AcknowledgedLedger,execute_batch,verify_path_fd
ledger=AcknowledgedLedger(sys.stdin,sys.stdout)
require(os.getuid()==os.geteuid()==2524 and ROOT.stat().st_uid==2524,'original_owner_not_root')
require(0<len(batch['groups'])<=5 and batch['max_paths']<=40,'bounded_remaining_batch')
require(all(group['selection_index']!=0 for group in batch['groups']),'canary_excluded')
before=os.statvfs(ROOT)
ledger.record('REMAINING_BATCH_RECEIVING_BOUND',dict(binding=approval,host=os.uname().nodename,uid=os.getuid(),
    owner_available_bytes=before.f_bavail*before.f_frsize,source_staging=False))
result=execute_batch(batch,expected_sha256=approved_sha256,root=ROOT,ledger=ledger,approval=approval)
expected_replacements=sum(len(inode['paths']) for group in batch['groups'] for inode in group['replacement_inodes'])
require(len(result)==expected_replacements,'exact_manifest_replacements')
verified=[]
for group in batch['groups']:
    canonical=group['canonical']
    paths=[entry['path'] for inode in [canonical,*group['replacement_inodes']] for entry in inode['paths']]
    for name in paths:
        path=Path(name)
        descriptor=os.open(path,os.O_RDONLY|os.O_NOFOLLOW|os.O_NOATIME)
        try:
            verify_path_fd(path,descriptor,group['metadata'],canonical)
            info=os.fstat(descriptor)
            require(info.st_nlink==len(paths),'postcheck_exact_hardlink_count')
            verified.append(dict(path=name,device=info.st_dev,inode=info.st_ino,nlink=info.st_nlink,
                sha256=group['metadata']['sha256'],allocated_bytes=info.st_blocks*512))
        finally:
            os.close(descriptor)
for operation in result:
    require(not os.path.lexists(operation['temporary']),'unexpected_temporary_preserve_and_halt')
after=os.statvfs(ROOT)
ledger.record('REMAINING_BATCH_COMPLETE_ALL_PATHS_VERIFIED',dict(paths=verified,replacements=len(result),
    owner_available_bytes_before=before.f_bavail*before.f_frsize,
    owner_available_bytes_after=after.f_bavail*after.f_frsize,
    filesystem_free_bytes_delta=(after.f_bfree-before.f_bfree)*after.f_frsize,
    filesystem_delta_may_include_concurrent_writes=True,
    selected_allocated_bytes_released=sum(group['potential_allocated_bytes_freed'] for group in batch['groups']),
    source_paths_removed=0,source_content_changed=False,canary_executed=False))
'''


def load_prepared():
    artifacts = frozen.frozen_artifacts()
    proof = local_proof()
    raw = (HERE / 'MANIFEST.json').read_bytes()
    manifest = json.loads(raw)
    require = frozen.require
    require(raw == canonical_bytes(manifest), 'canonical_manifest_bytes')
    require(manifest['source_review_sha256'] == frozen.REVIEW_SHA
            and manifest['frozen_transport_sha256'] == TRANSPORT_SHA
            and manifest['completed_canary'] == proof
            and proof['receipt_sha256'] == CANARY_RECEIPT_SHA, 'unchanged_kernel_and_completed_canary')
    require(set(manifest['source_files']) == set(CODE_FILES), 'exact_receiving_source_set')
    for name, checksum in manifest['source_files'].items():
        require(frozen.sha((HERE / name).read_bytes()) == checksum, 'receiving_source_changed:' + name)
    completion = json.loads((FROZEN / 'CANARY_EXECUTION/VERIFIED.json').read_bytes())
    expected = plan_batches(json.loads(artifacts['GROUPS.json']), json.loads(artifacts['CANARY.json']), completion)
    require(len(manifest['batches']) == len(expected) == 103 and manifest['groups'] == 514
            and manifest['paths'] == 4112 and manifest['replacements'] == 3084
            and manifest['execution_directory'] == str(OUTPUT), 'exact_remaining_scope')
    batches = []
    for entry, batch in zip(manifest['batches'], expected):
        require(entry['path'] == f"BATCH_{batch['ordinal']:04d}.json", 'exact_ordered_batch_name')
        batch_raw = (HERE / entry['path']).read_bytes()
        require(batch_raw == canonical_bytes(batch) and frozen.sha(batch_raw) == entry['sha256'],
                'exact_remaining_batch_raw_and_canonical_hash')
        batches.append(batch)
    return artifacts, manifest, frozen.sha(raw), batches


def binding_template(manifest_sha):
    return dict(status='AWAITING_MAIN_BINDING_NOT_AUTHORIZED', manifest_sha256=manifest_sha,
                runner_sha256=frozen.sha(Path(__file__).read_bytes()), source_review_sha256=frozen.REVIEW_SHA,
                excluded_canary_canonical_sha256=frozen.CANARY_SHA, execution_scope='EXACT_514_REMAINING_GROUPS',
                batch_count=103, groups=514, paths=4112, replacements=3084, max_paths_per_batch=40,
                execution_directory=str(OUTPUT), no_automatic_retry=True, no_automatic_rollback=True)


def validate_binding(raw, manifest_sha):
    binding = json.loads(raw)
    expected = dict(binding_template(manifest_sha), status='MAIN_REVIEWED_EXECUTION')
    frozen.require(all(key in binding and type(binding[key]) is type(value) and binding[key] == value
                       for key, value in expected.items()), 'fresh_Main_exact_remaining_manifest_binding_required')
    return binding


def batch_approval(binding, binding_raw, entry, previous_completion):
    return dict(binding, batch_sha256=entry['sha256'], batch_ordinal=entry['ordinal'],
                parent_binding_raw_sha256=frozen.sha(binding_raw),
                previous_batch_completion_sha256=previous_completion,
                ledger_path=str(OUTPUT / f"BATCH_{entry['ordinal']:04d}" / 'LEDGER.jsonl'))


def remote_program(artifacts, batch, approval):
    program = frozen.module_loader(artifacts)
    for name, value in [('batch', batch), ('approval', approval)]:
        encoded = base64.b64encode(canonical_bytes(value)).decode()
        program += f'{name}=json.loads(base64.b64decode({encoded!r}))\n'
    return program + f"approved_sha256={approval['batch_sha256']!r}\n" + REMOTE


def run(binding_path):
    artifacts, manifest, manifest_sha, batches = load_prepared()
    binding_raw = Path(binding_path).read_bytes()
    binding = validate_binding(binding_raw, manifest_sha)
    from retired_coalescer import DurableLedger
    repo = next(path for path in HERE.parents if (path / 'gpu/ovx_ssh.sh').is_file())
    OUTPUT.mkdir(mode=0o700)
    frozen.fsync_directory(HERE)
    write_once(OUTPUT / 'MAIN_BINDING.json', binding_raw)
    write_once(OUTPUT / 'MANIFEST.json', canonical_bytes(manifest))
    completed = []
    previous = manifest['completed_canary']['final_chain']
    for entry, batch in zip(manifest['batches'], batches):
        directory = OUTPUT / f"BATCH_{entry['ordinal']:04d}"
        directory.mkdir(mode=0o700)
        frozen.fsync_directory(OUTPUT)
        approval = batch_approval(binding, binding_raw, entry, previous)
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
                           'batch_failed_or_completion_not_durable_no_retry_no_further_batches')
            result = dict(ordinal=entry['ordinal'], ssh_exit=status, batch_sha256=entry['sha256'],
                          ledger_sha256=ledger.previous, ledger_records=ledger.sequence, completion=last)
            write_once(directory / 'VERIFIED.json', canonical_bytes(result))
            completed.append(dict(ordinal=entry['ordinal'], ledger_sha256=ledger.previous,
                                  selected_allocated_bytes_released=last['document']['selected_allocated_bytes_released']))
            previous = ledger.previous
            print(json.dumps(dict(batch_complete=entry['ordinal'], of=103,
                                  owner_available_bytes=last['document']['owner_available_bytes_after'])), flush=True)
        except BaseException as error:
            write_once(directory / 'HALTED.json', canonical_bytes(dict(error_type=type(error).__name__, error=str(error),
                       last_durable_sequence=ledger.sequence, last_durable_sha256=ledger.previous,
                       completed_batches=completed, no_retry=True, no_rollback=True, no_further_batches=True)))
            raise
        finally:
            ledger.close()
    write_once(OUTPUT / 'VERIFIED.json', canonical_bytes(dict(status='ALL_103_REMAINING_BATCHES_VERIFIED',
               manifest_sha256=manifest_sha, completed=completed, canary_reexecuted=False,
               selected_allocated_bytes_released=sum(row['selected_allocated_bytes_released'] for row in completed))))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    choice = parser.add_mutually_exclusive_group(required=True)
    choice.add_argument('--binding', type=Path)
    choice.add_argument('--print-binding-template', action='store_true')
    args = parser.parse_args()
    if args.print_binding_template:
        unused_artifacts, unused_manifest, manifest_sha, unused_batches = load_prepared()
        print(json.dumps(binding_template(manifest_sha), sort_keys=True, indent=2))
    else:
        run(args.binding)


if __name__ == '__main__':
    main()
