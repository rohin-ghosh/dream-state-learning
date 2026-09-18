"""Apply Main's tested R203 overlay and reload original C2 from preserved52."""

import argparse
import ast
from copy import deepcopy
import importlib.util
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
from types import SimpleNamespace


OLD = Path('/localhome/local-rohing/orch_r202_C2_20260918_resume1')
ROOT = Path('/localhome/local-rohing/orch_r203_C2_20260918_resume1')
LIFE = Path('/localhome/local-rohing/orch_r153_community_C2_20260916_attempt1/life')
PRESERVED = OLD / 'control/R203_PAUSE'
TRIAL = 'C2_R203_sleep52_resume'
PYTHON = '/localhome/local-rohing/v2/venv/bin/python'
specification = importlib.util.spec_from_file_location('saved', OLD / 'saved_primitives.py')
saved = importlib.util.module_from_spec(specification)
specification.loader.exec_module(saved)
read, sha, write, require = saved.read, saved.sha, saved.write, saved.require


def environment():
    return dict(os.environ, CUDA_VISIBLE_DEVICES='', PYTHONDONTWRITEBYTECODE='1',
        PYTHONPATH=str(ROOT / 'source'), HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1',
        OMP_NUM_THREADS='1', MKL_NUM_THREADS='1')


def boundary():
    paused = read(PRESERVED / 'PAUSED.json')
    saved.same(paused['actor'])
    tasks = list((Path('/proc') / str(paused['actor']['pid']) / 'task').iterdir())
    require(all((task / 'stat').read_text().rsplit(') ', 1)[1].split()[0] in ('T', 't')
        for task in tasks), 'original_C2_still_paused')
    paths = sorted((LIFE / 'stream/records').glob('[0-9]' * 20 + '.json'))
    require(saved.reference(paths[-1]) == paused['exact_head'], 'unchanged_COMPLETE52_head')
    record = read(paths[-1])
    require(record['kind'] == 'SLEEP_COMPLETE' and record['index'] == 5975
        and record['document']['cycle'] == 52, 'exact_original_complete52')
    state = record['document']['resume_state']
    require(state['sha256'] == saved.digest(state['state']) and state['state']['pending'] is None,
        'complete52_state_not_pending')
    checkpoint = record['document']['checkpoint']
    require(checkpoint['optimizer_steps'] == 4988, 'original52_not_clone51')
    preserved = read(PRESERVED / 'COMPLETED_CHECKPOINT_PRESERVED.json')
    require(saved.files(LIFE / 'checkpoints/sleep_000052') == preserved['files'], 'completed52_unchanged')
    return record


