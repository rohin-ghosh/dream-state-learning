"""Drain immutable old stages; resume their completed evidence without new budgets."""

import os
from pathlib import Path
import subprocess
import sys
import time

from gpu import orch_route_parent_campaign_run as run


def main():
    root = run.ROOT
    prepared = run.verify(root)
    publication = run.read(root / 'PUBLICATION.json')
    run.require(publication['own_cpu_tests_passed'] and publication['dated_builder_receipt']
        and publication['prepare_sha256'] == run.sha(root / 'PREPARE.json'), 'repair_pre_gpu_gate')
    deadline = run.read(root / 'START.json')['hard_deadline_unix']
    run.write(root / 'REPAIR_ACTIVE.json', dict(started_unix=time.time(), original_deadline=deadline,
        policy='Old immutable stages finish; next old-stage source binding fails before model; no signals sent',
        source_sha256=run.sha(root / 'PREPARE.json')))
    while not (root / 'TERMINAL.json').exists():
        run.require(time.time() < deadline - 360, 'original_deadline')
        time.sleep(2)
    terminal = run.read(root / 'TERMINAL.json')
    run.write(root / 'TERMINAL_ORIGINAL_PRESERVED.json', terminal)
    children = []
    try:
        for arm in run.policy.ARMS:
            output = root / (arm + '_repair_guardian.log')
            with output.open('x') as stream:
                child = subprocess.Popen([sys.executable, '-B', '-m', 'gpu.orch_route_parent_campaign_run',
                    '--phase', 'lane', '--arm', arm, '--resume'], env=dict(os.environ,
                    CUDA_VISIBLE_DEVICES='', ROUTE_PARENT_REPROJECT='1', PYTHONPATH=str(run.TREE)),
                    stdout=stream, stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL, start_new_session=True)
                children.append(child)
                run.write(root / ('REPAIR_LAUNCH_' + arm + '.json'), dict(pid=child.pid, time_unix=time.time()))
        while any(child.poll() is None for child in children):
            run.require(time.time() < deadline - 120, 'original_hard_deadline')
            time.sleep(2)
        run.write(root / 'TERMINAL_REPAIR.json', dict(exit_codes=[child.returncode for child in children],
                  finished_unix=time.time(), original_deadline=deadline, old_calls_replayed=0))
    finally:
        for child in children:
            if child.poll() is None:
                os.killpg(child.pid, 15)
                child.wait(timeout=30)


if __name__ == '__main__':
    main()
