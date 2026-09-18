"""Owned lane0 recovery; preserve R110 ledgers, captures, policy and deadlines."""

import argparse
from copy import deepcopy
import fcntl
import importlib.util
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time

import gpu
import organism_v6

LEGACY_SOURCE = Path('/localhome/local-rohing/orch_math_feedback_uptake_r110_20260915_attempt1/source')
if LEGACY_SOURCE.is_dir():
    gpu.__path__ = [str(LEGACY_SOURCE/'gpu'), *gpu.__path__]
    organism_v6.__path__ = [str(LEGACY_SOURCE/'organism_v6'), *organism_v6.__path__]

from gpu import orch_math_feedback_uptake_r110_run as old


common, require, policy = old.common, old.require, old.policy
LANE = old.ROOT / 'campaign_node3_style0'
DIRECTORY = 'R118_RECOVERY'
MODULE_PATH = Path(__file__).with_name('orch_math_feedback_uptake_r118_node3_native.py')
spec = importlib.util.spec_from_file_location('math_node3_recovery_native', MODULE_PATH)
native = importlib.util.module_from_spec(spec)
spec.loader.exec_module(native)


def reconstruct(root):
    previous = root / 'cycle7/experience'
    complete = common.read(previous / 'COMPLETE.json')
    require(complete['status'] == 'COMPLETE' and complete['state_sha256'] == common.sha(previous / 'STATE.json'), 'genuine_C7_state')
    readout = root / 'cycle7/readout'
    receipt = common.read(root / 'COMPLETE_C7_readout.json')
    require(receipt['complete_sha256'] == common.sha(readout / 'COMPLETE.json')
        and receipt['after_sha256'] == common.sha(readout / 'AFTER.json'), 'C7_readout_preserved')
    partial = root / 'cycle8/experience'
    require(common.read(root / 'RESIDENT_FAILED.json')['error'] == 'real_bound_parent'
        and common.read(partial / 'FAILED_AFTER.json')['verified'], 'known_verified_base_failure')
    tasks = common.read(root / 'COHORT.json')['train'][7]
    calls = [common.read(path) for path in sorted(partial.glob('CALL_*.json'))]
    require(len(calls) == 4 and all('response' in call and 'error' not in call for call in calls), 'exact_four_completed_calls')
    expected = [(tasks[0], purpose) for purpose in ('experience', 'check', 'revision')] + [(tasks[1], 'experience')]
    records = common.read(partial / 'EPISODES.json')
    for task in tasks:
        observed = [policy.record(task, purpose, call['response']) for (bound_task, purpose), call in zip(expected, calls)
            if bound_task['id'] == task['id']]
        require(records[task['id']] == observed, 'exact_sourced_records')
    require([(call['task_id'], call['purpose']) for call in calls] == [(task['id'], purpose) for task, purpose in expected], 'exact_completed_prefix')
    state = common.read(partial / 'STATE.json')
    require(state['completed_train_segments'] == 59 and state['pending']['segment'] == 59, 'saved_T59_state')
    require(calls[-1]['messages'] == policy.messages(tasks[1], [], 'experience', state['teacher'], state['memory']), 'T60_actual_causal_context')
    triple = common.read(partial / 'TRIPLE_0115.json')
    require(triple['parent_intervention'] == state['pending']
        and triple['subsequent_behavior']['sha256'] == common.sha(partial / 'CALL_0115.json'), 'prior_parent_consumed_by_T60')
    queue = root / 'r110_parent_queue'
    request = queue / 'GUIDED_SLEEP_C008_T060.request.json'
    response = common.read(queue / 'GUIDED_SLEEP_C008_T060.response.json')
    require(response['status'] == 'FAILED' and response['request_sha256'] == common.sha(request), 'failed_T60_not_retried')
    archive = Path(response['archive']['remote_root'])
    require(archive == root.parent / 'parent_transcripts' / root.name / 'GUIDED_SLEEP_C008_T060', 'failed_parent_custody')
    for name, digest in response['archive']['files'].items():
        require(Path(name).name == name and common.sha(archive / name) == digest, 'failed_parent_archive_verified')
    state = deepcopy(state)
    state.update(completed_train_segments=60, pending=None)
    return state


