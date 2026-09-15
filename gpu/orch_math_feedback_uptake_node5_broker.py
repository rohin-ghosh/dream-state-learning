"""Node5 private Astra transport; reuse bound R110 requests and verified custody."""

import argparse
from pathlib import Path
import subprocess

from gpu import orch_math_feedback_uptake_r110_broker as reusable
from organism_v6 import orch_math_feedback_uptake_node5 as policy


class Store(reusable.previous.Store):
    def shell(self, command, check=True):
        return subprocess.run(['bash', str(self.repository / 'gpu/ovx3_ssh.sh'), command],
            capture_output=True, text=True, timeout=60, check=check)

    def copy(self, source, destination, recursive=False):
        return subprocess.run(['bash', str(self.repository / 'gpu/ovx3_scp.sh')] + (['-r'] if recursive else []) +
            [str(source), str(destination)], capture_output=True, text=True, timeout=90, check=True)


def serve(repository, campaign, buffer, receipts, index, ready_sha256, deadline):
    policy.require(campaign.parent.name == 'orch_math_feedback_uptake_node5_20260915_attempt1'
        and campaign.name == f'campaign_node5_style{index}', 'node5_only_transport')
    reusable.previous.Store = Store
    reusable.policy = policy
    reusable.serve(repository, campaign, buffer, receipts, index, ready_sha256, deadline)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    for name in ('repository', 'campaign', 'buffer', 'receipts'):
        parser.add_argument('--' + name, type=Path, required=True)
    parser.add_argument('--index', type=int, choices=(2, 3), required=True)
    parser.add_argument('--ready-sha256', required=True)
    parser.add_argument('--deadline', type=float, required=True)
    args = parser.parse_args()
    serve(args.repository, args.campaign, args.buffer, args.receipts, args.index, args.ready_sha256, args.deadline)
