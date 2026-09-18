"""Stop only the relocated brain_guided node4 parent, not any node3 learner."""

import hashlib
import json
import os
from pathlib import Path
import select
import signal
import time


OWN = Path(__file__).resolve().parent
BINDING = OWN.parents[1] / 'node3/r188/receiving_parents/physical3/BINDING.json'


def identity():
    process = Path('/proc/1607579')
    fields = (process / 'stat').read_text().rsplit(') ', 1)[1].split()
    return dict(pid=1607579, start_ticks=fields[19], uid=process.stat().st_uid,
        argv=(process / 'cmdline').read_bytes().rstrip(b'\0').decode().split('\0'))


def main():
    binding = json.loads(BINDING.read_bytes())
    assert binding['target_node'] == 'node4' and binding['native']['pid'] == 2001674
    assert binding['root'] == '/localhome/local-rohing/orch_r188_node4_relocated_20260917t2349z/receiving3v2/run1'
    expected = identity()
    assert expected['uid'] == os.getuid() and expected['argv'][-3:] == ['serve', '--physical', '3']
    assert expected['argv'][2].endswith('/node3/receiving_parent.py')
    descriptor = os.pidfd_open(expected['pid'])
    assert identity() == expected
    paused = False
    try:
        deadline = time.monotonic() + 60
        while time.monotonic() < deadline:
            signal.pidfd_send_signal(descriptor, signal.SIGSTOP)
            paused = True
            time.sleep(.03)
            assert identity() == expected
            children = Path('/proc/1607579/task/1607579/children').read_text().split()
            active = [child for child in children if Path('/proc', child, 'stat').exists()
                      and Path('/proc', child, 'stat').read_text().rsplit(') ', 1)[1].split()[0] not in ('Z', 'X')]
            if not active:
                signal.pidfd_send_signal(descriptor, signal.SIGTERM)
                signal.pidfd_send_signal(descriptor, signal.SIGCONT)
                paused = False
                assert select.select([descriptor], [], [], 30)[0], 'parent_exit_required'
                receipt = dict(status='EXACT_BRAIN_GUIDED_PARENT_EXITED', process=expected,
                    target_node='node4', native_pid=2001674, root=binding['root'],
                    binding_sha256=hashlib.sha256(BINDING.read_bytes()).hexdigest(),
                    no_inflight_subprocess=True, observed_unix=time.time())
                with (OWN / 'PARENT_RETIRED.json').open('x') as output:
                    json.dump(receipt, output, sort_keys=True, indent=2)
                print(json.dumps(receipt))
                return
            signal.pidfd_send_signal(descriptor, signal.SIGCONT)
            paused = False
            time.sleep(.2)
        raise RuntimeError('parent_not_quiescent_no_retirement')
    finally:
        if paused:
            signal.pidfd_send_signal(descriptor, signal.SIGCONT)
        os.close(descriptor)


if __name__ == '__main__':
    main()
