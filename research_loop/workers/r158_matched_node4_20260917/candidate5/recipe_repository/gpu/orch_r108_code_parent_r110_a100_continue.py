"""Restore the exact A100 BASE context with no duplicate native/provider calls."""

import argparse
import os
from pathlib import Path
import shutil
import subprocess
import time
import json

from gpu import orch_r108_code_parent_r110_continue as continuation


run, policy = continuation.run, continuation.policy
read, write, sha, common = run.read, run.write, run.sha, run.common
ROOT = Path('/localhome/local-rohing/orch_r108_code_parent_r110_a100_continue_20260915_attempt1')
PREVIOUS = Path('/localhome/local-rohing/orch_r108_code_parent_r110_20260915_attempt1')
ARM = 'a100_segment'


def inherited_counts(records):
    policy.require(records and all((row['kind'] == 'NATIVE' and row['status'] == 'COMPLETE')
        or (row['kind'] == 'PARENT' and row['status'] in ('COMPLETE', 'FAILED')) for row in records),
        'no_partial_native_or_unresolved_provider_replay')
    policy.require(any(row['kind'] == 'PARENT' and row['status'] == 'FAILED' for row in records), 'operational_parent_failure')
    return dict(consumed_native=sum(row['kind'] == 'NATIVE' for row in records),
        consumed_parent=sum(row['kind'] == 'PARENT' for row in records),
        accepted_parent=sum(row['kind'] == 'PARENT' and row['status'] == 'COMPLETE' for row in records))


def prepare(root):
    policy.require(root == ROOT and not (root / 'READY.json').exists(), 'new_a100_continuation_only')
    old = run.validate(PREVIOUS, ARM)
    lane = PREVIOUS / run.LANE
    policy.require(read(lane / 'TERMINAL.json')['status'] == 'FAILED'
        and read(lane / 'AFTER.json')['status'] == 'PASS', 'preserved_terminal_and_base')
    cells = sorted((lane / 'cells').glob('*.json'))
    counts = inherited_counts([read(path) for path in cells])
    policy.require(counts == dict(consumed_native=6, consumed_parent=3, accepted_parent=2), 'exact_measured_a100_boundary')
    policy.require(read(root / 'CPU_TESTS.json')['passed'] is True, 'own_cpu_tests')
    (root / run.LANE / 'cells').mkdir(parents=True)
    (root / run.LANE / run.QUEUE).mkdir()
    inherited = {}
    for path in cells:
        shutil.copyfile(path, root / run.LANE / 'cells' / path.name)
        inherited[path.stem] = dict(path=str(path), sha256=sha(path))
    for name in old['files']:
        if name not in ('SOURCE_SHA256.json', 'CPU_TESTS.json', 'DEPLOY_INPUTS.json'):
            shutil.copyfile(PREVIOUS / name, root / name)
    inputs = read(PREVIOUS / 'DEPLOY_INPUTS.json')
    inputs['previous_lane'] = str(lane)
    write(root / 'DEPLOY_INPUTS.json', inputs)
    write(root / 'INHERITED_CELLS.json', inherited)
    write(root / 'LINEAGE.json', dict(previous_root=str(PREVIOUS), previous_ready_sha256=sha(PREVIOUS / 'READY.json'),
        previous_terminal_sha256=sha(lane / 'TERMINAL.json'), previous_after_sha256=sha(lane / 'AFTER.json'),
        lifetime_sha256=sha(PREVIOUS / 'LIFETIME.json'), reservations_sha256=sha(PREVIOUS / 'RESERVATIONS.json'),
        same_api_retry=False, raw_stays_node=True, **counts))
    ready = dict(old)
    ready['schema'] += '_A100_OPERATIONAL_CONTINUATION_V1'
    ready['files'] = {name: sha(root / name) for name in list(old['files']) + ['LINEAGE.json', 'INHERITED_CELLS.json']}
    ready['operational_failure_behavior'] = 'MISSING_INTERVENTION_OWN_REFLECTION_NEXT_SCHEDULED_PARENT'
    write(root / 'READY.json', ready)
    write(root / run.LANE / 'READY.json', ready)
    return dict(ready_sha256=sha(root / 'READY.json'), lineage=read(root / 'LINEAGE.json'),
        lifetime=read(root / 'LIFETIME.json'), inherited_cells=inherited)


