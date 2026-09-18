"""Bounded local-only reporting of the new node3 parenting segment."""

import argparse
from datetime import datetime
import fcntl
import hashlib
import json
import os
from pathlib import Path
import time
from zoneinfo import ZoneInfo

from observe_parents import HERE, observe


def render(current, previous=None):
    previous_rows = {} if previous is None else {row['physical']: row for row in previous['rows']}
    stamp = datetime.fromtimestamp(current['observed_unix'], ZoneInfo('America/Los_Angeles'))
    lines = [f'\n## [Builder — node3 R179 parent segment monitor] {stamp:%Y-%m-%d %H:%M:%S %Z}',
        '', 'Counts are **new R179-segment turns only**, not lifetime totals. Earlier attempts remain preserved.',
        'Registered means a verified INBOX receipt; it is not independently verified rendered REQUEST exposure.',
        '', '| GPU | Parent alive | Published | Registered | Newly registered since prior report | Missing calls |',
        '| --- | --- | --- | --- | --- | --- |']
    for row in current['rows']:
        before = previous_rows.get(row['physical'], {}).get('registered_deliveries', 0)
        registered = row['registered_deliveries']
        if registered < before:
            raise ValueError('registered_count_regressed_no_report')
        lines.append(f"| {row['physical']} | {row.get('alive', False)} | {row['statuses'].get('PUBLISHED', 0)} | "
                     f"{registered} | {registered-before} | {row['statuses'].get('MISSING', 0)} |")
    lines.extend(['', 'No child signals, parent calls, inbox writes, provider outputs or sealed files are part of this monitor.', ''])
    return '\n'.join(lines)


def write(path, value):
    with path.open('x') as stream:
        json.dump(value, stream, indent=2, sort_keys=True)
        stream.flush()
        os.fsync(stream.fileno())


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--deadline', required=True, type=int)
    args = parser.parse_args()
    if not time.time() < args.deadline <= 1789689000:
        raise ValueError('within_existing_node3_internal_wall')
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    coordinate = HERE.parents[2] / 'COORDINATION.md'
    with (HERE / 'PARENT_REPORTER.lock').open('a+b') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        write(output / 'STARTED.json', dict(pid=os.getpid(), started_unix=time.time(),
            deadline_unix=args.deadline, local_only=True, signals=False, provider_calls=False,
            source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()))
        previous = None
        while time.time() < args.deadline:
            current = observe(HERE)
            path = output / f'OBSERVATION_{time.time_ns()}.json'
            write(path, current)
            message = render(current, previous)
            message += f'Operational receipt: `{path.relative_to(HERE.parents[3])}`.\n'
            descriptor = os.open(coordinate, os.O_WRONLY | os.O_APPEND)
            try:
                fcntl.flock(descriptor, fcntl.LOCK_EX)
                payload = message.encode()
                if os.write(descriptor, payload) != len(payload):
                    raise OSError('coordination_append_incomplete_no_retry')
                os.fsync(descriptor)
            finally:
                os.close(descriptor)
            previous = current
            due = min((int(time.time()) // 3600 + 1) * 3600, args.deadline)
            time.sleep(max(0, due-time.time()))
        write(output / 'COMPLETE.json', dict(status='REPORTING_WALL_REACHED', finished_unix=time.time()))


if __name__ == '__main__':
    main()
