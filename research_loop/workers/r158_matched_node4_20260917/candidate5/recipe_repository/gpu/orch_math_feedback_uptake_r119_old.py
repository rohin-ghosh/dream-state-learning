"""Explicit lease continuation of owned R110 BASE contexts, never weight sleep."""

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
import time


ROOT = Path('/localhome/local-rohing/orch_math_feedback_uptake_r110_20260915_attempt1')
DIRECTORY = 'R119_LEASE_V3'
SOURCE_NAMES = tuple('orch_math_feedback_uptake_r119_old' + suffix + '.py'
                     for suffix in ('', '_native', '_scan', '_broker'))


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def read(path):
    return json.loads(Path(path).read_text())


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x') as stream:
        json.dump(value, stream, sort_keys=True, indent=2)


def clock(lease_end, now):
    require(type(lease_end) in (int, float) and lease_end == 1789689600,
            'existing_node3_lease_binding')
    hard = lease_end - 21600
    require(now < hard - 900, 'lease_margin')
    return dict(hard_deadline_unix=hard, native_deadline_unix=hard - 300,
                lease_end_unix=lease_end, margin_seconds=21600)


def legacy():
    import gpu
    import organism_v6
    gpu.__path__ = [str(ROOT / 'source/gpu'), *gpu.__path__]
    organism_v6.__path__ = [str(ROOT / 'source/organism_v6'), *organism_v6.__path__]
    from gpu import orch_math_feedback_uptake_r110_run as old
    old.validate(ROOT)
    return old


