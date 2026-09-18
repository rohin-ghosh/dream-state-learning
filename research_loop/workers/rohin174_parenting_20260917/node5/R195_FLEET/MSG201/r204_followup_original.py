"""Bounded R204 receiving adaptation using the existing C2 pause and guard."""

import argparse
import ast
from copy import deepcopy
import importlib.util
import os
from pathlib import Path
import select
import shutil
import signal
import subprocess
import sys
import tarfile
import time


OLD = Path('/localhome/local-rohing/orch_r203_C2_20260918_resume1')
ROOT = Path('/localhome/local-rohing/orch_r204_C2_20260918_resume1')
LIFE = Path('/localhome/local-rohing/orch_r153_community_C2_20260916_attempt1/life')
PYTHON = '/localhome/local-rohing/v2/venv/bin/python'
TRIAL = 'C2_R204_saved_boundary_resume'
specification = importlib.util.spec_from_file_location('saved',
    '/localhome/local-rohing/orch_r202_C2_20260918_resume1/saved_primitives.py')
saved = importlib.util.module_from_spec(specification)
specification.loader.exec_module(saved)
read, sha, write, require = saved.read, saved.sha, saved.write, saved.require


def environment():
    return dict(os.environ, CUDA_VISIBLE_DEVICES='', PYTHONDONTWRITEBYTECODE='1',
        PYTHONPATH=str(ROOT / 'source'), HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1',
        OMP_NUM_THREADS='1', MKL_NUM_THREADS='1')


def records():
    return sorted((LIFE / 'stream/records').glob('[0-9]' * 20 + '.json'))


def metadata(path):
    import json
    with path.open('rb') as handle:
        handle.seek(max(0, path.stat().st_size - 4096))
        raw = handle.read()
    return json.loads(b'{' + raw[raw.rfind(b',"index":') + 1:])


