"""One-shot transport for Main's exact approved canary; no general batch launcher."""

import base64
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import shlex
import subprocess

from assess_hardlinks import require
from retired_coalescer import DurableLedger


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]
APPROVED_SHA256 = 'c36db2e09f6918416a0276c353b30931361f4bad90d89bff49bd351292ba4f83'
BACKUP_CHECK = '''
import hashlib,json,os
from pathlib import Path
from datetime import datetime,timezone
root=Path('/localhome/local-rohing/node3_retired_archive_copy_20260919T133405Z_ws6')
assert os.uname().nodename=='ipp2-ovx-p3-02' and os.getuid()==1352
copy=json.loads((root/'COPY_VERIFIED.json').read_bytes())
restore=json.loads((root/'RESTORE_VERIFIED.json').read_bytes())
assert restore['status']=='FULL_FILESYSTEM_RESTORE_BYTES_LINKS_MODE_MTIME_XATTRS_VERIFIED'
assert restore['members']==copy['members']==85620
checks={}
for name in ['SOURCE_MANIFEST.jsonl','retired-node3.tar.zst']:
    path=root/name
    before=path.stat()
    value=hashlib.sha256()
    with path.open('rb') as source:
        while block:=source.read(8*1024*1024):
            value.update(block)
    after=path.stat()
    assert (before.st_dev,before.st_ino,before.st_size,before.st_mtime_ns,before.st_ctime_ns)==(after.st_dev,after.st_ino,after.st_size,after.st_mtime_ns,after.st_ctime_ns)
    expected=copy['manifest_sha256' if name=='SOURCE_MANIFEST.jsonl' else 'archive_sha256'].split()[0]
    assert value.hexdigest()==expected
    checks[name]=dict(sha256=value.hexdigest(),bytes=after.st_size,inode=after.st_ino,mtime_ns=after.st_mtime_ns)
print(json.dumps(dict(status='EXISTING_BACKUP_FRESHLY_REHASHED',utc=datetime.now(timezone.utc).isoformat(),root=str(root),checks=checks,no_gpu_operations=True),sort_keys=True))
'''
REMOTE = '''
from datetime import datetime, timezone
import json,os,subprocess,sys
from pathlib import Path
from assess_hardlinks import ROOT, require
from retired_coalescer import AcknowledgedLedger, execute_batch, verify_path_fd, digest

ledger=AcknowledgedLedger(sys.stdin,sys.stdout)
require(os.uname().nodename=='ipp2-ovx-p6-09' and os.getuid()==2524,'original_node_and_owner')
require(digest(batch)==approved_sha256 and batch['root']==str(ROOT),'exact_approved_canary')
require(len(batch['groups'])==3 and batch['max_paths']==9,'exact_three_groups_nine_paths')
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
            started=(process/'stat').read_text().rsplit(')',1)[1].split()[19]
            processes.append(dict(pid=int(process.name),start_ticks=started,argv=arguments))
    except FileNotFoundError:
        continue
before=os.statvfs(ROOT)
ledger.record('CANARY_FRESH_PREFLIGHT',dict(host=os.uname().nodename,uid=os.getuid(),batch_sha256=approved_sha256,
    gpu_memory=gpu,compute_apps=compute,matching_processes=processes,
    owner_available_bytes=before.f_bavail*before.f_frsize,free_bytes_including_reserved=before.f_bfree*before.f_frsize))
require(not compute.strip() and not processes,'changed_node3_liveness_stop_for_review')
result=execute_batch(batch,expected_sha256=approved_sha256,root=ROOT,ledger=ledger,
    approval=dict(status='MAIN_REVIEWED_EXECUTION',batch_sha256=approved_sha256))
require(len(result)==6,'exact_six_replacements')
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
            require(value.st_nlink==len(paths),'postcheck_exact_hardlink_count')
            verified.append(dict(path=name,device=value.st_dev,inode=value.st_ino,nlink=value.st_nlink,
                mode=value.st_mode,uid=value.st_uid,gid=value.st_gid,mtime_ns=value.st_mtime_ns,
                ctime_ns=value.st_ctime_ns,atime_ns=value.st_atime_ns,sha256=group['metadata']['sha256']))
        finally:
            os.close(descriptor)
for operation in result:
    require(not os.path.lexists(operation['temporary']),'unexpected_remaining_temporary')
after=os.statvfs(ROOT)
ledger.record('CANARY_COMPLETE_ALL_PATHS_VERIFIED',dict(utc=datetime.now(timezone.utc).isoformat(),
    batch_sha256=approved_sha256,replacements=len(result),verified_paths=verified,
    confirmed_replaced_inode_allocated_bytes=sum(group['potential_allocated_bytes_freed'] for group in batch['groups']),
    filesystem_free_bytes_before=before.f_bfree*before.f_frsize,
    filesystem_free_bytes_after=after.f_bfree*after.f_frsize,
    filesystem_free_bytes_delta=(after.f_bfree-before.f_bfree)*after.f_frsize,
    owner_available_bytes_before=before.f_bavail*before.f_frsize,
    owner_available_bytes_after=after.f_bavail*after.f_frsize,
    owner_available_bytes_delta=(after.f_bavail-before.f_bavail)*after.f_frsize,
    source_paths_removed=0,source_content_changed=False,no_automatic_retry=True))
'''


