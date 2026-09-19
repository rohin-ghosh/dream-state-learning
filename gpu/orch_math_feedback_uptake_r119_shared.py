"""Prospective shared math lease continuation; completed FINAL is never repeated."""

import argparse
from copy import deepcopy
import json
import os
from pathlib import Path
import subprocess
import sys
import time
from types import FunctionType, SimpleNamespace

from gpu import orch_math_feedback_uptake_r118_preinfer as prior
from gpu import orch_r119_lease_clock as lease_clock


life, require = prior.life, prior.require
shared, previous, client = life.shared, life.previous, life.client
MODULE = 'gpu.orch_math_feedback_uptake_r119_shared'
SOURCE = Path(__file__).resolve().parents[1]
SERVICES = Path('/localhome/local-rohing/orch_math_feedback_uptake_r119_shared_20260915_attempt1')
PREVIOUS = Path('/localhome/local-rohing/orch_math_feedback_uptake_r118_preinfer_20260915_attempt5')
FINALS = Path('/localhome/local-rohing/orch_math_feedback_uptake_r119_final_premodel_20260915_attempt1')
BACKEND_SHA = '33a30aa1793a053ca603a9c3e2c4e5fde477b35b99d858af87dfa980036a065c'
CLOCK = dict(path='/localhome/local-rohing/orch_r119_lease_continuation_20260915/CLOCK.json',
             sha256='a1aa51349c1784ec9f78e6411912576be43b55942c5fcdf1858ca391fd81c510')
ORIGINAL_BOUNDS = deepcopy(previous.ready.bounds())
ORIGINAL_ACTIVATION = previous.activation


def continuation_bounds(original, clock):
    result = deepcopy(original)
    result.update(native_end_unix=clock['train_end_unix'], hard_end_unix=clock['hard_end_unix'])
    require({key:value for key,value in result.items() if key not in ('native_end_unix','hard_end_unix')} ==
            {key:value for key,value in original.items() if key not in ('native_end_unix','hard_end_unix')}, 'only_clock_changes')
    return result


def completed_final(branch):
    root = FINALS / ('lane' + str(life.hook.BRANCHES.index(branch)))
    complete, terminal = shared.read(root/'COMPLETE.json'), shared.read(root/'TERMINAL.json')
    require(complete['native'] == terminal['completed_native'] == terminal['charged_native'] == 8
            and terminal['failed_or_partial_native'] == terminal['unattempted_native'] == 0,
            'original_FINAL_eight_complete')
    require(terminal['status'] == 'COMPLETE' and (root/'AFTER.json').exists(), 'original_FINAL_successful_release')
    launch = shared.read(root/'LAUNCH.json')
    identity = launch['identity']
    require(not life.alive(identity), 'original_FINAL_process_absent')
    return dict(complete=life.ref(root/'COMPLETE.json'), terminal=life.ref(root/'TERMINAL.json'),
                after=life.ref(root/'AFTER.json'), launch=life.ref(root/'LAUNCH.json'), repeat_allowed=False)


def configure():
    require(os.environ.get('ORCH_R119_LEASE_CLOCK') == CLOCK['path']
            and os.environ.get('ORCH_R119_LEASE_CLOCK_SHA256') == CLOCK['sha256'], 'explicit_Main_clock_environment')
    require(shared.sha(life.hook.__file__) == BACKEND_SHA, 'actual_Main_clock_backend')
    clock = lease_clock.validate(CLOCK, backend_path=life.hook.__file__)
    life.TRAIN_END = clock['train_end_unix']
    previous.math.NATIVE = clock['train_end_unix']
    previous.math.HARD = clock['hard_end_unix']
    life.SERVICES, life.SOURCE, life.MODULE = SERVICES, SOURCE, MODULE
    prior.native.SOURCE, prior.native.MODULE = SOURCE, MODULE
    prior.native.FINALIZED_HOOK_SHA256 = BACKEND_SHA
    life.unused_old_FINAL = lambda plan: completed_final(plan['branch'])
    return clock


