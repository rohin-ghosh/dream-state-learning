"""Prospective FINAL custody rebind; same original eight calls, not new quota."""

import argparse
from copy import deepcopy
import os
from pathlib import Path
import select
import signal
import sys
import time
from types import FunctionType

from gpu import orch_r108_code_parent_r118_final as original
from gpu import orch_r118_code_parallel_handoff as handoff


io, require = handoff.io, handoff.require
MODULE = 'gpu.orch_r118_code_parallel_final'
SOURCE_ROOT = Path(__file__).resolve().parents[1]


def unused_allocation(root):
    root = Path(root)
    require(not (root / 'ATTEMPT_ONCE').exists() and not (root / 'LAUNCH.json').exists()
        and not any((root / 'reservations').glob('*')), 'old_FINAL_charges_never_reset_or_replayed')
    plan = io.read(root / 'PLAN.json')
    require(plan['schema'] == 'R118_CODE_FINAL_ALLOCATION_V1' and plan['native_cap'] == 8
        and plan['parent_cap'] == 0 and plan['decoder'] == original.DECODER
        and plan['cutoff_unix'] == original.CUTOFF and plan['hard_deadline_unix'] <= original.EVAL_END,
        'original_eight_call_allocation_only')
    for name, expected in handoff.checked(plan['source_manifest']).items():
        require(io.sha(Path(plan['source_root']) / name) == expected, 'old_FINAL_source_preserved')
    return plan


def cancel_timer(old_root, expected, *, clock=time.time):
    require(clock() < original.CUTOFF - 600, 'rebind_before_old_drain_window')
    unused_allocation(old_root)
    dispatched = io.read(Path(old_root) / 'CPU_DISPATCH.json')
    require(dispatched['identity'] == expected and handoff.alive(expected), 'exact_old_CPU_timer')
    command = (Path('/proc') / str(expected['pid']) / 'cmdline').read_bytes().split(b'\0')
    require(b'gpu.orch_r108_code_parent_r118_final' in command and b'schedule' in command
        and str(old_root).encode() in command, 'only_recorded_FINAL_scheduler')
    descriptor = os.pidfd_open(expected['pid'])
    try:
        require(handoff.alive(expected), 'same_timer_pidfd')
        signal.pidfd_send_signal(descriptor, signal.SIGTERM)
        require(select.select([descriptor], [], [], 5)[0], 'old_CPU_timer_exited')
    finally:
        os.close(descriptor)
    return dict(identity=expected, actual_exit_unix=clock(), old_dispatch=handoff.ref(Path(old_root) / 'CPU_DISPATCH.json'),
        original_allocation=handoff.ref(Path(old_root) / 'PLAN.json'), cancelled_only_CPU_waiter=True)


def rebind(old_root, new_root, service, authorization, *, clock=time.time, cancel=cancel_timer):
    old_root, new_root, service = Path(old_root), Path(new_root), Path(service)
    require(not new_root.exists(), 'new_eval_custody_root')
    previous = unused_allocation(old_root)
    document, own, original_plan = handoff.authorize(authorization, previous['original_root'], 'LAUNCH', clock)
    require(own['final_old_root'] == str(old_root.resolve()) and own['final_new_root'] == str(new_root.resolve())
        and own['service'] == str(service.resolve()), 'Main_exact_FINAL_custody_roots')
    source_manifest = handoff.ref(SOURCE_ROOT.parent / 'SOURCE_SHA256.json')
    require(own['source_manifest_sha256'] == source_manifest['sha256'], 'Main_pinned_FINAL_successor')
    prospective = deepcopy(previous)
    prospective.update(source_root=str(SOURCE_ROOT), source_manifest=source_manifest,
        cpu_receipt=handoff.ref(SOURCE_ROOT.parent / 'CPU_TESTS.json'))
    functions()['source_check'](prospective)
    runtime = io.read(service / 'RUNTIME.json')
    released = handoff.checked(runtime['handoff'])
    require(runtime['root'] == previous['original_root'] and released['all_original_processes_exited'] is True
        and not handoff.alive(released['native']['identity']) and not handoff.alive(released['guardian']),
        'old_CODE_actual_exit_required')
    launched = io.read(service / 'LAUNCH.json')
    require(handoff.alive(launched['identity']) and handoff.alive(launched['guardian']), 'actual_new_guard_native_binding')
    expected_timer = io.read(old_root / 'CPU_DISPATCH.json')['identity']
    new_root.mkdir(parents=True)
    io.write(new_root / 'REBIND_STARTED.json', dict(old_allocation=handoff.ref(old_root / 'PLAN.json'),
        old_timer=expected_timer, authorization=authorization, source_generation='PROSPECTIVE_PARALLEL_SUCCESSOR'))
    stopped = cancel(old_root, expected_timer, clock=clock)
    plan = prospective
    plan.update(source_root=str(SOURCE_ROOT), source_manifest=handoff.ref(SOURCE_ROOT.parent / 'SOURCE_SHA256.json'),
        cpu_receipt=handoff.ref(SOURCE_ROOT.parent / 'CPU_TESTS.json'), inherited_allocation=handoff.ref(old_root / 'PLAN.json'))
    io.write(new_root / 'FINAL_REBIND.json', dict(schema='R118_CODE_FINAL_CUSTODY_REBIND_V1',
        old_root=str(old_root), service=str(service), old_timer_stop=stopped,
        old_handoff=runtime['handoff'], new_launch=handoff.ref(service / 'LAUNCH.json'),
        native_identity=launched['identity'], guardian_identity=launched['guardian'],
        same_eight_calls=True, native_cap_added=0, old_ledger_preserved=True,
        canonical_selection_path=plan['main_binding_path']))
    plan['rebind_reference'] = handoff.ref(new_root / 'FINAL_REBIND.json')
    io.write(new_root / 'PLAN.json', plan)
    functions()['validate_plan'](new_root)
    return plan


