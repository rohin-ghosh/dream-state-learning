"""A4 broker custody transfer only after the morning same-life resumption."""

import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import time


EVENT = 'final_20260916T060000Z_r119_v1'
MORNING = 1789538400
END = 1789596240


def source():
    path = Path(__file__).with_name('orch_r119_grid_fast_parent.py')
    specification = importlib.util.spec_from_file_location('unchanged_fast_parent', path)
    previous = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(previous)
    text = previous.source()
    replacements = {
        "('independent_r119_v1',)": repr((EVENT,)),
        "('R119_GRID_INDEPENDENT_TERMINAL.json',)": repr((EVENT + '/LIFE_TERMINAL.json',)),
    }
    for before, after in replacements.items():
        if text.count(before) != 1:
            raise ValueError('exact_future_custody_delta')
        text = text.replace(before, after)
    return text


def ready_for_transfer(released, resumed, runner_lock, terminal, now):
    return MORNING <= now < END and released and resumed and not runner_lock and not terminal


def watch(path, expected):
    raw = Path(path).read_bytes()
    if hashlib.sha256(raw).hexdigest() != expected or os.environ.get('CUDA_VISIBLE_DEVICES') != '':
        raise ValueError('bound_CPU_broker_custody')
    plan = json.loads(raw)
    if plan['root'] != '/localhome/local-rohing/orch_r115_grid_pair_20260915/A4':
        raise ValueError('only_A4')
    for name, digest in plan['source_files'].items():
        if hashlib.sha256(Path(name).read_bytes()).hexdigest() != digest:
            raise ValueError('bound_broker_source')
    folder = Path(path).parent
    with (folder / 'WATCH_ARMED.json').open('x') as output:
        json.dump(dict(pid=os.getpid(), observed_unix=time.time(), provider_calls=0,
            trigger='RELEASED_AND_RESUMED_AND_OLD_RUNNER_LOCK_ABSENT',
            plan_sha256=expected), output, indent=2)
    while time.time() < MORNING:
        time.sleep(min(5, MORNING-time.time()))
    root = Path(plan['root'])
    event = root / EVENT
    script = ('test -f ' + str(event / 'RELEASED.json') + ' && test -f ' + str(event / 'RESUMED.json')
        + ' && test ! -e ' + str(root / 'parent_claude/RUNNER.lock')
        + ' && test ! -e ' + str(event / 'LIFE_TERMINAL.json'))
    while time.time() < END:
        response = subprocess.run(['bash', plan['wrapper'], script], stdout=subprocess.DEVNULL,
                                  stderr=subprocess.DEVNULL, timeout=30)
        if response.returncode == 0:
            with (folder / 'BROKER.log').open('x') as log:
                child = subprocess.Popen(plan['command'], env=dict(os.environ, CUDA_VISIBLE_DEVICES=''),
                    stdin=subprocess.DEVNULL, stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
            with (folder / 'BROKER_SPAWN.json').open('x') as output:
                json.dump(dict(pid=child.pid, observed_unix=time.time(), command=plan['command'],
                    no_old_claim_replay=True), output, indent=2)
            return
        time.sleep(5)
    with (folder / 'NOT_TRANSFERRED.json').open('x') as output:
        json.dump(dict(reason='NO_SAFE_HANDOFF_BEFORE_WALL', provider_calls=0), output)


if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == 'watch':
        parser = argparse.ArgumentParser()
        parser.add_argument('mode')
        parser.add_argument('--plan', required=True)
        parser.add_argument('--sha256', required=True)
        args = parser.parse_args()
        watch(args.plan, args.sha256)
    else:
        exec(compile(source(), __file__, 'exec'), {'__name__': '__main__', '__file__': __file__})