def prepare(branch, manifest, tests):
    clock = configure()
    old_service = PREVIOUS/('lane'+str(life.hook.BRANCHES.index(branch)))
    old_owner = shared.read(old_service/'FRESH_OWNER.json')
    old_plan = shared.read(old_service/'PLAN.json')
    require(branch in client.BRANCHES and old_plan['root'] == str(client.BRANCHES[branch]), 'same_math_root')
    require(not (old_service/'GUARD_STARTED.json').exists(), 'attempt5_never_dispatched')
    release = shared.read(old_service/'RELEASED.json')
    saved = life.checked(release['boundary'])
    life.boundary.unchanged(Path(old_plan['root']), saved['preserved_files'])
    require(shared.read(Path(old_plan['root'])/'COUNTERS.json') == saved['counters'], 'no_counter_reset')
    final = completed_final(branch)
    session = client.prepare(previous.ready.COMMON_ROOT, branch)
    require(session['generation'] == 1 and session['checkpoint_sha256'] == saved['checkpoint_sha256'], 'same_genuine_gen1')
    service = life.service_for(branch)
    require(not service.exists(), 'new_lease_service_only')
    life.verify_source(manifest, tests)
    plan = deepcopy(old_plan)
    plan.update(service=str(service), source_root=str(SOURCE), source_manifest=manifest, tests_receipt=tests,
        final_root=str(service/'completed_final_custody'), inherited_bounds=continuation_bounds(ORIGINAL_BOUNDS, clock),
        train_end_unix=clock['train_end_unix'], lease_clock=CLOCK,
        previous_plan=life.ref(old_service/'PLAN.json'), completed_final=final, original_bounds=ORIGINAL_BOUNDS,
        prepared_unix=time.time(), old_timer_records=[], status='LEASE_CPU_PREPARED')
    shared.write(service/'PLAN.json', plan)
    release.update(service=str(service), previous_release=life.ref(old_service/'RELEASED.json'),
        final_custody_pending=False, completed_final=final, continuation_clock=CLOCK,
        retired_FINAL_timers=shared.read(old_service/'FINAL_TIMERS_RETIRED.json')['timers'])
    shared.write(service/'RELEASED.json', release)
    handoff = deepcopy(life.checked(old_owner['handoff']))
    handoff.update(release=life.ref(service/'RELEASED.json'), completed_final=final, lease_clock=CLOCK,
        original_handoff=old_owner['handoff'])
    handoff['bounds'].update(train_end_unix=clock['train_end_unix'], hard_end_unix=clock['hard_end_unix'])
    shared.write(service/'OWNER_HANDOFF.json', handoff)
    owner = deepcopy(old_owner)
    owner.update(handoff=life.ref(service/'OWNER_HANDOFF.json'), inherited_bounds=handoff['bounds'],
        command=[previous.math.PYTHON,'-B','-m',MODULE,'guard','--service',str(service)], cwd=str(SOURCE),
        source_files={str(SOURCE/name):digest for name,digest in life.checked(manifest).items()}, runtime_staged=False)
    owner['env'].update(PYTHONPATH=str(SOURCE), ORCH_R119_LEASE_CLOCK=CLOCK['path'],
        ORCH_R119_LEASE_CLOCK_SHA256=CLOCK['sha256'])
    shared.write(service/'OWNER_PREPARED.json', owner)
    return dict(branch=branch, plan=life.ref(service/'PLAN.json'), owner=life.ref(service/'OWNER_PREPARED.json'),
                release=life.ref(service/'RELEASED.json'), next_cycle=saved['next_cycle'], counters=saved['counters'])


def stage(service, authorization, campaign):
    configure()
    plan = life.plan_for(service)
    permission = life.authorization(authorization, plan, 'LAUNCH')
    require(permission['all_eight_released'], 'Main_common_handoff')
    saved = life.released(service)
    session = client.prepare(previous.ready.COMMON_ROOT, plan['branch'])
    require(session['checkpoint_sha256'] == saved['checkpoint_sha256'] == permission['checkpoint_sha256'], 'same_checkpoint')
    document, unused = life.hook.campaign_document(campaign['path'], campaign['sha256'])
    require(document['activation_directory'] == permission['activation_directory']
            and document['deadline_unix'] <= life.TRAIN_END, 'Main_campaign_and_wall')
    runtime = dict(schema='R118_MATH_FRESH_EXEC_RUNTIME_V1', plan=life.ref(service/'PLAN.json'),
        release=life.ref(service/'RELEASED.json'), authorization=authorization, session=session,
        next_cycle=saved['next_cycle'], carry=saved['carry'], inherited_bounds=plan['inherited_bounds'],
        activation_directory=permission['activation_directory'], campaign=campaign, train_end_unix=life.TRAIN_END,
        bootstrap_path=str(Path(plan['root'])/'R118_PARALLEL_BOOTSTRAP.json'), local_optimizer_steps=0,
        lease_clock=CLOCK, completed_final=plan['completed_final'])
    shared.write(service/'RUNTIME.json', runtime)
    shared.write(Path(plan['final_root'])/'PLAN.json', dict(branch=plan['branch'], original_completed=plan['completed_final'],
        never_dispatch=True, clock=CLOCK, custody='CPU_QUOTA_GUARD_ONLY_NOT_EVALUATOR'))
    owner = shared.read(service/'OWNER_PREPARED.json')
    owner['runtime_staged'] = True
    shared.write(service/'FRESH_OWNER.json', owner)
    return dict(owner=life.ref(service/'FRESH_OWNER.json'), runtime=life.ref(service/'RUNTIME.json'))


