"""Wait for the existing public snapshot copy, then independently dispatch4/5."""

import concurrent.futures
import json
import os
from pathlib import Path
import subprocess
import time

from gpu import ny_caption_vision as vision
from research_loop.workers.rohin206_games_20260918.vision.service import HOME, HARD_END, PYTHON, once, validate_host


validate_host()
once(HOME / 'DISPATCH_WAITER.json', dict(pid=os.getpid(), started_unix=time.time(),
    status='WAITING_EXACT_WEIGHTS_NO_GPU_ACTION_YET', physicals=[4, 5]))
while time.time() < HARD_END - 180:
    vision.require(not (HOME / 'PAUSED_BY_R209.json').exists(), 'allocation_withdrawn_no_dispatch')
    manifest = HOME / 'snapshot/SNAPSHOT_MANIFEST.json'
    if manifest.exists():
        value = vision.strict_json(manifest.read_bytes())
        if all((HOME / 'snapshot' / name).exists() and (HOME / 'snapshot' / name).stat().st_size == item['bytes']
                for name, item in value['files'].items()):
            break
    time.sleep(3)
else:
    raise RuntimeError('lease_time_exhausted_before_weight_transfer')
vision.verify_snapshot(HOME / 'snapshot')
once(HOME / 'WEIGHTS_VERIFIED.json', dict(status='EXACT_PINNED_PUBLIC_VLM_VERIFIED',
    model_id=vision.MODEL_ID, revision=vision.REVISION, observed_unix=time.time(),
    manifest_sha256=vision.file_digest(manifest), no_original_lives_modified=True))


def launch(role):
    vision.require(not (HOME / 'PAUSED_BY_R209.json').exists(), 'allocation_withdrawn_no_dispatch')
    worker = Path(__file__).with_name('service.py')
    with (HOME / ('LAUNCH_' + role + '.log')).open('x') as output:
        result = subprocess.run([PYTHON, '-B', str(worker), 'launch', '--role', role],
            cwd=HOME / 'source', env=dict(os.environ, PYTHONPATH=str(HOME / 'source'), PYTHONDONTWRITEBYTECODE='1'),
            stdin=subprocess.DEVNULL, stdout=output, stderr=subprocess.STDOUT, timeout=240)
    return dict(role=role, exit_code=result.returncode, observed_unix=time.time())


with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
    results = list(pool.map(launch, ('vision', 'comparator')))
once(HOME / 'DISPATCH_RESULTS.json', dict(results=results, actual_loaded_receipts_required=True))
