"""Prospective reviewed self-experience batches; no automatic semantic admission."""

import argparse
from copy import deepcopy
from dataclasses import asdict
import hashlib
import json
import os
from pathlib import Path
import signal
import subprocess
import time
from types import FunctionType, SimpleNamespace

try:
    import orch_r109_l1_experience as experience
except ImportError:
    from gpu import orch_r109_l1_experience as experience


ORIGIN = experience.ORIGIN
ROOT = ORIGIN / 'experience_feed_v1'
END = experience.END
CUTOFF = experience.CUTOFF
SLOTS = experience.SLOTS
read = experience.read
sha = experience.sha
digest = experience.digest


def require(value, reason):
    if not value:
        raise ValueError(reason)


def write(path, document):
    from gpu.orch_r109_l1_train import write as native_write
    native_write(path, document)


def alive(expected):
    try:
        directory = Path('/proc') / str(expected['pid'])
        fields = (directory / 'stat').read_text().rsplit(')', 1)[1].split()
        return (fields[0] != 'Z' and fields[19] == expected['start_ticks'] and
                directory.stat().st_uid == expected['uid'] and
                Path('/proc/sys/kernel/random/boot_id').read_text().strip() == expected['boot_id'])
    except FileNotFoundError:
        return False


def choose_version(segment, available):
    require(type(segment) is int and segment >= 0 and available, 'bounded_version_cursor')
    require(sorted(available) == list(range(len(available))), 'contiguous_immutable_batches')
    return min(segment, len(available) - 1)


def source_gate(review, row, task, plan, tasks_sha, *, draft=None):
    require(review['path'].startswith('generation_v3/gpu') and '..' not in Path(review['path']).parts,
            'native_V3_source_only')
    require(row['source_archive_sha256'] == plan['supplement_archive_sha256'] and
            row['original_environment_archive_sha256'] == plan['original_source_archive_sha256'] and
            row['prompt_policy_sha256'] == plan['policy_sha256'] and
            row['source_state_sha256'] == plan['generation_seed_unchanged'] and
            row['source_tasks_sha256'] == tasks_sha, 'exact_node_archives_seed_and_tasks')
    experience.review_gate(review, row, task, draft)
    require(not row.get('teacher_or_l2', False), 'no_silent_parented_source_mixing')


def runtime():
    from gpu import orch_r109_l1_run as original
    from gpu.orch_math_rich_source import verify_archive
    old = original.verify()
    manifest = read(ROOT / 'RUNTIME.json')
    require(sha(ROOT / 'source.tar') == manifest['archive_sha256'], 'feed_archive')
    require(verify_archive(ROOT / 'source.tar', ROOT / 'source') == manifest['source_files'],
            'exact_extracted_runtime')
    require(sha(__file__) == manifest['source_sha256'], 'feed_source')
    require(sha(experience.__file__) == manifest['experience_source_sha256'], 'unchanged_training_implementation')
    require(old['source_archive_sha256'] == manifest['original_archive_sha256'], 'original_archive')
    require(sha(ROOT / 'REVIEWS.json') == manifest['reviews_sha256'], 'author_review_bytes')
    return old


