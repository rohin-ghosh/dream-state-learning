"""Bounded read-only observer of NODE4 operator receipts and process identity."""

import argparse
import json
from pathlib import Path
import time


def read(path):
    if path.stat().st_size > 1024 * 1024:
        raise ValueError('bounded_operator_metadata_only')
    return json.loads(path.read_text())


def selected_lanes(bundle=None, lanes=None):
    if (bundle is None) == (lanes is None):
        raise ValueError('one_bundle_or_explicit_lanes')
    selected = [bundle / f'lane{physical}' for physical in (0, 1, 3, 4)] if bundle else lanes
    physicals = set()
    for lane in selected:
        if lane.name not in ('lane0', 'lane1', 'lane3', 'lane4') or lane.parent.parent != Path('/localhome/local-rohing') or not lane.parent.name.startswith('orch_r179_node4_'):
            raise ValueError('only_NODE4_operator_lanes')
        if lane.name in physicals:
            raise ValueError('no_duplicate_life_observation')
        physicals.add(lane.name)
    if not physicals:
        raise ValueError('explicit_lanes_required')
    return selected


def summary(bundle=None, lanes=None):
    rows = []
    for lane in selected_lanes(bundle, lanes):
        physical = int(lane.name[-1])
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
        entry['live_operator_identities'] = []
        for marker in sorted(lane.parent.glob(f'HANDOFF_{physical}*.pid')):
            try:
                operator_pid = int(marker.read_text().strip())
                process_root = Path('/proc', str(operator_pid))
                fields = (process_root / 'stat').read_text().rsplit(')', 1)[1].split()
                argv = [part.decode() for part in (process_root / 'cmdline').read_bytes().split(b'\0') if part]
                expected = [str(lane.parent / 'node4_rollout.py'), 'handoff', '--bundle', str(lane.parent), '--physical', str(physical)]
                if fields[0] not in ('Z', 'X') and argv[2:8] == expected and process_root.stat().st_uid == old['uid']:
                    entry['live_operator_identities'].append(dict(pid=operator_pid, start_ticks=fields[19], argv=argv,
                        uid=process_root.stat().st_uid, marker=str(marker)))
            except (FileNotFoundError, ProcessLookupError):
                pass
        try:
            fields = Path('/proc', str(old['pid']), 'stat').read_text().rsplit(')', 1)[1].split()
            entry.update(old_pid=old['pid'], original_identity_live=fields[19] == old['start_ticks']
                and fields[0] not in ('Z', 'X'), old_process_state=fields[0])
        except FileNotFoundError:
            entry.update(old_pid=old['pid'], original_identity_live=False)
        if not entry['live_operator_identities'] and entry['status'] == 'PREFLIGHT_PASSED_WAITING_SAVED_BOUNDARY':
            entry['status'] = ('WAIT_EXPIRED_NO_RETIREMENT' if any(lane.glob('WAIT_EXPIRED_*.json'))
                               else 'PREFLIGHT_PASSED_OPERATOR_NOT_LIVE')
        rows.append(entry)
    return rows


def observe(bundle, seconds, lanes=None, continuous=False):
    selected_lanes(bundle, lanes)
    if not 0 <= seconds <= 5400:
        raise ValueError('bounded_readonly_observation')
    deadline = time.monotonic() + seconds
    previous = None
    while True:
        rows = summary(bundle, lanes)
        if rows != previous or time.monotonic() >= deadline:
            print(json.dumps(dict(observed_unix=time.time(), rows=rows, journal_reads=0,
                journal_writes=0, signals_sent=0, model_calls=0), sort_keys=True), flush=True)
            previous = rows
        if time.monotonic() >= deadline or (not continuous and any(row['status'] in
                ('EXACT_SAVED_SUCCESSOR_LOADED', 'EXACT_SAVED_LOADED_AND_NEW_GENERATION', 'POST_RETIREMENT_ERROR') for row in rows)):
            return
        time.sleep(5)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    selection = parser.add_mutually_exclusive_group(required=True)
    selection.add_argument('--bundle', type=Path)
    selection.add_argument('--lane', type=Path, action='append')
    parser.add_argument('--seconds', type=int, default=120)
    parser.add_argument('--continuous', action='store_true')
    args = parser.parse_args()
    observe(args.bundle.resolve() if args.bundle else None, args.seconds,
        [lane.resolve() for lane in args.lane] if args.lane else None, args.continuous)