def stage():
    require(Path(__file__).resolve().parent == ROOT, 'owned_new_R203_control')
    record = boundary()
    main = read(ROOT / 'main_ready/READY.json')
    archive = ROOT / 'main_ready/runtime_overlay.tar.gz'
    require(main['schema'] == 'R203_MAIN_TESTED_SOURCE_OVERLAY_V1'
        and main['status'] == 'CPU_TESTED_NOT_LIVE' and len(main['files']) == 37
        and sha(archive) == main['archive_sha256'] ==
        'ca6c1b006260c677bdbb003baf52333e354d7a9e0ec266ebdacac08992f89544', 'exact_Main_R203')
    require(all(item['failed'] == 0 and item.get('skipped', 0) == 0
        for item in main['validation']), 'Main_test_results_with_explicit_known_deselection')
    source = ROOT / 'source'
    shutil.copytree(OLD / 'source', source, ignore=shutil.ignore_patterns('__pycache__', '*.pyc', '.pytest_cache'))
    with tarfile.open(archive) as package:
        members = package.getmembers()
        require(len(members) == 37 and all(member.isfile() and member.name in main['files']
            and not Path(member.name).is_absolute() and '..' not in Path(member.name).parts
            for member in members), 'safe_exact_overlay_members')
        package.extractall(source, filter='data')
    require(all(sha(source / name) == expected for name, expected in main['files'].items()),
        'all37_frozen_Main_files_verified')
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
    require(text.count(original) == 1, 'one_existing_CPU_adapter_insertion')
    driver.write_text(text.replace(original, replacement, 1))
    shutil.copy2(OLD / 'math_bridge.py', ROOT / 'math_bridge.py')
    shutil.copy2(OLD / 'math_bridge.py', source / 'gpu/r184_cpu_bridge.py')
    original_guard = read(OLD / 'control/GUARD.json')
    original_plan = read(original_guard['plan_path'])
    plan = deepcopy(original_plan)
    plan.update(main['required_native_options'])
    plan['source_root'] = str(source)
    plan['startup_context']['path'] = str(source / 'context/R153_STARTUP.md')
    plan['think_act_learn'] = dict(main['required_driver_options'], trial_id=TRIAL,
        cpu_gate_root=original_plan['think_act_learn']['cpu_gate_root'],
        cpu_gate_sha256=original_plan['think_act_learn']['cpu_gate_sha256'],
        environment_facts=original_plan['think_act_learn']['environment_facts'])
    require(plan['root'] == str(LIFE) and plan['physical'] == 1 and plan['hard_end_unix'] == 1789776000
        and plan['lease_end_unix'] == 1789776600 and plan['anchor_lambda'] == .25,
        'same_original_life_GPU1_recipe_and_wall')
    control = ROOT / 'control'
    control.mkdir()
    write(control / 'PLAN.json', plan)
    sys.path.insert(0, str(source))
    from organism_v6.orch_r125_continual_stream import ContinualStream
    from gpu import orch_r125_continual_native as native
    from gpu import orch_r125_continual_guard as guard
    from gpu import orch_r184_think_act_learn as driver_module
    from gpu import r184_cpu_bridge as bridge_module
    from gpu.orch_r125_cpu_experiment import digest, verify_gate
    import torch
    native.validate_plan(plan)
    restored = ContinualStream.restore(record['document']['resume_state'],
        expected_sha256=record['document']['resume_state']['sha256'])
    require(restored.checkpoint() == record['document']['resume_state'], 'exact52_history_and_state_roundtrip')
    native.NativeChild.verify_checkpoint(record['document']['checkpoint'])
    require(not torch.cuda.is_initialized(), 'receiving_smoke_CPU_only')
    require(digest(verify_gate(plan['think_act_learn']['cpu_gate_root'])) ==
        plan['think_act_learn']['cpu_gate_sha256'], 'same_actual_CPU_gate')
    origin = dict(kind='TRAIN_CHILD_RESPONSE', record_index=5875,
        record_sha256='18ba0b1d25ab06dd1f33e2dc6317a0ec444e272aad7c02ed6f08c1e01d36fb04')
    original_call = bridge_module.call
    received = []
    try:
        def witness(config, actual_origin):
            received.append((config, actual_origin))
            return {'route_smoke_only_not_execution': True}
        bridge_module.call = witness
        result = driver_module.ThinkActLearn._cpu(SimpleNamespace(config=plan['think_act_learn']), origin)
        require(result == {'route_smoke_only_not_execution': True}
            and received == [(plan['think_act_learn'], origin)], 'actual_C2_trial_uses_existing_CPU_bridge')
    finally:
        bridge_module.call = original_call
    pins = {str(path.relative_to(source)): sha(path) for path in source.rglob('*.py')}
    cpu = dict(passed=True, observed_unix=time.time(), source_pins=pins, tests_run=1,
        receiving_smoke='exact52 restore, checkpoint hashes, plan/gate validation, actual-trial bridge routing',
        no_gpu_initialized=True, Main_ready_sha256=sha(ROOT / 'main_ready/READY.json'),
        Main_validation=main['validation'], broad_suite_rerun=False,
        existing_bridge_adapter_delta=dict(Main_driver_sha256=main['files']['gpu/orch_r184_think_act_learn.py'],
            receiving_driver_sha256=sha(driver), trial_id=TRIAL, original_cpu_method=original),
        current_boundary_index=5975, current_checkpoint=52, optimizer_steps=4988,
        history_events=len(restored.history.events), no_model_or_history_reset=True)
    write(control / 'RECEIVING_CPU.json', cpu)
    allocation = dict(plan_sha256=sha(control / 'PLAN.json'), cpu_tests_passed=True,
        physical=1, gpu_uuid=plan['gpu_uuid'], builder_entry_logged=True, declared_unix=time.time(),
        cpu_receipt_path=str(control / 'RECEIVING_CPU.json'), cpu_receipt_sha256=sha(control / 'RECEIVING_CPU.json'),
        authority='Rohin203 explicit tested overlay release; Main frozen test provenance plus receiving smoke')
    write(control / 'ALLOCATION.json', allocation)
    config = deepcopy(original_guard)
    config.update(plan_path=str(control / 'PLAN.json'), plan_sha256=sha(control / 'PLAN.json'), source_pins=pins,
        allocation_path=str(control / 'ALLOCATION.json'), allocation_sha256=sha(control / 'ALLOCATION.json'),
        attempt_dir=str(control), copy_raw=str(LIFE), resume=True)
    write(control / 'GUARD.json', config)
    guard.validate(control / 'GUARD.json')
    write(ROOT / 'BRIDGE.json', dict(raw_root=str(LIFE), journal_id=read(LIFE / 'stream/JOURNAL.json')['journal_id'],
        socket='/tmp/r203_node5_c2_resume1.sock', cpu_source=str(source), native_source=str(source),
        gate_root=plan['think_act_learn']['cpu_gate_root'], gate_sha256=plan['think_act_learn']['cpu_gate_sha256'],
        code_policy=plan['think_act_learn']['code_policy'], guard_path=str(control / 'GUARD.json'),
        guard_sha256=sha(control / 'GUARD.json'), stop_unix=plan['hard_end_unix']))
    require(boundary() == record, 'original_still_paused_at52_after_smoke')
    write(ROOT / 'STAGED.json', dict(observed_unix=time.time(), status='R203_RECEIVING_SMOKE_PASS_NOT_RELOADED',
        current_boundary_index=5975, source_checkpoint=52, optimizer_steps=4988,
        Main_READY=saved.reference(ROOT / 'main_ready/READY.json'), receiving_cpu=saved.reference(control / 'RECEIVING_CPU.json')))
    print(json.dumps(dict(status='STAGED_SMOKE_PASS', original_still_paused=True)), flush=True)


