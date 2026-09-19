"""Execute only Main's exact remaining index with the frozen coalescer and durable ACKs."""

import base64
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import shlex
import subprocess

from assess_hardlinks import require
from retired_coalescer import DurableLedger, digest
from run_approved_canary import BACKUP_CHECK, encoded_command


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]
INDEX_SHA256 = 'a8c9c0ad3c594133084cf4cd78a4c33ddfea2762d0e0a5fd17bf5c6d49e7d8ff'
COALESCER_SHA256 = 'e2826bd80099e5d791c9c638b3113fb4150f461b5936d445c45656197a968b7f'
AUTHORIZATION = HERE.parent / 'operations' / 'NODE3_REMAINING_COALESCING_AUTHORIZATION.md'
REMOTE = '''
from datetime import datetime, timezone
import json,os,subprocess,sys
from pathlib import Path
from assess_hardlinks import ROOT,require
from retired_coalescer import AcknowledgedLedger,digest,execute_batch,verify_path_fd

payload=json.loads(sys.stdin.readline())
index,batches=payload['index'],payload['batches']
require(digest(index)==approved_index_sha256,'exact_approved_remaining_index')
require(os.uname().nodename=='ipp2-ovx-p6-09' and os.getuid()==2524,'original_node3_owner_only')
require(len(batches)==len(index['batches'])==125,'exact_125_batches')
for batch,binding in zip(batches,index['batches']):
    require(digest(batch)==binding['sha256'] and batch['ordinal']==binding['ordinal']
        and batch['root']==str(ROOT),'exact_index_bound_batch')
ledger=AcknowledgedLedger(sys.stdin,sys.stdout)
gpu=subprocess.run(['nvidia-smi','--query-gpu=index,memory.used','--format=csv,noheader'],check=True,capture_output=True,text=True).stdout
compute=subprocess.run(['nvidia-smi','--query-compute-apps=pid,process_name,used_memory','--format=csv,noheader'],check=True,capture_output=True,text=True).stdout
processes=[]
for process in Path('/proc').iterdir():
    if not process.name.isdigit() or int(process.name) in (os.getpid(),os.getppid()):
        continue
    try:
        if process.stat().st_uid!=os.getuid():
            continue
        arguments=(process/'cmdline').read_bytes().decode(errors='replace').split('\\0')
        if any(marker in argument for argument in arguments for marker in ['native_driver','native_life','caption_epoch','classroom','pending_math_b']):
            processes.append(dict(pid=int(process.name),start_ticks=(process/'stat').read_text().rsplit(')',1)[1].split()[19],argv=arguments))
    except FileNotFoundError:
        continue
before=os.statvfs(ROOT)
ledger.record('REMAINING_FRESH_PREFLIGHT',dict(index_sha256=approved_index_sha256,
    authorization_sha256=payload['authorization_sha256'],host=os.uname().nodename,uid=os.getuid(),
    gpu_memory=gpu,compute_apps=compute,matching_processes=processes,
    owner_available_bytes=before.f_bavail*before.f_frsize,
    free_bytes_including_reserved=before.f_bfree*before.f_frsize,
    directory_entry_mtime_ctime_changes_explicitly_authorized=True))
require(not compute.strip() and not processes,'changed_node3_liveness_stop_for_review')

def verify_batch_paths(batch,include_paths):
    verified=[]
    for group in batch['groups']:
        canonical=group['canonical']
        paths=[entry['path'] for inode in [canonical,*group['replacement_inodes']] for entry in inode['paths']]
        for name in paths:
            path=Path(name)
            descriptor=os.open(path,os.O_RDONLY|os.O_NOFOLLOW|os.O_NOATIME)
            try:
                verify_path_fd(path,descriptor,group['metadata'],canonical)
                value=os.fstat(descriptor)
                require(value.st_nlink==len(paths),'exact_postcheck_link_count')
                verified.append(dict(path=name,device=value.st_dev,inode=value.st_ino,nlink=value.st_nlink,
                    size=value.st_size,mode=value.st_mode,uid=value.st_uid,gid=value.st_gid,
                    mtime_ns=value.st_mtime_ns,sha256=group['metadata']['sha256']))
            finally:
                os.close(descriptor)
    return dict(path_count=len(verified),verified_paths_sha256=digest(verified),
        **(dict(verified_paths=verified) if include_paths else {}))

completed=0
last_ordinal=0
try:
    for batch,binding in zip(batches,index['batches']):
        last_ordinal=binding['ordinal']
        batch_before=os.statvfs(ROOT)
        ledger.record('REMAINING_BATCH_START',dict(ordinal=last_ordinal,batch_sha256=binding['sha256'],
            index_sha256=approved_index_sha256,expected_replacements=binding['replacements']))
        replacements=execute_batch(batch,expected_sha256=binding['sha256'],root=ROOT,ledger=ledger,
            approval=dict(status='MAIN_REVIEWED_EXECUTION',batch_sha256=binding['sha256']))
        require(len(replacements)==binding['replacements'],'exact_batch_replacement_count')
        check=verify_batch_paths(batch,True)
        for operation in replacements:
            require(not os.path.lexists(operation['temporary']),'unexpected_remaining_temporary')
        completed+=len(replacements)
        current=os.statvfs(ROOT)
        ledger.record('REMAINING_BATCH_POSTCHECK',dict(utc=datetime.now(timezone.utc).isoformat(),
            ordinal=last_ordinal,batch_sha256=binding['sha256'],replacements=len(replacements),
            cumulative_replacements=completed,**check,
            confirmed_replaced_inode_allocated_bytes=binding['potential_allocated_bytes'],
            batch_free_bytes_delta=(current.f_bfree-batch_before.f_bfree)*current.f_frsize,
            filesystem_free_bytes=current.f_bfree*current.f_frsize,
            owner_available_blocks=current.f_bavail,filesystem_block_bytes=current.f_frsize,
            owner_available_bytes=current.f_bavail*current.f_frsize))
    require(completed==index['replacements']==3189,'complete_replacement_count')
    final_verifications=[]
    for batch,binding in zip(batches,index['batches']):
        check=verify_batch_paths(batch,False)
        final_verifications.append(dict(ordinal=binding['ordinal'],**check))
    canary_check=verify_batch_paths(payload['canary'],False)
    require(sum(check['path_count'] for check in final_verifications)==4845
        and canary_check['path_count']==9,'all_4854_original_coalesced_paths_still_verified')
    after=os.statvfs(ROOT)
    ledger.record('REMAINING_COMPLETE_ALL_PATHS_VERIFIED',dict(utc=datetime.now(timezone.utc).isoformat(),
        index_sha256=approved_index_sha256,batches_completed=125,replacements=completed,
        verified_remaining_paths=4845,verified_prior_canary_paths=9,
        final_batch_verifications=final_verifications,final_canary_verification=canary_check,
        confirmed_replaced_inode_allocated_bytes=index['potential_allocated_bytes'],
        filesystem_free_bytes_before=before.f_bfree*before.f_frsize,
        filesystem_free_bytes_after=after.f_bfree*after.f_frsize,
        filesystem_free_bytes_delta=(after.f_bfree-before.f_bfree)*after.f_frsize,
        owner_available_blocks_before=before.f_bavail,owner_available_blocks_after=after.f_bavail,
        filesystem_block_bytes=after.f_frsize,owner_available_bytes_before=before.f_bavail*before.f_frsize,
        owner_available_bytes_after=after.f_bavail*after.f_frsize,
        original_paths_removed=0,file_content_or_required_metadata_changed=False,
        no_gpu_operations=True,no_automatic_retry=True))
except BaseException as error:
    ledger.record('REMAINING_HALTED_NO_RETRY',dict(error_type=type(error).__name__,error=str(error),
        index_sha256=approved_index_sha256,last_ordinal=last_ordinal,
        completed_postchecked_replacements=completed,partial_artifacts_preserved=True))
    raise
'''


