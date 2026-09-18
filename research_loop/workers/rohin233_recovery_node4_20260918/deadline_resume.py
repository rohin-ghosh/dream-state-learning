"""Exact durable-COMPLETE deadline-only continuation; no behavioral-policy delta."""

import argparse
from copy import deepcopy
import hashlib
import json
import os
from pathlib import Path
import select
import shutil
import signal
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


def boundary(root, journal, require_idle=True):
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
    if require_idle:
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
    if 'device_containment' in guard:
        guard['device_containment']['unit'] = 'orch-r136-native-' + uuid.uuid4().hex
    write(control / 'GUARD.json', guard)
    from gpu.orch_r125_continual_guard import validate
    validate(control / 'GUARD.json')
    if name == 'C2':
        write(control / 'RECEIVING_CPU.json', dict(passed=True, source_pins=guard['source_pins'],
            source_unchanged=True, original_receiving_receipt_sha256=sha(Path(settings['guard']).parent / 'RECEIVING_CPU.json'),
            deadline_continuation_receipt_sha256=sha(control / 'CPU.json')))
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
    old_binding = Path(plan['source_root']).parent / 'BRIDGE.json'
    config = read(old_binding)
    write(target / 'BRIDGE_BEFORE.json', config)
    config.update(guard_path=str(control / 'GUARD.json'), guard_sha256=sha(control / 'GUARD.json'),
        socket=str(control / 'cpu.sock'), stop_unix=settings['wall'], first_new_record=complete['index'] + 1)
    write(target / 'BRIDGE.json', config)
    temporary = old_binding.with_name('BRIDGE.deadline.next')
    write(temporary, config)
    os.replace(temporary, old_binding)
    bridge_script = P7_BASE / 'math_c_bridge.py' if name == 'P7' else Path(plan['source_root']).parent / 'math_bridge.py'
    with (target / 'BRIDGE.log').open('x') as output:
        bridge = subprocess.Popen([PYTHON, '-B', str(bridge_script), '--config', str(target / 'BRIDGE.json')],
            stdin=subprocess.DEVNULL, stdout=output, stderr=subprocess.STDOUT, start_new_session=True)
    until = time.monotonic() + 25
    while not list((target / 'bridge_receipts').glob('READY_*.json')):
        require(time.monotonic() < until and bridge.poll() is None, 'renewed_math_bridge_actual_ready')
        time.sleep(.2)
    module, action = ('gpu.r203_node4_containment', 'contained-supervise') if name == 'P7' else ('gpu.r188_node5_confinement', 'dispatch')
    with (control / 'SUPERVISOR.log').open('x') as output:
        supervisor = subprocess.Popen([PYTHON, '-B', '-m', module, action, '--config', str(control / 'GUARD.json')],
            cwd=plan['source_root'], env=dict(os.environ, CUDA_VISIBLE_DEVICES='', PYTHONPATH=plan['source_root'], PYTHONDONTWRITEBYTECODE='1'),
            stdin=subprocess.DEVNULL, stdout=output, stderr=subprocess.STDOUT, start_new_session=True)
    write(control / 'DISPATCHED.json', dict(pid=supervisor.pid, dispatched_unix=time.time(), native_signals=[],
        hard_end_unix=settings['wall'], status='DISPATCHED_NOT_YET_LOADED', gap_claim='ACTUAL_RELOAD_GAP_NOT_ZERO_GAP'))
    print(json.dumps(read(control / 'DISPATCHED.json')), flush=True)


def identity(pid):
    process = Path('/proc') / str(pid)
    fields = (process / 'stat').read_text().rsplit(') ', 1)[1].split()
    require(fields[0] != 'Z', 'live_not_zombie_process')
    return dict(pid=pid, start_ticks=fields[19], uid=process.stat().st_uid,
        cwd=os.readlink(process / 'cwd'), argv=(process / 'cmdline').read_bytes().decode().strip('\0').split('\0'),
        cgroup=(process / 'cgroup').read_text().strip())


def actor(name, plan):
    settings = TARGETS[name]
    actual = identity(settings['pid'])
    require(actual['start_ticks'] == settings['start'] and actual['uid'] == 2524
        and actual['cwd'] == plan['source_root'] and actual['argv'] == [PYTHON, '-B', '-m',
            'gpu.orch_r125_continual_guard', 'native', '--config', settings['guard']], 'exact_original_native_identity')
    if name == 'C2':
        require(actual['cgroup'] == '0::/system.slice/orch-r188-node5-c2-child-e4ec9ee6f9b48161.service',
            'exact_original_C2_containment')
    return actual


def blocked_readout(name, plan, complete):
    settings = TARGETS[name]
    process = Path('/proc') / str(settings['pid'])
    children = (process / 'task' / str(settings['pid']) / 'children').read_text().split()
    wait = (process / 'wchan').read_text().strip()
    if len(children) != 1 or not ('wait' in wait or wait == 'hrtimer_nanosleep'):
        return None
    child = identity(int(children[0]))
    checkpoint = str(Path(complete['document']['checkpoint']['adapter_path']).parent / 'COMMIT.json')
    prefix = [PYTHON, '-B', '-m', 'gpu.orch_r125_continual_readout', '--plan',
        str(Path(settings['guard']).parent / 'PLAN.json'), '--checkpoint', checkpoint, '--output']
    if (child['argv'][:len(prefix)] != prefix or child['cwd'] != plan['source_root'] or child['uid'] != 2524
            or child['cgroup'] != actor(name, plan)['cgroup']):
        return None
    return child