def prepare():
    from gpu import orch_r109_l1_train as trainer
    from gpu.orch_combined_l1_continual_content import encode_rows
    from organism_v6 import orch_rich_hot_node2 as math_source
    from organism_v6 import orch_r107_capability as capability
    require(os.environ.get('CUDA_VISIBLE_DEVICES') == '', 'CPU_only_prepare')
    old = runtime()
    v3 = read(ORIGIN / 'generation_v3/PLAN.json')
    require(v3['node'] == 'node2' and sha(ORIGIN / 'generation_v3/source.tar') ==
            v3['supplement_archive_sha256'], 'exact_node2_generation_archive')
    tasks_sha = sha(ORIGIN / 'TASKS.json')
    require(tasks_sha == read(ORIGIN / 'GENERATION_READY.json')['tasks_sha256'], 'generation_roster')
    document = read(ORIGIN / 'TASKS.json')
    tasks = {task['id']:task for task in document['math']['tasks']}
    excluded_ids = set(document['math']['excluded_ids'])
    excluded_questions = set(document['math']['excluded_question_hashes'])
    old_prepared = read(experience.ROOT / 'PREPARED.json')
    old_plan = read(experience.ROOT / 'PLAN.json')
    held = read(ORIGIN / 'input/prior/LEGACY_READOUT.json')['held']
    require(digest(held) == old_prepared['held_behavior_sha256'] and
            capability.digest(capability.tasks()) == old_prepared['fixed32_suite_sha256'], 'same_sealed_suites')
    require(sha(experience.ROOT / 'ELIGIBLE.json') == old_plan['eligible_sha256'] and
            sha(experience.ROOT / 'ENCODED.json') == old_prepared['encoded_sha256'], 'immutable_C1')
    encoded = read(experience.ROOT / 'ENCODED.json')
    eligible = read(experience.ROOT / 'ELIGIBLE.json')['rows']
    seen_tasks = {row['source_task_id'] for row in eligible}
    seen_targets = {row['target_sha256'] for row in eligible}
    historical = {row.get('target_sha256') for row in
                  read(ORIGIN / 'input/prior/CORPORA/000013.json')['rows']}
    tokenizer = trainer.native.source.native.load_local_tokenizer(old['model_dir'])
    reviews = read(ROOT / 'REVIEWS.json')
    all_decisions = list(reviews['rejected'])
    total_new = 0
    for number, batch in enumerate(reviews['batches']):
        folder = ROOT / 'versions' / f'{number:03d}'
        require(not folder.exists(), 'immutable_new_batch_only')
        admitted_new = []
        for review in batch:
            path = ORIGIN / review['path']
            try:
                require(path.resolve().is_relative_to(ORIGIN / 'generation_v3') and
                        sha(path) == review['call_sha256'], 'exact_capture_hash')
                row = read(path)
                task = tasks[row['source_task_id']]
                source_gate(review, row, task, v3, tasks_sha)
                require(math_source.outcome(task, row['response'])['correct'] is True, 'native_oracle_recomputed')
                require(task['id'] not in excluded_ids and task['question_sha256'] not in excluded_questions,
                        'held_task_and_question_excluded')
                text = json.dumps(row['messages'], ensure_ascii=False) + row['response']['raw']
                require(all(item['id'] not in text and item['prompt'] not in text for item in capability.tasks())
                        and all(item['event'] not in text for item in held['events']), 'sealed_content_excluded')
                target = row['response']['raw']
                target_sha = hashlib.sha256(target.encode()).hexdigest()
                require(task['id'] not in seen_tasks and target_sha not in seen_targets | historical,
                        'new_distinct_reviewed_target')
                item = encode_rows([dict(student_prefix=row['messages'], target=target)], tokenizer)[0]
                require(tuple(row['response']['token_ids']) == tuple(item.target_ids) and
                        len(item.input_ids) <= 2048, 'exact_native_tokens_untruncated_student_prefix')
                admitted = dict(source_label=experience.SOURCE_LABEL, split='TRAIN', task_id=row['task_id'],
                    contamination_family=task['question_sha256'], functional_verdict='PASS', grounding_verdict='PASS',
                    source_archive_sha256=row['source_archive_sha256'], source_call_sha256=sha(path),
                    annotation_sha256=digest(review), target_actor='CHILD', parent_text_masked=True,
                    target=target, target_sha256=target_sha, native_token_ids=row['response']['token_ids'],
                    student_prefix=row['messages'], prefix_sha256=digest(row['messages']),
                    source_task_id=task['id'], native_source_path=str(path), source_state_sha256=row['source_state_sha256'],
                    review=review, original_capture_unchanged=True, teacher_or_l2=False)
                trainer.policy.validate_eligible(admitted, excluded_ids, excluded_questions)
                eligible.append(admitted)
                encoded['eligible'].append(asdict(item))
                seen_tasks.add(task['id'])
                seen_targets.add(target_sha)
                admitted_new.append(dict(source_task_id=task['id'], target_sha256=target_sha,
                    call_sha256=sha(path), native_tokens=len(row['response']['token_ids'])))
                all_decisions.append(dict(path=review['path'], call_sha256=sha(path), status='ADMITTED',
                    reason='AUTHOR_REVIEWED_TASK_CONSTRAINT_USED', batch=number, admitted_unix=time.time()))
            except (AssertionError, ValueError) as error:
                all_decisions.append(dict(path=review['path'], call_sha256=review['call_sha256'],
                    status='REJECTED', reason=str(error), batch=number, observed_unix=time.time()))
        require(admitted_new, 'no_empty_new_experience_batch')
        write(folder / 'ELIGIBLE.json', dict(rows=deepcopy(eligible), newly_admitted=admitted_new,
            source_label=experience.SOURCE_LABEL, teacher_l2=False, reviews_sha256=sha(ROOT / 'REVIEWS.json')))
        write(folder / 'ENCODED.json', deepcopy(encoded))
        prior = folder / 'input/prior'
        prior.mkdir(parents=True)
        (prior / 'LEGACY_READOUT.json').symlink_to(ORIGIN / 'input/prior/LEGACY_READOUT.json')
        plan = dict(old_plan, cohort_id=f'R109_EXPERIENCE_C2_B{number:03d}',
            eligible_sha256=sha(folder / 'ELIGIBLE.json'), cohort_source_sha256=sha(__file__),
            cohort_archive_sha256=sha(ROOT / 'source.tar'), reviews_sha256=sha(ROOT / 'REVIEWS.json'),
            previous_cohort_plan_sha256=sha(experience.ROOT / 'PLAN.json'),
            original_schedule_seed_update=old_plan['seed_update'], batch_number=number,
            published_at_segment_boundary_only=True, reset=False, prepared_unix=time.time())
        write(folder / 'PLAN.json', plan)
        write(folder / 'PREPARED.json', dict(old_prepared, plan_sha256=sha(folder / 'PLAN.json'),
            encoded_sha256=sha(folder / 'ENCODED.json'), eligible_sha256=sha(folder / 'ELIGIBLE.json'),
            counts={name:len(rows) for name,rows in encoded.items()}, newly_admitted=len(admitted_new),
            eligible_unique_tasks=len(seen_tasks), all_prefix_masked=True))
        total_new += len(admitted_new)
    write(ROOT / 'ADMISSION_DECISIONS.json', dict(decisions=all_decisions, newly_admitted=total_new,
        original_C1_rows=4, current_eligible_rows=len(eligible), raw_outputs_node_only=True,
        prospective_only=True, observed_unix=time.time(), selection_not_random_prevalence=True))
    print(json.dumps(dict(newly_admitted=total_new, eligible_rows=len(eligible), batches=len(reviews['batches']),
                         decisions_sha256=sha(ROOT / 'ADMISSION_DECISIONS.json'))))


