"""R210 adapter of the existing R204 NODE2 saved-boundary operator."""

import argparse
import ast
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import select
import shutil
import signal
import subprocess
import sys
import tarfile
import time

import enrich
import r206_phase2 as phase
import saved_primitives as saved
from memory_handoff import complete_boundary

HERE = Path(__file__).resolve().parent
BASE = phase.BASE
PYTHON = phase.PYTHON
ARCHIVE = 'ccd62dbb0483240c23ac5caddc23cf5e7ee4a54b45e6896e49267f5f2efd60ec'
ATTEMPT = 'r210_filter_saved_boundary_20260918_v3'
MANIFEST = enrich.read(HERE / 'BEFORE_CURRENT.json')['arms']
TARGETS = {arm: (BASE / arm, 'raw', MANIFEST[arm]['native']['pid'], MANIFEST[arm]['native']['start_ticks'])
           for arm in enrich.ARMS}
read, write, sha, require = saved.read, saved.write, saved.sha, saved.require


def environment(source):
    return phase.environment(source)


def restore_stream(restore_function, document):
    return restore_function(document, expected_sha256=document['sha256'])


def old_control(arm):
    return Path(MANIFEST[arm]['current_control'])


def stage(arm):
    bound, root = enrich.identity(arm)
    old = old_control(arm)
    actor = saved.identity(bound['native']['pid'])
    output = root / ATTEMPT
    require(not output.exists(), 'new_handoff_identity_only')
    output.mkdir()
    source = output / 'source'
    shutil.copytree(bound['source_root'], source, ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
    previous_driver = (source / 'gpu/orch_r184_think_act_learn.py').read_text()
    ready = read(HERE / 'r209_ready/READY.json')
    archive_path = HERE / 'r209_ready/runtime_overlay.tar.gz'
    require(sha(archive_path) == ready['archive_sha256'] == ARCHIVE, 'exact_Descartes_R209_bundle')
    with tarfile.open(archive_path) as archive:
        members = archive.getmembers()
        require(len(members) == len(ready['files']) == 42 and all(member.isfile()
            and member.name in ready['files'] and '..' not in Path(member.name).parts
            and not Path(member.name).is_absolute() for member in members), 'exact_declared_overlay')
        archive.extractall(source, filter='data')
    require(all(sha(source / name) == value for name, value in ready['files'].items()), 'all42_overlay_hashes')
    regression = read(HERE / 'r209_ready/SHARED_TEST_RECEIPT.json')
    require(regression['passed'] and regression['tests_run'] == 62, 'author_companion_regression_receipt')
    for name, expected in regression['test_files'].items():
        require(name in ('tests/test_orch_r184_think_act_learn.py', 'tests/test_orch_r203_prose_target_filter.py')
            and sha(HERE / 'r209_ready/regression_tests' / name) == expected, 'exact_companion_regression_bytes')
        shutil.copy2(HERE / 'r209_ready/regression_tests' / name, source / name)
    old_plan = read(old / 'PLAN.json')
    driver = source / 'gpu/orch_r184_think_act_learn.py'
    driver.write_text(phase.executor_patch(driver.read_text(), previous_driver, old_plan['think_act_learn']['trial_id']))
    if arm == 'repo_c1':
        text = driver.read_text()
        marker = "        if route == 'CPU':\n"
        hook = "        if self.config['trial_id'] == 'R202_REPO_C_node2_clone1':\n            from research_loop.workers.rohin183_repo_learning_20260917.tools import request\n            try:\n                action = request(raw_act)\n            except (ValueError, TypeError):\n                route = 'REPO'\n            else:\n                if action is not None:\n                    route = 'REPO'\n"
        require(text.count(marker) == 1, 'unique_existing_repo_route')
        text = text.replace(marker, hook + "        if route in ('CPU', 'REPO'):\n", 1)
        ast.parse(text)
        driver.write_text(text)
    confinement = source / 'gpu/r184_node2_confinement.py'
    text, count = re.subn(r"unit='[^']+'\+mode", "unit='orch-r210-" + arm.replace('_', '-') + "-filter3-'+mode", confinement.read_text())
    require(count == 1, 'unique_private_confinement_namespace')
    ast.parse(text)
    confinement.write_text(text)
    control = output / 'control'
    control.mkdir()
    plan = dict(old_plan, source_root=str(source))
    if plan.get('startup_context'):
        plan['startup_context'] = dict(plan['startup_context'], path=str(source / Path(plan['startup_context']['path']).relative_to(old_plan['source_root'])))
    plan['think_act_learn'] = dict(old_plan['think_act_learn'], **ready['required_driver_options'])
    require(all(plan.get(key) == value for key, value in ready['required_native_options'].items()), 'native_prerequisites_unchanged')
    require({key: value for key, value in plan.items() if key not in ('source_root', 'startup_context', 'think_act_learn')}
        == {key: value for key, value in old_plan.items() if key not in ('source_root', 'startup_context', 'think_act_learn')}, 'dose_wall_gpu_budget_preserved')
    write(control / 'PLAN.json', plan)
    checked = subprocess.run([PYTHON, '-B', str(Path(__file__).resolve()), 'cpu', '--arm', arm], cwd=source,
        env=environment(source), capture_output=True, text=True, timeout=120)
    (output / 'CPU.log').write_text(checked.stdout + checked.stderr)
    require(checked.returncode == 0, 'receiving_CPU:' + checked.stderr[-1200:])
    pins = {str(path.relative_to(source)): sha(path) for path in source.rglob('*.py')}
    write(control / 'RECEIVING_CPU.json', dict(passed=True, source_pins=pins, archive_sha256=ARCHIVE,
        observed_unix=time.time(), log_sha256=sha(output / 'CPU.log'), phase='R210_PARENTED_ENRICHMENT', model_calls=0))
    allocation = dict(read(old / 'ALLOCATION.json'), plan_sha256=sha(control / 'PLAN.json'), cpu_tests_passed=True,
        cpu_receipt_path=str(control / 'RECEIVING_CPU.json'), cpu_receipt_sha256=sha(control / 'RECEIVING_CPU.json'),
        declared_unix=time.time(), builder_entry_logged=True)
    write(control / 'ALLOCATION.json', allocation)
    guard = dict(read(old / 'GUARD.json'), source_pins=pins, resume=True, copy_raw=str(root / 'raw'),
        attempt_dir=str(control), plan_path=str(control / 'PLAN.json'), plan_sha256=sha(control / 'PLAN.json'),
        allocation_path=str(control / 'ALLOCATION.json'), allocation_sha256=sha(control / 'ALLOCATION.json'))
    write(control / 'GUARD.json', guard)
    checked = subprocess.run([PYTHON, '-B', '-c', 'from gpu.orch_r125_continual_guard import validate; import sys; validate(sys.argv[1])', str(control / 'GUARD.json')],
        cwd=source, env=environment(source), capture_output=True, text=True, timeout=45)
    require(checked.returncode == 0, 'guard_validation:' + checked.stderr[-1200:])
    bridge = None
    if arm != 'creative_d1':
        old_bridge = read(old.parent / 'DISPATCHED.json')['processes']['bridge']
        bridge = saved.identity(old_bridge['pid'])
        require(bridge['start_ticks'] == old_bridge['start_ticks'] and bridge['argv'][-1] == str(old.parent / 'BRIDGE.json'), 'exact_current_bridge')
    write(output / 'READY.json', dict(actor=actor, bridge=bridge, source_pins=pins,
        old_control=str(old), old_guard_sha256=sha(old / 'GUARD.json'), new_guard_sha256=sha(control / 'GUARD.json'),
        observed_unix=time.time(), phase='R210_PARENTED_ENRICHMENT', status='CPU_READY_NOT_LIVE',
        raw_unchanged=True, prior_updates_not_undone=True, max_sleeps=plan['max_sleeps'], recipe_preserved=True))
    print(json.dumps(dict(arm=arm, status='CPU_READY_NOT_LIVE', ready=str(output / 'READY.json'))))


def cpu(arm):
    output = BASE / arm / ATTEMPT
    source = output / 'source'
    sys.path.insert(0, str(source))
    from gpu.orch_r125_continual_native import validate_plan
    from gpu.orch_r184_think_act_learn import ThinkActLearn
    from organism_v6.orch_r124_train_history import TrainEvent
    from organism_v6.orch_r125_plain_context import event_message
    from organism_v6 import orch_r203_prose_target_filter as prose
    from unittest.mock import patch
    plan = read(output / 'control/PLAN.json')
    validate_plan(plan)
    require(plan['think_act_learn']['prose_target_filter'] == prose.POLICY == 'R209_ENGLISH_PROSE_TARGET_QUARANTINE_V1', 'new_English_child_policy')
    probe = object.__new__(ThinkActLearn)
    probe.config = plan['think_act_learn']
    if arm == 'creative_d1':
        require(probe._cpu({})['executed'] is False, 'creative_executor_remains_absent')
    else:
        with patch('gpu.r184_cpu_bridge.call', return_value={'synthetic': True}) as mocked:
            require(probe._cpu({}) == {'synthetic': True} and mocked.call_count == 1, 'existing_arm_bridge')
    tool = dict(schema='R183_ACTUAL_TOOL_RESULT_V1', status='COMPLETE', action='read',
        origin=dict(actor='child', split='TRAIN'), source_sha256='b' * 64, content='synthetic fixture')
    event = TrainEvent(event_id='receiving:tool', episode_id='receiving', source_id='receiving', source_sha256='a' * 64,
        actor='environment', phase='feedback', text='Tool: ' + json.dumps(tool), split='TRAIN', origin='TRAIN_COLLECTION')
    require(event_message(event) == dict(role='user', content=event.text), 'real_tool_visibility_preserved')
    checked = subprocess.run([PYTHON, '-B', '-m', 'unittest', 'tests.test_orch_r184_think_act_learn',
        'tests.test_orch_r203_prose_target_filter'], cwd=source, env=environment(source), capture_output=True, text=True, timeout=90)
    print(checked.stdout + checked.stderr)
    require(checked.returncode == 0, 'released_R209_regressions')
    print(json.dumps(dict(arm=arm, passed=True, model_calls=0, actual_target_created=False)))


def candidate(raw):
    paths = sorted((raw / 'stream/records').glob('[0-9]' * 20 + '.json'))
    with paths[-1].open('rb') as stream:
        stream.seek(max(0, paths[-1].stat().st_size - 4096))
        tail = stream.read()
    metadata = json.loads(b'{' + tail[tail.rfind(b',"index":') + 1:])
    return complete_boundary(raw) if metadata['kind'] in ('SLEEP_COMPLETE', 'R184_LEARN_COMPLETE') else None


def restore(arm):
    root, raw_name, unused_pid, unused_ticks = TARGETS[arm]
    output = root / ATTEMPT
    plan = read(output / 'control/PLAN.json')
    sys.path.insert(0, plan['source_root'])
    import torch
    from gpu.orch_r125_continual_native import NativeChild
    from organism_v6.orch_r125_continual_stream import ContinualStream
    boundary_path = output / 'BOUNDARY.json'
    if not boundary_path.exists():
        raise ValueError('actual_new_boundary_required')
    boundary = read(boundary_path)
    logical = Path(plan['root'])
    require(logical.stat().st_ino == (root / raw_name).stat().st_ino, 'actual_private_life_binding')
    state = boundary['record']['document']['resume_state']
    stream = restore_stream(ContinualStream.restore, state)
    require(stream.pending is None and stream.sleep_frontier == len(stream.rows), 'exact_COMPLETE_stream_restore')
    checkpoint = boundary['record']['document']['checkpoint']
    NativeChild.verify_checkpoint(checkpoint)
    payload = torch.load(checkpoint['optimizer_rng_path'], map_location='cpu', weights_only=False)
    require(payload['optimizer_steps'] == checkpoint['optimizer_steps'] and not torch.cuda.is_initialized(), 'checkpoint_optimizer_CPU_exact')
    print(json.dumps(dict(passed=True, cycle=boundary['cycle'], optimizer_steps=payload['optimizer_steps'], state_sha256=state['sha256'], cuda_initialized=False)))


def handoff(arm, seconds):
    raise ValueError('R212_NO_PAUSES_HANDOFF_DISABLED_USE_NATURAL_COMPLETED_SCREEN_ONLY')
    root, raw_name, unused_pid, unused_ticks = TARGETS[arm]
    raw = root / raw_name
    output = root / ATTEMPT
    ready = read(output / 'READY.json')
    actor = ready['actor']
    old = old_control(arm)
    require(sha(old / 'GUARD.json') == ready['old_guard_sha256'], 'old_guard_unchanged')
    lock = os.open(output / 'OPERATOR.lock', os.O_CREAT | os.O_EXCL | os.O_RDWR, 0o600)
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    write(output / 'ARMED.json', dict(pid=os.getpid(), started_unix=time.time(), seconds=seconds, signals=0))
    descriptor = os.pidfd_open(actor['pid'])
    deadline = time.monotonic() + seconds
    stopped = False
    try:
        while time.monotonic() < deadline:
            saved.same(actor)
            boundary = candidate(raw)
            if boundary is None:
                time.sleep(0.2)
                continue
            with saved.pause_watchdog(descriptor, 240) as pause_end:
                saved.pause_exact(actor, descriptor)
                frozen = candidate(raw)
                if frozen is None or frozen['head'] != boundary['head']:
                    continue
                checkpoint = boundary['record']['document']['checkpoint']
                readout = None
                for directory in (raw / 'readouts').glob('sleep_' + f'{boundary["cycle"]:06d}' + '*'):
                    if not directory.is_dir() or not (directory / 'REQUEST.json').exists():
                        continue
                    request = read(directory / 'REQUEST.json')
                    if request.get('optimizer_steps') == checkpoint['optimizer_steps']:
                        readout = directory
                        break
                if readout is None:
                    continue
                while time.monotonic() < pause_end - 60:
                    if (readout / 'COMPLETE.json').exists() and not saved.live_children(actor['pid']):
                        require(read(readout / 'COMPLETE.json')['status'] == 'COMPLETE', 'independent_readout_complete')
                        break
                    time.sleep(0.2)
                require(not saved.live_children(actor['pid']) and (readout / 'COMPLETE.json').exists(), 'readout_finished_before_retire')
                require(candidate(raw)['head'] == frozen['head'], 'same_head_after_readout')
                write(output / 'BOUNDARY.json', boundary)
                preserve = output / 'preserved'
                preserve.mkdir()
                for name in ['stream', 'checkpoints/' + f'sleep_{boundary["cycle"]:06d}']:
                    destination = preserve / name
                    destination.parent.mkdir(parents=True, exist_ok=True)
                    subprocess.run(['cp', '-a', '--reflink=auto', str(raw / name), str(destination)], check=True, timeout=45)
                shutil.copy2(readout / 'REQUEST.json', preserve / 'READOUT_REQUEST.json')
                shutil.copy2(readout / 'COMPLETE.json', preserve / 'READOUT_COMPLETE.json')
                from importlib.util import spec_from_file_location, module_from_spec
                specification = spec_from_file_location('owned_confinement', output / 'source/gpu/r184_node2_confinement.py')
                module = module_from_spec(specification)
                sys.path.insert(0, str(output / 'source'))
                specification.loader.exec_module(module)
                command = module.command(output / 'control/GUARD.json', 'probe')
                command[command.index('--unit=' + next(value.split('=', 1)[1] for value in command if value.startswith('--unit=')))] += '-restore'
                marker = command.index('-m')
                command = command[:marker] + [str(Path(__file__).resolve()), 'restore', '--arm', arm]
                checked = subprocess.run(command, capture_output=True, text=True, timeout=40)
                (output / 'RESTORE_CPU.log').write_text(checked.stdout + checked.stderr)
                require(checked.returncode == 0, 'actual_CPU_restore:' + checked.stderr[-600:])
                require(candidate(raw)['head'] == frozen['head'], 'same_checkpoint_after_preservation_restore')
                saved.same(actor)
                signal.pidfd_send_signal(descriptor, signal.SIGTERM)
                signal.pidfd_send_signal(descriptor, signal.SIGCONT)
                require(bool(select.select([descriptor], [], [], 20)[0]), 'exact_native_exited')
                stopped = True
                write(output / 'RETIRED_EXACT.json', dict(actor=actor, boundary_cycle=boundary['cycle'], retired_unix=time.time(), group_signals=0, original_C2_signals=0))
                break
        require(stopped, 'finite_boundary_not_observed_no_restart')
        finish = time.monotonic() + 25
        while time.monotonic() < finish and not (old / 'OUTER_EXIT.json').exists():
            time.sleep(0.2)
        require((old / 'OUTER_EXIT.json').exists(), 'old_outer_exited')
        if arm != 'creative_d1':
            old_start = ready['bridge']
            try:
                bridge_identity = saved.identity(old_start['pid'])
            except FileNotFoundError:
                bridge_identity = None
            if bridge_identity is not None:
                require(bridge_identity['start_ticks'] == old_start['start_ticks']
                    and bridge_identity['argv'][-1] == str(old.parent / 'BRIDGE.json'), 'exact_idle_old_bridge')
                bridge_descriptor = os.pidfd_open(bridge_identity['pid'])
                try:
                    saved.same(bridge_identity)
                    signal.pidfd_send_signal(bridge_descriptor, signal.SIGTERM)
                    require(bool(select.select([bridge_descriptor], [], [], 10)[0]), 'idle_bridge_exit')
                finally:
                    os.close(bridge_descriptor)
            bridge = read(old.parent / 'BRIDGE.json')
            bridge.update(native_source=str(output / 'source'), guard_path=str(output / 'control/GUARD.json'),
                guard_sha256=sha(output / 'control/GUARD.json'), socket='/tmp/r210_' + arm + '_filter.sock')
            write(output / 'BRIDGE.json', bridge)
            with (output / 'bridge.log').open('x') as log:
                process = subprocess.Popen([PYTHON, '-B', str(output / 'source/gpu/r184_cpu_bridge.py'), '--config', str(output / 'BRIDGE.json')],
                    cwd=output / 'source', env=environment(output / 'source'), stdout=log, stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL, start_new_session=True)
            write(output / 'BRIDGE_STARTED.json', saved.identity(process.pid))
            wait = time.monotonic() + 15
            while time.monotonic() < wait and not list((output / 'bridge_receipts').glob('READY_*.json')):
                time.sleep(0.1)
            require(list((output / 'bridge_receipts').glob('READY_*.json')), 'new_bridge_READY')
        with (output / 'supervisor.log').open('x') as log:
            process = subprocess.Popen([PYTHON, '-B', '-m', 'gpu.r184_node2_confinement', 'dispatch', '--config', str(output / 'control/GUARD.json')],
                cwd=output / 'source', env=environment(output / 'source'), stdout=log, stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL, start_new_session=True)
        write(output / 'DISPATCHED.json', dict(supervisor=saved.identity(process.pid), boundary_cycle=boundary['cycle'],
            checkpoint_optimizer_steps=checkpoint['optimizer_steps'], new_guard_sha256=sha(output / 'control/GUARD.json'), dispatched_unix=time.time(), not_LOADED_proof=True))
    except BaseException as error:
        write(output / 'HANDOFF_FAILED.json', dict(error_type=type(error).__name__, reason=str(error), old_native_retired=stopped, observed_unix=time.time(), no_retry=True))
        raise
    finally:
        os.close(descriptor)
        os.close(lock)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('mode', choices=['stage', 'cpu', 'restore', 'handoff'])
    parser.add_argument('--arm', choices=TARGETS, required=True)
    parser.add_argument('--seconds', type=int, default=1200)
    arguments = parser.parse_args()
    if arguments.mode == 'handoff':
        raise ValueError('R212_NO_PAUSES_HANDOFF_DISABLED_USE_NATURAL_COMPLETED_SCREEN_ONLY')
    else:
        globals()[arguments.mode](arguments.arm)
