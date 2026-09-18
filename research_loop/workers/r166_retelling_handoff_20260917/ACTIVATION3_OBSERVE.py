import hashlib
import json
from pathlib import Path
import sys
import time

remaining_bytes = 64 * 1024 * 1024


def read(path):
    global remaining_bytes
    size = path.stat().st_size
    if size > min(remaining_bytes, 16 * 1024 * 1024):
        raise RuntimeError('bounded_observer_read_limit')
    data = path.read_bytes()
    remaining_bytes -= len(data)
    return dict(path=str(path), sha256=hashlib.sha256(data).hexdigest(), content=json.loads(data))


def identity(pid):
    proc = Path('/proc') / str(pid)
    try:
        fields = (proc / 'stat').read_text().rsplit(')', 1)[1].split()
        return dict(pid=pid, state=fields[0], start_ticks=fields[19],
            argv=(proc / 'cmdline').read_bytes().rstrip(b'\0').decode().split('\0'),
            cwd=str((proc / 'cwd').resolve()), parent=int(fields[1]))
    except FileNotFoundError:
        return None


duration = int(sys.argv[1])
if not 0 <= duration <= 180:
    raise ValueError('bounded_snapshot_window')
deadline = time.monotonic() + duration
cache = {}
cursors = {}
events = {}
while True:
    complete = []
    for agent in ('C1', 'C2', 'C4', 'C5'):
        root = Path('/localhome/local-rohing/orch_r166_retelling_' + agent + '_20260917_activation3')
        result = dict(agent=agent, observed_unix=time.time(), files={})
        for name in ('MAIN_DISPATCH.json', 'ACTUAL_BOUNDARY_READY.json', 'TERMINATION_INTENT.json',
                     'OWNER_RETIRED.json', 'ACTIVATION_FAILED.json', 'control/PREPARED.json',
                     'control/SAVED_PROOF.json', 'control/EFFECTIVE_POLICY.json', 'attempt/ADMISSION_TIME.json',
                     'attempt/FAILED.json', 'attempt/LAUNCH.json', 'attempt/CONTAINMENT_VERIFIED.json',
                     'attempt/NATIVE_EXIT.json', 'attempt/SERVICE_EXIT.json'):
            path = root / name
            if path.exists():
                if str(path) not in cache:
                    cache[str(path)] = read(path)
                result['files'][name] = cache[str(path)]
        dispatch = result['files']['MAIN_DISPATCH.json']['content']
        result['operator'] = identity(dispatch['pid'])
        request_path = root / 'REQUEST.json'
        if str(request_path) not in cache:
            cache[str(request_path)] = read(request_path)
        request = cache[str(request_path)]['content']
        result['originals'] = {role: identity(item['pid']) for role, item in request['pair'].items()}
        result['events'] = events.setdefault(agent, [])
        actual = result['files'].get('ACTUAL_BOUNDARY_READY.json')
        if actual:
            boundary = Path(actual['content']['boundary']['path'])
            cursor = cursors.setdefault(agent, int(boundary.stem) + 1)
            for index in range(cursor, cursor + 32):
                path = boundary.parent / ('%020d.json' % index)
                if not path.exists():
                    break
                record = read(path)
                document = record['content']
                calculated = hashlib.sha256(json.dumps({key: value for key, value in document.items()
                    if key != 'sha256'}, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()).hexdigest()
                if document['sha256'] != calculated:
                    raise RuntimeError('record_hash_mismatch')
                if document['kind'] in ('LOADED', 'PRESLEEP_RETELLING_INVITATION'):
                    events[agent].append(record)
                cursors[agent] = index + 1
                if len(events[agent]) >= 2:
                    break
            result['events'] = events[agent]
            for record in events[agent]:
                if record['content']['kind'] == 'LOADED':
                    result['native'] = identity(record['content']['document']['pid'])
        failed = 'ACTIVATION_FAILED.json' in result['files'] or 'attempt/FAILED.json' in result['files']
        complete.append(failed or len(events[agent]) >= 2)
        if failed or result['operator'] is None:
            path = root / 'MAIN_EXECUTE.log'
            with path.open('rb') as stream:
                stream.seek(max(0, path.stat().st_size - 16384))
                result['operator_log_tail'] = stream.read(16384).decode(errors='replace')
        result['remaining_read_bytes'] = remaining_bytes
        print(json.dumps(result), flush=True)
    if all(complete) or time.monotonic() >= deadline:
        break
    time.sleep(min(15, max(0, deadline - time.monotonic())))
