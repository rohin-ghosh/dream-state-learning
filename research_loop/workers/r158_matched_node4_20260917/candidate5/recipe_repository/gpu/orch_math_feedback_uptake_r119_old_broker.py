"""Original fixed R110 provider with new lease custody and no old-request retry."""

import argparse
import fcntl
import json
import os
from pathlib import Path
import shlex

from gpu import orch_math_feedback_uptake_r110_broker as old


def serve(repository, service, index, plan_sha256):
    old.policy.require(index in (1, 2) and os.environ.get('CUDA_VISIBLE_DEVICES') == '', 'cpu_owned_broker')
    lane = Path('/localhome/local-rohing/orch_math_feedback_uptake_r110_20260915_attempt1') / f'campaign_node3_style{index}'
    original_store, original_process = old.previous.Store, old.process
    store = original_store(repository, lane.parent)
    plan_path = lane / 'R119_LEASE_V3/PLAN.json'
    old.policy.require(store.shell('sha256sum ' + shlex.quote(str(plan_path))).stdout.split()[0] == plan_sha256, 'actual_plan')
    plan = json.loads(store.shell('cat ' + shlex.quote(str(plan_path))).stdout)
    old.policy.require(plan['index'] == index and plan['context_only'] and plan['no_replay'], 'same_context_only_life')
    service.mkdir(parents=True, exist_ok=True)
    class LeaseStore(original_store):
        def exists(self, path):
            if Path(path) == lane / 'TERMINAL.json':
                path = lane / 'R119_LEASE_V3/TERMINAL.json'
            return super().exists(path)
    def process(store, campaign, path, *args):
        if str(path.relative_to(lane)) in plan['preserved']:
            return
        return original_process(store, campaign, path, *args)
    with (service / 'BROKER.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        old.previous.Store, old.process = LeaseStore, process
        try:
            old.serve(repository, lane, service / 'buffer', service / 'receipts', index,
                plan['ready_sha256'], plan['clock']['native_deadline_unix'])
        finally:
            old.previous.Store, old.process = original_store, original_process


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--repository', type=Path, required=True)
    parser.add_argument('--service', type=Path, required=True)
    parser.add_argument('--index', type=int, choices=(1, 2), required=True)
    parser.add_argument('--plan-sha256', required=True)
    arguments = parser.parse_args()
    serve(arguments.repository, arguments.service, arguments.index, arguments.plan_sha256)
