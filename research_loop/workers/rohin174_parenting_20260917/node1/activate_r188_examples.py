"""Quiet, source-bound parent-only takeover preserving pending publications."""

import json
import os
from pathlib import Path
import select
import signal
import subprocess
import sys
import time

from inventory_node1 import HERE, Reader, digest, identity, unchanged, require
from parent_custody import transport_children, write
from r188_examples_parent import POLICY_SHA


def main(physical):
    require(physical in range(8), 'eight_current_node1_parent_lives')
    candidates = sorted(path for path in HERE.glob('*r184_effort_*') if path.is_dir()
        and (path / 'PARENT_ACTIVATED.json').exists() and not (path / 'SUPERSEDED.json').exists()
        and json.loads((path / 'SPEC.json').read_text())['physical'] == physical)
    require(len(candidates) == 1, 'one_current_parent')
    previous = candidates[0]
    old_spec = json.loads(Reader().raw(previous / 'SPEC.json'))
    expected = json.loads(Reader().raw(previous / 'PARENT_ACTIVATED.json'))['actor']
    require(expected['uid'] == os.getuid() and str(HERE / 'r184_effort_parent.py') in expected['argv'], 'exact_R184_parent')
    require(not (previous / 'PARENT_WITHDRAWAL.json').exists(), 'declared_withdrawal_do_not_inject')
    output = HERE / ('lane' + str(physical) + '_activation_r188_examples_' + str(time.time_ns()))
    output.mkdir()
    descriptor = os.pidfd_open(expected['pid'])
    paused, retired = False, False
    try:
        deadline = time.monotonic() + 90
        while True:
            current = identity(Path('/proc') / str(expected['pid']))
            require(unchanged(expected, current) and current['state'] not in ('T', 't', 'Z', 'X'), 'exact_live_parent')
            signal.pidfd_send_signal(descriptor, signal.SIGSTOP)
            paused = True
            for unused in range(100):
                if identity(Path('/proc') / str(expected['pid']))['state'] in ('T', 't'):
                    break
                time.sleep(.01)
            attempts = sorted(path for path in (previous / 'parent').glob('parent_*') if path.is_dir())
            if all((path / 'RESULT.json').exists() for path in attempts) and not transport_children(expected['pid']):
                break
            signal.pidfd_send_signal(descriptor, signal.SIGCONT)
            paused = False
            require(time.monotonic() < deadline, 'busy_parent_original_preserved')
            time.sleep(.2)
        require(not list((previous / 'parent').glob('parent_*/PUBLICATION_UNKNOWN.json')), 'unknown_publication_never_retried')
        results = [json.loads(Reader().raw(path / 'RESULT.json')) for path in attempts]
        require(all(result['status'] in ('PUBLISHED', 'MISSING', 'SILENT') for result in results), 'known_settled_previous_calls')
        cursor = max([old_spec['reserved_response_count']] + [result['source_response_count'] for result in results])
        original_cursor = cursor
        rebase = None
        if physical == 2:
            rebase = json.loads(Reader().raw(HERE / 'R188_REPLAY_RESPONSE_FRONTIER.json'))
            require(rebase['complete_index'] == 5120 and rebase['complete_sha256'] == '1b774bcf225db0011979c73fa018e7d2dcb198da83ff3d4e01ba0b795ff3410a', 'authorized_loss_frontier_only')
            cursor = min(cursor, rebase['response_count'])
        config = json.loads(Reader().raw(old_spec['config']))
        spec = dict(old_spec, output=str(output / 'parent'), predecessor_spec=str(previous / 'SPEC.json'),
            reserved_response_count=cursor, r184_first_cadence=1,
            r188_examples_source=str(HERE / 'r188_parent_examples_bound.py'), pins=dict(old_spec['pins']))
        for source in (HERE / 'r188_parent_examples_bound.py', HERE / 'r188_examples_parent.py', Path(__file__).resolve()):
            spec['pins'][str(source)] = digest(Reader().raw(source))
        require(spec['pins'][spec['r188_examples_source']] == POLICY_SHA, 'Main_exact_policy')
        write(output / 'SPEC.json', spec)
        write(output / 'PRESERVED_LEDGER.json', dict(attempts=[str(path) for path in attempts], results=results,
            previous_cursor=original_cursor, reserved_cursor=cursor, authorized_R188_rebase=rebase,
            common_baseline_resent=False, pending_publications_preserved=True, child_signals=0, observed_unix=time.time()))
        command = [sys.executable, '-B', str(HERE / 'r188_examples_parent.py'), '--spec', str(output / 'SPEC.json')]
        environment = dict(os.environ, PYTHONPATH=spec['bundle'], PYTHONDONTWRITEBYTECODE='1', CUDA_VISIBLE_DEVICES='')
        check = subprocess.run(command + ['--preflight'], cwd=spec['bundle'], env=environment, capture_output=True, text=True, timeout=45)
        write(output / 'ACTUAL_LOOP_CPU.json', dict(returncode=check.returncode, stdout=check.stdout, stderr=check.stderr, cpu_fixture_only=True))
        require(check.returncode == 0, 'actual_parent_loop_checks')
        require(unchanged(expected, identity(Path('/proc') / str(expected['pid']))), 'same_quiet_parent')
        write(output / 'RETIRE_INTENT.json', dict(parent=expected, observed_unix=time.time(), child_signals=0))
        signal.pidfd_send_signal(descriptor, signal.SIGTERM)
        signal.pidfd_send_signal(descriptor, signal.SIGCONT)
        paused = False
        require(bool(select.select([descriptor], [], [], 20)[0]), 'predecessor_exit_before_new_parent')
        retired = True
    finally:
        if paused and not retired:
            signal.pidfd_send_signal(descriptor, signal.SIGCONT)
        os.close(descriptor)
    write(previous / 'SUPERSEDED.json', dict(successor_spec=str(output / 'SPEC.json'), observed_unix=time.time(), child_actions=0))
    with (output / 'RUNNER.log').open('xb') as log:
        process = subprocess.Popen(command, cwd=spec['bundle'], env=environment, stdin=subprocess.DEVNULL,
            stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
    deadline = time.monotonic() + 30
    while not (output / 'parent/STARTED.json').exists():
        require(process.poll() is None and time.monotonic() < deadline, 'actual_parent_started')
        time.sleep(.1)
    write(output / 'PARENT_ACTIVATED.json', dict(physical=physical, actor=identity(Path('/proc') / str(process.pid)),
        first_due_response=cursor + 1, policy='R188_REPORTED_WORKED_EXAMPLES_V1', policy_sha256=POLICY_SHA,
        publication_verified=False, request_exposure_verified=False, observed_unix=time.time()))
    print(json.dumps(dict(physical=physical, pid=process.pid, output=str(output), status='STARTED_NOT_DELIVERED')), flush=True)


if __name__ == '__main__':
    main(int(sys.argv[1]))
