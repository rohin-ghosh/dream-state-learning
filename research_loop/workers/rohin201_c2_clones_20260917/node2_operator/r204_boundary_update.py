"""Owned node2 COMPLETE-boundary repair; preserve state, never replay birth."""

import argparse
import ast
import fcntl
import hashlib
import json
import os
from pathlib import Path
import select
import shutil
import signal
import subprocess
import sys
import tarfile
import time

import saved_primitives as saved
from memory_handoff import complete_boundary


BASE = Path('/localhome/local-rohing/orch_r153_r201_node2_clones_20260917_operator1')
PYTHON = '/localhome/local-rohing/v2/venv/bin/python'
ARCHIVE = 'b0f148c92172af9d1525fda79a97bebfb31337e312e26c0f6bc805b3c687f8fc'
ATTEMPT = 'r204_boundary_20260918t0356z'
TARGETS = {
    'repo_c1': (BASE / 'repo_c1', 'raw', 2170067, '92935338'),
    'birth1': (Path('/localhome/local-rohing/orch_r183_repo_learning_20260917/birth1'), 'life', 1815204, '91233592'),
}
read, write, sha, require = saved.read, saved.write, saved.sha, saved.require


def environment(source):
    return dict(PATH='/usr/bin:/bin', HOME=str(source.parent), TMPDIR='/tmp', CUDA_VISIBLE_DEVICES='',
        PYTHONPATH=str(source), PYTHONDONTWRITEBYTECODE='1', HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1',
        OMP_NUM_THREADS='1', MKL_NUM_THREADS='1', TOKENIZERS_PARALLELISM='false')


def replace_once(text, original, replacement):
    require(text.count(original) == 1, 'unique_source_anchor:' + original[:80])
    return text.replace(original, replacement, 1)


def sequence_start(directory):
    return max((int(path.stem.split('_')[1]) for path in Path(directory).glob('ACTION_*.json')), default=-1) + 1


def restore_stream(restore_function, document):
    return restore_function(document, expected_sha256=document['sha256'])


