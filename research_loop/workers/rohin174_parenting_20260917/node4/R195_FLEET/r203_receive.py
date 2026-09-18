"""Layer Main's release, bind existing transports, and dispatch assigned clones."""

import argparse
import ast
import fcntl
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time
import uuid

from math_c import HOME, GATE, LEASE, PYTHON, HOST_SHA, WALL, host, read, require, sha, write, extract_exact
from r203_prepare import ASSIGNMENTS
from stage_scale import DEVICES


OWN = Path(__file__).resolve().parent
ARCHIVE_SHA = 'ca6c1b006260c677bdbb003baf52333e354d7a9e0ec266ebdacac08992f89544'
PART_ONE_SHA = '48921afaf6c1a7dec7fbe7cbb79c3be8c52bd9612cbcdad3ff6da64fc7469e30'
STYLE = {'A': (1, 240), 'B': (2, 160), 'C': (3, 120), 'D': (3, 90)}


def paths(physical):
    root = HOME.parent / f'SCALE_physical{physical}'
    return root, root / 'source', root / 'control'


def prepare(physical):
    host()
    root, source, control = paths(physical)
    assignment = read(root / 'R203_ASSIGNMENT.json')
    require(assignment['physical'] == physical and not (root / 'DISPATCHED.json').exists(), 'assigned_unlaunched_receiver')
    repository = physical == 5
    packet = HOME.parent / ('r204_ready' if repository else 'r203_ready')
    archive_sha = 'b0f148c92172af9d1525fda79a97bebfb31337e312e26c0f6bc805b3c687f8fc' if repository else ARCHIVE_SHA
    ready = read(packet / 'READY.json')
    require(ready['archive_sha256'] == archive_sha and sha(packet / 'runtime_overlay.tar.gz') == archive_sha
        and ready['status'] == 'CPU_TESTED_NOT_LIVE' and len(ready['files']) == 37, 'Main_exact_R203_RELEASE')
    overlay = root / 'r203_overlay'
    overlay.mkdir()
    extract_exact(packet / 'runtime_overlay.tar.gz', overlay, ready['files'])
    for relative in ready['files']:
        shutil.copyfile(overlay / relative, source / relative)
    plan = read(control / 'PLAN.json')
    plan.update(ready['required_native_options'], max_sleeps=54)
    trial = plan['think_act_learn']['trial_id']
    plan['think_act_learn'].update(ready['required_driver_options'])
    facts = ('Actual isolated Python3.12.3 has SymPy1.14.0 and mpmath1.3.0, plus the Python standard library. '
        'No Torch, GPU execution, network, home access or external repository route is provided by this Python tool. '
        'Only returned tool receipts establish execution, not a proposed computation. ')
    plan['think_act_learn']['environment_facts'] = facts + assignment['parent_brief']
    if repository:
        from receive_repo import bind_transport, ENVIRONMENT
        bind_transport(root, source, trial)
        plan['think_act_learn']['environment_facts'] = ENVIRONMENT + assignment['parent_brief']
    driver = source / 'gpu/orch_r184_think_act_learn.py'
    text = driver.read_text()
    method = next(node for node in ast.walk(ast.parse(text)) if isinstance(node, ast.FunctionDef) and node.name == '_cpu')
    lines = text.splitlines(keepends=True)
    before = ''.join(lines[method.lineno-1:method.end_lineno])
    require('EXISTING_LIFE_CPU_POLICY' in before and 'code_policy' in before, 'strict_actual_CPU_policy_preserved')
    after = (f"    def _cpu(self, origin):\n        if self.config['trial_id'] == {trial!r}:\n"
        '            from gpu.r184_cpu_bridge import call\n            return call(self.config, origin)\n'
        + ''.join(before.splitlines(keepends=True)[1:]))
    text = text.replace(before, after, 1)
    if repository:
        marker = "        if route == 'CPU':\n"
        require(text.count(marker) == 1, 'one_ACT_dispatch_binding')
        text = text.replace(marker, f"        if self.config['trial_id'] == {trial!r}:\n"
            '            from research_loop.workers.rohin183_repo_learning_20260917.tools import request\n'
            '            try:\n                action = request(raw_act)\n'
            "            except (ValueError, TypeError):\n                route = 'REPO'\n"
            "            else:\n                if action is not None:\n                    route = 'REPO'\n"
            "        if route in ('CPU', 'REPO'):\n")
        text = text.replace("self.record_outcome(outcome, dispatched=route == 'CPU')",
            "self.record_outcome(outcome, dispatched=route in ('CPU', 'REPO'))")
    driver.write_text(text)
    if not repository:
        shutil.copyfile(OWN / 'math_c_bridge.py', source / 'gpu/r184_cpu_bridge.py')
    shutil.copyfile(OWN / 'node4_containment.py', source / 'gpu/r203_node4_containment.py')
    for name in ('math_c_bridge.py', 'arm_support.py', 'read_snapshot.py', 'read_transcript.py'):
        if not repository or name != 'math_c_bridge.py':
            shutil.copyfile(OWN / name, root / name)
    endpoint = (OWN / 'parent_endpoint.py').read_text().replace('from math_c import', 'from arm_support import')
    opening = next(node for node in ast.parse(endpoint).body if isinstance(node, ast.Assign)
        and any(isinstance(target, ast.Name) and target.id == 'OPENING' for target in node.targets))
    endpoint_lines = endpoint.splitlines(keepends=True)
    endpoint = ''.join(endpoint_lines[:opening.lineno-1]) + "OPENING = read(HOME / 'PARENT_SPEC.json')['opening']\n" + ''.join(endpoint_lines[opening.end_lineno:])
    endpoint = endpoint.replace("len(message.split()) <= 120", "len(message.split()) <= read(HOME / 'PARENT_SPEC.json')['word_limit']")
    endpoint = endpoint.replace("structured_think_policy='R202_WIDE_NARROW_WIDE_V1'", "structured_think_policy=read(HOME / 'control/PLAN.json')['think_act_learn'].get('structured_think_policy')")
    (root / 'parent_endpoint.py').write_text(endpoint)
    withdrawal = (OWN / 'withdraw_math_c.py').read_text().replace('from math_c import', 'from arm_support import')
    withdrawal = withdrawal.replace('gpu.orch_r188_node4_rehome_containment', 'gpu.r203_node4_containment')
    withdrawal = withdrawal.replace('MATH-C R202 structured THINK plus parentC, not parent-style-only',
        'R203 heterogeneous environment and parent-style screen; not a parent-style-only contrast')
    (root / 'withdraw_math_c.py').write_text(withdrawal)
    cadence, words = STYLE[assignment['parent_style']]
    from parent_repairs import new_opening
    opening_text = new_opening(assignment, words)
    require(len(opening_text.split()) <= words, 'bounded_actual_new_parent_opening')
    write(root / 'PARENT_SPEC.json', dict(arm=assignment['arm'], style=assignment['parent_style'],
        cadence=cadence, word_limit=words, opening=opening_text, actual_environment=facts,
        clean_reference_sha256=assignment['clean_reference_sha256']))
    pins = {str(path.relative_to(source)): sha(path) for path in source.rglob('*.py')}
    write(root / 'RECEIVING_CPU_R203.json', dict(passed=True, source_pins=pins, Main_archive_sha256=archive_sha,
        Main_READY_sha256=sha(packet / 'READY.json'), Main_validation=ready['validation'],
        local_broad_tests_run=0, all_37_incoming_hashes_verified=True, observed_unix=time.time(),
        operator_bindings=['exact-trial existing CPU bridge', 'seven assigned UUIDs through unchanged strict containment'],
        original_CPU_method_sha256=__import__('hashlib').sha256(before.encode()).hexdigest()))
    (control / 'PLAN.json').rename(control / 'PLAN_INITIAL_FIXED_STATE.json')
    write(control / 'PLAN.json', plan)
    write(control / 'ALLOCATION.json', dict(physical=physical, gpu_uuid=plan['gpu_uuid'], plan_sha256=sha(control / 'PLAN.json'),
        cpu_tests_passed=True, builder_entry_logged=True, builder_entry_pushed=True, declared_unix=time.time(),
        builder_entry=('Main R204 RELEASE; 67 changed-source CPU tests; exact repository transport receiving checks'
            if repository else 'Main R203 RELEASE; 125+217+29 CPU results; seven exact node4 slot assignments'),
        cpu_receipt_path=str(root / 'RECEIVING_CPU_R203.json'), cpu_receipt_sha256=sha(root / 'RECEIVING_CPU_R203.json')))
    guard = read(HOME / 'control/GUARD.json')
    guard.update(plan_path=str(control / 'PLAN.json'), plan_sha256=sha(control / 'PLAN.json'),
        allocation_path=str(control / 'ALLOCATION.json'), allocation_sha256=sha(control / 'ALLOCATION.json'),
        attempt_dir=str(control), source_pins=pins, resume=True,
        device_containment=dict(uid=2524, gid=2524, minor=DEVICES[physical][1], unit='orch-r136-native-'+uuid.uuid4().hex))
    write(control / 'GUARD.json', guard)
    environment = dict(os.environ, PYTHONPATH=str(source), CUDA_VISIBLE_DEVICES='', PYTHONDONTWRITEBYTECODE='1')
    subprocess.run([str(PYTHON), '-B', '-c', 'from gpu.orch_r125_continual_guard import validate; import sys; validate(sys.argv[1])',
        str(control / 'GUARD.json')], cwd=source, env=environment, check=True, timeout=45)
    socket_path = str(HOME.parent / f's{physical}.sock')
    require(len(socket_path.encode()) < 108, 'bounded_socket_path')
    bridge_config = dict(socket=socket_path, cpu_source=str(GATE.parent / 'source'), native_source=str(source),
        raw_root=str(root / 'life'), journal_id=read(root / 'CLONE_RESTORED.json')['journal_id'],
        guard_path=str(control / 'GUARD.json'), guard_sha256=sha(control / 'GUARD.json'),
        gate_root=str(GATE), gate_sha256=plan['think_act_learn']['cpu_gate_sha256'],
        code_policy=plan['think_act_learn']['code_policy'], first_new_record=4, stop_unix=WALL)
    if repository:
        bridge_config.update(repo_config=str(root / 'TOOLS.json'), repo_config_sha256=sha(root / 'TOOLS.json'))
    write(root / 'BRIDGE.json', bridge_config)
    sys.path.insert(0, str(source))
    from gpu.orch_r127_pilot_console import publish_parent
    first = root / 'inputs/R202_CLONE_PART_ONE_2026-09-17.txt'
    require(sha(first) == PART_ONE_SHA and not list((root / 'life/stream/inbox').iterdir()), 'exact_first_input_only')
    publication = publish_parent(str(root / 'life'), 'Rohin', first.read_text())
    write(root / 'ROHIN_FIRST_INPUT.json', dict(publication=publication, queued_unix=time.time(), text_sha256=PART_ONE_SHA))
    write(root / 'RECEIVING_READY.json', dict(status='CPU_TESTED_NOT_LIVE', guard_sha256=sha(control / 'GUARD.json'),
        Main_overlay_sha256=archive_sha, observed_unix=time.time(), physical=physical, arm=assignment['arm']))
    print(json.dumps(read(root / 'RECEIVING_READY.json')))


