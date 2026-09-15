"""Read-only completed-capture rates and exact native slot identities."""

import argparse
from collections import Counter
from datetime import datetime, timezone
import json
from pathlib import Path
import subprocess
import time


def read(path):
    return json.loads(Path(path).read_bytes())


def identity_alive(expected):
    directory = Path('/proc') / str(expected['pid'])
    try:
        fields = (directory / 'stat').read_text().rsplit(')', 1)[1].split()
        actual = dict(pid=int(directory.name), uid=directory.stat().st_uid, start_ticks=fields[19],
                      boot_id=Path('/proc/sys/kernel/random/boot_id').read_text().strip())
        return actual == expected and fields[0] != 'Z'
    except FileNotFoundError:
        return False


def lane(root, shard, now, window=600):
    output = root / f'shard{shard}'
    rows = []
    for path in output.glob('*.json'):
        row = read(path)
        if 'task_id' in row and 'finished_unix' in row and ('response' in row or 'error' in row):
            rows.append(row)
    recent = [row for row in rows if now - window <= row['finished_unix'] <= now]
    launch = root / f'LAUNCH_{shard}.json'
    process = read(launch)['identity'] if launch.exists() else None
    first_by_family = {}
    for row in sorted(rows, key=lambda row: row['finished_unix']):
        family = row.get('family', 'math')
        if family not in first_by_family:
            first_by_family[family] = {name: row.get(name) for name in
                ('task_id', 'source_task_id', 'stage', 'finished_unix', 'outcome', 'error')}
    evidence = [read(path) for path in (output / 'evidence').glob('B*-P*.json')]
    route = [row['evidence'] for row in evidence if row.get('task', {}).get('family') == 'route' and 'evidence' in row]
    return dict(root=str(root), shard=shard, identity=process, identity_alive=identity_alive(process) if process else False,
                completed_captures=len(rows), categories=dict(Counter(row.get('outcome', {}).get('category', 'execution_error') for row in rows)),
                stages=dict(Counter(row['stage'] for row in rows)), families=dict(Counter(row.get('family', 'math') for row in rows)),
                recent_window_seconds=window, recent_completed=len(recent), recent_captures_per_hour=len(recent) * 3600 / window,
                recent_content_tokens=sum(row.get('outcome', {}).get('content_tokens', 0) for row in recent),
                raw_above400=sum(row.get('outcome', {}).get('content_tokens', 0) > 400 for row in rows),
                latest_finish=max((row['finished_unix'] for row in rows), default=None), first_by_family=first_by_family,
                route_worlds_completed=len(route), route_goals_correct=sum(row['complete_routes'] for row in route),
                route_goals_denominator=sum(row['route_denominator'] for row in route),
                terminal=read(output / 'TERMINAL.json') if (output / 'TERMINAL.json').exists() else None,
                failed=read(output / 'FAILED.json') if (output / 'FAILED.json').exists() else None)


def observe(original, successor):
    now = time.time()
    roots = {name: {str(shard): lane(root, shard, now) for shard in range(8)}
             for name, root in (('original', original), ('successor', successor))}
    slots = {}
    for shard in range(8):
        live = [(name, roots[name][str(shard)]) for name in roots if roots[name][str(shard)]['identity_alive']]
        slots[str(shard)] = dict(status='OWNERSHIP_OVERLAP' if len(live) > 1 else 'ACTIVE' if live else 'NO_OWN_LIVE_PROCESS',
                                processes=[dict(generation=name, identity=row['identity'], families=row['families']) for name, row in live])
    return dict(observed_unix=now, observed_utc=datetime.fromtimestamp(now, timezone.utc).isoformat(), roots=roots, slots=slots,
                queue=read(successor / 'WATCH_STATUS.json') if (successor / 'WATCH_STATUS.json').exists() else None,
                successor_guard_failure=read(successor / 'GUARD_FAILED.json') if (successor / 'GUARD_FAILED.json').exists() else None,
                reservations={name: len(list((root / 'reservations').glob('*.json'))) for name, root in (('original', original), ('successor', successor))},
                gpu_inventory=subprocess.check_output(['nvidia-smi', '--query-gpu=index,uuid,memory.used,utilization.gpu', '--format=csv,noheader'], text=True),
                count_contract='Completed native captures, including drafts/source actions, not unique tasks or qualified rows.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--original', type=Path, default=Path('/localhome/local-rohing/orch_rich_hot_node2_20260915_attempt1'))
    parser.add_argument('--successor', type=Path, default=Path('/localhome/local-rohing/orch_rich_hot_node2_floor98_20260915_attempt1'))
    options = parser.parse_args()
    print(json.dumps(observe(options.original, options.successor), indent=2))
