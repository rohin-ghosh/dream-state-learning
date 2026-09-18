"""Read-only completion watcher for Main's requested physical7 inference window."""

import argparse
import json
import os
from pathlib import Path
import subprocess
import time

from math_c import HOME, PYTHON, WALL, host, read, require, write


ROOT = HOME.parent / 'SCALE_physical7'
RESERVATION = ROOT / 'R207_MAIN_INFERENCE_RESERVATION.json'
GPU = 'GPU-6eac3b9d-551a-d786-f598-04ef6d701c98'


def reserve():
    host()
    require(not RESERVATION.exists(), 'one_reservation_only')
    write(RESERVATION, dict(status='PENDING_CURRENT_SCREEN_NATURAL_EXIT', physical=7, gpu_uuid=GPU,
        requested_by='Main R207', purpose='Main inference', requested_seconds=3600,
        current_root=str(ROOT / 'life'), current_native_pid=3856866, current_native_start_ticks='27326191',
        current_guard=str(ROOT / 'reload_r206/control/GUARD.json'), hard_end_unix=WALL,
        requested_unix=time.time(), stop_new_allocations=True, active_child_signaled=False,
        scope='operator reservation; Main still performs actual admission before inference'))
    with (ROOT / 'R207_RESERVATION_WATCH.log').open('x') as output:
        process = subprocess.Popen([str(PYTHON), '-B', str(HOME / 'reserve_main7.py'), 'watch'],
            stdin=subprocess.DEVNULL, stdout=output, stderr=subprocess.STDOUT, start_new_session=True)
    write(ROOT / 'R207_RESERVATION_WATCH.json', dict(pid=process.pid, started_unix=time.time(),
        no_signals=True, no_GPU_work=True))
    print(json.dumps(read(RESERVATION)), flush=True)


def watch():
    host()
    reservation = read(RESERVATION)
    control = Path(reservation['current_guard']).parent
    while time.time() < WALL - reservation['requested_seconds']:
        if not (control / 'EXIT.json').exists():
            time.sleep(3)
            continue
        exit_receipt = read(control / 'EXIT.json')
        if exit_receipt['exit_code'] != 0:
            write(ROOT / 'R207_RESERVATION_BLOCKED.json', dict(reason='current_native_nonzero_exit_requires_review',
                exit_receipt=exit_receipt, observed_unix=time.time(), no_signals=True))
            return
        records = [read(path) for path in sorted((ROOT / 'life/stream/records').glob('[0-9]' * 20 + '.json'))]
        complete = next(row for row in reversed(records) if row['kind'] == 'SLEEP_COMPLETE')
        require(complete['document']['cycle'] == 57 and records[-1]['kind'] == 'TERMINAL'
            and records[-1]['document']['completed_sleeps'] == 57, 'fixed_screen_completed_at57')
        observed = subprocess.check_output(['nvidia-smi', '--query-compute-apps=pid,gpu_uuid',
            '--format=csv,noheader,nounits'], text=True, timeout=15)
        if any(line.split(',')[-1].strip() == GPU for line in observed.splitlines()):
            time.sleep(3)
            continue
        memory = subprocess.check_output(['nvidia-smi', '--query-gpu=uuid,memory.used',
            '--format=csv,noheader,nounits'], text=True, timeout=15)
        used = [line.split(',')[1].strip() for line in memory.splitlines() if line.split(',')[0].strip() == GPU]
        require(len(used) == 1, 'exact_selected_GPU_reported')
        if used != ['0']:
            time.sleep(3)
            continue
        now = time.time()
        write(ROOT / 'R207_MAIN_INFERENCE_AVAILABLE.json', dict(status='SCREEN57_PRESERVED_GPU7_CLEAR_RESERVED_FOR_MAIN',
            physical=7, gpu_uuid=GPU, reserved_from_unix=now, reserved_until_unix=now + 3600,
            hard_end_unix=WALL, complete_index=complete['index'], complete_sha256=complete['sha256'],
            checkpoint=complete['document']['checkpoint'], prior_root=str(ROOT / 'life'),
            current_native_exited=True, memory_used_mib=0, compute_processes=[], native_exit=exit_receipt,
            state_and_inboxes_preserved_in_place=True, no_signals=True, no_GPU_work=True,
            Main_must_use_fresh_admission=True))
        return
    write(ROOT / 'R207_RESERVATION_BLOCKED.json', dict(reason='insufficient_remaining_lease_for_full_60min',
        observed_unix=time.time(), no_signals=True))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=('reserve', 'watch'))
    options = parser.parse_args()
    globals()[options.action]()
