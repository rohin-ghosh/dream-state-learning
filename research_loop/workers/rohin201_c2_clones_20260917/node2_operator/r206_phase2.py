"""Continue naturally completed node2 screens, never restart an active owner."""

import argparse
import ast
import importlib.util
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tarfile
import time

import saved_primitives as saved


BASE = Path('/localhome/local-rohing/orch_r153_r201_node2_clones_20260917_operator1')
PYTHON = '/localhome/local-rohing/v2/venv/bin/python'
ARCHIVE = 'ab7c3ada0780d8414aba30e59721df1bb8c51fdee747105359682bae3c144f84'
ATTEMPT = 'r206_phase2_withdrawn_20260918'
ARMS = {'math_d1': 1, 'repo_c1': 3, 'creative_d1': 4, 'math_transfer_c1': 6}
read, write, sha, require = saved.read, saved.write, saved.sha, saved.require


def environment(source):
    return dict(PATH='/usr/bin:/bin', HOME=str(source.parent), TMPDIR='/tmp', CUDA_VISIBLE_DEVICES='',
        PYTHONPATH=str(source), PYTHONDONTWRITEBYTECODE='1', HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1',
        OMP_NUM_THREADS='1', MKL_NUM_THREADS='1', TOKENIZERS_PARALLELISM='false')


def executor_patch(released, previous, trial_id):
    methods = [node for node in ast.walk(ast.parse(previous)) if isinstance(node, ast.FunctionDef) and node.name == '_cpu']
    require(len(methods) == 1 and isinstance(methods[0].body[0], ast.If), 'existing_arm_executor_required')
    branch = methods[0].body[0]
    source = ''.join(previous.splitlines(keepends=True)[branch.lineno - 1:branch.end_lineno])
    require(trial_id in source and 'return' in source, 'exact_arm_executor_trial')
    marker = '    def _cpu(self, origin):\n'
    require(released.count(marker) == 1, 'unique_released_executor')
    changed = released.replace(marker, marker + source, 1)
    ast.parse(changed)
    return changed


def terminal_boundary(raw):
    paths = sorted((raw / 'stream/records').glob('[0-9]' * 20 + '.json'))
    records = [read(path) for path in paths[-3:]]
    require([record['kind'] for record in records] == ['SLEEP_COMPLETE', 'R184_LEARN_COMPLETE', 'TERMINAL'], 'natural_screen_terminal_required')
    complete, learned, terminal = records
    require(terminal['document'] == dict(completed_sleeps=57, status='R184_SCREEN_STOP'), 'only_original_six_cycle_screen')
    for record in records:
        require(record['sha256'] == saved.digest({key: value for key, value in record.items() if key != 'sha256'}), 'terminal_chain_integrity')
    require(learned['previous_sha256'] == complete['sha256'] and terminal['previous_sha256'] == learned['sha256'], 'terminal_chain_links')
    document = complete['document']
    state = document['resume_state']['state']
    require(document['cycle'] == learned['document']['cycle'] == 57 and document['status'] == 'COMPLETE'
        and document['checkpoint'] == learned['document']['checkpoint'] and state['pending'] is None
        and state['sleep_frontier'] == len(state['rows'])
        and saved.digest(state) == document['resume_state']['sha256'], 'exact_complete57_no_unsaved_rows')
    return dict(record=complete, terminal=saved.reference(paths[-1]), cycle=57, index=complete['index'])


def old_control(root, arm):
    if arm == 'repo_c1':
        return root / 'r204_boundary_20260918t0356z/control'
    return root / ('control' if arm == 'math_d1' else 'control_r204_casefix')


def no_owner(control):
    for process in Path('/proc').glob('[0-9]*'):
        try:
            arguments = (process / 'cmdline').read_bytes().decode().split('\0')
        except (OSError, UnicodeDecodeError):
            continue
        require(str(control / 'GUARD.json') not in arguments, 'previous_owner_or_supervisor_still_alive')