def activation(root, document=None):
    receipt = shared.read(Path(root)/'SHARED_CLIENT_READY.json')
    old_math = SimpleNamespace(**dict(vars(previous.math), NATIVE=ORIGINAL_BOUNDS['native_end_unix'],
                                    HARD=ORIGINAL_BOUNDS['hard_end_unix']))
    predecessor = FunctionType(previous.ready.predecessor.__code__,
        dict(previous.ready.predecessor.__globals__, math=old_math), 'original_predecessor',
        previous.ready.predecessor.__defaults__)
    namespace = dict(ORIGINAL_ACTIVATION.__globals__, SOURCE=Path(receipt['successor_source']),
        ready=SimpleNamespace(**dict(vars(previous.ready), bounds=lambda: ORIGINAL_BOUNDS, predecessor=predecessor)))
    return FunctionType(ORIGINAL_ACTIVATION.__code__, namespace, 'original_activation',
        ORIGINAL_ACTIVATION.__defaults__)(root, document)


def readout(root, binding):
    configure()
    require(shared.read(binding)['stage'] == 'cycle', 'completed_FINAL_never_repeat')
    namespace = dict(previous.readout.__globals__, activation=activation)
    FunctionType(previous.readout.__code__, namespace, 'readout', previous.readout.__defaults__)(root, binding)


def dispatch_readout(root, session, cycle):
    binding = Path(root)/'shared_readout_bindings'/f'cycle_{cycle:03d}.json'
    shared.write(binding, dict(session=deepcopy(session), stage='cycle', cycle=cycle,
        resident_process=client.native.process_identity(), parent_free=True, never_rows_or_buffer=True,
        lease_clock=CLOCK, evaluator_source_sha256=shared.sha(previous.__file__)))
    with binding.with_suffix('.log').open('x') as log:
        child = subprocess.Popen([sys.executable,'-B','-m',MODULE,'readout','--root',str(root),'--binding',str(binding)],
            cwd=SOURCE, stdin=subprocess.DEVNULL, stdout=log, stderr=subprocess.STDOUT,
            env=dict(os.environ, PYTHONPATH=str(SOURCE), PYTHONDONTWRITEBYTECODE='1'))
        identity = previous.math.common.process_identity(Path('/proc',str(child.pid)))
        shared.write(binding.with_suffix('.process.json'), identity)
        try:
            require(child.wait(timeout=max(.01,previous.math.NATIVE-time.time())) == 0, 'fresh_DEV_failure_no_retry')
        finally:
            if child.poll() is None:
                previous.math.common.stop_owned(child, identity)


def finalcustody(service):
    configure()
    plan = life.plan_for(service)
    completed_final(plan['branch'])
    shared.write(Path(plan['final_root'])/'SCHEDULED.json', dict(identity=life.identity(os.getpid()),
        runtime=life.ref(service/'RUNTIME.json'), completed_final=plan['completed_final'],
        never_dispatch=True, purpose='ORIGINAL_FINAL_QUOTA_CUSTODY_ONLY'))
    while time.time() < previous.math.HARD and not (service/'GUARD_TERMINAL.json').exists():
        time.sleep(2)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('phase', choices=('prepare','stage','guard','resident','scan','cutoff','finalcustody','readout'))
    parser.add_argument('--branch', choices=('F2','A2'))
    for name in ('service','manifest','tests','authorization','campaign','root','binding'):
        parser.add_argument('--'+name,type=Path)
    arguments = parser.parse_args()
    configure()
    if arguments.phase == 'prepare':
        print(json.dumps(prepare(arguments.branch,life.ref(arguments.manifest),life.ref(arguments.tests))))
    elif arguments.phase == 'stage':
        print(json.dumps(stage(arguments.service,life.ref(arguments.authorization),life.ref(arguments.campaign))))
    elif arguments.phase == 'readout':
        readout(arguments.root, arguments.binding)
    elif arguments.phase == 'finalcustody':
        finalcustody(arguments.service)
    elif arguments.phase == 'scan':
        print(json.dumps(prior.scan(arguments.service)))
    else:
        from gpu import orch_math_feedback_uptake_r119_shared_native as native
        native.MODULE, native.SOURCE = MODULE, SOURCE
        native.FINALIZED_HOOK_SHA256 = BACKEND_SHA
        native.scan = prior.scan
        native.loop.dispatch_readout = dispatch_readout
        if arguments.phase in ('guard','resident'):
            prior.session_open()
        getattr(native, arguments.phase)(arguments.service)


if __name__ == '__main__':
    main()