def write_once(name, value):
    with (HERE / name).open('x') as output:
        json.dump(value, output, sort_keys=True, indent=2)
        output.write('\n')
        output.flush()
        os.fsync(output.fileno())
    descriptor = os.open(HERE, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def encoded_command(program):
    expression = 'import base64;exec(compile(base64.b64decode(' + repr(base64.b64encode(program.encode()).decode())
    expression += '),"ws6_approved_canary","exec"))'
    return 'python3 -u -B -c ' + shlex.quote(expression)


def relay_acknowledgements(process, ledger):
    last = None
    try:
        for line in process.stdout:
            entry = json.loads(line)
            checksum = ledger.accept_remote(entry)
            process.stdin.write(json.dumps(dict(durable=True, sha256=checksum)) + '\n')
            process.stdin.flush()
            last = entry
    finally:
        process.stdin.close()
        process.stdout.close()
    status = process.wait(timeout=30)
    return status, last


def main():
    proposal = (HERE / 'HARDLINK_CANARY_PROPOSAL.json').read_bytes()
    require(hashlib.sha256(proposal).hexdigest() == APPROVED_SHA256, 'exact_main_authorized_proposal')
    batch = json.loads(proposal)
    for entry in [*batch['source_code_and_tests'], batch['cpu_evidence'], batch['eligible_assessment'],
            batch['archive_copy_receipt'], batch['archive_full_restore_receipt']]:
        require(hashlib.sha256((HERE / entry['path']).read_bytes()).hexdigest() == entry['sha256'],
            'reviewed_evidence_changed:' + entry['path'])
    write_once('CANARY_EXECUTION_AUTHORIZATION.json', dict(utc=datetime.now(timezone.utc).isoformat(),
        authority='Main explicit user message authorizing EXACT CANARY after full restore and 21 independent CPU tests',
        batch_sha256=APPROVED_SHA256, groups=3, paths=9, replacements=6,
        allocated_bytes=17088512, full_batch_authorized=False, no_automatic_retry=True))
    backup = subprocess.run(['bash', str(REPO / 'gpu/ovx4_ssh.sh'), encoded_command(BACKUP_CHECK)],
        check=True, capture_output=True, text=True, timeout=120)
    backup_receipt = json.loads(backup.stdout)
    require(backup_receipt['checks']['retired-node3.tar.zst']['sha256'] == batch['archive_sha256']
        and backup_receipt['checks']['SOURCE_MANIFEST.jsonl']['sha256'] == batch['source_manifest_sha256'],
        'fresh_backup_matches_reviewed_canary')
    write_once('CANARY_BACKUP_RECHECK.json', backup_receipt)
    program = 'import base64,sys,types,json\n'
    for name in ['assess_hardlinks', 'retired_coalescer']:
        payload = base64.b64encode((HERE / (name + '.py')).read_bytes()).decode()
        program += f'module=types.ModuleType({name!r});sys.modules[{name!r}]=module\n'
        program += f'exec(compile(base64.b64decode({payload!r}),{name!r},"exec"),module.__dict__)\n'
    program += f'batch=json.loads(base64.b64decode({base64.b64encode(proposal).decode()!r}))\n'
    program += f'approved_sha256={APPROVED_SHA256!r}\n' + REMOTE
    ledger = DurableLedger(HERE / 'CANARY_EXECUTION_LEDGER.jsonl')
    last = None
    try:
        with (HERE / 'CANARY_EXECUTION.stderr').open('x') as errors:
            process = subprocess.Popen(['bash', str(REPO / 'gpu/ovx2_ssh.sh'), encoded_command(program)],
                stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=errors, text=True, bufsize=1)
            status, last = relay_acknowledgements(process, ledger)
        require(status == 0 and last is not None and last['kind'] == 'CANARY_COMPLETE_ALL_PATHS_VERIFIED',
            'canary_failed_or_completion_not_durable_no_retry')
        write_once('CANARY_EXECUTION_VERIFIED.json', dict(status='CANARY_COMPLETE_ALL_PATHS_VERIFIED',
            ssh_exit=status, batch_sha256=APPROVED_SHA256, ledger_records=ledger.sequence,
            ledger_final_sha256=ledger.previous, result=last['document'],
            remaining_batches_authorized=False, preserved_archive_sha256=batch['archive_sha256'],
            preserved_manifest_sha256=batch['source_manifest_sha256']))
    except BaseException as error:
        write_once('CANARY_EXECUTION_HALTED.json', dict(status='HALTED_NO_AUTOMATIC_RETRY',
            error_type=type(error).__name__, error=str(error), last_durable_sequence=ledger.sequence,
            last_durable_sha256=ledger.previous, batch_sha256=APPROVED_SHA256,
            must_inspect_ledger_before_any_action=True, partial_artifacts_preserved=True))
        raise
    finally:
        ledger.close()


if __name__ == '__main__':
    main()
