"""Immutable host observations and one-shot starts for assigned NODE5 parents."""

import argparse
import json
import os
from pathlib import Path
import subprocess
import time

from activate_parent import identity, read, reference, require, sha, validate_owner, write


HERE = Path(__file__).resolve().parent


def observe_old_failure():
    root = HERE / 'ACTIVATION_A_1789678199677664261'
    manifest = read(root / 'C3_MANIFEST.json')
    require(not Path('/proc/444027').exists(), 'old_operator_not_running')
    owner = identity(manifest['predecessor']['pid'])
    validate_owner(manifest['predecessor'], owner)
    missing = ['PARENT_PAUSE_INTENT.json', 'PARENT_RETIRE_INTENT.json', 'ACTIVE_PARENT.json',
               'FIRST_PUBLICATION.json', 'FIRST_RENDERED_REQUEST.json']
    require(all(not (root / 'C3' / name).exists() for name in missing), 'no_takeover_evidence')
    receipt = HERE / ('C3_OLD_OPERATOR_FAILURE_OBSERVED_' + str(time.time_ns()) + '.json')
    write(receipt, dict(status='OPERATOR_FAILED_BEFORE_PARENT_PAUSE_NOT_CHILD_FAILURE',
        retrospectively_observed=True, observed_unix=time.time(), operator_pid=444027,
        original_parent=owner, operator_log=reference(root / 'C3_OPERATOR.log'),
        failed_callsite=str(root / 'source/activate_parent.py') + ':230',
        error='node_transport_failed_no_implicit_retry', reason='copied_wrapper_missing_adjacent_hosts.env',
        absent_receipts=missing, child_signals=0, publication_verified=False, rendered_verified=False,
        repair='new source-bound sanctioned-wrapper delegation; no consumed attempt retry'))
    print(json.dumps(reference(receipt)))


def start(ready_path, label):
    ready = read(ready_path)
    require(ready['status'] == 'CPU_AND_RECEIVING_READY_NOT_STARTED', 'ready_binding')
    chosen = next(item for item in ready['manifests'] if item['label'] == label)
    require(sha(chosen['path']) == chosen['sha256'], 'exact_manifest')
    manifest = read(chosen['path'])
    validate_owner(manifest['predecessor'], identity(manifest['predecessor']['pid']))
    root, source = Path(ready_path).parent, Path(manifest['source'])
    require(root.is_relative_to(HERE) and source.is_relative_to(root), 'owned_only')
    write(root / (label + '_START_ONCE.json'), dict(manifest=chosen, observed_unix=time.time(),
        authorization='Main R175 GO; assigned parent-only takeover; C2 excluded'))
    command = ['/usr/bin/python3', '-B', str(source / 'activate_parent.py'),
               '--manifest', chosen['path'], '--manifest-sha256', chosen['sha256']]
    with (root / (label + '_OPERATOR.log')).open('x') as log:
        process = subprocess.Popen(command, cwd=source, stdin=subprocess.DEVNULL, stdout=log,
            stderr=subprocess.STDOUT, start_new_session=True, close_fds=True,
            env=dict(os.environ, PYTHONPATH=str(source), PYTHONDONTWRITEBYTECODE='1'))
    started = dict(manifest=chosen, pid=process.pid, identity=identity(process.pid),
        observed_unix=time.time(), status='OPERATOR_STARTED_NOT_PUBLICATION_OR_RENDER')
    receipt = root / (label + '_STARTED.json')
    write(receipt, started)
    print(json.dumps(dict(started, receipt=reference(receipt))))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--observe-old-failure', action='store_true')
    parser.add_argument('--ready', type=Path)
    parser.add_argument('--label', choices=('run1', 'pilot', 'repo_reader', 'C1', 'C3', 'C4', 'C5'))
    arguments = parser.parse_args()
    if arguments.observe_old_failure:
        observe_old_failure()
    else:
        start(arguments.ready, arguments.label)
