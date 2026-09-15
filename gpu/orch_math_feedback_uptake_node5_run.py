"""One admitted resident BASE process per R110 lane, bounded by original lease."""

import argparse
import fcntl
import json
import os
from pathlib import Path
import signal
import subprocess
import time

import gpu
import organism_v6

gpu.__path__.insert(0, str(Path(__file__).parent))
organism_v6.__path__.insert(0, str(Path(__file__).parents[1] / 'organism_v6'))

from gpu import orch_math_feedback_uptake_r109_run as machinery
from gpu import orch_math_feedback_uptake_r110_native as driver
from organism_v6 import orch_math_feedback_uptake_node5 as policy


ROOT = Path('/localhome/local-rohing/orch_math_feedback_uptake_node5_20260915_attempt1')
LIBRARY = ROOT
common, require = machinery.common, policy.require
HARD, NATIVE = machinery.HARD, machinery.NATIVE
PRINCIPLES_SHA = 'b7f4d6baef8158b41533d15acf0f7c924b4bc1e875a30d6ca31f874b5e1c589d'


def configure(root):
    require(root == ROOT and root.resolve() == root, 'exact_node5_root')
    machinery.ROOT, machinery.policy, machinery.LIBRARY = ROOT, policy, ROOT
    machinery.previous.LIBRARY = ROOT
    machinery.previous.existing.LEASE_CUTOFF = 1789617840.0
    driver.policy = policy
    machinery.bind()
    require(Path('/proc/sys/kernel/random/boot_id').read_text().strip() ==
        '2c05ffec-1b4c-472f-9688-2a37543a6f4a', 'pinned_node5_boot')
    policy.bind_principles(root / 'PARENTING_PRINCIPLES.md', PRINCIPLES_SHA)


def validate(root):
    configure(root)
    ready = common.read(root / 'FAMILY_READY.json')
    for name, digest in ready['source_files'].items():
        require(common.sha(name) == digest, 'immutable_node5_source')
    require(common.sha(root / 'PARENTING_PRINCIPLES.md') == PRINCIPLES_SHA, 'principles_identity')
    return dict(bundle=machinery.previous.existing.BUNDLE, model_dir=machinery.previous.existing.MODEL)


def scan(root, index):
    configure(root)
    if os.geteuid() == 0:
        return machinery.previous.scanner.scan(index, root / 'SERVICE_IDENTITY.json')
    result = subprocess.run(['sudo', '-n', 'env', 'CUDA_VISIBLE_DEVICES=', 'PYTHONDONTWRITEBYTECODE=1',
        'PYTHONPATH=' + str(LIBRARY / 'source'), 'python3', '-B', str(Path(__file__)), 'scan',
        '--root', str(root), '--index', str(index)], capture_output=True, text=True, timeout=90, check=True)
    report = json.loads(result.stdout)
    require(report['gpu']['index'] == index and report['gpu']['uuid'] == policy.DEVICES[index]
        and report['host_sha256'] == policy.HOST_SHA and 'device_minor' in report, 'pinned_full_identity')
    return report


def prepare(root):
    configure(root)
    require(os.environ.get('CUDA_VISIBLE_DEVICES') == '', 'cpu_only_prepare')
    require(not (root / 'FAMILY_READY.json').exists(), 'no_prepare_overwrite')
    source = Path(__file__).parents[1]
    tests = common.read(source / 'CPU_RESULT_NODE5.json')
    require(tests['passed'] and tests['node5_tests'] >= 8 and tests['reused_tests'] >= 52, 'actual_native_cpu_gate')
    registry_path = root / 'INHERITED_EXCLUSION_REGISTRY.json'
    registry = common.read(registry_path)
    identifiers, questions = set(registry['excluded_ids']), set(registry['excluded_question_sha256'])
    require(len(identifiers) >= 5846 and len(questions) >= 5838, 'complete_inherited_r110_pools')
    tokenizer = machinery.previous.reuse.seam.native.source.native.load_local_tokenizer(machinery.previous.existing.MODEL)
    before = machinery.previous.reuse.seam.portable.verify_base_files(machinery.previous.existing.BUNDLE,
        machinery.previous.existing.MODEL, expected_manifest_sha256=machinery.previous.node_limits.BUNDLE_SHA)
    require(before['expected_base_sha256'] == policy.base.BASE_SHA, 'genuine_cached_base')
    family = dict(schema=policy.SCHEMA, source_files=machinery.previous.reuse.source_inventory(source),
        principles_sha256=PRINCIPLES_SHA, cpu_tests=tests, resident_cycles=True,
        inherited_registry_sha256=common.sha(registry_path), base_files=before,
        new_native_cap=3072, new_parent_cap=1056, max_gpu_hours=16,
        native_deadline_unix=NATIVE, hard_deadline_unix=HARD, lease_cutoff_unix=1789617840.0,
        separate_additive_node5_ledger=True, no_counter_reset=True,
        earlier_ledgers_untouched=True, no_optimizer=True, no_weight_learning_claim=True)
    require(HARD < family['lease_cutoff_unix'] - 21600, 'lease_margin')
    common.write(root / 'FAMILY_READY.json', family)
    for index in policy.DEVICES:
        lane = root / f'campaign_node5_style{index}'
        lane.mkdir()
        (lane / 'r110_parent_queue').mkdir()
        cohort = policy.make_cohort(index, identifiers, questions)
        for group in cohort['train'] + cohort['held']:
            for task in group:
                prompt = policy.messages(task, purpose='experience' if task['split'] == 'TRAIN' else 'held')
                require(len(tokenizer.apply_chat_template(prompt, tokenize=True, add_generation_prompt=True,
                    return_dict=False)) < 2048, 'actual_uncropped_prompt_bound')
                identifiers.add(task['id'])
                questions.add(task['question_sha256'])
        common.write(lane / 'COHORT.json', cohort)
        common.write(lane / 'READY.json', dict(index=index, uuid=policy.DEVICES[index], budget=policy.budget(index),
            family_ready_sha256=common.sha(root / 'FAMILY_READY.json'), principles_sha256=PRINCIPLES_SHA,
            cohort_sha256=common.sha(lane / 'COHORT.json'), base_files=before,
            provider_files=common.read(source / 'PROVIDER_BINDINGS_NODE5.json')))
    common.write(root / 'NODE5_EXCLUSION_REGISTRY.json', dict(excluded_ids=sorted(identifiers),
        excluded_question_sha256=sorted(questions), inherited_registry_sha256=common.sha(registry_path),
        inherited_inputs=registry.get('source_manifests'), concurrent_unseen_pools_not_claimed=True))


