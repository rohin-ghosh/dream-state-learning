"""Receiving-only MATH-C assembly using Main's frozen source and existing guard."""

import ast
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import time
import uuid

from math_c import HOME, SOURCE, GATE, OLD_GUARD, LEASE, WALL, PYTHON, HOST_SHA
from math_c import host, read, require, sha, write


def assemble():
    host()
    ready = read(HOME / 'main_ready/READY.json')
    require(all(sha(SOURCE / name) == expected for name, expected in ready['files'].items()),
            'exact_Main_READY_before_transport_hook')
    clone = read(HOME / 'CLONE_RESTORED.json')
    require(clone['optimizer_steps'] == 4908 and clone['first_new_record'] == 4,
            'exact_CPU_restored_source51_context5846')
    driver = SOURCE / 'gpu/orch_r184_think_act_learn.py'
    original = driver.read_text()
    nodes = [node for node in ast.walk(ast.parse(original))
             if isinstance(node, ast.FunctionDef) and node.name == '_cpu']
    require(len(nodes) == 1, 'one_cpu_transport')
    node = nodes[0]
    lines = original.splitlines(keepends=True)
    method = ''.join(lines[node.lineno - 1:node.end_lineno])
    require('EXISTING_LIFE_CPU_POLICY' in method and 'code_policy' in method, 'Main_explicit_policies')
    replacement = "    def _cpu(self, origin):\n        if self.config['trial_id'] == 'R201_MATH_C_node4_6':\n            from gpu.r184_cpu_bridge import call\n            return call(self.config, origin)\n"
    replacement += ''.join(method.splitlines(keepends=True)[1:])
    driver.write_text(original.replace(method, replacement, 1))
    shutil.copyfile(HOME / 'math_c_bridge.py', SOURCE / 'gpu/r184_cpu_bridge.py')
    write(HOME / 'BRIDGE_ADAPTATION.json', dict(original_method=method,
        original_driver_sha256=ready['files']['gpu/orch_r184_think_act_learn.py'],
        receiving_driver_sha256=sha(driver), original_source_modified=False,
        first_new_record=4, cpu_source=str(GATE.parent / 'source'), observed_unix=time.time()))


def configure():
    host()
    sys.path.insert(0, str(SOURCE))
    from gpu.orch_r125_continual_native import validate_plan
    from gpu.orch_r125_stream_journal import StreamJournal
    from organism_v6.orch_r125_continual_stream import ContinualStream
    plan_path = HOME / 'control/PLAN.json'
    plan = validate_plan(read(plan_path))
    require(Path(plan['model_dir']).is_dir() and Path(plan['anchors']).is_dir(), 'receiving_base_and_anchors')
    require(plan['max_sleeps'] == 57 and plan['hard_end_unix'] == WALL, 'six_cycles_unchanged_wall')
    with StreamJournal(Path(plan['root']) / 'stream', create=False) as journal:
        latest = journal.latest_checkpoint()
        state = ContinualStream.restore(latest['document'], expected_sha256=latest['expected_sha256'])
        require(state.pending is None and len(state.rows) == state.sleep_frontier == 153,
                'exact_restore_boundary')
    ready = read(HOME / 'main_ready/READY.json')
    modules = [name for name in ready['files'] if name.startswith('tests/')]
    environment = dict(os.environ, PYTHONPATH=':'.join(map(str, (SOURCE, SOURCE / 'tests', HOME / 'test_deps'))),
                       PYTHONDONTWRITEBYTECODE='1', PYTEST_DISABLE_PLUGIN_AUTOLOAD='1',
                       CUDA_VISIBLE_DEVICES='', OMP_NUM_THREADS='1', MKL_NUM_THREADS='1')
    log_path = HOME / 'RECEIVING_CPU_FINAL.log'
    with log_path.open('x') as log:
        result = subprocess.run([str(PYTHON), '-B', '-m', 'pytest', *modules, '-q',
                                 '-p', 'no:cacheprovider', '--basetemp', str(HOME / 'pytest_tmp')],
            cwd=SOURCE, env=environment, stdout=log, stderr=subprocess.STDOUT, timeout=180)
    require(result.returncode == 0, 'receiving_tests_failed_see_log')
    text = log_path.read_text()
    counts = re.findall(r'(\d+) passed', text)
    require(len(counts) == 1 and not re.search(r'\d+ skipped', text), 'receiving_tests_no_skips')
    pins = {str(path.relative_to(SOURCE)): sha(path) for path in SOURCE.rglob('*.py')}
    write(HOME / 'RECEIVING_CPU.json', dict(passed=True, tests_run=int(counts[0]),
        log_sha256=sha(log_path), source_pins=pins, observed_unix=time.time(),
        complete_cycle=51, console_cut=5846, no_GPU_model_calls=True))
    control = HOME / 'control'
    write(control / 'ALLOCATION.json', dict(physical=6, gpu_uuid=plan['gpu_uuid'],
        plan_sha256=sha(plan_path), cpu_tests_passed=True, builder_entry_pushed=True, builder_entry_logged=True,
        cpu_receipt_path=str(HOME / 'RECEIVING_CPU.json'),
        builder_entry='Main R201 MATH-C physical6 allocation, tested READY, table updated 2026-09-17 19:35 PDT',
        declared_unix=time.time(), cpu_receipt_sha256=sha(HOME / 'RECEIVING_CPU.json')))
    guard = dict(read(OLD_GUARD), plan_path=str(plan_path), plan_sha256=sha(plan_path),
        allocation_path=str(control / 'ALLOCATION.json'), allocation_sha256=sha(control / 'ALLOCATION.json'),
        attempt_dir=str(control), resume=True, source_pins=pins, host_sha256=HOST_SHA,
        hard_end_unix=WALL, next_reserved_unix=read(LEASE)['lease_end_unix'],
        lease_path=str(LEASE), lease_sha256=sha(LEASE), device_containment=dict(
            uid=2524, gid=2524, minor=5, unit='orch-r136-native-' + uuid.uuid4().hex))
    write(control / 'GUARD.json', guard)
    finish_binding()