def version_verify(folder):
    runtime()
    plan, prepared = read(folder / 'PLAN.json'), read(folder / 'PREPARED.json')
    require(prepared['status'] == 'PASS' and prepared['plan_sha256'] == sha(folder / 'PLAN.json') and
            prepared['encoded_sha256'] == sha(folder / 'ENCODED.json') and
            plan['eligible_sha256'] == sha(folder / 'ELIGIBLE.json'), 'immutable_batch_binding')
    require(plan['seed_update'] == plan['original_schedule_seed_update'] == 9444 and
            plan['lifetime']['hard_deadline_unix'] == END and
            plan['lifetime']['native_deadline_unix'] == CUTOFF and plan['train_slots'] == SLOTS,
            'no_schedule_lifetime_allocation_reset')
    receipt = read(ROOT / 'PRE_GPU.json')
    require(receipt['cpu_passed'] and receipt['builder_line'].startswith('[Builder]') and
            receipt['runtime_sha256'] == sha(ROOT / 'RUNTIME.json') and
            receipt['tests_sha256'] == sha(ROOT / 'CPU_TESTS.log'), 'owned_preGPU_receipt')
    return plan


def stage_namespace(folder):
    from gpu import orch_r109_l1_train as trainer
    namespace = dict(experience.__dict__, ROOT=folder, __file__=__file__, verify=lambda:version_verify(folder))
    def load_plan(arm, checkpoint, training):
        plan = version_verify(folder)
        prepared = read(folder / 'PREPARED.json')
        commit = trainer.storage.verify_checkpoint(checkpoint)['metadata']
        adapter = trainer.native.bridge.AdapterIdentity.from_document(dict(commit['adapter'], path=str(checkpoint / 'adapter')))
        binding = trainer.native.bridge.StageBinding(plan['cohort_id'] + '_' + arm, trainer.native.bridge.ARMS[2],
            0, 'training' if training else 'sealed_readout', adapter, False, not training, sha(folder / 'PREPARED.json'))
        proxy = SimpleNamespace(binding=lambda unused:binding,
            contract=SimpleNamespace(manifest=lambda unused:dict(recipe=trainer.previous.common.RECIPE)),
            lineage=SimpleNamespace(arm=trainer.native.bridge.ARMS[2]))
        return plan, prepared, commit, adapter, binding, proxy
    namespace['load_plan'] = load_plan
    for name in ('train', 'readout'):
        original = getattr(experience, name)
        namespace[name] = FunctionType(original.__code__, namespace, 'feed_' + name, original.__defaults__)
    return namespace


