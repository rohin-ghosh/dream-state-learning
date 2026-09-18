"""Runnable shared math successor; original ledger, resident actor, fresh readouts."""

import argparse
from copy import deepcopy
import fcntl
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time

from gpu import orch_math_feedback_uptake_r117_shared as client
from gpu import orch_math_feedback_uptake_r118_shared_ready as ready
from gpu import orch_math_feedback_uptake_r118_shared_boundary as boundary


shared, math, require = client.shared, client.math, client.require
SOURCE = Path(__file__).resolve().parents[1]
MODULE = ready.MODULE


def activation(root, document=None):
    root = Path(root)
    branch = ready.branch_for(root)
    document = shared.read(root/'SHARED_ACTIVATION.json') if document is None else document
    require(document['ready_sha256'] == shared.sha(root/'SHARED_CLIENT_READY.json'), 'exact_successor_readiness')
    receipt = shared.read(root/'SHARED_CLIENT_READY.json')
    require(receipt['successor_source'] == str(SOURCE), 'frozen_successor_source')
    for name, expected in receipt['source_files'].items():
        require(shared.sha(SOURCE/name) == expected, 'immutable_successor:'+name)
    require(document['inherited_bounds'] == receipt['inherited_bounds'] == ready.bounds(), 'original_lifetime_caps')
    require(ready.predecessor(root) == receipt['predecessor_bindings'], 'original_source_data_contract')
    binding = document['shared_learner']
    require(binding['branch'] == branch and binding['root'] == ready.COMMON_ROOT, 'exact_common_branch')
    require(shared.sha(Path(binding['root'])/'CONFIG.json') == binding['config_sha256'], 'common_config_hash')
    config = shared.read(Path(binding['root'])/'CONFIG.json')
    require(config['owner'] == 'F1' and set(config['branches']) == set(shared.BRANCHES), 'eight_branches_one_optimizer')
    require(config['branches'][branch]['root'] == str(root)
        and config['branches'][branch]['train_ids'] == receipt['train_ids'], 'bound_math_train_inventory')
    require(set(receipt['excluded_ids']).issubset(config['excluded_ids']), 'all_readouts_excluded')
    require(config['anchor_sha256'] == shared.ANCHOR_SHA and config['anchor_loss_weight'] == .25
        and config['new_presentations'] == 16 and config['rehearsal_presentations'] == 1, 'unchanged_shared_sleep_recipe')
    require(shared.sha(binding['adoption_path']) == binding['adoption_sha256'], 'exact_adoption')
    adoption = shared.read(binding['adoption_path'])
    require(adoption['checkpoint'] == config['initial_checkpoint']
        and adoption['prior_metrics'] == config['pretransition_metrics'] and config['initial_history'].get('F1'),
        'preserve_F1_optimizer_history')
    require(adoption['branch_bounds'][branch] == ready.bounds(), 'no_branch_budget_reset')
    return document


def activate(root, release, shared_root, adoption, authorization):
    root = Path(root)
    permission = shared.read(authorization)
    require(permission.get('authorized') is True and permission.get('all_eight_ready') is True
        and permission.get('common_handoff_coordinated') is True
        and permission.get('release_sha256') == shared.sha(release), 'agreed_released_boundary_only')
    require(str(shared_root) == ready.COMMON_ROOT, 'assigned_common_root')
    saved = boundary.verify_release(root, ready.reference(release))
    document = dict(schema='R118_MATH_SHARED_ACTIVATION_V1', ready_sha256=shared.sha(root/'SHARED_CLIENT_READY.json'),
        release=ready.reference(release), inherited_bounds=ready.bounds(), start_cycle=saved['next_cycle'],
        shared_learner=dict(branch=ready.branch_for(root), root=str(shared_root),
            config_sha256=shared.sha(Path(shared_root)/'CONFIG.json'), adoption_path=str(adoption),
            adoption_sha256=shared.sha(adoption)), authorization=ready.reference(authorization), observed_unix=time.time())
    activation(root, document)
    shared.write(root/'SHARED_ACTIVATION.json', document)
    return document


def wait_published(session, submission, deadline, now=time.time, pause=time.sleep):
    require(shared.sha(submission['path']) == submission['sha256'], 'own_accepted_submission')
    while now() < deadline:
        state = shared.read(Path(session['shared_root'])/'STATE.json')
        require(state['config_sha256'] == session['config_sha256'], 'unchanged_barrier_config')
        require(type(state['generation']) is int and session['generation'] <= state['generation'] <= session['generation']+1,
            'no_skipped_shared_generation')
        if state['generation'] == session['generation']+1:
            following = client.prepare(session['shared_root'], session['branch'])
            require(following['generation'] == session['generation']+1, 'exact_next_publication')
            return following
        require(state['checkpoint'] == session['checkpoint'], 'same_checkpoint_while_waiting')
        pause(min(1, max(0, deadline-now())))
    raise TimeoutError('shared_barrier_original_native_deadline_no_retry')