def stage():
    main = read(ROOT / 'main_ready/READY.json')
    archive = ROOT / 'main_ready/runtime_overlay.tar.gz'
    require(main['schema'] == 'R204_MAIN_TESTED_SOURCE_OVERLAY_V1'
        and main['status'] == 'CPU_TESTED_NOT_LIVE' and len(main['files']) == 37
        and sha(archive) == main['archive_sha256'] ==
        'b0f148c92172af9d1525fda79a97bebfb31337e312e26c0f6bc805b3c687f8fc', 'exact_Main_R204')
    require(all(item['failed'] == 0 and item.get('skipped', 0) == 0
        for item in main['validation']), 'Main_targeted_tests_with_recorded_deselection')
    source = ROOT / 'source'
    shutil.copytree(OLD / 'source', source,
        ignore=shutil.ignore_patterns('__pycache__', '*.pyc', '.pytest_cache'))
    with tarfile.open(archive) as package:
        members = package.getmembers()
        require(len(members) == 37 and all(member.isfile() and member.name in main['files']
            and not Path(member.name).is_absolute() and '..' not in Path(member.name).parts
            for member in members), 'bounded_overlay_members')
        package.extractall(source, filter='data')
    require(all(sha(source / name) == expected for name, expected in main['files'].items()),
        'all37_Main_files_verified_before_existing_bridge_hook')
    driver = source / 'gpu/orch_r184_think_act_learn.py'
    text = driver.read_text()
    method = next(node for node in ast.walk(ast.parse(text))
        if isinstance(node, ast.FunctionDef) and node.name == '_cpu')
    original = ast.get_source_segment(text, method)
    replacement = ('def _cpu(self, origin):\n'
        + f'        if self.config["trial_id"] == {TRIAL!r}:\n'
        + '            from gpu.r184_cpu_bridge import call\n'
        + '            return call(self.config, origin)\n'
        + ''.join(original.splitlines(keepends=True)[1:]))
    require(text.count(original) == 1, 'single_existing_bridge_hook')
    driver.write_text(text.replace(original, replacement, 1))
    shutil.copy2(OLD / 'math_bridge.py', ROOT / 'math_bridge.py')
    shutil.copy2(OLD / 'math_bridge.py', source / 'gpu/r184_cpu_bridge.py')
    previous_guard = read(OLD / 'control/GUARD.json')
    plan = deepcopy(read(previous_guard['plan_path']))
    plan.update(main['required_native_options'])
    previous_driver = plan['think_act_learn']
    plan['source_root'] = str(source)
    plan['startup_context']['path'] = str(source / 'context/R153_STARTUP.md')
    plan['think_act_learn'] = dict(main['required_driver_options'], trial_id=TRIAL,
        **{name: previous_driver[name] for name in
            ('cpu_gate_root', 'cpu_gate_sha256', 'environment_facts')})
    require(plan['root'] == str(LIFE) and plan['physical'] == 1
        and plan['hard_end_unix'] == 1789776000 and plan['lease_end_unix'] == 1789776600
        and plan['anchor_lambda'] == .25, 'same_life_GPU1_recipe_and_wall')
    control = ROOT / 'control'
    control.mkdir()
    write(control / 'PLAN.json', plan)
    sys.path.insert(0, str(source))
    from gpu.orch_r125_continual_native import validate_plan
    from gpu.orch_r125_cpu_experiment import digest, verify_gate
    from gpu.orch_r125_continual_guard import validate
    validate_plan(plan)
    require(digest(verify_gate(previous_driver['cpu_gate_root'])) == previous_driver['cpu_gate_sha256'],
        'same_actual_CPU_gate')
    pins = {str(path.relative_to(source)): sha(path) for path in source.rglob('*.py')}
    write(control / 'RECEIVING_CPU.json', dict(passed=True, observed_unix=time.time(),
        source_pins=pins, tests_run=0, Main_validation=main['validation'],
        Main_ready_sha256=sha(ROOT / 'main_ready/READY.json'), broad_suite_rerun=False,
        receiving_checks='37 frozen hashes, native plan, unchanged actual CPU gate, existing bridge adapter',
        bridge_driver_sha256=sha(driver), no_new_test_gate=True))
    write(control / 'ALLOCATION.json', dict(plan_sha256=sha(control / 'PLAN.json'),
        cpu_tests_passed=True, physical=1, gpu_uuid=plan['gpu_uuid'], builder_entry_logged=True,
        declared_unix=time.time(), cpu_receipt_path=str(control / 'RECEIVING_CPU.json'),
        cpu_receipt_sha256=sha(control / 'RECEIVING_CPU.json'), authority='Rohin204 next saved boundary'))
    config = deepcopy(previous_guard)
    config.update(plan_path=str(control / 'PLAN.json'), plan_sha256=sha(control / 'PLAN.json'),
        source_pins=pins, allocation_path=str(control / 'ALLOCATION.json'),
        allocation_sha256=sha(control / 'ALLOCATION.json'), attempt_dir=str(control),
        copy_raw=str(LIFE), resume=True)
    write(control / 'GUARD.json', config)
    validate(control / 'GUARD.json')
    bridge = read(OLD / 'BRIDGE.json')
    bridge.update(socket='/tmp/r204_node5_c2_resume1.sock', cpu_source=str(source),
        native_source=str(source), guard_path=str(control / 'GUARD.json'),
        guard_sha256=sha(control / 'GUARD.json'))
    write(ROOT / 'BRIDGE.json', bridge)
    write(ROOT / 'STAGED.json', dict(observed_unix=time.time(), status='R204_STAGED_NOT_LOADED',
        Main_READY=saved.reference(ROOT / 'main_ready/READY.json'), same_life_root=str(LIFE),
        human_source_writes=0, parent_source_writes=0, no_cancel_of_R203=True))
    print('R204_STAGED_WAIT_NEXT_COMPLETE', flush=True)


