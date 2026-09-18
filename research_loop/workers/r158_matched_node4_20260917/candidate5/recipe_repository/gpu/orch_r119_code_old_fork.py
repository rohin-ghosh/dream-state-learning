"""Explicit old BASE-context forks; optional frozen shared-gen1 adapter, no fitting."""

import argparse
from collections import Counter
from copy import deepcopy
import hashlib
import inspect
import json
import os
from pathlib import Path
import subprocess
import sys
import time
from types import FunctionType, SimpleNamespace

from gpu import orch_r119_code_continuation as io


require, read, ref, checked, write = io.require, io.read, io.ref, io.checked, io.write
MODULE = 'gpu.orch_r119_code_old_fork'
ALLOCATIONS = {'ovx2': (3, 4, 5, 6), 'a40r': (6,)}
PENDING = {}


def fresh_scan_retryable(report):
    return bool(report['blocking_reasons']) and all(reason.startswith((
        'process_identity_drift:', 'minor_scan_identity_changed:', 'minor_scan_process_drift:'))
        for reason in report['blocking_reasons'])


def ancestry(rows, saved_cycle, native_cap, parent_cap):
    require(bool(rows) and saved_cycle >= 1, 'actual_prior_context_and_charges')
    counts = Counter(row['kind'] for row in rows)
    last = max(row['cycle'] for row in rows)
    require(saved_cycle <= last, 'saved_context_not_future')
    return dict(saved_context_cycle=saved_cycle, last_charged_cycle=last,
        first_cycle=last + 1, native_used=counts['NATIVE'], parent_used=counts['PARENT'],
        native_cap=native_cap, parent_cap=parent_cap, label='FORK_OF_SAVED_BASE_CONTEXT',
        interrupted_original_preserved=True, replay_allowed=False)


def validate_plan(plan, now=None):
    now = time.time() if now is None else now
    require(plan['wrapper'] in ALLOCATIONS and plan['physical'] in ALLOCATIONS[plan['wrapper']],
        'only_Main_allocated_CODE_old_slots')
    require(plan['adapter'] is None if plan['wrapper'] == 'a40r' else plan['adapter'] is not None,
        'BASE_a40r_and_explicit_gen1_ovx2_forks')
    require(plan['hard_end_unix'] == plan['lease_end_unix'] - 21600
        and plan['train_end_unix'] == plan['hard_end_unix'] - 120
        and now < plan['train_end_unix'], 'actual_lease_minus_six_hours')
    require(plan['first_cycle'] == plan['ancestry']['first_cycle']
        and plan['first_cycle'] <= plan['cycle_limit'] <= 100, 'fixed_unseen_cycle_cursor')
    require(plan['parent_ttl_seconds'] == 600 and plan['parent_wait_seconds'] == 0
        and plan['parent_effort'] in ('low', 'medium') and plan['parent_cadence'] == 'EPISODE'
        and plan['optimizer_updates'] == 0, 'bound_nonblocking_parent_readonly_child')
    return plan


def plan_for(root):
    root = Path(root).resolve(strict=True)
    plan = validate_plan(read(root / 'PLAN.json'))
    require(plan['root'] == str(root), 'exact_fork_root')
    for path, pin in plan['source_files'].items():
        require(ref(path)['sha256'] == pin, 'frozen_fork_source')
    for entry in plan['inputs'].values():
        checked(entry)
    require(read(root / 'CPU_TESTS.json')['passed'] is True, 'own_CPU_tests_before_GPU')
    if plan['adapter'] is not None:
        require(plan['adapter']['checkpoint_sha256'] ==
            '43ce68acabb18f661ff929600239eb0a632981da841dd1182f886a85df78a02d', 'exact_authorized_gen1')
        for name, pin in plan['adapter']['files']:
            require(ref(Path(plan['adapter']['path']) / name)['sha256'] == pin, 'readonly_adapter_files')
    return plan


def bound_scan(root, service=False):
    from gpu import orch_rich_hot_a100_minor_scan as scanner
    plan = plan_for(root)
    require(os.geteuid() == 0 and scanner.pinned.host_identity() == plan['host_sha256'],
        'privileged_hashed_destination')
    def allocation(index):
        require(index == plan['physical'], 'exact_owned_physical')
        return plan['gpu_uuid']
    scanner.pinned.policy = SimpleNamespace(DEVICES={plan['physical']: plan['gpu_uuid']},
        HOST_SHA=plan['host_sha256'], allocation=allocation, require=require)
    path = Path(root) / 'SERVICE_IDENTITY.json'
    if service:
        scanner.pinned.service(path)
        return dict(service=ref(path))
    return scanner.scan(plan['physical'], path)


