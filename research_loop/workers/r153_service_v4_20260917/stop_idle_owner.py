"""Stop only the identified controller sidecar after verifying it has no CPU call."""

import json
import os
from pathlib import Path
import select
import signal
import sqlite3
import time


process_id = 1517195
directory = Path(__file__).resolve().parent
process = Path('/proc') / str(process_id)
expected_start = '170876732'
assert process.joinpath('stat').read_text().rsplit(') ', 1)[1].split()[19] == expected_start
arguments = process.joinpath('cmdline').read_bytes().split(b'\0')
assert b'gpu.orch_r153_community_service' in arguments
assert b'research_loop/workers/r153_service_v2_20260916/SERVICE_CONFIG_V2.json' in arguments
descriptor = os.pidfd_open(process_id)
stopped = False
try:
    for attempt in range(100):
        if process.joinpath('wchan').read_text().strip() != 'hrtimer_nanosleep':
            time.sleep(0.2)
            continue
        signal.pidfd_send_signal(descriptor, signal.SIGSTOP)
        stopped = True
        time.sleep(0.05)
        children = []
        for task in process.joinpath('task').iterdir():
            children.extend(task.joinpath('children').read_text().split())
        database = sqlite3.connect('file:/data/home/rohing/courier/r153_community_20260916/broker/state.sqlite3?mode=ro', uri=True)
        active = database.execute("SELECT count(*) FROM service_jobs WHERE status IN ('CPU_INTENT','CPU_UNKNOWN')").fetchone()[0]
        database.close()
        if children or active:
            signal.pidfd_send_signal(descriptor, signal.SIGCONT)
            stopped = False
            time.sleep(0.2)
            continue
        receipt = dict(pid=process_id, start_ticks=expected_start, observed_unix=time.time(),
                       child_processes=children, active_CPU_jobs=active, scope='controller_sidecar_only')
        with (directory / 'STOP_INTENT.json').open('x') as output:
            json.dump(receipt, output, sort_keys=True)
        signal.pidfd_send_signal(descriptor, signal.SIGTERM)
        signal.pidfd_send_signal(descriptor, signal.SIGCONT)
        stopped = False
        poller = select.poll()
        poller.register(descriptor, select.POLLIN)
        assert poller.poll(10000), 'controller_not_exited'
        with (directory / 'STOPPED.json').open('x') as output:
            json.dump(receipt, output, sort_keys=True)
        break
    else:
        raise RuntimeError('no_idle_controller_boundary_observed')
finally:
    if stopped:
        signal.pidfd_send_signal(descriptor, signal.SIGCONT)
    os.close(descriptor)