def write_once(path, value):
    with path.open('x') as output:
        json.dump(value, output, sort_keys=True, indent=2)
        output.write('\n')
        output.flush()
        os.fsync(output.fileno())
    descriptor = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def load_payload():
    index_bytes = (HERE / 'HARDLINK_REMAINING_PROPOSAL.json').read_bytes()
    require(hashlib.sha256(index_bytes).hexdigest() == INDEX_SHA256, 'exact_main_approved_index_bytes')
    require(hashlib.sha256((HERE / 'retired_coalescer.py').read_bytes()).hexdigest() == COALESCER_SHA256,
        'frozen_main_reviewed_coalescer')
    authorization = AUTHORIZATION.read_bytes()
    require(INDEX_SHA256 in authorization.decode() and COALESCER_SHA256 in authorization.decode(),
        'main_published_exact_authorization')
    index = json.loads(index_bytes)
    batches = []
    for entry in index['batches']:
        raw = (HERE / entry['path']).read_bytes()
        require(hashlib.sha256(raw).hexdigest() == entry['sha256'], 'exact_main_approved_batch_bytes')
        batch = json.loads(raw)
        for evidence in [*batch['source_code_and_tests'], batch['cpu_evidence'], batch['eligible_assessment'],
                batch['archive_copy_receipt'], batch['archive_full_restore_receipt'], batch['completed_canary'],
                batch['canary_ledger'], batch['fresh_backup_recheck']]:
            require(hashlib.sha256((HERE / evidence['path']).read_bytes()).hexdigest() == evidence['sha256'],
                'bound_evidence_changed:' + evidence['path'])
        batches.append(batch)
    require(len(batches) == 125 and sum(len(batch['groups']) for batch in batches) == 1656,
        'exact_reviewed_batch_and_group_totals')
    return dict(index=index, batches=batches, authorization_sha256=hashlib.sha256(authorization).hexdigest(),
        canary=json.loads((HERE / 'HARDLINK_CANARY_PROPOSAL.json').read_bytes()))


