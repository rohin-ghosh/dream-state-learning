"""Read-only bounded throughput accounting; never launches or reviews actors."""

import argparse
import hashlib
import json
import math
from pathlib import Path
import re
import time


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def window_counts(rows, start, end):
    if end - start != 600:
        raise ValueError('exact_600_second_window_required')
    selected = [row for row in rows if start < row['finished_unix'] <= end]
    command_only = sum(bool(re.fullmatch(r'(READ EVENT|ROUTE) [^\s]+',
        row['response']['raw'].strip())) for row in selected)
    text_hashes = [hashlib.sha256(row['response']['raw'].encode()).hexdigest()
                   for row in selected]
    tokens = sum(row['generated_tokens'] for row in selected)
    return dict(completed_raw_rows=len(selected), raw_command_only_rows=command_only,
        prose_rows=len(selected) - command_only, completed_content_tokens=tokens,
        raw_rows_per_hour=len(selected) * 6, completion_attributed_tokens_per_second=tokens / 600,
        crossed_start_boundary_rows=sum(row['started_unix'] <= start for row in selected),
        exact_duplicate_raw_rows=len(text_hashes) - len(set(text_hashes)),
        semantic_qualified_rows=None, qualified_rows_per_hour=None)


def collect(root, end):
    start = end - 600
    ready = {index: json.loads((root / f'shard{index}/ACTOR_READY.json').read_text())
             for index in (4, 5)}
    if start < max(row['ready_unix'] for row in ready.values()):
        raise ValueError('full_600_seconds_after_both_actors_ready_required')
    slots = []
    for index in (4, 5):
        shard = root / f'shard{index}'
        paths = sorted(shard.glob('CALL_[0-9][0-9][0-9][0-9].json'))
        pairs = [(path, json.loads(path.read_text())) for path in paths]
        selected = [(path, row) for path, row in pairs if start < row['finished_unix'] <= end]
        failures = [json.loads(path.read_text()) for path in shard.glob('CALL_*_FAILED.json')]
        launch = json.loads((root / f'LAUNCH_{index}.json').read_text())
        process = Path('/proc') / str(launch['pid'])
        identity_matches = False
        try:
            identity_matches = (process.stat().st_uid == launch['identity']['uid'] and
                (process / 'stat').read_text().rsplit(')', 1)[1].split()[19] ==
                launch['identity']['start_ticks'] and
                Path('/proc/sys/kernel/random/boot_id').read_text().strip() ==
                launch['identity']['boot_id'])
        except FileNotFoundError:
            pass
        slot = dict(index=index, pid=launch['pid'], uuid=launch['uuid'],
            identity_matches=identity_matches,
            window_failed_calls=sum(start < row['finished_unix'] <= end for row in failures),
            window_captures=[dict(path=str(path), sha256=digest(path)) for path, row in selected],
            total_completed_at_end=sum(row['finished_unix'] <= end for path, row in pairs),
            actor_terminal=(shard / 'RESULT.json').exists(),
            actor_failed=(shard / 'FAILED.json').exists(),
            **window_counts([row for path, row in pairs], start, end))
        slots.append(slot)
    ledger = root / 'CALL_RESERVATIONS.jsonl'
    reservations = [json.loads(line) for line in ledger.read_text().splitlines() if line.strip()]
    return dict(window_start_unix=start, window_end_unix=end, duration_seconds=600,
        collected_unix=time.time(), boundary='START_EXCLUSIVE_END_INCLUSIVE',
        rate_method='ROWS_AND_FULL_OUTPUT_TOKENS_ATTRIBUTED_TO_COMPLETION_TIME',
        token_rate_not_instantaneous_emission_rate=True, raw_embedded=False,
        semantic_qualification_not_inferred=True, slots=slots,
        reserved_at_end=sum(row['started_unix'] <= end for row in reservations),
        reservations_at_read=len(reservations), ledger_sha256_at_read=digest(ledger),
        source_sha256=digest(Path(__file__)), no_new_refill=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--end', type=float)
    arguments = parser.parse_args()
    end = arguments.end if arguments.end is not None else math.floor(time.time()) - 2
    if end > time.time() - 2:
        raise ValueError('settled_window_end_required')
    print(json.dumps(collect(arguments.root, end), sort_keys=True))
