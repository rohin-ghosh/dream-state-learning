"""Prospective native experience cohort; published rehearsal branches stay immutable."""

import argparse
from dataclasses import asdict
import hashlib
import json
import os
from pathlib import Path
import signal
import subprocess
import time
from types import FunctionType, SimpleNamespace


ORIGIN = Path('/localhome/local-rohing/orch_r109_l1_20260915')
ROOT = ORIGIN / 'experience_c1'
END = 1789491360
CUTOFF = END - 300
SLOTS = {'FULL': 5, 'CONTROL': 6}
SOURCE_LABEL = 'R109_SELF_GENERATED_FUNCTIONAL'


def read(path):
    return json.loads(Path(path).read_text())


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def positions(update, seed_update, prior_count, eligible_count):
    assert update > seed_update >= 8932 and eligible_count > 0
    cursor = update - 1
    result = [('legacy', cursor % 210), ('prior', (2 * cursor) % prior_count), ('anchor', cursor % 42)]
    offset = update - seed_update - 1
    result.append(('eligible', (offset // 8) % eligible_count) if offset % 8 == 0 else ('prior', (2 * cursor + 1) % prior_count))
    return result


def labels_for(arm, source, labels):
    assert arm in SLOTS
    return [-100] * len(labels) if arm == 'CONTROL' and source == 'eligible' else list(labels)


def boundary(progress, calls, intents, failures):
    return bool(progress and progress['calls'] == calls == intents and failures == 0)


def review_gate(review, row, task, draft=None):
    assert review['full_text_read'] is True and review['functional_verdict'] == review['grounding_verdict'] == 'PASS'
    assert review['evidence'] and review['property'] in ('ARITHMETIC_ERROR_CORRECTED', 'TASK_CONSTRAINT_USED')
    assert row['source_label'] == SOURCE_LABEL and row['split'] == 'TRAIN' and row['parent_calls'] == 0
    assert row['family'] == 'math' and row['source_task_id'] == task['id'] == review['source_task_id']
    assert row['response']['terminal'] and not row['response']['truncated'] and row['outcome']['correct'] is True
    if review['property'] == 'ARITHMETIC_ERROR_CORRECTED':
        assert draft is not None and draft['task_id'] == row['task_id']
        assert draft['outcome']['category'] == 'parsed_wrong' and draft['outcome']['answer'] != row['outcome']['answer']
        assert row['messages'][-2] == dict(role='assistant', content=draft['response']['raw'])


def verify(require_gpu_receipt=True):
    from gpu import orch_r109_l1_run as original
    plan = read(ROOT / 'PLAN.json')
    old = original.verify()
    assert sha(ORIGIN / 'PLAN.json') == plan['original_plan_sha256']
    assert old['source_archive_sha256'] == plan['original_archive_sha256']
    assert sha(__file__) == plan['cohort_source_sha256']
    assert sha(ROOT / 'source.tar') == plan['cohort_archive_sha256']
    assert sha(ROOT / 'REVIEWS.json') == plan['reviews_sha256']
    assert plan['lifetime']['hard_deadline_unix'] == END and plan['lifetime']['native_deadline_unix'] == CUTOFF
    assert plan['train_slots'] == SLOTS and plan['cohort_id'] == 'R109_EXPERIENCE_C1'
    prepared = read(ROOT / 'PREPARED.json')
    assert prepared['status'] == 'PASS' and prepared['plan_sha256'] == sha(ROOT / 'PLAN.json')
    assert sha(ROOT / 'ENCODED.json') == prepared['encoded_sha256']
    if require_gpu_receipt:
        receipt = read(ROOT / 'PRE_GPU.json')
        assert receipt['cpu_passed'] is True and receipt['builder_line'].startswith('[Builder]')
        assert receipt['plan_sha256'] == sha(ROOT / 'PLAN.json')
    return plan


def prepare():
    from gpu import orch_r109_l1_train as trainer
    from gpu import orch_r109_l1_run as original
    from gpu.orch_combined_l1_continual_content import encode_rows
    from organism_v6 import orch_rich_hot_node2 as math_source
    from organism_v6 import orch_r107_capability as capability
    assert os.environ.get('CUDA_VISIBLE_DEVICES') == ''
    old = original.verify()
    assert not (ROOT / 'PLAN.json').exists()
    reviews = read(ROOT / 'REVIEWS.json')
    assert reviews['node'] == 'node2' and reviews['source_archive_sha256'] == old['source_archive_sha256']
    assert reviews['node_plan_sha256'] == sha(ORIGIN / 'PLAN.json')
    old_prepared = read(ORIGIN / 'PREPARED.json')
    document = read(ORIGIN / 'TASKS.json')
    assert sha(ORIGIN / 'TASKS.json') == read(ORIGIN / 'GENERATION_READY.json')['tasks_sha256']
    tasks = {task['id']: task for task in document['math']['tasks']}
    excluded_ids = set(document['math']['excluded_ids'])
    excluded_questions = set(document['math']['excluded_question_hashes'])
    held = read(ORIGIN / 'input/prior/LEGACY_READOUT.json')['held']
    assert digest(held) == old_prepared['held_behavior_sha256'] and held['split'] == 'HELD'
    assert capability.digest(capability.tasks()) == old_prepared['fixed32_suite_sha256']
    tokenizer = trainer.native.source.native.load_local_tokenizer(old['model_dir'])
    rows = []
    encoded = []
    seen_tasks = set()
    seen_targets = set()
    corpus = read(ORIGIN / 'input/prior/CORPORA/000013.json')
    historical_targets = {entry.get('target_sha256') for entry in corpus['rows']}
    for review in reviews['accepted']:
        path = ORIGIN / review['path']
        assert path.resolve().is_relative_to(ORIGIN / 'generation') and sha(path) == review['call_sha256']
        row = read(path)
        assert row['source_archive_sha256'] == old['source_archive_sha256']
        assert row['source_state_sha256'] == trainer.policy.CHILD and row['source_tasks_sha256'] == sha(ORIGIN / 'TASKS.json')
        task = tasks[row['source_task_id']]
        draft = None
        if 'draft_path' in review:
            draft_path = ORIGIN / review['draft_path']
            assert draft_path.resolve().is_relative_to(ORIGIN / 'generation') and sha(draft_path) == review['draft_sha256']
            draft = read(draft_path)
        review_gate(review, row, task, draft)
        assert math_source.outcome(task, row['response'])['correct'] is True
        assert task['id'] not in excluded_ids and task['question_sha256'] not in excluded_questions
        text = json.dumps(row['messages'], ensure_ascii=False) + row['response']['raw']
        assert all(item['id'] not in text and item['prompt'] not in text for item in capability.tasks())
        assert all(entry['event'] not in text for entry in held['events'])
        target = row['response']['raw']
        target_sha = hashlib.sha256(target.encode()).hexdigest()
        assert task['id'] not in seen_tasks and target_sha not in seen_targets | historical_targets
        seen_tasks.add(task['id'])
        seen_targets.add(target_sha)
        material = dict(student_prefix=row['messages'], target=target)
        item = encode_rows([material], tokenizer)[0]
        assert tuple(row['response']['token_ids']) == tuple(item.target_ids), 'native_child_tokens_must_match_untruncated_supervised_target'
        assert len(item.input_ids) <= 2048
        admitted = dict(source_label=SOURCE_LABEL, split='TRAIN', task_id=row['task_id'],
            contamination_family=task['question_sha256'], functional_verdict='PASS', grounding_verdict='PASS',
            source_archive_sha256=row['source_archive_sha256'], source_call_sha256=sha(path),
            annotation_sha256=digest(review), target_actor='CHILD', parent_text_masked=True,
            target=target, target_sha256=target_sha, native_token_ids=row['response']['token_ids'],
            student_prefix=row['messages'], prefix_sha256=digest(row['messages']), source_task_id=task['id'],
            native_source_path=str(path), source_state_sha256=row['source_state_sha256'], review=review,
            original_capture_unchanged=True, teacher_or_l2=False)
        trainer.policy.validate_eligible(admitted, excluded_ids, excluded_questions)
        rows.append(admitted)
        encoded.append(asdict(item))
    assert len(rows) == 4 and len(seen_tasks) == 4
    parent_receipts = sorted((ORIGIN / 'fit/FULL').glob('segment*/ASYNC_READOUT_ACCEPTED.json'))
    parent_receipt = parent_receipts[-1]
    parent = read(parent_receipt)
    checkpoint = ORIGIN / 'fit/FULL/checkpoints' / f'{parent["update"]:09d}'
    commit = trainer.storage.verify_checkpoint(checkpoint)
    assert sha(checkpoint / 'COMMIT.json') == parent['checkpoint_commit_sha256']
    assert commit['metadata']['adapter']['state_sha256'] == parent['checkpoint_state_sha256']
    combined = read(ORIGIN / 'ENCODED.json')
    assert sha(ORIGIN / 'ENCODED.json') == old_prepared['encoded_sha256']
    combined['eligible'] = encoded
    trainer.write(ROOT / 'ELIGIBLE.json', dict(cohort_id='R109_EXPERIENCE_C1', rows=rows, reviews_sha256=sha(ROOT / 'REVIEWS.json')))
    trainer.write(ROOT / 'ENCODED.json', combined)
    held_destination = ROOT / 'input/prior/LEGACY_READOUT.json'
    held_destination.parent.mkdir(parents=True, exist_ok=True)
    held_destination.symlink_to(ORIGIN / 'input/prior/LEGACY_READOUT.json')
    plan = dict(old, cohort_id='R109_EXPERIENCE_C1', train_slots=SLOTS, source_labels=[*trainer.policy.LABELS[:2], SOURCE_LABEL],
        seed_checkpoint=str(checkpoint), seed_update=parent['update'], seed_commit_sha256=sha(checkpoint / 'COMMIT.json'),
        seed_state_sha256=parent['checkpoint_state_sha256'], seed_readout_receipt_sha256=sha(parent_receipt),
        original_plan_sha256=sha(ORIGIN / 'PLAN.json'), original_archive_sha256=old['source_archive_sha256'],
        cohort_source_sha256=sha(__file__), cohort_archive_sha256=sha(ROOT / 'source.tar'),
        reviews_sha256=sha(ROOT / 'REVIEWS.json'), eligible_sha256=sha(ROOT / 'ELIGIBLE.json'),
        recipe='C1_ONE_ACTUAL_ELIGIBLE_ROW_EVERY_8_UPDATES_REPLACES_SECOND_PRIOR;CONTROL_MASKS_ONLY_ELIGIBLE;BOTH_KEEP_BASE_ANCHORS',
        maximum_segments=512, updates_per_segment=128, reset=False, published_rehearsal_branches_unchanged=True,
        parent_text_masked=True, held_training_allowed=False, teacher_l2_allowed=False, frozen_unix=time.time())
    trainer.write(ROOT / 'PLAN.json', plan)
    trainer.write(ROOT / 'PREPARED.json', dict(old_prepared, plan_sha256=sha(ROOT / 'PLAN.json'),
        encoded_sha256=sha(ROOT / 'ENCODED.json'), counts={key:len(value) for key,value in combined.items()},
        eligible_sha256=sha(ROOT / 'ELIGIBLE.json'), eligible_unique_tasks=len(seen_tasks), native_target_tokens_verified=True,
        all_prefix_masked=True, prospective_only=True, status='PASS'))
    print(json.dumps(dict(status='PASS', cohort_id=plan['cohort_id'], plan_sha256=sha(ROOT / 'PLAN.json'),
        seed_update=plan['seed_update'], seed_state_sha256=plan['seed_state_sha256'], seed_commit_sha256=plan['seed_commit_sha256'],
        eligible_rows=len(rows), eligible_unique_tasks=len(seen_tasks), eligible_sha256=plan['eligible_sha256'],
        encoded_sha256=sha(ROOT / 'ENCODED.json'), source_sha256=sha(__file__), archive_sha256=sha(ROOT / 'source.tar'),
        counts={key:len(value) for key,value in combined.items()}, native_target_tokens_verified=True,
        all_prefix_masked=True, original_corpus_unchanged=True, hard_end_unix=END)))


def load_plan(arm, checkpoint, training):
    from gpu import orch_r109_l1_train as trainer
    plan = verify()
    prepared = read(ROOT / 'PREPARED.json')
    commit = trainer.storage.verify_checkpoint(checkpoint)['metadata']
    adapter = trainer.native.bridge.AdapterIdentity.from_document(dict(commit['adapter'], path=str(checkpoint / 'adapter')))
    binding = trainer.native.bridge.StageBinding('R109_EXPERIENCE_C1_' + arm, trainer.native.bridge.ARMS[2],
        0, 'training' if training else 'sealed_readout', adapter, False, not training, sha(ROOT / 'PREPARED.json'))
    proxy = SimpleNamespace(binding=lambda unused:binding,
        contract=SimpleNamespace(manifest=lambda unused:dict(recipe=trainer.previous.common.RECIPE)),
        lineage=SimpleNamespace(arm=trainer.native.bridge.ARMS[2]))
    return plan, prepared, commit, adapter, binding, proxy


def train(arm, segment, resume):
    from gpu import orch_r109_l1_train as trainer
    plan, prepared, commit, adapter, binding, proxy = load_plan(arm, resume, True)
    index = SLOTS[arm]
    uuid = plan['uuid_by_index'][index]
    assert os.environ['CUDA_VISIBLE_DEVICES'] == uuid
    check = lambda label:trainer.previous.common.check_deadline(plan['lifetime'], label)
    loaded = trainer.native.load_training(proxy, model_dir=plan['model_dir'], device='cuda:0', gpu_uuid=uuid,
        context=trainer.native.StageContext(), check=check)
    torch = loaded.engine.torch
    loaded.optimizer.load_state_dict(torch.load(resume / 'optimizer.pt', map_location='cuda:0', weights_only=False))
    trainer.previous.restore_rng(torch, torch.load(resume / 'rank0.pt', map_location='cpu', weights_only=False))
    parameters = {name:value for name,value in loaded.engine.model.named_parameters() if trainer.native.is_lora(name)}
    assert trainer.native.state_hash(parameters) == adapter.state_sha256
    encoded = read(ROOT / 'ENCODED.json')
    output = ROOT / 'fit' / arm / f'segment{segment:03d}'
    output.mkdir(parents=True, exist_ok=True)
    trainer.write(output / 'RANK0_LOADED.json', dict(update=commit['update'], state_sha256=adapter.state_sha256,
        optimizer_restored=True, rng_restored=True, global_cursor_preserved=True, process=loaded.process, uuid=uuid,
        cohort_id=plan['cohort_id'], eligible_sha256=plan['eligible_sha256'], observed_unix=time.time()))
    state = dict(update=commit['update'], prior_checkpoint_commit_sha256=sha(resume / 'COMMIT.json'),
        lifetime=plan['lifetime'], source_labels=plan['source_labels'], arm=arm, cohort_id=plan['cohort_id'],
        recipe=plan['recipe'], eligible_sha256=plan['eligible_sha256'], seed_update=plan['seed_update'],
        cohort_exposures=dict(commit.get('cohort_exposures', {})),
        eligible_supervised_tokens=commit.get('eligible_supervised_tokens', 0), original_history_unchanged=True)
    with (output / 'RANK0_LOSSES.jsonl').open('x') as log:
        for update in range(commit['update'] + 1, commit['update'] + 129):
            check('C1_optimizer_boundary')
            selections = positions(update, plan['seed_update'], len(encoded['prior']), len(encoded['eligible']))
            rows = [encoded[source][position] for source,position in selections]
            maximum = max(len(row['input_ids']) for row in rows)
            reference = sum(label != -100 for row in rows for label in row['labels'][1:])
            targets = [labels_for(arm, source, row['labels']) for (source,position),row in zip(selections,rows)]
            active = sum(label != -100 for labels in targets for label in labels[1:])
            assert active > 0
            tensors = {name:torch.tensor(values, dtype=torch.long, device=loaded.engine.device) for name,values in dict(
                input_ids=[row['input_ids'] + [loaded.engine.tokenizer.pad_token_id] * (maximum-len(row['input_ids'])) for row in rows],
                labels=[labels + [-100] * (maximum-len(labels)) for labels in targets],
                attention_mask=[[1] * len(row['input_ids']) + [0] * (maximum-len(row['input_ids'])) for row in rows]).items()}
            loaded.optimizer.zero_grad(set_to_none=True)
            with torch.autocast(device_type='cuda', dtype=torch.bfloat16):
                loss = loaded.engine.model(**tensors, use_cache=False).loss * (active/reference)
            assert bool(torch.isfinite(loss))
            loss.backward()
            assert all(parameter.grad is not None and bool(torch.isfinite(parameter.grad).all()) for parameter in parameters.values())
            loaded.optimizer.step()
            state['update'] = update
            eligible_tokens = sum(label != -100 for (source,position),labels in zip(selections,targets) if source == 'eligible' for label in labels[1:])
            state['eligible_supervised_tokens'] += eligible_tokens
            for source,position in selections:
                state['cohort_exposures'][source] = state['cohort_exposures'].get(source,0) + 1
            log.write(json.dumps(dict(update=update, loss=loss.item(), selections=selections, local_active=active,
                reference_tokens=reference, eligible_supervised_tokens=eligible_tokens, finished_unix=time.time())) + '\n')
            log.flush()
    destination = ROOT / 'fit' / arm / 'checkpoints' / f'{state["update"]:09d}'
    staging = destination.with_suffix('.pending')
    staging.mkdir(parents=True, exist_ok=False)
    torch.save(trainer.previous.rng_state(torch), staging / 'rank0.pt')
    torch.save(trainer.previous.rng_state(torch), staging / 'rank1.pt')
    loaded.engine.verify_base()
    torch.save(loaded.optimizer.state_dict(), staging / 'optimizer.pt')
    loaded.engine.model.save_pretrained(staging / 'adapter', safe_serialization=True, save_embedding_layers=False)
    adapter = trainer.native.bridge.AdapterIdentity(str(destination / 'adapter'), trainer.native.state_hash(parameters),
        trainer.policy.BASE, tuple((path.name,sha(path)) for path in sorted((staging / 'adapter').iterdir()) if path.is_file()))
    state.update(adapter=adapter.document(), source_sha256=plan['cohort_archive_sha256'],
        optimizer_preserved=True, rng_per_rank=True, world_size=1, saved_unix=time.time())
    trainer.storage.commit_checkpoint(staging, destination, state)
    trainer.write(output / 'COMPLETE.json', dict(checkpoint=str(destination), commit_sha256=sha(destination / 'COMMIT.json'),
        update=state['update'], adapter=adapter.document(), readout_required=True,
        eligible_supervised_tokens=state['eligible_supervised_tokens'], eligible_sha256=plan['eligible_sha256']))


def readout(arm, condition, segment, resume):
    from gpu import orch_r109_l1_train as trainer
    namespace = dict(trainer.__dict__, ROOT=ROOT, load_plan=load_plan)
    runner = FunctionType(trainer.readout.__code__, namespace, 'cohort_readout', trainer.readout.__defaults__)
    runner(arm, SLOTS[arm], condition, segment, resume)


def retire_generation(index):
    from gpu import orch_r109_l1_run as original
    from gpu.orch_r109_l1_ops import identity
    verify()
    assert index in SLOTS.values()
    launch = read(ORIGIN / f'generation_{index}_LAUNCH.json')
    expected = launch['identity']
    assert launch['module'] == 'gpu.orch_r109_l1_run' and launch['arguments'] == ['generate', '--index', str(index)]
    assert launch['source_archive_sha256'] == read(ORIGIN / 'PLAN.json')['source_archive_sha256']
    directory = ORIGIN / 'generation' / f'gpu{index}'
    descriptor = os.pidfd_open(expected['pid'])
    try:
        while time.time() < CUTOFF - 900:
            assert identity(expected['pid']) == expected and expected['uid'] == os.getuid()
            signal.pidfd_send_signal(descriptor, signal.SIGSTOP)
            time.sleep(.02)
            progress = read(directory / 'PROGRESS.json') if (directory / 'PROGRESS.json').exists() else None
            calls = list(directory.glob('CALL_*.json'))
            intents = list(directory.glob('INTENT_*.json'))
            failures = list(directory.glob('FAILED_*.json'))
            if boundary(progress, len(calls), len(intents), len(failures)):
                episode = directory / f'EPISODE_{progress["batch"]:03d}_{progress["position"]:02d}.json'
                latest = read(directory / f'CALL_{progress["calls"]:06d}.json')
                if latest['family'] != 'route' or episode.exists():
                    original.write(ROOT / f'RELEASE_{index}.json', dict(identity=expected, index=index,
                        boundary='COMPLETE_TASK_PAIR_OR_ROUTE_EPISODE', progress=progress,
                        capture_hashes={path.name:sha(path) for path in calls}, original_launch_sha256=sha(ORIGIN / f'generation_{index}_LAUNCH.json'),
                        model_job_safe_boundary=True, preserved_outputs=True, lifetime_reset=False, observed_unix=time.time()))
                    signal.pidfd_send_signal(descriptor, signal.SIGTERM)
                    signal.pidfd_send_signal(descriptor, signal.SIGCONT)
                    return
            signal.pidfd_send_signal(descriptor, signal.SIGCONT)
            time.sleep(.15)
        raise TimeoutError('no_complete_owned_generation_boundary')
    finally:
        try:
            if identity(expected['pid']) == expected:
                signal.pidfd_send_signal(descriptor, signal.SIGCONT)
        except (FileNotFoundError, ProcessLookupError):
            pass
        os.close(descriptor)


def supervise(arm):
    import fcntl
    from gpu import orch_r109_l1_run as original
    from gpu.orch_r109_l1_ops import identity
    from organism_v6 import orch_r107_capability as capability
    plan = verify()
    lock = (ROOT / (arm + '.lock')).open('a')
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    assert not (ROOT / ('START_' + arm + '.json')).exists(), 'explicit_recovery_required_no_reset'
    original.write(ROOT / ('START_' + arm + '.json'), dict(identity=identity(os.getpid()), plan_sha256=sha(ROOT / 'PLAN.json'), observed_unix=time.time()))
    index = SLOTS[arm]
    retire_generation(index)
    resume = Path(plan['seed_checkpoint'])
    child = expected = None
    try:
        for segment in range(plan['maximum_segments']):
            if time.time() >= CUTOFF - 600:
                break
            for phase, condition in [('train',None),('readout','ON'),('readout','OFF')]:
                while True:
                    verify()
                    report = original.scan('node2', index)
                    label = f'{arm}_{segment}_{phase}_{condition or "NA"}'
                    original.write(ROOT / 'admissions' / f'{label}_{time.time_ns()}.json', report)
                    if report['clear']:
                        assert report['scanner_euid'] == 0 and report['gpu']['uuid'] == plan['uuid_by_index'][index]
                        break
                    assert time.time() < CUTOFF
                    time.sleep(2)
                args = [phase,'--arm',arm,'--segment',str(segment),'--resume',str(resume)]
                if condition:
                    args += ['--condition',condition]
                with (ROOT / (label + '.log')).open('x') as log:
                    child = subprocess.Popen([original.PYTHON,'-B','-u',str(Path(__file__)),*args], cwd=ORIGIN / 'source',
                        stdin=subprocess.DEVNULL, stdout=log, stderr=subprocess.STDOUT, start_new_session=True,
                        env=dict(os.environ, PYTHONPATH=str(ORIGIN / 'source'), CUDA_VISIBLE_DEVICES=plan['uuid_by_index'][index],
                            PYTHONDONTWRITEBYTECODE='1',HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',OMP_NUM_THREADS='1',MKL_NUM_THREADS='1',TOKENIZERS_PARALLELISM='false'))
                expected = identity(child.pid)
                original.write(ROOT / (label + '_LAUNCH.json'), dict(identity=expected, index=index, arguments=args,
                    source_sha256=plan['cohort_source_sha256'], hard_deadline_unix=END, started_unix=time.time()))
                while child.poll() is None:
                    original.write(ROOT / ('HEARTBEAT_' + arm + '.json'), dict(phase=phase, condition=condition, segment=segment,
                        resume=str(resume), identity=expected, index=index, observed_unix=time.time(), hard_end_unix=END,
                        cohort_id=plan['cohort_id'], eligible_sha256=plan['eligible_sha256']))
                    if time.time() >= END - 45:
                        original.stop(child, expected, 'FIXED_R109_END')
                        raise TimeoutError('original_R109_deadline')
                    time.sleep(2)
                assert child.returncode == 0, 'cohort_stage_failed_no_silent_retry'
                if phase == 'train':
                    resume = Path(read(ROOT / 'fit' / arm / f'segment{segment:03d}' / 'COMPLETE.json')['checkpoint'])
            directory = ROOT / 'fit' / arm / f'segment{segment:03d}'
            records = [read(path) for path in sorted((directory / 'readout').glob('*/CAPABILITY_*.json'))]
            summaries = {condition:read(directory / 'readout' / condition / 'COMPLETE.json') for condition in ('ON','OFF')}
            assert all(row['capability_calls'] == 32 and row['behavior_calls'] == 16 and row['base_and_adapter_unchanged'] for row in summaries.values())
            original.write(directory / 'PAIRED_FIXED32.json', capability.reduce_paired(records,
                checkpoint_sha256=summaries['ON']['checkpoint_state_sha256'], base_sha256=original.policy.BASE, max_new_tokens=512))
    finally:
        if child is not None:
            original.stop(child, expected, 'C1_SUPERVISOR_EXIT_PRESERVE_COMMITTED_CHECKPOINTS')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=['prepare','verify','supervise','train','readout'])
    parser.add_argument('--arm', choices=list(SLOTS))
    parser.add_argument('--segment', type=int)
    parser.add_argument('--resume', type=Path)
    parser.add_argument('--condition', choices=['ON','OFF'])
    options = parser.parse_args()
    if options.action == 'prepare':
        prepare()
    elif options.action == 'verify':
        print(json.dumps(dict(status='PASS', plan=verify())))
    elif options.action == 'supervise':
        supervise(options.arm)
    elif options.action == 'train':
        train(options.arm, options.segment, options.resume)
    else:
        readout(options.arm, options.condition, options.segment, options.resume)
