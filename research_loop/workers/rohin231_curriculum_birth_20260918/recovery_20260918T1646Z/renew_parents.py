"""Renew only the pair CPU publishers under the corrected existing lease date."""

import json
import os
from pathlib import Path
import select
import signal
import subprocess
import sys
import time


def main():
    own = Path(__file__).resolve().parent
    private = own / 'private'
    allocation = json.loads((own / 'ALLOCATION_DATE_CORRECTION.json').read_bytes())
    if not os.environ.get('NVIDIA_API_KEY'):
        raise ValueError('existing_provider_environment_missing')
    targets = {'learner': (2779281, '185782871'), 'frozen': (2887550, '185904214')}
    for arm in ('frozen', 'learner'):
        process_id, ticks = targets[arm]
        result = private / ('RENEW_PARENT_' + arm + '.json')
        if result.exists():
            raise ValueError('no_duplicate_renewal')
        parent_private = own.parent / ('r232_pair/private/frozen_parent' if arm == 'frozen' else 'private/parent')
        incomplete = [path.parent.name for path in parent_private.glob('*/INPUT.json')
            if not (path.parent / 'RESULT.json').exists() and not (path.parent / 'REJECTED.json').exists()]
        if incomplete:
            raise ValueError('preserve_inflight_parent_provider_request_' + arm)
        directory = Path('/proc', str(process_id))
        fields = (directory / 'stat').read_text().rsplit(')', 1)[1].split()
        command = (directory / 'cmdline').read_bytes().split(b'\0')
        if fields[19] != ticks or str(own / 'resume_parent.py').encode() not in command or arm.encode() not in command:
            raise ValueError('exact_old_CPU_parent_identity')
        descriptor = os.pidfd_open(process_id)
        signal.pidfd_send_signal(descriptor, signal.SIGTERM)
        if not select.select([descriptor], [], [], 15)[0]:
            raise TimeoutError('old_CPU_parent_still_running')
        os.close(descriptor)
        with (private / ('RENEW_PARENT_' + arm + '.log')).open('x') as output:
            child = subprocess.Popen([sys.executable, '-B', str(own / 'resume_parent.py'), '--arm', arm,
                '--deadline', str(allocation['hard_end_unix'])], stdin=subprocess.DEVNULL,
                stdout=output, stderr=subprocess.STDOUT, env=dict(os.environ, PYTHONDONTWRITEBYTECODE='1'),
                start_new_session=True, close_fds=True)
        current = Path('/proc', str(child.pid), 'stat').read_text().rsplit(')', 1)[1].split()
        receipt = dict(observed_unix=time.time(), arm=arm, old_pid=process_id, old_start_ticks=ticks,
            old_CPU_parent_exited=True, pid=child.pid, start_ticks=current[19],
            deadline_unix=allocation['hard_end_unix'], same_parent_source_and_ledger=True,
            native_signals=0, secret_values_written=False, actual_new_delivery_not_yet_claimed=True)
        with result.open('x') as handle:
            json.dump(receipt, handle, indent=2)
        print(json.dumps(receipt, sort_keys=True))


if __name__ == '__main__':
    main()
