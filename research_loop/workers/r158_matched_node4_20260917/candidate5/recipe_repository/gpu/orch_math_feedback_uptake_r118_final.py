"""Separate math FINAL allocation; CPU waiter and one fresh evaluation process."""

import argparse
from copy import deepcopy
import fcntl
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time


START = 1789491600
END = START + 1200
MODULE = 'gpu.orch_math_feedback_uptake_r118_final'
SOURCE = Path(__file__).resolve().parents[1]
ORIGINAL = Path('/localhome/local-rohing/orch_math_feedback_uptake_r115_f2_20260915_attempt1')
COMMON = Path('/localhome/local-rohing/orch_r116_shared_node5_20260915_attempt1')
OUTPUT = Path('/localhome/local-rohing/orch_math_feedback_uptake_r118_final_20260915_attempt2')
MEMBERS = {'F2': (1, 'GPU-7fc4e5b2-060c-ada8-8f91-3fe262c3573c'),
           'A2': (5, 'GPU-65595cff-c6c2-c798-bc62-427168079270')}
FINAL_IDS = ['MATH_PIPELINE_L2_20260915_ATTEMPT1_R113_F2_FINAL_C0_E' + str(number)
             for number in (0, 1, 1003, 3, 4, 5, 2008, 7)]
FINAL_FILE_SHA = '1e5548fd989fa79f95a316a0943cae0a92de4e479d5021a0005defa2c00c6b8e'
FINAL_SET_SHA = 'b3642ffe0e6e501ca805e323d28cdf1f159296872b78f798f65180417dc044ee'
COMMON_SHA = 'e5ac72af0d88e4481174f853fbf3951294278b1c9f62c88080f7d4b816cceb51'
LINEAGE = {'CONFIG.json': COMMON_SHA,
           'ADOPTION.json': '6dfc7dcd59e86648478a13852ff740701930f36499c92bef1178d3e645dcf7b5',
           'INITIALIZED.json': 'd4e2c87e97bcfccb639d332d996f9f239023bbaa19f9312ce95d30f3f0aecff6'}
DECODER = dict(max_new_tokens=2048, context_limit=16384, do_sample=False, num_beams=1,
               use_cache=True, repetition_penalty=1.0, seed=0, independent_batch_size=8,
               truncate_input=False, reflection_guard=False)


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def read(path):
    return json.loads(Path(path).read_bytes())


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'),
                                   allow_nan=False).encode()).hexdigest()


def ref(path):
    return dict(path=str(Path(path).resolve(strict=True)), sha256=sha(path))


def bound(reference):
    require(sha(reference['path']) == reference['sha256'], 'immutable_reference')
    return read(reference['path'])


