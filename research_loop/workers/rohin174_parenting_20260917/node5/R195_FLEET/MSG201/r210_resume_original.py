"""R210 narrow original homework route using the deployed saved-boundary handoff."""

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


OLD = Path('/localhome/local-rohing/orch_r209_C2_20260918_resume1')
ROOT = Path('/localhome/local-rohing/orch_r210_C2_20260918_resume1')
LIFE = Path('/localhome/local-rohing/orch_r153_community_C2_20260916_attempt1/life')
BOUNDARY = OLD / 'control/R210_HOMEWORK_BOUNDARY'
PYTHON = '/localhome/local-rohing/v2/venv/bin/python'
TRIAL = 'C2_R209_prose_cadence_saved_boundary_resume'
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
    previous_guard = read(OLD / 'control/GUARD.json')
    require(all(sha(OLD / 'source' / name) == expected
        for name, expected in previous_guard['source_pins'].items()), 'unchanged_R209_source_pins')
    source = ROOT / 'source'
    shutil.copytree(OLD / 'source', source,
        ignore=shutil.ignore_patterns('__pycache__', '*.pyc', '.pytest_cache'))
    proof = read(ROOT / 'CPU_TESTED.json')
    require(proof['passed'] and proof['tests_run'] == 4
        and proof['helper_sha256'] == sha(ROOT / 'r210_homework.py'), 'four_R210_CPU_regressions')
    shutil.copy2(ROOT / 'r210_homework.py', source / 'gpu/r210_homework.py')
    driver = source / 'gpu/orch_r184_think_act_learn.py'
    text = driver.read_text()
    before = '        driver.wake()\n        cycle = completed_sleeps + 1'
    after = ('        from gpu.r210_homework import homework_wake\n'
        '        if not homework_wake(driver):\n'
        '            driver.wake()\n        cycle = completed_sleeps + 1')
    require(text.count(before) == 1, 'single_original_loop_hook')
    driver.write_text(text.replace(before, after, 1))
    ast.parse(driver.read_text())
    shutil.copy2(OLD / 'math_bridge.py', ROOT / 'math_bridge.py')
    plan = deepcopy(read(previous_guard['plan_path']))
    plan['source_root'] = str(source)
    plan['startup_context']['path'] = str(source / 'context/R153_STARTUP.md')
    previous_driver = plan['think_act_learn']
    require(plan['root'] == str(LIFE) and plan['physical'] == 1
        and plan['hard_end_unix'] == 1789776000 and plan['lease_end_unix'] == 1789776600
        and plan['new_presentations'] == 16 and plan['rehearsal_presentations'] == 0
        and previous_driver['prose_target_filter'] == 'R209_ENGLISH_PROSE_TARGET_QUARANTINE_V1',
        'same_life_wall_recipe_filters')
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
        source_pins=pins, R210_tests=proof, R209_shared_tests=62,
        receiving_checks='All prior pins, four scoped CPU tests, native plan and same CPU gate'))
    write(control / 'ALLOCATION.json', dict(plan_sha256=sha(control / 'PLAN.json'),
        cpu_tests_passed=True, physical=1, gpu_uuid=plan['gpu_uuid'], builder_entry_logged=True,
        declared_unix=time.time(), cpu_receipt_path=str(control / 'RECEIVING_CPU.json'),
        cpu_receipt_sha256=sha(control / 'RECEIVING_CPU.json'),
        authority='Rohin210 genuine homework before next reply; same original C2'))
    config = deepcopy(previous_guard)
    config.update(plan_path=str(control / 'PLAN.json'), plan_sha256=sha(control / 'PLAN.json'),
        source_pins=pins, allocation_path=str(control / 'ALLOCATION.json'),
        allocation_sha256=sha(control / 'ALLOCATION.json'), attempt_dir=str(control), copy_raw=str(LIFE), resume=True)
    write(control / 'GUARD.json', config)
    validate(control / 'GUARD.json')
    bridge = read(OLD / 'BRIDGE.json')
    bridge.update(socket='/tmp/r210_node5_c2_resume1.sock', cpu_source=str(source),
        native_source=str(source), guard_path=str(control / 'GUARD.json'), guard_sha256=sha(control / 'GUARD.json'))
    write(ROOT / 'BRIDGE.json', bridge)
    write(ROOT / 'STAGED.json', dict(observed_unix=time.time(), status='R210_STAGED_NOT_LOADED',
        awaiting_boundary=str(BOUNDARY), same_life_root=str(LIFE), human_source_writes=0))
    print('R210_STAGED', flush=True)