def execute():
    require(read(ROOT / 'STAGED.json')['source_checkpoint'] == 52, 'staged_original52')
    record = boundary()
    (ROOT / 'EXECUTE_ONCE').mkdir()
    owners = dict(actor=saved.identity(3114821), timer=saved.identity(3114820),
        supervisor=saved.identity(3114815), outer=saved.identity(3114756), bridge=saved.identity(3114716))
    handles = {name: os.pidfd_open(identity['pid']) for name, identity in owners.items()}
    try:
        inbox_before = saved.files(LIFE / 'stream/inbox')
        superseded = LIFE / 'stream/inbox/637e4fbb797349aa9b4e9b8d11ad85d8.json'
        require(sha(superseded) == 'b5aa4da566a2c6b6cace5d4ed54216f0ff2ea283f5ff12471fc0d84e26292cbd',
            'exact_superseded_pending_parent')
        require(all(event['event_id'] != 'parent:inbox:637e4fbb797349aa9b4e9b8d11ad85d8'
            for event in record['document']['resume_state']['state']['history']['events']), 'not_consumed_history')
        quarantine = ROOT / 'superseded_parent_sources'
        quarantine.mkdir()
        superseded.rename(quarantine / superseded.name)
        write(ROOT / 'PARENT_QUARANTINE.json', dict(observed_unix=time.time(), source=str(superseded),
            destination=str(quarantine / superseded.name), sha256=inbox_before[superseded.name],
            reason='R203 learning-system walkthrough first; older queued creative-first guidance superseded',
            source_preserved=True, consumed_history_deleted=False, human_sources_modified=False))
        shutil.copytree(LIFE / 'stream/inbox', ROOT / 'inbox_before_reload')
        inbox_after = saved.files(LIFE / 'stream/inbox')
        require({name: value for name, value in inbox_before.items() if name != superseded.name} == inbox_after,
            'only_explicit_pending_parent_quarantine_changed_inbox')
        write(ROOT / 'RELOAD_INTENT.json', dict(observed_unix=time.time(), owners=owners,
            preserved_complete=saved.reference(PRESERVED / 'PRESERVED_COMPLETE.json'),
            source_boundary_index=5975, checkpoint=52, optimizer_steps=4988,
            inbox=inbox_after, same_life=True, no_fake_human_messages=True))
        require(boundary() == record, 'exact_boundary_before_retiring_old_native')
        saved.same(owners['actor'])
        signal.pidfd_send_signal(handles['actor'], signal.SIGTERM)
        signal.pidfd_send_signal(handles['actor'], signal.SIGCONT)
        for name in ('actor', 'timer', 'supervisor', 'outer'):
            require(bool(select.select([handles[name]], [], [], 30)[0]), 'old_owned_actor_exited:' + name)
        require(saved.reference(LIFE / 'stream/records/00000000000000005975.json') ==
            read(PRESERVED / 'PAUSED.json')['exact_head'], 'no_checkpoint_or_history_rollback')
        saved.same(owners['bridge'])
        signal.pidfd_send_signal(handles['bridge'], signal.SIGTERM)
        require(bool(select.select([handles['bridge']], [], [], 15)[0]), 'old_bridge_exited')
        write(ROOT / 'OLD_RUNTIME_RETIRED.json', dict(observed_unix=time.time(), owners=owners,
            same_life_root=str(LIFE), checkpoint52_retained=True, no_inflight_kill=True))
        processes = {}
        for name, command in (
            ('bridge', [PYTHON, '-B', str(ROOT / 'math_bridge.py'), '--config', str(ROOT / 'BRIDGE.json')]),
            ('supervisor', [PYTHON, '-B', '-m', 'gpu.r188_node5_confinement', 'dispatch', '--config', str(ROOT / 'control/GUARD.json')]),
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
            checkpoint=52, optimizer_steps=4988, same_root=str(LIFE), loaded=False))
        print(json.dumps(dict(status='R203_ORIGINAL52_WRAPPERS_STARTED_NOT_YET_LOADED',
            processes=processes)), flush=True)
    finally:
        for descriptor in handles.values():
            os.close(descriptor)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=('stage', 'execute'))
    globals()[parser.parse_args().action]()
