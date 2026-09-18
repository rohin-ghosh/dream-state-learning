"""Separate R109 lifetime; reuse strict node3 scanner and tested BASE engine."""

import argparse
from datetime import datetime, timezone
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

from gpu import orch_math_feedback_uptake_r108_run as previous
from gpu import orch_math_feedback_uptake_r109_native as driver
from organism_v6 import orch_math_feedback_uptake_r109 as policy


ROOT = Path('/localhome/local-rohing/orch_math_feedback_uptake_r109_20260915_attempt1')
LIBRARY = previous.LIBRARY
common = previous.common
require = policy.require
HARD = datetime(2026, 9, 15, 17, 2, tzinfo=timezone.utc).timestamp()
NATIVE = HARD - 180
PRIOR = LIBRARY.parent / 'orch_math_feedback_uptake_r108_20260915_attempt1'


def bind():
    previous.policy = policy
    previous.bind()


def scan(root, index):
    bind()
    if os.geteuid() == 0:
        return previous.scanner.scan(index, root / 'SERVICE_IDENTITY.json')
    result = subprocess.run(['sudo', '-n', 'env', 'CUDA_VISIBLE_DEVICES=', 'PYTHONDONTWRITEBYTECODE=1',
        'PYTHONPATH=' + str(LIBRARY / 'source'), 'python3', '-B', str(Path(__file__)), 'scan',
        '--root', str(root), '--index', str(index)], capture_output=True, text=True, timeout=90, check=True)
    report = json.loads(result.stdout)
    require(report['gpu']['index'] == index and report['gpu']['uuid'] == policy.DEVICES[index]
        and report['host_sha256'] == policy.HOST_SHA and 'device_minor' in report, 'pinned_full_identity')
    return report


def validate(root):
    bind()
    require(root == ROOT and root.resolve() == root, 'exact_r109_root')
    ready = common.read(root / 'FAMILY_READY.json')
    for path, digest in ready['source_files'].items():
        require(common.sha(path) == digest, 'immutable_r109_source')
    require(common.sha(LIBRARY / 'SOURCE_SHA256.json') == ready['library_manifest_sha256'], 'library_binding')
    previous.existing.verify_sources(LIBRARY / 'source', LIBRARY / 'SOURCE_SHA256.json')
    return dict(bundle=previous.existing.BUNDLE, model_dir=previous.existing.MODEL)


def prepare(root):
    bind()
    require(root == ROOT and os.environ.get('CUDA_VISIBLE_DEVICES') == '', 'cpu_prepare_only')
    source = Path(__file__).parents[1]
    tests = common.read(source / 'CPU_RESULT_R109.json')
    require(tests['passed'] and tests['tests'] >= 10, 'focused_native_cpu_gate')
    registry_path = PRIOR / 'R108_EXCLUSION_REGISTRY.json'
    registry = common.read(registry_path)
    identifiers, questions = set(registry['excluded_ids']), set(registry['excluded_question_sha256'])
    inputs = {str(registry_path): common.sha(registry_path)}
    paths = sorted(LIBRARY.parent.glob('orch_math_feedback_uptake*/campaign*/COHORT.json'))
    paths += sorted((root / 'EXTERNAL_MANIFESTS').glob('*.json'))
    for path in paths:
        document = common.read(path)
        extra_ids, extra_questions = previous.reuse.exclusions.exclusions([document])
        identifiers.update(extra_ids)
        questions.update(policy.previous.add_declared_question_hashes([document], extra_questions))
        inputs[str(path)] = common.sha(path)
    require(len(identifiers) >= 2966 and len(questions) >= 2958, 'inherited_complete_pools')
    tokenizer = previous.reuse.seam.native.source.native.load_local_tokenizer(previous.existing.MODEL)
    before = previous.reuse.seam.portable.verify_base_files(previous.existing.BUNDLE, previous.existing.MODEL,
        expected_manifest_sha256=previous.node_limits.BUNDLE_SHA)
    require(before['expected_base_sha256'] == policy.base.BASE_SHA, 'cached_base_identity')
    inventory = previous.reuse.source_inventory(source)
    family = dict(schema=policy.SCHEMA, source_files=inventory, source_manifests=inputs,
        library_manifest_sha256=common.sha(LIBRARY / 'SOURCE_SHA256.json'),
        cpu_tests=tests, base_sha256=policy.base.BASE_SHA, native_deadline_unix=NATIVE,
        hard_deadline_unix=HARD, lease_safe_before='2026-09-19',
        new_native_cap=4032, new_parent_cap=773, max_gpu_hours=24,
        previous_campaign_cap_native=2274, previous_campaign_cap_parent=66,
        aggregate_native_cap=6306, aggregate_parent_cap=839, no_old_counter_reset=True)
    common.write(root / 'FAMILY_READY.json', family)
    for index in policy.DEVICES:
        lane = root / f'campaign_node3_style{index}'
        require(not lane.exists(), 'no_prepare_overwrite')
        lane.mkdir()
        (lane / 'r109_parent_queue').mkdir()
        cohort = policy.make_cohort(index, identifiers, questions)
        for group in cohort['train'] + cohort['held']:
            for task in group:
                prompt = policy.messages(task, purpose='experience' if task['split'] == 'TRAIN' else 'held')
                require(len(tokenizer.apply_chat_template(prompt, tokenize=True, add_generation_prompt=True, return_dict=False)) < 2048, 'prompt_tokenizer_bound')
                identifiers.add(task['id'])
                questions.add(task['question_sha256'])
        common.write(lane / 'COHORT.json', cohort)
        common.write(lane / 'READY.json', dict(index=index, uuid=policy.DEVICES[index], budget=policy.budget(index),
            family_ready_sha256=common.sha(root / 'FAMILY_READY.json'), cohort_sha256=common.sha(lane / 'COHORT.json'),
            provider_files=common.read(source / 'PROVIDER_BINDINGS_R109.json'), base_files=before))
    common.write(root / 'R109_EXCLUSION_REGISTRY.json', dict(excluded_ids=sorted(identifiers),
        excluded_question_sha256=sorted(questions), source_manifests=inputs,
        inherited_scope_contract=registry.get('inherited_scope_contract'), concurrent_unseen_pools_not_claimed=True))


