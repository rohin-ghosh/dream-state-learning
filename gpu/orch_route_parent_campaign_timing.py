"""Timestamp-only route timing reduction; never transfer raw calls or tasks."""

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path


ROOTS = ['/tmp/orch_route_parent_campaign_20260915_attempt1', '/tmp/orch_route_parent_campaign_20260915_segment2']


def read(path):
    return json.loads(path.read_text())


def snapshot():
    observed = datetime.now(timezone.utc).timestamp()
    output = dict(observed_utc=datetime.fromtimestamp(observed, timezone.utc).isoformat(), stages=[], failures=[], parent_reservations=[])
    for name in ROOTS:
        root = Path(name)
        for arm in ('GUIDED', 'UNPARENTED', 'FROZEN'):
            for cycle in (1, 2):
                for phase in ('experience', 'sleep', 'readout'):
                    folder = root / arm / f'cycle{cycle}' / phase
                    request = folder / 'REQUEST.json'
                    if not request.exists():
                        continue
                    start = read(request)['started_unix']
                    complete, failed = folder / 'COMPLETE.json', folder / 'FAILED.json'
                    terminal = complete if complete.exists() else failed if failed.exists() else None
                    finish = read(terminal)['finished_unix'] if terminal else observed
                    output['stages'].append(dict(root=root.name, arm=arm, cycle=cycle, phase=phase,
                        status='COMPLETE' if complete.exists() else 'FAILED' if failed.exists() else 'RUNNING_CENSORED',
                        start_unix=start, finish_unix=finish, elapsed_seconds=finish-start,
                        request_file=str(request), terminal_file=str(terminal) if terminal else None,
                        request_sha256=hashlib.sha256(request.read_bytes()).hexdigest(),
                        terminal_sha256=hashlib.sha256(terminal.read_bytes()).hexdigest() if terminal else None))
            ledger = root / f'CALLS_PARENT_{arm}.jsonl'
            if ledger.exists():
                for line in ledger.read_text().splitlines():
                    row = json.loads(line)
                    output['parent_reservations'].append(dict(root=root.name, arm=arm, cycle=row['cycle'],
                        index=row['index'], reserved_unix=row['reserved_unix'], ledger_file=str(ledger)))
        for path in root.glob('**/FAILED.json'):
            if any(part.startswith('source') for part in path.relative_to(root).parts):
                continue
            row = read(path)
            output['failures'].append(dict(root=root.name, file=str(path), error=row.get('error'),
                finished_unix=row.get('finished_unix'), preserved_original='original' in str(path),
                sha256=hashlib.sha256(path.read_bytes()).hexdigest()))
    return output


def reduce(document, repository):
    parents = dict(orch_route_parent_campaign_20260915_attempt1=repository / 'research_notes/analysis/orch_route_parent_campaign_20260915_attempt1/parent',
        orch_route_parent_campaign_20260915_segment2=repository / 'research_notes/analysis/orch_route_parent_campaign_20260915_monitor_v2/continuation/segment2/parent')
    invocations = []
    for reservation in document['parent_reservations']:
        identity = f'{reservation["index"]:04d}_{reservation["arm"]}_C{reservation["cycle"]}'
        folder = parents[reservation['root']] / identity
        dispatch, receipt = folder / 'DISPATCH.json', folder / 'RECEIPT.json'
        if not dispatch.exists():
            continue
        start = read(dispatch)['started_unix']
        row = dict(reservation, id=identity, dispatch_file=str(dispatch),
            native_reservation_to_provider_start_seconds=start-reservation['reserved_unix'],
            includes='native transport + broker scheduling + pre-dispatch lock wait',
            exact_native_parent_wait='NOT_INSTRUMENTED; not estimated from file mtimes')
        if receipt.exists():
            row.update(provider_invocation_seconds=read(receipt)['finished_unix']-start,
                receipt_file=str(receipt), actual_model=read(receipt)['model'], status='VERIFIED_RESPONSE')
        else:
            row['status'] = 'NO_VERIFIED_RECEIPT'
            raw = folder / 'stdout.json'
            if raw.exists():
                try:
                    envelope = read(raw)
                    row['cli_reported_duration_ms'] = envelope.get('duration_ms')
                    row['cli_reported_api_duration_ms'] = envelope.get('duration_api_ms')
                except (ValueError, OSError):
                    pass
        invocations.append(row)
    document['parent_timing'] = invocations
    document['timing_scope'] = 'Request-to-completion phase wall includes model loading, generation, parent waits; gaps include admission/process queues/baseline/repair, not pure idle.'
    return document


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--snapshot', action='store_true')
    parser.add_argument('--input')
    parser.add_argument('--output')
    args = parser.parse_args()
    if args.snapshot:
        print(json.dumps(snapshot()))
    else:
        Path(args.output).write_text(json.dumps(reduce(read(Path(args.input)), Path.cwd()), indent=2) + '\n')
