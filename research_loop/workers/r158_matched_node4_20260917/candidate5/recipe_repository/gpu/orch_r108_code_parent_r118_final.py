"""Separate, cutoff-gated CODE FINAL evaluation; never changes a living ledger."""

import argparse
from copy import deepcopy
import fcntl
import os
from pathlib import Path
import signal
import subprocess
import sys
import time

from gpu import orch_r108_code_parent_r118_activate as activation
from gpu import orch_r108_code_parent_r118_final_release as release
from gpu import orch_r118_final_selection as selector


client = activation.client
run = client.run
coordinator = client.coordinator
require = coordinator.require
SOURCE_ROOT = Path(__file__).resolve().parents[1]
MODULE = 'gpu.orch_r108_code_parent_r118_final'
CUTOFF = 1789491600
EVAL_END = CUTOFF + 1200
TASK_IDS = tuple(f'R113_F3_FINAL_{index:04d}' for index in range(1, 9))
DECODER = dict(max_new_tokens=2048, context_tokens=16384, do_sample=False,
    num_beams=1, no_repeat_ngram_size=4, use_cache=True)
ROUTES = dict(parent=False, head=False, exchange=False, sleep=False, optimizer=False,
    teacher_target=False, evaluation_only=True)


def ref(path):
    return dict(path=str(path), sha256=coordinator.sha(path))


def bound(reference):
    path = Path(reference['path'])
    require(coordinator.sha(path) == reference['sha256'], 'immutable_reference_changed')
    return coordinator.read(path)


def source_check(plan):
    require(Path(plan['source_root']).resolve() == SOURCE_ROOT, 'actual_frozen_source_root')
    manifest = bound(plan['source_manifest'])
    require(all(coordinator.sha(SOURCE_ROOT / name) == expected for name, expected in manifest.items()),
        'frozen_source_changed')
    cpu = bound(plan['cpu_receipt'])
    require(cpu['passed'] is True and cpu['cuda_initialized'] is False
        and cpu['source_manifest_sha256'] == plan['source_manifest']['sha256'], 'own_bound_CPU_tests')


def prior_final_attempts(original):
    original = Path(original)
    paths = set((original / 'readouts').glob('C*_FINAL'))
    paths.update((original / 'reservations').glob('R*_FINAL_FINAL_*.json'))
    paths.update((original / 'reservations').glob('*FINAL_MORNING*'))
    return sorted(str(path) for path in paths)


def prepare(root, original, binding_path, source=SOURCE_ROOT):
    root, original, source = Path(root), Path(original), Path(source)
    require(not root.exists(), 'new_separate_eval_root_required')
    original_plan = coordinator.read(original / 'PLAN.json')
    physical = original_plan['physical']
    require(physical in (2, 6), 'own_CODE_slots_only')
    require(original_plan['gpu_uuid'] == activation.original.DEVICES[physical], 'original_exact_UUID')
    adopted = coordinator.read(original / 'SHARED_ACTIVATION.json')
    require(adopted['predecessor_plan_sha256'] == coordinator.sha(original / 'PLAN.json'),
        'original_PLAN_preserved')
    common = Path(adopted['shared_learner']['root'])
    require(Path(binding_path) == common / 'FINAL_SELECTION.json', 'Main_canonical_selection_only')
    deadline = min(EVAL_END, original_plan['lease_end_unix'] - 21600)
    require(deadline > CUTOFF, 'verified_lease_must_cover_eval')
    plan = dict(schema='R118_CODE_FINAL_ALLOCATION_V1', branch={2:'F3', 6:'A3'}[physical],
        physical=physical, gpu_uuid=original_plan['gpu_uuid'], original_root=str(original),
        original_plan=ref(original / 'PLAN.json'), activation=ref(original / 'SHARED_ACTIVATION.json'),
        cohort=ref(original / 'COHORT.json'), common_root=str(common),
        common_config_sha256=adopted['shared_learner']['config_sha256'],
        common_initialized_sha256=coordinator.sha(common / 'INITIALIZED.json'),
        common_adoption_sha256=coordinator.sha(common / 'ADOPTION.json'),
        main_binding_path=str(binding_path), cutoff_unix=CUTOFF, hard_deadline_unix=deadline,
        lease_end_unix=original_plan['lease_end_unix'], native_cap=8, parent_cap=0,
        max_output_token_ids=16384, optimizer_steps=0, experience_rows=0,
        task_ids=list(TASK_IDS), task_ids_sha256=coordinator.digest(list(TASK_IDS)),
        decoder=DECODER, routes=ROUTES, source_root=str(source.resolve()),
        source_manifest=ref(source.parent / 'SOURCE_SHA256.json'),
        cpu_receipt=ref(source.parent / 'CPU_TESTS.json'), prepared_unix=time.time(),
        prior_final_attempts=prior_final_attempts(original), original_caps_unchanged=True)
    source_check(plan)
    root.mkdir(parents=True)
    coordinator.write(root / 'PLAN.json', plan)
    release.prepare(root, original)
    return plan


