"""CPU preparation after the second failed session; no historical replay."""

from copy import deepcopy
import os
from pathlib import Path
import time

from gpu import orch_math_feedback_uptake_r118_preinfer as prior

life = prior.life
require = life.require
MODULE = 'gpu.orch_math_feedback_uptake_r118_second_exit'
SERVICES = Path('/localhome/local-rohing/orch_math_feedback_uptake_r118_preinfer_20260915_attempt5')
FINALS = Path('/localhome/local-rohing/orch_math_feedback_uptake_r118_preinfer_final_20260915_attempt5')
PREVIOUS = prior.SERVICES
FAILED_SESSION = '2987f2cba47868934fd6d465f0001c94e7d754d3b7972bb56c328ed6f081e641'
original_session_open = prior.session_open


def validate_exit(guard, launch, terminal, failure, log, absent, counters, expected):
    require(launch['guardian']['pid'] == guard['pid']
        and launch['guardian']['start_ticks'] == guard['start_ticks']
        and launch['guardian']['boot_id'] == guard['boot_id'], 'same_actual_guard')
    require(terminal['status'] == 'FAILED' and terminal['native_alive'] is False
        and terminal['no_retry'] is True and terminal['identity'] == launch['identity'],
        'authentic_failed_spawned_child_terminal')
    require(absent is True, 'both_original_actors_absent')
    require(failure['session_sha256'] == FAILED_SESSION and failure['retry_allowed'] is False,
        'exact_second_failed_session')
    require(log.rstrip().endswith('ValueError: failed_or_expired_session_must_not_start'),
        'exact_prebootstrap_session_rejection')
    require(counters == expected, 'unchanged_charges')


def inspect_previous(branch):
    require(branch in life.client.BRANCHES, 'math_branches_only')
    service = PREVIOUS / ('lane' + str(life.hook.BRANCHES.index(branch)))
    runtime = life.shared.read(service/'RUNTIME.json')
    release = life.checked(runtime['release'])
    saved = life.checked(release['boundary'])
    plan = life.shared.read(service/'PLAN.json')
    root = Path(plan['root'])
    guard = life.shared.read(service/'GUARD_STARTED.json')['identity']
    launch = life.shared.read(service/'LAUNCH.json')
    terminal = life.shared.read(service/'GUARD_TERMINAL.json')
    campaign_root = Path(runtime['campaign']['path']).parent
    failure = life.ref(campaign_root/'SESSION.dispatch'/'FAILED.json')
    absent = all(not Path('/proc', str(actor['pid'])).exists()
        for actor in (guard, launch['identity']))
    validate_exit(guard, launch, terminal, life.checked(failure),
        (service/'NATIVE.log').read_text(), absent,
        life.shared.read(root/'COUNTERS.json'), saved['counters'])
    for path in (service/'MODEL_LOADED.json', service/'NEW_GRADIENT_RNG.json',
            root/'R118_PARALLEL_BOOTSTRAP.json', campaign_root/'SESSION.dispatch'/'GO.json'):
        require(not path.exists(), 'no_bootstrap_model_rng_or_GO')
    life.boundary.unchanged(root, saved['preserved_files'])
    state = life.shared.read(Path(runtime['session']['shared_root'])/'STATE.json')
    require(state['generation'] == 1 and state['checkpoint']['path_sha256'] == saved['checkpoint_sha256']
        and state['optimizer_steps'] == 3009 and state['shared_optimizer_steps'] == 1884,
        'unchanged_committed_generation_one')
    return dict(schema='R118_MATH_PREINFERENCE_EXIT_V2', status='CPU_CHILD_EXITED_BEFORE_MODEL_BOOTSTRAP',
        branch=branch, root=str(root), previous_service=str(service), previous_plan=life.ref(service/'PLAN.json'),
        previous_runtime=life.ref(service/'RUNTIME.json'), previous_release=runtime['release'],
        guard=guard, native=launch['identity'], guard_terminal=life.ref(service/'GUARD_TERMINAL.json'),
        launch=life.ref(service/'LAUNCH.json'), native_log=life.ref(service/'NATIVE.log'),
        admission=life.ref(service/'ADMISSION.json'), failed_dispatch=failure,
        prior_failure=life.ref(service/'PREINFERENCE_EXIT.json'), boundary=release['boundary'],
        counters=saved['counters'], next_cycle=saved['next_cycle'], preserved_files=saved['preserved_files'],
        checkpoint_sha256=saved['checkpoint_sha256'],
        old_timer_records=[life.ref(service/'CUTOFF_ARMED.json'),
            life.ref(Path(plan['final_root'])/'SCHEDULED.json')],
        previous_evaluation_plan=life.ref(Path(plan['final_root'])/'PLAN.json'),
        timer_custody='PENDING_NEW_SCOPED_AUTHORIZATION', signals=0, native_calls=0,
        old_session_deadline=life.checked(runtime['campaign'])['deadline_unix'], observed_unix=time.time())


