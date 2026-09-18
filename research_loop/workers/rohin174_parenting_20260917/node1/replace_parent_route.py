"""Reuse exact parent-only quiet custody; immutable old bundles and children remain untouched."""

import argparse
import json
import os
from pathlib import Path
import select
import signal
import subprocess
import sys
import time

from first_baseline import exclusive_parent
from inventory_node1 import HERE, Reader, digest, identity, require, unchanged
from parent_custody import write
from parent_runner import load
from forward_parent import next_boundary_loop


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--activation', type=Path, required=True)
    arguments = parser.parse_args()
    old_directory = arguments.activation.resolve()
    require(old_directory.parent == HERE and old_directory.name.startswith(tuple('lane' + str(number) + '_activation_' for number in range(2, 8))), 'only_six_owned_learning_parents')
    old_path = old_directory / 'SPEC.json'
    old_spec = json.loads(Reader().raw(old_path))
    activation = json.loads(Reader().raw(old_directory / 'PARENT_ACTIVATED.json'))
    parent, config, unused_provider, unused_selected = load(old_spec)
    require(not (old_directory / 'SUPERSEDED.json').exists(), 'parent_replacement_once')
    require(not (old_directory / 'PARENT_WITHDRAWAL.json').exists(), 'no_withdrawal_override')
    state = parent['snapshot'](Path(old_spec['repository']), config)
    directory = HERE / (old_directory.name.split('_activation_')[0] + '_activation_route_' + str(time.time_ns()))
    directory.mkdir(mode=0o700)
    write(directory / 'SOURCE_AT_BINDING.json', state)
    spec = dict(old_spec, output=str(directory / 'parent'), reserved_response_count=state['response_count'],
                predecessor_spec=str(old_path), no_common_baseline=True)
    spec['pins'] = dict(old_spec['pins'])
    for source in (HERE / 'forward_parent.py', HERE / 'replace_parent_route.py',
                   Path(old_spec['repository']) / 'gpu/orch_r175_parent_response.py'):
        spec['pins'][str(source)] = digest(Reader().raw(source))
    next_boundary_loop(Reader().raw(spec['legacy_source']).decode(), spec['legacy_source'], state['response_count'])
    descriptor = os.pidfd_open(activation['actor']['pid'])
    retired = False
    try:
        try:
            with exclusive_parent(activation, old_path, directory):
                for attempt in sorted((old_directory / 'parent').glob('parent_*')):
                    result = json.loads(Reader().raw(attempt / 'RESULT.json'))
                    require(result['status'] in ('PUBLISHED', 'MISSING', 'SILENT'), 'settled_prior_result')
                    require(result['status'] == 'PUBLISHED' or 'sent_unix' not in result, 'unknown_publication_reconcile_before_replacement')
                    spec['reserved_response_count'] = max(spec['reserved_response_count'], result['source_response_count'])
                write(directory / 'SPEC.json', spec)
                require(unchanged(activation['actor'], identity(Path('/proc') / str(activation['actor']['pid']))), 'exact_paused_parent_before_retirement')
                write(directory / 'OLD_PARENT_RETIRE_INTENT.json', dict(actor=activation['actor'], observed_unix=time.time(), child_signals=0))
                signal.pidfd_send_signal(descriptor, signal.SIGTERM)
                signal.pidfd_send_signal(descriptor, signal.SIGCONT)
                require(bool(select.select([descriptor], [], [], 20)[0]), 'old_parent_exit_before_new_parent')
                retired = True
        except ProcessLookupError:
            require(retired, 'unexpected_parent_disappearance')
    finally:
        os.close(descriptor)
    write(old_directory / 'SUPERSEDED.json', dict(successor_spec=str(directory / 'SPEC.json'), observed_unix=time.time(), child_actions=0))
    command = [sys.executable, '-B', str(HERE / 'forward_parent.py'), '--spec', str(directory / 'SPEC.json')]
    environment = dict(os.environ, PYTHONPATH=spec['bundle'], PYTHONDONTWRITEBYTECODE='1', CUDA_VISIBLE_DEVICES='')
    with (directory / 'RUNNER.log').open('xb') as output:
        successor = subprocess.Popen(command, cwd=spec['bundle'], env=environment, stdin=subprocess.DEVNULL,
                                     stdout=output, stderr=subprocess.STDOUT, start_new_session=True)
    deadline = time.monotonic() + 30
    while not (directory / 'parent/STARTED.json').exists():
        require(successor.poll() is None, 'successor_failed_before_started')
        require(time.monotonic() < deadline, 'bounded_started_observation')
        time.sleep(.1)
    receipt = dict(activation, actor=identity(Path('/proc') / str(successor.pid)), observed_unix=time.time(),
                   predecessor=activation['actor'], source_spec_sha256=digest(Reader().raw(directory / 'SPEC.json')),
                   first_due_response=spec['reserved_response_count'] + 1, publication_verified=False, request_exposure_verified=False)
    write(directory / 'PARENT_ACTIVATED.json', receipt)
    print(json.dumps(dict(label=activation['label'], pid=successor.pid, first_due_response=receipt['first_due_response'],
                          source_response_count=state['response_count'], directory=str(directory), status='LIVE_WAITING_FRESH_RESPONSE_NOT_DELIVERED')))


if __name__ == '__main__':
    main()
