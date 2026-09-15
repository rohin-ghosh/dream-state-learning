"""Isolated GRID failed-startup recovery; preparation never starts a process."""

import argparse
from copy import deepcopy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import signal
import time


TERMINAL = 'R118_GRID_PARALLEL_RECOVERY_V1_TERMINAL.json'
ORIGINAL_TERMINAL = 'R118_GRID_PARALLEL_TERMINAL.json'
ORIGINAL_SOURCE_SHA = 'af71b0a51f2f9743eaa240b485741a2d208a6c335f6cc51ad64417070fa2efda'
FAILED_SESSION_SHA = 'e834ff7869f9309d70cf46f682adcc522f3120c8ac293ed7065708a6f50da94b'
CHECKPOINT_SHA = '43ce68acabb18f661ff929600239eb0a632981da841dd1182f886a85df78a02d'
SELECTOR_PID = 1519259


def require(value, reason):
    if not value:
        raise ValueError(reason)


def ref(path):
    path = Path(path)
    require(path.is_absolute() and not path.is_symlink(), 'absolute_nonsymlink_reference')
    return dict(path=str(path), sha256=hashlib.sha256(path.read_bytes()).hexdigest())


def read(reference):
    require(ref(reference['path']) == reference, 'exact_reference')
    return json.loads(Path(reference['path']).read_bytes())


def write(path, document):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x') as output:
        json.dump(document, output, sort_keys=True, indent=2)
        output.write('\n')
    return ref(path)


def verify_failed_start(plan, handoff):
    recovery = read(plan['failed_startup_recovery'])
    require(recovery['schema'] == 'R118_GRID_FAILED_STARTUP_RECOVERY_V1' and
            recovery['root'] == plan['root'] and recovery['branch'] == plan['branch'], 'own_recovery_binding')
    require(recovery['failed_session']['sha256'] == FAILED_SESSION_SHA, 'only_failed_e834ff_session')
    old_session = read(recovery['failed_session'])
    failure = read(recovery['failed_dispatch'])
    require(failure['session_sha256'] == FAILED_SESSION_SHA and failure['retry_allowed'] is False,
            'failed_session_not_retried')
    old_plan = read(recovery['old_plan'])
    require(old_plan['root'] == plan['root'] and old_plan['branch'] == plan['branch'] and
            plan['directory'] != old_plan['directory'] and plan['bounds'] == old_plan['bounds'] and
            plan['boundary'] == old_plan['boundary'], 'same_state_caps_new_execution_only')
    require(old_session['state']['generation'] == 1 and
            old_session['state']['checkpoint']['path_sha256'] == CHECKPOINT_SHA,
            'same_committed_gen1')
    root = Path(plan['root']).resolve(strict=True)
    require(Path(plan['directory']).resolve().is_relative_to(root) and
            Path(plan['directory']).name == 'parallel_recovery_1548', 'separate_owned_recovery_directory')
    require(recovery['old_terminal']['path'] == str(root / ORIGINAL_TERMINAL) and
            read(recovery['old_terminal'])['status'] == 'FAILED', 'preserve_actual_failed_terminal')
    proof = read(recovery['observation'])
    own = proof['branches'][plan['branch']]
    require(proof['session'] == recovery['failed_session'] and proof['GO_exists'] is False and
            own['new_generation_calls'] == own['optimizer_steps'] == 0 and
            not own['preserved_mismatches'] and not own['extra_call_or_parent_or_triple_files'],
            'failed_start_no_calls_or_optimizer')
    require(own['ledger_counts'] == {'NATIVE': 565 if plan['branch'] == 'F4' else 567, 'PARENT': 40},
            'exact_historical_charges')
    require(ref(root / 'LEDGER.jsonl') == own['ledger'] and ref(root / 'CARRY.json') == own['carry'],
            'no_new_charges_or_carry')
    for identity in recovery['predecessors']:
        require(identity['pid'] != SELECTOR_PID, 'never_selector')
        handoff.parallel.predecessor_released(identity)
    for relative, digest in recovery['preserved_files'].items():
        target = handoff.inside(root, relative)
        require(ref(target)['sha256'] == digest, 'failed_evidence_unchanged')
    for name in ('FRESH_BOOTSTRAP_RETURN.json', 'ENTRY.json'):
        require(not (Path(old_plan['directory']) / name).exists(), 'failed_start_never_collected')
    control = Path(recovery['failed_session']['path']).parent / 'SESSION.dispatch'
    require(not (control / 'GO.json').exists() and
            not (control / (plan['branch'] + '.BOOTSTRAP_START.json')).exists(), 'failed_start_never_bootstrapped')
    require(not Path(old_session['owners'][plan['branch']]['bootstrap_path']).exists(), 'no_old_bootstrap_reuse')
    return recovery


def validate_active_session(plan, handoff):
    session_path = os.environ.get('R118_PARALLEL_SESSION', '')
    session_sha = os.environ.get('R118_PARALLEL_SESSION_SHA256', '')
    require(session_sha and session_sha != FAILED_SESSION_SHA, 'new_Main_session_required')
    session, control = handoff.parallel.fresh_session(Path(session_path), session_sha)
    require(not (control / 'FAILED.json').exists() and time.time() < session['startup_deadline_unix'],
            'new_session_live_before_any_model_load')
    require(session['owners'][plan['branch']]['runtime_plan'] == ref(Path(plan['directory']) / 'PLAN.json'),
            'session_binds_exact_recovery_plan')
    return session