def validate_plan(root):
    plan = coordinator.read(Path(root) / 'PLAN.json')
    require(plan['schema'] == 'R118_CODE_FINAL_ALLOCATION_V1', 'separate_eval_allocation')
    require(plan['cutoff_unix'] == CUTOFF and plan['hard_deadline_unix'] ==
        min(EVAL_END, plan['lease_end_unix'] - 21600), 'fixed_eval_only_window')
    require(plan['native_cap'] == 8 and plan['parent_cap'] == 0 and plan['optimizer_steps'] == 0
        and plan['experience_rows'] == 0 and plan['max_output_token_ids'] == 16384,
        'exact_eight_call_zero_training_allocation')
    require(plan['decoder'] == DECODER and plan['routes'] == ROUTES
        and plan['task_ids'] == list(TASK_IDS)
        and plan['task_ids_sha256'] == coordinator.digest(list(TASK_IDS)), 'fixed_FINAL_contract')
    original = bound(plan['original_plan'])
    adopted = bound(plan['activation'])
    require(original['physical'] == plan['physical'] and original['gpu_uuid'] == plan['gpu_uuid']
        and original['lease_end_unix'] == plan['lease_end_unix'], 'original_slot_and_lease')
    require(adopted['shared_learner']['branch'] == plan['branch']
        and adopted['shared_learner']['config_sha256'] == plan['common_config_sha256'], 'shared_branch_binding')
    require(coordinator.sha(plan['cohort']['path']) == plan['cohort']['sha256'], 'original_cohort_bytes')
    source_check(plan)
    return plan


def window(plan, now):
    require(CUTOFF <= now < plan['hard_deadline_unix'] - 5, 'FINAL_clock_gate')


def validate_binding(plan, binding_path, now):
    window(plan, now)
    require(str(binding_path) == plan['main_binding_path'], 'one_Main_binding_for_all_eight')
    common = Path(plan['common_root'])
    require(Path(binding_path) == common / 'FINAL_SELECTION.json', 'Main_canonical_selection_only')
    selected = selector.validate_selection(common, config_sha256=plan['common_config_sha256'],
        initialized_sha256=plan['common_initialized_sha256'], adoption_sha256=plan['common_adoption_sha256'],
        clock=lambda: now)
    require(selected['evaluation_deadline_unix'] >= plan['hard_deadline_unix'], 'bounded_canonical_eval_window')
    return dict(state=bound(selected['state_reference']), selection=selected)


def final_tasks(plan, now):
    window(plan, now)
    cohort = bound(plan['cohort'])
    tasks = cohort['FINAL']
    require(len(tasks) == 8 and [task['task_id'] for task in tasks] == list(TASK_IDS), 'exact_original_FINAL8')
    for task in tasks:
        require(task['split'] == 'FINAL' and task['content_sha256'] ==
            run.policy.digest({key:value for key, value in task.items() if key != 'content_sha256'}),
            'original_task_content_hash')
    return tasks


def load_engine(plan, binding, check):
    checkpoint = coordinator.checked_checkpoint(binding['state']['checkpoint'])
    document = coordinator.read(checkpoint['path'])
    identity = client.native.bridge.AdapterIdentity.from_document(document['adapter'])
    stage = client.native.bridge.StageBinding('R118_CODE_FINAL_' + plan['branch'],
        client.native.bridge.ARMS[0], binding['state']['generation'], 'sealed_readout',
        identity, False, True, coordinator.digest(plan))
    original = bound(plan['original_plan'])
    loaded = client.native.load_stage(stage, model_dir=original['model_dir'], device='cuda:0',
        gpu_uuid=plan['gpu_uuid'], context=client.native.StageContext(private_guidance=()),
        check=check, predecessor_processes=(tuple(document['source_process']),))
    require(loaded.optimizer is None and loaded.observed == identity, 'readonly_exact_shared_adapter')
    return client.Engine(loaded)


def verify_engine(engine, binding):
    engine.verify_base()
    identity = client.native.bridge.AdapterIdentity.from_document(
        coordinator.read(binding['state']['checkpoint']['path'])['adapter'])
    require(client.native.observe_adapter(engine.underlying, identity) == identity,
        'adapter_unchanged_after_FINAL')
    coordinator.checked_checkpoint(binding['state']['checkpoint'])


