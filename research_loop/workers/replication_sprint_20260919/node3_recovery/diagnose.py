"""Read-only, bounded node-3 outage inspection. This is not an admission tool."""

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import socket
import subprocess
import time


ROOT = Path('/localhome/local-rohing/orch_r205_node3_20260918')
LIVES = (
    'r213_math_a', 'r213_math_b_fork', 'r213_math_c',
    'r213_r226_caption_observation_fork', 'r213_r226_caption_perspective_fork',
    'r213_r226_caption_revision_fork', 'r213_r226_caption_selfderive_fork',
    'r213_r226_caption_unparented_fork',
)
MAX_RECORD_BYTES = 64 * 1024 * 1024
MAX_TAIL_BYTES = 512 * 1024 * 1024
MAX_TAIL_RECORDS = 160


def digest(document):
    return hashlib.sha256(json.dumps(document, sort_keys=True,
        separators=(',', ':'), allow_nan=False).encode()).hexdigest()


def read_json(path):
    return json.loads(path.read_bytes())


def file_receipt(path):
    before = path.stat()
    checksum = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            checksum.update(block)
    after = path.stat()
    stable = (before.st_ino, before.st_size, before.st_mtime_ns) == (
        after.st_ino, after.st_size, after.st_mtime_ns)
    return dict(path=str(path), bytes=before.st_size,
        mtime_unix=before.st_mtime, sha256=checksum.hexdigest(), stable=stable)


def record_summary(record, path):
    document = record['document']
    summary = dict(index=record['index'], kind=record['kind'],
        sha256=record['sha256'], previous_sha256=record['previous_sha256'],
        document_keys=sorted(document), bytes=path.stat().st_size,
        mtime_unix=path.stat().st_mtime)
    summary['digest_valid'] = record['sha256'] == digest({
        key: value for key, value in record.items() if key != 'sha256'})
    for key in ('finished_unix', 'started_unix', 'cycle', 'completed_sleeps',
                'optimizer_step', 'stage', 'operation', 'request_id'):
        if key in document:
            summary[key] = document[key]
    request = document.get('request')
    if isinstance(request, dict):
        summary['request_keys'] = sorted(request)
        summary['request'] = {key: value for key, value in request.items()
            if key in ('kind', 'operation', 'cycle', 'stage', 'request_id')}
    resume = document.get('resume_state', document.get('state'))
    if isinstance(resume, dict):
        summary['resume_keys'] = sorted(resume)
        state = resume.get('state', resume)
        if isinstance(state, dict):
            summary['resume_state_sha256'] = digest(resume)
            summary['state_keys'] = sorted(state)
            summary['rows_count'] = len(state.get('rows', []))
            summary['sleep_frontier'] = state.get('sleep_frontier')
            pending = state.get('pending')
            summary['pending'] = ({key: value for key, value in pending.items()
                if key in ('kind', 'request_id', 'cycle', 'operation')}
                if isinstance(pending, dict) else pending)
    checkpoint = document.get('checkpoint')
    if isinstance(checkpoint, dict):
        summary['checkpoint'] = {key: value for key, value in checkpoint.items()
            if key in ('checkpoint_sha256', 'optimizer_steps', 'adapter_path',
                'optimizer_rng_path', 'adapter_state_sha256', 'schema')}
    intent_path = path.with_name(path.stem + '.intent.json')
    expected = {key: record[key] for key in (
        'schema', 'journal_id', 'index', 'previous_sha256')}
    expected['record_sha256'] = record['sha256']
    try:
        summary['intent_valid'] = read_json(intent_path) == expected
    except (ValueError, OSError) as error:
        summary['intent_valid'] = False
        summary['intent_error'] = str(error)
    return summary


def inspect_tail(raw):
    directory = raw / 'stream' / 'records'
    paths = sorted(path for path in directory.iterdir()
        if re.fullmatch(r'\d{20}\.json', path.name))
    manifest = read_json(raw / 'stream' / 'JOURNAL.json')
    report = dict(journal_id=manifest['journal_id'],
        records_count=len(paths), bounded=True, full_history_audited=False,
        tail=[], failures=[], bytes_read=0)
    complete = None
    for path in reversed(paths[-MAX_TAIL_RECORDS:]):
        size = path.stat().st_size
        if size > MAX_RECORD_BYTES or report['bytes_read'] + size > MAX_TAIL_BYTES:
            report['failures'].append(dict(path=str(path), reason='bounded_read_limit'))
            break
        report['bytes_read'] += size
        try:
            record = read_json(path)
            summary = record_summary(record, path)
            summary['journal_id_valid'] = record['journal_id'] == manifest['journal_id']
            report['tail'].append(summary)
            if record['kind'] == 'SLEEP_COMPLETE':
                complete = record
                report['last_complete'] = summary
                break
        except (ValueError, KeyError, OSError) as error:
            report['failures'].append(dict(path=str(path), bytes=size,
                reason=type(error).__name__, detail=str(error)))
    report['tail'].reverse()
    report['tail_links_valid'] = all(
        current['index'] == previous['index'] + 1 and
        current['previous_sha256'] == previous['sha256']
        for previous, current in zip(report['tail'], report['tail'][1:]))
    report['unpaired_or_partial_files'] = [dict(name=path.name,
        bytes=path.stat().st_size) for path in sorted(directory.iterdir())
        if (path.name.endswith('.partial') or
            (path.name.endswith('.intent.json') and not path.with_name(
                path.name.replace('.intent.json', '.json')).exists()))][-20:]
    return report, complete


