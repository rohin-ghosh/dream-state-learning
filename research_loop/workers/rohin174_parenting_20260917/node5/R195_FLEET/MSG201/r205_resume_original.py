"""R205 same-life receiving adaptation of the existing R204 handoff."""

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


OLD = Path('/localhome/local-rohing/orch_r204_C2_20260918_resume1')
ROOT = Path('/localhome/local-rohing/orch_r205_C2_20260918_resume1')
LIFE = Path('/localhome/local-rohing/orch_r153_community_C2_20260916_attempt1/life')
BOUNDARY = OLD / 'control/R205_PAUSE_20260918T0357Z'
PYTHON = '/localhome/local-rohing/v2/venv/bin/python'
TRIAL = 'C2_R205_saved_boundary_resume'
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


def stage():
    main = read(ROOT / 'main_ready/READY.json')
    archive = ROOT / 'main_ready/runtime_overlay.tar.gz'
    require(main['schema'] == 'R205_MAIN_TESTED_SOURCE_OVERLAY_V1'
        and main['status'] == 'CPU_TESTED_NOT_LIVE' and len(main['files']) == 40
        and sha(archive) == main['archive_sha256'] ==
        '72531868c065ecb518c4bac589303085a315e80a15df7c2de59c0925a5a25231', 'exact_Main_R205')
    require(main['cpu_validation']['result'] == 'PASS'
        and main['cpu_validation']['stream_stage_hold_unittest'] == 71
        and main['cpu_validation']['transport_exchange_cpu_pytest'] == 142, 'Main_test_receipts')
    source = ROOT / 'source'
    shutil.copytree(OLD / 'source', source,
        ignore=shutil.ignore_patterns('__pycache__', '*.pyc', '.pytest_cache'))
    with tarfile.open(archive) as package:
        members = package.getmembers()
        require(len(members) == 40 and {member.name for member in members} == set(main['files'])
            and all(member.isfile() and not Path(member.name).is_absolute()
                and '..' not in Path(member.name).parts for member in members), 'bounded_overlay')
        package.extractall(source, filter='data')
    require(all(sha(source / name) == expected for name, expected in main['files'].items()),
        'all40_frozen_hashes_before_existing_bridge_hook')
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
        and plan['anchor_lambda'] == .25 and plan['new_presentations'] == 16
        and plan['rehearsal_presentations'] == 0
        and plan['think_act_learn']['console_reply_policy'] == 'R205_CONSOLE_REPLY_ACT_V1',
        'same_life_wall_recipe_with_console_reply')
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
        source_pins=pins, tests_run=0, Main_validation=main['cpu_validation'],
        Main_ready_sha256=sha(ROOT / 'main_ready/READY.json'), broad_suite_rerun=False,
        bridge_driver_sha256=sha(driver), frozen_driver_sha256=main['files'][str(driver.relative_to(source))],
        receiving_checks='40 frozen hashes, native plan, unchanged CPU gate, existing bridge hook'))
    write(control / 'ALLOCATION.json', dict(plan_sha256=sha(control / 'PLAN.json'),
        cpu_tests_passed=True, physical=1, gpu_uuid=plan['gpu_uuid'], builder_entry_logged=True,
        declared_unix=time.time(), cpu_receipt_path=str(control / 'RECEIVING_CPU.json'),
        cpu_receipt_sha256=sha(control / 'RECEIVING_CPU.json'), authority='Rohin206 deploy R205 same C2 now'))
    config = deepcopy(previous_guard)
    config.update(plan_path=str(control / 'PLAN.json'), plan_sha256=sha(control / 'PLAN.json'),
        source_pins=pins, allocation_path=str(control / 'ALLOCATION.json'),
        allocation_sha256=sha(control / 'ALLOCATION.json'), attempt_dir=str(control), copy_raw=str(LIFE), resume=True)
    write(control / 'GUARD.json', config)
    validate(control / 'GUARD.json')
    bridge = read(OLD / 'BRIDGE.json')
    bridge.update(socket='/tmp/r205_node5_c2_resume1.sock', cpu_source=str(source),
        native_source=str(source), guard_path=str(control / 'GUARD.json'), guard_sha256=sha(control / 'GUARD.json'))
    write(ROOT / 'BRIDGE.json', bridge)
    write(ROOT / 'STAGED.json', dict(observed_unix=time.time(), status='R205_STAGED_NOT_LOADED',
        Main_READY=saved.reference(ROOT / 'main_ready/READY.json'), preserved=saved.reference(BOUNDARY / 'PRESERVED_COMPLETE.json'),
        same_life_root=str(LIFE), human_source_writes=0, parent_source_writes=0))
    print('R205_STAGED_SAVED56', flush=True)


