"""FINAL-only custody after failed startup; inherits the existing eight-call quota."""

import argparse
from copy import deepcopy
import fcntl
import json
import os
from pathlib import Path
import subprocess
import time
from types import FunctionType

from gpu import orch_math_feedback_uptake_r118_final as original
from gpu import orch_math_feedback_uptake_r118_second_exit as recovery

life = recovery.life
require, ref, read, write = original.require, original.ref, original.read, original.write
MODULE = 'gpu.orch_math_feedback_uptake_r118_final_custody'
SOURCE = Path(__file__).resolve().parents[1]
OUTPUT = Path('/localhome/local-rohing/orch_math_feedback_uptake_r118_final_custody_20260915_attempt1')
SERVICES = recovery.SERVICES


def functions():
    namespace = dict(vars(original), MODULE=MODULE, SOURCE=SOURCE, OUTPUT=OUTPUT)
    for name, value in vars(original).items():
        if isinstance(value, FunctionType) and value.__module__ == original.__name__:
            namespace[name] = FunctionType(value.__code__, namespace, name, value.__defaults__, value.__closure__)
            namespace[name].__kwdefaults__ = value.__kwdefaults__
    namespace['legacy_validate'] = namespace['validate']
    namespace.update(validate=validate, release=release)
    return namespace


def evaluation_chain(reference):
    chain, seen = [], set()
    while reference is not None:
        require(reference['path'] not in seen and len(chain) < 32, 'acyclic_evaluation_lineage')
        seen.add(reference['path'])
        document = original.bound(reference)
        require(document['native_cap'] == 8 and document['parent_cap'] == 0,
            'same_eight_call_parent_free_lineage')
        chain.append(dict(reference=reference, root=document['root']))
        reference = document.get('previous_evaluation_plan')
    require(bool(chain), 'actual_original_quota_lineage')
    return chain


def custody(plan):
    evidence = original.bound(plan['failed_startup_custody'])
    service = Path(evidence['service'])
    require(service == SERVICES / ('lane'+str(plan['physical'])), 'exact_never_dispatched_service')
    for name in ('GUARD_STARTED.json', 'LAUNCH.json', 'TIMERS_DISPATCHED.json', 'CUTOFF_ARMED.json'):
        require(not (service/name).exists(), 'attempt5_must_remain_never_dispatched')
    runtime = original.bound(evidence['runtime'])
    released = original.bound(evidence['release'])
    require(runtime['release'] == evidence['release'] and released['status'] == 'RELEASED'
        and released['root'] == plan['original_root'], 'actual_failed_predecessor_release')
    failed = original.bound(evidence['second_failure'])
    require(failed['status'] == 'CPU_CHILD_EXITED_BEFORE_MODEL_BOOTSTRAP'
        and failed['native_calls'] == 0 and failed['signals'] == 0, 'real_failure_not_fake_CLEAN')
    terminal = original.bound(failed['guard_terminal'])
    require(terminal['status'] == 'FAILED' and terminal['native_alive'] is False
        and terminal['no_retry'] is True and terminal['identity'] == failed['native'],
        'authentic_spawned_child_FAILED_not_CLEAN')
    failure = original.bound(failed['failed_dispatch'])
    require(failure['session_sha256'] == recovery.FAILED_SESSION and failure['retry_allowed'] is False,
        'original_second_session_failure_preserved')
    for actor in released['predecessors']:
        require(not life.alive(actor), 'failed_predecessor_still_live')
    retirement = original.bound(evidence['timer_retirement'])
    require(retirement['release'] == evidence['release'], 'actual_attempt5_retirement_binding')
    for timer in retirement['timers']:
        original.bound(timer['record'])
        require(not life.alive(timer['identity']) and timer['actual_eval_calls'] == 0,
            'prior_FINAL_timer_still_live_or_used')
    saved = original.bound(released['boundary'])
    life.boundary.unchanged(Path(plan['original_root']), saved['preserved_files'])
    require(read(Path(plan['original_root'])/'COUNTERS.json') == saved['counters'], 'no_charge_reset_or_new_collection')
    require(not life.drain.live_readout_identities(Path(plan['original_root'])), 'no_live_old_readout')
    return dict(failed_startup_custody=plan['failed_startup_custody'],
        authentic_predecessor_release=evidence['release'], authentic_failed_terminal=failed['guard_terminal'],
        timer_retirement=evidence['timer_retirement'], never_dispatched_service=str(service),
        no_fabricated_clean_release=True)


