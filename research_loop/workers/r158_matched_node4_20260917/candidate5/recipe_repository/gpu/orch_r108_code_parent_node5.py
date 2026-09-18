"""New node5 frozen-BASE CODE lives; no changes to existing live sources."""

import argparse
from copy import deepcopy
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import subprocess
import time

from gpu import orch_r108_code_parent_r110_continue as continuation
from gpu import orch_r108_code_parent_r109_broker as broker


run, policy = continuation.run, continuation.policy
read, write, sha, common = run.read, run.write, run.sha, run.common
HOST_SHA = '0cb7eb43862102b79ae0a30d2babfedfbf9598b31967a1a04122c3cf849c746d'
DEVICES = {4: 'GPU-94c9a79c-8b13-5679-ad35-8dda3fe5c94d', 5: 'GPU-65595cff-c6c2-c798-bc62-427168079270'}
ARMS = {4: 'node5_segment', 5: 'node5_episode'}
START = datetime(2026, 9, 15, 9, 30, tzinfo=timezone.utc).timestamp()
LEASE_END = datetime(2026, 9, 17, 4, 4, tzinfo=timezone.utc).timestamp()
SOURCE_CONFIGS = deepcopy(policy.ARMS)
SOURCE_TASKS = policy.frozen_tasks
ORIGINAL_SCAN = run.admission.scan


def root_for(index):
    policy.require(type(index) is int and index in DEVICES, 'only_node5_physical4_5')
    return Path(f'/localhome/local-rohing/orch_r108_code_parent_node5_{index}_20260915_attempt2')


def fresh_tasks(arm):
    rows = deepcopy(list(SOURCE_TASKS(arm)))
    for row in rows:
        old_marker = 1000 + row['cycle'] * 6 + row['slot'] - 1
        new_marker = old_marker + 20000
        for field in ('prompt', 'question', 'reference_expression'):
            row[field] = row[field].replace(str(old_marker), str(new_marker))
        row['task_id'] = row['task_id'].replace('R109_CODE_', 'R110_NODE5_CODE_', 1)
        row['cohort'] = 'R110_NODE5_BASE_CODE_FRESH_MARKERS_V1'
        row['prompt_sha256'] = policy.digest(row['prompt'])
        row['question_sha256'] = policy.prior.question_hash(row['question'])
        for case in row['tests']:
            case['expected'] = policy.prior.gym.evaluate(row['reference_expression'], case['arguments'])
        row.pop('content_sha256', None)
        row['content_sha256'] = policy.digest(row)
    return tuple(rows)


def configure(index):
    root = root_for(index)
    policy.ARMS = {ARMS[physical]: dict(SOURCE_CONFIGS['a100_segment' if physical == 4 else 'node3_episode'],
        wrapper='ovx3', index=physical, uuid=DEVICES[physical], host_sha256=HOST_SHA) for physical in DEVICES}
    policy.START = START
    policy.frozen_tasks = fresh_tasks
    continuation.ROOT, continuation.ARM = root, ARMS[index]
    continuation.install()
    run.validate, run.status = validate, status
    run.admission.scan = scan
    return root, ARMS[index]


def validate(root, arm):
    ready = continuation.original_validate(root, arm)
    bound = read(root / 'LIFETIME.json')
    policy.require(bound['started_unix'] == START and bound['lease_end_unix'] == LEASE_END
        and bound['hard_deadline_unix'] <= LEASE_END - 21600
        and bound['hard_deadline_unix'] - START <= 28800, 'new_node5_bounds')
    policy.require(read(root / 'INHERITED_CELLS.json') == {}, 'new_node5_no_old_call_reuse')
    return ready


def prepare(root, arm):
    policy.require(read(root / 'DEPLOY_INPUTS.json')['lease_end_unix'] == LEASE_END, 'exact_verified_lease')
    write(root / 'INHERITED_CELLS.json', {})
    value = run.prepare(root, arm)
    ready = read(root / 'READY.json')
    ready['files']['INHERITED_CELLS.json'] = sha(root / 'INHERITED_CELLS.json')
    ready['operational_failure_behavior'] = 'MISSING_INTERVENTION_OWN_REFLECTION_NEXT_SCHEDULED_PARENT'
    ready['separate_node5_allocation'] = True
    write(root / 'READY.json', ready)
    write(root / run.LANE / 'READY.json', ready)
    value['ready_sha256'] = sha(root / 'READY.json')
    return value


