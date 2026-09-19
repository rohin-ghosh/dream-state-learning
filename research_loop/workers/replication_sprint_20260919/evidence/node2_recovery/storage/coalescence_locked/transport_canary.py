"""One exact node2 canary, only after Main binds this transport and its ledger."""

import argparse
import base64
import hashlib
import json
import os
from pathlib import Path
import shlex
import subprocess
import sys
import zlib


HERE = Path(__file__).resolve().parent
REVIEW_SHA = 'e939d282d7d6501ba81bbef4294d0ce38856fb0149b0c62c6a2f9608b8f5a911'
CANARY_RAW_SHA = 'ae622ada631759a66368a911bcacad2dfabac3c82b349389c3e0a803a1c6dd9e'
CANARY_SHA = 'd98bc74ee5a7cf88527d7c660dcec8ed407dba70ccd31653fc87fcb442568220'
OUTPUT = HERE / 'CANARY_EXECUTION'
LEDGER = OUTPUT / 'LEDGER.jsonl'
MODULES = ('pidfd_scan', 'node2_scope', 'retired_writer_guard', 'retired_coalescer')
REMOTE = '''
import os,sys
from pathlib import Path
from node2_scope import ROOT,require
from retired_coalescer import AcknowledgedLedger,execute_batch,verify_path_fd
ledger=AcknowledgedLedger(sys.stdin,sys.stdout)
require(os.getuid()==os.geteuid()==2524 and ROOT.stat().st_uid==2524,'original_owner_not_root')
before=os.statvfs(ROOT)
ledger.record('CANARY_RECEIVING_BOUND',dict(binding=approval,host=os.uname().nodename,
    uid=os.getuid(),owner_available_bytes=before.f_bavail*before.f_frsize,
    source_staging=False,no_automatic_retry=True,no_automatic_rollback=True))
result=execute_batch(batch,expected_sha256=approved_sha256,root=ROOT,ledger=ledger,approval=approval)
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
            info=os.fstat(descriptor)
            require(info.st_nlink==len(paths),'postcheck_exact_hardlink_count')
            verified.append(dict(path=name,device=info.st_dev,inode=info.st_ino,nlink=info.st_nlink,
                sha256=group['metadata']['sha256'],allocated_bytes=info.st_blocks*512))
        finally:
            os.close(descriptor)
for operation in result:
    require(not os.path.lexists(operation['temporary']),'unexpected_temporary_preserve_and_halt')
after=os.statvfs(ROOT)
ledger.record('CANARY_COMPLETE_ALL_PATHS_VERIFIED',dict(paths=verified,replacements=len(result),
    owner_available_bytes_before=before.f_bavail*before.f_frsize,
    owner_available_bytes_after=after.f_bavail*after.f_frsize,
    filesystem_free_bytes_delta=(after.f_bfree-before.f_bfree)*after.f_frsize,
    filesystem_delta_may_include_concurrent_writes=True,
    selected_allocated_bytes_released=batch['groups'][0]['potential_allocated_bytes_freed'],
    source_paths_removed=0,source_content_changed=False,remaining_batches_authorized=False))
'''


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def frozen_artifacts():
    review_raw = (HERE / 'REVIEW.json').read_bytes()
    require(sha(review_raw) == REVIEW_SHA, 'frozen_review_changed')
    artifacts = {}
    for entry in json.loads(review_raw)['files']:
        raw = (HERE / entry['path']).read_bytes()
        require(len(raw) == entry['bytes'] and sha(raw) == entry['sha256'],
                'frozen_artifact_changed:' + entry['path'])
        artifacts[entry['path']] = raw
    require(sha(artifacts['CANARY.json']) == CANARY_RAW_SHA, 'exact_canary_raw_bytes')
    parsed = json.loads(artifacts['CANARY.json'])
    require(sha(json.dumps(parsed, sort_keys=True, separators=(',', ':')).encode()) == CANARY_SHA,
            'exact_canary_canonical_bytes')
    return artifacts


def binding_template():
    return dict(status='AWAITING_MAIN_BINDING_NOT_AUTHORIZED', review_sha256=REVIEW_SHA,
                transport_sha256=sha(Path(__file__).read_bytes()), canary_raw_sha256=CANARY_RAW_SHA,
                batch_sha256=CANARY_SHA, ledger_path=str(LEDGER), execution_scope='CANARY_ONLY',
                groups=1, paths=8, replacements=6, no_automatic_retry=True, no_automatic_rollback=True)


