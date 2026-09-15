"""CPU preparation and finite, strict-admission supervision for one learned life."""

import argparse
import json
import math
import os
from pathlib import Path
import subprocess
import time
from types import SimpleNamespace

from gpu import orch_r110_guided_run as run
from gpu import orch_rich_hot_a100_minor_scan as admission
from organism_v6 import orch_r107_capability as capability


read, write, sha = run.read, run.write, run.sha
require = run.policy.require
PYTHON = '/localhome/local-rohing/v2/venv/bin/python'


def bind_scanner():
    admission.pinned.policy = SimpleNamespace(DEVICES={7: run.UUID}, HOST_SHA=run.HOST_SHA,
        require=require, allocation=lambda index: require(index == 7, 'only_allocated_physical7'))


def scan(root):
    require(root == run.ROOT, 'exact_campaign')
    service = root / 'SERVICE_IDENTITY.json'
    if os.geteuid() != 0:
        command = ['sudo', '-n', 'env', 'CUDA_VISIBLE_DEVICES=', 'PYTHONDONTWRITEBYTECODE=1',
            'PYTHONPATH=' + str(run.SOURCE_ROOT), 'python3', '-B', '-m',
            'gpu.orch_r110_guided_supervisor', 'scan', '--root', str(root)]
        return json.loads(subprocess.run(command, capture_output=True, text=True, timeout=90, check=True).stdout)
    bind_scanner()
    from gpu import orch_r110_admission
    return orch_r110_admission.scan(7, service)


def cohort(registry):
    require(registry['excluded_ids'] and registry['excluded_question_sha256'],
        'nonempty_complete_exclusion_registry')
    seen_ids = set(registry['excluded_ids'])
    seen_questions = set(registry['excluded_question_sha256'])
    seen_ids.update(task['id'] for task in capability.tasks())
    seen_questions.update(run.policy.text_sha(task['prompt']) for task in capability.tasks())
    seen_ids.update(task['id'] for task in run.verified_anchors.policy.tasks())
    seen_questions.update(run.policy.text_sha(task['prompt']) for task in run.verified_anchors.policy.tasks())
    groups = dict(train=[], held=[])
    for cycle in range(1, run.policy.CYCLES + 1):
        for split, count, destination in [('TRAIN', 2, groups['train']), ('HELD', 8, groups['held'])]:
            group = []
            for position in range(count):
                for nonce in range(1000):
                    task = run.policy.history.source.make_task('R110_GUIDED_' + split, cycle, position + nonce * 1000)
                    task['split'] = split
                    if task['id'] not in seen_ids and task['question_sha256'] not in seen_questions:
                        seen_ids.add(task['id'])
                        seen_questions.add(task['question_sha256'])
                        group.append(task)
                        break
                else:
                    raise ValueError('fresh_cohort_exhausted')
            destination.append(group)
    return dict(groups, exclusions_sha256=run.policy.digest(registry),
        capability_suite_sha256=capability.digest(capability.tasks()))