def loaded_receipt(root, engine, phase):
    mounted = math.mounted(root, phase)
    return dict(mounted, adapter=engine.verify_base().document(), optimizer=None,
        **client.binding(engine.session), local_optimizer_steps=0)


def readout(root, binding_path):
    root, binding_path = Path(root), Path(binding_path).resolve(strict=True)
    activation(root)
    require(binding_path.is_relative_to((root/'shared_readout_bindings').resolve()), 'own_pinned_readout_binding')
    binding = shared.read(binding_path)
    session, stage, cycle = binding['session'], binding['stage'], binding['cycle']
    require(session['branch_root'] == str(root) and tuple(binding['resident_process']) != client.native.process_identity(),
        'fresh_readout_process_not_resident')
    require(stage in ('cycle', 'morning_final'), 'no_initial_readout_repetition')
    require(stage != 'morning_final' or math.policy.previous.MORNING <= time.time() < math.HARD, 'original_final_window')
    output = (root/'sealed' if stage == 'morning_final' else root/'readouts')/f'{stage}_{cycle:03d}'
    output.mkdir(parents=True, exist_ok=False)
    expected = 16 if stage == 'morning_final' else 20
    deadline = math.HARD if stage == 'morning_final' else math.NATIVE
    def check(label):
        require(time.time() < deadline, 'readout_original_wall:'+label)
    shared.write(output/'DENOMINATORS.json', dict(planned_native=expected, retries=0, never_rows_or_buffer=True))
    engine = None
    try:
        index = shared.read(root/'CONFIG.json')['index']
        engine = client.load(session, model_dir=math.MODEL, gpu_uuid=math.policy.DEVICES[index], check=check, readout=True)
        shared.write(output/'BEFORE.json', loaded_receipt(root, engine, 'shared_readout_before'))
        tasks = shared.read(root.parent/('sealed/FINAL8.json' if stage == 'morning_final' else 'DEV8.json'))
        def batch(selected, purpose, previous=None, cap=2048):
            prompts = [math.policy.readout_messages(task, purpose, None if previous is None else previous[position])
                for position, task in enumerate(selected)]
            first = math.reserve(root, 'native', len(selected), dict(phase=stage, purpose=purpose,
                split=selected[0]['split'], never_rows_or_buffer=True, **client.binding(session)))
            shared.write(output/f'BATCH_{first:04d}.request.json', dict(prompts=prompts,
                task_ids=[task['id'] for task in selected], cap=cap, started_unix=time.time(),
                parent_free=True, never_rows_or_buffer=True, **client.binding(session)))
            try:
                responses = engine.batch(prompts, cap)
                require(len(responses) == len(selected), 'all_independent_readout_responses')
                for position, (task, response) in enumerate(zip(selected, responses)):
                    shared.write(output/f'CALL_{first+position:04d}.json', dict(task_id=task['id'], split=task['split'],
                        purpose=purpose, response=response, status='COMPLETE', finished_unix=time.time(),
                        parent_free=True, never_rows_or_buffer=True, **client.binding(session)))
                    if purpose == 'open_turn':
                        shared.write(output/f'OPEN_{first+position:04d}.json', dict(
                            observations=math.policy.enact(task, response['raw']), never_rows_or_buffer=True))
                return responses
            except BaseException as error:
                for position, task in enumerate(selected):
                    path = output/f'CALL_{first+position:04d}.json'
                    if not path.exists():
                        shared.write(path, dict(task_id=task['id'], split=task['split'], purpose=purpose,
                            status='FAILED', error=str(error), finished_unix=time.time(),
                            parent_free=True, never_rows_or_buffer=True, **client.binding(session)))
                raise
        answers = batch(tasks, 'held')
        batch(tasks, 'open_turn', answers, cap=1024)
        if stage == 'cycle':
            batch(tasks[:2], 'focused')
            probes = [dict(task, split='PROBE') for task in shared.read(root.parent/'TRAIN.json')[cycle-1]]
            original = shared.read(root/f'cycle{cycle:03d}'/'BOUNDARY.json')['original_responses']
            batch(probes, 'open_turn', original, cap=1024)
        shared.write(output/'AFTER.json', loaded_receipt(root, engine, 'shared_readout_after'))
        shared.write(output/'COMPLETE.json', dict(status='COMPLETE', actual_native=expected, planned_native=expected,
            parent_free=True, never_rows_or_buffer=True, local_optimizer_steps=0, finished_unix=time.time(),
            **client.binding(session)))
    except BaseException as error:
        calls = [shared.read(path) for path in output.glob('CALL_*.json')]
        shared.write(output/'FAILED.json', dict(error=str(error), planned_native=expected,
            attempted_native=len(calls), completed_native=sum(call['status']=='COMPLETE' for call in calls), retries=0))
        raise
    finally:
        if engine is not None:
            shared.write(output/'MOUNTED_FINAL.json', loaded_receipt(root, engine, 'shared_readout_final'))


