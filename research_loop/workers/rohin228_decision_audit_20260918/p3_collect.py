"""Own-scope finite, incremental P3 read-only observer; no model or control calls."""

import argparse
import datetime
import fcntl
import json
import os
from pathlib import Path
import subprocess
import time

from observe import atomic_json, identity, utc
from p3_audit import project
from source_adapter import OWN, PREVIOUS, merge, sha


REPOSITORY = OWN.parents[2]
ACCOUNTING = OWN.parent / 'rohin221_continuous_caption_20260918/audit_metrics.py'
if not ACCOUNTING.exists():
    ACCOUNTING = OWN / 'accounting_snapshot.py'


def collect(after=None, start_cycle=69):
    config = json.loads((OWN / 'private/P3_TARGET.json').read_bytes())
    if set(config) != {'life', 'sessions'} or not Path(config['life']).is_absolute():
        raise ValueError('private_target_configuration_required')
    modules = [PREVIOUS / 'journal_reader.py', PREVIOUS / 'read_tail.py', ACCOUNTING, OWN / 'p3_read.py']
    payloads = [path.read_bytes() for path in modules]
    operation = f'collect_window(life, {start_cycle!r}, 1600)' if after is None else f'collect_tail(life, {after!r}, 256)'
    program = b'\n'.join(payload.rsplit(b'\nif __name__', 1)[0] for payload in payloads)
    program += (f'\nCONFIG={config!r}\nlife=Path(CONFIG["life"])\n'
                'WANTED.discard("INBOX")\n'
                f'journal={operation}\n'
                'print(json.dumps(dict(journal=journal,receipts=scorer_receipts(CONFIG["sessions"]),'
                'scorer_observed_unix=time.time()),ensure_ascii=False))\n').encode()
    wrapper = REPOSITORY / 'gpu/a40r_ssh.sh'
    stamp = str(time.time_ns())
    try:
        result = subprocess.run(['bash', str(wrapper), 'CUDA_VISIBLE_DEVICES= PYTHONDONTWRITEBYTECODE=1 python3 -B -'],
                                input=program, capture_output=True, timeout=75, cwd=REPOSITORY)
    except subprocess.TimeoutExpired as error:
        (OWN / f'private/P3_{stamp}.stderr').write_bytes(error.stderr or b'')
        raise ValueError('bounded_read_timeout_private_error_retained') from None
    (OWN / f'private/P3_{stamp}.stderr').write_bytes(result.stderr)
    if result.returncode:
        raise ValueError('bounded_read_failed_private_error_retained')
    document = json.loads(result.stdout)
    source_path = OWN / f'private/P3_{stamp}.json'
    source_path.write_bytes(result.stdout)
    provenance = dict(input_file_sha256=sha(result.stdout), transported_program_sha256=sha(program),
                      modules={path.name: sha(payload) for path, payload in zip(modules, payloads)},
                      wrapper_sha256=sha(wrapper.read_bytes()), remote_writes=False, learner_signals=0,
                      inbox_writes=0, scorer_observed_utc=utc(document['scorer_observed_unix']),
                      scorer_cut_not_atomic_with_journal=True)
    return document, provenance


def run(interval=60, maximum_seconds=1800, start_cycle=69):
    if not 30 <= interval <= 600 or not 30 <= maximum_seconds <= 3600 or not 2 <= start_cycle <= 10000:
        raise ValueError('bounded_P3_observer_required')
    os.umask(0o077)
    (OWN / 'private').mkdir(mode=0o700, exist_ok=True)
    operator = OWN / 'operator'
    (operator / 'p3_history').mkdir(parents=True, exist_ok=True)
    lock = (OWN / 'private/p3_observer.lock').open('a')
    fcntl.flock(lock.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
    started = time.time()
    expiry = started + maximum_seconds
    process = dict(schema='R228_P3_READ_ONLY_OBSERVER_PROCESS_V1', **identity(),
                   started_utc=utc(started), expires_utc=utc(expiry), interval_seconds=interval,
                   status='RUNNING', successful_projections=0, start_cycle=start_cycle,
                   learner_signals=0, inbox_writes=0, parent_messages=0, GPU_calls=0,
                   source_files={name: sha((OWN / name).read_bytes()) for name in (
                       'p3_collect.py', 'p3_read.py', 'p3_audit.py', 'decision_audit.py', 'source_adapter.py')})
    atomic_json(operator / 'P3_PROCESS.json', process)
    evidence = None
    source_hashes = []
    try:
        while time.time() < expiry:
            poll_start = time.time()
            try:
                document, provenance = collect(evidence['head']['index'] if evidence else None, start_cycle)
                evidence = merge(evidence, document['journal']) if evidence else document['journal']
                source_hashes.append(provenance['input_file_sha256'])
                report = project(evidence, document['receipts'], provenance)
                report['observation'] = dict(observer_pid=process['pid'], start_ticks=process['start_ticks'],
                                           input_part_sha256=source_hashes[:], interval_seconds=interval,
                                           expires_utc=process['expires_utc'], projection_utc=utc(time.time()))
                atomic_json(operator / 'P3_LATEST.json', report)
                atomic_json(operator / 'p3_history' / f"P3_{report['head']['index']}_{time.time_ns()}.json", report)
                process['successful_projections'] += 1
                process['head'] = report['head']
                process['last_success_utc'] = utc(time.time())
                process['last_source_cut_utc'] = report['observed_utc']
                process['game_coverage'] = report['game_coverage']
            except (OSError, ValueError, KeyError) as error:
                process.setdefault('errors', []).append(dict(utc=utc(time.time()), error_type=type(error).__name__))
            atomic_json(operator / 'P3_PROCESS.json', process)
            delay = min(expiry-time.time(), interval-(time.time()-poll_start))
            if delay > 0:
                time.sleep(delay)
        process['status'] = 'EXPIRED_NORMALLY'
    finally:
        process['ended_utc'] = utc(time.time())
        if process['status'] == 'RUNNING':
            process['status'] = 'OBSERVER_EXITED_EARLY'
        atomic_json(operator / 'P3_PROCESS.json', process)
        lock.close()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--interval-seconds', type=int, default=60)
    parser.add_argument('--maximum-seconds', type=int, default=1800)
    parser.add_argument('--start-cycle', type=int, default=69)
    arguments = parser.parse_args()
    run(arguments.interval_seconds, arguments.maximum_seconds, arguments.start_cycle)
