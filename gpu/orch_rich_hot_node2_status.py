"""Read-only completed-capture rates and exact native slot identities."""

import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import time


def read(path):
    return json.loads(Path(path).read_bytes())


def reference(path, payload):
    return dict(native_path=str(path), bytes=len(payload), sha256=hashlib.sha256(payload).hexdigest())


def receipt(path, fields=()):
    if not path.exists():
        return None
    payload = path.read_bytes()
    document = json.loads(payload)
    summary = {name: document[name] for name in fields if name in document and
               isinstance(document[name], (str, int, float, bool, type(None)))}
    return dict(reference(path, payload), summary=summary)


def queue_summary(path):
    if not path.exists():
        return None
    document = read(path)
    result = {name: [shard for shard in document.get(name, []) if type(shard) is int and shard in range(8)]
              for name in ('launched_shards', 'pending_shards') if name in document}
    if isinstance(document.get('observed_unix'), (int, float)):
        result['observed_unix'] = document['observed_unix']
    if isinstance(document.get('returncodes'), dict):
        result['returncodes'] = {str(shard): document['returncodes'][str(shard)] for shard in range(8)
                                if str(shard) in document['returncodes'] and
                                (document['returncodes'][str(shard)] is None or type(document['returncodes'][str(shard)]) is int)}
    return result


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
        payload = path.read_bytes()
        row = json.loads(payload)
        if 'task_id' in row and 'finished_unix' in row and ('response' in row or 'error' in row):
            outcome = row.get('outcome', {})
            response = row.get('response', {})
            rows.append(dict(task_id=row['task_id'], source_task_id=row.get('source_task_id'), stage=row['stage'],
                finished_unix=row['finished_unix'], family=row.get('family', 'math'),
                category=outcome.get('category', 'execution_error'), content_tokens=outcome.get('content_tokens', 0),
                correct=outcome.get('correct'), terminal=response.get('terminal'), truncated=response.get('truncated'),
                execution_error='error' in row, artifact=reference(path, payload)))
    recent = [row for row in rows if now - window <= row['finished_unix'] <= now]
    launch = root / f'LAUNCH_{shard}.json'
    process = read(launch)['identity'] if launch.exists() else None
    first_by_family = {}
    for row in sorted(rows, key=lambda row: row['finished_unix']):
        family = row.get('family', 'math')
        if family not in first_by_family:
            first_by_family[family] = {name: row.get(name) for name in
                ('task_id', 'source_task_id', 'stage', 'finished_unix', 'category', 'content_tokens', 'correct',
                 'terminal', 'truncated', 'execution_error', 'artifact')}
    route = []
    for path in (output / 'evidence').glob('B*-P*.json'):
        row = read(path)
        if row.get('task', {}).get('family') == 'route' and 'evidence' in row:
            route.append((row['evidence']['complete_routes'], row['evidence']['route_denominator']))
    return dict(root=str(root), shard=shard, identity=process, identity_alive=identity_alive(process) if process else False,
                completed_captures=len(rows), categories=dict(Counter(row['category'] for row in rows)),
                stages=dict(Counter(row['stage'] for row in rows)), families=dict(Counter(row.get('family', 'math') for row in rows)),
                recent_window_seconds=window, recent_completed=len(recent), recent_captures_per_hour=len(recent) * 3600 / window,
                recent_content_tokens=sum(row['content_tokens'] for row in recent),
                raw_above400=sum(row['content_tokens'] > 400 for row in rows),
                latest_finish=max((row['finished_unix'] for row in rows), default=None), first_by_family=first_by_family,
                route_worlds_completed=len(route), route_goals_correct=sum(row[0] for row in route),
                route_goals_denominator=sum(row[1] for row in route),
                terminal=receipt(output / 'TERMINAL.json', ('status', 'finished_unix', 'completed_calls', 'admitted_rows', 'fits', 'parent_calls')),
                failed=receipt(output / 'FAILED.json'))


def observe(original, successor, derived=None, control=None):
    now = time.time()
    generations = [('original', original), ('successor', successor)]
    if derived is not None:
        generations.append(('checkpoint_derived', derived))
    roots = {name: {str(shard): lane(root, shard, now) for shard in range(8)}
             for name, root in generations}
    slots = {}
    for shard in range(8):
        live = [(name, roots[name][str(shard)]) for name in roots if roots[name][str(shard)]['identity_alive']]
        slots[str(shard)] = dict(status='OWNERSHIP_OVERLAP' if len(live) > 1 else 'ACTIVE' if live else 'NO_OWN_LIVE_PROCESS',
                                processes=[dict(generation=name, identity=row['identity'], families=row['families']) for name, row in live])
    controller = control if control is not None else successor
    queue_path = controller / ('STATUS.json' if control is not None else 'WATCH_STATUS.json')
    failure_path = controller / ('FAILED.json' if control is not None else 'GUARD_FAILED.json')
    return dict(observed_unix=now, observed_utc=datetime.fromtimestamp(now, timezone.utc).isoformat(), roots=roots, slots=slots,
                controller_root=str(controller), queue=queue_summary(queue_path), queue_artifact=receipt(queue_path),
                successor_guard_failure=receipt(failure_path),
                controller_terminal=receipt(controller / 'TERMINAL.json', ('status', 'finished_unix')),
                reservations={name: len(list((root / 'reservations').glob('*.json'))) for name, root in generations},
                gpu_inventory=subprocess.check_output(['nvidia-smi', '--query-gpu=index,uuid,memory.used,utilization.gpu', '--format=csv,noheader'], text=True),
                count_contract='Completed native captures, including drafts/source actions, not unique tasks or qualified rows.',
                storage_contract='COMPACT_V2: no embedded raw targets, messages, tokens, verifier inputs or exception text; raw remains at native paths.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--original', type=Path, default=Path('/localhome/local-rohing/orch_rich_hot_node2_20260915_attempt1'))
    parser.add_argument('--successor', type=Path, default=Path('/localhome/local-rohing/orch_rich_hot_node2_floor98_20260915_attempt1'))
    parser.add_argument('--derived', type=Path)
    parser.add_argument('--control', type=Path)
    options = parser.parse_args()
    print(json.dumps(observe(options.original, options.successor, options.derived, options.control), indent=2))