def statistics(lane, index, activation):
    calls = [common.read(path) for path in sorted(lane.glob('cycle*/*/CALL_*.json'))]
    completed = [call for call in calls if 'response' in call]
    parents = list(lane.glob('cycle*/experience/PARENT_T*.json'))
    counter = dict(index=index, observed_unix=time.time(), cadence=policy.CADENCES[index],
        native_reserved=len(calls), native_completed=len(completed), failed=len([call for call in calls if 'error' in call]),
        episodes_completed=sum(call['purpose'] == 'revision' for call in completed),
        train_segments_completed=sum(call['purpose'] != 'held' for call in completed),
        child_tokens=sum(len(call['response']['token_ids']) for call in completed),
        actual_parents=len(parents), triples=len(list(lane.glob('cycle*/experience/TRIPLE_*.json'))),
        configured_class_exposures={label: len(parents) for label in policy.CLASSES},
        actual_intervention_class_counts='UNKNOWN_AUTHOR_REVIEW', semantic_behavior_change='UNKNOWN_AUTHOR_REVIEW',
        terminal_reasons={label: sum(bool(call['response'].get(label)) for call in completed) for label in ('terminal', 'truncated')},
        repetition_stops=sum(bool(call['response'].get('reflection_guard', {}).get('early_stopped')) for call in completed),
        phase_timings=[dict(path=str(path.relative_to(lane)), seconds=common.read(path)['finished_unix'] - common.read(path)['started_unix'])
            for path in sorted(lane.glob('cycle*/*/COMPLETE.json'))])
    common.write(lane / 'PROGRESS.json', counter)
    hour = int((time.time() - activation['started_unix']) // 3600)
    common.write(lane / f'HOURLY_{hour:02d}.json', counter)


def guard(root, index, expected):
    validate(root)
    lane = root / f'campaign_node3_style{index}'
    require(common.sha(lane / 'READY.json') == expected, 'ready_binding')
    ready = common.read(lane / 'READY.json')
    require(ready['family_ready_sha256'] == common.sha(root / 'FAMILY_READY.json'), 'family_binding')
    publication = common.read(lane / 'PUBLICATION.json')
    require(publication['ready_sha256'] == expected and publication['entry_sha256'] == common.sha(root / 'ALLOCATION.md'), 'pre_gpu_publication')
    started = time.time()
    activation = dict(started_unix=started, native_deadline_unix=min(NATIVE, started + 28620),
        hard_deadline_unix=min(HARD, started + 28800), index=index,
        guardian=common.process_identity(Path('/proc') / str(os.getpid())), ready_sha256=expected,
        new_lifetime=True, previous_ledgers_untouched=True)
    with (lane / 'ACTIVATION.json').open('x') as stream:
        json.dump(activation, stream, indent=2)
    child = identity = log = None
    status = 'FAILED'
    def interrupted(signum, frame):
        raise SystemExit(128 + signum)
    signal.signal(signal.SIGTERM, interrupted)
    signal.signal(signal.SIGINT, interrupted)
    try:
        for cycle in range(1, policy.CYCLES + 1):
            for phase in ('experience', 'readout'):
                if time.time() >= activation['native_deadline_unix'] - 600:
                    status = 'BOUNDED_DEADLINE_PARTIAL'
                    return
                output = lane / f'cycle{cycle}' / phase
                require(not output.exists(), 'no_native_retry')
                admitted = False
                until = min(time.time() + 600, activation['native_deadline_unix'])
                attempt = 0
                while time.time() < until:
                    try:
                        report = scan(root, index)
                        common.write(lane / f'ADMISSION_C{cycle}_{phase}_{attempt}.json', report)
                        admitted = report['clear'] and report['scanner_euid'] == 0 and not report['blocking_reasons']
                    except subprocess.CalledProcessError as error:
                        common.write(lane / f'ADMISSION_ERROR_C{cycle}_{phase}_{attempt}.json', dict(error=str(error), no_waiver=True))
                    if admitted:
                        break
                    attempt += 1
                    time.sleep(3)
                require(admitted, 'strict_full_proc_admission')
                log = (lane / f'C{cycle}_{phase}.log').open('x')
                child = subprocess.Popen([previous.existing.PYTHON, '-B', str(Path(__file__)), 'native',
                    '--root', str(root), '--index', str(index), '--cycle', str(cycle), '--native-phase', phase],
                    cwd=LIBRARY / 'source', start_new_session=True, stdout=log, stderr=subprocess.STDOUT,
                    env=dict(os.environ, CUDA_VISIBLE_DEVICES=policy.DEVICES[index], PYTHONPATH=str(LIBRARY / 'source'),
                        HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1', TOKENIZERS_PARALLELISM='false',
                        OMP_NUM_THREADS='1', MKL_NUM_THREADS='1', PYTHONDONTWRITEBYTECODE='1'))
                identity = common.process_identity(Path('/proc') / str(child.pid))
                common.write(lane / f'LAUNCH_C{cycle}_{phase}.json', dict(identity=identity, uuid=policy.DEVICES[index], started_unix=time.time()))
                next_stats = time.time()
                while child.poll() is None:
                    require(time.time() < activation['hard_deadline_unix'] - 120, 'hard_deadline')
                    if time.time() >= next_stats:
                        statistics(lane, index, activation)
                        next_stats = time.time() + 60
                    time.sleep(2)
                require(child.returncode == 0, 'native_failure_no_retry')
                complete, after = common.read(output / 'COMPLETE.json'), common.read(output / 'AFTER.json')
                require(complete['status'] == 'COMPLETE' and after['actual_mounted_base_verified'], 'actual_complete_after')
                require(complete['process'] == [identity['boot_id'], identity['pid'], int(identity['start_ticks'])] == after['process'], 'actual_process')
                require(len(list(output.glob('CALL_*.json'))) == (6 if phase == 'experience' else 8), 'denominators')
                common.write(lane / f'COMPLETE_C{cycle}_{phase}.json', dict(complete_sha256=common.sha(output / 'COMPLETE.json'),
                    after_sha256=common.sha(output / 'AFTER.json'), finished_unix=time.time()))
                statistics(lane, index, activation)
                log.close()
                child = identity = log = None
        status = 'COMPLETE'
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
    parser.add_argument('phase', choices=('prepare', 'service', 'scan', 'guard', 'native'))
    parser.add_argument('--root', type=Path, default=ROOT)
    parser.add_argument('--index', type=int, choices=(0, 1, 2))
    parser.add_argument('--cycle', type=int)
    parser.add_argument('--native-phase', choices=('experience', 'readout'))
    parser.add_argument('--ready-sha256')
    args = parser.parse_args()
    if args.phase == 'service':
        bind()
        previous.scanner.pinned.service(args.root / 'SERVICE_IDENTITY.json')
    elif args.phase == 'scan':
        print(json.dumps(scan(args.root, args.index)))
    elif args.phase == 'prepare':
        prepare(args.root)
    elif args.phase == 'guard':
        guard(args.root, args.index, args.ready_sha256)
    else:
        driver.run(args.root / f'campaign_node3_style{args.index}', args.index, args.cycle, args.native_phase,
            previous.response_contract.engine_class(previous.direct.Engine), validate)