def continue_at_complete(name, commit):
    require(name == 'C2', 'currently_only_exact_C2_live_continuation')
    settings = TARGETS[name]
    require(sha(settings['guard']) == settings['guard_sha'], 'source_bound_original_C2_guard')
    old_guard = read(settings['guard'])
    plan = read(old_guard['plan_path'])
    sys.path.insert(0, plan['source_root'])
    from gpu.orch_r125_continual_guard import validate
    from gpu.orch_r125_continual_native import NativeChild
    validate(settings['guard'])
    original = actor(name, plan)
    target = Path(settings['target'])
    target.mkdir(exist_ok=True)
    baseline, unused_saved, unused_tail = boundary(plan['root'], settings['journal'], require_idle=False)
    write(target / 'WAITING_NEXT_COMPLETE.json', dict(actor=original, baseline_index=baseline['index'],
        began_unix=time.time(), pending_deadline=settings['wall'], no_SIGSTOP=True, no_hold=True,
        no_training_policy_change=True, authority='Rohin explicit same-COMPLETE continuation'))
    descriptor = os.pidfd_open(settings['pid'])
    try:
        until = time.monotonic() + 2700
        while time.monotonic() < until:
            require(actor(name, plan) == original, 'same_pidfd_native_before_boundary')
            try:
                complete, saved, tail = boundary(plan['root'], settings['journal'])
            except ValueError as error:
                if str(error) != 'no_post_COMPLETE_model_context_or_optimizer_advance':
                    raise
                time.sleep(.25)
                continue
            if complete['index'] <= baseline['index']:
                time.sleep(.25)
                continue
            reader = blocked_readout(name, plan, complete)
            if reader is None:
                time.sleep(.25)
                continue
            NativeChild.verify_checkpoint(complete['document']['checkpoint'])
            import torch
            payload = torch.load(complete['document']['checkpoint']['optimizer_rng_path'], map_location='cpu', weights_only=False)
            require(payload['optimizer_steps'] == complete['document']['checkpoint']['optimizer_steps']
                and payload['optimizer']['state'] and all(key in payload for key in ('cpu_rng', 'cuda_rng', 'python_rng'))
                and not torch.cuda.is_initialized(), 'durable_full_AdamW_and_RNG_before_exact_exit')
            checked, checked_saved, checked_tail = boundary(plan['root'], settings['journal'])
            if (checked['sha256'] != complete['sha256'] or checked_saved != saved or checked_tail != tail
                    or blocked_readout(name, plan, complete) != reader or actor(name, plan) != original):
                continue
            preservation = dict(actor=original, readout=reader, complete_index=complete['index'],
                complete_sha256=complete['sha256'], checkpoint=complete['document']['checkpoint'],
                state_sha256=saved['sha256'], tail=tail, observed_unix=time.time(), root=plan['root'],
                backing_root=str(Path(plan['root']).resolve()), preserved_in_place=True,
                inbox_sha256={path.name:sha(path) for path in (Path(plan['root'])/'stream/inbox').glob('*.json')},
                no_SIGSTOP=True, no_hold=True, intent='CONTINUE_SAME_LIFE_NOT_RETIRE')
            proof_path = target / f'BOUNDARY_CHECK_{time.time_ns()}.json'
            write(proof_path, preservation)
            final, final_saved, final_tail = boundary(plan['root'], settings['journal'])
            if (final['sha256'] != complete['sha256'] or final_saved != saved or final_tail != tail
                    or blocked_readout(name, plan, complete) != reader or actor(name, plan) != original):
                continue
            signaled = time.time()
            signal.pidfd_send_signal(descriptor, signal.SIGTERM)
            poller = select.poll()
            poller.register(descriptor, select.POLLIN)
            require(poller.poll(15000), 'exact_original_C2_exit_observed')
            after, after_saved, after_tail = boundary(plan['root'], settings['journal'])
            require(after['sha256'] == complete['sha256'] and after_saved == saved and after_tail == tail,
                'no_model_or_history_advance_after_exact_complete_exit')
            write(target / 'CONTINUATION_EXIT.json', dict(actor=original, signaled_unix=signaled,
                exited_observed_unix=time.time(), signal='pidfd_SIGTERM', no_SIGSTOP=True,
                preservation_path=str(proof_path), preservation_sha256=sha(proof_path),
                complete_index=complete['index'], purpose='AUTHORIZED_CHECKPOINT_RESUME_NOT_RETIREMENT',
                readout_may_be_interrupted_not_success_claimed=True, other_life_signals=[]))
            limit = time.monotonic() + 20
            while Path(f'/proc/{settings["pid"]}').exists():
                require(time.monotonic() < limit, 'exact_old_native_reaped_before_resume')
                time.sleep(.2)
            prepare(name, commit)
            dispatch(name)
            return
        raise TimeoutError('finite_next_COMPLETE_window_expired_no_native_signal')
    finally:
        os.close(descriptor)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=('prepare', 'dispatch', 'continue'))
    parser.add_argument('life', choices=TARGETS)
    parser.add_argument('--commit')
    options = parser.parse_args()
    if options.action == 'continue':
        continue_at_complete(options.life, options.commit)
    elif options.action == 'prepare':
        prepare(options.life, options.commit)
    else:
        dispatch(options.life)
