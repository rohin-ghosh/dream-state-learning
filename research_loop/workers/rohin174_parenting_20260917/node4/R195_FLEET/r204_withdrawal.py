"""Use frozen R204 for the existing COMPLETE54-to57 same-life continuation."""

import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import time
import uuid

from math_c import HOME, PYTHON, host, read, require, sha, write
from apply_r204 import layer


def prepare(physical):
    host()
    require(physical in (2, 7), 'only_undispatched_withdrawn_R203_slots')
    root = HOME.parent / f'SCALE_physical{physical}'
    require((root / 'WITHDRAWAL_R204_TRANSITION.json').exists()
        and not (root / 'WITHDRAWN_DISPATCHED.json').exists(), 'old_watcher_stopped_before_continuation')
    target = root / 'reload_r204'
    target.mkdir()
    source, control = target / 'source', target / 'control'
    shutil.copytree(root / 'source', source)
    control.mkdir()
    plan = read(root / 'control/PLAN.json')
    old_source = Path(plan['source_root'])
    plan['source_root'] = str(source)
    if plan.get('startup_context'):
        plan['startup_context']['path'] = str(source / Path(plan['startup_context']['path']).relative_to(old_source))
    write(control / 'PLAN.json', plan)
    allocation = read(root / 'control/ALLOCATION.json')
    allocation.update(plan_sha256=sha(control / 'PLAN.json'), declared_unix=time.time())
    write(control / 'ALLOCATION.json', allocation)
    guard = read(root / 'control/GUARD.json')
    guard.update(plan_path=str(control / 'PLAN.json'), plan_sha256=sha(control / 'PLAN.json'),
        allocation_path=str(control / 'ALLOCATION.json'), allocation_sha256=sha(control / 'ALLOCATION.json'),
        attempt_dir=str(control))
    guard['device_containment']['unit'] = 'orch-r136-native-' + uuid.uuid4().hex
    write(control / 'GUARD.json', guard)
    bridge = read(root / 'BRIDGE.json')
    bridge.update(native_source=str(source), guard_path=str(control / 'GUARD.json'),
        guard_sha256=sha(control / 'GUARD.json'))
    write(target / 'BRIDGE.json', bridge)
    write(target / 'RECEIVING_READY.json', dict(status='CPU_TESTED_NOT_LIVE',
        guard_sha256=sha(control / 'GUARD.json'), same_life=True))
    layer(target, source, control)
    support = (root / 'arm_support.py').read_text().replace("SOURCE = HOME / 'source'",
        "SOURCE = HOME / 'reload_r204/source'")
    (root / 'withdraw_r204_support.py').write_text(support)
    worker = (root / 'withdraw_math_c.py').read_text().replace('from arm_support import',
        'from withdraw_r204_support import')
    for filename in ('PLAN.json', 'ALLOCATION.json', 'GUARD.json'):
        worker = worker.replace("HOME / 'control/" + filename + "'",
            "HOME / 'reload_r204/control/" + filename + "'")
    worker = worker.replace("HOME / 'BRIDGE.json'", "HOME / 'reload_r204/BRIDGE.json'")
    worker = worker.replace('WITHDRAWAL_WAITER.json', 'WITHDRAWAL_WAITER_R204.json')
    (root / 'withdraw_r204.py').write_text(worker)
    compile(worker, str(root / 'withdraw_r204.py'), 'exec')
    with (root / 'WITHDRAWAL_R204.log').open('x') as log:
        process = subprocess.Popen([str(PYTHON), '-B', str(root / 'withdraw_r204.py')],
            env=dict(os.environ, CUDA_VISIBLE_DEVICES='', PYTHONDONTWRITEBYTECODE='1'),
            stdin=subprocess.DEVNULL, stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
    receipt = dict(physical=physical, pid=process.pid, started_unix=time.time(),
        transition='natural_COMPLETE54_then_R204_same_life_55_to57',
        root=str(root / 'life'), no_native_signal=True, no_parent_queue_replay=True)
    write(root / 'R204_CONTINUATION_ARMED.json', receipt)
    print(json.dumps(receipt))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--physical', type=int, required=True)
    prepare(parser.parse_args().physical)
