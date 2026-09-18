"""Finite local-only decision projections over the already-running R227 reader."""

import argparse
import datetime
import fcntl
import json
import os
from pathlib import Path
import time

from decision_audit import analyze
from source_adapter import OWN, from_observer, prior_watcher_receipt, sha


def utc(timestamp):
    return datetime.datetime.fromtimestamp(timestamp, datetime.timezone.utc).isoformat()


def identity():
    fields = Path('/proc/self/stat').read_text().rsplit(')', 1)[1].split()
    return dict(pid=os.getpid(), start_ticks=int(fields[19]), uid=os.getuid())


def atomic_json(path, value):
    temporary = path.with_name(path.name + '.tmp')
    with temporary.open('w') as output:
        json.dump(value, output, sort_keys=True, indent=2)
        output.write('\n')
    os.replace(temporary, path)


def retain_new_raw(label, evidence, report, seen):
    responses = {event['source_sha256']: event for event in evidence['events'] if event['kind'] == 'RESPONSE'}
    additions = []
    for row in report['rows']:
        source = row['source_sha256']
        if source not in seen:
            additions.append(dict(metadata=row, raw_response=responses[source]['document']['response']['raw']))
            seen.add(source)
    if additions:
        with (OWN / 'private' / f'{label}_RAW_DECISION_SOURCES.jsonl').open('a') as output:
            for entry in additions:
                output.write(json.dumps(entry, ensure_ascii=False) + '\n')


def run(interval=60, maximum_seconds=3600):
    if not 15 <= interval <= 600 or not 30 <= maximum_seconds <= 7200:
        raise ValueError('bounded_local_observer_required')
    os.umask(0o077)
    private = OWN / 'private'
    private.mkdir(mode=0o700, exist_ok=True)
    operator = OWN / 'operator'
    history = operator / 'history'
    history.mkdir(parents=True, exist_ok=True)
    lock = (private / 'observer.lock').open('a')
    fcntl.flock(lock.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
    prior = prior_watcher_receipt()
    if not prior['proc_identity_matches'] or prior['status'] != 'RUNNING':
        lock.close()
        raise ValueError('prior_reader_not_running_no_restart_attempted')
    started = time.time()
    expiry = min(started + maximum_seconds, datetime.datetime.fromisoformat(prior['expires_utc']).timestamp())
    if expiry <= started:
        lock.close()
        raise ValueError('prior_reader_window_already_expired')
    process = dict(schema='R228_LOCAL_DECISION_OBSERVER_PROCESS_V1', **identity(),
                   started_utc=utc(started), expires_utc=utc(expiry), interval_seconds=interval,
                   decision_module_sha256=sha((OWN / 'decision_audit.py').read_bytes()),
                   observer_sha256=sha(Path(__file__).read_bytes()),
                   source_adapter_sha256=sha((OWN / 'source_adapter.py').read_bytes()),
                   upstream_pid=prior['pid'], upstream_start_ticks=prior['start_ticks'],
                   successful_projections={'C2': 0, 'P7': 0}, status='RUNNING',
                   remote_calls=0, learner_signals=0, inbox_writes=0, parent_messages=0,
                   upstream_restarted=False, upstream_expiry_extended=False)
    atomic_json(operator / 'PROCESS.json', process)
    seen = {'C2': set(), 'P7': set()}
    previous_heads = {}
    try:
        while time.time() < expiry:
            poll_started = time.time()
            prior = prior_watcher_receipt()
            atomic_json(operator / 'R227_WATCHER_STATE.json', prior)
            process['upstream_identity_matches'] = prior['proc_identity_matches']
            process['upstream_status'] = prior['status']
            process['upstream_last_success_utc'] = prior['last_success_utc']
            for label in ('C2', 'P7'):
                if time.time() >= expiry:
                    break
                try:
                    evidence, provenance = from_observer(label)
                    report = analyze(evidence, label)
                    report['source_observer'] = provenance
                    report['decision_module_sha256'] = process['decision_module_sha256']
                    report['projection_utc'] = utc(time.time())
                    report['observation'] = dict(observer_pid=process['pid'], start_ticks=process['start_ticks'],
                                               expires_utc=process['expires_utc'], interval_seconds=interval,
                                               source_age_seconds=max(0, time.time() - datetime.datetime.fromisoformat(report['observed_utc']).timestamp()),
                                               local_source_only=True, remote_calls=0)
                    retain_new_raw(label, evidence, report, seen[label])
                    atomic_json(operator / f'{label}_LATEST.json', report)
                    if previous_heads.get(label) != report['head']['index']:
                        with (history / f"{label}_{report['head']['index']}_{time.time_ns()}.json").open('x') as output:
                            json.dump(report, output, sort_keys=True, indent=2)
                            output.write('\n')
                    previous_heads[label] = report['head']['index']
                    process['successful_projections'][label] += 1
                    process.setdefault('heads', {})[label] = report['head']
                    process.setdefault('last_success_utc', {})[label] = utc(time.time())
                except (OSError, ValueError, KeyError) as error:
                    process.setdefault('errors', []).append(dict(label=label, utc=utc(time.time()), error_type=type(error).__name__))
                atomic_json(operator / 'PROCESS.json', process)
            delay = min(expiry - time.time(), interval - (time.time() - poll_started))
            if delay > 0:
                time.sleep(delay)
        process['status'] = 'EXPIRED_NORMALLY'
    finally:
        process['ended_utc'] = utc(time.time())
        if process['status'] == 'RUNNING':
            process['status'] = 'OBSERVER_EXITED_EARLY'
        atomic_json(operator / 'PROCESS.json', process)
        lock.close()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--interval-seconds', type=int, default=60)
    parser.add_argument('--maximum-seconds', type=int, default=3600)
    arguments = parser.parse_args()
    run(arguments.interval_seconds, arguments.maximum_seconds)