def prepare(branch, manifest, tests):
    require(branch in original.MEMBERS and time.time() < original.START, 'prospective_FINAL_only')
    physical = original.MEMBERS[branch][0]
    service, root = SERVICES/f'lane{physical}', OUTPUT/f'lane{physical}'
    require(not root.exists(), 'unique_FINAL_custody_namespace')
    previous = read(service/'PLAN.json')
    inherited = original.bound(previous['old_evaluation_plan'])
    chain = evaluation_chain(previous['old_evaluation_plan'])
    evidence = dict(service=str(service), runtime=ref(service/'RUNTIME.json'),
        release=ref(service/'RELEASED.json'), second_failure=ref(service/'PREINFERENCE_EXIT.json'),
        timer_retirement=ref(service/'FINAL_TIMERS_RETIRED.json'),
        authority='Main FINAL-only recovery original8calls/branch 17:00-17:20; no TRAIN restart',
        startup_authorization_expired=True, observed_unix=time.time())
    write(root/'FAILED_STARTUP_CUSTODY.json', evidence)
    plan = deepcopy(inherited)
    plan.update(root=str(root), source_root=str(SOURCE), source_manifest=manifest, tests=tests,
        previous_evaluation_plan=previous['old_evaluation_plan'],
        failed_startup_custody=ref(root/'FAILED_STARTUP_CUSTODY.json'), evaluation_chain=chain,
        quota_id=original.digest(dict(branch=branch, original_quota=chain[-1]['reference'], native=8)),
        quota_claim=str(Path(plan['original_root'])/'R118_FINAL_ALLOCATION_CLAIM.json'),
        quota_lock=str(Path(plan['original_root'])/'R118_FINAL_ALLOCATION.lock'),
        custody_note='SAME_UNUSED_EIGHT_CALL_ALLOCATION_NOT_NEW_QUOTA',
        authority=evidence['authority'])
    write(root/'PLAN.json', plan)
    validate(root)
    write(root/'DENOMINATORS.json', dict(planned_native=8, parent=0, optimizer_steps=0,
        extra_native_authorized=0, retries=0, quota_id=plan['quota_id']))
    return ref(root/'PLAN.json')


def validate(root):
    plan = functions()['legacy_validate'](Path(root))
    chain = evaluation_chain(plan['previous_evaluation_plan'])
    require(chain == plan['evaluation_chain'] and plan['quota_id'] == original.digest(
        dict(branch=plan['branch'], original_quota=chain[-1]['reference'], native=8)), 'one_original_quota')
    require(plan['quota_claim'] == str(Path(plan['original_root'])/'R118_FINAL_ALLOCATION_CLAIM.json')
        and plan['quota_lock'] == str(Path(plan['original_root'])/'R118_FINAL_ALLOCATION.lock'), 'one_original_claim_location')
    custody(plan)
    return plan


def attempts(plan, now):
    original.window(plan, now)
    found = original.prior_attempts(plan['original_root'], now)
    for entry in plan['evaluation_chain']:
        root = Path(entry['root'])
        found.extend(str(root/name) for name in ('LEDGER.json', 'NATIVE_CLAIM.json', 'LAUNCH.json')
            if (root/name).exists())
        found.extend(str(path) for path in root.glob('CALL_*.json'))
    return sorted(set(found))


def claim(plan):
    original.window(plan, time.time())
    require(not attempts(plan, time.time()), 'prior_FINAL_attempt_no_retry')
    document = dict(quota_id=plan['quota_id'], root=plan['root'], plan=ref(Path(plan['root'])/'PLAN.json'),
        native_cap=8, parent=0, optimizer_steps=0, attempt=1, retry=False, claimed_unix=time.time())
    write(plan['quota_claim'], document)
    return ref(plan['quota_claim'])


def release(plan):
    released = custody(plan)
    require(not attempts(plan, time.time()), 'prior_FINAL_attempt_no_retry')
    if Path(plan['quota_claim']).exists():
        claimed = read(plan['quota_claim'])
        require(claimed['quota_id'] == plan['quota_id'] and claimed['root'] == plan['root']
            and claimed['plan'] == ref(Path(plan['root'])/'PLAN.json'), 'no_other_quota_owner')
    return released


