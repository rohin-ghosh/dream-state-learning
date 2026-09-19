"""Bounded node2 inspection; remote branch only reads, local branch saves a receipt."""

import hashlib
import json
import os
from pathlib import Path
import re
import stat
import subprocess
import sys
import time


BASES = {
    'C0': '/localhome/local-rohing/orch_r216_C0_20260918_attempt2',
    'Astra7': '/localhome/local-rohing/orch_r229_Astra7_20260918',
}
GUARDS = {
    'C0': 'acf4d2d015874af1cc9585a25de63827e7d7ec36acd7a4509bce09671985f6c2',
    'Astra7': 'fae6f4ede1e9c80be060aeca8dd494cbb24a6228b9225e33856b62ec3c0047f6',
}
HEADER = re.compile(rb',"index":([0-9]+),"journal_id":"([^"]+)","kind":"([^"]+)",'
    rb'"previous_sha256":"([0-9a-f]{64})","schema":"([^"]+)","sha256":"([0-9a-f]{64})"}\n?\Z')
SOURCES = ('gpu/r233_node2_recovery.py', 'gpu/r205_runtime.py',
    'gpu/r213_recovery_runtime.py', 'gpu/r229_p7_inbox.py',
    'gpu/r184_node2_confinement.py', 'gpu/orch_r125_continual_guard.py',
    'gpu/orch_r125_continual_native.py', 'gpu/orch_r125_stream_journal.py',
    'gpu/orch_r184_think_act_learn.py', 'gpu/checkpoint_tail_runtime.py')


def identity(metadata):
    return dict(dev=metadata.st_dev, ino=metadata.st_ino, size=metadata.st_size,
        mode=metadata.st_mode, mtime_ns=metadata.st_mtime_ns, ctime_ns=metadata.st_ctime_ns)


def read_bytes(path, limit):
    descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    with os.fdopen(descriptor, 'rb') as stream:
        before = identity(os.fstat(stream.fileno()))
        if not stat.S_ISREG(before['mode']) or before['size'] > limit:
            raise ValueError('bounded_regular_file_required: ' + str(path))
        raw = stream.read(limit + 1)
        if len(raw) != before['size'] or identity(os.fstat(stream.fileno())) != before:
            raise ValueError('changed_during_read: ' + str(path))
    return raw


def load(path, limit=4 * 1024 * 1024):
    raw = read_bytes(path, limit)
    return json.loads(raw), hashlib.sha256(raw).hexdigest()


def small_fields(value):
    if not isinstance(value, dict):
        return {'value_type': type(value).__name__}
    allowed = ('cycle', 'status', 'checkpoint', 'checkpoint_sha256', 'optimizer_steps',
        'checkpoint_path', 'checkpoint_commit_sha256', 'adapter_state_sha256',
        'schema', 'path', 'sha256', 'files', 'model_state_sha256', 'deadline_unix',
        'sleep_frontier', 'revision', 'generation_index', 'sleep_count')
    return {key: value[key] for key in allowed if key in value
        and len(json.dumps(value[key])) <= 8192}


def header(path):
    descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    with os.fdopen(descriptor, 'rb') as stream:
        before = identity(os.fstat(stream.fileno()))
        if not stat.S_ISREG(before['mode']):
            raise ValueError('regular_record_required')
        stream.seek(max(0, before['size'] - 4096))
        match = HEADER.search(stream.read(4096))
        if not match or identity(os.fstat(stream.fileno())) != before:
            raise ValueError('invalid_or_changed_bounded_header: ' + str(path))
    values = [item.decode() for item in match.groups()]
    result = dict(zip(('index', 'journal_id', 'kind', 'previous_sha256', 'schema', 'sha256'), values))
    result['index'] = int(result['index'])
    if path.name != f"{result['index']:020d}.json":
        raise ValueError('record_filename_index_mismatch')
    return dict(result, file=identity(path.lstat()))


def record_summary(path):
    value, raw_sha = load(path, 128 * 1024 * 1024)
    document = value['document']
    result = dict(index=value['index'], kind=value['kind'], record_sha256=value['sha256'],
        raw_file_sha256=raw_sha, document_keys=sorted(document), fields=small_fields(document),
        canonical_record_hash_verified=False)
    saved = document.get('resume_state', document.get('state'))
    if isinstance(saved, dict) and isinstance(saved.get('state'), dict):
        state = saved['state']
        result['saved_state'] = dict(sha256=saved.get('sha256'), keys=sorted(state),
            fields=small_fields(state), rows=len(state.get('rows', [])),
            sleep_receipts=len(state.get('sleep_receipts', [])),
            pending_is_null=state.get('pending') is None,
            collection_sizes={key: len(item) for key, item in state.items()
                if isinstance(item, (list, dict))})
    return result