def execute():
    require(read(ROOT / 'STAGED.json')['status'] == 'R205_STAGED_NOT_LOADED', 'staged_R205')
    (ROOT / 'EXECUTE_ONCE').mkdir()
    pause = read(BOUNDARY / 'PAUSED.json')
    preserved = read(BOUNDARY / 'PRESERVED_COMPLETE.json')
    actor = pause['actor']
    saved.same(actor)
    require(actor['pid'] == 3179563 and actor['start_ticks'] == '23773135'
        and (Path('/proc') / str(actor['pid']) / 'stat').read_text().rsplit(') ', 1)[1].split()[0] == 'T',
        'exact_paused_R204_original')
    owners = dict(actor=actor, timer=saved.identity(3179562), supervisor=saved.identity(3179560),
        outer=saved.identity(3179463), bridge=saved.identity(3179422))
    for name, owner in owners.items():
        require(owner['cwd'] == str(OLD / 'source') and
            str(OLD / ('BRIDGE.json' if name == 'bridge' else 'control/GUARD.json')) in owner['argv'],
            'owned_original_actor:' + name)
    handles = {name: os.pidfd_open(owner['pid']) for name, owner in owners.items()}
    try:
        current = records()
        require(saved.reference(current[-1]) == pause['exact_head'], 'unchanged_paused_head')
        complete = read(LIFE / 'stream/records' / f'{pause["complete_index"]:020d}.json')
        document = complete['document']
        state = document['resume_state']['state']
        require(document['status'] == 'COMPLETE' and document['cycle'] == preserved['cycle'] == 56
            and state['pending'] is None and document['resume_state']['sha256'] == saved.digest(state)
            and document['checkpoint']['optimizer_steps'] == preserved['optimizer_steps'] == 5164,
            'exact_saved56_state')
        require(saved.files(LIFE / 'checkpoints/sleep_000056') == preserved['checkpoint_files'],
            'unchanged_adapter_optimizer_saved_RNG')
        from gpu.orch_r125_continual_native import NativeChild
        NativeChild.verify_checkpoint(document['checkpoint'])
        write(ROOT / 'PAUSED_PRESERVED.json', dict(observed_unix=time.time(), preserved=preserved,
            exact_head=pause['exact_head'], owners=owners, current_inbox_files=saved.files(LIFE / 'stream/inbox'),
            source_boundary=str(BOUNDARY), same_life=True, no_history_or_weight_rollback=True))
        for owner in owners.values():
            saved.same(owner)
        signal.pidfd_send_signal(handles['actor'], signal.SIGTERM)
        signal.pidfd_send_signal(handles['actor'], signal.SIGCONT)
        for name in ('actor', 'timer', 'supervisor', 'outer'):
            require(bool(select.select([handles[name]], [], [], 30)[0]), 'owned_exit:' + name)
        saved.same(owners['bridge'])
        signal.pidfd_send_signal(handles['bridge'], signal.SIGTERM)
        require(bool(select.select([handles['bridge']], [], [], 15)[0]), 'owned_bridge_exit')
        require(saved.reference(records()[-1]) == pause['exact_head'], 'no_shutdown_generation')
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
            source_cycle=56, complete_index=6283, loaded=False, same_root=str(LIFE),
            console_reply_policy='R205_CONSOLE_REPLY_ACT_V1', human_inbox_writes=0, same_parent_untouched=True))
        print('R205_WRAPPERS_STARTED_AWAIT_ACTUAL_LOAD', flush=True)
    except BaseException as error:
        write(ROOT / ('FAILURE_' + str(time.time_ns()) + '.json'),
            dict(observed_unix=time.time(), error_type=type(error).__name__, reason=str(error)))
        raise
    finally:
        for descriptor in handles.values():
            os.close(descriptor)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=('stage', 'execute'))
    arguments = parser.parse_args()
    if arguments.action == 'execute':
        sys.path.insert(0, str(ROOT / 'source'))
    globals()[arguments.action]()