def dispatch_readout(root, session, cycle, stage):
    binding = root/'shared_readout_bindings'/f'{stage}_{cycle:03d}.json'
    shared.write(binding, dict(session=deepcopy(session), stage=stage, cycle=cycle,
        resident_process=client.native.process_identity(), parent_free=True, never_rows_or_buffer=True))
    with binding.with_suffix('.log').open('x') as log:
        child = subprocess.Popen([sys.executable, '-B', '-m', MODULE, 'readout', '--root', str(root),
            '--binding', str(binding)], cwd=SOURCE, stdin=subprocess.DEVNULL, stdout=log, stderr=subprocess.STDOUT)
        identity = math.common.process_identity(Path('/proc')/str(child.pid))
        shared.write(binding.with_suffix('.process.json'), identity)
        deadline = math.HARD if stage == 'morning_final' else math.NATIVE
        try:
            code = child.wait(timeout=max(.01, deadline-time.time()))
            require(code == 0, 'fresh_shared_readout_failed_no_retry')
        finally:
            if child.poll() is None:
                math.common.stop_owned(child, identity)


def run_cycle(root, engine, cycle, tasks, carry):
    started = time.time()
    collected = client.collect_cycle(root, engine, cycle, tasks, carry)
    output = root/f'cycle{cycle:03d}'
    following = wait_published(engine.session, collected['submission'], math.NATIVE-60)
    mounted = client.reload_at_boundary(engine, following, collected['submission'])
    shared.write(output/'SHARED_SLEEP.json', dict(status='COMPLETE', publication=following['checkpoint'],
        submission=collected['submission'], mounted=mounted, optimizer_owner='F1', local_optimizer_steps=0,
        finished_unix=time.time()))
    dispatch_readout(root, engine.session, cycle, 'cycle')
    shared.write(output/'COMPLETE.json', dict(status='COMPLETE', cycle=cycle, started_unix=started,
        finished_unix=time.time(), counters=shared.read(root/'COUNTERS.json'), label='SHARED_F1_LORA_SLEEP',
        local_optimizer_steps=0, **client.binding(engine.session)))
    math.atomic(root/'PROGRESS.json', dict(cycle=cycle, phase='CYCLE_COMPLETE',
        counters=shared.read(root/'COUNTERS.json'), observed_unix=time.time(), **client.binding(engine.session)))
    return collected['carry']


def resident(root):
    root = Path(root)
    document = activation(root)
    saved = boundary.verify_release(root, document['release'])
    require(saved['next_cycle'] == document['start_cycle'], 'exact_original_cursor')
    if saved['empty_successor']:
        empty = Path(saved['empty_successor'])
        require(empty == root/f"cycle{saved['next_cycle']:03d}" and not list(empty.iterdir()), 'only_empty_unstarted_directory')
        empty.rmdir()
    carry = shared.read(saved['carry']['path'])['own_reflection']
    engine = None
    status = 'FAILED'
    def check(label):
        require(time.time() < math.NATIVE, 'original_native_wall:'+label)
    try:
        session = client.prepare(document['shared_learner']['root'], document['shared_learner']['branch'])
        index = shared.read(root/'CONFIG.json')['index']
        engine = client.load(session, model_dir=math.MODEL, gpu_uuid=math.policy.DEVICES[index], check=check)
        shared.write(root/'SHARED_MODEL_LOADED.json', loaded_receipt(root, engine, 'shared_resident_before'))
        tasks = shared.read(root.parent/'TRAIN.json')
        for cycle in range(saved['next_cycle'], math.policy.CYCLES+1):
            if time.time() >= math.NATIVE-120:
                break
            carry = run_cycle(root, engine, cycle, tasks[cycle-1], carry)
        engine.verify_base()
        while time.time() < math.policy.previous.MORNING:
            time.sleep(min(5, math.policy.previous.MORNING-time.time()))
        dispatch_readout(root, engine.session, 0, 'morning_final')
        status = 'COMPLETE'
    except BaseException as error:
        shared.write(root/'SHARED_FAILED.json', dict(error=str(error), type=type(error).__name__,
            counters=shared.read(root/'COUNTERS.json'), no_retry=True, finished_unix=time.time()))
        raise
    finally:
        if engine is not None:
            shared.write(root/'SHARED_MOUNTED_AFTER.json', loaded_receipt(root, engine, 'shared_resident_after'))
        shared.write(root/'SHARED_RESIDENT_TERMINAL.json', dict(status=status,
            counters=shared.read(root/'COUNTERS.json'), local_optimizer_steps=0, finished_unix=time.time()))


