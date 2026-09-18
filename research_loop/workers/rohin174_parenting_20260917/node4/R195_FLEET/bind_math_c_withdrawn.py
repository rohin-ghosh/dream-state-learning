"""Bind the existing R204 receiver to MATH-C's actual withdrawn incarnation."""

import json
import os
from pathlib import Path
import subprocess
import time

from math_c import HOME, PYTHON, host, read, require, sha, write
from reload_math_c import exact_stop


def main():
    host()
    require(read(HOME / 'PARENT_WITHDRAWAL_RECONCILED.json')['no_pending_parent_replay'], 'parent_withdrawal_complete')
    require(not (HOME / 'reload_r204/control/DISPATCH_ONCE').exists(), 'R204_not_dispatched')
    original_guard = HOME / 'withdrawn/control/GUARD.json'
    original_plan = read(HOME / 'withdrawn/control/PLAN.json')
    records = [read(path) for path in sorted((HOME / 'life/stream/records').glob('[0-9]' * 20 + '.json'))]
    loaded = next(record['document'] for record in reversed(records) if record['kind'] == 'LOADED')
    process = Path('/proc', str(loaded['pid']))
    require(process.exists() and os.readlink(process / 'cwd') == original_plan['source_root'], 'actual_withdrawn_native_alive')
    arguments = (process / 'cmdline').read_bytes().rstrip(b'\0').decode().split('\0')
    require(arguments[-3:] == ['native', '--config', str(original_guard)], 'actual_withdrawn_guard_identity')
    ticks = (process / 'stat').read_text().rsplit(')', 1)[1].split()[19]
    target, control = HOME / 'reload_r204', HOME / 'reload_r204/control'
    plan, allocation, guard = read(control / 'PLAN.json'), read(control / 'ALLOCATION.json'), read(control / 'GUARD.json')
    require(original_plan['max_sleeps'] == 57 and plan['root'] == original_plan['root'], 'same_life_withdrawn_limit')
    plan['max_sleeps'] = 57
    stamp = str(time.time_ns())
    for name in ('PLAN', 'ALLOCATION', 'GUARD'):
        (control / (name + '.json')).rename(control / (name + '_GUIDED_' + stamp + '.json'))
    write(control / 'PLAN.json', plan)
    allocation['plan_sha256'] = sha(control / 'PLAN.json')
    write(control / 'ALLOCATION.json', allocation)
    guard.update(plan_sha256=sha(control / 'PLAN.json'), allocation_sha256=sha(control / 'ALLOCATION.json'))
    write(control / 'GUARD.json', guard)
    bridge, ready = read(target / 'BRIDGE.json'), read(target / 'RECEIVING_READY.json')
    for name in ('BRIDGE', 'RECEIVING_READY'):
        (target / (name + '.json')).rename(target / (name + '_GUIDED_' + stamp + '.json'))
    bridge['guard_sha256'] = ready['guard_sha256'] = sha(control / 'GUARD.json')
    write(target / 'BRIDGE.json', bridge)
    write(target / 'RECEIVING_READY.json', ready)
    subprocess.run([str(PYTHON), '-B', '-c', 'from gpu.orch_r125_continual_guard import validate; import sys; validate(sys.argv[1])',
        str(control / 'GUARD.json')], cwd=target / 'source', env=dict(os.environ, CUDA_VISIBLE_DEVICES='',
        PYTHONPATH=str(target / 'source'), PYTHONDONTWRITEBYTECODE='1'), check=True, timeout=45)
    for name in ('RELOAD6_CENSUS.json', 'RELOAD_SELECTION.json'):
        if (HOME / name).exists():
            (HOME / name).rename(HOME / (name + '.prior_' + stamp))
    write(HOME / 'RELOAD6_CENSUS.json', dict(learners=[dict(plan=original_plan,
        guard_path=str(original_guard), guard_sha256=sha(original_guard), backing_root=str(HOME / 'life'),
        native=dict(pid=loaded['pid'], start_ticks=ticks))]))
    write(HOME / 'PARENT_QUIESCED_R204.json', dict(no_future_old_parent_writes=True,
        basis='actual_PARENT_WITHDRAWAL_CLOSED_and_RECONCILED_at54', observed_unix=time.time()))
    waiter = read(HOME / 'WITHDRAWAL_WAITER.json')
    exact_stop(waiter['pid'], ['withdraw_math_c.py'])
    import r203_retire
    r203_retire.prepare_binding(6, capture=True)
    with (HOME / 'RELOAD_R204.log').open('x') as log:
        operator = subprocess.Popen([str(PYTHON), '-B', str(HOME / 'r203_retire.py'), 'retire_launch', '--physical', '6'],
            env=dict(os.environ, CUDA_VISIBLE_DEVICES='', PYTHONDONTWRITEBYTECODE='1'), stdin=subprocess.DEVNULL,
            stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
    write(HOME / 'R204_RELOAD_ARMED.json', dict(pid=operator.pid, native_pid=loaded['pid'],
        native_start_ticks=ticks, armed_unix=time.time(), fresh_COMPLETE_required=True, max_sleeps=57))
    print(json.dumps(read(HOME / 'R204_RELOAD_ARMED.json')))


if __name__ == '__main__':
    main()
