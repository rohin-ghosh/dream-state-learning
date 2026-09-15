"""One explicit R109 successor after a useful R108 life naturally terminates."""

import argparse
from datetime import datetime,timezone
import json
import os
from pathlib import Path
import time

from gpu import orch_r109_route_ops as operations


def wait(lane):
    assert lane in ('a100_1','a100_5')
    assert os.environ.get('CUDA_VISIBLE_DEVICES')==''
    root=operations.ROOTS[lane]
    store=operations.Store(operations.REPOSITORY,root,lane)
    prior=Path('/localhome/local-rohing/orch_r107_route_parent_20260915_attempt3_long')/('campaign_route_parent_'+lane[-1])
    target=operations.ANALYSIS/lane
    while time.time()<operations.run.END-300:
        if (target/'HOLD_SUCCESSOR.json').exists():
            return
        ready=store.exists(root/('campaign_'+lane)/'READY.json')
        released=store.exists(prior/'TERMINAL.json') and store.exists(prior/'RELEASE.json')
        operations.run.write(target/'SUCCESSOR_STATUS.json',dict(lane=lane,controller_pid=os.getpid(),
            observed_utc=datetime.now(timezone.utc).isoformat(),ready=ready,old_release_present=released,
            no_gpu_or_owner_signal=True,no_reservation_claim=True,hard_deadline_unix=operations.run.END))
        if ready and released:
            operations.launch(lane)
            return
        time.sleep(20)


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--lane',required=True,choices=('a100_1','a100_5'))
    wait(parser.parse_args().lane)
