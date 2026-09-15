"""New pre-inference recovery namespace; one pidfd-bound scan, no automatic retry."""

import argparse
from copy import deepcopy
import hashlib
import json
import os
from pathlib import Path
import resource
import time

from gpu import orch_admission_transient_exit as transient
from gpu import orch_math_feedback_uptake_r118_parallel_lifecycle as life
from gpu import orch_math_feedback_uptake_r118_parallel_native as native
from gpu import orch_math_feedback_uptake_r118_parallel_final as final
from gpu import orch_math_feedback_uptake_r118_argv_admission as argv_admission


MODULE = 'gpu.orch_math_feedback_uptake_r118_preinfer'
SERVICES = Path('/localhome/local-rohing/orch_math_feedback_uptake_r118_preinfer_20260915_attempt4')
FINALS = Path('/localhome/local-rohing/orch_math_feedback_uptake_r118_preinfer_final_20260915_attempt4')
PREVIOUS = Path('/localhome/local-rohing/orch_math_feedback_uptake_r118_parallel_20260915_attempt2')
require = life.require


def bind_scan(scanner):
    require(os.geteuid() == 0, 'fresh_same_process_root_scan_required')
    previous_limit = resource.getrlimit(resource.RLIMIT_NOFILE)
    required = 4096 + len(os.listdir('/proc/self/fd')) + 256
    require(previous_limit[1] == resource.RLIM_INFINITY or previous_limit[1] >= required,
        'sufficient_hard_pidfd_budget_required')
    changed = previous_limit[0] != resource.RLIM_INFINITY and previous_limit[0] < required
    if changed:
        resource.setrlimit(resource.RLIMIT_NOFILE, (required, previous_limit[1]))
    try:
        envelope = transient.reconcile_scan(scanner)
    finally:
        if changed:
            resource.setrlimit(resource.RLIMIT_NOFILE, previous_limit)
    require(envelope['schema'] == 'orch_admission_transient_exit/v1', 'exact_transient_proof_schema')
    report = deepcopy(envelope['original_report'])
    canonical = json.dumps(report, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()
    require(hashlib.sha256(canonical).hexdigest() == envelope['original_report_sha256'],
        'original_privileged_scan_hash')
    result = envelope['reconciliation']
    cleared = result['cleared_reasons']
    require(len(cleared) == len(set(cleared)) and set(cleared) <= set(report['blocking_reasons']),
        'only_original_exact_reasons')
    for reason in cleared:
        require(reason.split(':', 1)[0] in transient.TRANSIENT_REASONS, 'transient_reason_only')
        decisions = [entry for entry in result['decisions'] if entry['reason'] == reason]
        require(len(decisions) == 1 and decisions[0]['cleared'] is True, 'one_actual_exit_decision')
        for key in ('first_observation', 'final_observation'):
            proof = decisions[0][key]
            require(proof['proven'] is True and proof['disposition'] == 'pidfd_exited_and_pid_absent'
                and proof['pidfd_pollin'] is True and proof['proc_lookup_errno'] == 2
                and proof['kernel_pidfd_open_errno'] == 3, 'two_kernel_exit_and_absence_proofs')
    remaining = [reason for reason in report['blocking_reasons'] if reason not in cleared]
    remaining.extend('transient_exit_sidecar:' + error for error in result['errors'])
    require(remaining == result['blocking_reasons'] and result['candidate_clear'] == (not remaining)
        and not (cleared and result['errors']), 'no_hidden_blocker_removal')
    report.update(clear=not remaining, blocking_reasons=remaining,
        transient_exit_evidence=envelope, admission_binding='MATH_PREINFERENCE_SINGLE_SCAN_V1',
        pidfd_capacity=dict(previous_soft=previous_limit[0], hard=previous_limit[1],
            required=required, own_process_soft_limit_temporarily_raised=changed,
            restored=True, max_pins=4096))
    return report


def scan(service):
    plan = life.plan_for(service)
    rank = life.hook.BRANCHES.index(plan['branch'])
    return fresh_scan(Path(plan['root']).parent, rank)


def fresh_scan(root, rank):
    life.previous.math.bind()
    return bind_scan(lambda: argv_admission.scan(rank, Path(root)/'SERVICE_IDENTITY.json'))


def configure():
    life.SERVICES, life.FINAL_ROOT, life.MODULE = SERVICES, FINALS, MODULE
    native.MODULE, native.scan, final.MODULE = MODULE, scan, MODULE


def session_open():
    session_path = os.environ['R118_PARALLEL_SESSION']
    session_sha = os.environ['R118_PARALLEL_SESSION_SHA256']
    session, control = life.hook.fresh_session(session_path, session_sha)
    require(not (control/'FAILED.json').exists() and time.time() < session['startup_deadline_unix'],
        'failed_or_expired_session_must_not_start')
    require(session_sha != 'e834ff7869f9309d70cf46f682adcc522f3120c8ac293ed7065708a6f50da94b',
        'failed_original_session_never_reused')


def inspect_previous(branch):
    service = PREVIOUS / ('lane' + str(life.hook.BRANCHES.index(branch)))
    require(branch in life.client.BRANCHES, 'math_branches_only')
    runtime = life.shared.read(service / 'RUNTIME.json')
    release = life.checked(runtime['release'])
    saved = life.checked(release['boundary'])
    plan = life.shared.read(service / 'PLAN.json')
    root = Path(plan['root'])
    guard = life.shared.read(service / 'GUARD_STARTED.json')['identity']
    terminal = life.shared.read(service / 'GUARD_TERMINAL.json')
    require(not life.alive(guard) and terminal['status'] == 'FAILED'
        and terminal['identity'] is None and terminal['native_alive'] is False
        and terminal['no_retry'] is True, 'actual_failed_preinference_guard_exit')
    for name in ('LAUNCH.json', 'MODEL_LOADED.json', 'NEW_GRADIENT_RNG.json', 'NATIVE.log'):
        require(not (service / name).exists(), 'native_dispatch_or_load_already_attempted')
    require(not (root / 'R118_PARALLEL_BOOTSTRAP.json').exists(), 'no_prior_bootstrap')
    life.boundary.unchanged(root, saved['preserved_files'])
    require(life.shared.read(root / 'COUNTERS.json') == saved['counters'], 'unchanged_charges')
    state = life.shared.read(Path(runtime['session']['shared_root']) / 'STATE.json')
    require(state['generation'] == 1 and state['checkpoint']['path_sha256'] == saved['checkpoint_sha256'],
        'same_committed_generation_one')
    campaign = life.checked(runtime['campaign'])
    campaign_root = Path(runtime['campaign']['path']).parent
    failure = life.ref(campaign_root / 'SESSION.dispatch' / 'FAILED.json')
    require(life.checked(failure)['retry_allowed'] is False, 'failed_session_no_retry')
    require(not (campaign_root / 'SESSION.dispatch' / 'GO.json').exists(), 'no_old_collection_GO')
    timer_records = [life.ref(service / 'CUTOFF_ARMED.json'),
        life.ref(Path(plan['final_root']) / 'SCHEDULED.json')]
    return dict(schema='R118_MATH_PREINFERENCE_EXIT_V1', status='GUARD_EXITED_NATIVE_NOT_STARTED',
        branch=branch, root=str(root), previous_service=str(service), previous_plan=life.ref(service/'PLAN.json'),
        previous_runtime=life.ref(service/'RUNTIME.json'), previous_release=runtime['release'],
        guard=guard, guard_terminal=life.ref(service/'GUARD_TERMINAL.json'),
        admission=life.ref(service/'ADMISSION.json'), failed_dispatch=failure,
        boundary=release['boundary'], counters=saved['counters'], next_cycle=saved['next_cycle'],
        preserved_files=saved['preserved_files'], checkpoint_sha256=saved['checkpoint_sha256'],
        old_timer_records=timer_records, previous_evaluation_plan=life.ref(Path(plan['final_root'])/'PLAN.json'),
        timer_custody='PENDING_NEW_SCOPED_AUTHORIZATION', signals=0, native_calls=0,
        old_session_deadline=campaign['deadline_unix'], observed_unix=time.time())


def owner(service):
    service = Path(service)
    plan = life.plan_for(service)
    saved = life.released(service)
    evidence = life.shared.read(service/'PREINFERENCE_EXIT.json')
    previous = Path(evidence['previous_service'])
    result = deepcopy(life.shared.read(previous/'FRESH_OWNER.json'))
    handoff = deepcopy(life.checked(result['handoff']))
    handoff.update(release=life.ref(service/'RELEASED.json'),
        predecessors=handoff['predecessors']+[life.boundary.minimal_identity(evidence['guard'])])
    target = service/'OWNER_HANDOFF.json'
    if target.exists():
        require(life.shared.read(target) == handoff, 'immutable_preinference_owner_handoff')
    else:
        life.shared.write(target, handoff)
    result.update(handoff=life.ref(target), cwd=str(life.SOURCE),
        command=[life.previous.math.PYTHON, '-B', '-m', MODULE, 'guard', '--service', str(service)],
        source_files={str(life.SOURCE/name):digest for name,digest in life.checked(plan['source_manifest']).items()},
        runtime_staged=(service/'RUNTIME.json').exists())
    result['env']['PYTHONPATH'] = str(life.SOURCE)
    require(handoff['next_cycle'] == saved['next_cycle'], 'unchanged_next_genuine_cycle')
    name = 'FRESH_OWNER.json' if result['runtime_staged'] else 'FRESH_OWNER_PREPARED.json'
    require(not (service/name).exists(), 'new_owner_output_only')
    life.shared.write(service/name, result)
    return life.ref(service/name)


def prepare(branch, manifest, tests):
    evidence = inspect_previous(branch)
    configure()
    service = life.service_for(branch)
    require(not service.exists(), 'new_preinference_service_only')
    life.verify_source(manifest, tests)
    plan = deepcopy(life.checked(evidence['previous_plan']))
    plan.update(service=str(service), source_root=str(life.SOURCE), source_manifest=manifest,
        tests_receipt=tests, final_root=str(FINALS/service.name),
        old_timer_records=evidence['old_timer_records'], old_evaluation_plan=evidence['previous_evaluation_plan'],
        preinference_previous_service=evidence['previous_service'],
        status='CPU_PREPARED_NOT_RELEASED_NOT_STAGED', prepared_unix=time.time())
    life.shared.write(service/'PLAN.json', plan)
    life.shared.write(service/'PREINFERENCE_EXIT.json', evidence)
    released = deepcopy(life.checked(evidence['previous_release']))
    released.update(service=str(service), predecessors=released['predecessors']+[evidence['guard']],
        authentic_guard_terminal=evidence['guard_terminal'], final_custody_pending=True,
        kind='PREINFERENCE_FAILURE_WITH_ORIGINAL_POSTCOMMIT_BOUNDARY',
        previous_release=evidence['previous_release'], preinference_evidence=life.ref(service/'PREINFERENCE_EXIT.json'),
        released_unix=time.time(), process_signals=0)
    life.shared.write(service/'RELEASED.json', released)
    return dict(plan=life.ref(service/'PLAN.json'), evidence=life.ref(service/'PREINFERENCE_EXIT.json'),
        owner=owner(service), release=life.ref(service/'RELEASED.json'),
        launch_authorized=False, timer_custody_pending=True, fresh_Main_session_required=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('phase', choices=('inspect', 'prepare', 'stage', 'scan', 'guard', 'resident', 'cutoff', 'schedule', 'native'))
    parser.add_argument('--branch', choices=('F2', 'A2'))
    parser.add_argument('--service', type=Path)
    parser.add_argument('--root', type=Path)
    parser.add_argument('--manifest', type=Path)
    parser.add_argument('--tests', type=Path)
    parser.add_argument('--authorization', type=Path)
    parser.add_argument('--campaign', type=Path)
    args = parser.parse_args()
    if args.phase == 'inspect':
        print(json.dumps(inspect_previous(args.branch)))
        return
    if args.phase == 'prepare':
        print(json.dumps(prepare(args.branch, life.ref(args.manifest), life.ref(args.tests))))
        return
    configure()
    if args.phase == 'stage':
        campaign = life.shared.read(args.campaign)
        evidence = life.shared.read(args.service/'PREINFERENCE_EXIT.json')
        failed_campaign = Path(evidence['failed_dispatch']['path']).parents[1]/'CAMPAIGN.json'
        require(args.campaign.resolve() != failed_campaign.resolve(), 'new_Main_campaign_required')
        runtime = life.stage(args.service, life.ref(args.authorization),
            Path(campaign['activation_directory']), life.ref(args.campaign))
        print(json.dumps(dict(runtime=runtime, owner=owner(args.service))))
        return
    if args.phase in ('guard', 'resident') and args.root is None:
        session_open()
    if args.root is not None:
        if args.phase == 'schedule':
            final.schedule(args.root)
        elif args.phase == 'native':
            final.original_functions()['native'](args.root)
        elif args.phase == 'scan':
            plan = final.validate(args.root)
            final.original.window(plan, time.time())
            print(json.dumps(fresh_scan(Path(plan['original_root']).parent, plan['physical'])))
        else:
            raise ValueError('unsupported_FINAL_phase')
    elif args.phase == 'scan':
        print(json.dumps(scan(args.service)))
    else:
        getattr(native, args.phase)(args.service)


if __name__ == '__main__':
    main()
