"""Record Main's explicit replacement reservation on the already-empty slot0."""

import json
import subprocess
import time

from math_c import HOME, WALL, host, read, require, write


host()
root = HOME.parent / 'SCALE_physical0'
gpu = 'GPU-5b370d4d-bdcc-21d5-cf06-e9bea52e602d'
inventory = subprocess.check_output(['nvidia-smi', '--query-gpu=index,uuid,memory.used',
    '--format=csv,noheader,nounits'], text=True, timeout=15)
rows = [line.split(',') for line in inventory.splitlines()]
require(any([field.strip() for field in row] == ['0', gpu, '0'] for row in rows), 'actual_physical0_empty')
applications = subprocess.check_output(['nvidia-smi', '--query-compute-apps=pid,gpu_uuid',
    '--format=csv,noheader,nounits'], text=True, timeout=15)
require(not any(line.split(',')[-1].strip() == gpu for line in applications.splitlines()), 'no_GPU0_compute_occupant')
now = time.time()
require(now + 3600 < WALL, 'full_hour_within_existing_hard_wall')
receipt = dict(status='GPU0_CLEAR_RESERVED_FOR_MAIN_R207', physical=0, gpu_uuid=gpu,
    requested_by='Main explicit04:25 physical0 replacement request', reserved_from_unix=now,
    reserved_until_unix=now + 3600, hard_end_unix=WALL, memory_used_mib=0, compute_processes=[],
    stop_new_allocations=True, no_signals=True, no_GPU_work=True, Main_must_use_fresh_admission=True,
    original_root_preserved=str(root / 'life'), replaces_pending_physical7_reservation=True)
write(root / 'R207_MAIN_INFERENCE_RESERVATION.json', receipt)
write(HOME.parent / 'SCALE_physical7/R207_MAIN_RESERVATION_SUPERSEDED.json',
    dict(replacement_physical=0, superseded_unix=now, native_child_signaled=False, no_new_allocation=True))
print(json.dumps(receipt), flush=True)