def timer_command(expected, old_plan_reference, command_bytes, environment):
    require(expected['pid'] != SELECTOR_PID and expected['uid'] == os.getuid(), 'own_timer_never_selector')
    command = [part.decode() for part in command_bytes.split(b'\0') if part]
    require(hashlib.sha256(command_bytes).hexdigest() == expected['command_sha256'] and
            command.count('--plan') == command.count('--sha256') == 1 and
            command[command.index('--plan') + 1] == old_plan_reference['path'] and
            command[command.index('--sha256') + 1] == old_plan_reference['sha256'] and
            'timer' in command and 'readout' not in command and
            any(Path(part).name == 'orch_r118_grid_parallel_run.py' for part in command),
            'exact_old_guard_timer_command')
    require(b'CUDA_VISIBLE_DEVICES=' in environment.split(b'\0'), 'CPU_timer_only')


def retire_previous_timer(plan, handoff):
    from gpu import orch_r118_grid_final_drain as process

    recovery = verify_failed_start(plan, handoff)
    validate_active_session(plan, handoff)
    expected = recovery['timer_identity']
    require(expected['pid'] != SELECTOR_PID, 'never_selector')
    previous = read(plan['previous_final_plan'])
    require(previous['branch_root'] == plan['root'] and
            not (Path(previous['output']) / 'DISPATCH.json').exists(), 'never_retire_dispatched_FINAL')
    try:
        actual = process.identity(expected['pid'])
    except FileNotFoundError:
        return [dict(identity=expected, already_exited=True)]
    if not process.same_process(actual, expected) or actual['state'] in ('Z', 'X'):
        return [dict(identity=expected, already_exited=True)]
    directory = Path('/proc') / str(expected['pid'])
    timer_command(expected, recovery['old_plan'], (directory / 'cmdline').read_bytes(),
                  (directory / 'environ').read_bytes())
    descriptor = os.pidfd_open(expected['pid'])
    try:
        require(process.same_process(process.identity(expected['pid']), expected), 'timer_PID_not_reused')
        process.send(descriptor, expected, signal.SIGTERM)
        for unused in range(100):
            if process.exited(descriptor):
                break
            time.sleep(.02)
        require(process.exited(descriptor), 'old_timer_did_not_retire')
    finally:
        os.close(descriptor)
    return [dict(identity=expected, already_exited=False)]


def configured_runner(plan):
    path = Path(__file__).resolve().with_name('orch_r118_grid_parallel_run.py')
    require(ref(path)['sha256'] == ORIGINAL_SOURCE_SHA, 'unchanged_original_runner')
    spec = importlib.util.spec_from_file_location('grid_failed_startup_private_runner', path)
    runner = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(runner)
    runner.__file__ = __file__
    runner.TERMINAL = TERMINAL
    original_validate = runner.validate

    def validate(current, handoff, *, released=True):
        verify_failed_start(current, handoff)
        validate_active_session(current, handoff)
        return original_validate(current, handoff, released=released)

    runner.validate = validate
    runner.retire_old_timers = retire_previous_timer
    return runner


def bind_campaign(prepared_reference, campaign_reference):
    prepared = read(prepared_reference)
    plan = deepcopy(prepared['plan'])
    require(plan['campaign'] is None, 'unbound_preparation_only')
    plan['campaign'] = campaign_reference
    runner = configured_runner(plan)
    handoff, unused = runner.modules(plan)
    verify_failed_start(plan, handoff)
    campaign, unused = handoff.parallel.campaign_document(campaign_reference['path'], campaign_reference['sha256'])
    require(campaign['root'] == plan['common_root'] and campaign['first_generation'] == 1 and
            time.time() < campaign['deadline_unix'] <= plan['bounds']['train_end_unix'], 'new_bounded_gen1_campaign')
    require(campaign_reference != read(prepared['recovery'])['old_campaign'], 'not_old_failed_campaign')
    owner = deepcopy(prepared['owner'])
    require(all(campaign['source_files'].get(path) == digest for path, digest in owner['source_files'].items()),
            'new_campaign_includes_frozen_recovery_sources')
    plan_reference = write(Path(plan['directory']) / 'PLAN.json', plan)
    owner.update(runtime_plan=plan_reference, runtime_staged=True, GPU_started=False,
                 command=[prepared['python'], '-B', str(Path(__file__).resolve()), 'guard', '--plan',
                          plan_reference['path'], '--sha256', plan_reference['sha256']])
    return write(Path(plan['directory']) / 'FRESH_OWNER_FINAL.json', owner)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode', choices=('guard', 'native', 'timer', 'bind'))
    parser.add_argument('--plan', type=Path)
    parser.add_argument('--sha256')
    parser.add_argument('--prepared', type=Path)
    parser.add_argument('--prepared-sha256')
    parser.add_argument('--campaign', type=Path)
    parser.add_argument('--campaign-sha256')
    args = parser.parse_args()
    if args.mode == 'bind':
        require(os.environ.get('CUDA_VISIBLE_DEVICES') == '', 'CPU_only_binding')
        require(all((args.prepared, args.prepared_sha256, args.campaign, args.campaign_sha256)), 'exact_binding_args')
        result = bind_campaign(dict(path=str(args.prepared), sha256=args.prepared_sha256),
                               dict(path=str(args.campaign), sha256=args.campaign_sha256))
        print(json.dumps(result))
        return
    require(args.plan and args.sha256, 'exact_plan_required')
    plan_reference = dict(path=str(args.plan), sha256=args.sha256)
    plan = read(plan_reference)
    runner = configured_runner(plan)
    handoff, loop = runner.modules(plan)
    if args.mode == 'guard':
        runner.guard(plan, handoff, loop, plan_reference)
    elif args.mode == 'native':
        runner.native(plan, handoff, loop)
    else:
        runner.timer(plan, handoff)


if __name__ == '__main__':
    main()
