"""Isolated route queues using the existing qualified private Astra transport."""

import argparse
from contextlib import contextmanager
import json
import os
import re
import shutil
from pathlib import Path
import shlex
import time
from types import SimpleNamespace

from gpu.orch_r107_route_parent_long_protocol import parsing_context

from gpu import orch_math_feedback_uptake_base_broker as existing
from organism_v6 import orch_r107_route_parent_long as policy


@contextmanager
def route_digest():
    parent_policy = existing.transport.parent.policy
    previous = parent_policy.digest
    parent_policy.digest = policy.digest
    try:
        yield
    finally:
        parent_policy.digest = previous


transport = existing.transport


def process(store, campaign, path, buffer, receipts, deadline, ready_sha256):
    policy.require(path.parent == campaign / existing.QUEUE, 'isolated_queue_only')
    identifier = path.name.removesuffix('.request.json')
    policy.require(re.fullmatch(r'GUIDED_SLEEP_C(?:[1-9]|10)_P[12]', identifier) is not None, 'bounded_parent_identifier')
    response_path = path.with_name(identifier + '.response.json')
    if store.exists(response_path):
        return
    if store.shell('mkdir ' + shlex.quote(str(path.with_suffix('.claim'))), check=False).returncode:
        return
    policy.require(not any(buffer.iterdir()), 'one_bounded_local_parent_buffer')
    incoming = buffer / 'incoming.json'
    store.copy('NODE:' + str(path), incoming)
    request = transport.parent.read(incoming)
    policy.require(request['ready_sha256'] == ready_sha256, 'registered_request')
    directory = buffer / identifier
    status, plan, error = 'FAILED', None, None
    try:
        with existing.parent_context(), parsing_context():
            plan = transport.strong.evaluate(request, directory, {}, timeout=min(120, deadline - time.time()))
        status = 'COMPLETE'
    except Exception as failure:
        error = dict(type=type(failure).__name__, message=str(failure))
    directory.mkdir(exist_ok=True)
    if not (directory / 'REQUEST.json').exists():
        shutil.copyfile(incoming, directory / 'REQUEST.json')
    transport.parent.write(directory / 'TRANSPORT_RESULT.json', dict(status=status, error=error,
        request_sha256=transport.parent.sha(incoming), finished_unix=time.time()))
    archive = store.archive(directory, campaign.name, identifier)
    response = dict(status=status, plan=plan, error=error, request_sha256=transport.parent.sha(incoming), archive=archive)
    local_response = buffer / 'response.json'
    transport.parent.write(local_response, response)
    store.copy(local_response, 'NODE:' + str(response_path) + '.partial')
    verified = store.shell('sha256sum ' + shlex.quote(str(response_path) + '.partial')).stdout.split()[0]
    policy.require(verified == transport.parent.sha(local_response), 'response_transfer_hash')
    store.shell('test ! -e ' + shlex.quote(str(response_path)) + ' && mv ' + shlex.quote(str(response_path) + '.partial') + ' ' + shlex.quote(str(response_path)))
    transport.parent.write(receipts / (identifier + '.json'), dict(status=status, archive=archive,
        response_sha256=verified, request_sha256=response['request_sha256'], raw_in_repository=False))
    shutil.rmtree(directory)
    incoming.unlink()
    local_response.unlink()


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
        policy.require(len(names) <= policy.PARENT_CAP, 'twenty_parent_calls_per_long_arm')
        for name in sorted(names):
            with route_digest():
                process(store, campaign, Path(name), buffer, receipts, deadline, ready_sha256)
        time.sleep(2)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    for name in ('repository', 'campaign', 'buffer', 'receipts'):
        parser.add_argument('--' + name, type=Path, required=True)
    parser.add_argument('--index', type=int, choices=(1, 5), required=True)
    parser.add_argument('--ready-sha256', required=True)
    parser.add_argument('--deadline', type=float, required=True)
    arguments = parser.parse_args()
    serve(**vars(arguments))