def inspect_checkpoints(raw):
    directories = sorted((raw / 'checkpoints').glob('sleep_*'))[-3:]
    results = []
    for directory in directories:
        result = dict(name=directory.name, files=[dict(
            name=str(path.relative_to(directory)), bytes=path.stat().st_size)
            for path in directory.rglob('*') if path.is_file()])
        commit_path = directory / 'COMMIT.json'
        if not commit_path.exists() or not commit_path.stat().st_size:
            result['status'] = 'UNCOMMITTED_PRESERVE_DO_NOT_LOAD'
            results.append(result)
            continue
        commit = read_json(commit_path)
        result['commit'] = file_receipt(commit_path)
        result['optimizer_steps'] = commit['optimizer_steps']
        result['checkpoint_sha256'] = commit['checkpoint_sha256']
        result['adapter_files'] = {
            name: dict(expected=expected, actual=file_receipt(directory / 'adapter' / name))
            for name, expected in commit['adapter_files'].items()}
        result['optimizer_rng'] = file_receipt(directory / 'optimizer_rng.pt')
        result['file_hashes_match'] = all(
            item['expected'] == item['actual']['sha256'] and item['actual']['stable']
            for item in result['adapter_files'].values()) and (
            result['optimizer_rng']['sha256'] == commit['checkpoint_sha256']['optimizer']
            == commit['checkpoint_sha256']['rng'] and result['optimizer_rng']['stable'])
        result['tensor_payload_not_loaded'] = True
        results.append(result)
    return results


def inspect_life(name, now):
    life = ROOT / name
    active = read_json(life / 'ACTIVE_RUNTIME.json')
    control = Path(active['control'])
    plan = read_json(control / 'PLAN.json')
    guard = read_json(control / 'GUARD.json')
    lease = read_json(control / 'LEASE.json')
    result = dict(life=name, active=active, control=str(control),
        plan=file_receipt(control / 'PLAN.json'), guard=file_receipt(control / 'GUARD.json'),
        physical_gpu=plan['physical'], gpu_uuid=plan['gpu_uuid'],
        hard_end_unix=plan['hard_end_unix'], lease_end_unix=lease['lease_end_unix'],
        original_lease_bound_unexpired=now < plan['hard_end_unix'] <= lease['lease_end_unix'],
        learn_row_policy=plan.get('learn_row_policy'),
        guard_plan_hash_matches=guard['plan_sha256'] == file_receipt(control / 'PLAN.json')['sha256'])
    exit_path = control / 'EXIT.json'
    result['exit'] = file_receipt(exit_path)
    result['downtime_seconds_lower_bound'] = now - exit_path.stat().st_mtime
    if exit_path.stat().st_size:
        result['exit']['document'] = read_json(exit_path)
    native_log = control / 'NATIVE.log'
    text = native_log.read_text(errors='replace')
    result['native_log'] = file_receipt(native_log)
    result['enospc_in_native_log'] = 'No space left on device' in text
    result['error_lines'] = [line.strip() for line in text.splitlines()
        if any(term in line for term in ('Error', 'record(', 'checkpoint =', 'receipt ='))][-12:]
    raw = Path(guard['copy_raw'])
    result['tail'], complete = inspect_tail(raw)
    result['checkpoints'] = inspect_checkpoints(raw)
    result['checkpoint_matches_complete'] = bool(complete and any(
        checkpoint.get('checkpoint_sha256') == complete['document'].get('checkpoint', {}).get('checkpoint_sha256')
        and checkpoint.get('file_hashes_match')
        for checkpoint in result['checkpoints']))
    source = Path(active['source'])
    result['source_pins_checked'] = {}
    for relative, expected in guard['source_pins'].items():
        receipt = file_receipt(source / relative)
        result['source_pins_checked'][relative] = dict(
            expected=expected, actual=receipt['sha256'], stable=receipt['stable'])
    result['all_source_pins_match'] = all(item['actual'] == item['expected'] and item['stable']
        for item in result['source_pins_checked'].values())
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--life', choices=LIVES, action='append')
    arguments = parser.parse_args()
    now = time.time()
    filesystem = os.statvfs(ROOT)
    report = dict(schema='NODE3_BOUNDED_READONLY_DIAGNOSIS_V1', captured_unix=now,
        host=socket.gethostname(), boot_id=Path('/proc/sys/kernel/random/boot_id').read_text().strip(),
        uptime_seconds=float(Path('/proc/uptime').read_text().split()[0]),
        filesystem_available_bytes=filesystem.f_bavail * filesystem.f_frsize,
        filesystem_unallocated_bytes_including_reserved=filesystem.f_bfree * filesystem.f_frsize,
        gpu_state=subprocess.check_output(['nvidia-smi', '--query-gpu=index,uuid,memory.used',
            '--format=csv,noheader'], text=True),
        compute_apps=subprocess.check_output(['nvidia-smi',
            '--query-compute-apps=pid,process_name,used_gpu_memory', '--format=csv,noheader'], text=True),
        observations_only_not_launch_authority=True, lives=[])
    for name in arguments.life or LIVES:
        try:
            report['lives'].append(inspect_life(name, now))
        except (OSError, ValueError, KeyError) as error:
            report['lives'].append(dict(life=name, audit_error=type(error).__name__, detail=str(error)))
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == '__main__':
    main()