def schedule(root):
    root = Path(root)
    plan = validate(root)
    child = expected = None
    status = 'NOT_RUN'
    with Path(plan['quota_lock']).open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        write(root/'SCHEDULED.json', dict(identity=life.identity(os.getpid()), plan=ref(root/'PLAN.json'),
            status='ARMED_NOT_EVALUATED', quota_id=plan['quota_id'], GPU_allocated=False, observed_unix=time.time()))
        try:
            while time.time() < original.START:
                time.sleep(min(5, original.START-time.time()))
            original.window(plan, time.time())
            require(not Path(plan['quota_claim']).exists(), 'already_claimed_FINAL_no_retry')
            while time.time() < plan['end_unix']-120:
                released = release(plan)
                if Path(plan['selection_path']).exists():
                    selected = functions()['selection'](plan, time.time())
                    write(root/'RELEASE.json', released)
                    write(root/'SELECTED.json', dict(selection=selected, reference=ref(plan['selection_path'])))
                    break
                time.sleep(2)
            else:
                raise TimeoutError('canonical_selection_unavailable')
            result = subprocess.run(['sudo', '-n', 'env', 'CUDA_VISIBLE_DEVICES=', 'PYTHONDONTWRITEBYTECODE=1',
                'PYTHONPATH='+str(SOURCE), 'python3', '-B', '-m', MODULE, 'scan', '--root', str(root)],
                capture_output=True, text=True, check=True, timeout=min(90, plan['end_unix']-time.time()))
            admission = json.loads(result.stdout)
            write(root/'ADMISSION.json', admission)
            require(admission['clear'] and admission['scanner_euid'] == 0 and not admission['blocking_reasons'],
                'strict_fresh_FINAL_full_proc_UUID_admission')
            release(plan)
            write(root/'NATIVE_CLAIM.json', dict(allocation=claim(plan), retry=False, attempt=1))
            with (root/'NATIVE.log').open('x') as log:
                child = subprocess.Popen([life.previous.math.PYTHON, '-B', '-m', MODULE, 'native', '--root', str(root)],
                    cwd=SOURCE, stdin=subprocess.DEVNULL, stdout=log, stderr=subprocess.STDOUT, start_new_session=True,
                    env=dict(os.environ, CUDA_VISIBLE_DEVICES=plan['uuid'], PYTHONPATH=str(SOURCE),
                        PYTHONDONTWRITEBYTECODE='1', HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1',
                        OMP_NUM_THREADS='1', MKL_NUM_THREADS='1', TOKENIZERS_PARALLELISM='false'))
                for observation in range(100):
                    expected = life.identity(child.pid)
                    if MODULE.encode() in (Path('/proc')/str(child.pid)/'cmdline').read_bytes().split(b'\0'):
                        break
                    time.sleep(.01)
                else:
                    raise ValueError('actual_FINAL_exec_not_observed')
                write(root/'LAUNCH.json', dict(identity=expected, uuid=plan['uuid'], observed_unix=time.time()))
                require(child.wait(timeout=max(.01, plan['end_unix']-20-time.time())) == 0
                    and (root/'COMPLETE.json').exists(), 'fresh_FINAL_failed_no_retry')
                status = 'COMPLETE'
        except BaseException as error:
            status = 'FAILED' if child is not None or Path(plan['quota_claim']).exists() else 'NOT_RUN'
            write(root/(status+'.json'), dict(reason=type(error).__name__+': '+str(error),
                retry=False, observed_unix=time.time()))
        finally:
            if child is not None and child.poll() is None:
                life.terminate_owned(expected, force=True)
            write(root/'TERMINAL.json', dict(status=status, **original.denominators(root),
                original_allocation_unchanged=True, quota_claimed=Path(plan['quota_claim']).exists(),
                observed_unix=time.time()))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('phase', choices=('prepare', 'schedule', 'scan', 'native'))
    parser.add_argument('--branch', choices=tuple(original.MEMBERS))
    parser.add_argument('--root', type=Path)
    parser.add_argument('--manifest', type=Path)
    parser.add_argument('--tests', type=Path)
    args = parser.parse_args()
    if args.phase == 'prepare':
        print(json.dumps(prepare(args.branch, ref(args.manifest), ref(args.tests))))
    elif args.phase == 'schedule':
        schedule(args.root)
    elif args.phase == 'scan':
        plan = validate(args.root)
        original.window(plan, time.time())
        print(json.dumps(recovery.prior.fresh_scan(Path(plan['original_root']).parent, plan['physical'])))
    else:
        plan = validate(args.root)
        original.window(plan, time.time())
        require(Path(plan['quota_claim']).exists(), 'allocation_claim_before_native')
        functions()['native'](args.root)


if __name__ == '__main__':
    main()