def evaluate(root, plan, binding, *, engine_factory=load_engine, clock=time.time):
    root = Path(root)
    window(plan, clock())
    require(not prior_final_attempts(plan['original_root']), 'prior_FINAL_attempt_never_repeated')
    (root / 'ATTEMPT_ONCE').mkdir()
    tasks = final_tasks(plan, clock())
    rows = []
    for index, task in enumerate(tasks):
        path = root / 'reservations' / f'FINAL_{index:02d}.json'
        row = dict(id=path.stem, task_id=task['task_id'], task_sha256=task['content_sha256'],
            split='FINAL', phase='readout', kind='NATIVE', status='STARTED',
            started_unix=clock(), routes=deepcopy(ROUTES), requested_generation_cap=2048,
            shared_generation=binding['state']['generation'],
            shared_checkpoint_sha256=binding['state']['checkpoint']['path_sha256'],
            main_binding=ref(plan['main_binding_path']), retry=False)
        coordinator.write(path, row)
        rows.append((path, row))

    def check(phase):
        window(plan, clock())
        require(os.environ.get('CUDA_VISIBLE_DEVICES') == plan['gpu_uuid'], 'exact_eval_CVD')

    try:
        engine = engine_factory(plan, binding, check)
        check('before_FINAL_batch')
        messages = [run.policy.previous.messages(task, 'readout') for task in tasks]
        responses = engine.generate_batch(messages, max_new_tokens=2048)
        coordinator.write(root / 'NATIVE_BATCH_RESPONSE.json', dict(responses=responses, routes=ROUTES))
        require(len(responses) == 8, 'all_eight_results_required')
        for (path, row), response in zip(rows, responses):
            row['response'] = response
            coordinator.write(path, row, replace=True)
        for index, ((path, row), response) in enumerate(zip(rows, responses)):
            require(response['messages'] == messages[index], 'exact_parent_free_prompt_capture')
            require(len(response['token_ids']) <= 2048 and response['effective_generation_cap'] == 2048
                and not response['input_truncated'], 'original_decoder_capture')
            row.update(status='COMPLETE', response=response, finished_unix=clock())
            coordinator.write(path, row, replace=True)
        verify_engine(engine, binding)
        source_check(plan)
        outcomes = [dict(task_id=task['task_id'], outcome=run.environment.score(task, row['response']['raw']))
            for task, (path, row) in zip(tasks, rows)]
        coordinator.write(root / 'SEALED_OUTCOMES.json', dict(outcomes=outcomes, routes=ROUTES))
        coordinator.write(root / 'COMPLETE.json', dict(completed_unix=clock(), native_calls=8,
            completed_calls=8, child_tokens=sum(len(row['response']['token_ids']) for path, row in rows),
            fresh_process=True, parent_calls=0, optimizer_steps=0, experience_rows=0,
            main_binding=ref(plan['main_binding_path']), checkpoint=binding['state']['checkpoint'],
            old_ledger_changed=False, shared_pair_not_independent_models=True))
    except Exception as error:
        for path, row in rows:
            if row['status'] == 'STARTED':
                row.update(status='FAILED', error_type=type(error).__name__, finished_unix=clock())
                coordinator.write(path, row, replace=True)
        coordinator.write(root / 'FAILED.json', dict(error_type=type(error).__name__,
            finished_unix=clock(), retry=False, original_artifacts_preserved=True))
        raise


def native(root):
    plan = validate_plan(root)
    release.validate_release(root)
    selected = coordinator.read(Path(root) / 'BOUND_MAIN.json')
    require(selected['path'] == plan['main_binding_path'], 'scheduler_selected_common_binding')
    bound(selected)
    binding = validate_binding(plan, Path(plan['main_binding_path']), time.time())
    require(os.environ.get('CUDA_VISIBLE_DEVICES') == plan['gpu_uuid'], 'exact_eval_CVD')
    try:
        evaluate(root, plan, binding)
        bound(selected)
    finally:
        coordinator.write(Path(root) / 'TERMINAL.json', dict(finished_unix=time.time(),
            completed=(Path(root) / 'COMPLETE.json').exists(), parent_calls=0, optimizer_steps=0))