def stage(arm):
    root = BASE / arm
    output = root / ATTEMPT
    old = old_control(root, arm)
    require(not output.exists(), 'new_phase_identity_only')
    output.mkdir()
    source = output / 'source'
    old_plan = read(old / 'PLAN.json')
    require(old_plan['max_sleeps'] == 57 and old_plan['physical'] == ARMS[arm], 'exact_assigned_screen')
    shutil.copytree(old_plan['source_root'], source, ignore=shutil.ignore_patterns('__pycache__'))
    previous_driver = (source / 'gpu/orch_r184_think_act_learn.py').read_text()
    ready = read(BASE / 'r206_ready/READY.json')
    require(sha(BASE / 'r206_ready/runtime_overlay.tar.gz') == ready['archive_sha256'] == ARCHIVE, 'frozen_R206_release')
    with tarfile.open(BASE / 'r206_ready/runtime_overlay.tar.gz') as archive:
        members = archive.getmembers()
        require(len(members) == len(ready['files']) == 42 and all(member.isfile() and member.name in ready['files'] for member in members), 'declared_regular_R206_source')
        archive.extractall(source, filter='data')
    require(all(sha(source / name) == expected for name, expected in ready['files'].items()), 'exact_released_files_before_arm_binding')
    driver = source / 'gpu/orch_r184_think_act_learn.py'
    driver.write_text(executor_patch(driver.read_text(), previous_driver, old_plan['think_act_learn']['trial_id']))
    if arm == 'repo_c1':
        text = driver.read_text()
        marker = "        if route == 'CPU':\n"
        require(text.count(marker) == 1, 'unique_repo_route_binding')
        hook = "        if self.config['trial_id'] == 'R202_REPO_C_node2_clone1':\n            from research_loop.workers.rohin183_repo_learning_20260917.tools import request\n            try:\n                action = request(raw_act)\n            except (ValueError, TypeError):\n                route = 'REPO'\n            else:\n                if action is not None:\n                    route = 'REPO'\n"
        text = text.replace(marker, hook + "        if route in ('CPU', 'REPO'):\n", 1)
        ast.parse(text)
        driver.write_text(text)
    confinement = source / 'gpu/r184_node2_confinement.py'
    text, count = re.subn("unit='[^']+'\\+mode", "unit='orch-r206-" + arm.replace('_', '-') + '-' + ATTEMPT.replace('_', '-') + "-'+mode", confinement.read_text())
    require(count == 1, 'single_private_confinement_unit_namespace')
    ast.parse(text)
    confinement.write_text(text)
    control = output / 'control'
    control.mkdir()
    plan = dict(old_plan, source_root=str(source), max_sleeps=69)
    if plan.get('startup_context'):
        plan['startup_context'] = dict(plan['startup_context'], path=str(source / Path(plan['startup_context']['path']).relative_to(old_plan['source_root'])))
    plan['think_act_learn'] = dict(old_plan['think_act_learn'], **ready['required_driver_options'])
    require(all(plan.get(key) == value for key, value in ready['required_native_options'].items()), 'unchanged_fixed_native_dose')
    write(control / 'PLAN.json', plan)
    checks = subprocess.run([PYTHON, '-B', str(Path(__file__).resolve()), 'cpu', '--arm', arm, '--attempt', ATTEMPT], cwd=source,
        env=environment(source), capture_output=True, text=True, timeout=80)
    (output / 'CPU.log').write_text(checks.stdout + checks.stderr)
    require(checks.returncode == 0, 'receiving_CPU:' + checks.stderr[-1000:])
    pins = {str(path.relative_to(source)): sha(path) for path in source.rglob('*.py')}
    write(control / 'RECEIVING_CPU.json', dict(passed=True, source_pins=pins, Main_archive_sha256=ARCHIVE,
        observed_unix=time.time(), log_sha256=sha(output / 'CPU.log')))
    allocation = dict(read(old / 'ALLOCATION.json'), plan_sha256=sha(control / 'PLAN.json'), cpu_tests_passed=True,
        cpu_receipt_path=str(control / 'RECEIVING_CPU.json'), cpu_receipt_sha256=sha(control / 'RECEIVING_CPU.json'),
        declared_unix=time.time(), builder_entry_logged=True)
    write(control / 'ALLOCATION.json', allocation)
    guard = dict(read(old / 'GUARD.json'), source_pins=pins, resume=True, copy_raw=str(root / 'raw'), attempt_dir=str(control),
        plan_path=str(control / 'PLAN.json'), plan_sha256=sha(control / 'PLAN.json'),
        allocation_path=str(control / 'ALLOCATION.json'), allocation_sha256=sha(control / 'ALLOCATION.json'))
    write(control / 'GUARD.json', guard)
    validation = subprocess.run([PYTHON, '-B', '-c', 'from gpu.orch_r125_continual_guard import validate; import sys; validate(sys.argv[1])', str(control / 'GUARD.json')],
        cwd=source, env=environment(source), capture_output=True, text=True, timeout=45)
    require(validation.returncode == 0, 'guard_validation:' + validation.stderr[-800:])
    write(output / 'READY.json', dict(status='CPU_READY_NOT_LIVE', archive_sha256=ARCHIVE,
        previous_control=str(old), guard_sha256=sha(control / 'GUARD.json'), source_pins=pins,
        phase='PHASE2_R206_LONGER_PARENT_WITHDRAWN_NO_PEER', cycles=list(range(58, 70)),
        no_new_parent_publication=True, no_first_input_replay=True, no_birth_or_dose_reset=True))
    print(json.dumps(dict(arm=arm, status='CPU_READY_NOT_LIVE')))


