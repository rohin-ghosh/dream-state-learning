"""Apply the authorized two-file R202 layer and exact first clone input."""

import ast
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time

from math_c import HOME, SOURCE, PYTHON, OVERLAY_SHA, extract_exact
from math_c import host, read, require, sha, write

ARCHIVE_SHA = '84f567f601dff4c86fc839b504d0ae0651ee76f3d24384e0513e5f090b769b91'
PART_ONE_SHA = '48921afaf6c1a7dec7fbe7cbb79c3be8c52bd9612cbcdad3ff6da64fc7469e30'


def apply():
    host()
    require(not (HOME / 'DISPATCHED.json').exists(), 'unlaunched_clone_only')
    ready = read(HOME / 'r202_ready/READY.json')
    require(ready['archive_sha256'] == ARCHIVE_SHA and ready['base_archive_sha256'] == OVERLAY_SHA
        and sha(HOME / 'r202_ready/structured_think_overlay.tar.gz') == ARCHIVE_SHA, 'exact_R202_on_R201')
    overlay = HOME / 'r202_overlay'
    overlay.mkdir()
    extract_exact(HOME / 'r202_ready/structured_think_overlay.tar.gz', overlay, ready['files'])
    for relative in ready['files']:
        (SOURCE / relative).write_bytes((overlay / relative).read_bytes())
    driver = SOURCE / 'gpu/orch_r184_think_act_learn.py'
    original = driver.read_text()
    method = next(node for node in ast.walk(ast.parse(original))
        if isinstance(node, ast.FunctionDef) and node.name == '_cpu')
    lines = original.splitlines(keepends=True)
    before = ''.join(lines[method.lineno - 1:method.end_lineno])
    require('EXISTING_LIFE_CPU_POLICY' in before and 'code_policy' in before, 'same_actual_CPU_policies')
    after = "    def _cpu(self, origin):\n        if self.config['trial_id'] == 'R201_MATH_C_node4_6':\n            from gpu.r184_cpu_bridge import call\n            return call(self.config, origin)\n" + ''.join(before.splitlines(keepends=True)[1:])
    driver.write_text(original.replace(before, after, 1))
    environment = dict(os.environ, PYTHONPATH=':'.join(map(str, (SOURCE, SOURCE / 'tests', HOME / 'test_deps'))),
        PYTHONDONTWRITEBYTECODE='1', CUDA_VISIBLE_DEVICES='', PYTEST_DISABLE_PLUGIN_AUTOLOAD='1',
        OMP_NUM_THREADS='1', MKL_NUM_THREADS='1')
    files = ['tests/test_orch_r184_think_act_learn.py', 'tests/test_orch_r194_console_reflection.py',
             'tests/test_orch_r195_learn_review_filter.py', 'tests/test_orch_r197_correction_ledger.py']
    with (HOME / 'R202_FOCUSED.log').open('x') as output:
        result = subprocess.run([str(PYTHON), '-B', '-m', 'pytest', '-q', '-p', 'no:cacheprovider', *files],
            cwd=SOURCE, env=environment, stdout=output, stderr=subprocess.STDOUT, timeout=90)
    require(result.returncode == 0, 'focused_R202_tests')
    count = re.findall(r'(\d+) passed', (HOME / 'R202_FOCUSED.log').read_text())
    require(len(count) == 1, 'actual_focused_count')
    pins = {str(path.relative_to(SOURCE)): sha(path) for path in SOURCE.rglob('*.py')}
    write(HOME / 'RECEIVING_CPU_R202.json', dict(passed=True, source_pins=pins, tests_run=int(count[0]),
        prior_400_test_receipt_sha256=sha(HOME / 'RECEIVING_CPU.json'), overlay_sha256=ARCHIVE_SHA,
        log_sha256=sha(HOME / 'R202_FOCUSED.log'), original_CPU_method=before,
        actual_bridge_guarded_by_exact_trial=True, observed_unix=time.time()))
    control = HOME / 'control'
    plan = read(control / 'PLAN.json')
    require(plan['think_act_learn']['judgment_policy'] == ready['required_judgment_policy'], 'judgment_first')
    plan['think_act_learn'].update(ready['driver_config_delta'])
    allocation = read(control / 'ALLOCATION.json')
    guard = read(control / 'GUARD.json')
    bridge = read(HOME / 'BRIDGE.json')
    for name in ('PLAN', 'ALLOCATION', 'GUARD'):
        (control / (name + '.json')).rename(control / (name + '_R201.json'))
    (HOME / 'BRIDGE.json').rename(HOME / 'BRIDGE_R201.json')
    (HOME / 'RECEIVING_READY.json').rename(HOME / 'RECEIVING_READY_R201.json')
    write(control / 'PLAN.json', plan)
    allocation.update(plan_sha256=sha(control / 'PLAN.json'),
        cpu_receipt_path=str(HOME / 'RECEIVING_CPU_R202.json'),
        cpu_receipt_sha256=sha(HOME / 'RECEIVING_CPU_R202.json'),
        builder_entry='Main R202 selected-arm READY, 101 focused tests, builder 2026-09-17 19:45 PDT')
    write(control / 'ALLOCATION.json', allocation)
    guard.update(source_pins=pins, plan_sha256=sha(control / 'PLAN.json'),
        allocation_sha256=sha(control / 'ALLOCATION.json'))
    write(control / 'GUARD.json', guard)
    bridge['guard_sha256'] = sha(control / 'GUARD.json')
    write(HOME / 'BRIDGE.json', bridge)
    subprocess.run([str(PYTHON), '-B', '-c',
        'from gpu.orch_r125_continual_guard import validate; import sys; validate(sys.argv[1])',
        str(control / 'GUARD.json')], cwd=SOURCE, env=environment, check=True, timeout=30)
    write(HOME / 'RECEIVING_READY.json', dict(status='CPU_TESTED_NOT_LIVE',
        guard_sha256=sha(control / 'GUARD.json'), cpu_sha256=sha(HOME / 'RECEIVING_CPU_R202.json'),
        structured_think_policy=plan['think_act_learn']['structured_think_policy'],
        comparison_confound='MATH-C differs in structured THINK as well as parent style; not parent-only',
        observed_unix=time.time()))
    print(json.dumps(read(HOME / 'RECEIVING_READY.json')))


