"""Isolated R107 queue; reuse verified provider and node-only transcript storage."""

import argparse
from contextlib import contextmanager
import json
import os
from pathlib import Path
import re
import shlex
import shutil
import time

from gpu import orch_math_pipeline_l2_parent_node as transport
from organism_v6 import orch_math_feedback_uptake_base as policy


QUEUE = 'base_parent_queue_r107'


@contextmanager
def parent_context():
    parent = transport.parent
    validator, instructions = parent.policy.validate_parent_payload, parent.INSTRUCTIONS
    parent.policy.validate_parent_payload = policy.validate_parent_payload
    parent.INSTRUCTIONS = policy.PARENT_INSTRUCTION
    try:
        yield
    finally:
        parent.policy.validate_parent_payload, parent.INSTRUCTIONS = validator, instructions


def process(store, campaign, path, buffer, receipts, deadline, ready_sha256):
    policy.require(path.parent == campaign / QUEUE, 'isolated_queue_only')
    identifier = path.name.removesuffix('.request.json')
    policy.require(re.fullmatch(r'GUIDED_SLEEP_C[12]_P[12]', identifier) is not None, 'bounded_parent_identifier')
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
        with parent_context():
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


def serve(repository, campaign, buffer, receipts, ready_sha256, deadline):
    policy.require(os.environ.get('CUDA_VISIBLE_DEVICES') == '' and str(buffer).startswith('/tmp/'), 'cpu_bounded_buffer')
    buffer.mkdir(exist_ok=False)
    receipts.mkdir(parents=True, exist_ok=True)
    store = transport.Store(repository, campaign.parent)
    observed = store.shell('sha256sum ' + shlex.quote(str(campaign / 'READY.json'))).stdout.split()[0]
    policy.require(observed == ready_sha256 and store.exists(campaign / 'PUBLICATION.json'), 'published_ready_required')
    ready = json.loads(store.shell('cat ' + shlex.quote(str(campaign / 'READY.json'))).stdout)
    for relative, digest in ready['provider_files'].items():
        policy.require(transport.parent.sha(repository / relative) == digest, 'bound_provider_and_broker_source')
    while time.time() < deadline and not store.exists(campaign / 'TERMINAL.json'):
        names = store.shell('find ' + shlex.quote(str(campaign / QUEUE)) + ' -maxdepth 1 -name "*.request.json"').stdout.splitlines()
        for name in sorted(names):
            process(store, campaign, Path(name), buffer, receipts, deadline, ready_sha256)
        time.sleep(2)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    for name in ('repository', 'campaign', 'buffer', 'receipts'):
        parser.add_argument('--' + name, type=Path, required=True)
    parser.add_argument('--ready-sha256', required=True)
    parser.add_argument('--deadline', type=float, required=True)
    options = parser.parse_args()
    serve(options.repository, options.campaign, options.buffer, options.receipts, options.ready_sha256, options.deadline)
