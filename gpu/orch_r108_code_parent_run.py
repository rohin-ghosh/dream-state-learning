"""One new A1000 lifetime: 100 native / 20 parents, no optimizer or retries."""

import argparse
from collections import Counter
import json
import os
from pathlib import Path
import subprocess
import time

from gpu import orch_r107_base_anchors_run as anchors
from gpu import orch_math_pipeline_l2_run as common
from gpu.orch_math_pipeline_l2_parent_strong import parse as parse_parent
from gpu.orch_r108_code_parent_engine import Engine, assert_no_adapter
from organism_v6 import orch_r108_code_parent as policy


ROOT = Path('/localhome/local-rohing/orch_r108_code_parent_20260915_attempt1')
ANCHORS = Path('/localhome/local-rohing/orch_r107_base_anchors_20260915_attempt1')
LANE = 'campaign_code_parent_0'
QUEUE = 'code_parent_queue'
write, read, sha = common.write, common.read, common.sha


def validate_lifetime(lifetime, now):
    policy.require(lifetime['native_cap'] == 100 and lifetime['parent_cap'] == 20
        and lifetime['gpu_hours_cap'] == 2, 'fixed_separate_caps')
    policy.require(lifetime['started_unix'] <= now < lifetime['native_deadline_unix']
        < lifetime['hard_deadline_unix'] <= lifetime['started_unix'] + 7200
        and lifetime['hard_deadline_unix'] <= lifetime['lease_end_unix'] - 21600, 'finite_original_lifetime')
    return lifetime


def verify(root):
    policy.require(root == ROOT and root.resolve() == root and common.host_identity() == policy.HOST_SHA,
        'exact_root_and_hashed_host')
    sources = read(root / 'SOURCE_SHA256.json')
    for relative, expected in sources.items():
        path = Path(relative)
        policy.require(not path.is_absolute() and '..' not in path.parts
            and sha(root / 'source' / path) == expected, 'frozen_source_bytes')
    return sources


def prepare(root):
    policy.require(os.environ.get('CUDA_VISIBLE_DEVICES') == '', 'cpu_prepare_only')
    verify(root)
    policy.require(not (root / 'READY.json').exists(), 'prepare_once')
    prior, prior_ready = read(ANCHORS / 'PLAN.json'), read(ANCHORS / 'READY.json')
    policy.require(read(ANCHORS / 'readout/COMPLETE.json')['status'] == 'COMPLETE', 'anchor_natural_complete')
    metadata, context = anchors.common.metadata(prior['model_dir'])
    policy.require(metadata == prior_ready['model_metadata'] and context >= policy.CONTEXT, 'unchanged_base_metadata')
    tokenizer = anchors.common.native.source.native.load_local_tokenizer(prior['model_dir'])
    tasks = policy.tasks()
    cohort_check = policy.validate_cohort(tasks, read(root / 'EXCLUSIONS.json'))
    tokenization = []
    for task in tasks:
        tokens = tokenizer.apply_chat_template(policy.messages(task), tokenize=True, add_generation_prompt=True, return_dict=False)
        policy.require(policy.token_budget(len(tokens)) == policy.OUTPUT, 'initial_context_fits')
        tokenization.append(dict(task_id=task['task_id'], prompt_tokens=len(tokens), prompt_ids_sha256=policy.digest(tokens)))
    engine = Engine(prior['model_dir'], tokenizer, device='cpu', check=lambda label: None)
    base_identity = dict(base_sha256=engine.loaded_base_sha256, no_adapter=assert_no_adapter(engine.model),
        runtime=engine.runtime, native_calls=0, weight_updates=0)
    del engine
    tests = read(root / 'CPU_TESTS.json')
    policy.require(tests['passed'] is True, 'own_cpu_tests_pass')
    started = time.time()
    lifetime = dict(started_unix=started, native_deadline_unix=started+7080, hard_deadline_unix=started+7200,
        lease_end_unix=common.LEASE_END, gpu_hours_cap=2, native_cap=100, parent_cap=20)
    validate_lifetime(lifetime, time.time())
    policy.require(lifetime['hard_deadline_unix'] <= common.LEASE_END - 21600, 'lease_margin')
    write(root / 'COHORT_PRIVATE.json', tasks)
    write(root / 'RESERVATIONS.json', policy.schedule(tasks))
    write(root / 'LIFETIME.json', lifetime)
    write(root / 'BASE_CPU_IDENTITY.json', base_identity)
    lane = root / LANE
    lane.mkdir(exist_ok=False)
    (lane / QUEUE).mkdir()
    ready = dict(schema=policy.VERSION, index=0, gpu_uuid=policy.GPU_UUID, base_sha256=policy.BASE_SHA,
        model_dir=prior['model_dir'], model_metadata=metadata, context=policy.CONTEXT, output_cap=policy.OUTPUT,
        cohort_check=cohort_check, tokenization=tokenization, parent_files=read(root / 'PROVIDER_FILES.json'),
        files={name: sha(root / name) for name in ('SOURCE_SHA256.json', 'EXCLUSIONS.json', 'COHORT_PRIVATE.json',
            'RESERVATIONS.json', 'LIFETIME.json', 'BASE_CPU_IDENTITY.json', 'CPU_TESTS.json', 'PROVIDER_FILES.json')},
        no_adapter=True, optimizer_updates=0, no_L2_to_L1=True, exploratory_not_retained_weight_learning=True)
    write(root / 'READY.json', ready)
    write(lane / 'READY.json', ready)
    return dict(status='READY', ready_sha256=sha(root / 'READY.json'), lifetime=lifetime,
        cohort_sha256=sha(root / 'COHORT_PRIVATE.json'), planned_native=100, planned_parents=20)


