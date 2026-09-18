"""Exact durable-COMPLETE deadline-only continuation; no behavioral-policy delta."""

import argparse
from copy import deepcopy
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time
import uuid


PYTHON = '/localhome/local-rohing/v2/venv/bin/python'
P7_BASE = Path('/localhome/local-rohing/orch_r201_node4_20260918/node4/R195_FLEET/SCALE_physical7')
TARGETS = {
    'P7': dict(pid=1100592, start='28670738', guard=str(P7_BASE / 'r224_language_v3/control/GUARD.json'),
        guard_sha='cddb47df78958aee311c6ed120fbffb5cf1e4cb8017bc7ab399ff40627ed642d',
        target='/localhome/local-rohing/orch_r233_p7_deadline_20260918', wall=1790359200,
        ceiling=1790380800, journal='e9d22d1e26234c4bbac761922929365f'),
    'C2': dict(pid=3624513, start='25171256',
        guard='/localhome/local-rohing/orch_r222_C2_20260918_discussion2/control/GUARD.json',
        guard_sha='e4ec9ee6f9b481612061148a232750955a0c4e7fbbd1889f8c2213a4d1379e87',
        target='/localhome/local-rohing/orch_r233_C2_deadline_20260918', wall=1789927200,
        ceiling=1789948800, journal='260be8b8710a42559b291797c6e14983')
}


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def read(path):
    return json.loads(Path(path).read_bytes())


def sha(path):
    result = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            result.update(block)
    return result.hexdigest()