def safe_readout(heartbeat, summaries, checkpoint_update, state_sha256):
    return (heartbeat['phase'] == 'readout' and heartbeat['condition'] == 'OFF' and
            int(Path(heartbeat['resume']).name) == checkpoint_update and set(summaries) == {'ON','OFF'} and
            all(row['status'] == 'COMPLETE' and row['capability_calls'] == 32 and row['behavior_calls'] == 16
                and row['base_and_adapter_unchanged'] and not row['parent_access'] and
                not row['training_ingestion'] for row in summaries.values()) and
            summaries['ON']['checkpoint_state_sha256'] == summaries['OFF']['checkpoint_state_sha256'] == state_sha256)


def handoff():
    from gpu.orch_r109_l1_ops import identity
    from gpu import orch_r109_l1_train as trainer
    version_verify(ROOT / 'versions/000')
    require(not (ROOT / 'HANDOFF.json').exists(), 'no_duplicate_handoff')
    held = {}
    descriptors = {}
    released = set()
    deadline = min(time.time() + 420, CUTOFF - 600)
    try:
        while time.time() < deadline:
            for arm in SLOTS:
                if arm in held:
                    continue
                expected = read(experience.ROOT / (arm + '_CPU_LAUNCH.json'))['identity']
                require(identity(expected['pid']) == expected and expected['uid'] == os.getuid(), 'own_C1_scheduler_identity')
                heartbeat = read(experience.ROOT / ('HEARTBEAT_' + arm + '.json'))
                if heartbeat['phase'] != 'readout' or heartbeat['condition'] != 'OFF':
                    continue
                descriptor = os.pidfd_open(expected['pid'])
                descriptors[arm] = descriptor
                signal.pidfd_send_signal(descriptor, signal.SIGSTOP)
                time.sleep(.1)
                after = read(experience.ROOT / ('HEARTBEAT_' + arm + '.json'))
                if after['identity'] != heartbeat['identity'] or after['phase'] != 'readout' or after['condition'] != 'OFF':
                    signal.pidfd_send_signal(descriptor, signal.SIGCONT)
                    os.close(descriptors.pop(arm))
                    continue
                held[arm] = dict(cpu=expected, heartbeat=after)
                write(ROOT / ('HELD_' + arm + '.json'), dict(held[arm], observed_unix=time.time(), native_untouched=True))
            if len(held) == 2:
                require(len({Path(item['heartbeat']['resume']).name for item in held.values()}) == 1,
                        'paired_same_update_boundary_required')
                ready = {}
                for arm, item in held.items():
                    heartbeat = item['heartbeat']
                    folder = experience.ROOT / 'fit' / arm / f'segment{heartbeat["segment"]:03d}'
                    paths = {condition:folder / 'readout' / condition / 'COMPLETE.json' for condition in ('ON','OFF')}
                    if not all(path.exists() for path in paths.values()) or alive(heartbeat['identity']):
                        continue
                    checkpoint = Path(heartbeat['resume'])
                    commit = trainer.storage.verify_checkpoint(checkpoint)
                    require(safe_readout(heartbeat, {key:read(path) for key,path in paths.items()},
                        commit['metadata']['update'], commit['metadata']['adapter']['state_sha256']),
                        'completed_exact_fixed32_and_held')
                    ready[arm] = dict(item, checkpoint=str(checkpoint), commit_sha256=sha(checkpoint / 'COMMIT.json'),
                        optimizer_sha256=commit['files']['optimizer.pt'], update=commit['metadata']['update'],
                        readouts={key:dict(path=str(path),sha256=sha(path)) for key,path in paths.items()})
                if len(ready) == 2:
                    write(ROOT / 'HANDOFF.json', dict(arms=ready, native_processes_signalled=False,
                        original_C1_artifacts_unchanged=True, optimizer_reset=False, observed_unix=time.time()))
                    for arm, item in held.items():
                        require(identity(item['cpu']['pid']) == item['cpu'], 'same_owned_scheduler')
                        signal.pidfd_send_signal(descriptors[arm], signal.SIGTERM)
                        signal.pidfd_send_signal(descriptors[arm], signal.SIGCONT)
                        released.add(arm)
                    print(json.dumps(dict(handoff_sha256=sha(ROOT / 'HANDOFF.json'),
                        checkpoint_update=next(iter(ready.values()))['update'], native_signals=0)))
                    return
            time.sleep(.05)
        raise TimeoutError('C1_full_readout_boundary_not_reached')
    finally:
        for arm, descriptor in descriptors.items():
            if arm not in released:
                try:
                    signal.pidfd_send_signal(descriptor, signal.SIGCONT)
                except ProcessLookupError:
                    pass
            os.close(descriptor)