def first_input():
    host()
    sys.path.insert(0, str(SOURCE))
    from gpu.orch_r127_pilot_console import publish_parent
    source = HOME / 'inputs/R202_CLONE_PART_ONE_2026-09-17.txt'
    require(sha(source) == PART_ONE_SHA, 'Main_exact_Rohin_PART_ONE')
    require(not list((HOME / 'life/stream/inbox').iterdir()), 'first_new_input_no_other_pending')
    publication = publish_parent(str(HOME / 'life'), 'Rohin', source.read_text())
    write(HOME / 'ROHIN_FIRST_INPUT.json', dict(publication=publication, text_sha256=PART_ONE_SHA,
        queued_unix=time.time(), original_C2_changed=False, story_test_included=False,
        source_file=str(source), status='EXACT_FIRST_NEW_INPUT_QUEUED_NOT_YET_RENDERED'))
    print(json.dumps(read(HOME / 'ROHIN_FIRST_INPUT.json')))


def guided_limit():
    host()
    require(not (HOME / 'DISPATCHED.json').exists(), 'not_launched')
    control = HOME / 'control'
    plan = read(control / 'PLAN.json')
    require(plan['max_sleeps'] == 57, 'initial_six_cycle_screen')
    allocation, guard = read(control / 'ALLOCATION.json'), read(control / 'GUARD.json')
    bridge, ready = read(HOME / 'BRIDGE.json'), read(HOME / 'RECEIVING_READY.json')
    plan['max_sleeps'] = 54
    for name in ('PLAN', 'ALLOCATION', 'GUARD'):
        (control / (name + '.json')).rename(control / (name + '_R202_SIX_CYCLE_DECLARATION.json'))
    for name in ('BRIDGE', 'RECEIVING_READY'):
        (HOME / (name + '.json')).rename(HOME / (name + '_R202_SIX_CYCLE_DECLARATION.json'))
    write(control / 'PLAN.json', plan)
    allocation['plan_sha256'] = sha(control / 'PLAN.json')
    write(control / 'ALLOCATION.json', allocation)
    guard.update(plan_sha256=sha(control / 'PLAN.json'), allocation_sha256=sha(control / 'ALLOCATION.json'))
    write(control / 'GUARD.json', guard)
    bridge['guard_sha256'] = sha(control / 'GUARD.json')
    write(HOME / 'BRIDGE.json', bridge)
    environment = dict(os.environ, PYTHONPATH=str(SOURCE), CUDA_VISIBLE_DEVICES='', PYTHONDONTWRITEBYTECODE='1')
    subprocess.run([str(PYTHON), '-B', '-c',
        'from gpu.orch_r125_continual_guard import validate; import sys; validate(sys.argv[1])',
        str(control / 'GUARD.json')], cwd=SOURCE, env=environment, check=True, timeout=30)
    ready.update(guard_sha256=sha(control / 'GUARD.json'), guided_cycles=[52, 53, 54],
        withdrawn_cycles=[55, 56, 57], phase_boundary='Saved COMPLETE54; pending-parent reconciliation before continuation',
        observed_unix=time.time())
    write(HOME / 'RECEIVING_READY.json', ready)
    print(json.dumps(ready))


if __name__ == '__main__':
    {'apply': apply, 'first_input': first_input, 'guided_limit': guided_limit}[sys.argv[1]]()
