"""Isolated route queues using the existing qualified private Astra transport."""

import argparse
from contextlib import contextmanager
import json
import os
from pathlib import Path
import shlex
import time
from types import SimpleNamespace

from gpu import orch_math_feedback_uptake_base_broker as existing
from organism_v6 import orch_r107_route_parent_r108 as policy


@contextmanager
def route_digest():
    parent_policy = existing.transport.parent.policy
    previous = parent_policy.digest
    parent_policy.digest = policy.digest
    try:
        yield
    finally:
        parent_policy.digest = previous


def serve(repository, campaign, buffer, receipts, index, ready_sha256, deadline):
    policy.allocation(index)
    policy.require(os.environ.get('CUDA_VISIBLE_DEVICES') == '' and str(buffer).startswith('/tmp/'),
                   'one_bounded_cpu_transport_buffer')
    buffer.mkdir(exist_ok=False)
    receipts.mkdir(parents=True, exist_ok=True)
    store = existing.transport.Store(repository, campaign.parent)
    policy.require(store.shell('sha256sum ' + shlex.quote(str(campaign / 'READY.json'))).stdout.split()[0] == ready_sha256,
                   'exact_lane_ready_binding')
    policy.require(store.exists(campaign / 'PUBLICATION.json'), 'publication_before_parent_dispatch')
    ready = json.loads(store.shell('cat ' + shlex.quote(str(campaign / 'READY.json'))).stdout)
    policy.require(ready['index'] == index, 'lane_style_binding')

    def validate(payload):
        policy.require(payload['style'] == policy.STYLES[index], 'exact_parent_style')
        return policy.validate_parent_payload(payload)

    existing.policy = SimpleNamespace(require=policy.require, validate_parent_payload=validate,
        PARENT_INSTRUCTION=policy.PARENT_INSTRUCTIONS + '\n\nREGISTERED STYLE: ' + policy.STYLE_INSTRUCTIONS[index])
    while time.time() < deadline and not store.exists(campaign / 'TERMINAL.json'):
        for name, digest in ready['provider_files'].items():
            policy.require(existing.transport.parent.sha(repository / name) == digest, 'provider_source_stayed_pinned')
        names = store.shell('find ' + shlex.quote(str(campaign / existing.QUEUE)) +
            ' -maxdepth 1 -name "*.request.json"').stdout.splitlines()
        policy.require(len(names) <= policy.PARENT_CAP, 'four_parent_calls_per_arm')
        for name in sorted(names):
            with route_digest():
                existing.process(store, campaign, Path(name), buffer, receipts, deadline, ready_sha256)
        time.sleep(2)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    for name in ('repository', 'campaign', 'buffer', 'receipts'):
        parser.add_argument('--' + name, type=Path, required=True)
    parser.add_argument('--index', type=int, choices=(2, 3, 6), required=True)
    parser.add_argument('--ready-sha256', required=True)
    parser.add_argument('--deadline', type=float, required=True)
    arguments = parser.parse_args()
    serve(**vars(arguments))