def owner(service):
    service = Path(service)
    plan, saved = life.plan_for(service), life.released(service)
    evidence = life.shared.read(service/'PREINFERENCE_EXIT.json')
    result = deepcopy(life.shared.read(Path(evidence['previous_service'])/'FRESH_OWNER.json'))
    handoff = deepcopy(life.checked(result['handoff']))
    handoff.update(release=life.ref(service/'RELEASED.json'),
        predecessors=handoff['predecessors'] + [life.boundary.minimal_identity(evidence[key])
            for key in ('guard', 'native')])
    target = service/'OWNER_HANDOFF.json'
    if target.exists():
        require(life.shared.read(target) == handoff, 'immutable_second_exit_handoff')
    else:
        life.shared.write(target, handoff)
    result.update(handoff=life.ref(target), cwd=str(life.SOURCE),
        command=[life.previous.math.PYTHON, '-B', '-m', MODULE, 'guard', '--service', str(service)],
        source_files={str(life.SOURCE/name):digest for name,digest in life.checked(plan['source_manifest']).items()},
        runtime_staged=(service/'RUNTIME.json').exists())
    result['env']['PYTHONPATH'] = str(life.SOURCE)
    require(handoff['next_cycle'] == saved['next_cycle'], 'unchanged_next_genuine_cycle')
    target = service/('FRESH_OWNER.json' if result['runtime_staged'] else 'FRESH_OWNER_PREPARED.json')
    require(not target.exists(), 'new_owner_output_only')
    life.shared.write(target, result)
    return life.ref(target)


def prepare(branch, manifest, tests):
    evidence = inspect_previous(branch)
    prior.configure()
    service = life.service_for(branch)
    require(not service.exists(), 'new_second_exit_service_only')
    life.verify_source(manifest, tests)
    plan = deepcopy(life.checked(evidence['previous_plan']))
    plan.update(service=str(service), source_root=str(life.SOURCE), source_manifest=manifest,
        tests_receipt=tests, final_root=str(FINALS/service.name), old_timer_records=evidence['old_timer_records'],
        old_evaluation_plan=evidence['previous_evaluation_plan'],
        preinference_previous_service=evidence['previous_service'],
        status='CPU_PREPARED_NOT_STAGED', prepared_unix=time.time())
    life.shared.write(service/'PLAN.json', plan)
    life.shared.write(service/'PREINFERENCE_EXIT.json', evidence)
    released = deepcopy(life.checked(evidence['previous_release']))
    released.update(service=str(service), predecessors=released['predecessors']+
        [evidence['guard'], evidence['native']], authentic_guard_terminal=evidence['guard_terminal'],
        final_custody_pending=True, kind='SECOND_SESSION_EXIT_BEFORE_BOOTSTRAP',
        previous_release=evidence['previous_release'], preinference_evidence=life.ref(service/'PREINFERENCE_EXIT.json'),
        released_unix=time.time(), process_signals=0)
    life.shared.write(service/'RELEASED.json', released)
    return dict(plan=life.ref(service/'PLAN.json'), evidence=life.ref(service/'PREINFERENCE_EXIT.json'),
        owner=owner(service), release=life.ref(service/'RELEASED.json'), launch_authorized=False,
        timer_custody_pending=True, fresh_Main_session_required=True)


def session_open():
    require(os.environ['R118_PARALLEL_SESSION_SHA256'] != FAILED_SESSION,
        'second_failed_session_never_reused')
    original_session_open()


def main():
    prior.MODULE, prior.SERVICES, prior.FINALS = MODULE, SERVICES, FINALS
    prior.inspect_previous, prior.prepare, prior.owner = inspect_previous, prepare, owner
    prior.session_open = session_open
    prior.main()


if __name__ == '__main__':
    main()
