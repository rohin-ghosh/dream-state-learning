"""FINAL-only custody transfer using factual failed-startup exits, never CLEAN_RELEASE."""

import argparse
from copy import deepcopy
import fcntl
import os
from pathlib import Path
import sys
import time
from types import FunctionType

from gpu import orch_r118_code_parallel_final as previous
from gpu import orch_r118_code_parallel_recovery_final as timers


io, handoff, require = previous.io, previous.handoff, previous.require
SOURCE_ROOT = Path(__file__).resolve().parents[1]
MODULE = 'gpu.orch_r118_code_final_failed_release'
TRANSFER_END = previous.original.CUTOFF - 600


def unused_siblings(original, current):
    original, current = Path(original), Path(current)
    require(not previous.original.prior_final_attempts(original), 'no_original_FINAL_attempt')
    for sibling in (original / 'parallel_v4').glob('final_*'):
        if sibling.resolve() != current.resolve():
            require(not (sibling / 'ATTEMPT_ONCE').exists()
                and not (sibling / 'LAUNCH.json').exists()
                and not any((sibling / 'reservations').glob('*')), 'no_sibling_FINAL_attempt')


def facts(root):
    root = Path(root)
    record = io.read(root / 'FAILED_RELEASE_FACTS.json')
    plan = io.read(root / 'PLAN.json')
    require(record['original_root'] == plan['original_root'], 'same_original_life')
    proof = handoff.checked(record['proof'])
    require(proof['root'] == plan['original_root'] and proof['new_calls'] == 0
        and proof['optimizer_steps'] == 0, 'zero_new_training_failed_startup')
    require(record['predecessors'] and all(not handoff.alive(identity)
        for identity in record['predecessors']), 'all_failed_guard_native_exited')
    require(all(identity in record['predecessors'] for identity in proof['predecessors']),
        'all_proof_predecessors_bound')
    released = handoff.checked(record['release'])
    for name, expected in released['native']['boundary']['preserved_files'].items():
        require(io.sha(Path(plan['original_root']) / name) == expected, 'preserved_pending_and_charges')
    require(handoff.ledger(plan['original_root'])[0]['preserved'] == {
        name: expected for name, expected in released['native']['boundary']['preserved_files'].items()
        if name.startswith('reservations/')}, 'no_new_lifetime_charges')
    terminal = handoff.checked(record['guard_terminal'])
    require(terminal['native_alive'] is False, 'factual_failed_guard_terminal')
    require(not (Path(record['unused_service']) / 'LAUNCH.json').exists(), 'no_late_service4_actor')
    unused_siblings(plan['original_root'], root)
    return record


def validate_release(root):
    root = Path(root)
    record = facts(root)
    committed = io.read(root / 'TRANSFER_COMMITTED.json')
    require(committed['facts'] == handoff.ref(root / 'FAILED_RELEASE_FACTS.json')
        and committed['plan'] == handoff.ref(root / 'PLAN.json'), 'committed_exact_replacement_custody')
    require(not handoff.alive(record['old_timer']), 'old_FINAL_timer_exited')
    return dict(failed_release=handoff.ref(root / 'FAILED_RELEASE_FACTS.json'),
        custody=handoff.ref(root / 'TRANSFER_COMMITTED.json'), fabricated_clean_release=False)


def wait_release(root):
    return validate_release(root)


def functions():
    original = previous.original
    namespace = dict(vars(original), MODULE=MODULE, SOURCE_ROOT=SOURCE_ROOT,
        release=sys.modules[__name__])
    for name, value in vars(original).items():
        if isinstance(value, FunctionType) and value.__module__ == original.__name__:
            replacement = FunctionType(value.__code__, namespace, name, value.__defaults__, value.__closure__)
            replacement.__kwdefaults__ = value.__kwdefaults__
            namespace[name] = replacement
    return namespace