def execute(recover=False):
    require(read(ROOT / 'STAGED.json')['status'] == 'R204_STAGED_NOT_LOADED', 'staged_R204')
    if recover:
        require((ROOT / 'preserved_boundary/stream').is_dir()
            and not (ROOT / 'OLD_RUNTIME_RETIRED.json').exists(), 'only_pre_retirement_recovery')
    else:
        (ROOT / 'EXECUTE_ONCE').mkdir()
    actor = saved.identity(3165023)
    require(actor['start_ticks'] == '23723871' and actor['cwd'] == str(OLD / 'source')
        and actor['argv'][-1] == str(OLD / 'control/GUARD.json'), 'exact_original_R203_actor')
    owners = dict(actor=actor, timer=saved.identity(actor['parent']),
        supervisor=saved.identity(3165019), outer=saved.identity(3164927), bridge=saved.identity(3164888))
    handles = {name: os.pidfd_open(identity['pid']) for name, identity in owners.items()}
    preserve = ROOT / 'preserved_boundary'
    preserve.mkdir(exist_ok=recover)
    write(ROOT / ('RECOVERY_ARMED.json' if recover else 'ARMED.json'), dict(observed_unix=time.time(), pid=os.getpid(), owners=owners,
        next_index=6004, no_inflight_kill=True, parent_walkthrough_preserved=True))
    next_index = 6004
    try:
        while time.time() < 1789775970:
            path = LIFE / 'stream/records' / f'{next_index:020d}.json'
            if not path.exists():
                time.sleep(.01)
                continue
            next_index += 1
            if metadata(path)['kind'] != 'SLEEP_COMPLETE':
                continue
            saved.pause_exact(actor, handles['actor'])
            paused_unix = time.time()
            complete = read(path)
            current = records()
            tail = [metadata(item) for item in current[complete['index'] + 1:]]
            if any(item['kind'] != 'R184_LEARN_COMPLETE' for item in tail):
                write(preserve / f'MISSED_{complete["index"]}.json', dict(observed_unix=paused_unix, tail=tail))
                signal.pidfd_send_signal(handles['actor'], signal.SIGCONT)
                continue
            document = complete['document']
            state = document['resume_state']['state']
            require(document['status'] == 'COMPLETE' and state['pending'] is None
                and document['resume_state']['sha256'] == saved.digest(state), 'complete_saved_state')
            checkpoint = LIFE / 'checkpoints' / f'sleep_{document["cycle"]:06d}'
            if not recover:
                shutil.copytree(checkpoint, preserve / checkpoint.name)
            require(saved.files(checkpoint) == saved.files(preserve / checkpoint.name), 'checkpoint_exact')
            if not recover:
                shutil.copytree(LIFE / 'stream', preserve / 'stream')
            saved.verify_snapshot(preserve / 'stream', LIFE, dict(reference=saved.reference(current[-1])))
            write(ROOT / 'PAUSED_PRESERVED.json', dict(observed_unix=paused_unix,
                completed_preservation_unix=time.time(), cycle=document['cycle'],
                complete_index=complete['index'], complete_sha256=complete['sha256'],
                optimizer_steps=document['checkpoint']['optimizer_steps'],
                checkpoint_files=saved.files(preserve / checkpoint.name),
                exact_head=saved.reference(current[-1]), actor=actor, tail=tail,
                snapshot_root=str(preserve), source52_retained_with_corrupt_exposure=True,
                earlier_live_console_sampling_RNG_not_separately_checkpointed=True,
                same_parent=True, inbox_source_writes=0, no_history_rollback=True))
            from gpu.orch_r125_continual_native import NativeChild
            NativeChild.verify_checkpoint(document['checkpoint'])
            require(saved.reference(records()[-1]) == saved.reference(current[-1]), 'no_post_pause_generation')
            saved.same(actor)
            signal.pidfd_send_signal(handles['actor'], signal.SIGTERM)
            signal.pidfd_send_signal(handles['actor'], signal.SIGCONT)
            for name in ('actor', 'timer', 'supervisor', 'outer'):
                require(bool(select.select([handles[name]], [], [], 30)[0]), 'owned_exit:' + name)
            saved.same(owners['bridge'])
            signal.pidfd_send_signal(handles['bridge'], signal.SIGTERM)
            require(bool(select.select([handles['bridge']], [], [], 15)[0]), 'owned_bridge_exit')
            write(ROOT / 'OLD_RUNTIME_RETIRED.json', dict(observed_unix=time.time(), owners=owners,
                preserved=saved.reference(ROOT / 'PAUSED_PRESERVED.json'), same_life=True))
            processes = {}
            for name, command in (
                ('bridge', [PYTHON, '-B', str(ROOT / 'math_bridge.py'), '--config', str(ROOT / 'BRIDGE.json')]),
                ('supervisor', [PYTHON, '-B', '-m', 'gpu.r188_node5_confinement', 'dispatch',
                    '--config', str(ROOT / 'control/GUARD.json')]),
            ):
                with (ROOT / (name + '.log')).open('x') as log:
                    process = subprocess.Popen(command, cwd=ROOT / 'source', env=environment(),
                        stdin=subprocess.DEVNULL, stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
                processes[name] = saved.identity(process.pid)
                if name == 'bridge':
                    deadline = time.monotonic() + 20
                    while not list((ROOT / 'bridge_receipts').glob('READY*')):
                        require(process.poll() is None and time.monotonic() < deadline, 'new_bridge_ready')
                        time.sleep(.1)
            write(ROOT / 'STARTED.json', dict(observed_unix=time.time(), processes=processes,
                source_cycle=document['cycle'], complete_index=complete['index'], loaded=False,
                same_root=str(LIFE), no_human_or_parent_message_fabrication=True))
            print('R204_WRAPPERS_STARTED_AWAIT_ACTUAL_LOAD', flush=True)
            return
        raise TimeoutError('no_complete_before_existing_wall')
    except BaseException as error:
        write(ROOT / ('FAILURE_' + str(time.time_ns()) + '.json'), dict(observed_unix=time.time(),
            error_type=type(error).__name__, reason=str(error)))
        raise
    finally:
        for descriptor in handles.values():
            os.close(descriptor)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=('stage', 'execute', 'recover'))
    arguments = parser.parse_args()
    if arguments.action in ('execute', 'recover'):
        sys.path.insert(0, str(ROOT / 'source'))
    if arguments.action == 'recover':
        execute(recover=True)
    else:
        globals()[arguments.action]()
