"""Cancel exact obsolete operator observers without signaling any learner."""

import os
from pathlib import Path
import signal
import time

from math_c import HOME, PYTHON, host, read, require, write


def main():
    host()
    selected = [(3737307, '27211236', ['--physical', '7']), (3798395, '27268940', [])]
    evidence = []
    for pid, start_ticks, suffix in selected:
        process = Path('/proc', str(pid))
        row = dict(pid=pid, expected_start_ticks=start_ticks, action='ALREADY_EXITED')
        if process.exists():
            arguments = (process / 'cmdline').read_bytes().decode().strip('\0').split('\0')
            expected = [str(PYTHON), '-B', str(HOME / 'finish_r204_screen.py')] + suffix
            fields = (process / 'stat').read_text().rsplit(') ', 1)[1].split()
            require(arguments == expected and fields[19] == start_ticks and process.stat().st_uid == os.getuid(),
                'exact_own_obsolete_screen_observer_only')
            descriptor = os.pidfd_open(pid)
            require((process / 'stat').read_text().rsplit(') ', 1)[1].split()[19] == start_ticks, 'same_pidfd_identity')
            signal.pidfd_send_signal(descriptor, signal.SIGTERM)
            os.close(descriptor)
            row.update(action='CANCELED_EXACT_PIDFD_SIGTERM', argv=arguments,
                observer_only_not_a_child_pause_process=True, signaled_unix=time.time())
        evidence.append(row)
    output = HOME.parent / 'R212_NO_HOLDS.json'
    write(output, dict(phase='R212_NO_OPERATOR_HOLDS', observed_unix=time.time(),
        canceled_obsolete_observers=evidence, child_signals=[], hard_lease_wall_unchanged=True,
        P7_parent_silent_isolation_preserved=True, no_PAUSED_markers_written=True))
    print(output, flush=True)


if __name__ == '__main__':
    main()
