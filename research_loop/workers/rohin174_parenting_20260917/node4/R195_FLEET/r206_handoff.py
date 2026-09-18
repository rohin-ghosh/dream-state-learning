"""Frozen R206 receiving sources and exact-boundary continuation of node4 clones."""

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

from math_c import HOME, PYTHON, WALL, extract_exact, host, read, require, sha, write


ARCHIVE_SHA = 'ab7c3ada0780d8414aba30e59721df1bb8c51fdee747105359682bae3c144f84'


def root_for(physical):
    require(physical in (0, 1, 2, 3, 5, 6, 7), 'seven_authorized_node4_clones_only')
    return HOME if physical == 6 else HOME.parent / f'SCALE_physical{physical}'


def records(root):
    return [read(path) for path in sorted((root / 'life/stream/records').glob('[0-9]' * 20 + '.json'))]


def bind_driver(source, trial, repository):
    path = source / 'gpu/orch_r184_think_act_learn.py'
    text = path.read_text()
    method = next(node for node in ast.walk(ast.parse(text)) if isinstance(node, ast.FunctionDef) and node.name == '_cpu')
    before = ''.join(text.splitlines(keepends=True)[method.lineno - 1:method.end_lineno])
    require('EXISTING_LIFE_CPU_POLICY' in before and 'code_policy' in before, 'strict_root_and_code_policy_retained')
    after = (f"    def _cpu(self, origin):\n        if self.config['trial_id'] == {trial!r}:\n"
        '            from gpu.r184_cpu_bridge import call\n            return call(self.config, origin)\n'
        + ''.join(before.splitlines(keepends=True)[1:]))
    text = text.replace(before, after, 1)
    if repository:
        marker = "        if route == 'CPU':\n"
        require(text.count(marker) == 1, 'one_repository_ACT_binding')
        text = text.replace(marker, f"        if self.config['trial_id'] == {trial!r}:\n"
            '            from research_loop.workers.rohin183_repo_learning_20260917.tools import request\n'
            '            try:\n                action = request(raw_act)\n'
            "            except (ValueError, TypeError):\n                route = 'REPO'\n"
            "            else:\n                if action is not None:\n                    route = 'REPO'\n"
            "        if route in ('CPU', 'REPO'):\n")
        text = text.replace("self.record_outcome(outcome, dispatched=route == 'CPU')",
            "self.record_outcome(outcome, dispatched=route in ('CPU', 'REPO'))")
    compile(text, str(path), 'exec')
    path.write_text(text)