def cpu(arm):
    output = BASE / arm / ATTEMPT
    source = output / 'source'
    sys.path.insert(0, str(source))
    from gpu.orch_r125_continual_native import validate_plan
    from gpu.orch_r184_think_act_learn import ThinkActLearn
    from unittest.mock import patch
    plan = read(output / 'control/PLAN.json')
    validate_plan(plan)
    probe = object.__new__(ThinkActLearn)
    probe.config = plan['think_act_learn']
    if arm == 'creative_d1':
        require(probe._cpu({})['executed'] is False, 'creative_executor_stays_absent')
    else:
        with patch('gpu.r184_cpu_bridge.call', return_value={'synthetic_cpu_fixture': True}) as mocked:
            require(probe._cpu({}) == {'synthetic_cpu_fixture': True} and mocked.call_count == 1, 'existing_math_transport_preserved')
    print(json.dumps(dict(passed=True, arm=arm, CUDA_initialized=False, target_or_parent_rows_created=0)))


def restore(arm):
    output = BASE / arm / ATTEMPT
    plan = read(output / 'control/PLAN.json')
    sys.path.insert(0, plan['source_root'])
    import torch
    from gpu.orch_r125_continual_native import NativeChild
    from organism_v6.orch_r125_continual_stream import ContinualStream
    boundary = read(output / 'BOUNDARY.json')
    require(Path(plan['root']).stat().st_ino == (BASE / arm / 'raw').stat().st_ino, 'private_clone_bind_not_original_C2')
    envelope = boundary['record']['document']['resume_state']
    state = ContinualStream.restore(envelope, expected_sha256=envelope['sha256'])
    require(state.pending is None and state.sleep_frontier == len(state.rows), 'complete_stream_restore')
    checkpoint = boundary['record']['document']['checkpoint']
    NativeChild.verify_checkpoint(checkpoint)
    payload = torch.load(checkpoint['optimizer_rng_path'], map_location='cpu', weights_only=False)
    require(payload['optimizer_steps'] == checkpoint['optimizer_steps'] and not torch.cuda.is_initialized(), 'exact_CPU_optimizer_restore')
    print(json.dumps(dict(passed=True, cycle=57, optimizer_steps=checkpoint['optimizer_steps'], state_sha256=envelope['sha256'])))


