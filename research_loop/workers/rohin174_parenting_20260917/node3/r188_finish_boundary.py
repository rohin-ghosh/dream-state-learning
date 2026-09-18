"""Finish a proven pre-dispatch failure at the original exact saved boundary."""

import argparse
import json
import os
from pathlib import Path
import socket
import subprocess
import time

import r181_boundary as base
import r181_journal_boundary as journal


def eligible(folder, spec, boundary):
    base.require(not any((folder / name).exists() for name in
        ('DISPATCH_ONCE', 'DISPATCHED.json', 'LAUNCH.json', 'NATIVE.log', 'SERVICE.log')),
        'unknown_or_previous_dispatch_must_not_retry')
    base.require(base.head(spec['backing_root'])['sha256'] == boundary['record']['sha256'],
        'same_latest_complete_boundary')
    base.require(boundary['record']['kind'] == 'SLEEP_COMPLETE', 'complete_saved_state_only')
    for actor in boundary['actors']:
        proc = Path('/proc') / str(actor['pid'])
        if proc.exists():
            fields = (proc / 'stat').read_text().rsplit(') ', 1)[1].split()
            base.require(fields[19] != actor['ticks'] or fields[0] in ('Z', 'X'),
                'predecessor_still_present')
    targets = {spec['config_path'], str(folder / 'GUARD.json')}
    for proc in Path('/proc').glob('[0-9]*'):
        try:
            argv = (proc / 'cmdline').read_bytes().rstrip(b'\0').decode().split('\0')
        except FileNotFoundError:
            continue
        if '--config' in argv:
            base.require(not targets.intersection(argv), 'possible_existing_successor')
    base.require(time.time() < base.HARD_END - 180, 'unchanged_boundary_admission_deadline')


def finish(folder):
    spec = base.read(folder / 'LIVE_HANDOFF.json')
    boundary = base.read(folder / 'BOUNDARY.json')
    failure = base.read(folder / 'WAIT_FAILED.json')
    base.require(failure['reason'] == 'fresh_same_GPU_admission' or
        failure['error_type'] == 'ProcessLookupError', 'documented_predispatch_failure_only')
    eligible(folder, spec, boundary)
    checkpoint_path = Path(spec['backing_root']) / 'checkpoints' / (
        'sleep_%06d' % boundary['record']['document']['cycle']) / 'COMMIT.json'
    base.require(base.sha(checkpoint_path) == boundary['checkpoint_file_sha256'],
        'original_exact_checkpoint_commit_unchanged')
    for name, digest in boundary['inbox_files'].items():
        base.require(base.sha(Path(spec['backing_root']) / 'stream/inbox' / name) == digest,
            'original_pending_inbox_bytes_preserved')
    bound = base.read(folder / 'JOURNAL_SOURCE_BOUND.json')
    base.require(bound['guard_sha256'] == base.sha(folder / 'GUARD.json') and
        bound['native_sha256'] == base.sha(folder / 'new_native.py') and
        bound['journal_sha256'] == base.sha(folder / 'new_journal.py'),
        'already_tested_exact_R181_cache_binding')
    command = ['sudo', '-n', 'env', 'CUDA_VISIBLE_DEVICES=', 'PYTHONDONTWRITEBYTECODE=1',
        'PYTHONPATH=' + spec['plan']['source_root'], base.PYTHON, '-B', '-m',
        'gpu.orch_r125_continual_guard', 'scan', '--config', spec['config_path']]
    result = subprocess.run(command, capture_output=True, text=True, timeout=90,
        cwd=spec['plan']['source_root'])
    base.require(result.returncode == 0, 'fresh_original_scanner_failed:' + result.stderr[-300:])
    report = json.loads(result.stdout)
    receipt = folder / ('BOUNDARY_REPAIR_SCAN_' + str(time.time_ns()) + '.json')
    base.write(receipt, report)
    base.require(report['scanner_euid'] == 0 and report['clear'] and not report['blocking_reasons']
        and report['gpu']['uuid'] == spec['plan']['gpu_uuid'],
        'fresh_admission_blocked:' + json.dumps(report['blocking_reasons']))
    eligible(folder, spec, boundary)
    base.write(folder / 'BOUNDARY_RECONCILED.json', dict(observed_unix=time.time(),
        prior_failure_sha256=base.sha(folder / 'WAIT_FAILED.json'), scan_receipt=str(receipt),
        boundary_sha256=base.sha(folder / 'BOUNDARY.json'), saved_cycle=boundary['record']['document']['cycle'],
        exact_saved_state_preserved=True, discarded_updates=0, no_prior_dispatch=True,
        native_sha256=bound['native_sha256'], journal_sha256=bound['journal_sha256'],
        hard_end_unix=base.HARD_END))
    base.write(folder / 'ADMISSION.json', report)
    base.write(folder / 'ADMISSION_TIME.json', dict(verified_unix=time.time()))
    (folder / 'DISPATCH_ONCE').mkdir()
    launch = journal.command(folder, 'contained')
    base.write(folder / 'CONTAINED_COMMAND.json', dict(command=launch, observed_unix=time.time()))
    with (folder / 'SERVICE.log').open('x') as log:
        process = subprocess.Popen(launch, stdin=subprocess.DEVNULL, stdout=log,
            stderr=subprocess.STDOUT, start_new_session=True)
    base.write(folder / 'DISPATCHED.json', dict(pid=process.pid, observed_unix=time.time(),
        resumed_same_saved_life=True, reconciled_predispatch_failure=True))
    print(json.dumps(dict(physical=spec['physical'], pid=process.pid,
        saved_cycle=boundary['record']['document']['cycle'], status='DISPATCHED_NOT_YET_LOADED')), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--physical', type=int, choices=(0, 3, 4, 7), required=True)
    args = parser.parse_args()
    base.require(socket.gethostname() == '[REDACTED_HOST]', 'node3_only')
    finish(base.HERE / 'r181' / ('physical' + str(args.physical)))