def stage(arm):
    root, raw_name, native_pid, start_ticks = TARGETS[arm]
    old = root / 'control'
    output = root / ATTEMPT
    require(not output.exists(), 'new_handoff_identity_only')
    actor = saved.identity(native_pid)
    require(actor['start_ticks'] == start_ticks and actor['cwd'] == str(root / 'source')
        and actor['argv'][-3:] == ['native', '--config', str(old / 'GUARD.json')], 'exact_owned_old_native')
    output.mkdir()
    source = output / 'source'
    shutil.copytree(root / 'source', source)
    ready = read(BASE / 'r204_ready/READY.json')
    require(sha(BASE / 'r204_ready/runtime_overlay.tar.gz') == ready['archive_sha256'] == ARCHIVE, 'frozen_Main_R204')
    with tarfile.open(BASE / 'r204_ready/runtime_overlay.tar.gz') as archive:
        chosen = list(ready['files']) if arm == 'repo_c1' else ['organism_v6/orch_r125_plain_context.py', 'tests/test_orch_r125_plain_context.py']
        members = [archive.getmember(name) for name in chosen]
        require(all(member.isfile() for member in members), 'only_declared_regular_overlay_files')
        archive.extractall(source, members=members, filter='data')
    require(all(sha(source / name) == ready['files'][name] for name in chosen), 'exact_frozen_overlay_bytes')
    containment = (BASE / 'repo_c1/source/gpu/r184_node2_confinement.py').read_text()
    containment = replace_once(containment, "'orch-r202-repo-c1-'", repr('orch-r204-' + arm.replace('_', '-') + '-boundary-'))
    if arm == 'birth1':
        containment = containment.replace('GPU-c9450d3d-0455-f034-b9bf-7f8956e44733', 'GPU-d2db2a6a-a308-1782-bf41-e41411d8dc05')
        containment = replace_once(containment, 'MINOR=3', 'MINOR=2').replace('/dev/nvidia3', '/dev/nvidia2')
        containment = containment.replace('0000:57:00.0', '0000:56:00.0')
        containment = replace_once(containment, '[0, 1, 2, 4, 5, 6, 7]', '[0, 1, 3, 4, 5, 6, 7]')
        containment = replace_once(containment, "    properties['BindPaths']=config['copy_raw']+':'+plan['root']\n", '')
    ast.parse(containment)
    (source / 'gpu/r184_node2_confinement.py').write_text(containment)
    if arm == 'repo_c1':
        driver = source / 'gpu/orch_r184_think_act_learn.py'
        text = driver.read_text()
        text = replace_once(text, '    def _cpu(self, origin):\n',
            "    def _cpu(self, origin):\n        if self.config['trial_id'] == 'R202_REPO_C_node2_clone1':\n            from gpu.r184_cpu_bridge import call\n            return call(self.config, origin)\n")
        hook = "        if self.config['trial_id'] == 'R202_REPO_C_node2_clone1':\n            from research_loop.workers.rohin183_repo_learning_20260917.tools import request\n            try:\n                action = request(raw_act)\n            except (ValueError, TypeError):\n                route = 'REPO'\n            else:\n                if action is not None:\n                    route = 'REPO'\n"
        text = replace_once(text, "        if route == 'CPU':\n", hook + "        if route in ('CPU', 'REPO'):\n")
        ast.parse(text)
        driver.write_text(text)
        bridge = (root / 'repo_bridge.py').read_text() if (root / 'repo_bridge.py').exists() else (root / 'repo_c_bridge.py').read_text()
        bridge = replace_once(bridge, '    sequence = 0\n', "    sequence = max((int(item.stem.split('_')[1]) for item in Path(settings['receipts']).glob('ACTION_*.json')), default=-1) + 1\n")
        (output / 'repo_bridge.py').write_text(bridge)
        (source / 'gpu/r184_cpu_bridge.py').write_text(bridge)
    control = output / 'control'
    control.mkdir()
    plan = read(old / 'PLAN.json')
    plan['source_root'] = str(source)
    if plan.get('startup_context'):
        plan['startup_context']['path'] = str(source / Path(plan['startup_context']['path']).relative_to(root / 'source'))
    if arm == 'repo_c1':
        plan['think_act_learn'].update(ready['required_driver_options'])
    write(control / 'PLAN.json', plan)
    old_guard = read(old / 'GUARD.json')
    pins = {str(path.relative_to(source)): sha(path) for path in source.rglob('*.py')}
    checks = subprocess.run([PYTHON, '-B', str(Path(__file__).resolve()), 'cpu', '--arm', arm],
        cwd=source, env=environment(source), capture_output=True, text=True, timeout=100)
    (output / 'CPU.log').write_text(checks.stdout + checks.stderr)
    require(checks.returncode == 0, 'focused_receiving_CPU_PASS:' + checks.stderr[-1000:])
    cpu = dict(passed=True, source_pins=pins, observed_unix=time.time(), Main_archive_sha256=ARCHIVE,
        log_sha256=sha(output / 'CPU.log'), regression='real Tool rendering; no target creation; exact route; continuation checks; sequence resume')
    write(control / 'RECEIVING_CPU.json', cpu)
    allocation = read(old / 'ALLOCATION.json')
    allocation.update(plan_sha256=sha(control / 'PLAN.json'), cpu_tests_passed=True,
        cpu_receipt_path=str(control / 'RECEIVING_CPU.json'), cpu_receipt_sha256=sha(control / 'RECEIVING_CPU.json'),
        declared_unix=time.time(), builder_entry_logged=True)
    write(control / 'ALLOCATION.json', allocation)
    config = dict(old_guard, source_pins=pins, resume=True, copy_raw=str(root / raw_name),
        attempt_dir=str(control), plan_path=str(control / 'PLAN.json'), plan_sha256=sha(control / 'PLAN.json'),
        allocation_path=str(control / 'ALLOCATION.json'), allocation_sha256=sha(control / 'ALLOCATION.json'))
    write(control / 'GUARD.json', config)
    validation = subprocess.run([PYTHON, '-B', '-c', 'from gpu.orch_r125_continual_guard import validate; import sys; validate(sys.argv[1])', str(control / 'GUARD.json')],
        cwd=source, env=environment(source), capture_output=True, text=True, timeout=45)
    require(validation.returncode == 0, 'guard_validation:' + validation.stderr[-1000:])
    write(output / 'READY.json', dict(arm=arm, actor=actor, source_pins=pins, old_guard_sha256=sha(old / 'GUARD.json'),
        new_guard_sha256=sha(control / 'GUARD.json'), new_plan_sha256=sha(control / 'PLAN.json'),
        original_root=str(root / raw_name), phase='R204_FULL' if arm == 'repo_c1' else 'JASON_RENDERER_ONLY',
        no_live_source_mutation=True, source51_not_restored=True, observed_unix=time.time()))
    print(json.dumps(dict(arm=arm,ready=str(output / 'READY.json'))))


