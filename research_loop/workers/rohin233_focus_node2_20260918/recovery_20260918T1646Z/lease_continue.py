"""Authorized exact-owner completed-sleep continuation on node2 only."""

import argparse
from copy import deepcopy
import json
import os
from pathlib import Path
import shutil
import signal
import subprocess
import sys
import time

import recover
from c0_lease_parent import HORIZON
from observe import checked, header, observation, utc
from recover import HERE, LEASE_SOURCE, LEASE_SHA, PYTHON, TARGETS, environment, read, require, sha, write


NAMES = ('C0', 'ASTRA7')


def paths(name):
    require(name in NAMES, 'only_C0_and_Astra7_not_caption')
    root = Path(TARGETS[name][0])
    return root, root / 'source_r233_lease_continuation', root / 'control_r233_lease_continuation'


def records(root):
    return sorted((root / 'raw/stream/records').glob('[0-9]' * 20 + '.json'))


def latest_complete(root):
    for path in reversed(records(root)):
        if header(path)['kind'] == 'SLEEP_COMPLETE':
            result = checked(path)
            require(result['document']['status'] == 'COMPLETE', 'actual_completed_sleep')
            return result
    raise ValueError('no_completed_sleep')


def at_boundary(head, complete):
    return (complete['kind'] == 'SLEEP_COMPLETE'
        and head['journal_id'] == complete['journal_id']
        and ((head['kind'] == 'SLEEP_COMPLETE' and head['index'] == complete['index'])
            or (head['kind'] == 'R184_LEARN_COMPLETE' and head['index'] == complete['index'] + 1)))


def exact_owner(root, owner):
    process = Path('/proc', str(owner['pid']))
    fields = (process / 'stat').read_text().rsplit(')', 1)[1].split()
    arguments = (process / 'cmdline').read_bytes().split(b'\0')
    require(int(fields[19]) == owner['start_ticks'] and process.stat().st_uid == owner['uid'] == 2524
        and fields[0] not in ('T', 'Z', 'X') and b'native' in arguments
        and str(root / 'control_r233_recovery/GUARD.json').encode() in arguments,
        'exact_owned_recovery_native_no_pid_reuse')
    return process


def bind_plan(previous, complete, source, authority):
    plan = deepcopy(previous)
    saved = complete['document']['resume_state']
    plan.update(source_root=str(source), hard_end_unix=HORIZON, lease_end_unix=authority['lease_end_unix'])
    if 'startup_context' in plan:
        plan['startup_context']['path'] = str(source / Path(previous['startup_context']['path']).relative_to(previous['source_root']))
    plan.pop('preupdate_recovery', None)
    from gpu.orch_r125_stream_journal import WALL_EXTENSION_SCHEMA
    plan['authorized_wall_extension'] = dict(schema=WALL_EXTENSION_SCHEMA,
        previous_stream_sha256=saved['sha256'], previous_deadline_unix=saved['state']['deadline_unix'],
        new_deadline_unix=HORIZON, lease_end_unix=authority['lease_end_unix'], safety_margin_seconds=21600)
    return plan


def verify_candidate(root, source, complete, plan):
    from gpu.orch_r125_continual_native import NativeChild, prepare_wall_extension
    from organism_v6.orch_r125_continual_stream import ContinualStream
    checkpoint = deepcopy(complete['document']['checkpoint'])
    directory = root / 'raw/checkpoints' / f'sleep_{complete["document"]["cycle"]:06d}'
    require(read(directory / 'COMMIT.json') == checkpoint, 'completed_COMMIT_matches_journal')
    checkpoint.update(adapter_path=str(directory / 'adapter'), optimizer_rng_path=str(directory / 'optimizer_rng.pt'))
    NativeChild.verify_checkpoint(checkpoint)
    saved = complete['document']['resume_state']
    stream = ContinualStream.restore(saved, expected_sha256=saved['sha256'])
    extension = prepare_wall_extension(plan, stream, resume=True, plan_sha256='0' * 64)
    return dict(cycle=complete['document']['cycle'], optimizer_steps=checkpoint['optimizer_steps'],
        record_index=complete['index'], record_sha256=complete['sha256'], state_sha256=saved['sha256'],
        checkpoint_commit_sha256=sha(directory / 'COMMIT.json'), checkpoint_sha256=checkpoint['checkpoint_sha256'],
        extended_state_sha256=extension['state']['sha256'], checkpoint_path=str(directory))