def configured(root):
    from gpu import orch_r108_code_parent_r109_run as run
    plan = plan_for(root)
    root = Path(root)
    run.ROOT = root
    original_begin = run.begin
    def begin(checked_root, task, phase):
        require(Path(checked_root) == root and task['cycle'] >= plan['first_cycle'], 'no_ancestor_call_replay')
        kind = 'PARENT' if phase.startswith(('parent', 'meta_parent')) else 'NATIVE'
        counts = Counter(read(path)['kind'] for path in (root / run.LANE / 'cells').glob('*.json'))
        key = 'parent' if kind == 'PARENT' else 'native'
        require(plan['ancestry'][key + '_used'] + counts[kind] < plan['ancestry'][key + '_cap'],
            'inherited_absolute_call_cap')
        return original_begin(root, task, phase)
    run.begin = begin
    run.validate = lambda checked_root, arm: plan if Path(checked_root) == root else require(False, 'owned_root')
    original_generate = run.generate
    def generate(checked_root, engine, task, phase, messages, check):
        applied = poll_parents(root, plan) if task['split'] == 'TRAIN' else []
        if applied:
            messages = list(messages) + [dict(role='user', content='Parent guidance received since your previous turn:\n'
                + '\n\n'.join(item['guidance'] for item in applied))]
        row = original_generate(checked_root, engine, task, phase, messages, check)
        row.update(injected_parent_ids=[item['id'] for item in applied], model_binding=engine.identity(),
            parent_wait_seconds=0)
        run.write(root / run.LANE / 'cells' / (row['cell_id'] + '.json'), row)
        for item in applied:
            write(root / 'delayed_interventions' / (item['id'] + '.json'), dict(parent=item,
                continuation=ref(root / run.LANE / 'cells' / (row['cell_id'] + '.json')),
                semantic_change='UNASSESSED', no_optimizer=True))
        return row
    run.generate = generate
    def save_triple(checked_root, arm, task, segment, before, intervention, reflection_row, after):
        run.write(root / run.LANE / f'OBSERVATION_C{task["cycle"]:03d}_E{task["slot"]}_S{segment}.json',
            dict(before_call=before['cell_id'], reflection_call=reflection_row['cell_id'],
                after_call=after['cell_id'], parent_status=intervention['status'],
                actual_parent_triple=False, delayed_interventions_recorded_separately=True))
    run.save_triple = save_triple
    return run, plan


def parent_payload(plan, task, records, memory, payload=None):
    require(task['split'] == 'TRAIN' or task['slot'] == 0, 'TRAIN_only_parent')
    events = []
    def event(actor, text):
        events.append(dict(sequence=len(events), actor=actor, text=text,
            source_sha256=hashlib.sha256(text.encode()).hexdigest(), visibility='TRAIN_PUBLIC'))
    if task['slot'] != 0:
        event('environment', task['prompt'])
    for record in records:
        event('child', record['response']['raw'])
    if memory:
        event('child', memory)
    if payload is not None:
        event('child', json.dumps(dict(actual_dialogue=payload.get('dialogue', []),
            own_prior_context=memory), sort_keys=True))
    require(any(entry['actor'] == 'child' and entry['text'] for entry in events), 'actual_child_context_required')
    return dict(schema='r111_train_public_v1', life_id=plan['life_id'], cycle=task['cycle'],
        episode=max(0, task['slot'] - 1), phase='presleep_metacognition' if task['slot'] == 0 else 'experience',
        game='code', task_id=task['task_id'], task_provenance=dict(split='TRAIN',
            task_sha256=plan['train_tasks'][task['task_id']], cohort_sha256=plan['cohort_sha256']), events=events)


def parent_call(root, arm, task, segment, records, memory, lessons, check, payload=None):
    from gpu import orch_r108_code_parent_r109_run as run
    from gpu import orch_r110_claude_broker as provider
    root = Path(root)
    plan = read(root / 'PLAN.json')
    check('parent')
    if task['slot'] == 0:
        return dict(status='NOT_SCHEDULED', lesson='', declared_intervention_classes=[],
            intervention_available=False, provider_dispatched=False)
    require(task['split'] == 'TRAIN' and segment == 2, 'one_parent_per_TRAIN_episode')
    phase = ('meta_parent' if task['slot'] == 0 else 'parent') + str(segment)
    path, record = run.begin(root, task, phase)
    identifier = record['cell_id']
    public = parent_payload(plan, task, records, memory, payload)
    until = min(time.time() + plan['parent_ttl_seconds'], plan['train_end_unix'])
    request_path = root / 'parent_queue' / (identifier + '.request.json')
    request = dict(id=identifier, payload=public, payload_sha256=provider.digest(public), lane_deadline_unix=until)
    write(request_path, request)
    record.update(status='PENDING', lesson='', intervention_available=False, deadline_unix=until,
        asynchronous=True, wait_seconds=0, declared_intervention_classes=[], retry=False)
    run.write(path, record)
    PENDING.setdefault(str(root), {})[identifier] = dict(path=path, record=record, request=request)
    return record