def inspect_life(life, base_name):
    base = Path(base_name)
    control = base / 'control_r233_lease_continuation'
    guard, guard_sha = load(control / 'GUARD.json')
    if guard_sha != GUARDS[life]:
        raise ValueError('previously_pinned_guard_changed')
    plan, plan_sha = load(Path(guard['plan_path']))
    if plan_sha != guard['plan_sha256']:
        raise ValueError('plan_pin_mismatch')
    raw_root = Path(guard['copy_raw'])
    records = raw_root / 'stream/records'
    names = sorted(item.name for item in records.iterdir())
    record_names = [name for name in names if re.fullmatch(r'[0-9]{20}\.json', name)]
    newest = [header(records / name) for name in record_names[-512:]]
    complete = next((item for item in reversed(newest) if item['kind'] == 'SLEEP_COMPLETE'), None)
    learn = next((item for item in reversed(newest) if item['kind'] == 'R184_LEARN_COMPLETE'), None)
    result = dict(life=life, guard_path=str(control / 'GUARD.json'), guard_sha256=guard_sha,
        plan_path=str(guard['plan_path']), plan_sha256=plan_sha,
        plan={key: plan.get(key) for key in ('root', 'source_root', 'physical', 'gpu_uuid',
            'hard_end_unix', 'lease_end_unix', 'learn_row_policy', 'checkpoint_tail_recovery', 'anchors')},
        guard={key: guard[key] for key in ('resume', 'copy_raw', 'attempt_dir', 'next_reserved_unix')},
        records_count=len(record_names), inspected_header_count=len(newest),
        head=newest[-1] if newest else None, latest_complete_header=complete,
        latest_learn_header=learn, tail_headers=[item for item in newest
            if complete and item['index'] >= complete['index']],
        unexpected_record_entries=[dict(name=name, **identity((records / name).lstat()))
            for name in names if not re.fullmatch(r'[0-9]{20}(\.intent)?\.json', name)],
        missing_record_intents=[name for name in record_names if name[:-5] + '.intent.json' not in names],
        controls={}, sources={}, checkpoint_directories=[])
    for name in ('EXIT.json', 'OUTER_EXIT.json', 'FAILED.json', 'LAUNCH.json',
            'CONFINEMENT_CHILD.json', 'ALLOCATION.json', 'LEASE.json'):
        path = control / name
        if path.exists():
            raw = read_bytes(path, 1024 * 1024)
            result['controls'][name] = dict(identity=identity(path.lstat()),
                sha256=hashlib.sha256(raw).hexdigest(), value=json.loads(raw) if raw else None)
    log = control / 'NATIVE.log'
    if log.exists() and log.stat().st_size <= 65536:
        result['native_log_tail'] = read_bytes(log, 65536).decode(errors='replace')[-5000:]
    for relative in SOURCES:
        path = Path(plan['source_root']) / relative
        if path.exists():
            data = read_bytes(path, 2 * 1024 * 1024)
            result['sources'][relative] = dict(sha256=hashlib.sha256(data).hexdigest(),
                guard_pin=guard['source_pins'].get(relative), size=len(data))
        else:
            result['sources'][relative] = dict(exists=False)
    selected = {item['index'] for item in (complete, learn, newest[-1] if newest else None) if item}
    result['selected_records'] = []
    for index in sorted(selected):
        try:
            result['selected_records'].append(record_summary(records / f'{index:020d}.json'))
        except (ValueError, OSError) as error:
            result['selected_records'].append(dict(index=index, bounded_read_error=str(error)))
    for path in sorted((raw_root / 'checkpoints').iterdir())[-3:]:
        entry = dict(path=str(path), identity=identity(path.lstat()))
        if path.is_dir():
            entry['files'] = [dict(name=item.name, **identity(item.lstat())) for item in sorted(path.iterdir())]
            for candidate in ('COMMIT.json', 'MANIFEST.json', 'manifest.json', 'checkpoint.json'):
                target = path / candidate
                if target.exists() and target.stat().st_size <= 65536:
                    value, digest = load(target, 65536)
                    entry[candidate] = dict(sha256=digest, keys=sorted(value), fields=small_fields(value))
        result['checkpoint_directories'].append(entry)
    result['record_listing_unchanged'] = names == sorted(item.name for item in records.iterdir())
    return result


def remote_main():
    started = time.monotonic()
    result = dict(schema='NODE2_ENOSPC_READ_ONLY_V1', observed_unix=time.time(),
        boot_id=Path('/proc/sys/kernel/random/boot_id').read_text().strip(),
        root_available_bytes=os.statvfs('/').f_bavail * os.statvfs('/').f_frsize,
        native_pid_exists={str(pid): Path('/proc', str(pid)).exists() for pid in (881309, 886059)},
        full_journal_audit=False, source_code_executed=False, node_writes=False,
        native_signals=[], journal_bodies_exported=False, lives=[])
    for life, base in BASES.items():
        try:
            result['lives'].append(inspect_life(life, base))
        except Exception as error:
            result['lives'].append(dict(life=life, error_type=type(error).__name__, error=str(error)))
    result['elapsed_seconds'] = time.monotonic() - started
    print(json.dumps(result, sort_keys=True))


if __name__ == '__main__':
    if sys.argv[1:] == ['--remote-read-only']:
        remote_main()
    elif len(sys.argv) == 3 and sys.argv[1] == '--receipt':
        completed = subprocess.run(['bash', 'gpu/ovx_ssh.sh', 'python3 -B - --remote-read-only'],
            input=Path(__file__).read_bytes(), stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=60)
        receipt = dict(returncode=completed.returncode, stderr=completed.stderr.decode(errors='replace'),
            inspector_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            report=json.loads(completed.stdout) if completed.returncode == 0 else None)
        with Path(sys.argv[2]).open('x') as stream:
            json.dump(receipt, stream, sort_keys=True, indent=2)
            stream.write('\n')
        print(json.dumps(dict(path=sys.argv[2], returncode=completed.returncode,
            elapsed_seconds=receipt['report']['elapsed_seconds'] if receipt['report'] else None)))
    else:
        raise SystemExit('use --receipt NEW_LOCAL_PATH or --remote-read-only')
