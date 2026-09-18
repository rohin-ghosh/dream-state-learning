"""Main's exact-identity, drained CPU-parent handoff; never signal a learner."""

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

import parent
import repair


def exact_parent(arguments, physical):
    expected = ['-B', str(repair.CURRICULUM / 'node4_parent.py'), 'serve', '--physical', str(physical)]
    if physical not in repair.ALLOWED or arguments[1:] != expected or Path(arguments[0]).name not in ('python3', 'python'):
        raise ValueError('exact_current_R230_CPU_parent_only')


def reconciled(attempts):
    receipts = {}
    for source in sorted(attempts.glob('parent_*/SOURCE.json')):
        result_path = source.parent / 'RESULT.json'
        if not result_path.exists():
            return None
        result = repair.read(result_path)
        if result.get('source_sha256') != repair.sha(source):
            raise ValueError('attempt_source_pin_mismatch')
        if result.get('status') not in ('PUBLISHED', 'SILENT', 'PROVIDER_FAILED', 'VALIDATION_FAILED'):
            raise ValueError('uncertain_or_unknown_publication_status')
        receipts[str(source.relative_to(attempts))] = repair.sha(source)
        receipts[str(result_path.relative_to(attempts))] = repair.sha(result_path)
    return receipts


def write_once(path, value):
    with path.open('x') as stream:
        json.dump(value, stream, sort_keys=True, indent=2)
        stream.flush()
        os.fsync(stream.fileno())


def interrupted(signum, frame):
    raise KeyboardInterrupt('CPU handoff interrupted; resume any quiesced writer')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--physical', type=int, choices=repair.ALLOWED, required=True)
    parser.add_argument('--pid', type=int, required=True)
    parser.add_argument('--reviewed-config-sha256', required=True)
    options = parser.parse_args()
    signal.signal(signal.SIGTERM, interrupted)
    module, unused_frozen, policy, config = parent.load_runtime(options.physical)
    policy.validate(config)
    target = repair.HERE / f'physical{options.physical}'
    if repair.sha(target / 'CONFIG.json') != options.reviewed_config_sha256:
        raise ValueError('reviewed_config_bytes_required')
    output = repair.FLEET / f'r210_parent{options.physical}'
    process = Path('/proc') / str(options.pid)
    arguments = (process / 'cmdline').read_bytes().decode().strip('\0').split('\0')
    exact_parent(arguments, options.physical)
    ticks = (process / 'stat').read_text().rsplit(') ', 1)[1].split()[19]
    descriptor = os.pidfd_open(options.pid)
    stopped = False
    try:
        with (target / 'HANDOFF.lock').open('a') as lock:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            if (target / 'HANDOFF.json').exists() or (target / 'LIVE.json').exists():
                raise ValueError('existing_handoff_requires_reconciliation_not_retry')
            deadline = time.monotonic() + 180
            while time.monotonic() < deadline:
                if (process / 'stat').read_text().rsplit(') ', 1)[1].split()[19] != ticks:
                    raise ValueError('CPU_process_identity_changed')
                exact_parent((process / 'cmdline').read_bytes().decode().strip('\0').split('\0'), options.physical)
                signal.pidfd_send_signal(descriptor, signal.SIGSTOP)
                stopped = True
                for unused in range(100):
                    if (process / 'stat').read_text().rsplit(') ', 1)[1].split()[0] in ('T', 't'):
                        break
                    time.sleep(.01)
                else:
                    raise RuntimeError('CPU_parent_not_quiescent')
                receipts = reconciled(output / 'turns')
                if receipts is None:
                    signal.pidfd_send_signal(descriptor, signal.SIGCONT)
                    stopped = False
                    time.sleep(2)
                    continue
                policy.local_attempts(output / 'turns')
                write_once(target / 'HANDOFF.json', dict(policy=repair.POLICY,
                    physical=options.physical, old_pid=options.pid, old_start_ticks=ticks,
                    old_argv=arguments, old_executable=os.readlink(process / 'exe'),
                    old_config_sha256=repair.sha(repair.CURRICULUM / f'physical{options.physical}/CONFIG.json'),
                    reviewed_config_sha256=options.reviewed_config_sha256,
                    checked_unix=time.time(), seed_sha256=repair.sha(output / 'SEED.json'),
                    binding_sha256=repair.sha(output / 'BINDING.json'), preserved_attempts=receipts,
                    original_output=str(output), learner_signals=[], classification='NEW_R230_PARENT_TREATMENT'))
                signal.pidfd_send_signal(descriptor, signal.SIGTERM)
                signal.pidfd_send_signal(descriptor, signal.SIGCONT)
                stopped = False
                poller = select.poll()
                poller.register(descriptor, select.POLLIN)
                if not poller.poll(10000):
                    raise RuntimeError('old_CPU_writer_exit_not_confirmed_no_successor')
                exit_observed = time.time()
                with (output / 'PARENT_OPERATOR.lock').open('a') as writer:
                    fcntl.flock(writer, fcntl.LOCK_EX | fcntl.LOCK_NB)
                command = [sys.executable, '-B', str(repair.HERE / 'parent.py'), 'serve',
                    '--physical', str(options.physical), '--reviewed-config-sha256', options.reviewed_config_sha256]
                with (target / 'PARENT.log').open('a') as log:
                    successor = subprocess.Popen(command, cwd=repair.REPO, stdin=subprocess.DEVNULL,
                        stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
                time.sleep(1)
                if successor.poll() is not None:
                    raise RuntimeError('new_CPU_parent_failed_check_log_no_automatic_duplicate')
                for name, digest in receipts.items():
                    if repair.sha(output / 'turns' / name) != digest:
                        raise ValueError('prior_evidence_changed')
                document = dict(policy=repair.POLICY, physical=options.physical,
                    old_pid=options.pid, parent_pid=successor.pid, started_unix=time.time(),
                    old_exit_observed_unix=exit_observed, cpu_handoff_seconds=time.time() - exit_observed,
                    config_sha256=options.reviewed_config_sha256, learner_signals=[],
                    previous_attempt_count=len(receipts) // 2, cadence_responses=1,
                    publication='pending_actual_render_verification', original_output=str(output))
                write_once(target / 'LIVE.json', document)
                print(json.dumps(document, sort_keys=True))
                return
            raise TimeoutError('CPU_writer_busy_old_parent_preserved')
    finally:
        if stopped:
            signal.pidfd_send_signal(descriptor, signal.SIGCONT)
        os.close(descriptor)


if __name__ == '__main__':
    main()
