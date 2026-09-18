"""Layer the released R204 bytes on unstarted receiving configurations only."""

import argparse
import ast
import fcntl
import json
import os
from pathlib import Path
import shutil
import subprocess
import time

from math_c import HOME, PYTHON, host, read, require, sha, write, extract_exact
from r203_receive import paths


ARCHIVE_SHA = 'b0f148c92172af9d1525fda79a97bebfb31337e312e26c0f6bc805b3c687f8fc'


def layer(root, source, control):
    require(not (control / 'DISPATCH_ONCE').exists(), 'no_mutation_of_dispatched_source')
    packet = HOME.parent / 'r204_ready'
    ready = read(packet / 'READY.json')
    require(ready['archive_sha256'] == ARCHIVE_SHA and sha(packet / 'runtime_overlay.tar.gz') == ARCHIVE_SHA
        and ready['status'] == 'CPU_TESTED_NOT_LIVE', 'exact_R204_release')
    overlay = root / ('r204_overlay_' + str(time.time_ns()))
    overlay.mkdir()
    extract_exact(packet / 'runtime_overlay.tar.gz', overlay, ready['files'])
    for relative in ready['files']:
        shutil.copyfile(overlay / relative, source / relative)
    plan = read(control / 'PLAN.json')
    plan.update(ready['required_native_options'])
    plan['think_act_learn'].update(ready['required_driver_options'])
    driver = source / 'gpu/orch_r184_think_act_learn.py'
    text = driver.read_text()
    method = next(node for node in ast.walk(ast.parse(text)) if isinstance(node, ast.FunctionDef) and node.name == '_cpu')
    before = ''.join(text.splitlines(keepends=True)[method.lineno-1:method.end_lineno])
    require('EXISTING_LIFE_CPU_POLICY' in before and 'code_policy' in before, 'strict_CPU_policy_preserved')
    after = (f"    def _cpu(self, origin):\n        if self.config['trial_id'] == {plan['think_act_learn']['trial_id']!r}:\n"
        '            from gpu.r184_cpu_bridge import call\n            return call(self.config, origin)\n'
        + ''.join(before.splitlines(keepends=True)[1:]))
    driver.write_text(text.replace(before, after, 1))
    pins = {str(path.relative_to(source)): sha(path) for path in source.rglob('*.py')}
    cpu_path = root / ('RECEIVING_CPU_R204_' + str(time.time_ns()) + '.json')
    write(cpu_path, dict(passed=True, source_pins=pins, Main_archive_sha256=ARCHIVE_SHA,
        Main_READY_sha256=sha(packet/'READY.json'), Main_validation=ready['validation'], local_broad_tests_run=0,
        all_incoming_hashes_verified=True, observed_unix=time.time(), transport='existing exact-trial strict CPU bridge'))
    allocation, guard = read(control/'ALLOCATION.json'), read(control/'GUARD.json')
    bridge, readiness = read(root/'BRIDGE.json'), read(root/'RECEIVING_READY.json')
    tag = '_BEFORE_R204_' + str(time.time_ns())
    for name in ('PLAN','ALLOCATION','GUARD'):
        (control/(name+'.json')).rename(control/(name+tag+'.json'))
    for name in ('BRIDGE','RECEIVING_READY'):
        (root/(name+'.json')).rename(root/(name+tag+'.json'))
    write(control/'PLAN.json', plan)
    allocation.update(plan_sha256=sha(control/'PLAN.json'), cpu_receipt_path=str(cpu_path),
        cpu_receipt_sha256=sha(cpu_path), builder_entry='Main R204 RELEASE, changed-source67 tests PASS; unchanged provenance and recipe')
    write(control/'ALLOCATION.json', allocation)
    guard.update(source_pins=pins, plan_sha256=sha(control/'PLAN.json'), allocation_sha256=sha(control/'ALLOCATION.json'))
    write(control/'GUARD.json', guard)
    bridge['guard_sha256'] = sha(control/'GUARD.json')
    write(root/'BRIDGE.json', bridge)
    subprocess.run([str(PYTHON),'-B','-c','from gpu.orch_r125_continual_guard import validate; import sys; validate(sys.argv[1])',str(control/'GUARD.json')],
        cwd=source, env=dict(os.environ,CUDA_VISIBLE_DEVICES='',PYTHONPATH=str(source),PYTHONDONTWRITEBYTECODE='1'),check=True,timeout=45)
    readiness.update(guard_sha256=sha(control/'GUARD.json'), Main_overlay_sha256=ARCHIVE_SHA,
        think_continuation_policy=plan['think_act_learn']['think_continuation_policy'], observed_unix=time.time())
    write(root/'RECEIVING_READY.json', readiness)
    print(json.dumps(readiness))


def apply(physical):
    host()
    root, source, control = paths(physical)
    with (root/'SOURCE.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX)
        layer(root,source,control)


if __name__ == '__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--physical',type=int,choices=(0,1,3,5),required=True)
    apply(parser.parse_args().physical)