def status(root, arm):
    value = continuation.original_status(root, arm)
    value.update(unusable_interventions=len(list((root / run.LANE).glob('UNUSABLE_*.json'))),
        missing_intervention_continuations=len(list((root / run.LANE).glob('MISSING_INTERVENTION_CONTINUATION_*.json'))),
        inherited_native_charged=0, inherited_parent_charged=0, separate_node5_allocation=True)
    write(root / run.LANE / 'STATUS.json', value)
    return value


def scan(root, arm):
    config = policy.allocation(arm)
    if os.geteuid() == 0:
        return ORIGINAL_SCAN(root, arm)
    result = subprocess.run(['sudo', '-n', 'env', 'CUDA_VISIBLE_DEVICES=', 'PYTHONDONTWRITEBYTECODE=1',
        'PYTHONPATH=' + str(root / 'source'), 'python3', '-B', '-m', 'gpu.orch_r108_code_parent_node5',
        'scan', '--index', str(config['index'])], capture_output=True, text=True, timeout=90, check=True)
    snapshot = json.loads(result.stdout)
    policy.require(snapshot['gpu']['index'] == config['index'] and snapshot['gpu']['uuid'] == config['uuid']
        and snapshot['host_sha256'] == HOST_SHA and snapshot['scanner_euid'] == 0
        and 'device_minor' in snapshot, 'full_privileged_node5_binding')
    return snapshot


def guard(root, arm, index):
    ready = validate(root, arm)
    policy.require(os.environ.get('CUDA_VISIBLE_DEVICES') == '', 'cpu_guard_only')
    lane = root / run.LANE
    (lane / 'GUARD_ONCE').mkdir()
    child = identity = None
    result = 'FAILED'
    bound = read(root / 'LIFETIME.json')
    try:
        deadline = min(time.time() + 600, bound['native_deadline_unix'])
        snapshot = None
        for attempt in range(200):
            policy.require(time.time() < deadline, 'strict_admission_window')
            snapshot = run.admission.scan(root, arm)
            write(lane / f'ADMISSION_{attempt:03d}.json', snapshot)
            if snapshot['clear'] is True:
                break
            policy.require(continuation.transient_scan(snapshot), 'real_ownership_block')
            time.sleep(3)
        policy.require(snapshot is not None and snapshot['clear'] is True and snapshot['scanner_euid'] == 0, 'privileged_clear')
        write(lane / 'ADMISSION.json', snapshot)
        with (lane / 'native.log').open('x') as log:
            child = subprocess.Popen([common.PYTHON, '-B', '-m', 'gpu.orch_r108_code_parent_node5', 'native', '--index', str(index)],
                cwd=root / 'source', start_new_session=True, stdin=subprocess.DEVNULL, stdout=log, stderr=subprocess.STDOUT,
                env=dict(os.environ, CUDA_VISIBLE_DEVICES=ready['config']['uuid'], PYTHONPATH=str(root / 'source'),
                    PYTHONDONTWRITEBYTECODE='1', HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1', OMP_NUM_THREADS='1', MKL_NUM_THREADS='1'))
        identity = common.process_identity(Path('/proc') / str(child.pid))
        write(lane / 'LAUNCH.json', dict(identity=identity, started_unix=time.time(), ready_sha256=sha(root / 'READY.json'),
            admission_sha256=sha(lane / 'ADMISSION.json'), arm=arm, index=index))
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
    parser.add_argument('phase', choices=('prepare', 'native', 'guard', 'status', 'service', 'scan', 'broker'))
    parser.add_argument('--index', type=int, choices=(4, 5), required=True)
    for name in ('repository', 'buffer', 'receipts', 'principles'):
        parser.add_argument('--' + name, type=Path)
    parser.add_argument('--ready-sha256')
    args = parser.parse_args()
    root, arm = configure(args.index)
    value = None
    if args.phase == 'service':
        run.admission.bind(arm)
        run.admission.scanner.pinned.service(root / 'SERVICE_IDENTITY.json')
    elif args.phase == 'broker':
        broker.serve(args.repository, root / run.LANE, args.buffer, args.receipts, args.ready_sha256,
            policy.HARD_END - 120, arm, args.principles)
    elif args.phase == 'guard':
        guard(root, arm, args.index)
    elif args.phase == 'prepare':
        value = prepare(root, arm)
    elif args.phase == 'scan':
        value = scan(root, arm)
    else:
        value = getattr(run, args.phase)(root, arm)
    if value is not None:
        print(json.dumps(value, sort_keys=True))