def prepare(root, old, prepared_reference, authorization):
    root, old = Path(root), Path(old)
    require(time.time() < TRANSFER_END and not root.exists(), 'new_FINAL_only_before1650')
    prepared = handoff.checked(prepared_reference)
    approved = handoff.checked(authorization)
    require(approved['scope'] == 'FINAL_ONLY_FAILED_STARTUP_RECOVERY'
        and approved['expires_unix'] == TRANSFER_END and approved['native_cap_per_branch'] == 8
        and approved['parent_cap'] == 0 and approved['optimizer_steps'] == 0
        and approved['destinations'][prepared['branch']] == str(root), 'exact_FINAL_only_authority')
    require(prepared['final_old_root'] == str(old), 'actual_old_custody')
    plan = deepcopy(previous.unused_allocation(old))
    timers.validate_timer(old, prepared['old_final_identity'])
    bound = io.read(old / 'FINAL_REBIND.json')
    proof = handoff.checked(prepared['proof'])
    identities = list(proof['predecessors'])
    for identity in (bound['native_identity'], bound['guardian_identity']):
        if identity not in identities:
            identities.append(identity)
    plan.update(source_root=str(SOURCE_ROOT), source_manifest=handoff.ref(SOURCE_ROOT.parent / 'SOURCE_SHA256.json'),
        cpu_receipt=handoff.ref(SOURCE_ROOT.parent / 'CPU_TESTS.json'), inherited_allocation=handoff.ref(old / 'PLAN.json'))
    root.mkdir()
    io.write(root / 'PLAN.json', plan)
    io.write(root / 'FAILED_RELEASE_FACTS.json', dict(schema='R118_CODE_FINAL_FAILED_RELEASE_V1',
        original_root=plan['original_root'], old_root=str(old), old_timer=prepared['old_final_identity'],
        proof=prepared['proof'], release=handoff.checked(prepared['owner']['handoff'])['release'],
        predecessors=identities, guard_terminal=handoff.ref(Path(bound['service']) / 'GUARD_TERMINAL.json'),
        unused_service=prepared['service'], authorization=authorization, old_plan=handoff.ref(old / 'PLAN.json'),
        no_training=True, fabricated_clean_release=False))
    functions()['validate_plan'](root)
    facts(root)
    io.write(root / 'PREPARED.json', dict(plan=handoff.ref(root / 'PLAN.json'), CPU_only=True,
        observed_unix=time.time(), native_cap_added=0))


def transfer(root, *, cancel=timers.cancel_timer, clock=time.time):
    root = Path(root)
    require(clock() < TRANSFER_END, 'transfer_before1650')
    functions()['validate_plan'](root)
    record = facts(root)
    armed = io.read(root / 'REPLACEMENT_ARMED.json')
    require(armed['plan'] == handoff.ref(root / 'PLAN.json')
        and armed['facts'] == handoff.ref(root / 'FAILED_RELEASE_FACTS.json')
        and handoff.alive(armed['identity']), 'replacement_custody_live_before_old_stop')
    with (root / 'TRANSFER.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        require(not (root / 'TRANSFER_INTENT.json').exists(), 'no_transfer_retry')
        io.write(root / 'TRANSFER_INTENT.json', dict(replacement=handoff.ref(root / 'REPLACEMENT_ARMED.json'),
            old_timer=record['old_timer'], observed_unix=clock()))
        stopped = cancel(Path(record['old_root']), record['old_timer'], clock=clock)
        require(not handoff.alive(record['old_timer']), 'old_timer_actually_exited')
        io.write(root / 'TRANSFER_COMMITTED.json', dict(plan=handoff.ref(root / 'PLAN.json'),
            facts=handoff.ref(root / 'FAILED_RELEASE_FACTS.json'), stopped=stopped,
            observed_unix=clock(), native_cap_added=0))


def schedule(root):
    root = Path(root)
    require(os.environ.get('CUDA_VISIBLE_DEVICES') == '', 'CPU_only_waiter')
    functions()['validate_plan'](root)
    facts(root)
    (root / 'REPLACEMENT_ONCE').mkdir()
    io.write(root / 'REPLACEMENT_ARMED.json', dict(identity=handoff.identities.identity(os.getpid()),
        plan=handoff.ref(root / 'PLAN.json'), facts=handoff.ref(root / 'FAILED_RELEASE_FACTS.json'),
        GPU_calls=0, observed_unix=time.time()))
    while not (root / 'TRANSFER_COMMITTED.json').exists():
        require(time.time() < TRANSFER_END, 'untransferred_waiter_expires1650')
        time.sleep(.2)
    validate_release(root)
    functions()['schedule'](root)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('phase', choices=('schedule', 'transfer', 'native'))
    parser.add_argument('--root', type=Path, required=True)
    args = parser.parse_args()
    if args.phase == 'native':
        functions()['native'](args.root)
    else:
        globals()[args.phase](args.root)