def relay(process, ledger, receipt_directory):
    last = None
    try:
        for line in process.stdout:
            entry = json.loads(line)
            checksum = ledger.accept_remote(entry)
            if entry['kind'] == 'REMAINING_BATCH_POSTCHECK':
                ordinal = entry['document']['ordinal']
                write_once(receipt_directory / f'BATCH_{ordinal:04d}_VERIFIED.json', entry)
            process.stdin.write(json.dumps(dict(durable=True, sha256=checksum)) + '\n')
            process.stdin.flush()
            last = entry
    finally:
        process.stdin.close()
        process.stdout.close()
    return process.wait(timeout=30), last


def main():
    payload = load_payload()
    write_once(HERE / 'REMAINING_EXECUTION_AUTHORIZATION.json', dict(utc=datetime.now(timezone.utc).isoformat(),
        index_sha256=INDEX_SHA256,coalescer_sha256=COALESCER_SHA256,
        main_authorization_path=str(AUTHORIZATION.relative_to(REPO)),
        main_authorization_sha256=payload['authorization_sha256'],batches=125,groups=1656,
        paths=4845,replacements=3189,potential_allocated_bytes=35262947328,
        no_native_or_gpu_launch_authorized=True,no_automatic_retry=True))
    backup = subprocess.run(['bash', str(REPO / 'gpu/ovx4_ssh.sh'), encoded_command(BACKUP_CHECK)],
        check=True, capture_output=True, text=True, timeout=120)
    backup_receipt = json.loads(backup.stdout)
    require(backup_receipt['checks']['retired-node3.tar.zst']['sha256'] == payload['index']['archive_sha256']
        and backup_receipt['checks']['SOURCE_MANIFEST.jsonl']['sha256'] == payload['index']['source_manifest_sha256'],
        'fresh_backup_matches_remaining_index')
    write_once(HERE / 'REMAINING_BACKUP_RECHECK.json', backup_receipt)
    program = 'import base64,sys,types,json\n'
    for name in ['assess_hardlinks', 'retired_coalescer']:
        raw = (HERE / (name + '.py')).read_bytes()
        program += f'module=types.ModuleType({name!r});sys.modules[{name!r}]=module\n'
        program += f'exec(compile(base64.b64decode({base64.b64encode(raw).decode()!r}),{name!r},"exec"),module.__dict__)\n'
    program += f'approved_index_sha256={INDEX_SHA256!r}\n' + REMOTE
    receipt_directory = HERE / 'remaining_execution_receipts'
    receipt_directory.mkdir(exist_ok=False)
    ledger = DurableLedger(HERE / 'REMAINING_EXECUTION_LEDGER.jsonl')
    try:
        with (HERE / 'REMAINING_EXECUTION.stderr').open('x') as errors:
            process = subprocess.Popen(['bash', str(REPO / 'gpu/ovx2_ssh.sh'), encoded_command(program)],
                stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=errors, text=True, bufsize=1)
            process.stdin.write(json.dumps(payload, sort_keys=True, separators=(',', ':')) + '\n')
            process.stdin.flush()
            status, last = relay(process, ledger, receipt_directory)
        require(status == 0 and last is not None and last['kind'] == 'REMAINING_COMPLETE_ALL_PATHS_VERIFIED',
            'remaining_failed_or_completion_not_durable_no_retry')
        write_once(HERE / 'REMAINING_EXECUTION_VERIFIED.json', dict(status='REMAINING_COMPLETE_ALL_PATHS_VERIFIED',
            ssh_exit=status,index_sha256=INDEX_SHA256,ledger_records=ledger.sequence,
            ledger_final_sha256=ledger.previous,result=last['document'],
            original_archive_sha256=payload['index']['archive_sha256'],
            original_manifest_sha256=payload['index']['source_manifest_sha256'],
            native_gpu_launch_performed=False))
    except BaseException as error:
        write_once(HERE / 'REMAINING_EXECUTION_HALTED.json', dict(status='HALTED_NO_AUTOMATIC_RETRY',
            error_type=type(error).__name__,error=str(error),index_sha256=INDEX_SHA256,
            last_durable_sequence=ledger.sequence,last_durable_sha256=ledger.previous,
            must_inspect_ledger_before_any_action=True,partial_artifacts_preserved=True))
        raise
    finally:
        ledger.close()


if __name__ == '__main__':
    main()