def preserve():
    pause = read(BOUNDARY / 'PAUSED.json')
    saved.same(pause['actor'])
    require(saved.reference(records()[-1]) == pause['exact_head'], 'unchanged_paused_head')
    record = read(LIFE / 'stream/records' / f'{pause["complete_index"]:020d}.json')
    document = record['document']
    checkpoint = LIFE / 'checkpoints' / f'sleep_{document["cycle"]:06d}'
    shutil.copytree(checkpoint, BOUNDARY / checkpoint.name)
    require(saved.files(checkpoint) == saved.files(BOUNDARY / checkpoint.name), 'exact_checkpoint_bytes')
    shutil.copytree(LIFE / 'stream', BOUNDARY / 'preserved_stream')
    saved.verify_snapshot(BOUNDARY / 'preserved_stream', LIFE, dict(reference=pause['exact_head']))
    require(saved.reference(records()[-1]) == pause['exact_head'], 'same_paused_head')
    write(BOUNDARY / 'PRESERVED_COMPLETE.json', dict(observed_unix=time.time(),
        cycle=document['cycle'], complete_index=record['index'], complete_sha256=record['sha256'],
        state_sha256=document['resume_state']['sha256'],
        optimizer_steps=document['checkpoint']['optimizer_steps'],
        checkpoint_files=saved.files(BOUNDARY / checkpoint.name),
        checkpoint_root=str(BOUNDARY / checkpoint.name), stream_root=str(BOUNDARY / 'preserved_stream'),
        preserved_inbox_files=saved.files(BOUNDARY / 'preserved_stream/inbox'),
        human_inbox_writes=0, same_life=True, no_history_or_weight_rollback=True,
        earlier_resident_post_console_sampling_RNG_not_separately_checkpointed=True))
    print('R210_COMPLETE61_PRESERVED', flush=True)


def execute():
    require(read(ROOT / 'STAGED.json')['status'] == 'R210_STAGED_NOT_LOADED', 'staged_R209')
    (ROOT / 'EXECUTE_ONCE').mkdir()
    pause = read(BOUNDARY / 'PAUSED.json')
    preserved = read(BOUNDARY / 'PRESERVED_COMPLETE.json')
    actor = pause['actor']
    saved.same(actor)
    require(actor['pid'] == 3304081 and actor['start_ticks'] == '24203056'
        and (Path('/proc') / str(actor['pid']) / 'stat').read_text().rsplit(') ', 1)[1].split()[0] == 'T',
        'exact_paused_R205_original')
    owners = dict(actor=actor, timer=saved.identity(3304080), supervisor=saved.identity(3304043),
        outer=saved.identity(3303984), bridge=saved.identity(3303943))
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
        require(document['status'] == 'COMPLETE' and document['cycle'] == preserved['cycle'] >= 57
            and state['pending'] is None and document['resume_state']['sha256'] == saved.digest(state)
            and document['checkpoint']['optimizer_steps'] == preserved['optimizer_steps'] >= 5164,
            'exact_next_complete_state')
        require(saved.files(LIFE / 'checkpoints' / f'sleep_{document["cycle"]:06d}') == preserved['checkpoint_files'],
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
            source_cycle=document['cycle'], complete_index=complete['index'], loaded=False, same_root=str(LIFE),
            console_reply_policy='R205_CONSOLE_REPLY_ACT_V1', pinned_messages_policy='R206_VERBATIM_ROHIN_MESSAGES_V1',
            human_inbox_writes=0, same_parent_untouched=True))
        print('R210_WRAPPERS_STARTED_AWAIT_ACTUAL_LOAD', flush=True)
    except BaseException as error:
        write(ROOT / ('FAILURE_' + str(time.time_ns()) + '.json'),
            dict(observed_unix=time.time(), error_type=type(error).__name__, reason=str(error)))
        raise
    finally:
        for descriptor in handles.values():
            os.close(descriptor)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=('stage', 'preserve', 'execute'))
    arguments = parser.parse_args()
    if arguments.action == 'execute':
        sys.path.insert(0, str(ROOT / 'source'))
    globals()[arguments.action]()