def prepare(name, finish=False):
    os.environ['CUDA_VISIBLE_DEVICES'] = ''
    root, source, control = paths(name)
    require((source.is_dir() and control.is_dir() and not list(control.iterdir())) if finish
        else not source.exists() and not control.exists(), 'one_new_continuation_attempt')
    require(sha(LEASE_SOURCE) == LEASE_SHA, 'authoritative_existing_lease')
    authority = read(LEASE_SOURCE)
    require(time.time() < HORIZON <= authority['hard_deadline_unix'], 'authorized_conservative_horizon')
    observed = observation(name)
    require(observed['status'] == 'LOADED', 'existing_native_stays_alive_during_preparation')
    exact_owner(root, observed['native'])
    if not finish:
        control.mkdir(mode=0o700)
        shutil.copytree(root / 'source_r233_recovery', source)
        shutil.copy2(HERE / 'runtime.py', source / 'gpu/r233_node2_recovery.py')
        shutil.copy2(HERE / 'test_recovery.py', source / 'tests/test_r233_node2_recovery.py')
    sys.path.insert(0, str(source))
    complete = latest_complete(root)
    plan = bind_plan(read(root / 'control_r233_recovery/PLAN.json'), complete, source, authority)
    candidate = verify_candidate(root, source, complete, plan)
    write(control / 'CANDIDATE_CPU.json', candidate)
    write(control / 'OLD_IDENTITY.json', observed['native'])
    tests = ['test_r233_node2_recovery', 'test_orch_r227_learning_policy',
        'test_orch_r125_continual_native', 'test_orch_r184_think_act_learn']
    with (control / 'CPU.log').open('x') as output:
        result = subprocess.run([PYTHON, '-B', '-m', 'unittest', '-q', *tests], cwd=source,
            env=environment(source), stdout=output, stderr=subprocess.STDOUT, timeout=240)
    require(result.returncode == 0, 'receiving_CPU_suite')
    pins = {str(path.relative_to(source)): sha(path) for path in source.rglob('*.py')}
    write(control / 'RECEIVING_CPU.json', dict(passed=True, tests=tests, source_pins=pins,
        log_sha256=sha(control / 'CPU.log'), candidate=candidate, latest_boundary_reselected_at_handoff=True,
        native_signals=0, new_horizon_utc=utc(HORIZON), lease_source_sha256=LEASE_SHA))
    print(json.dumps(dict(arm=name, status='CPU_PASS_OLD_NATIVE_UNCHANGED', candidate=candidate)), flush=True)