def statistics(lane, index, activation):
    with (lane / 'STATISTICS.lock').open('a') as stream:
        fcntl.flock(stream, fcntl.LOCK_EX)
        _statistics(lane, index, activation)


def _statistics(lane, index, activation):
    machinery.statistics(lane, index, activation)
    progress = common.read(lane / 'PROGRESS.json')
    completed = [common.read(path) for path in lane.glob('cycle*/experience/CALL_*.json')]
    progress['episodes_completed'] = sum(call['purpose'] == 'revision' and not call.get('context_distillation')
        and 'response' in call for call in completed)
    progress['metacognition_segments_completed'] = sum(bool(call.get('context_distillation')) and 'response' in call for call in completed)
    progress['mandatory_dialogue_parents'] = sum((common.read(path)['segment'] - 1) % 8 + 1 == 7
        for path in lane.glob('cycle*/experience/PARENT_T*.json'))
    progress['reflection_boundaries'] = len(list(lane.glob('cycle*/experience/REFLECTION_BOUNDARY.json')))
    progress['principles_sha256'] = PRINCIPLES_SHA
    progress['effort_allocation_self_capability_learning_system'] = 'UNKNOWN_AUTHOR_REVIEW'
    progress['literal_check_field_is_legacy_continuation_label_not_prescribed_check'] = True
    progress['weight_writes'] = 0
    common.write(lane / 'PROGRESS.json', progress)
    common.write(lane / f"HOURLY_{int((time.time()-activation['started_unix'])//3600):02d}.json", progress)


def resident(root, index):
    validate(root)
    lane = root / f'campaign_node5_style{index}'
    activation = common.read(lane / 'ACTIVATION.json')
    cached = []
    original = machinery.previous.response_contract.engine_class(machinery.previous.direct.Engine)
    guarded = driver.reflection.engine_class(original)
    def factory(model_dir, tokenizer, device, check):
        if not cached:
            cached.append(guarded(model_dir, tokenizer, device=device, check=check))
        return cached[0]
    original_wrapper = driver.reflection.engine_class
    driver.reflection.engine_class = lambda engine: engine
    status = 'COMPLETE'
    try:
        for cycle in range(1, policy.CYCLES + 1):
            for phase in ('experience', 'readout'):
                if time.time() >= activation['native_deadline_unix'] - 600:
                    status = 'BOUNDED_DEADLINE_PARTIAL'
                    return
                driver.run(lane, index, cycle, phase, factory, validate)
                output = lane / f'cycle{cycle}' / phase
                complete, after = common.read(output / 'COMPLETE.json'), common.read(output / 'AFTER.json')
                require(complete['process'] == after['process'] == list(driver.reuse.driver.seam.native.process_identity()), 'resident_process_boundary')
                require(complete['status'] == 'COMPLETE' and after['actual_mounted_base_verified'], 'verified_boundary')
                require(len(list(output.glob('CALL_*.json'))) == 8, 'exact_phase_denominators')
                common.write(lane / f'COMPLETE_C{cycle}_{phase}.json', dict(complete_sha256=common.sha(output / 'COMPLETE.json'),
                    after_sha256=common.sha(output / 'AFTER.json'), finished_unix=time.time()))
                statistics(lane, index, activation)
    except BaseException as error:
        status = 'FAILED'
        common.write(lane / 'RESIDENT_FAILED.json', dict(error=str(error), type=type(error).__name__, finished_unix=time.time()))
        raise
    finally:
        driver.reflection.engine_class = original_wrapper
        common.write(lane / 'RESIDENT_TERMINAL.json', dict(status=status, loads=len(cached),
            process=driver.reuse.driver.seam.native.process_identity(), finished_unix=time.time(), no_repeated_admission=True))


