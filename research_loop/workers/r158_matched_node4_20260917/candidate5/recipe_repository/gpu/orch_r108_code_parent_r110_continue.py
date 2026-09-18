"""Node3-only operational continuation; inherited calls never dispatch again."""

import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import time

from gpu import orch_r108_code_parent_r109_run as run


ROOT = Path('/localhome/local-rohing/orch_r108_code_parent_r110_continue_20260915_attempt2')
PREVIOUS = run.ROOT
ARM = 'node3_episode'
read, write, sha, common, policy = run.read, run.write, run.sha, run.common, run.policy
original_generate, original_reflection = run.generate, run.reflection
original_cycles, original_status, original_validate = run.cycles, run.status, run.validate
original_meta_dialogue = run.meta_dialogue


def prepare(root):
    policy.require(root == ROOT and not (root / 'READY.json').exists(), 'new_continuation_only')
    old = run.validate(PREVIOUS, ARM)
    lane = PREVIOUS / run.LANE
    policy.require(read(lane / 'TERMINAL.json')['status'] == 'FAILED'
        and read(lane / 'AFTER.json')['status'] == 'PASS', 'preserved_terminal_and_base')
    cells = sorted((lane / 'cells').glob('*.json'))
    records = [read(path) for path in cells]
    policy.require(len(records) == 3 and sum(row['kind'] == 'NATIVE' and row['status'] == 'COMPLETE'
        for row in records) == 2 and sum(row['kind'] == 'PARENT' and row['status'] == 'FAILED'
        for row in records) == 1, 'exact_initial_consumed_cells')
    policy.require(read(root / 'CPU_TESTS.json')['passed'] is True, 'own_cpu_tests')
    (root / run.LANE / 'cells').mkdir(parents=True)
    (root / run.LANE / run.QUEUE).mkdir()
    inherited = {}
    for path in cells:
        destination = root / run.LANE / 'cells' / path.name
        shutil.copyfile(path, destination)
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
        consumed_native=2, consumed_parent=1, lifetime_sha256=sha(PREVIOUS / 'LIFETIME.json'),
        reservations_sha256=sha(PREVIOUS / 'RESERVATIONS.json'), same_api_retry=False, raw_stays_node=True))
    ready = dict(old)
    ready['schema'] += '_OPERATIONAL_CONTINUATION_V1'
    ready['files'] = {name: sha(root / name) for name in list(old['files']) + ['LINEAGE.json', 'INHERITED_CELLS.json']}
    ready['operational_failure_behavior'] = 'MISSING_INTERVENTION_OWN_REFLECTION_NEXT_SCHEDULED_PARENT'
    write(root / 'READY.json', ready)
    write(root / run.LANE / 'READY.json', ready)
    return dict(ready_sha256=sha(root / 'READY.json'), lineage=read(root / 'LINEAGE.json'),
        lifetime=read(root / 'LIFETIME.json'), inherited_cells=inherited)


def validate(root, arm):
    policy.require(arm == ARM, 'node3_only_a100_untouched')
    ready = original_validate(root, arm)
    lineage = read(root / 'LINEAGE.json')
    policy.require(lineage['previous_root'] == str(PREVIOUS)
        and lineage['previous_ready_sha256'] == sha(PREVIOUS / 'READY.json')
        and lineage['lifetime_sha256'] == sha(root / 'LIFETIME.json')
        and lineage['reservations_sha256'] == sha(root / 'RESERVATIONS.json'), 'original_lifetime_caps_lineage')
    for cell_id, entry in read(root / 'INHERITED_CELLS.json').items():
        policy.require(sha(Path(entry['path'])) == entry['sha256']
            == sha(root / run.LANE / 'cells' / (cell_id + '.json')), 'inherited_bytes_immutable')
    return ready


def inherited_cell(root, task, phase):
    selected = next(row for row in read(root / 'RESERVATIONS.json')
        if row['task_id'] == task['task_id'] and row['phase'] == phase)
    entry = read(root / 'INHERITED_CELLS.json').get(selected['cell_id'])
    if entry is None:
        return None
    path = root / run.LANE / 'cells' / (selected['cell_id'] + '.json')
    policy.require(sha(path) == entry['sha256'] == sha(Path(entry['path'])), 'no_inherited_drift')
    record = read(path)
    policy.require(all(record[key] == value for key, value in selected.items()), 'same_reserved_cell')
    return record