def poll_parents(root, plan, now=None):
    from gpu import orch_r110_claude_broker as provider
    from gpu import orch_r108_code_parent_r109_run as run
    root = Path(root)
    now = time.time() if now is None else now
    applied = []
    pending = PENDING.setdefault(str(root), {})
    for identifier, entry in list(pending.items()):
        path = root / 'parent_queue' / (identifier + '.response.json')
        record, request = entry['record'], entry['request']
        if not path.exists() and now < record['deadline_unix']:
            continue
        record.update(status='MISSING', finished_unix=now, no_retry=True)
        try:
            if path.exists():
                result = read(path)
                archive = result.get('transcript_receipt', {})
                archive_root = Path(archive.get('remote_root', '/nonexistent'))
                files = archive.get('files', {})
                valid = result.get('id') == identifier and result.get('request_sha256') == provider.digest(request)
                valid = valid and result.get('payload_sha256') == request['payload_sha256']
                valid = valid and archive_root.is_absolute() and archive_root.is_relative_to(root)
                valid = valid and bool(files) and all(Path(name).name == name
                    and ref(archive_root / name)['sha256'] == pin for name, pin in files.items())
                valid = valid and result.get('actual_model') in plan['allowed_parent_models']
                record.update(response=ref(path), provider_dispatched=result.get('provider_dispatched'),
                    delivery_latency_seconds=now-record['started_unix'])
                if valid and now < record['deadline_unix'] and result.get('status') in ('COMPLETE', 'SILENT'):
                    record['status'] = result['status']
                    if result['status'] == 'COMPLETE':
                        guidance = result['plan']['guidance']
                        require(isinstance(guidance, str) and bool(guidance.strip()), 'usable_parent_guidance')
                        applied.append(dict(id=identifier, guidance=guidance, request_sha256=provider.digest(request),
                            response=ref(path), actual_model=result['actual_model']))
        except (ValueError, KeyError, OSError, TypeError):
            record['status'] = 'MISSING'
        run.write(entry['path'], record)
        del pending[identifier]
    return applied


def cycles_function(run, context, first_cycle):
    source = inspect.getsource(run.cycles)
    replacements = {"memory,lessons='',[]": 'memory,lessons=restored_memory,list(restored_lessons)',
        'range(1,policy.CYCLES+1)': 'range(first_cycle,policy.CYCLES+1)',
        'prior.assert_no_adapter(engine.model)': 'engine.identity()'}
    for old, new in replacements.items():
        require(source.count(old) == 1, 'exact_fixed_cycle_source:' + old)
        source = source.replace(old, new)
    namespace = dict(run.__dict__, restored_memory=context['own_context'],
        restored_lessons=context.get('lessons', []), first_cycle=first_cycle, parent=parent_call)
    exec(compile(source, __file__ + ':fixed_cycles', 'exec'), namespace)
    return namespace['cycles']


def load_engine(run, plan, check):
    from gpu import orch_r108_code_parent_engine as source
    from organism_v6.pcfl_vertical_train import _state_hash
    tokenizer = run.prior.anchors.common.native.source.native.load_local_tokenizer(plan['model_dir'])
    engine = source.Engine(plan['model_dir'], tokenizer, device='cuda:0', check=check)
    if plan['adapter'] is not None:
        from peft import PeftModel
        engine.model = PeftModel.from_pretrained(engine.model, plan['adapter']['path'], is_trainable=False)
        engine.model.requires_grad_(False)
        engine.model.eval()
    adapter_parameters = {name: value for name, value in engine.model.named_parameters() if 'lora_' in name}
    adapter_hash = _state_hash(adapter_parameters) if adapter_parameters else None
    require(bool(adapter_parameters) == (plan['adapter'] is not None), 'actual_BASE_or_LoRA_identity')
    def identity(model=None):
        require(not any(parameter.requires_grad for parameter in engine.model.parameters()), 'zero_trainable_parameters')
        return dict(kind='READ_ONLY_SHARED_GEN1_LORA_FORK' if adapter_parameters else 'PURE_BASE_CONTEXT_FORK',
            base_sha256=engine.loaded_base_sha256, adapter_sha256=adapter_hash, optimizer_updates=0)
    def verify():
        check('readonly_hash')
        identity()
        require(_state_hash(engine.base_references) == engine.loaded_base_sha256, 'unchanged_BASE_tensors')
        require((_state_hash(adapter_parameters) if adapter_parameters else None) == adapter_hash,
            'unchanged_adapter_tensors')
    engine.identity, engine.verify_base = identity, verify
    namespace = dict(source.Engine.generate.__globals__, assert_no_adapter=identity)
    engine.generate = FunctionType(source.Engine.generate.__code__, namespace,
        'generate', source.Engine.generate.__defaults__).__get__(engine)
    engine.generate.__func__.__kwdefaults__ = dict(source.Engine.generate.__kwdefaults__)
    return engine