def load_native():
    path = Path(__file__).with_name('orch_math_feedback_uptake_r119_old_native.py')
    spec = importlib.util.spec_from_file_location('math_lease_native', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def reconstruct(lane, index, policy):
    require(index in (1, 2), 'only_current_owned_slots')
    cycle = {1: 33, 2: 53}[index]
    phase = 'experience' if index == 1 else 'readout'
    previous = lane / f'cycle{cycle}/experience'
    state = read(previous / 'STATE.json')
    calls = [read(path) for path in sorted(previous.glob('CALL_*.json'))]
    require(len(calls) == (7 if index == 1 else 8)
            and all('response' in call and 'error' not in call for call in calls),
            'genuine_completed_prefix')
    require(not (lane / f'cycle{cycle}/readout').exists(), 'no_readout_replay')
    tasks = read(lane / 'COHORT.json')['train'][cycle - 1]
    records = read(previous / 'EPISODES.json')
    expected = [(task, purpose) for task in tasks for purpose in ('experience', 'check', 'revision')]
    require([(call['task_id'], call['purpose']) for call in calls[:6]] ==
            [(task['id'], purpose) for task, purpose in expected], 'exact_task_prefix')
    for task in tasks:
        require(records[task['id']] == [policy.record(task, purpose, call['response'])
            for (bound_task, purpose), call in zip(expected, calls)
            if bound_task['id'] == task['id']], 'actual_source_records')
    dialogue = read(previous / 'METACOGNITION_DIALOGUE.json')
    require(len(dialogue) == len(calls) - 6
            and all(event['response'] == call['response']
                    for event, call in zip(dialogue, calls[6:])), 'actual_dialogue_prefix')
    disposition = None
    if index == 1:
        require(state['completed_train_segments'] == 262
                and read(lane / 'RESIDENT_FAILED.json')['error'] == 'parent_timeout_no_retry',
                'exact_interrupted_parent_boundary')
        triple = read(previous / 'TRIPLE_0518.json')
        require(triple['parent_intervention'] == state['pending']
                and triple['subsequent_behavior']['sha256'] == sha(previous / 'CALL_0518.json'),
                'pending_parent_actually_consumed')
        queue = lane / 'r110_parent_queue/GUIDED_SLEEP_C033_T263.request.json'
        require(queue.exists(), 'failed_parent_charge_preserved')
        event = dialogue[0]
        state = deepcopy(state)
        state.update(completed_train_segments=263, pending=None,
            memory=dict(task_id=f'R110_DISTILL_TRAIN_C{cycle}',
                question='Prior own metacognition/context distillation; not certified facts.',
                trace=event['response']['raw'], source_record_sha256=policy.digest(event),
                outcome=event['outcome'], original_outcome=event['outcome']))
        disposition = dict(segment=263, status='MISSING', reason='original_parent_timeout_no_retry',
                           request_sha256=sha(queue), retried=False, previous_guidance_preserved=True)
    else:
        complete = read(previous / 'COMPLETE.json')
        require(complete['status'] == 'COMPLETE' and complete['state_sha256'] == sha(previous / 'STATE.json')
                and state['completed_train_segments'] == 424
                and read(previous / 'AFTER.json')['actual_mounted_base_verified'], 'genuine_completed_context')
    incoming = read(lane / f'cycle{cycle - 1}/experience/STATE.json')['memory']
    return cycle, phase, state, records, dialogue, incoming, disposition


def prepare(index):
    require(index in (1, 2) and os.environ.get('CUDA_VISIBLE_DEVICES') == '', 'cpu_owned_prepare')
    old = legacy()
    lane = ROOT / f'campaign_node3_style{index}'
    output = lane / DIRECTORY
    require(not output.exists(), 'one_explicit_continuation')
    identities = [read(lane / 'LAUNCH.json')['identity'], read(lane / 'ACTIVATION.json')['guardian']]
    require(all(not Path('/proc', str(identity['pid'])).exists() for identity in identities), 'old_actors_absent')
    cycle, phase, state, records, dialogue, incoming, disposition = reconstruct(lane, index, old.policy)
    preserved = {str(path.relative_to(lane)): sha(path) for path in lane.rglob('*') if path.is_file()}
    ledgers = {name: dict(sha256=sha(lane / name), bytes=(lane / name).stat().st_size,
                         count=len((lane / name).read_text().splitlines()))
               for name in ('CALLS_NATIVE.jsonl', 'CALLS_PARENT.jsonl')}
    require([ledgers[name]['count'] for name in ledgers] == ([519, 99] if index == 1 else [840, 57]),
            'exact_original_charged_work')
    lease = read(ROOT / 'FAMILY_READY.json')['lease_cutoff_unix']
    output.mkdir()
    for name, value in [('INITIAL_STATE', state), ('INITIAL_EPISODES', records),
                        ('INITIAL_DIALOGUE', dialogue), ('INCOMING_MEMORY', incoming)]:
        write(output / (name + '.json'), value)
    plan = dict(schema='MATH_R119_BASE_LEASE_CONTINUATION_V1', root=str(lane), index=index,
        uuid=old.policy.DEVICES[index], next_cycle=cycle, next_phase=phase,
        completed_prefix=7 if index == 1 else 0, clock=clock(lease, time.time()),
        initial_files={name: sha(output / name) for name in ('INITIAL_STATE.json', 'INITIAL_EPISODES.json',
            'INITIAL_DIALOGUE.json', 'INCOMING_MEMORY.json')},
        preserved=preserved, ledger_prefixes=ledgers, prior_identities=identities,
        source_files={str(Path(__file__).with_name(name)): sha(Path(__file__).with_name(name)) for name in SOURCE_NAMES},
        ready_sha256=sha(lane / 'READY.json'), cohort_sha256=sha(lane / 'COHORT.json'),
        old_activation_sha256=sha(lane / 'ACTIVATION.json'), original_caps=read(lane / 'READY.json')['budget'],
        failed_parent_disposition=disposition, original_lease_receipt_sha256=sha(ROOT / 'FAMILY_READY.json'),
        authorization='Main direct 2026-09-15T17:17Z allocation + Rohin report-cut-not-stop',
        no_weight_writes=True, context_only=True, no_replay=True, prepared_unix=time.time())
    write(output / 'PLAN.json', plan)
    return dict(root=str(output), plan_sha256=sha(output / 'PLAN.json'), clock=plan['clock'],
                next_cycle=cycle, next_phase=phase, ledger_prefixes=ledgers)


def validate(index):
    old = legacy()
    lane = ROOT / f'campaign_node3_style{index}'
    output = lane / DIRECTORY
    plan = read(output / 'PLAN.json')
    require(index in (1, 2) and plan['index'] == index and plan['root'] == str(lane), 'owned_lane')
    require(plan['clock'] == clock(read(ROOT / 'FAMILY_READY.json')['lease_cutoff_unix'], time.time()), 'bound_clock')
    for path, digest in plan['source_files'].items():
        require(sha(path) == digest, 'immutable_continuation_source')
    for name, digest in plan['initial_files'].items():
        require(sha(output / name) == digest, 'authentic_context')
    for name, digest in plan['preserved'].items():
        if name not in plan['ledger_prefixes']:
            require(sha(lane / name) == digest, 'old_artifact_untouched:' + name)
    for name, prefix in plan['ledger_prefixes'].items():
        require(hashlib.sha256((lane / name).read_bytes()[:prefix['bytes']]).hexdigest() == prefix['sha256'], 'append_only_charges')
    return old, lane, output, plan


def resident(index):
    old, lane, output, plan = validate(index)
    driver = load_native()
    cached = []
    engine = old.machinery.previous.response_contract.engine_class(old.machinery.previous.direct.Engine)
    guarded = driver.reflection.engine_class(engine)
    def factory(model_dir, tokenizer, device, check):
        if not cached:
            cached.append(guarded(model_dir, tokenizer, device=device, check=check))
        return cached[0]
    driver.reflection.engine_class = lambda engine_class: engine_class
    status = 'FAILED'
    try:
        for cycle in range(plan['next_cycle'], old.policy.CYCLES + 1):
            for phase in ('experience', 'readout'):
                if cycle == plan['next_cycle'] and plan['next_phase'] == 'readout' and phase == 'experience':
                    continue
                if time.time() >= plan['clock']['native_deadline_unix'] - 600:
                    status = 'LEASE_BOUNDARY'
                    return
                driver.run(lane, index, cycle, phase, factory, old.validate, sha(output / 'PLAN.json'))
                complete = read(output / f'cycle{cycle}/{phase}/COMPLETE.json')
                require(complete['status'] == 'COMPLETE', 'actual_completed_phase')
        status = 'ORIGINAL_COHORT_EXHAUSTED'
    except BaseException as error:
        write(output / 'RESIDENT_FAILED.json', dict(type=type(error).__name__, error=str(error), finished_unix=time.time()))
        raise
    finally:
        write(output / 'RESIDENT_TERMINAL.json', dict(status=status, loads=len(cached),
            process=old.driver.reuse.driver.seam.native.process_identity(), finished_unix=time.time()))


def guard(index):
    old, lane, output, plan = validate(index)
    require(read(Path(__file__).parents[1] / 'CPU_TESTS.json')['passed'], 'native_cpu_tests')
    require(all(not Path('/proc', str(identity['pid'])).exists() for identity in plan['prior_identities']), 'predecessor_absence')
    with (output / 'GUARD.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        require(not (output / 'LAUNCH.json').exists(), 'single_native_attempt')
        scan_path = Path(__file__).with_name('orch_math_feedback_uptake_r119_old_scan.py')
        report = subprocess.run(['sudo', '-n', 'env', 'CUDA_VISIBLE_DEVICES=',
            'PYTHONPATH=' + str(old.LIBRARY / 'source'), 'PYTHONDONTWRITEBYTECODE=1',
            'python3', '-B', str(scan_path), '--index', str(index)], capture_output=True, text=True, check=True, timeout=120)
        admission = json.loads(report.stdout)
        write(output / 'ADMISSION.json', admission)
        require(admission['clear'] and admission['scanner_euid'] == 0 and not admission['blocking_reasons']
            and admission['gpu']['index'] == index and admission['gpu']['uuid'] == plan['uuid'], 'strict_pinned_full_proc')
        child = identity = None
        status = 'FAILED'
        def interrupted(signum, frame):
            raise SystemExit(128 + signum)
        signal.signal(signal.SIGTERM, interrupted)
        signal.signal(signal.SIGINT, interrupted)
        try:
            with (output / 'NATIVE.log').open('x') as log:
                child = subprocess.Popen([old.machinery.previous.existing.PYTHON, '-B', str(Path(__file__)),
                    'resident', '--index', str(index)], cwd=old.LIBRARY / 'source', start_new_session=True,
                    stdin=subprocess.DEVNULL, stdout=log, stderr=subprocess.STDOUT,
                    env=dict(os.environ, CUDA_VISIBLE_DEVICES=plan['uuid'], PYTHONPATH=str(old.LIBRARY / 'source'),
                        HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1', OMP_NUM_THREADS='1', MKL_NUM_THREADS='1'))
                identity = old.common.process_identity(Path('/proc', str(child.pid)))
                write(output / 'LAUNCH.json', dict(identity=identity, plan_sha256=sha(output / 'PLAN.json'), started_unix=time.time()))
                require(child.wait(timeout=plan['clock']['hard_deadline_unix'] - 120 - time.time()) == 0, 'native_failure_no_retry')
                status = read(output / 'RESIDENT_TERMINAL.json')['status']
        finally:
            if child is not None:
                old.common.stop_owned(child, identity)
            write(output / 'TERMINAL.json', dict(status=status, finished_unix=time.time(), foreign_signals=0))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=('prepare', 'guard', 'resident'))
    parser.add_argument('--index', type=int, choices=(1, 2), required=True)
    arguments = parser.parse_args()
    result = globals()[arguments.action](arguments.index)
    if result is not None:
        print(json.dumps(result))
