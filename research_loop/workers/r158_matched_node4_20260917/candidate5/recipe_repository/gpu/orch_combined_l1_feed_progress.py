"""Read-only loss-log monitor: admission is not an actual presentation."""

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import time

from organism_v6.orch_combined_l1_continual import ContinualLayout, atomic_json


INGEST_SHA = '3d014fb3c0a88eb945b53c648d9060f7785f4ea02ab067fc2538e443d8242178'
FIRST_INDEX = 222 + 3260
LAST_INDEX = FIRST_INDEX + 375


def new_positions(record):
    return [index for index in record['rows'] if FIRST_INDEX <= index < LAST_INDEX]


def next_exposure(update, corpus_rows):
    layout = ContinualLayout(corpus_rows, 2)
    for future in range(update + 1, update + layout.trajectory_rows + 1):
        if new_positions(dict(rows=layout.training_indexes(future))):
            return future
    raise AssertionError('new375_not_in_current_corpus_cycle')


def capture(root):
    bound = root / 'INGEST_RECEIPTS/000002020.json'
    assert hashlib.sha256(bound.read_bytes()).hexdigest() == INGEST_SHA
    receipts = [json.loads(path.read_text()) for path in (root / 'INGEST_RECEIPTS').glob('*.json')]
    latest_corpus = max(receipts, key=lambda value: value['time_unix'])
    arms = {}
    for arm in ('FULL', 'OFF'):
        records = {}
        for path in (root / arm).glob('RANK0_LOSSES_*.jsonl'):
            for line in path.read_text().splitlines():
                try:
                    record = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if record['update'] <= 2020:
                    continue
                prior = records.get(record['update'])
                if prior is None or record['finished_unix'] > prior['finished_unix']:
                    records[record['update']] = dict(record,
                        line_sha256=hashlib.sha256(line.encode()).hexdigest(), native_log=str(path))
        ordered = [records[key] for key in sorted(records)]
        assert ordered
        last = ordered[-1]
        first = next((record for record in ordered if new_positions(record)), None)
        recent = ordered[-128:]
        interval = recent[-1]['update'] - recent[0]['update']
        rate = (recent[-1]['finished_unix'] - recent[0]['finished_unix']) / interval if interval else None
        future = next_exposure(last['update'], latest_corpus['rows'])
        counts = [0] * 375
        for record in ordered:
            for index in new_positions(record):
                counts[index - FIRST_INDEX] += 1
        eta = time.time() + (future - last['update']) * rate if rate is not None else None
        arms[arm] = dict(last_update=last['update'], last_update_unix=last['finished_unix'],
            first_actual=first, total_presentations=sum(counts), distinct_presented=sum(value > 0 for value in counts),
            minimum=min(counts), maximum=max(counts), observed_seconds_per_update=rate,
            next_presentation_update_if_corpus_unchanged=future,
            conditional_eta_utc=datetime.fromtimestamp(eta, timezone.utc).isoformat() if eta else None)
    return dict(captured_unix=time.time(),ingested375_at_update2020=True,
        current_corpus_rows=latest_corpus['rows'], arms=arms, native_model_calls=0,
        sampler_unchanged=True, uncertainty='ETA assumes current corpus size and recent wall-clock throughput; new admissions change modulo schedule, checkpoints/topology change speed.',
        extra_physical_recovery_updates=dict(FULL=0, OFF=117), recovery_count_through_update2020=True)


def main(root, once=False):
    output = root / 'FEED_PRESENTATION_PROGRESS'
    output.mkdir(exist_ok=True)
    deadline = json.loads((root / 'LIFETIME.json').read_text())['training_deadline_unix']
    while time.time() < deadline:
        value = capture(root)
        atomic_json(output / 'LATEST.json', value)
        for arm, progress in value['arms'].items():
            path = output / f'FIRST_NEW375_{arm}.json'
            if progress['first_actual'] is not None and not path.exists():
                with path.open('x') as stream:
                    json.dump(dict(arm=arm, first_actual=progress['first_actual'],
                        observed_unix=value['captured_unix'], source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()), stream, indent=2)
        print(json.dumps(value), flush=True)
        if once:
            return
        time.sleep(min(60, max(0, deadline-time.time())))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--once', action='store_true')
    args = parser.parse_args()
    main(args.root, args.once)