def guard(root, index, expected):
    validate(root)
    lane = root / f'campaign_node5_style{index}'
    require(common.sha(lane / 'READY.json') == expected, 'ready_hash')
    ready, publication = common.read(lane / 'READY.json'), common.read(lane / 'PUBLICATION.json')
    require(ready['family_ready_sha256'] == common.sha(root / 'FAMILY_READY.json'), 'family_hash')
    require(publication['ready_sha256'] == expected and publication['entry_sha256'] == common.sha(root / 'ALLOCATION.md'), 'publication')
    started = time.time()
    activation = dict(started_unix=started, native_deadline_unix=min(NATIVE, started+28620),
        hard_deadline_unix=min(HARD, started+28800), index=index, ready_sha256=expected,
        guardian=common.process_identity(Path('/proc') / str(os.getpid())), resident=True, earlier_ledgers_untouched=True)
    with (lane / 'ACTIVATION.json').open('x') as stream:
        json.dump(activation, stream, indent=2)
    child = identity = log = None
    status = 'FAILED'
    def interrupted(signum, frame):
        raise SystemExit(128 + signum)
    signal.signal(signal.SIGTERM, interrupted)
    signal.signal(signal.SIGINT, interrupted)
    try:
        until = min(started+600, activation['native_deadline_unix'])
        admitted = False
        attempt = 0
        while time.time() < until:
            try:
                report = scan(root, index)
                common.write(lane / f'ADMISSION_{attempt:03d}.json', report)
                admitted = report['clear'] and report['scanner_euid'] == 0 and not report['blocking_reasons']
            except subprocess.CalledProcessError as error:
                common.write(lane / f'ADMISSION_ERROR_{attempt:03d}.json', dict(error=str(error), no_waiver=True))
            if admitted:
                break
            attempt += 1
            time.sleep(3)
        require(admitted, 'strict_initial_full_proc_admission')
        log = (lane / 'RESIDENT.log').open('x')
        child = subprocess.Popen([machinery.previous.existing.PYTHON, '-B', str(Path(__file__)), 'resident',
            '--root', str(root), '--index', str(index)], cwd=LIBRARY/'source', start_new_session=True,
            stdout=log, stderr=subprocess.STDOUT, env=dict(os.environ, CUDA_VISIBLE_DEVICES=policy.DEVICES[index],
                PYTHONPATH=str(LIBRARY/'source'), HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1', TOKENIZERS_PARALLELISM='false',
                OMP_NUM_THREADS='1', MKL_NUM_THREADS='1', PYTHONDONTWRITEBYTECODE='1'))
        identity = common.process_identity(Path('/proc') / str(child.pid))
        common.write(lane / 'LAUNCH.json', dict(identity=identity, uuid=policy.DEVICES[index], started_unix=time.time()))
        next_stats = time.time()+60
        while child.poll() is None:
            require(time.time() < activation['hard_deadline_unix'] - 120, 'hard_deadline')
            if time.time() >= next_stats:
                statistics(lane, index, activation)
                next_stats = time.time()+60
            time.sleep(2)
        require(child.returncode == 0, 'native_failure_no_retry')
        terminal = common.read(lane / 'RESIDENT_TERMINAL.json')
        require(terminal['process'] == [identity['boot_id'], identity['pid'], int(identity['start_ticks'])]
            and terminal['loads'] == 1, 'one_actual_resident_model')
        status = terminal['status']
    except BaseException as error:
        common.write(lane / 'GUARDIAN_FAILED.json', dict(type=type(error).__name__, error=str(error), finished_unix=time.time()))
        raise
    finally:
        if child is not None:
            common.stop_owned(child, identity)
        if log is not None:
            log.close()
        common.write(lane / 'TERMINAL.json', dict(status=status, finished_unix=time.time(), peer_processes_signalled=0))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('phase', choices=('prepare', 'service', 'scan', 'guard', 'resident'))
    parser.add_argument('--root', type=Path, default=ROOT)
    parser.add_argument('--index', type=int, choices=(2, 3))
    parser.add_argument('--ready-sha256')
    args = parser.parse_args()
    if args.phase == 'service':
        configure(args.root)
        machinery.previous.scanner.pinned.service(args.root / 'SERVICE_IDENTITY.json')
    elif args.phase == 'scan':
        print(json.dumps(scan(args.root, args.index)))
    elif args.phase == 'prepare':
        prepare(args.root)
    elif args.phase == 'guard':
        guard(args.root, args.index, args.ready_sha256)
    else:
        resident(args.root, args.index)
