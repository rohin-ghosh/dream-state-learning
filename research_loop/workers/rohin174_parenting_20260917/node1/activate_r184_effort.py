"""Exact quiet-parent takeover only; never reserve away a fresh child response."""

import argparse
import fcntl
import importlib.util
import json
import os
from pathlib import Path
import select
import signal
import subprocess
import sys
import time

from inventory_node1 import HERE, Reader, digest, identity, require, unchanged
from parent_custody import transport_children, write
from r184_effort_parent import POLICY


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--activation', type=Path, required=True)
    arguments = parser.parse_args()
    previous = arguments.activation.resolve()
    require(previous.parent == HERE, 'owned_activation_directory')
    old_path = previous / 'SPEC.json'
    old_spec = json.loads(Reader().raw(old_path))
    activation = json.loads(Reader().raw(previous / 'PARENT_ACTIVATED.json'))
    expected = activation['actor']
    labels = dict(teach_replay=2, teach_perception=3, teach_parenting=4,
                  classroom_brain=5, classroom_creative=6, classroom_support=7)
    physical = old_spec.get('physical', labels.get(activation.get('label')))
    require(physical in range(8) and expected['uid'] == os.getuid(), 'eight_owned_parent_operators')
    require(old_spec['root'] == activation['root'], 'same_actual_parented_root')
    require(expected['argv'][2] == str(HERE / ('frozen_forward_parent.py' if physical < 2 else 'forward_parent.py'))
            and expected['argv'][3:] == ['--spec', str(old_path)], 'exact_existing_parent_command')
    require(not (previous / 'SUPERSEDED.json').exists() and not (previous / 'PARENT_WITHDRAWAL.json').exists(),
            'no_supersession_or_withdrawal_override')
    name = ('lane' + str(physical) + '_activation_' if physical >= 2 else 'frozen' + str(physical) + '_parenting_')
    directory = HERE / (name + 'r184_effort_' + str(time.time_ns()))
    directory.mkdir(mode=0o700)
    lock = os.open(previous / 'R184_PARENT_TAKEOVER.lock', os.O_CREAT | os.O_WRONLY | os.O_NOFOLLOW, 0o600)
    descriptor = os.pidfd_open(expected['pid'])
    stopped, retired = False, False
    try:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        deadline = time.monotonic() + 120
        while True:
            current = identity(Path('/proc') / str(expected['pid']))
            require(unchanged(expected, current) and current['state'] not in ('T', 't', 'Z', 'X'), 'live_unpaused_parent_owner')
            signal.pidfd_send_signal(descriptor, signal.SIGSTOP)
            stopped = True
            for unused in range(100):
                if identity(Path('/proc') / str(expected['pid']))['state'] in ('T', 't'):
                    break
                time.sleep(.01)
            require(identity(Path('/proc') / str(expected['pid']))['state'] in ('T', 't'), 'actual_parent_pause')
            attempts = sorted(path for path in (previous / 'parent').glob('parent_*') if path.is_dir())
            if all((path / 'RESULT.json').exists() for path in attempts) and not transport_children(expected['pid']):
                break
            signal.pidfd_send_signal(descriptor, signal.SIGCONT)
            stopped = False
            require(time.monotonic() < deadline, 'busy_parent_left_running')
            time.sleep(.5)
        results = [json.loads(Reader().raw(path / 'RESULT.json')) for path in attempts]
        require(not list((previous / 'parent').glob('parent_*/PUBLICATION_UNKNOWN.json')), 'unknown_publication_no_retry')
        require(all(result['status'] in ('PUBLISHED', 'MISSING', 'SILENT') and
                    (result['status'] == 'PUBLISHED' or 'sent_unix' not in result) for result in results), 'settled_parent_ledger')
        cursor = max([old_spec['reserved_response_count']] + [result['source_response_count'] for result in results])
        config = json.loads(Reader().raw(old_spec['config']))
        first_cadence = config['cadence_responses'] if results else 1
        spec = dict(old_spec, physical=physical, output=str(directory / 'parent'), predecessor_spec=str(old_path),
                    reserved_response_count=cursor, r184_first_cadence=first_cadence,
                    r184_effort_policy=POLICY, pins=dict(old_spec['pins']))
        for source in (HERE / 'r184_effort_parent.py', Path(__file__)):
            spec['pins'][str(source)] = digest(Reader().raw(source))
        write(directory / 'SPEC.json', spec)
        write(directory / 'PRESERVED_LEDGER.json', dict(attempts=[str(path) for path in attempts], results=results,
              cursor=cursor, first_due_response=cursor + first_cadence, original_inbox_unchanged=True,
              common_baseline_resent=False, child_signals=0, observed_unix=time.time()))
        command = [sys.executable, '-B', str(HERE / 'r184_effort_parent.py'), '--spec', str(directory / 'SPEC.json')]
        environment = dict(os.environ, PYTHONPATH=spec['bundle'], PYTHONDONTWRITEBYTECODE='1', CUDA_VISIBLE_DEVICES='')
        preflight = subprocess.run(command + ['--preflight'], cwd=spec['bundle'], env=environment,
                                  capture_output=True, text=True, timeout=45)
        write(directory / 'ACTUAL_LOOP_CPU.json', dict(returncode=preflight.returncode, stdout=preflight.stdout,
                                                     stderr=preflight.stderr, cpu_fixture_only=True))
        require(preflight.returncode == 0, 'actual_bound_loop_CPU_gate')
        helper = HERE.parents[3] / 'research_loop/workers/r179_context_survival_20260917/node1/autonomy_node1.py'
        definition = importlib.util.spec_from_file_location('node1_effort_post', helper)
        posting = importlib.util.module_from_spec(definition)
        definition.loader.exec_module(posting)
        posting.post(directory, {'posted': []}, 'cpu', 'R184 effort parent lane' + str(physical) + ' actual-loop CPU PASS',
            'Parent-text-only source-bound policy; existing arm/caps/cadence/masks/schema/provider/English/object guards preserved. '
            'CPU synthetic cases are NOT live receipts. Source/spec and actual-loop tests in `' + str(directory.relative_to(HERE.parents[3]))
            + '`. Cursor preserved' + str(cursor) + ', first due' + str(cursor + first_cadence)
            + '. No common introduction repeated, no child signals, frozen conditions unchanged. Actual publication/rendering pending.')
        require(unchanged(expected, identity(Path('/proc') / str(expected['pid']))), 'same_paused_parent_before_retirement')
        write(directory / 'OLD_PARENT_RETIRE_INTENT.json', dict(actor=expected, child_signals=0, observed_unix=time.time()))
        signal.pidfd_send_signal(descriptor, signal.SIGTERM)
        signal.pidfd_send_signal(descriptor, signal.SIGCONT)
        stopped = False
        require(bool(select.select([descriptor], [], [], 20)[0]), 'old_parent_exit_before_successor')
        retired = True
    finally:
        if stopped and not retired:
            signal.pidfd_send_signal(descriptor, signal.SIGCONT)
        os.close(descriptor)
        os.close(lock)
    write(previous / 'SUPERSEDED.json', dict(successor_spec=str(directory / 'SPEC.json'), child_actions=0, observed_unix=time.time()))
    with (directory / 'RUNNER.log').open('xb') as log:
        process = subprocess.Popen(command, cwd=spec['bundle'], env=environment, stdin=subprocess.DEVNULL,
                                   stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
    deadline = time.monotonic() + 30
    while not (directory / 'parent/STARTED.json').exists():
        require(process.poll() is None and time.monotonic() < deadline, 'bounded_actual_parent_started')
        time.sleep(.1)
    receipt = dict(activation, actor=identity(Path('/proc') / str(process.pid)), policy=POLICY,
                   predecessor=expected, observed_unix=time.time(), first_due_response=cursor + first_cadence,
                   publication_verified=False, request_exposure_verified=False)
    write(directory / 'PARENT_ACTIVATED.json', receipt)
    print(json.dumps(dict(physical=physical, pid=process.pid, directory=str(directory),
                         first_due_response=cursor + first_cadence, status='ACTUAL_STARTED_NOT_DELIVERED')))


if __name__ == '__main__':
    main()