def launch(physical):
    require(not (HOME.parent / f'SCALE_physical{physical}' / 'R207_MAIN_INFERENCE_RESERVATION.json').exists(),
        'reserved_for_Main_no_new_allocation')
    root, source, control = paths(physical)
    with (root / 'SOURCE.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        return dispatch(physical)


def dispatch(physical):
    host()
    root, source, control = paths(physical)
    require(sha(control / 'GUARD.json') == read(root / 'RECEIVING_READY.json')['guard_sha256'], 'ready_bound_guard')
    if physical in (0, 1, 3, 5):
        require(read(root / 'retirement/RETIRED.json')['status'] == 'EXACT_COMPLETE_PRESERVED_RETIRED', 'selected_life_retired')
    with (root / 'BRIDGE.log').open('x') as log:
        bridge = subprocess.Popen([str(PYTHON), '-B', str(root / 'math_c_bridge.py'), '--config', str(root / 'BRIDGE.json')],
            stdin=subprocess.DEVNULL, stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
    deadline = time.monotonic()+15
    while not list((root / 'bridge_receipts').glob('READY_*.json')):
        require(time.monotonic()<deadline and bridge.poll() is None, 'actual_CPU_bridge_ready')
        time.sleep(.1)
    command = [str(PYTHON), '-B', '-m', 'gpu.r203_node4_containment', 'contained-supervise', '--config', str(control / 'GUARD.json')]
    with (control / 'SUPERVISOR.log').open('x') as log:
        process = subprocess.Popen(command, cwd=source, env=dict(os.environ, CUDA_VISIBLE_DEVICES='', PYTHONPATH=str(source),
            PYTHONDONTWRITEBYTECODE='1'), stdin=subprocess.DEVNULL, stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
    with (root / 'WITHDRAWAL.log').open('x') as log:
        withdrawal = subprocess.Popen([str(PYTHON), '-B', str(root / 'withdraw_math_c.py')], stdin=subprocess.DEVNULL,
            stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
    write(root / 'DISPATCHED.json', dict(supervisor_pid=process.pid, bridge_pid=bridge.pid,
        withdrawal_pid=withdrawal.pid, started_unix=time.time(), physical=physical))
    print(json.dumps(read(root / 'DISPATCHED.json')))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=('prepare', 'launch'))
    parser.add_argument('--physical', type=int, choices=tuple(ASSIGNMENTS), required=True)
    options = parser.parse_args()
    {'prepare': prepare, 'launch': launch}[options.action](options.physical)