def prepare(root, initial_path, registry_path, cpu_result):
    require(root == run.ROOT and root.resolve() == root and run.common.host_identity() == run.HOST_SHA,
        'exact_native_root_host')
    require(os.environ.get('CUDA_VISIBLE_DEVICES') == '' and not (root / 'PLAN.json').exists(), 'fresh_cpu_only_prepare')
    initial = read(initial_path)
    run.seed.validate(initial)
    registry = read(registry_path)
    tests = read(cpu_result)
    require(tests['passed'] is True and tests['failed'] == 0 and tests['skipped'] == 0,
        'complete_native_cpu_tests_required')
    sources = read(root / 'SOURCE_SHA256.json')
    require(sources and 'gpu/orch_r110_guided_supervisor.py' in sources, 'source_snapshot_required')
    for name, expected in sources.items():
        relative = Path(name)
        require(not relative.is_absolute() and '..' not in relative.parts
            and sha(run.SOURCE_ROOT / relative) == expected, 'source_snapshot_changed')
    selected = cohort(registry)
    tokenizer = run.native.source.native.load_local_tokenizer(initial['model_dir'])
    for group in selected['train']:
        for task in group:
            tokens = tokenizer.apply_chat_template(run.policy.messages(task, 'experience'), tokenize=True,
                add_generation_prompt=True, return_dict=False)
            require(0 < len(tokens) + 2048 < run.policy.CONTEXT, 'complete_original_context')
    write(root / 'INITIAL.json', initial)
    write(root / 'EXCLUSIONS.json', registry)
    write(root / 'COHORT.json', selected)
    write(root / 'CPU_RESULT.json', tests)
    started = time.time()
    plan = dict(schema=run.policy.SCHEMA, uuid=run.UUID, physical=7, native_cap=run.NATIVE_CAP,
        parent_cap=run.PARENT_CAP, cycles=run.policy.CYCLES, episodes_per_cycle=2, sleep_seconds_per_cycle=240,
        started_unix=started, native_deadline_unix=1789491600, hard_deadline_unix=1789491720,
        lease_end_unix=run.seed.continual.LEASE_END, gpu_hours=8.0, no_L2_into_original_L1=True,
        anchor_weight=0.1, old_rehearsal_weight=0.2, new_own_weight=0.7,
        collection_does_not_wait_for_anchors=True, sleep_requires_explicit_anchor_binding=True,
        no_control_replicates=True, no_causal_parenting_claim_without_matched_controls=True)
    write(root / 'PLAN.json', plan)
    ready = dict(plan_sha256=sha(root / 'PLAN.json'), own_cpu_tests_passed=True, provenance_passed=True,
        source_files=sources, input_files={name: sha(root / name)
            for name in ('INITIAL.json', 'EXCLUSIONS.json', 'COHORT.json', 'CPU_RESULT.json')},
        native_calls=0, parent_calls=0, optimizer_updates=0, scope='COLLECTION_THEN_ANCHOR_BOUND_SLEEP',
        prepared_unix=time.time())
    write(root / 'READY.json', ready)
    environment = dict(os.environ, CUDA_VISIBLE_DEVICES='', PYTHONPATH=str(run.SOURCE_ROOT))
    pins = json.loads(subprocess.run([PYTHON, '-B', '-m', 'gpu.orch_r110_guided_broker', '--source-pins'],
        cwd=run.SOURCE_ROOT, env=environment, capture_output=True, text=True, timeout=60, check=True).stdout)
    broker = dict(schema='ORCH_R110_GUIDED_BROKER_ALLOCATION_V1', campaign=str(root),
        ready_sha256=sha(root / 'READY.json'), source_files=pins,
        tasks_by_request={f'cycle{cycle}_episode{episode}': dict(id=task['id'], question=task['question'])
            for cycle, group in enumerate(selected['train'], 1) for episode, task in enumerate(group, 1)},
        started_unix=plan['started_unix'], deadline_unix=plan['native_deadline_unix'],
        dispatch_cutoff_unix=plan['native_deadline_unix'] - 600,
        max_parent_calls=run.PARENT_CAP, attempts_per_request=1, max_output_tokens=4096)
    for cycle, group in enumerate(selected['train'], 1):
        broker['tasks_by_request'][f'cycle{cycle}_presleep'] = dict(id=group[-1]['id'], question=group[-1]['question'])
    write(root / 'PARENT_BROKER_ALLOCATION.json', broker)
    service_command = ['sudo', '-n', 'env', 'CUDA_VISIBLE_DEVICES=', 'PYTHONDONTWRITEBYTECODE=1',
        'PYTHONPATH=' + str(run.SOURCE_ROOT), 'python3', '-B', '-m',
        'gpu.orch_r110_guided_supervisor', 'service', '--root', str(root)]
    subprocess.run(service_command, check=True, capture_output=True, timeout=60)
    return dict(ready_sha256=sha(root / 'READY.json'), plan=plan,
        parent_allocation_sha256=sha(root / 'PARENT_BROKER_ALLOCATION.json'))