def digest(document):
    return hashlib.sha256(json.dumps(document, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()).hexdigest()


def write(path, value):
    path = Path(path)
    with path.open('x') as stream:
        json.dump(value, stream, sort_keys=True, indent=2)
        stream.write('\n')
        stream.flush()
        os.fsync(stream.fileno())


def deadline_plan(old, saved_sha, wall, ceiling):
    require(wall > old['hard_end_unix'] and ceiling - wall == 21600, 'authorized_six_hour_lease_margin')
    result = deepcopy(old)
    result.update(hard_end_unix=wall, lease_end_unix=ceiling,
        authorized_wall_extension=dict(schema='R131_SAVED_STATE_WALL_EXTENSION_V1',
            previous_deadline_unix=old['hard_end_unix'], previous_stream_sha256=saved_sha,
            new_deadline_unix=wall, lease_end_unix=ceiling, safety_margin_seconds=21600))
    normalized = deepcopy(result)
    normalized.pop('authorized_wall_extension')
    for key in ('hard_end_unix', 'lease_end_unix'):
        normalized[key] = old[key]
    if 'authorized_wall_extension' in old:
        normalized['authorized_wall_extension'] = old['authorized_wall_extension']
    require(normalized == old, 'only_deadline_delta_no_behavioral_or_source_change')
    return result


def boundary(root, journal):
    paths = sorted((Path(root) / 'stream/records').glob('[0-9]' * 20 + '.json'))
    complete = None
    tail = []
    for path in reversed(paths):
        with path.open('rb') as stream:
            stream.seek(max(0, path.stat().st_size - 1024))
            ending = stream.read()
        if b'"kind":"SLEEP_COMPLETE"' in ending or b'"kind": "SLEEP_COMPLETE"' in ending:
            complete = read(path)
            break
        record = read(path)
        tail.append(dict(index=record['index'], kind=record['kind'], sha256=record['sha256']))
    require(complete is not None and complete['journal_id'] == journal
        and complete['sha256'] == digest({key:value for key,value in complete.items() if key != 'sha256'}), 'latest_COMPLETE_integrity')
    require(all(record['kind'] in ('R184_LEARN_COMPLETE', 'INBOX') for record in tail),
        'no_post_COMPLETE_model_context_or_optimizer_advance')
    saved = complete['document']['resume_state']
    require(saved['sha256'] == digest(saved['state']) and saved['state']['pending'] is None
        and saved['state']['sleep_frontier'] == len(saved['state']['rows']), 'coherent_whole_saved_boundary')
    return complete, saved, tail


def prepare(name, commit):
    settings = TARGETS[name]
    require(not Path(f'/proc/{settings["pid"]}').exists(), 'exact_old_native_exited_before_resume')
    require(sha(settings['guard']) == settings['guard_sha'], 'same_original_guard')
    old_guard = read(settings['guard'])
    require(sha(old_guard['plan_path']) == old_guard['plan_sha256'], 'same_original_plan')
    old = read(old_guard['plan_path'])
    target, source = Path(settings['target']), Path(old['source_root'])
    target.mkdir(exist_ok=True)
    control = target / 'control'
    control.mkdir(exist_ok=True)
    require(not (control / 'READY.json').exists() and not (control / 'DISPATCHED.json').exists(),
        'no_duplicate_preparation_or_dispatch')
    complete, saved, tail = boundary(old['root'], settings['journal'])
    sys.path.insert(0, str(source))
    from gpu import orch_r125_continual_native as native
    checkpoint = complete['document']['checkpoint']
    native.NativeChild.verify_checkpoint(checkpoint)
    import torch
    payload = torch.load(checkpoint['optimizer_rng_path'], map_location='cpu', weights_only=False)
    require(payload['optimizer_steps'] == checkpoint['optimizer_steps'] > 0 and payload['optimizer']['state']
        and all(key in payload for key in ('cpu_rng', 'cuda_rng', 'python_rng')) and not torch.cuda.is_initialized(),
        'full_adapter_AdamW_RNG_CPU_verified')
    plan = deadline_plan(old, saved['sha256'], settings['wall'], settings['ceiling'])
    if (control / 'PLAN.json').exists():
        require(read(control / 'PLAN.json') == plan, 'same_preserved_preflight_plan')
    else:
        write(control / 'PLAN.json', plan)
    stream = native.ContinualStream.restore(saved, expected_sha256=saved['sha256'])
    extension = native.prepare_wall_extension(plan, stream, resume=True, plan_sha256=sha(control / 'PLAN.json'))
    checked_complete, checked_saved, checked_tail = boundary(old['root'], settings['journal'])
    require(checked_complete['sha256'] == complete['sha256'] and checked_saved == saved
        and checked_tail == tail, 'stable_latest_COMPLETE_after_full_checkpoint_verification')
    require(sha(old_guard['plan_path']) == old_guard['plan_sha256'], 'old_source_plan_unchanged')
    write(control / 'PRESERVED.json', dict(checkpoint=checkpoint, complete_index=complete['index'],
        complete_sha256=complete['sha256'], state_sha256=saved['sha256'], tail=tail,
        preserved_in_place=True, old_guard_path=settings['guard'], old_guard_sha256=settings['guard_sha'],
        old_native_pid=settings['pid'], old_native_absent=True, no_post_checkpoint_updates=True,
        inbox_sha256={path.name:sha(path) for path in (Path(old['root']) / 'stream/inbox').glob('*.json')},
        observed_unix=time.time(), exact_resident_continuity_claimed=False, native_signals=[]))
    write(control / 'CPU.json', dict(passed=True, deadline_only=True, unchanged_source_pins=old_guard['source_pins'],
        optimizer_steps=checkpoint['optimizer_steps'], full_AdamW_Python_CPU_CUDA_RNG=True,
        before_state_sha256=saved['sha256'], proposed_after_state_sha256=extension['state']['sha256'],
        full_replay_verified=False, unchanged_native_full_replay_required=True,
        source_hashes_validated_by_guard=True))
    lease = read(old_guard['lease_path'])
    lease.update(hard_end_unix=settings['wall'], lease_end_unix=settings['ceiling'],
        authority='Rohin September18 explicit deadline renewal with six-hour date-only lease margin',
        provider_exact_expiry_independently_verified=False)
    write(control / 'LEASE.json', lease)
    allocation = read(old_guard['allocation_path'])
    allocation.update(plan_sha256=sha(control / 'PLAN.json'), cpu_receipt_path=str(control / 'CPU.json'),
        cpu_receipt_sha256=sha(control / 'CPU.json'), declared_unix=time.time(),
        builder_entry_pushed=True, builder_entry_commit=commit,
        builder_entry='R233 explicit deadline-only same-COMPLETE continuation; CPU full-state provenance; no training-policy change')
    write(control / 'ALLOCATION.json', allocation)
    guard = deepcopy(old_guard)
    guard.update(plan_path=str(control / 'PLAN.json'), plan_sha256=sha(control / 'PLAN.json'),
        hard_end_unix=settings['wall'], next_reserved_unix=settings['ceiling'], lease_path=str(control / 'LEASE.json'),
        lease_sha256=sha(control / 'LEASE.json'), allocation_path=str(control / 'ALLOCATION.json'),
        allocation_sha256=sha(control / 'ALLOCATION.json'), attempt_dir=str(control), resume=True)
    guard['device_containment']['unit'] = 'orch-r136-native-' + uuid.uuid4().hex
    write(control / 'GUARD.json', guard)
    from gpu.orch_r125_continual_guard import validate
    validate(control / 'GUARD.json')
    write(control / 'READY.json', dict(status='CPU_TESTED_NOT_LIVE', created_unix=time.time(),
        guard_sha256=sha(control / 'GUARD.json'), complete_index=complete['index'],
        checkpoint_cycle=complete['document']['cycle'], optimizer_steps=checkpoint['optimizer_steps'],
        source_unchanged=True, behavioral_policy_unchanged=True, hard_end_unix=settings['wall']))
    print(json.dumps(read(control / 'READY.json')), flush=True)


def dispatch(name):
    settings = TARGETS[name]
    target = Path(settings['target'])
    control = target / 'control'
    ready = read(control / 'READY.json')
    guard = read(control / 'GUARD.json')
    plan = read(control / 'PLAN.json')
    require(ready['guard_sha256'] == sha(control / 'GUARD.json')
        and not Path(f'/proc/{settings["pid"]}').exists(), 'same_prepared_guard_old_native_absent')
    complete, saved, tail = boundary(plan['root'], settings['journal'])
    require(complete['index'] == ready['complete_index']
        and saved['sha256'] == plan['authorized_wall_extension']['previous_stream_sha256'], 'latest_no_stale_checkpoint_resume')
    if name == 'P7':
        old_binding = Path(plan['source_root']).parent / 'BRIDGE.json'
        config = read(old_binding)
        write(target / 'BRIDGE_BEFORE.json', config)
        config.update(guard_path=str(control / 'GUARD.json'), guard_sha256=sha(control / 'GUARD.json'),
            socket=str(control / 'cpu.sock'), stop_unix=settings['wall'], first_new_record=complete['index'] + 1)
        write(target / 'BRIDGE.json', config)
        temporary = old_binding.with_name('BRIDGE.deadline.next')
        write(temporary, config)
        os.replace(temporary, old_binding)
        with (target / 'BRIDGE.log').open('x') as output:
            bridge = subprocess.Popen([PYTHON, '-B', str(P7_BASE / 'math_c_bridge.py'), '--config', str(target / 'BRIDGE.json')],
                stdin=subprocess.DEVNULL, stdout=output, stderr=subprocess.STDOUT, start_new_session=True)
        until = time.monotonic() + 25
        while not list((target / 'bridge_receipts').glob('READY_*.json')):
            require(time.monotonic() < until and bridge.poll() is None, 'renewed_math_bridge_actual_ready')
            time.sleep(.2)
        module = 'gpu.r203_node4_containment'
    else:
        raise ValueError('C2_containment_module_must_be_source_verified_before_dispatch')
    with (control / 'SUPERVISOR.log').open('x') as output:
        supervisor = subprocess.Popen([PYTHON, '-B', '-m', module, 'contained-supervise', '--config', str(control / 'GUARD.json')],
            cwd=plan['source_root'], env=dict(os.environ, CUDA_VISIBLE_DEVICES='', PYTHONPATH=plan['source_root'], PYTHONDONTWRITEBYTECODE='1'),
            stdin=subprocess.DEVNULL, stdout=output, stderr=subprocess.STDOUT, start_new_session=True)
    write(control / 'DISPATCHED.json', dict(pid=supervisor.pid, dispatched_unix=time.time(), native_signals=[],
        hard_end_unix=settings['wall'], status='DISPATCHED_NOT_YET_LOADED', gap_claim='ACTUAL_RELOAD_GAP_NOT_ZERO_GAP'))
    print(json.dumps(read(control / 'DISPATCHED.json')), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=('prepare', 'dispatch'))
    parser.add_argument('life', choices=TARGETS)
    parser.add_argument('--commit')
    options = parser.parse_args()
    prepare(options.life, options.commit) if options.action == 'prepare' else dispatch(options.life)