def prepare():
    old.validate(old.ROOT)
    output = LANE / DIRECTORY
    require(not output.exists(), 'one_recovery_preparation')
    activation = common.read(LANE / 'ACTIVATION.json')
    identities = [common.read(LANE / 'LAUNCH.json')['identity'], activation['guardian']]
    require(all(not (Path('/proc') / str(item['pid'])).exists() for item in identities), 'original_processes_gone')
    require(common.read(LANE / 'TERMINAL.json')['status'] == 'FAILED', 'original_failed_no_overwrite')
    state = reconstruct(LANE)
    ledgers = {name: dict(sha256=common.sha(LANE / name), bytes=(LANE / name).stat().st_size,
        count=len((LANE / name).read_text().splitlines())) for name in ('CALLS_NATIVE.jsonl', 'CALLS_PARENT.jsonl')}
    require([ledgers[name]['count'] for name in ledgers] == [116, 60], 'no_new_or_lost_charges')
    preserved = {str(path.relative_to(LANE)): common.sha(path) for path in LANE.rglob('*')
        if path.is_file() and path.name not in ledgers}
    output.mkdir()
    common.write(output / 'INITIAL_STATE.json', state)
    plan = dict(schema='MATH_R118_NODE3_RECOVERY_V1', root=str(LANE), cycle=8,
        completed_prefix=4, next_purpose='check', original_activation=activation,
        prior_identities=identities, preserved=preserved, ledger_prefixes=ledgers,
        initial_state_sha256=common.sha(output / 'INITIAL_STATE.json'),
        source_files={path.name: common.sha(path) for path in (Path(__file__), MODULE_PATH)},
        no_replay=True, no_weight_reset=True, frozen_base_context_only=True,
        missing_parent_retains_previous_guidance=True, original_caps=common.read(LANE / 'READY.json')['budget'],
        prepared_unix=time.time())
    common.write(output / 'PLAN.json', plan)
    return dict(plan_sha256=common.sha(output / 'PLAN.json'), preserved_files=len(preserved), ledger_prefixes=ledgers,
        state_sha256=plan['initial_state_sha256'], prior_identities=identities, source_files=plan['source_files'])


def validate():
    old.validate(old.ROOT)
    output = LANE / DIRECTORY
    plan = common.read(output / 'PLAN.json')
    require(plan['root'] == str(LANE) and plan['cycle'] == 8 and plan['completed_prefix'] == 4, 'exact_owned_recovery')
    require(common.read(LANE / 'ACTIVATION.json') == plan['original_activation'], 'original_wall_not_extended')
    require(common.read(LANE / 'READY.json')['budget'] == plan['original_caps'], 'original_caps_not_reset')
    require(common.sha(output / 'INITIAL_STATE.json') == plan['initial_state_sha256'], 'preserved_context')
    for name, digest in plan['source_files'].items():
        require(Path(name).name == name and common.sha(Path(__file__).parent / name) == digest, 'frozen_recovery_source')
    for name, digest in plan['preserved'].items():
        require(common.sha(LANE / name) == digest, 'preserved_original:' + name)
    import hashlib
    for name, prefix in plan['ledger_prefixes'].items():
        require(hashlib.sha256((LANE / name).read_bytes()[:prefix['bytes']]).hexdigest() == prefix['sha256'], 'append_only_ledger')
    return plan


