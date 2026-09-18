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


OLD = Path('/localhome/local-rohing/orch_r210_C2_20260918_resume1')
ROOT = Path('/localhome/local-rohing/orch_r210_C2_20260918_resume2')
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
    require(proof['passed'] and proof['tests_run'] == 6
        and proof['helper_sha256'] == sha(ROOT / 'r210_homework.py'), 'six_R210_CPU_regressions')
    shutil.copy2(ROOT / 'r210_homework.py', source / 'gpu/r210_homework.py')
    native = source / 'gpu/orch_r125_continual_native.py'
    text = native.read_text()
    before = "                require(recovering or stream.sleep_frontier == len(stream.rows), 'resume_requires_saved_RNG_sleep_boundary')"
    after = ("                from gpu.r210_homework import allow_committed_reply_recovery\n"
        "                require(recovering or stream.sleep_frontier == len(stream.rows) or "
        "allow_committed_reply_recovery(stream), 'resume_requires_saved_RNG_sleep_boundary')")
    require(text.count(before) == 1, 'single_exact_committed_reply_recovery_binding')
    native.write_text(text.replace(before, after, 1))
    ast.parse(native.read_text())
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
        receiving_checks='All prior pins, six scoped CPU tests, native plan and same CPU gate'))
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
    bridge.update(socket='/tmp/r210_node5_c2_resume2.sock', cpu_source=str(source),
        native_source=str(source), guard_path=str(control / 'GUARD.json'), guard_sha256=sha(control / 'GUARD.json'))
    write(ROOT / 'BRIDGE.json', bridge)
    write(ROOT / 'STAGED.json', dict(observed_unix=time.time(), status='R210_STAGED_NOT_LOADED',
        awaiting_boundary=str(BOUNDARY), same_life_root=str(LIFE), human_source_writes=0))
    print('R210_STAGED', flush=True)


def preserve():
    require(not Path('/proc/3356655').exists() and not Path('/proc/3356559').exists(),
        'failed_original_native_and_supervisor_exited')
    paths = records()
    require(read(paths[-1])['index'] == 6742 and read(paths[-1])['sha256'] ==
        '5196e6ccde5f3ed5ae298e6ac216f7c7ec9faa80560e32e712a1b93296ede88a',
        'unchanged_committed_reply_head_no_later_training')
    state = read(LIFE / 'stream/records/00000000000000006739.json')['document']['state']
    require(state['sha256'] == '537b3bfc06ab2f6dd386099127ef0e1d9edea83ac34e5ddcba7c813eb1658c9c'
        and state['sha256'] == saved.digest(state['state']) and state['state']['pending'] is None,
        'exact_committed_current_history_three_pending_rows')
    complete = read(LIFE / 'stream/records/00000000000000006714.json')['document']
    checkpoint = LIFE / 'checkpoints/sleep_000061'
    shutil.copytree(checkpoint, ROOT / 'preserved_checkpoint61')
    require(saved.files(checkpoint) == saved.files(ROOT / 'preserved_checkpoint61'), 'exact_checkpoint_bytes')
    shutil.copytree(LIFE / 'stream', ROOT / 'preserved_stream')
    saved.verify_snapshot(ROOT / 'preserved_stream', LIFE, dict(reference=saved.reference(paths[-1])))
    require(saved.reference(records()[-1]) == saved.reference(paths[-1]), 'same_inactive_head')
    write(ROOT / 'PRESERVED_COMMITTED.json', dict(observed_unix=time.time(),
        exact_head=saved.reference(paths[-1]), state_sha256=state['sha256'],
        optimizer_steps=complete['checkpoint']['optimizer_steps'],
        checkpoint_files=saved.files(ROOT / 'preserved_checkpoint61'),
        stream_root=str(ROOT / 'preserved_stream'), human_inbox_writes=0,
        pending_rows=len(state['state']['rows']) - state['state']['sleep_frontier'],
        same_life=True, no_history_or_weight_rollback=True, no_generation_replay=True,
        saved_checkpoint_RNG_restored=True, resident_post_generation_sampling_RNG_not_captured=True))
    print('CURRENT_COMMITTED_CONTEXT_AND_COMPLETE61_PRESERVED', flush=True)


def execute():
    (ROOT / 'EXECUTE_ONCE').mkdir()
    require(read(ROOT / 'STAGED.json')['status'] == 'R210_STAGED_NOT_LOADED', 'tested_staged_recovery')
    preserved = read(ROOT / 'PRESERVED_COMMITTED.json')
    require(saved.reference(records()[-1]) == preserved['exact_head'], 'unchanged_committed_head')
    require(saved.files(LIFE / 'checkpoints/sleep_000061') == preserved['checkpoint_files'],
        'unchanged_model_optimizer_saved_RNG')
    require(not Path('/proc/3356655').exists() and not Path('/proc/3356559').exists()
        and not Path('/proc/3356556').exists(), 'prior_original_actors_exited')
    from gpu.orch_r125_continual_native import NativeChild
    NativeChild.verify_checkpoint(read(LIFE / 'stream/records/00000000000000006714.json')['document']['checkpoint'])
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
        source_cycle=61, source_head=preserved['exact_head'], loaded=False, same_root=str(LIFE),
        expected_first_action='LEARN_REVIEW_NO_REPLY_REPLAY', human_inbox_writes=0,
        saved_checkpoint_RNG_restored=True, resident_post_generation_sampling_RNG_not_captured=True))
    print('R210_REVIEW_RECOVERY_STARTED_AWAIT_LOAD', flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=('stage', 'preserve', 'execute'))
    arguments = parser.parse_args()
    if arguments.action == 'execute':
        sys.path.insert(0, str(ROOT / 'source'))
    globals()[arguments.action]()
