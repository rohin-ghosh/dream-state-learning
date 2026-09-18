"""Drain and replace exactly the existing P3 CPU publisher, preserving its ledger."""

import argparse
import fcntl
import json
import os
from pathlib import Path
import select
import signal
import subprocess
import sys
import time

import p3_parent
import handoff as predecessor_handoff


def exact_parent(arguments, manifest):
    expected = ['-B', str(p3_parent.PREDECESSOR / 'parent.py'), 'serve', '--physical', '3',
                '--reviewed-config-sha256', manifest['predecessor_config_sha256']]
    if arguments[1:] != expected or Path(arguments[0]).name not in ('python3', 'python'):
        raise ValueError('exact_existing_P3_CPU_publisher_required')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--pid', type=int, required=True)
    parser.add_argument('--manifest-sha256', required=True)
    options = parser.parse_args()
    unused_module, policy, unused_config, manifest = p3_parent.load()
    approved = p3_parent.HERE / 'P3_MANIFEST.json'
    if p3_parent.sha(approved) != options.manifest_sha256 or json.loads(approved.read_text()) != manifest:
        raise ValueError('reviewed_manifest_bytes_required')
    signal.signal(signal.SIGTERM, predecessor_handoff.interrupted)
    output = p3_parent.repair.FLEET / 'r210_parent3'
    process = Path('/proc') / str(options.pid)
    arguments = (process / 'cmdline').read_bytes().decode().strip('\0').split('\0')
    exact_parent(arguments, manifest)
    ticks = (process / 'stat').read_text().rsplit(') ', 1)[1].split()[19]
    descriptor = os.pidfd_open(options.pid)
    stopped = False
    try:
        with (p3_parent.HERE / 'P3_HANDOFF.lock').open('a') as lock:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            if (p3_parent.HERE / 'P3_HANDOFF.json').exists() or (p3_parent.HERE / 'P3_LIVE.json').exists():
                raise ValueError('existing_handoff_requires_reconciliation_not_retry')
            deadline = time.monotonic() + 180
            while time.monotonic() < deadline:
                if (process / 'stat').read_text().rsplit(') ', 1)[1].split()[19] != ticks:
                    raise ValueError('process_identity_changed')
                exact_parent((process / 'cmdline').read_bytes().decode().strip('\0').split('\0'), manifest)
                signal.pidfd_send_signal(descriptor, signal.SIGSTOP)
                stopped = True
                for unused in range(100):
                    if (process / 'stat').read_text().rsplit(') ', 1)[1].split()[0] in ('T', 't'):
                        break
                    time.sleep(.01)
                else:
                    raise RuntimeError('CPU_publisher_not_quiescent')
                receipts = predecessor_handoff.reconciled(output / 'turns')
                if receipts is None:
                    signal.pidfd_send_signal(descriptor, signal.SIGCONT)
                    stopped = False
                    time.sleep(2)
                    continue
                policy.local_attempts(output / 'turns')
                predecessor_handoff.write_once(p3_parent.HERE / 'P3_HANDOFF.json',
                    dict(policy=p3_parent.POLICY, old_pid=options.pid, old_start_ticks=ticks,
                         old_argv=arguments, manifest_sha256=options.manifest_sha256,
                         checked_unix=time.time(), seed_sha256=p3_parent.sha(output / 'SEED.json'),
                         preserved_attempts=receipts, learner_signals=[],
                         classification='NEW_R233_STRONG_PARENT_TREATMENT'))
                signal.pidfd_send_signal(descriptor, signal.SIGTERM)
                signal.pidfd_send_signal(descriptor, signal.SIGCONT)
                stopped = False
                poller = select.poll()
                poller.register(descriptor, select.POLLIN)
                if not poller.poll(10000):
                    raise RuntimeError('old_publisher_exit_unconfirmed_no_successor')
                exit_observed = time.time()
                with (output / 'PARENT_OPERATOR.lock').open('a') as writer:
                    fcntl.flock(writer, fcntl.LOCK_EX | fcntl.LOCK_NB)
                command = [sys.executable, '-B', str(p3_parent.HERE / 'p3_parent.py'), 'serve',
                           '--manifest-sha256', options.manifest_sha256]
                with (p3_parent.HERE / 'P3_PARENT.log').open('a') as log:
                    successor = subprocess.Popen(command, cwd=p3_parent.REPO, stdin=subprocess.DEVNULL,
                        stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
                time.sleep(1)
                if successor.poll() is not None:
                    raise RuntimeError('successor_failed_check_log_no_duplicate_start')
                for name, checksum in receipts.items():
                    if p3_parent.sha(output / 'turns' / name) != checksum:
                        raise ValueError('prior_evidence_changed')
                result = dict(policy=p3_parent.POLICY, parent_pid=successor.pid, old_pid=options.pid,
                    old_exit_observed_unix=exit_observed, checked_unix=time.time(),
                    cpu_handoff_upper_bound_seconds=time.time()-exit_observed,
                    learner_signals=[], preserved_receipt_files=len(receipts),
                    manifest_sha256=options.manifest_sha256, actual_render='pending')
                predecessor_handoff.write_once(p3_parent.HERE / 'P3_LIVE.json', result)
                print(json.dumps(result, sort_keys=True))
                return
            raise TimeoutError('busy_CPU_publisher_preserved')
    finally:
        if stopped:
            signal.pidfd_send_signal(descriptor, signal.SIGCONT)
        os.close(descriptor)


if __name__ == '__main__':
    main()