def run_child(root, plan):
    with (root / 'NATIVE.log').open('x') as output:
        process = subprocess.Popen([sys.executable, '-B', '-m', MODULE, 'native', '--root', str(root)],
            cwd=SOURCE_ROOT, env=dict(os.environ, CUDA_VISIBLE_DEVICES=plan['gpu_uuid'],
                PYTHONPATH=str(SOURCE_ROOT), HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1',
                OMP_NUM_THREADS='1', MKL_NUM_THREADS='1'), stdin=subprocess.DEVNULL,
            stdout=output, stderr=subprocess.STDOUT, start_new_session=True)
        identity = activation.original.scanner.pinned.identity(Path('/proc') / str(process.pid))
        coordinator.write(root / 'LAUNCH.json', dict(identity=identity, started_unix=time.time(),
            plan_sha256=coordinator.sha(root / 'PLAN.json'), main_binding=ref(plan['main_binding_path'])))
        while process.poll() is None and time.time() < plan['hard_deadline_unix'] - 5:
            time.sleep(1)
        if process.poll() is None:
            require(activation.original.scanner.pinned.identity(Path('/proc') / str(process.pid)) == identity,
                'exact_owned_eval_process_before_stop')
            os.killpg(process.pid, signal.SIGTERM)
            try:
                process.wait(timeout=4)
            except subprocess.TimeoutExpired:
                require(activation.original.scanner.pinned.identity(Path('/proc') / str(process.pid)) == identity,
                    'exact_owned_eval_process_before_kill')
                os.killpg(process.pid, signal.SIGKILL)
                process.wait(timeout=2)
        coordinator.write(root / 'GUARD_TERMINAL.json', dict(returncode=process.returncode,
            finished_unix=time.time(), original_lives_signalled=False))


def schedule(root):
    root = Path(root)
    require(os.environ.get('CUDA_VISIBLE_DEVICES') == '', 'CPU_scheduler_only')
    plan = validate_plan(root)
    activation.original.bind(plan['physical'])
    (root / 'SCHEDULER_ONCE').mkdir()
    coordinator.write(root / 'SCHEDULER_STARTED.json', dict(pid=os.getpid(), started_unix=time.time(),
        cutoff_unix=CUTOFF, hard_deadline_unix=plan['hard_deadline_unix'], no_GPU_calls_before_cutoff=True))
    if release.wait_release(root) is None:
        coordinator.write(root / 'NOT_LAUNCHED.json', dict(reason='NO_ACTUAL_PREDECESSOR_RELEASE',
            native_calls=0, observed_unix=time.time()))
        return
    attempt = 0
    while time.time() < plan['hard_deadline_unix'] - 30:
        if time.time() < CUTOFF or not Path(plan['main_binding_path']).exists():
            time.sleep(min(30, max(1, CUTOFF - time.time())))
            continue
        validate_binding(plan, Path(plan['main_binding_path']), time.time())
        previous = prior_final_attempts(plan['original_root'])
        if previous:
            coordinator.write(root / 'SKIPPED.json', dict(reason='PRIOR_FINAL_ATTEMPT_PRESERVED',
                paths=previous, native_calls=0, observed_unix=time.time()))
            return
        lock_path = Path('/tmp') / ('orch_r115_f3_' + plan['gpu_uuid'] + '.lock')
        with lock_path.open('a') as lock:
            try:
                fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError:
                time.sleep(15)
                continue
            snapshot = activation.scan(Path(plan['original_root']))
            coordinator.write(root / 'admission' / f'SCAN_{attempt:04d}.json', snapshot)
            attempt += 1
            if not activation.admitted(snapshot, plan):
                time.sleep(15)
                continue
            require(not prior_final_attempts(plan['original_root']), 'no_concurrent_original_FINAL')
            release.validate_release(root)
            validate_plan(root)
            validate_binding(plan, Path(plan['main_binding_path']), time.time())
            coordinator.write(root / 'ADMISSION.json', snapshot)
            coordinator.write(root / 'BOUND_MAIN.json', ref(plan['main_binding_path']))
            run_child(root, plan)
            return
    coordinator.write(root / 'NOT_LAUNCHED.json', dict(reason='EVAL_WINDOW_EXPIRED', native_calls=0,
        observed_unix=time.time(), original_lives_signalled=False))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('entry', choices=('prepare', 'schedule', 'native'))
    parser.add_argument('--root', required=True, type=Path)
    parser.add_argument('--original-root', type=Path)
    parser.add_argument('--binding', type=Path)
    args = parser.parse_args()
    if args.entry == 'prepare':
        require(args.original_root is not None and args.binding is not None, 'explicit_original_and_Main_binding')
        prepare(args.root, args.original_root, args.binding)
    elif args.entry == 'schedule':
        schedule(args.root)
    else:
        native(args.root)