def supervise(arm):
    import fcntl
    from gpu import orch_r109_l1_run as original
    from gpu.orch_r109_l1_ops import identity
    from organism_v6 import orch_r107_capability as capability
    lock = (ROOT / (arm + '.lock')).open('a')
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    handoff_receipt = read(ROOT / 'HANDOFF.json')['arms'][arm]
    require(not alive(handoff_receipt['cpu']), 'old_scheduler_still_owns_slot')
    require(not (ROOT / ('START_' + arm + '.json')).exists(), 'explicit_recovery_no_reset')
    write(ROOT / ('START_' + arm + '.json'), dict(identity=identity(os.getpid()),
        handoff_sha256=sha(ROOT / 'HANDOFF.json'), observed_unix=time.time(), hard_end_unix=END))
    resume = Path(handoff_receipt['checkpoint'])
    require(sha(resume / 'COMMIT.json') == handoff_receipt['commit_sha256'], 'latest_own_checkpoint_only')
    for segment in range(512):
        if time.time() >= CUTOFF - 600:
            return
        available = sorted(int(path.name) for path in (ROOT / 'versions').iterdir() if path.is_dir())
        version = choose_version(segment, available)
        folder = ROOT / 'versions' / f'{version:03d}'
        plan = version_verify(folder)
        write(ROOT / 'bindings' / f'{arm}_{segment:03d}.json', dict(version=version,
            plan_sha256=sha(folder / 'PLAN.json'), encoded_sha256=sha(folder / 'ENCODED.json'),
            eligible_sha256=plan['eligible_sha256'], resume=str(resume), prior_commit_sha256=sha(resume / 'COMMIT.json'),
            segment=segment, observed_unix=time.time(), immutable_for_train_and_both_readouts=True))
        for phase, condition in [('train',None),('readout','ON'),('readout','OFF')]:
            while True:
                report = original.scan('node2', SLOTS[arm])
                write(ROOT / 'admissions' / f'{arm}_{segment}_{phase}_{condition}_{time.time_ns()}.json', report)
                if report['clear']:
                    require(report['scanner_euid'] == 0 and report['gpu']['uuid'] == plan['uuid_by_index'][SLOTS[arm]],
                            'strict_original_slot_admission')
                    break
                require(time.time() < CUTOFF, 'original_cutoff')
                time.sleep(2)
            command = [original.PYTHON, '-B', '-u', str(Path(__file__).resolve()), phase, '--arm', arm,
                '--segment', str(segment), '--version', str(version), '--resume', str(resume)]
            if condition:
                command += ['--condition', condition]
            with (ROOT / f'{arm}_{segment}_{phase}_{condition}.log').open('x') as log:
                child = subprocess.Popen(command, cwd=ORIGIN / 'source', env=dict(os.environ,
                    CUDA_VISIBLE_DEVICES=plan['uuid_by_index'][SLOTS[arm]], PYTHONDONTWRITEBYTECODE='1',
                    HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1', OMP_NUM_THREADS='1', MKL_NUM_THREADS='1'),
                    stdin=subprocess.DEVNULL, stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
            expected = identity(child.pid)
            write(ROOT / f'{arm}_{segment}_{phase}_{condition}_LAUNCH.json', dict(identity=expected,
                arguments=command, index=SLOTS[arm], version=version, hard_end_unix=END, started_unix=time.time()))
            while child.poll() is None:
                document = dict(phase=phase, condition=condition, version=version, segment=segment,
                    resume=str(resume), identity=expected, index=SLOTS[arm], observed_unix=time.time(),
                    cohort_id=plan['cohort_id'], eligible_sha256=plan['eligible_sha256'], hard_end_unix=END)
                from gpu.orch_r109_l1_train import write as native_write
                native_write(ROOT / ('HEARTBEAT_' + arm + '.json'), document)
                if time.time() >= END - 45:
                    original.stop(child, expected, 'ORIGINAL_R109_END')
                    raise TimeoutError('original_hard_end')
                time.sleep(2)
            require(child.returncode == 0, 'feed_stage_failed_preserve_no_retry')
            if phase == 'train':
                resume = Path(read(folder / 'fit' / arm / f'segment{segment:03d}' / 'COMPLETE.json')['checkpoint'])
        directory = folder / 'fit' / arm / f'segment{segment:03d}'
        records = [read(path) for path in sorted((directory / 'readout').glob('*/CAPABILITY_*.json'))]
        summaries = {condition:read(directory / 'readout' / condition / 'COMPLETE.json') for condition in ('ON','OFF')}
        from gpu import orch_r109_l1_train as trainer
        commit = trainer.storage.verify_checkpoint(resume)
        require(safe_readout(dict(phase='readout',condition='OFF',resume=str(resume)),summaries,int(resume.name),
                            commit['metadata']['adapter']['state_sha256']),
                'same_readout_contract_before_next_batch')
        write(directory / 'PAIRED_FIXED32.json', capability.reduce_paired(records,
            checkpoint_sha256=summaries['ON']['checkpoint_state_sha256'], base_sha256=original.policy.BASE,
            max_new_tokens=512))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('prepare','handoff','supervise','train','readout'))
    parser.add_argument('--arm', choices=list(SLOTS))
    parser.add_argument('--segment', type=int)
    parser.add_argument('--version', type=int)
    parser.add_argument('--resume', type=Path)
    parser.add_argument('--condition', choices=('ON','OFF'))
    args = parser.parse_args()
    if args.action == 'prepare':
        prepare()
    elif args.action == 'handoff':
        handoff()
    elif args.action == 'supervise':
        try:
            supervise(args.arm)
        except BaseException as error:
            write(ROOT / ('FAILURE_' + args.arm + '.json'), dict(error_type=type(error).__name__,
                error=str(error), observed_unix=time.time(), no_silent_restart=True))
            raise
    else:
        namespace = stage_namespace(ROOT / 'versions' / f'{args.version:03d}')
        if args.action == 'train':
            namespace['train'](args.arm, args.segment, args.resume)
        else:
            namespace['readout'](args.arm, args.condition, args.segment, args.resume)


if __name__ == '__main__':
    main()