def resident():
    plan = validate()
    output = LANE / DIRECTORY
    require(all(not (Path('/proc') / str(item['pid'])).exists() for item in plan['prior_identities']), 'old_processes_absent')
    cached = []
    original = old.machinery.previous.response_contract.engine_class(old.machinery.previous.direct.Engine)
    guarded = native.reflection.engine_class(original)
    def factory(model_dir, tokenizer, device, check):
        if not cached:
            cached.append(guarded(model_dir, tokenizer, device=device, check=check))
        return cached[0]
    original_wrapper = native.reflection.engine_class
    native.reflection.engine_class = lambda engine: engine
    status = 'FAILED'
    try:
        for cycle in range(8, policy.CYCLES + 1):
            for phase in ('experience', 'readout'):
                if time.time() >= plan['original_activation']['native_deadline_unix'] - 600:
                    status = 'BOUNDED_DEADLINE_PARTIAL'
                    return
                native.run(LANE, 0, cycle, phase, factory, old.validate, common.sha(output / 'PLAN.json'))
                phase_root = output / f'cycle{cycle}' / phase
                complete = common.read(phase_root / 'COMPLETE.json')
                require(complete['status'] == 'COMPLETE', 'actual_phase_complete')
                require(len(list(phase_root.glob('CALL_*.json'))) == (4 if cycle == 8 and phase == 'experience' else 8), 'remaining_calls_only')
                validate()
                common.write(output / f'COMPLETE_C{cycle}_{phase}.json', dict(complete_sha256=common.sha(phase_root / 'COMPLETE.json'),
                    after_sha256=common.sha(phase_root / 'AFTER.json'), finished_unix=time.time()))
        status = 'COMPLETE'
    except BaseException as error:
        common.write(output / 'RESIDENT_FAILED.json', dict(error=str(error), type=type(error).__name__, finished_unix=time.time()))
        raise
    finally:
        native.reflection.engine_class = original_wrapper
        common.write(output / 'RESIDENT_TERMINAL.json', dict(status=status, loads=len(cached),
            process=native.reuse.driver.seam.native.process_identity(), finished_unix=time.time(), no_weight_writes=True))


def guard(expected):
    plan = validate()
    output = LANE / DIRECTORY
    require(common.sha(output / 'READY.json') == expected and common.read(output / 'READY.json')['passed'], 'own_cpu_ready')
    require(common.read(output / 'READY.json')['plan_sha256'] == common.sha(output / 'PLAN.json'), 'cpu_plan_bound')
    with (output / 'GUARD.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        require(not (output / 'LAUNCH.json').exists(), 'never_duplicate_native')
        deadline = min(time.time()+180, plan['original_activation']['native_deadline_unix']-600)
        admitted = False
        for attempt in range(60):
            require(time.time() < deadline, 'bounded_strict_admission')
            report = old.scan(old.ROOT, 0)
            common.write(output / f'ADMISSION_{attempt:03d}.json', report)
            admitted = report['clear'] and report['scanner_euid'] == 0 and not report['blocking_reasons']
            if admitted:
                break
            time.sleep(1)
        require(admitted, 'strict_full_proc_no_waiver')
        validate()
        child = identity = None
        status = 'FAILED'
        def interrupted(signum, frame):
            raise SystemExit(128+signum)
        signal.signal(signal.SIGTERM, interrupted)
        signal.signal(signal.SIGINT, interrupted)
        try:
            with (output / 'RESIDENT.log').open('x') as log:
                child = subprocess.Popen([old.machinery.previous.existing.PYTHON, '-B', str(Path(__file__)), 'resident'],
                    cwd=old.LIBRARY/'source', stdin=subprocess.DEVNULL, stdout=log, stderr=subprocess.STDOUT,
                    start_new_session=True, env=dict(os.environ, CUDA_VISIBLE_DEVICES=policy.DEVICES[0],
                        PYTHONPATH=str(old.LIBRARY/'source'), HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1',
                        PYTHONDONTWRITEBYTECODE='1', OMP_NUM_THREADS='1', MKL_NUM_THREADS='1', TOKENIZERS_PARALLELISM='false'))
                identity = common.process_identity(Path('/proc') / str(child.pid))
                common.write(output / 'LAUNCH.json', dict(identity=identity, uuid=policy.DEVICES[0],
                    plan_sha256=common.sha(output / 'PLAN.json'), started_unix=time.time()))
                require(child.wait(timeout=max(.01, plan['original_activation']['hard_deadline_unix']-120-time.time())) == 0, 'native_failure_no_retry')
                status = common.read(output / 'RESIDENT_TERMINAL.json')['status']
        finally:
            if child is not None:
                common.stop_owned(child, identity)
            common.write(output / 'TERMINAL.json', dict(status=status, finished_unix=time.time(), peer_processes_signalled=0))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('phase', choices=('prepare', 'guard', 'resident', 'validate'))
    parser.add_argument('--ready-sha256')
    args = parser.parse_args()
    if args.phase == 'prepare':
        print(json.dumps(prepare()))
    elif args.phase == 'validate':
        print(json.dumps(dict(valid=True, plan_sha256=common.sha(LANE / DIRECTORY / 'PLAN.json'))) if validate() else '{}')
    elif args.phase == 'guard':
        guard(args.ready_sha256)
    else:
        resident()
