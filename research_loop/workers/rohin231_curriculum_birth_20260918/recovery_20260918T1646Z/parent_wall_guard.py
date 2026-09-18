"""Cap one exact existing CPU parent without changing either learner."""

import argparse
import json
import os
from pathlib import Path
import select
import signal
import time


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--pid', type=int, required=True)
    parser.add_argument('--start-ticks', required=True)
    arguments = parser.parse_args()
    deadline = 1789754400
    directory = Path('/proc', str(arguments.pid))
    own = Path(__file__).resolve().parent
    descriptor = os.pidfd_open(arguments.pid)
    fields = (directory / 'stat').read_text().rsplit(')', 1)[1].split()
    command = (directory / 'cmdline').read_bytes().split(b'\0')
    if fields[19] != arguments.start_ticks or str(own / 'resume_parent.py').encode() not in command:
        raise ValueError('exact_existing_CPU_parent_required')
    output = own / 'private' / ('PARENT_WALL_' + str(arguments.pid) + '.json')
    with output.open('x') as handle:
        json.dump(dict(observed_unix=time.time(), parent_pid=arguments.pid,
            parent_start_ticks=arguments.start_ticks, deadline_unix=deadline,
            controller_pid=os.getpid(), native_signals=0), handle)
    if not select.select([descriptor], [], [], max(0, deadline - time.time()))[0]:
        signal.pidfd_send_signal(descriptor, signal.SIGTERM)
        if not select.select([descriptor], [], [], 15)[0]:
            raise TimeoutError('CPU_parent_did_not_exit')
    with output.with_name(output.stem + '_EXIT.json').open('x') as handle:
        json.dump(dict(observed_unix=time.time(), parent_pid=arguments.pid, exited=True, native_signals=0), handle)
    os.close(descriptor)


if __name__ == '__main__':
    main()