def guard(root):
    root = Path(root)
    document = activation(root)
    boundary.verify_release(root, document['release'])
    with (root/'SHARED_RUNNER.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        require(not (root/'SHARED_LAUNCH.json').exists(), 'no_duplicate_successor')
        index = shared.read(root/'CONFIG.json')['index']
        report = subprocess.run(['sudo', '-n', 'env', 'CUDA_VISIBLE_DEVICES=', 'PYTHONDONTWRITEBYTECODE=1',
            'PYTHONPATH='+str(SOURCE), 'python3', '-B', '-m', MODULE, 'scan', '--root', str(root)],
            capture_output=True, text=True, timeout=90, check=True)
        admission = json.loads(report.stdout)
        shared.write(root/'SHARED_ADMISSION.json', admission)
        require(admission['clear'] and not admission['blocking_reasons'] and admission['scanner_euid'] == 0,
            'strict_full_proc_admission_no_waiver')
        child = identity = None
        status = 'FAILED'
        def interrupted(signum, frame):
            raise SystemExit(128+signum)
        signal.signal(signal.SIGTERM, interrupted)
        signal.signal(signal.SIGINT, interrupted)
        try:
            require(time.time() < math.NATIVE-120, 'original_native_launch_wall')
            with (root/'SHARED_RESIDENT.log').open('x') as log:
                child = subprocess.Popen([sys.executable, '-B', '-m', MODULE, 'resident', '--root', str(root)],
                    cwd=SOURCE, stdout=log, stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL, start_new_session=True,
                    env=dict(os.environ, CUDA_VISIBLE_DEVICES=math.policy.DEVICES[index], PYTHONPATH=str(SOURCE),
                        HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1', PYTHONDONTWRITEBYTECODE='1', OMP_NUM_THREADS='1',
                        MKL_NUM_THREADS='1', TOKENIZERS_PARALLELISM='false'))
                identity = math.common.process_identity(Path('/proc')/str(child.pid))
                shared.write(root/'SHARED_LAUNCH.json', dict(identity=identity, uuid=math.policy.DEVICES[index],
                    activation_sha256=shared.sha(root/'SHARED_ACTIVATION.json'), started_unix=time.time()))
                require(child.wait(timeout=max(.01, math.HARD-time.time())) == 0, 'shared_native_failed_no_retry')
                status = 'COMPLETE'
        finally:
            if child is not None and child.poll() is None:
                math.common.stop_owned(child, identity)
            for path in (root/'shared_readout_bindings').glob('*.process.json'):
                expected = shared.read(path)
                directory = Path('/proc')/str(expected['pid'])
                if directory.exists() and math.common.process_identity(directory) == expected:
                    descriptor = os.pidfd_open(expected['pid'])
                    try:
                        require(math.common.process_identity(directory) == expected and expected['uid'] == os.getuid(),
                            'only_owned_shared_readout_cleanup')
                        signal.pidfd_send_signal(descriptor, signal.SIGTERM)
                    finally:
                        os.close(descriptor)
            shared.write(root/'SHARED_TERMINAL.json', dict(status=status, finished_unix=time.time(),
                local_optimizer_steps=0, no_retry=True))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('phase', choices=('activate', 'guard', 'resident', 'readout', 'scan'))
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--binding', type=Path)
    parser.add_argument('--release', type=Path)
    parser.add_argument('--shared-root', type=Path)
    parser.add_argument('--adoption', type=Path)
    parser.add_argument('--authorization', type=Path)
    args = parser.parse_args()
    if args.phase == 'activate':
        activate(args.root, args.release, args.shared_root, args.adoption, args.authorization)
    elif args.phase == 'scan':
        ready.branch_for(args.root)
        print(json.dumps(math.scan(args.root.parent, shared.read(args.root/'CONFIG.json')['index'])))
    elif args.phase == 'readout':
        readout(args.root, args.binding)
    elif args.phase == 'resident':
        resident(args.root)
    else:
        guard(args.root)