def native(root):
    root = Path(root)
    run, plan = configured(root)
    require(os.environ.get('CUDA_VISIBLE_DEVICES') == plan['gpu_uuid'], 'exact_fork_CVD')
    (root / 'NATIVE_ONCE').mkdir()
    identity = run.common.process_identity(Path('/proc') / str(os.getpid()))
    write(root / 'NATIVE_REQUEST.json', dict(identity=identity, plan=ref(root / 'PLAN.json'), observed_unix=time.time()))
    def check(label):
        require(time.time() < plan['train_end_unix'], 'lease_end:' + label)
    engine, failure = None, None
    try:
        engine = load_engine(run, plan, check)
        write(root / 'ACTOR_READY.json', dict(identity=identity, model=engine.identity(), ancestry=plan['ancestry'],
            ready_unix=time.time(), model_reset_claim=False, no_optimizer=True))
        cycles_function(run, checked(plan['inputs']['context']), plan['first_cycle'])(root, plan['arm'], engine, check,
            parent_call=parent_call)
    except BaseException as error:
        failure = error
    finally:
        if engine is not None:
            engine.verify_base()
            write(root / 'AFTER.json', dict(model=engine.identity(), unchanged=True))
        write(root / 'TERMINAL.json', dict(status='FAILED' if failure else 'COMPLETE',
            error_type=type(failure).__name__ if failure else None, observed_unix=time.time(),
            optimizer_updates=0, retry=False))
    if failure:
        raise failure


def guard(root):
    root = Path(root)
    plan = plan_for(root)
    require(os.environ.get('CUDA_VISIBLE_DEVICES') == '', 'CPU_guard_only')
    require((root / 'PUBLICATION.json').exists(), 'own_CPU_and_allocation_logged_before_GPU')
    (root / 'GUARD_ONCE').mkdir()
    command = [plan['interpreter'], '-B', '-m', MODULE]
    base_env = dict(os.environ, PYTHONPATH=plan['source_root'], PYTHONDONTWRITEBYTECODE='1')
    for ordinal in range(20):
        result = subprocess.run(['sudo', '-n', 'env', 'CUDA_VISIBLE_DEVICES=',
            'PYTHONDONTWRITEBYTECODE=1', 'PYTHONPATH=' + plan['source_root'],
            'python3', '-B', '-m', MODULE, 'scan', '--root', str(root)],
            capture_output=True, text=True, check=True, timeout=120)
        report = json.loads(result.stdout)
        write(root / f'ADMISSION_{ordinal:02d}.json', report)
        if report['clear'] is True:
            break
        require(fresh_scan_retryable(report),
            'actual_occupancy_or_unknown_blocker_no_waiver')
        time.sleep(5)
    require(report['clear'] is True and report['scanner_euid'] == 0
        and report['gpu']['uuid'] == plan['gpu_uuid'] and report['gpu']['index'] == plan['physical'],
        'fresh_privileged_full_UUID_proc_CVD_CLEAR')
    from gpu import orch_r108_code_parent_r109_run as run
    with (root / 'NATIVE.log').open('x') as log:
        child = subprocess.Popen(command + ['native', '--root', str(root)],
            env=dict(base_env, CUDA_VISIBLE_DEVICES=plan['gpu_uuid']), cwd=plan['source_root'],
            stdin=subprocess.DEVNULL, stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
    identity = run.common.process_identity(Path('/proc') / str(child.pid))
    write(root / 'LAUNCH.json', dict(identity=identity, guardian=run.common.process_identity(Path('/proc') / str(os.getpid())),
        admission=ref(root / f'ADMISSION_{ordinal:02d}.json'), plan=ref(root / 'PLAN.json'), started_unix=time.time()))
    try:
        child.wait(timeout=max(1, plan['hard_end_unix'] - time.time() - 10))
    finally:
        run.common.stop_owned(child, identity)
        write(root / 'GUARD_TERMINAL.json', dict(returncode=child.poll(), observed_unix=time.time()))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('phase', choices=('native', 'guard', 'scan', 'service'))
    parser.add_argument('--root', type=Path, required=True)
    args = parser.parse_args()
    if args.phase in ('scan', 'service'):
        print(json.dumps(bound_scan(args.root, service=args.phase == 'service')))
    else:
        globals()[args.phase](args.root)