def prepare(physical, audit_path):
    host()
    root = root_for(physical)
    target = root / 'reload_r206'
    target.mkdir()
    snapshot = next(row for row in read(audit_path)['slots'] if row['physical'] == physical)
    current = snapshot['current_native']
    guard_path = Path(current['guard'])
    guard = read(guard_path)
    plan = read(guard['plan_path'])
    old_source = Path(plan['source_root'])
    require(plan['physical'] == physical and plan['root'] == str(root / 'life')
        and plan['hard_end_unix'] == WALL and plan['max_sleeps'] in (54, 57), 'same_life_recipe_and_wall')
    require(sha(guard['plan_path']) == guard['plan_sha256'], 'bound_previous_plan')
    require(all(sha(old_source / name) == digest for name, digest in guard['source_pins'].items()), 'previous_source_unchanged')
    old_bridge_path = old_source.parent / 'BRIDGE.json'
    old_bridge = read(old_bridge_path)
    if old_bridge['guard_path'] != str(guard_path):
        old_bridge_path = root / 'withdrawn/BRIDGE.json'
        old_bridge = read(old_bridge_path)
    require(old_bridge['guard_path'] == str(guard_path) and old_bridge['guard_sha256'] == sha(guard_path), 'actual_current_bridge_binding')
    source, control = target / 'source', target / 'control'
    shutil.copytree(old_source, source)
    control.mkdir()
    packet = HOME.parent / 'r206_ready'
    ready = read(packet / 'READY.json')
    require(ready['status'] == 'CPU_TESTED_NOT_LIVE' and ready['archive_sha256'] == ARCHIVE_SHA
        and sha(packet / 'runtime_overlay.tar.gz') == ARCHIVE_SHA and len(ready['files']) == 42, 'exact_Main_R206_release')
    overlay = target / 'overlay'
    overlay.mkdir()
    extract_exact(packet / 'runtime_overlay.tar.gz', overlay, ready['files'])
    kernel = 'gpu/orch_r132_kernel_bridge.py'
    prior_kernel = sha(source / kernel)
    prior_release = read(HOME.parent / 'r204_ready/READY.json')['files'][kernel]
    require(ready['files'][kernel] == prior_release, 'R206_does_not_conflict_with_existing_kernel_bridge')
    for relative in ready['files']:
        if relative == kernel and prior_kernel != prior_release:
            continue
        (source / relative).parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(overlay / relative, source / relative)
    require(sha(source / kernel) == prior_kernel, 'existing_kernel_bridge_bytes_preserved')
    plan.update(ready['required_native_options'])
    plan['think_act_learn'].update(ready['required_driver_options'])
    plan['source_root'] = str(source)
    if plan.get('startup_context'):
        plan['startup_context']['path'] = str(source / Path(plan['startup_context']['path']).relative_to(old_source))
    bind_driver(source, plan['think_act_learn']['trial_id'], physical == 5)
    bridge_name = 'gpu/r184_cpu_bridge.py'
    require(sha(source / bridge_name) == sha(old_source / bridge_name), 'unchanged_arm_specific_transport')
    pins = {str(path.relative_to(source)): sha(path) for path in source.rglob('*.py')}
    cpu = target / 'RECEIVING_CPU.json'
    write(cpu, dict(passed=True, source_pins=pins, Main_archive_sha256=ARCHIVE_SHA,
        Main_READY_sha256=sha(packet / 'READY.json'), Main_validation=ready['validation'],
        local_broad_tests_run=0, incoming_hashes_verified=42, existing_bridge_sha256=sha(source / bridge_name),
        existing_kernel_bridge_sha256=prior_kernel, observed_unix=time.time()))
    write(control / 'PLAN.json', plan)
    allocation = read(guard['allocation_path'])
    allocation.update(plan_sha256=sha(control / 'PLAN.json'), cpu_receipt_path=str(cpu), cpu_receipt_sha256=sha(cpu),
        declared_unix=time.time(), builder_entry='Main R206 frozen release; receiving hashes/config only; same life and recipe')
    write(control / 'ALLOCATION.json', allocation)
    guard.update(plan_path=str(control / 'PLAN.json'), plan_sha256=sha(control / 'PLAN.json'),
        allocation_path=str(control / 'ALLOCATION.json'), allocation_sha256=sha(control / 'ALLOCATION.json'),
        source_pins=pins, attempt_dir=str(control))
    guard['device_containment']['unit'] = 'orch-r136-native-' + uuid.uuid4().hex
    write(control / 'GUARD.json', guard)
    bridge = dict(old_bridge, native_source=str(source), guard_path=str(control / 'GUARD.json'),
        guard_sha256=sha(control / 'GUARD.json'), socket=str(target / 'cpu.sock'))
    write(target / 'BRIDGE.json', bridge)
    subprocess.run([str(PYTHON), '-B', '-c',
        'from gpu.orch_r125_continual_guard import validate; import sys; validate(sys.argv[1])', str(control / 'GUARD.json')],
        cwd=source, env=dict(os.environ, CUDA_VISIBLE_DEVICES='', PYTHONPATH=str(source), PYTHONDONTWRITEBYTECODE='1'),
        check=True, timeout=45)
    selected = dict(plan=read(read(guard_path)['plan_path']), guard_path=str(guard_path), guard_sha256=sha(guard_path),
        backing_root=str((root / 'life').resolve()), native=dict(pid=current['pid'], start_ticks=current['start_ticks']))
    write(target / 'CONTEXT.json', dict(selected=selected, selection=str(target / 'SELECTION.json'),
        retirement=str(target / 'boundary'), old_bridge_path=str(old_bridge_path), source_archive_sha256=ARCHIVE_SHA))
    write(target / 'RECEIVING_READY.json', dict(status='CPU_TESTED_NOT_LIVE', physical=physical,
        guard_sha256=sha(control / 'GUARD.json'), Main_archive_sha256=ARCHIVE_SHA,
        same_life=True, max_sleeps=plan['max_sleeps'], prepared_unix=time.time()))
    print(json.dumps(read(target / 'RECEIVING_READY.json')), flush=True)


