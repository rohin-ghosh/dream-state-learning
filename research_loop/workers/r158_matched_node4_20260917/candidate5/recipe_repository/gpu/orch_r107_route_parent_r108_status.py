"""Allowlisted node-side reductions; never emit prompts, outputs or raw API text."""

import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import time


def read(path):
    return json.loads(path.read_text())


def reference(path):
    return dict(path=str(path), sha256=hashlib.sha256(path.read_bytes()).hexdigest())


def utc(value):
    return datetime.fromtimestamp(value, timezone.utc).isoformat()


def capture(path, row):
    response = row['response']
    return dict(reference(path), purpose=row['purpose'], finished_utc=utc(row['finished_unix']),
                content_tokens=len(response['token_ids']) - int(response['terminal']),
                terminal=response['terminal'], input_truncated=response['input_truncated'],
                full_prompt_prefix_verified=response['full_prompt_prefix_verified'],
                helper_sha256=response.get('reflection_stop_source_sha256'))


def collect(root, indices):
    observed = time.time()
    result = dict(observed_utc=utc(observed), root=str(root), raw_embedded=False,
                  functional_change='UNKNOWN_PENDING_AUTHOR_AUDIT', lanes=[])
    for index in indices:
        lane = root / f'campaign_route_parent_{index}'
        calls = [(path, read(path)) for path in sorted((lane / 'native').glob('CALL_*.json'))]
        completed = [(path, row) for path, row in calls if 'response' in row and 'finished_unix' in row]
        parents = []
        for path in sorted(lane.glob('PARENT_C*_P*.json')):
            parent = read(path)
            archive = Path(parent['archive']['remote_root'])
            provider = read(archive / 'COMPLETE.json')
            assert parent['archive']['all_verified'] and provider['status'] == 'COMPLETE'
            parents.append(dict(reference(path), delivered_utc=utc(parent['observed_unix']),
                provider_finished_utc=utc(provider['finished_unix']),
                actual_primary_model=provider['actual_primary_model'],
                plan_sha256=provider['plan_sha256'], raw_response_sha256=provider['raw_response_sha256'],
                archive_hashes_verified=True, held_exposed=parent['held_exposed']))
        launch = read(lane / 'LAUNCH.json') if (lane / 'LAUNCH.json').exists() else None
        reflections = [(path, row) for path, row in completed if row['purpose'] == 'reflection']
        terminal_name = 'RECOVERY_TERMINAL.json' if (lane / 'RECOVERY_PUBLICATION.json').exists() else 'TERMINAL.json'
        terminal = read(lane / terminal_name) if (lane / terminal_name).exists() else None
        window = [(path, row) for path, row in completed if observed - 600 <= row['finished_unix'] <= observed]
        started = min((row['started_unix'] for _, row in completed), default=observed)
        duration = max(0, min(600, observed - started))
        summary = dict(index=index, launch=launch, launch_utc=utc(launch['started_unix']) if launch else None,
            completed_native_calls=len(completed), recorded_call_intents=len(calls),
            completed_by_purpose=dict(Counter(row['purpose'] for _, row in completed)),
            completed_content_tokens=sum(len(row['response']['token_ids']) - int(row['response']['terminal']) for _, row in completed),
            native_failure=(lane / 'FAILED.json').exists(), terminal=terminal,
            actual_parent_responses=len(parents), parents=parents,
            first_native=capture(*completed[0]) if completed else None,
            first_parent_conditioned_reflection=capture(*reflections[0]) if reflections else None,
            all_completed_full_prompt_verified=all(row['response']['full_prompt_prefix_verified']
                and row['response']['input_truncated'] is False for _, row in completed),
            raw_throughput_window=dict(observed_seconds=duration, full_600s=duration == 600,
                completed_native_calls=len(window), normalized_calls_per_hour=3600 * len(window) / duration if duration else None,
                qualified_functional_count=None, qualified_rate=None))
        if (lane / 'ACTOR_READY.json').exists():
            summary['actor_ready'] = read(lane / 'ACTOR_READY.json')
        scans = sorted(lane.glob('ADMISSION_*.json'))
        clear = [(path, read(path)) for path in scans if read(path)['clear']]
        if clear:
            path, admission = clear[-1]
            summary['strict_admission'] = dict(reference(path), clear=True,
                scanner_euid=admission['scanner_euid'], blocking_reasons=admission['blocking_reasons'])
        result['lanes'].append(summary)
    ledger = root / 'RESERVATIONS.jsonl'
    rows = [json.loads(line) for line in ledger.read_text().splitlines()] if ledger.exists() else []
    result['reservations_by_kind'] = dict(Counter(row['kind'] for row in rows))
    result['reservations_by_slot'] = {str(index):dict(Counter(row['kind'] for row in rows if row['index'] == index)) for index in indices}
    result['ledger'] = reference(ledger) if ledger.exists() else None
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--indices', nargs='+', type=int, required=True)
    args = parser.parse_args()
    print(json.dumps(collect(args.root, args.indices), sort_keys=True))