def validate_ready(root):
    verify(root)
    ready = read(root / 'READY.json')
    for name, expected in ready['files'].items():
        policy.require(sha(root / name) == expected, 'frozen_ready_input')
    policy.require(ready['gpu_uuid'] == policy.GPU_UUID and ready['index'] == 0
        and ready['base_sha256'] == policy.BASE_SHA and ready['no_adapter'] is True
        and ready['context'] == policy.CONTEXT and ready['output_cap'] == policy.OUTPUT, 'allocated_base_only')
    validate_lifetime(read(root / 'LIFETIME.json'), time.time())
    policy.require(read(root / 'COHORT_PRIVATE.json') == policy.tasks()
        and read(root / 'RESERVATIONS.json') == policy.schedule(policy.tasks()), 'exact_frozen_reservations')
    publication = read(root / 'PUBLICATION.json')
    policy.require(publication['ready_sha256'] == sha(root / 'READY.json')
        and publication['own_cpu_tests_passed'] is True and publication['dated_builder_publication']
        and publication['board_allocation'], 'pre_gpu_publication')
    return ready


def begin_cell(root, task, phase):
    cell = next((row for row in read(root / 'RESERVATIONS.json')
        if row['task_id'] == task['task_id'] and row['phase'] == phase), None)
    policy.require(cell is not None, 'reserved_schedule_cell_required')
    path = root / LANE / 'cells' / (cell['cell_id'] + '.json')
    path.parent.mkdir(exist_ok=True)
    record = dict(cell, status='STARTED', started_unix=time.time())
    with path.open('x') as stream:
        json.dump(record, stream, sort_keys=True)
        stream.flush()
        os.fsync(stream.fileno())
    return path, record


def generate(root, engine, task, phase, messages, check):
    check('dispatch')
    path, record = begin_cell(root, task, phase)
    try:
        tokens = engine.tokenizer.apply_chat_template(messages, tokenize=True, add_generation_prompt=True, return_dict=False)
        record['response'] = engine.generate(messages, max_new_tokens=policy.token_budget(len(tokens)), reflection=phase == 'reflection')
        record['outcome'] = policy.outcome(task, record['response']) if phase != 'reflection' else dict(
            audit_status='UNREVIEWED', reflection_guard=record['response'].get('reflection_guard'))
        record['status'] = 'COMPLETE'
    except BaseException as error:
        record.update(status='FAILED', error_type=type(error).__name__)
        raise
    finally:
        record['finished_unix'] = time.time()
        write(path, record)
    return record


def parent(root, task, original, memory, check):
    check('parent_dispatch')
    path, record = begin_cell(root, task, 'parent')
    lane = root / LANE
    identifier = f'GUIDED_SLEEP_C{task["cycle"]}_P{task["slot"]}'
    request_path = lane / QUEUE / (identifier + '.request.json')
    payload = policy.parent_payload(task, original, memory)
    write(request_path, dict(id=identifier, payload=payload, payload_sha256=policy.digest(payload),
        ready_sha256=sha(root / 'READY.json')))
    until = min(time.time()+300, read(root / 'LIFETIME.json')['native_deadline_unix'])
    response_path = request_path.with_name(identifier + '.response.json')
    try:
        while not response_path.exists():
            check('parent_wait')
            policy.require(time.time() < until, 'parent_timeout_no_retry')
            time.sleep(2)
        result = read(response_path)
        policy.require(result['status'] == 'COMPLETE' and result['request_sha256'] == sha(request_path), 'actual_parent_join')
        archive = result['archive']
        directory = Path(archive['remote_root'])
        policy.require(directory.is_relative_to(root / 'parent_transcripts' / LANE), 'own_parent_archive')
        for name, expected in archive['files'].items():
            policy.require(not Path(name).is_absolute() and '..' not in Path(name).parts
                and sha(directory / name) == expected, 'parent_archive_hash')
        plan = parse_parent(read(directory / 'RAW_RESPONSE.json'), [task['task_id']])
        policy.require(plan == result['plan'] == read(directory / 'PLAN.json'), 'actual_astra_plan')
        lesson = policy.parent_lesson(plan, task)
        record.update(status='COMPLETE', lesson=lesson, result=result, held_exposed=False)
    except BaseException as error:
        record.update(status='FAILED', error_type=type(error).__name__)
        raise
    finally:
        record['finished_unix'] = time.time()
        write(path, record)
    return record


