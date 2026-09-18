"""Finite CPU observer. Reads remote tails; writes only this worker's outputs."""

import argparse
import copy
import datetime
import fcntl
import hashlib
import json
import os
from pathlib import Path
import subprocess
import time

from audit import analyze, utc
from collect import OWN, READER, REPOSITORY, TARGETS, target_life


def sha(payload):
    return hashlib.sha256(payload).hexdigest()


def atomic_json(path, value):
    temporary = path.with_name(path.name + '.tmp')
    with temporary.open('w') as output:
        json.dump(value, output, sort_keys=True, indent=2)
        output.write('\n')
    os.replace(temporary, path)


def merge_tail(evidence, batch):
    if (batch['journal_id'] != evidence['journal_id']
            or batch['anchor']['index'] != evidence['head']['index']
            or batch['anchor']['sha256'] != evidence['head']['sha256']):
        raise ValueError('tail_does_not_extend_exact_cut')
    previous = batch['anchor']
    for meta in batch['continuity']:
        if (meta['index'] != previous['index'] + 1 or meta['previous_sha256'] != previous['sha256']
                or meta['journal_id'] != batch['journal_id']):
            raise ValueError('local_tail_chain_mismatch')
        previous = meta
    if previous != batch['through']:
        raise ValueError('tail_through_mismatch')
    known = {meta['index']: meta for meta in batch['continuity']}
    for event in batch['events']:
        meta = known.get(event['record_index'])
        if meta is None or meta['sha256'] != event['record_sha256'] or meta['kind'] != event['kind']:
            raise ValueError('tail_event_identity_mismatch')
    merged = copy.deepcopy(evidence)
    merged['events'].extend(batch['events'])
    merged['continuity'].extend(batch['continuity'])
    merged['head'] = batch['through']
    merged['observed_unix'] = batch['observed_unix']
    return merged


def make_tail_program(label, cursor, limit):
    reader = READER.read_bytes()
    tail_reader = (OWN / 'read_tail.py').read_bytes()
    program = (reader.rsplit(b'\nif __name__', 1)[0] + b'\n' + tail_reader
               + f'\nprint(json.dumps(collect_tail(Path({target_life(label)!r}), {cursor}, {limit}), ensure_ascii=False))\n'.encode())
    return program, dict(reader_sha256=sha(reader), tail_reader_sha256=sha(tail_reader),
                         transported_program_sha256=sha(program))


def read_batch(label, cursor, limit, remaining):
    program, provenance = make_tail_program(label, cursor, limit)
    stamp = str(time.time_ns())
    result = subprocess.run(['bash', str(REPOSITORY / TARGETS[label]),
                             'CUDA_VISIBLE_DEVICES= PYTHONDONTWRITEBYTECODE=1 python3 -B -'],
                            input=program, capture_output=True, timeout=min(45, remaining), cwd=REPOSITORY)
    with (OWN / 'private' / f'{label}_TAIL_{stamp}.stderr').open('xb') as output:
        output.write(result.stderr)
    if result.returncode:
        raise RuntimeError('read_only_tail_transport_failed')
    batch = json.loads(result.stdout)
    with (OWN / 'private' / f'{label}_TAIL_{stamp}.json').open('xb') as output:
        output.write(result.stdout)
    return batch, dict(provenance, batch_file_sha256=sha(result.stdout))


def process_identity():
    fields = Path('/proc/self/stat').read_text().rsplit(')', 1)[1].split()
    return dict(pid=os.getpid(), start_ticks=int(fields[19]), uid=os.getuid())


def run(initial_paths, interval, duration, limit):
    if not 15 <= interval <= 600 or not 30 <= duration <= 7200 or not 1 <= limit <= 256:
        raise ValueError('bounded_observer_configuration_required')
    os.umask(0o077)
    operator = OWN / 'operator'
    history = operator / 'history'
    history.mkdir(parents=True, exist_ok=True)
    lock = (OWN / 'private/observer.lock').open('a')
    fcntl.flock(lock.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
    evidence = {}
    source_parts = {}
    for label, path in initial_paths.items():
        payload = path.read_bytes()
        evidence[label] = json.loads(payload)
        analyze(evidence[label], label)
        source_parts[label] = [sha(payload)]
    started = time.time()
    expiry = started + duration
    identity = process_identity()
    process = dict(schema='R227_READ_ONLY_OBSERVER_PROCESS_V1', **identity,
                   started_utc=utc(started), expires_utc=utc(expiry), interval_seconds=interval,
                   duration_seconds=duration, max_records_per_target_per_poll=limit,
                   targets=sorted(evidence), observer_sha256=sha(Path(__file__).read_bytes()),
                   audit_sha256=sha((OWN / 'audit.py').read_bytes()),
                   child_signals=0, remote_writes=False, parent_messages=0,
                   status='RUNNING', successful_polls={label: 0 for label in evidence})
    atomic_json(operator / 'PROCESS.json', process)
    previous_heads = {}
    try:
        while time.time() < expiry:
            poll_started = time.time()
            for label in evidence:
                remaining = expiry - time.time()
                if remaining <= 0:
                    break
                try:
                    batch, provenance = read_batch(label, evidence[label]['head']['index'], limit, remaining)
                    evidence[label] = merge_tail(evidence[label], batch)
                    source_parts[label].append(provenance['batch_file_sha256'])
                    report = analyze(evidence[label], label)
                    report['audit_module_sha256'] = process['audit_sha256']
                    report['observation'] = dict(provenance, input_part_sha256=source_parts[label][:],
                                               observer_identity=identity, expires_utc=process['expires_utc'],
                                               interval_seconds=interval,
                                               remote_head_index=batch['remote_head']['index'],
                                               backlog_records=batch['remote_head']['index'] - batch['through']['index'],
                                               remote_writes=False, child_signals=0, parent_messages=0)
                    atomic_json(operator / f'{label}_LATEST.json', report)
                    if previous_heads.get(label) != report['head']['index']:
                        filename = f"{label}_{report['head']['index']}_{time.time_ns()}.json"
                        with (history / filename).open('x') as output:
                            json.dump(report, output, sort_keys=True, indent=2)
                            output.write('\n')
                    previous_heads[label] = report['head']['index']
                    process['successful_polls'][label] += 1
                    process.setdefault('heads', {})[label] = report['head']
                    process.setdefault('last_success_utc', {})[label] = utc(time.time())
                except (OSError, ValueError, RuntimeError, subprocess.TimeoutExpired) as error:
                    process.setdefault('errors', []).append(dict(label=label, utc=utc(time.time()), error_type=type(error).__name__))
                atomic_json(operator / 'PROCESS.json', process)
            wait = min(expiry - time.time(), interval - (time.time() - poll_started))
            if wait > 0:
                time.sleep(wait)
        process['status'] = 'EXPIRED_NORMALLY'
    finally:
        process['ended_utc'] = utc(time.time())
        if process['status'] == 'RUNNING':
            process['status'] = 'OBSERVER_EXITED_EARLY'
        atomic_json(operator / 'PROCESS.json', process)
        lock.close()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--c2-evidence', type=Path, required=True)
    parser.add_argument('--p7-evidence', type=Path, required=True)
    parser.add_argument('--interval-seconds', type=int, default=60)
    parser.add_argument('--duration-seconds', type=int, default=3600)
    parser.add_argument('--limit', type=int, default=256)
    arguments = parser.parse_args()
    run({'C2': arguments.c2_evidence, 'P7': arguments.p7_evidence},
        arguments.interval_seconds, arguments.duration_seconds, arguments.limit)