def arm(physical):
    host()
    root = root_for(physical)
    require(not (root / 'R207_MAIN_INFERENCE_RESERVATION.json').exists(), 'reserved_for_Main_no_new_allocation')
    target = root / 'reload_r206'
    require(read(target / 'RECEIVING_READY.json')['guard_sha256'] == sha(target / 'control/GUARD.json'), 'receiving_ready_unchanged')
    require((root / 'PARENT_WITHDRAWAL_CLOSED.json').exists()
        and read(root / 'PARENT_WITHDRAWAL_RECONCILED.json')['no_pending_parent_replay'], 'withdrawn_parent_frontier_preserved')
    complete = [record for record in records(root) if record['kind'] == 'SLEEP_COMPLETE']
    if complete[-1]['document']['cycle'] >= 57:
        write(target / 'HELD_SCREEN_COMPLETE.json', dict(status='FIXED_SCREEN_COMPLETE_R206_READY_NOT_DISPATCHED',
            cycle=57, complete_sha256=complete[-1]['sha256'], observed_unix=time.time(), no_signals=True))
        return
    import r203_retire
    context = read(target / 'CONTEXT.json')
    r203_retire.prepare_binding(physical, capture=True, reload_context=context)
    with (target / 'OPERATOR.log').open('x') as output:
        process = subprocess.Popen([str(PYTHON), '-B', str(HOME / 'r206_handoff.py'), 'run', '--physical', str(physical)],
            stdin=subprocess.DEVNULL, stdout=output, stderr=subprocess.STDOUT, start_new_session=True)
    write(target / 'ARMED.json', dict(pid=process.pid, started_unix=time.time(), exact_native=context['selected']['native']))
    print(json.dumps(read(target / 'ARMED.json')), flush=True)


def phase(physical):
    from reload_math_c import exact_stop
    host()
    require(physical == 5, 'only_remaining_guided_repository_arm')
    root = root_for(physical)
    target = root / 'reload_r206'
    require(read(target / 'RECEIVING_READY.json')['guard_sha256'] == sha(target / 'control/GUARD.json'), 'R206_ready_before_watcher_change')
    require(read(target / 'control/PLAN.json')['max_sleeps'] == 54, 'unchanged_guided_phase_cap')
    require(not (root / 'withdrawn').exists() and not (root / 'PARENT_WITHDRAWAL_CLOSED.json').exists(),
        'no_concurrent_withdrawal_dispatch')
    latest = records(root)[-1]
    require(latest['kind'] != 'TERMINAL' and not (root / 'control/EXIT.json').exists(), 'guided_life_still_running')
    watcher = read(root / 'WITHDRAWAL_WAITER.json')
    exact_stop(watcher['pid'], [str(root / 'withdraw_math_c.py')])
    require(not (root / 'withdrawn').exists(), 'old_watcher_exited_before_phase_transition')
    support = (root / 'arm_support.py').read_text().replace("SOURCE = HOME / 'source'", "SOURCE = HOME / 'reload_r206/source'")
    require("SOURCE = HOME / 'reload_r206/source'" in support, 'explicit_receiving_source')
    (root / 'withdraw_r206_support.py').write_text(support)
    worker = (root / 'withdraw_math_c.py').read_text().replace('from arm_support import', 'from withdraw_r206_support import')
    for filename in ('PLAN.json', 'ALLOCATION.json', 'GUARD.json'):
        worker = worker.replace("HOME / 'control/" + filename + "'", "HOME / 'reload_r206/control/" + filename + "'")
    worker = worker.replace("HOME / 'BRIDGE.json'", "HOME / 'reload_r206/BRIDGE.json'")
    worker = worker.replace('WITHDRAWAL_WAITER.json', 'WITHDRAWAL_WAITER_R206.json')
    compile(worker, str(root / 'withdraw_r206.py'), 'exec')
    (root / 'withdraw_r206.py').write_text(worker)
    with (root / 'WITHDRAWAL_R206.log').open('x') as output:
        process = subprocess.Popen([str(PYTHON), '-B', str(root / 'withdraw_r206.py')],
            stdin=subprocess.DEVNULL, stdout=output, stderr=subprocess.STDOUT, start_new_session=True)
    write(target / 'PHASE_ARMED.json', dict(pid=process.pid, started_unix=time.time(), old_watcher_pid=watcher['pid'],
        transition='natural_COMPLETE54_then_R206_same_life_55_to57', no_native_signals=True,
        parent_withdrawal_reconciliation_unchanged=True))
    print(json.dumps(read(target / 'PHASE_ARMED.json')), flush=True)


