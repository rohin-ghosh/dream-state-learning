import hashlib
import json
import os
from pathlib import Path
import sys
import time

BASE = Path('/localhome/local-rohing')
SOURCE = BASE / 'orch_r166_retelling_operator_20260917_activation5/source'
os.environ['CUDA_VISIBLE_DEVICES'] = ''
os.environ['PYTHONDONTWRITEBYTECODE'] = '1'
sys.path.insert(0, str(SOURCE))
from gpu import orch_r157_community_wall_extension as saved

PINS = {'C1': '11c3c6cd6be1b0cd008f2e2c445e871541be74d2976c25659ba452516abbe604',
        'C4': '87e5ca710f611281e5f84ce359ad4a93180155bfc05bdd7f60583cb2b4f2c2fb'}
remaining = 64 * 1024 * 1024
output_remaining = 4 * 1024 * 1024
cache = {}
started = time.time()
deadline = time.monotonic() + 1200
states = {}


def data(path):
    global remaining
    path = saved.regular(path)
    key = str(path)
    if key not in cache:
        size = path.stat().st_size
        assert size <= min(remaining, 16 * 1024 * 1024), 'finite_read_budget'
        content = path.read_bytes()
        remaining -= len(content)
        assert remaining >= 0, 'finite_read_budget'
        cache[key] = content
    return cache[key]


saved.read = lambda path: json.loads(data(path))
saved.sha = lambda path: hashlib.sha256(data(path)).hexdigest()


def emit(value):
    global output_remaining
    line = json.dumps(dict(value, observed_unix=time.time(), deadline_unix=started + 1200,
        remaining_read_bytes=remaining, no_signals=True, no_dispatch=True, no_GO=True), sort_keys=True)
    output_remaining -= len(line.encode()) + 1
    assert output_remaining >= 0, 'finite_output_budget'
    print(line, flush=True)


def current(path):
    paths = [item for item in path.glob('*.json') if len(item.stem) == 20 and item.stem.isdigit()]
    assert paths, 'existing_journal'
    return max(paths)


def owners(request):
    global remaining
    for expected in request['pair'].values():
        remaining -= 16384
        assert remaining >= 0, 'finite_identity_read_budget'
        saved.same(expected)
        fields = Path('/proc', str(expected['pid']), 'stat').read_text().rsplit(')', 1)[1].split()
        assert fields[0] not in ('T', 't', 'Z', 'X'), 'original_not_running_unpaused'


for agent, pin in PINS.items():
    root = BASE / ('orch_r166_retelling_' + agent + '_20260917_activation5')
    ready = saved.bound(dict(path=str(root / 'readiness/READY.json'), sha256=pin))
    request = saved.bound(ready['required_GO_binding']['request'])
    config = saved.bound(request['old_config'])
    plan = saved.bound(request['old_plan'])
    records = Path(plan['root']) / 'stream/records'
    latest = current(records)
    owners(request)
    states[agent] = dict(root=root, ready=ready, request=request, config=config, plan=plan,
        records=records, baseline=int(latest.stem), last_status=None, last_identity=time.monotonic(), done=False)
    emit(dict(agent=agent, status='PASSIVE_STARTED_FUTURE_ONLY', ready_sha256=pin,
        baseline_index=int(latest.stem), original_pair=request['pair'], poll_seconds=2,
        identity_interval_seconds=15, max_seconds=1200, read_cap_bytes=64 * 1024 * 1024,
        output_cap_bytes=4 * 1024 * 1024))

while time.monotonic() < deadline and not all(state['done'] for state in states.values()):
    for agent, state in states.items():
        if state['done']:
            continue
        try:
            if (state['root'] / 'ACTIVATE_ONCE').exists():
                emit(dict(agent=agent, status='EXTERNAL_ACTIVATION_OBSERVED_PASSIVE_WATCH_STOPPED'))
                state['done'] = True
                continue
            if time.monotonic() - state['last_identity'] >= 15:
                owners(state['request'])
                state['last_identity'] = time.monotonic()
            path = current(state['records'])
            record = saved.read(path)
            assert record['sha256'] == saved.digest({key: value for key, value in record.items() if key != 'sha256'})
            index = int(path.stem)
            status = 'WAIT_FUTURE_BOUNDARY'
            event = dict(agent=agent, index=index, kind=record['kind'])
            if index > state['baseline'] and record['kind'] == 'SLEEP_COMPLETE':
                boundary = saved.saved_boundary(state['plan']['root'])
                if boundary and boundary['reference']['path'] == str(path):
                    assert index >= state['ready']['required_GO_binding']['earliest_boundary_index']
                    metadata = saved.readout(state['plan']['root'], state['config'], state['plan'],
                        boundary, state['request']['pair']['actor'])
                    status = 'SAVED_BOUNDARY_WAIT_READOUT_REQUEST'
                    if metadata:
                        owners(state['request'])
                        if current(state['records']) == path:
                            status = 'WINDOW_OPEN_REQUEST_MAIN_GO_NO_AUTOMATIC_ACTION'
                            event.update(boundary=boundary['reference'], cycle=boundary['cycle'],
                                readout=metadata, ready_sha256=PINS[agent],
                                required_GO_binding=state['ready']['required_GO_binding'])
                        else:
                            status = 'WINDOW_CLOSED_NO_ACTION'
            marker = (index, status)
            if marker != state['last_status']:
                emit(dict(event, status=status))
                state['last_status'] = marker
        except Exception as error:
            emit(dict(agent=agent, status='PASSIVE_STOPPED_NO_ACTION', error_type=type(error).__name__, reason=str(error)))
            state['done'] = True
    time.sleep(min(2, max(0, deadline - time.monotonic())))
emit(dict(status='PASSIVE_FINISHED_NO_ACTION', reason='deadline_or_all_targets_stopped'))