def cpu(arm):
    root = TARGETS[arm][0]
    output = root / ATTEMPT
    source = output / 'source'
    sys.path.insert(0, str(source))
    from gpu.orch_r125_continual_native import validate_plan
    from organism_v6.orch_r124_train_history import TrainEvent
    from organism_v6.orch_r125_plain_context import event_message
    validate_plan(read(output / 'control/PLAN.json'))
    tool = dict(schema='R183_ACTUAL_TOOL_RESULT_V1', status='COMPLETE', action='read',
        origin=dict(actor='child', split='TRAIN'), source_sha256='b' * 64, content='synthetic receiving fixture')
    event = TrainEvent(event_id='receiving:tool', episode_id='receiving', source_id='receiving', source_sha256='a' * 64,
        actor='environment', phase='feedback', text='Tool: ' + json.dumps(tool), split='TRAIN', origin='TRAIN_COLLECTION')
    require(event_message(event) == dict(role='user', content=event.text), 'tool_receipt_content_visible')
    if arm == 'repo_c1':
        from unittest.mock import patch
        from gpu.orch_r184_think_act_learn import ThinkActLearn
        probe = object.__new__(ThinkActLearn)
        probe.config = dict(trial_id='R202_REPO_C_node2_clone1')
        with patch('gpu.r184_cpu_bridge.call', return_value={'status': 'SYNTHETIC'}) as mocked:
            require(probe._cpu({}) == {'status': 'SYNTHETIC'} and mocked.call_count == 1, 'private_actual_transport_binding')
        require(read(output / 'control/PLAN.json')['think_act_learn']['think_continuation_policy'] == 'R204_EXPLICIT_THINK_CONTINUATION_V1', 'R204_policy')
        require(sequence_start(root / 'tool_receipts') > 0, 'existing_tool_sequences_preserved')
    print(json.dumps(dict(passed=True, arm=arm, cuda_used=False)))


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
        boundary_path = root / 'r204_boundary_20260918t0353z/BOUNDARY.json'
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
    root, raw_name, unused_pid, unused_ticks = TARGETS[arm]
    raw = root / raw_name
    output = root / ATTEMPT
    ready = read(output / 'READY.json')
    actor = ready['actor']
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
        while time.monotonic() < finish and not (root / 'control/OUTER_EXIT.json').exists():
            time.sleep(0.2)
        require((root / 'control/OUTER_EXIT.json').exists(), 'old_outer_exited')
        if arm == 'repo_c1':
            old_start = read(root / 'STARTED.json')['processes']['repo_bridge']
            bridge_identity = saved.identity(old_start['pid'])
            require(bridge_identity['start_ticks'] == old_start['start_ticks'] and bridge_identity['argv'][-1] == str(root / 'BRIDGE.json'), 'exact_idle_old_bridge')
            bridge_descriptor = os.pidfd_open(bridge_identity['pid'])
            try:
                signal.pidfd_send_signal(bridge_descriptor, signal.SIGTERM)
                require(bool(select.select([bridge_descriptor], [], [], 10)[0]), 'idle_bridge_exit')
            finally:
                os.close(bridge_descriptor)
            bridge = read(root / 'BRIDGE.json')
            bridge.update(native_source=str(output / 'source'), guard_path=str(output / 'control/GUARD.json'),
                guard_sha256=sha(output / 'control/GUARD.json'), socket='/tmp/r204_repo_c1_boundary.sock')
            write(output / 'BRIDGE.json', bridge)
            with (output / 'bridge.log').open('x') as log:
                process = subprocess.Popen([PYTHON, '-B', str(output / 'repo_bridge.py'), '--config', str(output / 'BRIDGE.json')],
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
        handoff(arguments.arm, arguments.seconds)
    else:
        globals()[arguments.mode](arguments.arm)
