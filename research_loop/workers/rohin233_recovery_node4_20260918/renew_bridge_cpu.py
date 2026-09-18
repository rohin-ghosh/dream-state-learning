"""Renew only owned CPU route processes; preserve every queue and cursor."""

import hashlib
import json
import os
from pathlib import Path
import select
import signal
import subprocess
import sys
import time


OWN = Path(__file__).resolve().parent


def write(path, document):
    with path.open('x') as stream:
        json.dump(document, stream, sort_keys=True, indent=2)
        stream.write('\n')
        stream.flush()
        os.fsync(stream.fileno())


def stop_cpu(pid, start, script):
    process = Path('/proc') / str(pid)
    descriptor = os.pidfd_open(pid)
    until = time.monotonic() + 120
    try:
        while time.monotonic() < until:
            fields = (process / 'stat').read_text().rsplit(') ', 1)[1].split()
            argv = (process / 'cmdline').read_bytes().decode().strip('\0').split('\0')
            if fields[19] != start or argv != ['/usr/bin/python3', '-B', str(OWN / script)]:
                raise ValueError('exact_owned_CPU_identity_required')
            children = (process / 'task' / str(pid) / 'children').read_text().strip()
            if not children and (process / 'wchan').read_text().strip() == 'hrtimer_nanosleep':
                signal.pidfd_send_signal(descriptor, signal.SIGTERM)
                poller = select.poll()
                poller.register(descriptor, select.POLLIN)
                if not poller.poll(10000):
                    raise ValueError('owned_CPU_exit_not_observed')
                return dict(pid=pid, start_ticks=start, argv=argv, exited_unix=time.time(),
                    exact_idle_no_subprocess=True, native_signals=[])
            time.sleep(.1)
        raise TimeoutError('CPU_not_idle_no_signal')
    finally:
        os.close(descriptor)


def main():
    output = OWN / 'private/bridge'
    receipt_path = OWN / 'CPU_BRIDGE_CONTINUATION.json'
    if receipt_path.exists():
        raise ValueError('once_only_bridge_continuation')
    status = json.loads((OWN / 'private/ASTRA7_RENEWED_STATUS.json').read_bytes())
    if status['native_pid'] != 886059 or status['loaded_record']['index'] != 3545:
        raise ValueError('actual_Jason_LOAD3545_required')
    stopped = stop_cpu(2996246, '186012013', 'bridge.py')
    cursor_bytes = (output / 'CURSOR.json').read_bytes()
    old_bytes = (output / 'BINDING.json').read_bytes()
    old = json.loads(old_bytes)
    before = output / 'BINDING_BEFORE_NATIVE_CONTINUATION.json'
    with before.open('xb') as stream:
        stream.write(old_bytes)
    binding = dict(old, astra7=status,
        astra7_export_cutoff_index=old.get('astra7_export_cutoff_index', old['astra7']['loaded_record']['index']),
        rebound_unix=time.time(), previous_binding_sha256=hashlib.sha256(old_bytes).hexdigest(),
        queue_history_preserved=True, cursors_preserved=True)
    temporary = output / 'BINDING.continued.json'
    write(temporary, binding)
    os.replace(temporary, output / 'BINDING.json')
    if (output / 'CURSOR.json').read_bytes() != cursor_bytes:
        raise ValueError('no_cursor_advance_during_exact_CPU_rebind')
    with (OWN / 'private/bridge_continuation.log').open('x') as log:
        child = subprocess.Popen([sys.executable, '-B', str(OWN / 'bridge.py')],
            cwd=OWN.parents[2], stdin=subprocess.DEVNULL, stdout=log,
            stderr=subprocess.STDOUT, start_new_session=True)
    receipt = dict(cpu_predecessor=stopped, successor_pid=child.pid, dispatched_unix=time.time(),
        current_child_loaded=3545, current_child_native=886059,
        hard_end_unix=min(1790359200, status['hard_end_unix']),
        prior_export_cutoff_preserved=binding['astra7_export_cutoff_index'],
        cursor_sha256=hashlib.sha256(cursor_bytes).hexdigest(),
        queues_unchanged=True, native_signals=[], delivery_not_claimed_until_actual_receipt=True)
    write(receipt_path, receipt)
    print(json.dumps(receipt), flush=True)


if __name__ == '__main__':
    main()
