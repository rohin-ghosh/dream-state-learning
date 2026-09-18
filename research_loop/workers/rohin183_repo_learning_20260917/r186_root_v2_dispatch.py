"""One explicit dispatch for each CPU-ready fresh root-repair attempt."""

from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
import subprocess
import time

from research_loop.workers.rohin183_repo_learning_20260917.safe_snapshot import write, digest, require


ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[2]
REMOTE = '/localhome/local-rohing/orch_r153_r186_c2_plasticity_20260917'


def dispatch(label):
    ready = json.loads((ROOT / ('R186_ROOT_V2_' + label.upper() + '_RECEIVING.log')).read_text().splitlines()[-1])
    require(ready['status'] == 'CPU_READY_NOT_DISPATCHED' and ready['tests_run'] == 91,
        'actual_root_repair_receiving_CPU_gate')
    entry = dict(label=label, logged_unix=time.time(), cpu_sha256=ready['cpu_sha256'],
        plan_sha256=ready['plan_sha256'],
        coordination_entry_sha256=digest((ROOT / 'R186_ROOT_V2_CPU_GATE.md').read_bytes()),
        coordination_path='research_loop/COORDINATION.md',
        coordination_heading='[Builder/Ampere — R186 root repair91 receiving tests PASS, prior attempts preserved] 2026-09-17 16:21 PDT')
    write(ROOT / ('R186_ROOT_V2_' + label.upper() + '_BUILDER_ENTRY.json'), entry)
    command = 'set -eu; cd ' + REMOTE + '/' + label + '2; set -C; cat > BUILDER_ENTRY.json; ' + (
        'CUDA_VISIBLE_DEVICES= PYTHONDONTWRITEBYTECODE=1 /localhome/local-rohing/v2/venv/bin/python -B receive.py launch ' + label)
    with (ROOT / ('R186_ROOT_V2_' + label.upper() + '_LAUNCH.log')).open('x') as output:
        result = subprocess.run(['bash', 'gpu/ovx_ssh.sh', command], cwd=REPO, input=json.dumps(entry).encode(),
            stdout=output, stderr=subprocess.STDOUT, timeout=60)
    return dict(label=label, wrapper_exit=result.returncode, observed_unix=time.time(), actual_LOADED_claim=False)


if __name__ == '__main__':
    with ThreadPoolExecutor(max_workers=4) as pool:
        results = list(pool.map(dispatch, ('p4', 'p32', 'lr03', 'lr3')))
    print(json.dumps(write(ROOT / 'R186_ROOT_V2_DISPATCH.json', results), sort_keys=True))
