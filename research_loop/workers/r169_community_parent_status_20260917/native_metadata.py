"""Read-only bounded COMMUNITY process and TRAIN journal metadata; no probe files."""

import hashlib
import json
import os
from pathlib import Path
import re
import stat
import time

from gpu.orch_r125_stream_console import _open_stream_directory
from gpu.orch_r125_stream_journal import _decode, _digest


ROOTS = {branch: '/localhome/local-rohing/orch_r153_community_' + branch + '_20260916_attempt1/life'
    for branch in ('C1', 'C2', 'C3', 'C4', 'C5')}
LIMIT = 64 * 1024 * 1024
used = 0


def read(path, directory=None):
    global used
    descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=directory)
    with os.fdopen(descriptor, 'rb') as stream:
        before = os.fstat(stream.fileno())
        assert stat.S_ISREG(before.st_mode) and before.st_size <= 16 * 1024 * 1024
        assert used + before.st_size <= LIMIT, 'bounded_read_budget'
        raw = stream.read(before.st_size + 1)
        after = os.fstat(stream.fileno())
    assert (before.st_size, before.st_mtime_ns) == (after.st_size, after.st_mtime_ns)
    assert len(raw) == before.st_size
    used += len(raw)
    return _decode(raw), dict(sha256=hashlib.sha256(raw).hexdigest(), bytes=len(raw), mtime_unix=before.st_mtime)


def identity(process):
    global used
    raw = (process / 'stat').read_bytes()
    command = (process / 'cmdline').read_bytes()
    used += len(raw) + len(command)
    fields = raw.decode().rsplit(')', 1)[1].split()
    return dict(pid=int(process.name), start_ticks=fields[19], state=fields[0],
        parent_pid=int(fields[1]), cwd=str((process / 'cwd').resolve()),
        argv=command.rstrip(b'\0').decode().split('\0'), uid=process.stat().st_uid)


def main():
    global used
    natives = {branch: [] for branch in ROOTS}
    for process in Path('/proc').iterdir():
        if not process.name.isdigit():
            continue
        try:
            raw = (process / 'cmdline').read_bytes()
            used += len(raw)
            assert used <= LIMIT
            argv = raw.rstrip(b'\0').decode().split('\0')
            if '-m' not in argv or argv[argv.index('-m') + 1] != 'gpu.orch_r125_continual_guard':
                continue
            if 'native' not in argv or '--config' not in argv:
                continue
            config_path = Path(argv[argv.index('--config') + 1])
            if not re.search(r'_C[1-5]_', str(config_path)):
                continue
            config, config_ref = read(config_path)
            plan, plan_ref = read(Path(config['plan_path']))
            assert plan_ref['sha256'] == config['plan_sha256']
            branches = [branch for branch, root in ROOTS.items() if root == plan['root']]
            if not branches:
                continue
            observed = identity(process)
            assert observed['cwd'] == plan['source_root']
            natives[branches[0]].append(dict(identity=observed, config=dict(path=str(config_path), **config_ref),
                plan=dict(path=config['plan_path'], **plan_ref), resume=config.get('resume')))
        except (FileNotFoundError, ProcessLookupError, PermissionError):
            continue
    results = {}
    for branch, root in ROOTS.items():
        value = dict(root=root, native_processes=natives[branch], observed_unix=time.time())
        try:
            with _open_stream_directory(root, 'records') as (directory, directory_path):
                names = []
                with os.scandir(directory) as entries:
                    for count, entry in enumerate(entries, 1):
                        assert count <= 401024
                        if re.fullmatch(r'[0-9]{20}\.json', entry.name):
                            names.append(entry.name)
                names.sort()
                assert len(names) <= 100000
                previous = None
                for name in reversed(names[-64:]):
                    record, record_ref = read(name, directory)
                    assert record['index'] == int(name[:20])
                    assert record['sha256'] == _digest({key: item for key, item in record.items() if key != 'sha256'})
                    if previous is not None:
                        assert previous == record['sha256']
                    previous = record['previous_sha256']
                    document = record['document']
                    metadata = dict(index=record['index'], kind=record['kind'], journal_id=record['journal_id'],
                        record_sha256=record['sha256'], path=str(directory_path / name), **record_ref)
                    metadata['optimizer_step'] = document.get('optimizer_step')
                    if 'head' not in value:
                        value['head'] = metadata
                    envelope = document.get('state', document.get('resume_state'))
                    if isinstance(envelope, dict) and isinstance(envelope.get('state'), dict) and 'rows' in envelope['state']:
                        assert envelope['sha256'] == _digest(envelope['state'])
                        state = envelope['state']
                        value['checkpoint'] = dict(**metadata, committed_rows=len(state['rows']),
                            pending=state.get('pending') is not None, sleep_frontier=state.get('sleep_frontier'))
                        break
        except Exception as error:
            value['metadata_error'] = dict(type=type(error).__name__, reason=str(error)[:120])
        results[branch] = value
    print(json.dumps(dict(observed_unix=time.time(), communities=results, bytes_read=used,
        byte_limit=LIMIT, sealed_files_read=False, signals_sent=False, basis='bounded_metadata_not_full_chain_audit')))


if __name__ == '__main__':
    main()
