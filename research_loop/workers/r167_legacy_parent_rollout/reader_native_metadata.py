"""Exact existing R154 reader bind-mount custody; metadata only, no mutation."""

import hashlib
import json
from pathlib import Path
import socket
import time


PID = 2611440
RUNTIME_ROOT = '/localhome/local-rohing/orch_r136_repo_reader_20260916_attempt1/run1'
HOST_ROOT = '/localhome/local-rohing/orch_r136_repo_reader_20260916_attempt1/recovery_r154_saved30_20260916_attempt2/run1'


def verify_projection(rows, mounts):
    assert len(rows) == 3 and {row['relative'] for row in rows} == {
        'stream/WRITER.lock', 'stream/records', 'stream/inbox'}
    assert all(row['host'] == row['namespace'] == row['fd'] for row in rows)
    assert len(mounts) == 1 and mounts[0] == dict(source=HOST_ROOT, target=RUNTIME_ROOT)


def scan():
    process = Path('/proc') / str(PID)
    before = (process / 'stat').read_text().rsplit(')', 1)[1].split()
    raw = (process / 'cmdline').read_bytes()
    argv = raw.rstrip(b'\0').decode().split('\0')
    assert argv[argv.index('-m') + 1] == 'gpu.orch_r125_continual_guard' and 'native' in argv
    guard_path = Path(argv[argv.index('--config') + 1])
    assert str(guard_path) == '/localhome/local-rohing/orch_r157_repo_reader_wall_20260917_attempt2/GUARD.json'
    assert guard_path.stat().st_size < 1048576
    guard_raw = guard_path.read_bytes()
    guard = json.loads(guard_raw)
    plan_path = Path(guard['plan_path'])
    assert plan_path.stat().st_size < 1048576
    plan_raw = plan_path.read_bytes()
    assert hashlib.sha256(plan_raw).hexdigest() == guard['plan_sha256']
    plan = json.loads(plan_raw)
    assert plan['root'] == RUNTIME_ROOT
    descriptor_paths = {}
    for descriptor in (process / 'fd').iterdir():
        try:
            descriptor_paths[str(descriptor.readlink())] = descriptor
        except OSError:
            continue
    rows = []
    for relative in ('stream/WRITER.lock', 'stream/records', 'stream/inbox'):
        host = (Path(HOST_ROOT) / relative).stat()
        namespace = (process / 'root' / RUNTIME_ROOT.lstrip('/') / relative).stat()
        descriptor = descriptor_paths[RUNTIME_ROOT + '/' + relative].stat()
        rows.append(dict(relative=relative, host=[host.st_dev, host.st_ino],
            namespace=[namespace.st_dev, namespace.st_ino], fd=[descriptor.st_dev, descriptor.st_ino]))
    mounts = []
    for line in (process / 'mountinfo').read_text().splitlines():
        fields = line.split()
        if fields[4] == RUNTIME_ROOT:
            mounts.append(dict(source=fields[3], target=fields[4]))
    verify_projection(rows, mounts)
    after = (process / 'stat').read_text().rsplit(')', 1)[1].split()
    assert before[19] == after[19] and (process / 'cmdline').read_bytes() == raw
    return dict(schema='R167_READER_EXACT_NAMESPACE_CUSTODY_V1', hostname=socket.gethostname(),
        observed_unix=time.time(), native=dict(pid=PID, start_ticks=after[19], state=after[0],
            argv_sha256=hashlib.sha256(raw).hexdigest(),
            plans=[dict(path=str(guard_path), sha256=hashlib.sha256(guard_raw).hexdigest()),
                dict(path=str(plan_path), sha256=guard['plan_sha256'], root=plan['root'])],
            root_binding=dict(host_root=HOST_ROOT, runtime_root=RUNTIME_ROOT, inodes=rows, mounts=mounts)),
        no_signals=True, no_readout_contents=True)


if __name__ == '__main__':
    print(json.dumps(scan(), sort_keys=True))