def generate(root, engine, task, phase, messages, check):
    check('continuation_native_dispatch')
    inherited = inherited_cell(root, task, phase)
    if inherited is not None:
        policy.require(inherited['kind'] == 'NATIVE' and inherited['status'] == 'COMPLETE', 'only_complete_native_reuse')
        return inherited
    messages = [dict(message) for message in messages]
    for message in messages:
        message['content'] = message['content'].replace('Actual parent guidance:\n\nYour own reflection:',
            'No usable parent intervention was received for this turn.\nYour own reflection:')
    return original_generate(root, engine, task, phase, messages, check)


def verified_result(response, request, archive_root):
    result = read(response)
    policy.require(result['request_sha256'] == sha(request), 'actual_request_join')
    directory = Path(result['archive']['remote_root'])
    policy.require(directory.is_relative_to(archive_root / 'parent_transcripts' / run.LANE), 'own_archive')
    policy.require(result['archive']['all_verified'] is True and result['archive']['files'], 'verified_archive_required')
    for name, expected in result['archive']['files'].items():
        relative = Path(name)
        policy.require(not relative.is_absolute() and '..' not in relative.parts
            and sha(directory / relative) == expected, 'archive_hash')
    return result, directory


def missing(root, record, reason, result=None, inherited=False):
    value = dict(record, status='MISSING', operational_failure=True, intervention_available=False,
        classification='UNCLASSIFIED', missing_reason=reason, lesson='', result=result,
        declared_intervention_classes=['UNCLASSIFIED'], declared_behavior_operation='UNCLASSIFIED',
        classes_are_self_declared_not_semantic_audit=True, no_retry=True, finished_unix=time.time(),
        inherited_charged_call=inherited)
    write(root / run.LANE / ('UNUSABLE_' + record['cell_id'] + '.json'), value)
    if not inherited:
        write(root / run.LANE / 'cells' / (record['cell_id'] + '.json'), value)
    return value


def parent(root, arm, task, segment, records, memory, lessons, check, payload=None):
    check('continuation_parent_dispatch')
    phase = ('meta_parent' if task['slot'] == 0 else 'parent') + str(segment)
    previous = inherited_cell(root, task, phase)
    identifier = f'GUIDED_SLEEP_C{task["cycle"]}_P{task["slot"]}_S{segment}'
    if previous is not None:
        policy.require(previous['kind'] == 'PARENT' and previous['status'] == 'FAILED', 'only_initial_failed_parent')
        request = PREVIOUS / run.LANE / run.QUEUE / (identifier + '.request.json')
        result, directory = verified_result(request.with_name(identifier + '.response.json'), request, PREVIOUS)
        policy.require(result['status'] == 'FAILED', 'preserved_failed_provider')
        return missing(root, previous, 'INHERITED_UNUSABLE_PROVIDER_RESPONSE', result, inherited=True)
    path, record = run.begin(root, task, phase)
    request = root / run.LANE / run.QUEUE / (identifier + '.request.json')
    payload = payload if payload is not None else policy.parent_payload(arm, task, segment, records, memory, lessons)
    policy.validate_parent_payload(payload)
    write(request, dict(id=identifier, payload=payload, payload_sha256=policy.digest(payload), ready_sha256=sha(root / 'READY.json')))
    until = min(time.time() + 300, read(root / 'LIFETIME.json')['native_deadline_unix'])
    response = request.with_name(identifier + '.response.json')
    while not response.exists():
        check('continuation_parent_wait')
        if time.time() >= until:
            return missing(root, record, 'PROVIDER_TIMEOUT_NO_RETRY')
        time.sleep(2)
    result, directory = verified_result(response, request, root)
    if result['status'] == 'FAILED':
        return missing(root, record, 'UNUSABLE_PROVIDER_RESPONSE', result)
    policy.require(result['status'] == 'COMPLETE', 'known_provider_status')
    try:
        plan = run.prior.parse_parent(read(directory / 'RAW_RESPONSE.json'), [task['task_id']])
        lesson = policy.prior.parent_lesson(plan, task)
    except (ValueError, AssertionError, TypeError, KeyError):
        return missing(root, record, 'UNUSABLE_PARSED_PLAN', result)
    policy.require(plan == result['plan'] == read(directory / 'PLAN.json'), 'actual_plan_join')
    record.update(status='COMPLETE', result=result, lesson=lesson, intervention_available=True,
        declared_intervention_classes=policy.declared_classes(plan), declared_behavior_operation=policy.declared_operation(plan),
        classes_are_self_declared_not_semantic_audit=True, finished_unix=time.time())
    write(path, record)
    return record