def cycles(root, engine, check, parent_call=parent):
    memory = ''
    tasks = read(root / 'COHORT_PRIVATE.json')
    for cycle in range(1, 11):
        episode_rows, held_rows = [], []
        for task in [row for row in tasks if row['cycle'] == cycle]:
            if task['split'] == 'TRAIN':
                original = generate(root, engine, task, 'original', policy.messages(task, memory), check)
                intervention = parent_call(root, task, original, memory, check)
                reflection_messages = [dict(role='system', content=policy.REFLECTION_SYSTEM),
                    dict(role='user', content=json.dumps(dict(actual_train_prompt=task['prompt'],
                        own_attempt=original['response']['raw'], failure_class=original['outcome']['failure_class'],
                        actual_parent_message=intervention['lesson'], prior_own_reflection=memory), sort_keys=True))]
                reflection = generate(root, engine, task, 'reflection', reflection_messages, check)
                continuation_messages = policy.messages(task, memory) + [
                    dict(role='assistant', content=original['response']['raw']),
                    dict(role='user', content='Actual parent guidance:\n'+intervention['lesson']+
                        '\nYour own actual reflection:\n'+reflection['response']['raw']+
                        '\nContinue this TRAIN task now. Final nonempty line: {"expression":"..."}.')]
                continuation = generate(root, engine, task, 'continuation', continuation_messages, check)
                triple = policy.triple(task, original, intervention, reflection, continuation)
                write(root / LANE / f'TRIPLE_C{cycle}_E{task["slot"]}.json', triple)
                episode_rows.append(triple)
                memory = reflection['response']['raw']
            else:
                held = generate(root, engine, task, 'held', policy.messages(task, memory), check)
                held_rows.append(dict(task_id=task['task_id'], outcome=held['outcome'], parent_free=True,
                    direct_parent_text=False, own_train_reflection_carried=True, sealed_from_parent=True))
        engine.verify_base()
        write(root / LANE / f'CYCLE_{cycle:02d}_COMPLETE.json', dict(cycle=cycle, status='COMPLETE',
            finished_unix=time.time(), train_triples=len(episode_rows), held=held_rows,
            no_adapter=assert_no_adapter(engine.model), updates=0, retained_weight_learning_claim=False))


def native(root):
    ready = validate_ready(root)
    policy.require(os.environ.get('CUDA_VISIBLE_DEVICES') == policy.GPU_UUID, 'only_physical0_uuid')
    lifetime, lane = read(root / 'LIFETIME.json'), root / LANE
    finalized, engine = False, None
    def check(label):
        cutoff = lifetime['hard_deadline_unix']-30 if finalized else lifetime['native_deadline_unix']
        policy.require(time.time() < cutoff, 'fixed_lifetime_no_reset:'+label)
    write(lane / 'NATIVE_REQUEST.json', dict(started_unix=time.time(), process=common.process_identity(Path('/proc') / str(os.getpid())),
        ready_sha256=sha(root / 'READY.json'), native_cap=100, parent_cap=20))
    failure = None
    try:
        tokenizer = anchors.common.native.source.native.load_local_tokenizer(ready['model_dir'])
        engine = Engine(ready['model_dir'], tokenizer, device='cuda:0', check=check)
        write(lane / 'BEFORE.json', dict(base_sha256=engine.loaded_base_sha256, no_adapter=assert_no_adapter(engine.model),
            updates=0, runtime=engine.runtime))
        cycles(root, engine, check)
    except BaseException as error:
        failure = error
    finally:
        finalized = True
        try:
            policy.require(engine is not None, 'loaded_base_required')
            engine.verify_base()
            policy.require(anchors.common.metadata(ready['model_dir'])[0] == ready['model_metadata'], 'after_metadata')
            write(lane / 'AFTER.json', dict(status='PASS', base_sha256=policy.BASE_SHA,
                no_adapter=assert_no_adapter(engine.model), updates=0))
        except BaseException as error:
            failure = failure or error
            write(lane / 'AFTER.json', dict(status='FAILED', error_type=type(error).__name__))
        cells = [read(path) for path in (lane / 'cells').glob('*.json')]
        counts = Counter((cell['kind'], cell['status']) for cell in cells)
        complete = failure is None and counts['NATIVE', 'COMPLETE'] == 100 and counts['PARENT', 'COMPLETE'] == 20
        write(lane / ('COMPLETE.json' if complete else 'FAILED.json'), dict(status='COMPLETE' if complete else 'FAILED',
            finished_unix=time.time(), native_started=sum(cell['kind']=='NATIVE' for cell in cells),
            native_complete=counts['NATIVE', 'COMPLETE'], parent_started=sum(cell['kind']=='PARENT' for cell in cells),
            parent_complete=counts['PARENT', 'COMPLETE'], cycles=len(list(lane.glob('CYCLE_*_COMPLETE.json'))),
            error_type=type(failure).__name__ if failure else None, updates=0, no_refill=True))
    if failure:
        raise failure


