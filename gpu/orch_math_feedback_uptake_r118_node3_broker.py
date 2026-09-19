"""Prospective lane0 broker terminal binding; unchanged R110 parent policy."""

import argparse
import fcntl
import json
import os
from pathlib import Path
import shlex

from gpu import orch_math_feedback_uptake_r110_broker as old


LANE = Path('/localhome/local-rohing/orch_math_feedback_uptake_r110_20260915_attempt1/campaign_node3_style0')


def terminal_path(path):
    return LANE/'R118_RECOVERY/TERMINAL.json' if Path(path) == LANE/'TERMINAL.json' else path


def serve(repository, ready_sha256, plan_sha256):
    old.policy.require(os.environ.get('CUDA_VISIBLE_DEVICES') == '', 'cpu_only')
    old.policy.require(not Path('/proc/275602').exists(), 'old_lane0_broker_exited')
    original = old.previous.Store
    store = original(repository, LANE.parent)
    remote = lambda name: json.loads(store.shell('cat '+shlex.quote(str(LANE/name))).stdout)
    ready = remote('R118_RECOVERY/READY.json')
    old.policy.require(ready['passed'] and ready['plan_sha256'] == plan_sha256, 'actual_recovery_cpu_plan')
    old.policy.require(store.shell('sha256sum '+shlex.quote(str(LANE/'R118_RECOVERY/READY.json'))).stdout.split()[0] == ready_sha256, 'exact_recovery_ready')
    plan = remote('R118_RECOVERY/PLAN.json')
    old.policy.require(store.shell('sha256sum '+shlex.quote(str(LANE/'R118_RECOVERY/PLAN.json'))).stdout.split()[0] == plan_sha256, 'exact_recovery_plan')
    old.policy.require(plan['root'] == str(LANE) and plan['no_replay'] and plan['cycle'] == 8, 'same_lane_no_reset')
    class SuccessorStore(original):
        def exists(self, path):
            return super().exists(terminal_path(path))
    with (repository/'BROKER.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        try:
            old.previous.Store = SuccessorStore
            old.serve(repository, LANE, repository/'buffer', repository/'receipts', 0,
                plan['original_activation']['ready_sha256'], plan['original_activation']['native_deadline_unix'])
        finally:
            old.previous.Store = original


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--repository', type=Path, required=True)
    parser.add_argument('--ready-sha256', required=True)
    parser.add_argument('--plan-sha256', required=True)
    args = parser.parse_args()
    serve(args.repository, args.ready_sha256, args.plan_sha256)
