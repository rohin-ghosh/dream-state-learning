"""Bounded read-only fresh parent provider/delivery observer, excluding inherited turns."""

from collections import Counter
import hashlib
import json
import os
from pathlib import Path
import time

import refresh


STAGE = Path(__file__).resolve().parent
LIMIT = 64 * 1024 * 1024
used = 0
cache = {}


def read(path):
    global used
    path = Path(path)
    before = path.stat()
    key = (str(path), before.st_size, before.st_mtime_ns)
    if key not in cache:
        assert used + before.st_size <= LIMIT, 'observer_read_limit'
        raw = refresh.custody.read_file(path)
        used += len(raw)
        cache[key] = (json.loads(raw), dict(path=str(path), sha256=hashlib.sha256(raw).hexdigest()))
    return cache[key]


def observe(home):
    started, started_ref = read(home / 'STARTED.json')
    transfer, unused = read(home / 'LEDGER_TRANSFER.json')
    inherited = {entry['attempt'] for entry in transfer['attempts']}
    expected = started['successor']
    observed = refresh.custody.identity(expected['pid'])
    assert observed['start_ticks'] == expected['start_ticks'] and observed['argv'] == started['command']
    assert observed['state'] not in ('Z', 'X', 'T', 't')
    result = dict(branch=home.name, parent_pid=observed['pid'], start_ticks=observed['start_ticks'],
        parent_state=observed['state'], started=started_ref, reserved_response_count=started['reserved_response_count'],
        inherited_attempts=len(inherited), fresh_attempts=[])
    for attempt in sorted((home / 'parent').glob('parent_*')):
        if attempt.name in inherited:
            continue
        item = dict(attempt=attempt.name, provider_complete=False, published=False, rendered=False)
        source, source_ref = read(attempt / 'SOURCE.json')
        assert source['response_count'] > started['reserved_response_count'], 'old_request_replay_refused'
        item.update(source=source_ref, source_response_count=source['response_count'])
        if (attempt / 'DISPATCH.json').exists():
            dispatch, dispatch_ref = read(attempt / 'DISPATCH.json')
            item.update(dispatch=dispatch_ref, requested_model=dispatch['requested_model'],
                dispatch_utc=dispatch['utc'], retries=dispatch['retries'])
            assert dispatch['requested_model'] == refresh.MODEL and dispatch['attempts'] == 1 and dispatch['retries'] == 0
        if (attempt / 'stdout.json').exists():
            envelope, envelope_ref = read(attempt / 'stdout.json')
            item.update(provider_status=envelope.get('status'), actual_model=envelope.get('model'),
                provider_receipt=envelope_ref,
                provider_complete=envelope.get('status') == 'completed' and not envelope.get('error')
                    and envelope.get('model') == refresh.MODEL and bool(envelope.get('usage')))
        if (attempt / 'RESULT.json').exists():
            response, response_ref = read(attempt / 'RESULT.json')
            assert response['source_sha256'] == source_ref['sha256']
            item.update(status=response['status'], result=response_ref, error_type=response.get('error_type'),
                published=response['status'] == 'PUBLISHED')
            if response['status'] == 'PUBLISHED':
                item['publication'] = response['publication']
            if (attempt / 'DELIVERED.json').exists():
                delivery, delivery_ref = read(attempt / 'DELIVERED.json')
                assert delivery['status'] == 'RENDERED' and delivery['result_sha256'] == response_ref['sha256']
                assert delivery['publication'] == response['publication']
                assert delivery['rendered']['speaker'] == 'Astra'
                assert delivery['rendered']['inbox_sha256'] == response['publication']['sha256']
                assert delivery['rendered']['text_sha256'] == hashlib.sha256(response['message'].encode()).hexdigest()
                item.update(rendered=True, delivery=delivery_ref, request_exposure=delivery['rendered'])
        result['fresh_attempts'].append(item)
    return result


def main():
    started_unix = time.time()
    deadline = started_unix + 1200
    authority, unused = read(STAGE / 'AUTHORITY.json')
    homes = [STAGE / authority['epoch'] / branch for branch in refresh.BRANCHES]
    refresh.write(STAGE / 'OBSERVER_STARTED.json', dict(pid=os.getpid(), started_unix=started_unix,
        deadline_unix=deadline, read_limit_bytes=LIMIT, interval_seconds=15, source=refresh.reference(__file__),
        no_signals=True, no_provider_calls=True, no_remote_reads=True, no_retries=True))
    previous = None
    with (STAGE / 'OBSERVATIONS.jsonl').open('x') as output:
        while time.time() < deadline:
            rows = []
            for home in homes:
                try:
                    rows.append(observe(home))
                except Exception as error:
                    rows.append(dict(branch=home.name, observer_error=type(error).__name__, reason=str(error)[:160]))
            counts = Counter()
            for row in rows:
                counts['alive'] += 'parent_pid' in row
                for attempt in row.get('fresh_attempts', []):
                    counts['fresh_attempts'] += 1
                    for name in ('provider_complete', 'published', 'rendered'):
                        counts[name] += attempt[name]
            receipt = dict(observed_unix=time.time(), rows=rows, counts=dict(counts),
                deadline_unix=deadline, bytes_read=used, no_inherited_completion_counted=True)
            state = json.dumps(rows, sort_keys=True)
            if state != previous:
                output.write(json.dumps(receipt, sort_keys=True) + '\n')
                output.flush()
                os.fsync(output.fileno())
                refresh.write(STAGE / ('OBSERVATION_' + str(time.time_ns()) + '.json'), receipt)
                print(json.dumps(dict(observed_unix=receipt['observed_unix'], counts=dict(counts), bytes_read=used)), flush=True)
                previous = state
            if all(any(item['rendered'] for item in row.get('fresh_attempts', [])) for row in rows):
                break
            if any('observer_error' in row for row in rows):
                break
            time.sleep(min(15, max(0, deadline - time.time())))
    refresh.write(STAGE / 'OBSERVER_FINISHED.json', dict(finished_unix=time.time(), counts=dict(counts),
        deadline_unix=deadline, bytes_read=used, no_retry_or_extension=True))


if __name__ == '__main__':
    main()