def guard(root):
    validate_ready(root)
    policy.require(os.environ.get('CUDA_VISIBLE_DEVICES') == '', 'cpu_guard_only')
    lane, lifetime = root / LANE, read(root / 'LIFETIME.json')
    (lane / 'GUARD_ONCE').mkdir(exist_ok=False)
    child = identity = None
    status = 'FAILED'
    try:
        prior_request = read(ANCHORS / 'readout/REQUEST.json')['process']
        prior_proc = Path('/proc') / str(prior_request[1]) / 'stat'
        policy.require(not prior_proc.exists() or prior_proc.read_text().rsplit(')',1)[1].split()[19] != str(prior_request[2]),
            'natural_anchor_release_required')
        cutoff = min(time.time()+600, lifetime['native_deadline_unix'])
        snapshot = None
        for attempt in range(200):
            policy.require(time.time() < cutoff, 'bounded_admission_window')
            snapshot = anchors.ownership.continual.scan(0, anchors.ownership.continual.ROOT / 'SERVICE_IDENTITY.json')
            write(lane / f'ADMISSION_{attempt:03d}.json', snapshot)
            if snapshot['clear'] is True:
                anchors.ownership.validate_scan(snapshot, time.time())
                break
            policy.require(anchors.rescan.transient(snapshot), 'real_ownership_block_no_waiver')
            time.sleep(3)
        policy.require(snapshot is not None and snapshot['clear'] is True, 'strict_privileged_clear_required')
        write(lane / 'ADMISSION.json', snapshot)
        with (lane / 'native.log').open('x') as log:
            child = subprocess.Popen([common.PYTHON, '-B', '-m', 'gpu.orch_r108_code_parent_run', 'native', '--root', str(root)],
                cwd=root / 'source', start_new_session=True, stdout=log, stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL,
                env=dict(os.environ, CUDA_VISIBLE_DEVICES=policy.GPU_UUID, PYTHONPATH=str(root / 'source'),
                    HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1', PYTHONDONTWRITEBYTECODE='1', OMP_NUM_THREADS='1', MKL_NUM_THREADS='1'))
        identity = common.process_identity(Path('/proc') / str(child.pid))
        write(lane / 'LAUNCH.json', dict(pid=child.pid, identity=identity, started_unix=time.time(),
            ready_sha256=sha(root / 'READY.json'), admission_sha256=sha(lane / 'ADMISSION.json'), uuid=policy.GPU_UUID))
        while child.poll() is None:
            policy.require(time.time() < lifetime['hard_deadline_unix']-30, 'hard_lifetime_guard')
            time.sleep(2)
        policy.require(child.returncode == 0 and (lane / 'COMPLETE.json').exists(), 'no_native_retry')
        status = 'COMPLETE'
    except BaseException as error:
        write(lane / 'GUARD_FAILED.json', dict(status='FAILED', error_type=type(error).__name__, finished_unix=time.time()))
        raise
    finally:
        if child is not None:
            common.stop_owned(child, identity)
        write(lane / 'TERMINAL.json', dict(status=status, finished_unix=time.time(), no_refill=True))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('phase', choices=('prepare', 'native', 'guard'))
    parser.add_argument('--root', type=Path, required=True)
    arguments = parser.parse_args()
    result = globals()[arguments.phase](arguments.root)
    if result is not None:
        print(json.dumps(result, sort_keys=True))
