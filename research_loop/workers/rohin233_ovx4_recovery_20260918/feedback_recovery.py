"""Incremental future-result Tool delivery using the original locked dedup ledger."""

import argparse
import fcntl
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import time


def pending_paths(session, processed):
    ready = []
    for path in session.glob('attempts/*/RESULT.json'):
        status = path.stat()
        identity = (status.st_ino, status.st_size, status.st_mtime_ns)
        if path in processed:
            if processed[path] != identity:
                raise ValueError('immutable_future_result_changed')
        else:
            ready.append((path, identity))
    return ready


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--config', type=Path, required=True)
    args = parser.parse_args()
    config = json.loads(args.config.read_bytes())
    if not time.time() < config['deadline_unix'] <= config['lease_boundary_unix'] - 21600:
        raise ValueError('six_hour_margin_required')
    dependency = Path(config['relay_source'])
    if hashlib.sha256(dependency.read_bytes()).hexdigest() != config['relay_sha256']:
        raise ValueError('original_frozen_feedback_publisher')
    spec = importlib.util.spec_from_file_location('frozen_caption_feedback', dependency)
    relay = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(relay)
    output, session, life = Path(config['ledger']), Path(config['session']), Path(config['life'])
    receipt_root = Path(config['receipt_root'])
    receipt_root.mkdir(mode=0o700, exist_ok=False)
    processed = {}
    with (output / 'WRITER.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        preserved = {str(path.relative_to(output)): hashlib.sha256(path.read_bytes()).hexdigest()
            for folder in ('published', 'projections') for path in (output / folder).glob('*.json')}
        relay.write_once(receipt_root / 'STARTED.json', dict(unix=time.time(), pid=os.getpid(),
            end_unix=config['deadline_unix'], prior_receipts=len(preserved), prior_inventory_sha256=relay.digest(preserved),
            relay_source_sha256=config['relay_sha256'], future_session_only=True, parent_publications=[],
            learner_signals=[], scoring_calls=0, journal_scan_each_poll=False))
        while time.time() < config['deadline_unix']:
            sessions = [Path(value) for value in config.get('sessions', [str(session)])]
            for path, identity in [item for current in sessions for item in pending_paths(current, processed)]:
                try:
                    document, reference = relay.load(path)
                    if document['unix'] < config['minimum_result_unix']:
                        raise ValueError('new_session_future_result_only')
                    published = relay.publish(life, output, document, reference)
                    processed[path] = identity
                    for publication in published:
                        proof = dict(unix=time.time(), result_sha256=reference['sha256'],
                            origin=publication['origin'], chunk=publication['chunk'],
                            inbox_id=publication['publication']['id'], scoring_calls=0,
                            raw_result_unchanged=True, parent_publication=False,
                            rendering='pending_actual_REQUEST_verification')
                        relay.write_once(receipt_root / ('DELIVERED_'+proof['inbox_id']+'.json'), proof)
                except Exception as error:
                    relay.write_once(receipt_root / ('ERROR_'+str(time.time_ns())+'.json'), dict(
                        unix=time.time(), error_type=type(error).__name__, result_file_sha256=hashlib.sha256(path.read_bytes()).hexdigest()))
            time.sleep(2)
        relay.write_once(receipt_root / 'FINISHED.json', dict(unix=time.time(), processed_results=len(processed),
            deadline_unix=config['deadline_unix'], historical_rescoring=False, learner_signals=[]))


if __name__ == '__main__':
    main()