def finish_binding():
    control = HOME / 'control'
    plan = read(control / 'PLAN.json')
    environment = dict(os.environ, PYTHONPATH=str(SOURCE), PYTHONDONTWRITEBYTECODE='1', CUDA_VISIBLE_DEVICES='')
    subprocess.run([str(PYTHON), '-B', '-c',
        'from gpu.orch_r125_continual_guard import validate; import sys; validate(sys.argv[1])',
        str(control / 'GUARD.json')], cwd=SOURCE, env=environment, check=True, timeout=60)
    clone = read(HOME / 'CLONE_RESTORED.json')
    socket_path = str(HOME / 'cpu.sock')
    require(len(socket_path.encode()) < 108, 'unix_socket_length')
    write(HOME / 'BRIDGE.json', dict(socket=socket_path, cpu_source=str(GATE.parent / 'source'),
        native_source=str(SOURCE), raw_root=str(HOME / 'life'), journal_id=clone['journal_id'],
        guard_path=str(control / 'GUARD.json'), guard_sha256=sha(control / 'GUARD.json'),
        gate_root=str(GATE), gate_sha256=plan['think_act_learn']['cpu_gate_sha256'],
        code_policy=plan['think_act_learn']['code_policy'], first_new_record=4, stop_unix=WALL))
    write(HOME / 'RECEIVING_READY.json', dict(status='CPU_TESTED_NOT_LIVE',
        guard_sha256=sha(control / 'GUARD.json'), cpu_sha256=sha(HOME / 'RECEIVING_CPU.json'),
        unchanged_hard_wall=WALL, observed_unix=time.time(), retirement_signals=0))
    print(json.dumps(read(HOME / 'RECEIVING_READY.json')))


def repair_allocation():
    host()
    control = HOME / 'control'
    allocation = read(control / 'ALLOCATION.json')
    guard = read(control / 'GUARD.json')
    require(sha(control / 'ALLOCATION.json') == guard['allocation_sha256'], 'unchanged_failed_allocation')
    require(read(HOME / 'RECEIVING_CPU.json')['source_pins'] == guard['source_pins'], 'same_tested_source')
    allocation.update(builder_entry_logged=True, cpu_receipt_path=str(HOME / 'RECEIVING_CPU.json'))
    (control / 'ALLOCATION.json').rename(control / 'ALLOCATION_INITIAL_DECLARATION.json')
    (control / 'GUARD.json').rename(control / 'GUARD_INITIAL_DECLARATION.json')
    write(control / 'ALLOCATION.json', allocation)
    guard['allocation_sha256'] = sha(control / 'ALLOCATION.json')
    write(control / 'GUARD.json', guard)
    finish_binding()


if __name__ == '__main__':
    {'assemble': assemble, 'configure': configure, 'repair_allocation': repair_allocation}[sys.argv[1]]()