def validate_binding(raw):
    binding = json.loads(raw)
    expected = dict(binding_template(), status='MAIN_REVIEWED_EXECUTION')
    require(all(key in binding and type(binding[key]) is type(value) and binding[key] == value
                for key, value in expected.items()), 'fresh_Main_exact_canary_transport_and_ledger_binding_required')
    return binding


def module_loader(artifacts):
    program = 'import base64,json,sys,types\n'
    for name in MODULES:
        encoded = base64.b64encode(artifacts[name + '.py']).decode()
        program += f'module=types.ModuleType({name!r});module.__file__={name + ".py"!r};sys.modules[{name!r}]=module\n'
        program += f'exec(compile(base64.b64decode({encoded!r}),module.__file__,"exec"),module.__dict__)\n'
    for name, method, filename in [('node2_scope', 'bind_scope_bytes', 'GROUP_BINDINGS.json'),
                                   ('retired_writer_guard', 'bind_lock_bytes', 'WRITER_LOCKS.json')]:
        encoded = base64.b64encode(artifacts[filename]).decode()
        program += f'sys.modules[{name!r}].{method}(base64.b64decode({encoded!r}))\n'
    return program


def remote_program(artifacts, approval):
    program = module_loader(artifacts)
    for name, raw in [('batch', artifacts['CANARY.json']), ('approval', json.dumps(approval).encode())]:
        program += f'{name}=json.loads(base64.b64decode({base64.b64encode(raw).decode()!r}))\n'
    return program + f'approved_sha256={CANARY_SHA!r}\n' + REMOTE


def encoded_command(program):
    encoded = base64.b64encode(zlib.compress(program.encode())).decode()
    expression = f'import base64,zlib;exec(compile(zlib.decompress(base64.b64decode({encoded!r})),"node2_bound_canary","exec"))'
    command = 'python3 -u -B -c ' + shlex.quote(expression)
    require(len(command.encode()) < 100000, 'bounded_ssh_argument_no_source_staging')
    return command


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


def fsync_directory(path):
    descriptor = os.open(path, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def write_once(name, raw):
    with (OUTPUT / name).open('xb') as target:
        target.write(raw)
        target.flush()
        os.fsync(target.fileno())
    fsync_directory(OUTPUT)


def run(binding_path):
    artifacts = frozen_artifacts()
    binding_raw = Path(binding_path).read_bytes()
    approval = validate_binding(binding_raw)
    from retired_coalescer import DurableLedger
    repo = next(path for path in HERE.parents if (path / 'gpu/ovx_ssh.sh').is_file())
    OUTPUT.mkdir(mode=0o700)
    fsync_directory(HERE)
    write_once('MAIN_BINDING.json', binding_raw)
    write_once('TRANSPORT.py', Path(__file__).read_bytes())
    ledger = DurableLedger(LEDGER)
    try:
        with (OUTPUT / 'SSH.stderr').open('x') as errors:
            process = subprocess.Popen(['bash', str(repo / 'gpu/ovx_ssh.sh'),
                                        encoded_command(remote_program(artifacts, approval))],
                                       stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=errors,
                                       text=True, bufsize=1)
            status, last = relay_acknowledgements(process, ledger)
        require(status == 0 and last is not None and last['kind'] == 'CANARY_COMPLETE_ALL_PATHS_VERIFIED',
                'canary_failed_or_completion_not_durable_no_retry')
        write_once('VERIFIED.json', json.dumps(dict(ssh_exit=status, ledger_sha256=ledger.previous,
                   ledger_records=ledger.sequence, completion=last), sort_keys=True).encode())
        print(json.dumps(dict(status='CANARY_COMPLETE_ALL_PATHS_VERIFIED', ledger=str(LEDGER))))
    except BaseException as error:
        write_once('HALTED.json', json.dumps(dict(error_type=type(error).__name__, error=str(error),
                   last_durable_sequence=ledger.sequence, last_durable_sha256=ledger.previous,
                   no_retry=True, no_rollback=True, partial_artifacts_preserved=True), sort_keys=True).encode())
        raise
    finally:
        ledger.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    choice = parser.add_mutually_exclusive_group(required=True)
    choice.add_argument('--binding', type=Path)
    choice.add_argument('--print-binding-template', action='store_true')
    args = parser.parse_args()
    if args.print_binding_template:
        print(json.dumps(binding_template(), indent=2, sort_keys=True))
    else:
        run(args.binding)


if __name__ == '__main__':
    main()