def continue_at_boundary(name, commit):
    root, source, control = paths(name)
    require(not (control / 'HANDOFF_REQUESTED.json').exists(), 'no_duplicate_controller')
    cpu, owner = read(control / 'RECEIVING_CPU.json'), read(control / 'OLD_IDENTITY.json')
    require(cpu['passed'] and len(commit) == 40, 'pushed_tested_builder_gate')
    require(sha(LEASE_SOURCE) == LEASE_SHA and time.time() < HORIZON
        <= read(LEASE_SOURCE)['hard_deadline_unix'], 'same_authorized_existing_lease')
    exact_owner(root, owner)
    if name == 'C0':
        parent_directory = HERE / 'C0_CURRICULUM_LEASE'
        service = read(parent_directory / 'SERVICE.json')
        process = Path('/proc', str(service['pid']))
        fields = (process / 'stat').read_text().rsplit(')', 1)[1].split()
        require(int(fields[19]) == service['start_ticks'] and b'c0_lease_parent.py' in (process / 'cmdline').read_bytes(),
            'exact_sole_CPU_publisher_handoff')
        write(parent_directory / 'CANCEL_CURRICULUM_SERVICE', dict(reason='Authorized checkpoint continuation; ledger preserved'))
        deadline = time.time() + 30
        while not (parent_directory / 'EXIT.json').exists():
            require(time.time() < deadline, 'CPU_parent_handoff_timeout_no_learner_signal')
            time.sleep(0.2)
        shutil.copytree(parent_directory, control / 'parent_ledger.private')
    write(control / 'HANDOFF_REQUESTED.json', dict(requested_utc=utc(time.time()), old_owner=owner,
        builder_commit=commit, no_SIGSTOP=True, no_idle_hold=True))
    sys.path.insert(0, str(source))
    while time.time() < HORIZON:
        exact_owner(root, owner)
        available = records(root)
        head = header(available[-1])
        if head['kind'] not in ('SLEEP_COMPLETE', 'R184_LEARN_COMPLETE'):
            time.sleep(0.2)
            continue
        complete = checked(available[-1] if head['kind'] == 'SLEEP_COMPLETE' else available[-2])
        if not at_boundary(head, complete):
            time.sleep(0.2)
            continue
        require(complete['document']['status'] == 'COMPLETE', 'completed_sleep_before_signal')
        exact_owner(root, owner)
        signaled = time.time()
        os.kill(owner['pid'], signal.SIGTERM)
        break
    else:
        raise ValueError('no_remaining_authorized_lease')
    while Path('/proc', str(owner['pid'])).exists():
        require(time.time() - signaled < 60, 'old_native_exit_timeout_no_duplicate_start')
        time.sleep(0.05)
    stopped = time.time()
    final_complete = latest_complete(root)
    require(final_complete['index'] >= complete['index'], 'latest_complete_never_older')
    complete = final_complete
    authority = read(LEASE_SOURCE)
    plan = bind_plan(read(root / 'control_r233_recovery/PLAN.json'), complete, source, authority)
    candidate = verify_candidate(root, source, complete, plan)
    preserved = control / 'preserved.private'
    preserved.mkdir(mode=0o700)
    subprocess.run(['cp', '-a', '--reflink=auto', candidate['checkpoint_path'], str(preserved)], check=True)
    shutil.copy2(root / 'raw/stream/records' / f'{complete["index"]:020d}.json', preserved / 'SLEEP_COMPLETE.json')
    head = header(records(root)[-1])
    require(at_boundary(head, complete), 'raced_awake_tail_preserved_needs_supported_reconciliation')
    write(control / 'RECOVERY.json', dict(complete_cycle=candidate['cycle'], saved_state_sha256=candidate['state_sha256'],
        old_outer_exit=dict(finished_unix=stopped), candidate=candidate, preserved_state=True,
        native_term_utc=utc(signaled), old_native_absent_utc=utc(stopped), boundary_head=head,
        no_SIGSTOP=True, no_idle_hold=True, old_owner=owner))
    write(control / 'PLAN.json', plan)
    write(control / 'LEASE.json', dict(lease_end_unix=authority['lease_end_unix'], hard_end_unix=HORIZON,
        authoritative_source_sha256=LEASE_SHA, physical_lease_changed=False))
    write(control / 'ALLOCATION.json', dict(plan_sha256=sha(control / 'PLAN.json'), cpu_tests_passed=True,
        gpu_uuid=plan['gpu_uuid'], physical=plan['physical'], builder_entry_logged=True, builder_entry_pushed=True,
        builder_entry_commit=commit, cpu_receipt_path=str(control / 'RECEIVING_CPU.json'),
        cpu_receipt_sha256=sha(control / 'RECEIVING_CPU.json'), declared_unix=time.time()))
    guard = read(root / 'control_r233_recovery/GUARD.json')
    guard.update(source_pins=cpu['source_pins'], attempt_dir=str(control), plan_path=str(control / 'PLAN.json'),
        plan_sha256=sha(control / 'PLAN.json'), hard_end_unix=HORIZON, lease_path=str(control / 'LEASE.json'),
        lease_sha256=sha(control / 'LEASE.json'), allocation_path=str(control / 'ALLOCATION.json'),
        allocation_sha256=sha(control / 'ALLOCATION.json'), next_reserved_unix=authority['hard_deadline_unix'])
    write(control / 'GUARD.json', guard)
    subprocess.run([PYTHON, '-B', '-c', 'from gpu.orch_r125_continual_guard import validate; import sys; validate(sys.argv[1])',
        str(control / 'GUARD.json')], cwd=source, env=environment(source), check=True)
    write(control / 'DISPATCHED.json', dict(dispatched_utc=utc(time.time()), candidate=candidate,
        old_native_absent_unix=stopped, status='DISPATCHED_NOT_LOADED'))
    os.chdir(source)
    os.execve(PYTHON, [PYTHON, '-B', '-m', 'gpu.r233_node2_recovery', 'dispatch',
        '--config', str(control / 'GUARD.json')], environment(source))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('mode', choices=('prepare', 'finish-prepare', 'continue'))
    parser.add_argument('name', choices=NAMES)
    parser.add_argument('--commit')
    arguments = parser.parse_args()
    if arguments.mode == 'continue':
        continue_at_boundary(arguments.name, arguments.commit)
    else:
        prepare(arguments.name, finish=arguments.mode == 'finish-prepare')