def reflection(root, engine, task, segment, records, intervention, memory, check):
    if intervention.get('intervention_available', True):
        return original_reflection(root, engine, task, segment, records, intervention, memory, check)
    messages = [dict(role='system', content=policy.prior.REFLECTION_SYSTEM), dict(role='user', content=json.dumps(dict(
        actual_train_prompt=task['prompt'], actual_own_segments=[row['response']['raw'] for row in records],
        intervention_available=False, operational_notice='No usable parent intervention was received. Reflect on your own work; do not invent parent advice.',
        prior_own_reflection=memory), sort_keys=True))]
    return generate(root, engine, task, 'reflection' + str(segment), messages, check)


def save_triple(root, arm, task, segment, before, intervention, reflected, after):
    available = intervention.get('intervention_available', True)
    value = policy.prior.triple(task, before, intervention, reflected, after)
    value.update(arm=arm, segment=segment, intervention_available=available,
        operational_failure=not available, actual_parent_triple=available,
        classification='UNCLASSIFIED' if not available else 'STRUCTURED_PLAN', semantic_compiler_used=False)
    prefix = 'TRIPLE' if available else 'MISSING_INTERVENTION_CONTINUATION'
    write(root / run.LANE / f'{prefix}_C{task["cycle"]:03d}_E{task["slot"]}_S{segment}.json', value)


def status(root, arm):
    value = original_status(root, arm)
    value.update(unusable_interventions=len(list((root / run.LANE).glob('UNUSABLE_*.json'))),
        missing_intervention_continuations=len(list((root / run.LANE).glob('MISSING_INTERVENTION_CONTINUATION_*.json'))),
        inherited_native_charged=2, inherited_parent_charged=1, no_budget_reset=True)
    write(root / run.LANE / 'STATUS.json', value)
    return value


def cycles(root, arm, engine, check):
    return original_cycles(root, arm, engine, check, parent_call=parent)


def meta_dialogue(root, arm, engine, cycle, before, memory, lessons, check, parent_call):
    memory = original_meta_dialogue(root, arm, engine, cycle, before, memory, lessons, check, parent_call)
    path = root / run.LANE / f'CONTEXT_DISTILLATION_C{cycle:03d}.json'
    value = read(path)
    task_id = policy.meta_task(arm, cycle)['task_id']
    missing_count = sum(read(path)['task_id'] == task_id for path in (root / run.LANE).glob('UNUSABLE_*.json'))
    value.update(scheduled_parent_rounds=3, parent_rounds=3 - missing_count, unusable_parent_rounds=missing_count,
        parent_field_empty_means_unavailable=True)
    write(path, value)
    return memory


def install():
    run.ROOT = ROOT
    run.validate, run.generate, run.reflection = validate, generate, reflection
    run.save_triple, run.status, run.cycles = save_triple, status, cycles
    run.meta_dialogue = meta_dialogue


def transient_scan(snapshot):
    config = policy.allocation(ARM)
    reasons = snapshot['blocking_reasons']
    return bool(reasons) and snapshot['scanner_euid'] == 0 and snapshot['gpu']['uuid'] == config['uuid'] \
        and snapshot['gpu']['index'] == config['index'] and snapshot['gpu']['memory_used_mib'] <= 32 \
        and snapshot['gpu']['utilization_percent'] == 0 \
        and not any(row['gpu_uuid'] == config['uuid'] for row in snapshot['compute_processes']) \
        and all(reason.startswith(('process_identity_drift:', 'minor_scan_identity_changed:',
            'minor_scan_process_drift:')) for reason in reasons)


def guard(root):
    ready = validate(root, ARM)
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
            policy.require(transient_scan(snapshot), 'real_ownership_block')
            time.sleep(3)
        policy.require(snapshot is not None and snapshot['clear'] is True and snapshot['scanner_euid'] == 0, 'privileged_clear')
        write(lane / 'ADMISSION.json', snapshot)
        with (lane / 'native.log').open('x') as log:
            child = subprocess.Popen([common.PYTHON, '-B', '-m', 'gpu.orch_r108_code_parent_r110_continue', 'native', '--root', str(root)],
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
    parser.add_argument('--root', type=Path, required=True)
    args = parser.parse_args()
    if args.phase == 'prepare':
        value = prepare(args.root)
    else:
        install()
        value = guard(args.root) if args.phase == 'guard' else getattr(run, args.phase)(args.root, ARM)
    if value is not None:
        print(json.dumps(value, sort_keys=True))