def run(physical):
    import r203_retire
    import retire_brain_guided6 as existing
    root = root_for(physical)
    target = root / 'reload_r206'
    context = read(target / 'CONTEXT.json')

    def check_ready():
        require(read(target / 'RECEIVING_READY.json')['guard_sha256'] == sha(target / 'control/GUARD.json'), 'R206_receiving_ready')
        require(read(root / 'PARENT_WITHDRAWAL_RECONCILED.json')['no_pending_parent_replay'], 'no_withdrawn_parent_replay')

    existing.prepare = lambda: r203_retire.prepare_binding(physical, reload_context=context)
    existing.run(wait_seconds=2400, check_ready=check_ready)
    require((target / 'boundary/RETIRED.json').exists(), 'fresh_COMPLETE_preserved')
    launch(physical)


def launch(physical):
    root = root_for(physical)
    require(not (root / 'R207_MAIN_INFERENCE_RESERVATION.json').exists(), 'reserved_for_Main_no_new_allocation')
    target = root / 'reload_r206'
    with (target / 'SOURCE.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        require(not (target / 'DISPATCHED.json').exists(), 'no_duplicate_dispatch')
        retired = read(target / 'boundary/RETIRED.json')
        require(retired['status'] == 'EXACT_COMPLETE_PRESERVED_RETIRED', 'exact_preserved_boundary')
        if retired['cycle'] >= 57:
            write(target / 'HELD_SCREEN_COMPLETE.json', dict(status='FIXED_SCREEN_COMPLETE_R206_READY_NOT_DISPATCHED',
                cycle=retired['cycle'], retired_unix=retired['retired_unix'], observed_unix=time.time()))
            return
        bridge = read(target / 'BRIDGE.json')
        bridge['first_new_record'] = int(Path(retired['saved']['record_path']).stem) + 1
        (target / 'BRIDGE.json').rename(target / 'BRIDGE_PREBOUNDARY.json')
        write(target / 'BRIDGE.json', bridge)
        with (target / 'BRIDGE.log').open('x') as output:
            server = subprocess.Popen([str(PYTHON), '-B', str(root / 'math_c_bridge.py'), '--config', str(target / 'BRIDGE.json')],
                stdin=subprocess.DEVNULL, stdout=output, stderr=subprocess.STDOUT, start_new_session=True)
        deadline = time.monotonic() + 15
        while not list((target / 'bridge_receipts').glob('READY_*.json')):
            require(time.monotonic() < deadline and server.poll() is None, 'actual_R206_bridge_ready')
            time.sleep(.1)
        module = 'gpu.orch_r188_node4_rehome_containment' if physical == 6 else 'gpu.r203_node4_containment'
        source = target / 'source'
        command = [str(PYTHON), '-B', '-m', module, 'contained-supervise', '--config', str(target / 'control/GUARD.json')]
        with (target / 'control/SUPERVISOR.log').open('x') as output:
            native = subprocess.Popen(command, cwd=source,
                env=dict(os.environ, CUDA_VISIBLE_DEVICES='', PYTHONPATH=str(source), PYTHONDONTWRITEBYTECODE='1'),
                stdin=subprocess.DEVNULL, stdout=output, stderr=subprocess.STDOUT, start_new_session=True)
        write(target / 'DISPATCHED.json', dict(physical=physical, supervisor_pid=native.pid, bridge_pid=server.pid,
            started_unix=time.time(), saved_cycle=retired['cycle'], root=str(root / 'life'), max_sleeps=57,
            source_archive_sha256=ARCHIVE_SHA, no_inbox_or_history_reset=True, no_parent_publications=True))
        print(json.dumps(read(target / 'DISPATCHED.json')), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=('prepare', 'arm', 'phase', 'run', 'launch'))
    parser.add_argument('--physical', type=int, required=True)
    parser.add_argument('--audit')
    options = parser.parse_args()
    if options.action == 'prepare':
        prepare(options.physical, options.audit)
    else:
        globals()[options.action](options.physical)