def parent(root, arm, task, segment, records, memory, lessons, check, payload=None):
    phase = ('meta_parent' if task['slot'] == 0 else 'parent') + str(segment)
    previous = continuation.inherited_cell(root, task, phase)
    if previous is not None and previous['status'] == 'COMPLETE':
        check('inherited_accepted_parent')
        identifier = f'GUIDED_SLEEP_C{task["cycle"]}_P{task["slot"]}_S{segment}'
        request = PREVIOUS / run.LANE / run.QUEUE / (identifier + '.request.json')
        result, directory = continuation.verified_result(request.with_name(identifier + '.response.json'), request, PREVIOUS)
        policy.require(result['status'] == 'COMPLETE' and previous['result'] == result, 'exact_previous_accepted_parent')
        return previous
    return continuation.parent(root, arm, task, segment, records, memory, lessons, check, payload)


def status(root, arm):
    value = continuation.original_status(root, arm)
    lineage = read(root / 'LINEAGE.json')
    value.update(unusable_interventions=len(list((root / run.LANE).glob('UNUSABLE_*.json'))),
        missing_intervention_continuations=len(list((root / run.LANE).glob('MISSING_INTERVENTION_CONTINUATION_*.json'))),
        inherited_native_charged=lineage['consumed_native'], inherited_parent_charged=lineage['consumed_parent'],
        no_budget_reset=True)
    write(root / run.LANE / 'STATUS.json', value)
    return value


def cycles(root, arm, engine, check):
    return continuation.original_cycles(root, arm, engine, check, parent_call=parent)


def install():
    continuation.ROOT, continuation.PREVIOUS, continuation.ARM = ROOT, PREVIOUS, ARM
    continuation.install()
    run.status, run.cycles = status, cycles


def guard(root):
    ready = run.validate(root, ARM)
    policy.require(os.environ.get('CUDA_VISIBLE_DEVICES') == '', 'cpu_guard_only')
    lane = root / run.LANE
    (lane / 'GUARD_ONCE').mkdir()
    child = identity = None
    result = 'FAILED'
    bound = read(root / 'LIFETIME.json')
    try:
        policy.require(run.previous_released(root), 'previous_exact_native_released')
        deadline = min(time.time() + 600, bound['native_deadline_unix'])
        snapshot = None
        for attempt in range(200):
            policy.require(time.time() < deadline, 'strict_admission_window')
            snapshot = run.admission.scan(root, ARM)
            write(lane / f'ADMISSION_{attempt:03d}.json', snapshot)
            if snapshot['clear'] is True:
                break
            policy.require(continuation.transient_scan(snapshot), 'real_ownership_block')
            time.sleep(3)
        policy.require(snapshot is not None and snapshot['clear'] is True and snapshot['scanner_euid'] == 0, 'privileged_clear')
        write(lane / 'ADMISSION.json', snapshot)
        with (lane / 'native.log').open('x') as log:
            child = subprocess.Popen([common.PYTHON, '-B', '-m', 'gpu.orch_r108_code_parent_r110_a100_continue', 'native'],
                cwd=root / 'source', start_new_session=True, stdin=subprocess.DEVNULL, stdout=log, stderr=subprocess.STDOUT,
                env=dict(os.environ, CUDA_VISIBLE_DEVICES=ready['config']['uuid'], PYTHONPATH=str(root / 'source'),
                    PYTHONDONTWRITEBYTECODE='1', HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1', OMP_NUM_THREADS='1', MKL_NUM_THREADS='1'))
        identity = common.process_identity(Path('/proc') / str(child.pid))
        write(lane / 'LAUNCH.json', dict(identity=identity, started_unix=time.time(), ready_sha256=sha(root / 'READY.json'),
            admission_sha256=sha(lane / 'ADMISSION.json'), arm=ARM, continued_from=str(PREVIOUS)))
        while child.poll() is None:
            policy.require(time.time() < bound['hard_deadline_unix'] - 30, 'finite_hard_guard')
            time.sleep(2)
        policy.require(child.returncode == 0 and (lane / 'COMPLETE.json').exists(), 'native_failure_no_retry')
        result = 'COMPLETE'
    finally:
        if child is not None:
            common.stop_owned(child, identity)
        write(lane / 'TERMINAL.json', dict(status=result, finished_unix=time.time(), no_refill=True))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('phase', choices=('prepare', 'native', 'guard', 'status'))
    args = parser.parse_args()
    if args.phase == 'prepare':
        value = prepare(ROOT)
    else:
        install()
        value = guard(ROOT) if args.phase == 'guard' else getattr(run, args.phase)(ROOT, ARM)
    if value is not None:
        print(json.dumps(value, sort_keys=True))
