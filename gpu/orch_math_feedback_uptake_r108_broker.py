"""Private per-style broker; existing provider, node3-only transcript custody."""

import argparse
import json
import os
from pathlib import Path
import shlex
import subprocess
import time

from gpu import orch_math_feedback_uptake_base_broker as existing
from organism_v6 import orch_math_feedback_uptake_r108 as policy


class Store(existing.transport.Store):
    def shell(self, command, check=True):
        return subprocess.run(['bash', str(self.repository / 'gpu/ovx2_ssh.sh'), command],
            capture_output=True, text=True, timeout=60, check=check)

    def copy(self, source, destination, recursive=False):
        return subprocess.run(['bash', str(self.repository / 'gpu/ovx2_scp.sh')] + (['-r'] if recursive else []) +
            [str(source), str(destination)], capture_output=True, text=True, timeout=90, check=True)


def serve(repository, campaign, buffer, receipts, index, ready_sha256, deadline):
    scope = policy.configured(index)
    scope.require(os.environ.get('CUDA_VISIBLE_DEVICES') == '' and str(buffer).startswith('/tmp/'), 'cpu_bounded_buffer')
    buffer.mkdir(exist_ok=False)
    receipts.mkdir(parents=True, exist_ok=True)
    store = Store(repository, campaign.parent)
    scope.require(store.shell('sha256sum ' + shlex.quote(str(campaign / 'READY.json'))).stdout.split()[0] == ready_sha256, 'ready_binding')
    scope.require(store.exists(campaign / 'PUBLICATION.json'), 'published_allocation')
    ready = json.loads(store.shell('cat ' + shlex.quote(str(campaign / 'READY.json'))).stdout)
    scope.require(ready['index'] == index, 'style_binding')
    for name, digest in ready['provider_files'].items():
        scope.require(existing.transport.parent.sha(repository / name) == digest, 'provider_sources')
    existing.policy = scope
    while time.time() < deadline and not store.exists(campaign / 'TERMINAL.json'):
        names = store.shell('find ' + shlex.quote(str(campaign / existing.QUEUE)) + ' -maxdepth 1 -name "*.request.json"').stdout.splitlines()
        for name in sorted(names):
            existing.process(store, campaign, Path(name), buffer, receipts, deadline, ready_sha256)
        time.sleep(2)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    for name in ('repository', 'campaign', 'buffer', 'receipts'):
        parser.add_argument('--' + name, type=Path, required=True)
    parser.add_argument('--index', type=int, choices=(4, 5), required=True)
    parser.add_argument('--ready-sha256', required=True)
    parser.add_argument('--deadline', type=float, required=True)
    args = parser.parse_args()
    serve(args.repository, args.campaign, args.buffer, args.receipts, args.index, args.ready_sha256, args.deadline)
