"""Replace only exact CPU publisher handles to adopt the requested retry guard."""

import argparse
import os
from pathlib import Path
import select
import signal
import subprocess
import sys
import time

from parent_service import HERE, REPO, read, require, write


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--revision', choices=('initial', 'bounded_transport'), default='initial')
    arguments = parser.parse_args()
    os.umask(0o077)
    for arm in ('learner', 'frozen'):
        directory = HERE / 'private' / arm
        receipt_path = directory / ('RETRY_GUARD_ADOPTION.json' if arguments.revision == 'initial' else
                                    'RETRY_GUARD_ADOPTION_' + arguments.revision + '.json')
        require(not receipt_path.exists(), 'do_not_duplicate_adoption')
        previous = read(sorted(directory.glob('PROCESS_*.json'), key=lambda path: path.stat().st_mtime)[-1])
        process_id = previous['pid']
        require(process_id not in (493500, 471737), 'never_signal_a_native')
        descriptor = os.pidfd_open(process_id)
        process = Path('/proc') / str(process_id)
        fields = (process / 'stat').read_text().rsplit(')', 1)[1].split()
        argv = (process / 'cmdline').read_bytes().decode().rstrip('\0').split('\0')
        require(fields[19] == previous['start_ticks'] and argv == previous['argv'] and
                str(HERE / 'parent_service.py') in argv, 'exact_CPU_publisher_required')
        signal.pidfd_send_signal(descriptor, signal.SIGTERM)
        require(bool(select.select([descriptor], [], [], 15)[0]), 'CPU_publisher_exit_required')
        os.close(descriptor)
        stamp = str(time.time_ns())
        with (directory / ('RETRY_GUARD_' + stamp + '.log')).open('x') as output:
            child = subprocess.Popen(previous['argv'], cwd=REPO, stdin=subprocess.DEVNULL,
                                     stdout=output, stderr=subprocess.STDOUT, close_fds=True, start_new_session=True,
                                     env=dict(os.environ, PYTHONDONTWRITEBYTECODE='1', PYTHONUNBUFFERED='1',
                                              CUDA_VISIBLE_DEVICES=''))
        current = Path('/proc', str(child.pid), 'stat').read_text().rsplit(')', 1)[1].split()
        receipt = dict(arm=arm, old_CPU_parent=previous['pid'], old_start_ticks=previous['start_ticks'],
                       pid=child.pid, start_ticks=current[19], observed_unix=time.time(),
                       native_signals=0, native_restarts=0, model_unchanged=True, scaffold_unchanged=True,
                       reason='explicit_user_no_ambiguous_provider_retry_and_bounded_429_backoff',
                       revision=arguments.revision,
                       previously_published_deliveries_and_cursor_preserved=True)
        write(receipt_path, receipt)
        print(arm, child.pid, current[19], flush=True)


if __name__ == '__main__':
    main()