def wait_clear(root, cycle, phase, plan):
    output = root / 'ADMISSIONS'
    output.mkdir(exist_ok=True)
    until = min(time.time() + 300, plan['native_deadline_unix'])
    for attempt in range(150):
        require(time.time() < until, 'bounded_strict_admission_timeout')
        report = scan(root)
        path = output / f'{cycle}_{phase}_{attempt:03d}.json'
        require(not path.exists(), 'admission_evidence_never_overwritten')
        write(path, report)
        if report['clear'] is True:
            require(report['scanner_euid'] == 0 and report['blocking_reasons'] == []
                and report['gpu']['index'] == 7 and report['gpu']['uuid'] == run.UUID
                and report['host_sha256'] == run.HOST_SHA and 'device_minor' in report,
                'full_privileged_uuid_minor_admission')
            return path
        require(report['scanner_euid'] == 0, 'unknown_privileged_visibility')
        time.sleep(2)
    raise TimeoutError('strict_admission_not_clear')


def supervise(root):
    plan = run.validate(root)
    require(os.environ.get('CUDA_VISIBLE_DEVICES') == '', 'cpu_only_supervisor')
    (root / 'SUPERVISOR_ONCE').mkdir()
    try:
        first_admission = wait_clear(root, 1, 'lifetime', plan)
        for cycle in range(1, run.policy.CYCLES + 1):
            if time.time() >= plan['native_deadline_unix'] - 600:
                break
            for phase in ('collection', 'sleep', 'readout'):
                run.validate(root)
                if phase == 'sleep':
                    while not (root / 'ANCHORS.json').exists():
                        require(time.time() < plan['native_deadline_unix'] - 600, 'anchor_wait_within_original_lifetime')
                        time.sleep(2)
                receipt = first_admission
                seconds = math.floor(plan['hard_deadline_unix'] - time.time() - 5)
                require(seconds > 0, 'hard_lifetime_exhausted')
                command = ['timeout', '--signal=TERM', '--kill-after=5s', f'{seconds}s', PYTHON,
                    '-B', '-m', 'gpu.orch_r110_guided_run', '--root', str(root), '--cycle', str(cycle), '--phase', phase]
                environment = dict(os.environ, CUDA_VISIBLE_DEVICES=run.UUID, HF_HUB_OFFLINE='1',
                    TRANSFORMERS_OFFLINE='1', PYTHONDONTWRITEBYTECODE='1', PYTHONPATH=str(run.SOURCE_ROOT))
                with (root / f'cycle{cycle}_{phase}.log').open('x') as log:
                    child = subprocess.Popen(command, cwd=run.SOURCE_ROOT, env=environment,
                        stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
                write(root / f'LAUNCH_{cycle}_{phase}.json', dict(pid=child.pid, command=command,
                    admission_sha256=sha(receipt), launched_unix=time.time(), native_calls_cap=run.NATIVE_CAP,
                    parent_calls_cap=run.PARENT_CAP, hard_deadline_unix=plan['hard_deadline_unix']))
                code = child.wait()
                require(code == 0, 'native_phase_failed_no_retry')
                complete = root / f'cycle{cycle}' / phase / 'COMPLETE.json'
                require(read(complete)['status'] == 'COMPLETE', 'native_completion_required')
                write(root / f'DONE_{cycle}_{phase}.json', dict(complete_sha256=sha(complete), returncode=code))
        write(root / 'TERMINAL.json', dict(status='COMPLETE', cycles=sum(1 for path in root.glob('DONE_*_readout.json')), finished_unix=time.time()))
    except BaseException as error:
        write(root / 'TERMINAL.json', dict(status='FAILED', error_type=type(error).__name__,
            error=str(error), finished_unix=time.time(), retry=False))
        raise


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('mode', choices=('prepare', 'supervise', 'scan', 'service'))
    parser.add_argument('--root', type=Path, default=run.ROOT)
    parser.add_argument('--initial', type=Path)
    parser.add_argument('--registry', type=Path)
    parser.add_argument('--cpu-result', type=Path)
    args = parser.parse_args()
    if args.mode == 'prepare':
        print(json.dumps(prepare(args.root, args.initial, args.registry, args.cpu_result)))
    elif args.mode == 'service':
        require(os.geteuid() == 0, 'privileged_service_creation')
        bind_scanner()
        admission.pinned.service(args.root / 'SERVICE_IDENTITY.json')
    elif args.mode == 'scan':
        print(json.dumps(scan(args.root)))
    else:
        supervise(args.root)
