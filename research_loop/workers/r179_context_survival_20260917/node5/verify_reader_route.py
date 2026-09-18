"""Prove mounted reader inbox routing without opening messages or sending a turn."""

import hashlib
import json
import os
from pathlib import Path
import shlex
import subprocess
import sys
import time


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def reference(path):
    return dict(path=str(path), sha256=hashlib.sha256(Path(path).read_bytes()).hexdigest())


def inode(path):
    metadata = Path(path).stat()
    return dict(device=metadata.st_dev, inode=metadata.st_ino)


def identity(process_id):
    process = Path('/proc') / str(process_id)
    fields = (process / 'stat').read_text().rsplit(') ', 1)[1].split()
    require(fields[0] not in ('Z', 'X'), 'current_reader_alive')
    command = (process / 'cmdline').read_bytes()
    return dict(pid=process_id, start_ticks=fields[19], uid=process.stat().st_uid,
        cwd=os.readlink(process / 'cwd'), argv_sha256=hashlib.sha256(command).hexdigest(),
        cgroup=(process / 'cgroup').read_text().strip())


def inspect():
    output = Path('/localhome/local-rohing/orch_r179_context_repo_reader_20260917_attempt2')
    request = json.loads((output / 'INPUT.json').read_bytes())
    expected = request['identity']
    before = identity(expected['pid'])
    require(before['start_ticks'] == expected['start_ticks'] and before['uid'] == 2524
            and before['cwd'] == request['plan']['source_root'], 'bound_current_reader_native')
    logical, stored = Path(request['logical_root']), Path(request['storage_root'])
    process = Path('/proc') / str(before['pid'])
    descriptors = []
    for descriptor in (process / 'fd').iterdir():
        try:
            target = os.readlink(descriptor)
            if target.endswith('/stream/inbox'):
                descriptors.append(dict(fd=int(descriptor.name), consumer_path=target, inode=inode(descriptor)))
        except FileNotFoundError:
            continue
    require(len(descriptors) == 1, 'one_actual_open_consumer_inbox')
    descriptor = descriptors[0]
    mounted = process / 'root' / logical.relative_to('/')
    require(inode(mounted) == inode(stored) and inode(logical) != inode(stored),
            'recovered_mount_not_archival_host_root')
    require(descriptor['inode'] == inode(stored / 'stream/inbox') == inode(mounted / 'stream/inbox')
            and descriptor['inode'] != inode(logical / 'stream/inbox'), 'actual_open_inbox_is_recovered_host_storage')
    mounts = []
    for line in (process / 'mountinfo').read_text().splitlines():
        fields = line.split()
        if len(fields) > 6 and fields[4] == str(logical):
            mounts.append(dict(device=fields[2], backing_root=fields[3], mountpoint=fields[4], options=fields[5]))
    require(len(mounts) == 1, 'exact_reader_private_bind_mount')
    source = Path(before['cwd'])
    sources = {name: reference(source / name) for name in
        ('gpu/orch_r127_pilot_console.py', 'gpu/orch_r125_stream_console.py',
         'gpu/orch_r125_stream_journal.py', 'gpu/orch_r125_continual_native.py')}
    console = (source / 'gpu/orch_r127_pilot_console.py').read_text()
    require("SCHEMA = 'R127_ATTRIBUTED_INBOX_V1'" in console and "'Rohin'" in console,
            'actual_attributed_console_supports_Rohin')
    require(identity(before['pid']) == before, 'reader_identity_unchanged_during_route_proof')
    return dict(schema='R179_READER_CONSOLE_ROUTE_V1', status='HOST_DELIVERY_ROUTE_INODE_VERIFIED',
        label='repo_reader', node='ovx3', identity=before, native_consumer_inbox=descriptor,
        consumer_namespace_root=str(logical), actual_root=str(stored), host_delivery_root=str(stored),
        host_delivery_inbox=str(stored / 'stream/inbox'), archival_host_root_do_not_deliver=str(logical),
        mounted_root_inode=inode(mounted), host_storage_root_inode=inode(stored),
        archival_host_root_inode=inode(logical), bind_mount=mounts[0],
        python='/localhome/local-rohing/v2/venv/bin/python', source_root=str(source), source_files=sources,
        attributed_console_module='gpu.orch_r127_pilot_console', attributed_speaker='Rohin',
        console_root_argument=str(stored), delivery_namespace='NODE5_HOST',
        ingestion_proven=False, messages_sent=0, inbox_content_reads=0, journal_content_reads=0,
        sealed_reads=0, signals_sent=0, model_calls=0, observed_unix=time.time())


def main():
    if '--remote' in sys.argv:
        print(json.dumps(inspect(), sort_keys=True))
        return
    command = '/localhome/local-rohing/v2/venv/bin/python -B -c ' + shlex.quote(Path(__file__).read_text()) + ' --remote'
    result = subprocess.run(['bash', 'gpu/ovx3_ssh.sh', command], capture_output=True, text=True, timeout=25)
    if result.returncode:
        raise RuntimeError('reader_route_proof_failed: ' + result.stderr[-1800:])
    document = json.loads(result.stdout)
    document['corrects_metadata_reference'] = reference('research_loop/workers/rohin162_console_route_20260917/ovx3.json')
    document['prior_collection_unmodified'] = True
    path = Path(__file__).parent / f'REPO_READER_CONSOLE_ROUTE_{time.time_ns()}.json'
    with path.open('x') as handle:
        json.dump(document, handle, sort_keys=True, indent=2)
        handle.write('\n')
    print(path)
    print(json.dumps({name: document[name] for name in ('status', 'consumer_namespace_root', 'host_delivery_root',
        'archival_host_root_do_not_deliver', 'messages_sent', 'ingestion_proven')}, sort_keys=True))


if __name__ == '__main__':
    main()
