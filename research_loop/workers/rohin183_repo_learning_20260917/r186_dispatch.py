"""Consume each prepared arm once, with the actual pre-dispatch Builder entry."""

from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
import subprocess
import time

from research_loop.workers.rohin183_repo_learning_20260917.r186_copy import ARMS, REMOTE_ROOT
from research_loop.workers.rohin183_repo_learning_20260917.safe_snapshot import write, digest, require


ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[2]


def dispatch(label):
    logfile = ROOT / ('R186_' + label.upper() + '_RECEIVING.log')
    ready = json.loads(logfile.read_text().splitlines()[-1])
    require(ready['status'] == 'CPU_READY_NOT_DISPATCHED' and ready['tests_run'] == 89,
        'actual_receiving_gate_before_dispatch')
    entry = dict(label=label, logged_unix=time.time(), cpu_sha256=ready['cpu_sha256'],
        plan_sha256=ready['plan_sha256'], coordination_entry_sha256=digest((ROOT / 'R186_BUILDER_CPU_GATE.md').read_bytes()),
        coordination_path='research_loop/COORDINATION.md',
        coordination_heading='[Builder/Ampere — R186 actual receiving CPU PASS before four dispatches] 2026-09-17 16:14 PDT')
    write(ROOT / ('R186_' + label.upper() + '_BUILDER_ENTRY.json'), entry)
    remote = REMOTE_ROOT + '/' + label + '1'
    command = 'set -eu; cd ' + remote + '; set -C; cat > BUILDER_ENTRY.json; ' + (
        'CUDA_VISIBLE_DEVICES= PYTHONDONTWRITEBYTECODE=1 /localhome/local-rohing/v2/venv/bin/python -B receive.py launch ' + label)
    with (ROOT / ('R186_' + label.upper() + '_LAUNCH.log')).open('x') as output:
        process = subprocess.run(['bash', 'gpu/ovx_ssh.sh', command], cwd=REPO,
            input=json.dumps(entry).encode(), stdout=output, stderr=subprocess.STDOUT, timeout=60)
    return dict(label=label, wrapper_exit=process.returncode, finished_unix=time.time(),
        actual_LOADED_claim=False)


if __name__ == '__main__':
    with ThreadPoolExecutor(max_workers=4) as pool:
        results = list(pool.map(dispatch, ARMS))
    print(json.dumps(write(ROOT / 'R186_DISPATCH.json', results), sort_keys=True))