def write(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    temporary = path.with_name(path.name + '.' + str(os.getpid()) + '.pending')
    with temporary.open('x') as stream:
        json.dump(value, stream, indent=2, sort_keys=True, allow_nan=False)
        stream.write('\n')
        stream.flush()
        os.fsync(stream.fileno())
    try:
        os.link(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def module_from(reference):
    require(sha(reference['path']) == reference['sha256'], 'pinned_selector_source')
    spec = importlib.util.spec_from_file_location('math_final_selection', reference['path'])
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def window(plan, now):
    require(plan['start_unix'] == START and plan['end_unix'] == min(END, plan['lease_end_unix']-21600),
            'separate_absolute_window')
    require(START <= now < plan['end_unix'], 'FINAL_clock_gate')


def source_check(plan):
    require(plan['source_root'] == str(SOURCE), 'immutable_runtime_root')
    manifest = bound(plan['source_manifest'])
    require(all(sha(SOURCE/name) == expected for name, expected in manifest.items()), 'frozen_source_closure')
    tests = bound(plan['tests'])
    require(tests['passed'] is True and tests['cuda_initialized'] is False
            and tests['source_manifest_sha256'] == plan['source_manifest']['sha256'], 'source_bound_CPU_gate')


def prepare(branch, selector, lease_reference, previous_evaluation, drain_reference):
    from gpu import orch_math_feedback_uptake_r118_final_drain as drain
    require(branch in MEMBERS and time.time() < START, 'prospective_owned_math_only')
    physical, uuid = MEMBERS[branch]
    original = ORIGINAL/f'lane{physical}'
    root = OUTPUT/f'lane{physical}'
    require(not root.exists(), 'unique_new_evaluation_root')
    previous = bound(previous_evaluation)
    drain_plan = drain.plan_check(drain_reference)
    require(previous['original_root'] == str(original) and previous['branch'] == branch
            and drain_plan['previous_evaluation_plan'] == previous_evaluation, 'exact_previous_eval_and_drain_binding')
    require(not (Path(previous['root'])/'LEDGER.json').exists()
            and not (Path(previous['root'])/'NATIVE_CLAIM.json').exists(), 'no_charged_prior_evaluation_replay')
    ready = read(ORIGINAL/'READY.json')
    roster = read(ORIGINAL/'sealed/READOUT_ROSTER.json')
    require(ready['data_files']['sealed/FINAL8.json'] == FINAL_FILE_SHA
            and roster['final_ids'] == FINAL_IDS and roster['final_set_sha256'] == FINAL_SET_SHA,
            'metadata_only_original_FINAL_inventory')
    lease_end = bound(lease_reference)['bounds']['lease_end_unix']
    require(min(END, lease_end-21600) > START, 'lease_six_hour_margin')
    config = read(COMMON/'CONFIG.json')
    require(sha(COMMON/'CONFIG.json') == COMMON_SHA and config['branches'][branch]['root'] == str(original),
            'registered_common_math_branch')
    require(set(FINAL_IDS).issubset(config['excluded_ids'])
            and not set(FINAL_IDS).intersection(config['branches'][branch]['train_ids']), 'FINAL_excluded_from_shared_rows')
    selector_ref = ref(selector)
    require(Path(selector).name == 'orch_r118_final_selection.py', 'Main_canonical_selector_only')
    old = read(original/'ACTIVATION.json')
    require(old['native_deadline_unix'] == START-60 and old['hard_deadline_unix'] == START+120,
            'old_lifetime_not_extended')
    predecessors = [read(original/name)['identity'] for name in
                    ('SHARED_LAUNCH.json', 'R118_SHARED_ADMISSION_REPAIR_LAUNCH.json')]
    plan = dict(schema='R118_MATH_FINAL_EVALUATION_V1', branch=branch, physical=physical, uuid=uuid,
        root=str(root), original_root=str(original), common_root=str(COMMON), common_config=ref(COMMON/'CONFIG.json'),
        start_unix=START, end_unix=min(END, lease_end-21600), lease_end_unix=lease_end,
        lease_reference=lease_reference, native_cap=8, parent_cap=0, optimizer_steps=0, experience_rows=0,
        attached_open_calls=0, max_output_token_ids=16384, never_rows_or_buffer=True,
        task_ids=FINAL_IDS, task_ids_sha256=digest(FINAL_IDS), final_file_sha256=FINAL_FILE_SHA,
        final_set_sha256=FINAL_SET_SHA, decoder=DECODER, selector_source=selector_ref,
        selection_path=str(COMMON/'FINAL_SELECTION.json'), source_root=str(SOURCE),
        source_manifest=ref(SOURCE/'FINAL_SOURCE_MANIFEST.json'), tests=ref(SOURCE/'FINAL_CPU_TESTS.json'),
        predecessor_refs={name: ref(original/name) for name in
                          ('CONFIG.json', 'ACTIVATION.json', 'SHARED_ACTIVATION.json', 'SHARED_LAUNCH.json',
                           'R118_SHARED_ADMISSION_REPAIR_LAUNCH.json')},
        predecessors=predecessors, original_bounds=old,
        previous_evaluation_plan=previous_evaluation, drain_plan=drain_reference,
        authorization='Main 13:07 FINAL allocation plus13:41 deadline-only clean boundary drain', prepared_unix=time.time())
    require(all(plan[name] == previous[name] for name in ('branch', 'physical', 'uuid', 'original_root',
        'start_unix', 'end_unix', 'native_cap', 'parent_cap', 'task_ids', 'decoder', 'predecessor_refs',
        'predecessors', 'original_bounds', 'lease_reference')), 'no_bounds_or_predecessor_ref_reset')
    source_check(plan)
    root.mkdir(parents=True, mode=0o700)
    write(root/'PLAN.json', plan)
    write(root/'DENOMINATORS.json', dict(planned_native=8, parent=0, optimizer_steps=0,
                                        training_rows=0, retries=0, original_ledger_unchanged=True))
    return ref(root/'PLAN.json')


def validate(root):
    root = Path(root)
    plan = read(root/'PLAN.json')
    require(plan['schema'] == 'R118_MATH_FINAL_EVALUATION_V1' and plan['branch'] in MEMBERS, 'math_eval_only_schema')
    physical, uuid = MEMBERS[plan['branch']]
    require(plan['physical'] == physical and plan['uuid'] == uuid and root == OUTPUT/f'lane{physical}'
            and plan['root'] == str(root) and plan['original_root'] == str(ORIGINAL/f'lane{physical}'), 'exact_roots_UUID')
    require(plan['native_cap'] == 8 and plan['parent_cap'] == plan['optimizer_steps'] == plan['experience_rows'] == 0
            and plan['attached_open_calls'] == 0 and plan['never_rows_or_buffer'] is True
            and plan['max_output_token_ids'] == 16384, 'new_ledger_fixed_eval_ceiling')
    require(plan['task_ids'] == FINAL_IDS and plan['task_ids_sha256'] == digest(FINAL_IDS)
            and plan['final_file_sha256'] == FINAL_FILE_SHA and plan['final_set_sha256'] == FINAL_SET_SHA
            and plan['decoder'] == DECODER, 'exact_original_inventory_decoder')
    require(plan['common_root'] == str(COMMON) and plan['selection_path'] == str(COMMON/'FINAL_SELECTION.json')
            and plan['common_config']['sha256'] == COMMON_SHA, 'one_Main_selection')
    require(bound(plan['lease_reference'])['bounds']['lease_end_unix'] == plan['lease_end_unix'], 'verified_lease')
    bound(plan['common_config'])
    for reference in plan['predecessor_refs'].values():
        bound(reference)
    prior = bound(plan['previous_evaluation_plan'])
    require(all(plan[name] == prior[name] for name in ('branch', 'physical', 'uuid', 'original_root',
        'start_unix', 'end_unix', 'native_cap', 'parent_cap', 'task_ids', 'decoder', 'predecessor_refs',
        'predecessors', 'original_bounds', 'lease_reference')), 'same_original_eval_caps_and_predecessors')
    source_check(plan)
    return plan


def prior_attempts(original, now):
    require(now >= START, 'no_early_FINAL_attempt_inspection')
    original = Path(original)
    paths = list((original/'sealed').glob('morning_final_*'))
    paths += list((original/'shared_readout_bindings').glob('morning_final_*'))
    for path in (original/'reservations').glob('native_*.json'):
        if read(path).get('metadata', {}).get('phase') == 'morning_final':
            paths.append(path)
    return sorted(set(str(path) for path in paths))


def same_process(expected):
    directory = Path('/proc')/str(expected['pid'])
    try:
        fields = (directory/'stat').read_text().rsplit(')', 1)[1].split()
        uid = directory.stat().st_uid
        boot = Path('/proc/sys/kernel/random/boot_id').read_text().strip()
        return uid == expected['uid'] and boot == expected['boot_id'] and str(fields[19]) == str(expected['start_ticks'])
    except (FileNotFoundError, ProcessLookupError):
        return False


def release(plan):
    from gpu import orch_math_feedback_uptake_r118_final_drain as drain
    return drain.validate_release(plan['drain_plan'])


def selection(plan, now):
    window(plan, now)
    selector = module_from(plan['selector_source'])
    common = Path(plan['common_root'])
    selected = selector.validate_selection(common, config_sha256=LINEAGE['CONFIG.json'],
        initialized_sha256=LINEAGE['INITIALIZED.json'], adoption_sha256=LINEAGE['ADOPTION.json'], clock=lambda: now)
    require(selected['selected_unix'] <= now, 'no_future_selection')
    return selected


def materialize(plan, now):
    window(plan, now)
    path = ORIGINAL/'sealed/FINAL8.json'
    require(sha(path) == plan['final_file_sha256'], 'sealed_FINAL_file_changed')
    tasks = read(path)
    require([task['id'] for task in tasks] == plan['task_ids'] and digest(tasks) == plan['final_set_sha256']
            and all(task['split'] == 'FINAL' for task in tasks), 'exact_sealed_eight')
    return tasks


def reserve(root, plan, tasks):
    require([task['id'] for task in tasks] == plan['task_ids'] and len(tasks) == plan['native_cap'], 'exact_denominator')
    write(Path(root)/'LEDGER.json', dict(native=8, parent=0, optimizer_steps=0, rows=0, attempts=1,
        task_ids=plan['task_ids'], charged_unix=time.time(), no_retry=True, charged_before_dispatch=True))


def capture(root, plan, tasks, checkpoint, batch, messages):
    root = Path(root)
    window(plan, time.time())
    prompts = [messages(task, 'held') for task in tasks]
    reserve(root, plan, tasks)
    for number, (task, prompt) in enumerate(zip(tasks, prompts), 1):
        write(root/f'CALL_{number:04d}.request.json', dict(task_id=task['id'], split='FINAL', phase='morning_final',
            messages=prompt, decoder=plan['decoder'], checkpoint=checkpoint, started_unix=time.time(),
            never_rows_or_buffer=True, parent_present=False))
    try:
        responses = batch(prompts, 2048)
        require(len(responses) == 8, 'complete_batch_denominator')
        for number, response in enumerate(responses, 1):
            write(root/f'CALL_{number:04d}.raw.json', dict(response=response, finished_unix=time.time()))
        for number, (task, prompt, response) in enumerate(zip(tasks, prompts, responses), 1):
            require(response['messages'] == prompt and type(response['raw']) is str
                    and type(response['token_ids']) is list and len(response['token_ids']) <= 2048
                    and not response['input_truncated'], 'full_native_response_before_any_parser')
            write(root/f'CALL_{number:04d}.json', dict(status='COMPLETE', task_id=task['id'], split='FINAL',
                response=response, request=ref(root/f'CALL_{number:04d}.request.json'),
                checkpoint=checkpoint, finished_unix=time.time(), never_rows_or_buffer=True))
        return responses
    except BaseException as error:
        for number, task in enumerate(tasks, 1):
            if not (root/f'CALL_{number:04d}.json').exists():
                write(root/f'CALL_{number:04d}.json', dict(status='FAILED', task_id=task['id'], split='FINAL',
                    error_type=type(error).__name__, finished_unix=time.time(), retry=False,
                    raw_preserved=(root/f'CALL_{number:04d}.raw.json').exists()))
        raise


def native(root):
    from gpu import orch_math_feedback_uptake_r117_shared as client
    plan = validate(root)
    window(plan, time.time())
    require(not prior_attempts(plan['original_root'], time.time()), 'no_prior_morning_attempt')
    release(plan)
    chosen = selection(plan, time.time())
    require(ref(plan['selection_path']) == read(root/'SELECTED.json')['reference'], 'one_immutable_selection_for_dispatch')
    write(root/'SELECTION_USED.json', dict(selection=chosen, reference=ref(plan['selection_path'])))
    checkpoint = client.shared.checked_checkpoint(chosen['checkpoint'])
    saved = read(checkpoint['path'])
    identity = client.native.bridge.AdapterIdentity.from_document(saved['adapter'])
    require(saved['complete'] is True and identity.base_sha256 == client.math.direct.BASE_SHA, 'committed_original_base_adapter')
    stage = client.native.bridge.StageBinding(plan['branch'], client.native.bridge.ARMS[0],
        chosen['generation'], 'sealed_readout', identity, False, True, COMMON_SHA)
    def check(label):
        window(plan, time.time())
        require(time.time() < plan['end_unix']-20, 'native_cleanup_margin')
    mounted = client.math.mounted(Path(plan['original_root']), 'separate_FINAL_before_load')
    loaded = client.native.load_stage(stage, model_dir=client.math.MODEL, device='cuda:0', gpu_uuid=plan['uuid'],
        context=client.native.StageContext(), check=check, predecessor_processes=(tuple(saved['source_process']),))
    class Readout:
        def __getattr__(self, name):
            return getattr(loaded.engine, name)
        def verify_base(self):
            require(loaded.optimizer is None, 'no_eval_optimizer')
            return loaded.verify_unchanged()
    engine = Readout()
    def receipt(phase):
        observed = engine.verify_base().document()
        return dict(client.math.mounted(Path(plan['original_root']), phase), adapter=observed, optimizer=None,
                    selected_checkpoint=checkpoint, shared_generation=chosen['generation'], parent_present=False)
    try:
        write(root/'BEFORE.json', dict(receipt('separate_FINAL_mounted'), pre_load=mounted))
        tasks = materialize(plan, time.time())
        responses = capture(root, plan, tasks, checkpoint,
            lambda prompts, cap: client.math.Engine.batch(engine, prompts, cap), client.math.policy.readout_messages)
        write(root/'AFTER.json', receipt('separate_FINAL_after'))
        write(root/'COMPLETE.json', dict(status='COMPLETE', native=8, parent=0, optimizer_steps=0,
            output_token_ids=sum(len(response['token_ids']) for response in responses),
            checkpoint=checkpoint, shared_generation=chosen['generation'], finished_unix=time.time(),
            comparison='SYSTEMS_ON_ONE_SHARED_LEARNER_NOT_INDEPENDENT_MODELS', raw_node_only=True))
    finally:
        write(root/'MOUNTED_FINAL.json', receipt('separate_FINAL_final'))


def denominators(root):
    calls = [read(path) for path in Path(root).glob('CALL_*.json')
             if not path.name.endswith(('.request.json', '.raw.json'))]
    charged = read(Path(root)/'LEDGER.json')['native'] if (Path(root)/'LEDGER.json').exists() else 0
    complete = sum(call.get('status') == 'COMPLETE' for call in calls)
    return dict(planned_native=8, charged_native=charged, completed_native=complete,
                failed_or_partial_native=charged-complete, unattempted_native=8-charged, parent=0, optimizer_steps=0)


def scheduler(root):
    from gpu import orch_math_feedback_uptake_r117_shared as client
    plan = validate(root)
    from gpu import orch_math_feedback_uptake_r118_final_drain as drain
    predecessor = bound(plan['previous_evaluation_plan'])
    previous_root = Path(predecessor['root'])
    previous_timer = read(previous_root/'SCHEDULED.json')['identity']
    child = child_identity = None
    with (root/'SCHEDULER.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        write(root/'SCHEDULED.json', dict(plan=ref(root/'PLAN.json'), identity=client.math.common.process_identity(
            Path('/proc')/str(os.getpid())), status='ARMED_NOT_EVALUATED', observed_unix=time.time(), GPU_allocated=False))
        def interrupted(signum, frame):
            raise SystemExit(128+signum)
        signal.signal(signal.SIGTERM, interrupted)
        signal.signal(signal.SIGINT, interrupted)
        status = 'NOT_STARTED'
        try:
            while time.time() < START:
                time.sleep(min(15, START-time.time()))
            require(not same_process(previous_timer) and not (previous_root/'LEDGER.json').exists()
                    and not (previous_root/'NATIVE_CLAIM.json').exists(), 'old_CPU_timer_retired_zero_evaluation_calls')
            drain_plan = drain.plan_check(plan['drain_plan'])
            if not (Path(drain_plan['output'])/'RELEASED.json').exists():
                status = 'NOT_RUN'
                write(root/'NOT_RUN.json', dict(status=status, reason='NO_VERIFIED_DEADLINE_BOUNDARY_RELEASE',
                    drain_plan=plan['drain_plan'], no_new_model_calls=True, observed_unix=time.time()))
                return
            while time.time() < plan['end_unix']-60:
                attempts = prior_attempts(plan['original_root'], time.time())
                if attempts:
                    write(root/'SKIPPED_PRIOR_FINAL.json', dict(paths=attempts, status='NO_REPLAY', observed_unix=time.time()))
                    status = 'PRIOR_FINAL_NO_REPLAY'
                    return
                released = release(plan)
                if not Path(plan['selection_path']).exists():
                    time.sleep(5)
                    continue
                chosen = selection(plan, time.time())
                write(root/'RELEASE.json', released)
                write(root/'SELECTED.json', dict(selection=chosen, reference=ref(plan['selection_path'])))
                break
            else:
                raise TimeoutError('release_or_selection_unavailable_within_eval_window')
            result = subprocess.run(['sudo', '-n', 'env', 'CUDA_VISIBLE_DEVICES=', 'PYTHONDONTWRITEBYTECODE=1',
                'PYTHONPATH='+str(SOURCE), 'python3', '-B', '-m', MODULE, 'scan', '--root', str(root)],
                capture_output=True, text=True, timeout=min(90, plan['end_unix']-time.time()), check=True)
            report = json.loads(result.stdout)
            write(root/'ADMISSION.json', report)
            require(report['clear'] and report['scanner_euid'] == 0 and not report['blocking_reasons'], 'strict_full_proc_admission')
            release(plan)
            require(not prior_attempts(plan['original_root'], time.time()), 'no_dispatch_race_with_old_FINAL')
            window(plan, time.time())
            write(root/'NATIVE_CLAIM.json', dict(attempt=1, retry=False, claimed_unix=time.time()))
            with (root/'NATIVE.log').open('x') as log:
                child = subprocess.Popen([client.math.PYTHON, '-B', '-m', MODULE, 'native', '--root', str(root)],
                    cwd=SOURCE, stdin=subprocess.DEVNULL, stdout=log, stderr=subprocess.STDOUT, start_new_session=True,
                    env=dict(os.environ, CUDA_VISIBLE_DEVICES=plan['uuid'], PYTHONPATH=str(SOURCE),
                        PYTHONDONTWRITEBYTECODE='1', HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1',
                        OMP_NUM_THREADS='1', MKL_NUM_THREADS='1', TOKENIZERS_PARALLELISM='false'))
                for observation in range(100):
                    child_identity = client.math.common.process_identity(Path('/proc')/str(child.pid))
                    command = (Path('/proc')/str(child.pid)/'cmdline').read_bytes().split(b'\0')
                    if MODULE.encode() in command and b'native' in command:
                        break
                    time.sleep(.01)
                else:
                    raise ValueError('owned_exec_identity_not_stable')
                write(root/'LAUNCH.json', dict(identity=child_identity, uuid=plan['uuid'], started_unix=time.time()))
                require(child.wait(timeout=max(.01, plan['end_unix']-20-time.time())) == 0, 'fresh_FINAL_failed_no_retry')
                require((root/'COMPLETE.json').exists(), 'native_completion_required')
                status = 'COMPLETE'
        except BaseException as error:
            status = 'FAILED'
            write(root/'FAILED.json', dict(error_type=type(error).__name__, reason=str(error), finished_unix=time.time()))
            raise
        finally:
            if child is not None and child.poll() is None:
                client.math.common.stop_owned(child, child_identity)
            write(root/'TERMINAL.json', dict(status=status, **denominators(root), finished_unix=time.time(),
                                           foreign_signals=0, original_lifetime_unchanged=True))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('phase', choices=('prepare', 'schedule', 'scan', 'native'))
    parser.add_argument('--branch', choices=tuple(MEMBERS))
    parser.add_argument('--root', type=Path)
    parser.add_argument('--selector', type=Path)
    parser.add_argument('--lease-reference', type=Path)
    parser.add_argument('--previous-evaluation', type=Path)
    parser.add_argument('--drain-plan', type=Path)
    args = parser.parse_args()
    if args.phase == 'prepare':
        print(json.dumps(prepare(args.branch, args.selector, read(args.lease_reference),
                                ref(args.previous_evaluation), ref(args.drain_plan))))
    elif args.phase == 'schedule':
        scheduler(args.root)
    elif args.phase == 'native':
        native(args.root)
    else:
        from gpu import orch_math_feedback_uptake_r115_native as math
        plan = validate(args.root)
        window(plan, time.time())
        print(json.dumps(math.scan(ORIGINAL, plan['physical'])))


if __name__ == '__main__':
    main()
