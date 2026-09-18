"""Bounded read-only observer of NODE4 operator receipts and process identity."""

import argparse
import json
from pathlib import Path
import time


def read(path):
    if path.stat().st_size > 1024 * 1024:
        raise ValueError('bounded_operator_metadata_only')
    return json.loads(path.read_text())


def summary(bundle):
    rows = []
    for physical in (0, 1, 3, 4):
        lane = bundle / f'lane{physical}'
        request = read(lane / 'STAGED.json')
        entry = dict(physical=physical, stage=str(lane), status='STAGED')
        if any(lane.glob('PREFLIGHT_ACCEPTED_*.json')):
            entry['status'] = 'PREFLIGHT_PASSED_WAITING_SAVED_BOUNDARY'
        errors = sorted(lane.glob('ERROR_*.json'))
        accepted = sorted(lane.glob('PREFLIGHT_ACCEPTED_*.json'))
        if errors and (not accepted or errors[-1].stat().st_mtime_ns > accepted[-1].stat().st_mtime_ns):
            entry.update(status='OPERATOR_ERROR', error=read(errors[-1]))
        for name, status in (('BOUNDARY.json', 'EXACT_BOUNDARY_VERIFIED'),
                             ('RETIREMENT_STARTED.json', 'RETIREMENT_STARTED'),
                             ('RETIRED.json', 'EXACT_OLD_OWNERS_RETIRED'),
                             ('DISPATCHED.json', 'SUCCESSOR_GUARDED_DISPATCHED'),
                             ('LOADED_RECEIPT.json', 'EXACT_SAVED_SUCCESSOR_LOADED'),
                             ('HANDOFF_COMPLETE.json', 'EXACT_SAVED_LOADED_AND_NEW_GENERATION')):
            if (lane / name).exists():
                receipt = read(lane / name)
                entry.update(status=status, receipt=str(lane / name))
                if name == 'LOADED_RECEIPT.json':
                    entry.update(successor_pid=receipt['actor']['pid'], saved_cycle=receipt['saved']['cycle'],
                        optimizer_steps=receipt['saved']['optimizer_steps'])
        if (lane / 'RETIREMENT_STARTED.json').exists() and errors:
            if errors[-1].stat().st_mtime_ns > (lane / 'RETIREMENT_STARTED.json').stat().st_mtime_ns:
                entry.update(status='POST_RETIREMENT_ERROR', error=read(errors[-1]))
        old = request['processes']['actor']
        try:
            fields = Path('/proc', str(old['pid']), 'stat').read_text().rsplit(')', 1)[1].split()
            entry.update(old_pid=old['pid'], original_identity_live=fields[19] == old['start_ticks']
                and fields[0] not in ('Z', 'X'), old_process_state=fields[0])
        except FileNotFoundError:
            entry.update(old_pid=old['pid'], original_identity_live=False)
        rows.append(entry)
    return rows


def observe(bundle, seconds):
    if bundle.parent != Path('/localhome/local-rohing') or not bundle.name.startswith('orch_r179_node4_'):
        raise ValueError('only_NODE4_operator_bundle')
    if not 0 <= seconds <= 600:
        raise ValueError('bounded_readonly_observation')
    deadline = time.monotonic() + seconds
    previous = None
    while True:
        rows = summary(bundle)
        if rows != previous or time.monotonic() >= deadline:
            print(json.dumps(dict(observed_unix=time.time(), rows=rows, journal_reads=0,
                journal_writes=0, signals_sent=0, model_calls=0), sort_keys=True), flush=True)
            previous = rows
        if time.monotonic() >= deadline or any(row['status'] in
                ('EXACT_SAVED_SUCCESSOR_LOADED', 'EXACT_SAVED_LOADED_AND_NEW_GENERATION', 'POST_RETIREMENT_ERROR') for row in rows):
            return
        time.sleep(5)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--bundle', type=Path, required=True)
    parser.add_argument('--seconds', type=int, default=120)
    args = parser.parse_args()
    observe(args.bundle.resolve(), args.seconds)