def dispatch(arm):
    root = BASE / arm
    output = root / ATTEMPT
    source = output / 'source'
    control = output / 'control'
    old = old_control(root, arm)
    require(not (output / 'DISPATCH_ATTEMPT.json').exists(), 'one_dispatch_attempt_only')
    require(read(old / 'EXIT.json')['exit_code'] == read(old / 'OUTER_EXIT.json')['status'] == 0, 'prior_native_and_outer_exited_normally')
    no_owner(old)
    withdrawal = list((root / 'parent_receipts').glob('WITHDRAWN*.json'))
    require(withdrawal and all(read(path).get('no_future_parent_publications') for path in withdrawal), 'actual_parent_withdrawal_receipt')
    boundary = terminal_boundary(root / 'raw')
    write(output / 'DISPATCH_ATTEMPT.json', dict(started_unix=time.time(), no_automatic_retry=True, signals=0))
    write(output / 'BOUNDARY.json', boundary)
    preserved = output / 'preserved'
    preserved.mkdir()
    for relative in ['stream', 'checkpoints/sleep_000057']:
        destination = preserved / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(['cp', '-a', '--reflink=auto', str(root / 'raw' / relative), str(destination)], check=True, timeout=60)
    specification = importlib.util.spec_from_file_location('phase2_confinement', source / 'gpu/r184_node2_confinement.py')
    module = importlib.util.module_from_spec(specification)
    sys.path.insert(0, str(source))
    specification.loader.exec_module(module)
    command = module.command(control / 'GUARD.json', 'probe')
    command = [value + '-restore' if value.startswith('--unit=') else value for value in command]
    command = command[:command.index('-m')] + [str(Path(__file__).resolve()), 'restore', '--arm', arm, '--attempt', ATTEMPT]
    checked = subprocess.run(command, capture_output=True, text=True, timeout=60)
    (output / 'RESTORE_CPU.log').write_text(checked.stdout + checked.stderr)
    require(checked.returncode == 0, 'private_bind_CPU_restore:' + checked.stderr[-1000:])
    require(terminal_boundary(root / 'raw')['terminal'] == boundary['terminal'], 'preserved_terminal_still_current')
    processes = {}
    def start(name, arguments):
        with (output / (name + '.log')).open('x') as log:
            process = subprocess.Popen(arguments, cwd=source, env=environment(source), stdout=log, stderr=subprocess.STDOUT,
                stdin=subprocess.DEVNULL, start_new_session=True)
        processes[name] = saved.identity(process.pid)
    if arm != 'creative_d1':
        previous_bridge = old.parent / 'BRIDGE.json' if arm == 'repo_c1' else root / 'BRIDGE.json'
        bridge = dict(read(previous_bridge), native_source=str(source), guard_path=str(control / 'GUARD.json'),
            guard_sha256=sha(control / 'GUARD.json'), socket='/tmp/r206_' + arm + '_' + ATTEMPT + '.sock', stop_unix=read(control / 'PLAN.json')['hard_end_unix'])
        write(output / 'BRIDGE.json', bridge)
        start('bridge', [PYTHON, '-B', str(source / 'gpu/r184_cpu_bridge.py'), '--config', str(output / 'BRIDGE.json')])
        deadline = time.monotonic() + 18
        while time.monotonic() < deadline and not list((output / 'bridge_receipts').glob('READY_*.json')):
            time.sleep(0.1)
        require(list((output / 'bridge_receipts').glob('READY_*.json')), 'actual_bound_bridge_READY')
    no_owner(old)
    start('supervisor', [PYTHON, '-B', '-m', 'gpu.r184_node2_confinement', 'dispatch', '--config', str(control / 'GUARD.json')])
    write(output / 'DISPATCHED.json', dict(status='DISPATCHED_NOT_LOADED_PROOF', processes=processes, dispatched_unix=time.time(),
        preserved_complete=57, phase2_cycles=list(range(58, 70)), original_C2_signals=0, parent_publications=0, peer_messages=0))
    print(json.dumps(dict(arm=arm, status='DISPATCHED_NOT_LOADED_PROOF', processes=processes)))


def wait(arm):
    root = BASE / arm
    output = root / ATTEMPT
    control = old_control(root, arm)
    write(output / 'WAITER_STARTED.json', dict(actor=saved.identity(os.getpid()), started_unix=time.time(),
        maximum_seconds=1200, no_signals=True, only_normal_screen57=True, retries=0))
    deadline = time.monotonic() + 1200
    try:
        while time.monotonic() < deadline:
            if (control / 'EXIT.json').exists() and (control / 'OUTER_EXIT.json').exists():
                dispatch(arm)
                return
            time.sleep(2)
        write(output / 'WAIT_EXPIRED.json', dict(observed_unix=time.time(), signals=0, launches=0))
    except BaseException as error:
        write(output / 'PHASE2_FAILED.json', dict(observed_unix=time.time(), error_type=type(error).__name__, reason=str(error), no_retry=True))
        raise


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('mode', choices=['stage', 'cpu', 'restore', 'dispatch', 'wait'])
    parser.add_argument('--arm', choices=ARMS, required=True)
    parser.add_argument('--attempt', choices=['r206_phase2_withdrawn_20260918', 'r209_dispatch_recovery_20260918'], default=ATTEMPT)
    arguments = parser.parse_args()
    ATTEMPT = arguments.attempt
    globals()[arguments.mode](arguments.arm)