def bind_supervision(root, authorization):
    root = Path(root)
    plan = functions()['validate_plan'](root)
    bound = handoff.checked(plan['rebind_reference'])
    service = Path(bound['service'])
    document, own, unused = handoff.authorize(authorization, plan['original_root'], 'LAUNCH')
    require(own['final_new_root'] == str(root.resolve()) and own['service'] == str(service.resolve()),
        'Main_exact_final_supervision')
    launched = handoff.checked(bound['new_launch'])
    timer = io.read(root / 'CPU_DISPATCH.json')['identity']
    started = io.read(root / 'SCHEDULER_STARTED.json')
    require(started['pid'] == timer['pid'] and handoff.alive(timer), 'actual_successor_FINAL_timer')
    command = (Path('/proc') / str(timer['pid']) / 'cmdline').read_bytes().split(b'\0')
    require(MODULE.encode() in command and b'schedule' in command and str(root).encode() in command,
        'exact_parallel_FINAL_timer_command')
    supervision = dict(native_identity=handoff.collective_identity(launched['identity']),
        guard_identity=handoff.collective_identity(launched['guardian']), guard_binding=bound['new_launch'],
        final_identity_bindings=[dict(identity=handoff.collective_identity(timer),
            evidence=handoff.ref(root / 'CPU_DISPATCH.json'))],
        final_plan=handoff.ref(root / 'PLAN.json'), owner_verified_safe_for_parallel=True)
    io.write(service / 'SUPERVISION.json', supervision)
    return supervision


def schedule(root):
    root = Path(root)
    require(os.environ.get('CUDA_VISIBLE_DEVICES') == '', 'CPU_parallel_FINAL_timer')
    functions()['validate_plan'](root)
    io.write(root / 'CPU_DISPATCH.json', dict(identity=handoff.identities.identity(os.getpid()),
        module=MODULE, custody=handoff.ref(root / 'FINAL_REBIND.json'), observed_unix=time.time()))
    functions()['schedule'](root)


def validate_release(root):
    root = Path(root)
    plan = io.read(root / 'PLAN.json')
    bound = handoff.checked(plan['rebind_reference'])
    unused_allocation(bound['old_root'])
    require(not handoff.alive(bound['old_timer_stop']['identity']), 'old_timer_must_remain_stopped')
    handoff.checked(bound['new_launch'])
    require(not handoff.alive(bound['native_identity']) and not handoff.alive(bound['guardian_identity']),
        'new_parallel_native_and_guard_exited')
    service = Path(bound['service'])
    clean = io.read(service / 'CLEAN_RELEASE.json')
    require(clean['actual_settled_boundary'] is True and clean['identity'] == bound['native_identity'],
        'actual_parallel_settled_cursor')
    handoff.checked(clean['cursor'])
    terminal = io.read(service / 'GUARD_TERMINAL.json')
    require(terminal['identity'] == bound['native_identity'] and terminal['native_alive'] is False,
        'actual_guard_terminal')
    original_root = io.read(root / 'PLAN.json')['original_root']
    require(handoff.ledger(original_root)[0]['preserved'] == clean['charges']['preserved'],
        'no_post_parallel_release_calls')
    return dict(clean_release=handoff.ref(service / 'CLEAN_RELEASE.json'),
        guard_terminal=handoff.ref(service / 'GUARD_TERMINAL.json'), custody=handoff.ref(root / 'FINAL_REBIND.json'))


def wait_release(root):
    root = Path(root)
    plan = io.read(root / 'PLAN.json')
    bound = handoff.checked(plan['rebind_reference'])
    service = Path(bound['service'])
    while time.time() < plan['hard_deadline_unix'] - 30:
        if (service / 'CLEAN_RELEASE.json').exists() and (service / 'GUARD_TERMINAL.json').exists():
            if not handoff.alive(bound['native_identity']) and not handoff.alive(bound['guardian_identity']):
                receipt = validate_release(root)
                io.write(root / 'PREDECESSOR_RELEASE.json', receipt)
                return receipt
        time.sleep(5)
    return None


def functions():
    namespace = dict(vars(original), MODULE=MODULE, SOURCE_ROOT=SOURCE_ROOT, release=sys.modules[__name__])
    for name, value in vars(original).items():
        if isinstance(value, FunctionType) and value.__module__ == original.__name__:
            namespace[name] = FunctionType(value.__code__, namespace, name, value.__defaults__, value.__closure__)
            namespace[name].__kwdefaults__ = value.__kwdefaults__
    return namespace


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('entry', choices=('schedule', 'native', 'rebind', 'bind-supervision'))
    parser.add_argument('--root', required=True, type=Path)
    parser.add_argument('--old-root', type=Path)
    parser.add_argument('--service', type=Path)
    parser.add_argument('--authorization', type=Path)
    args = parser.parse_args()
    if args.entry == 'rebind':
        require(args.old_root is not None and args.service is not None and args.authorization is not None,
            'explicit_rebind_inputs')
        rebind(args.old_root, args.root, args.service, handoff.ref(args.authorization))
    elif args.entry == 'bind-supervision':
        require(args.authorization is not None, 'Main_authorization_required')
        bind_supervision(args.root, handoff.ref(args.authorization))
    elif args.entry == 'schedule':
        schedule(args.root)
    else:
        functions()['native'](args.root)
