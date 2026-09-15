"""Own twenty-call Astra queue; raw transcripts archived on-node, no retries."""

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
from organism_v6 import orch_r108_code_parent as policy


QUEUE = 'code_parent_queue'


@contextmanager
def parent_context():
    parent = transport.parent
    previous = parent.policy.validate_parent_payload, parent.policy.digest, parent.INSTRUCTIONS
    parent.policy.validate_parent_payload = policy.validate_parent_payload
    parent.policy.digest = policy.digest
    parent.INSTRUCTIONS = policy.PARENT_INSTRUCTIONS
    try:
        yield
    finally:
        parent.policy.validate_parent_payload, parent.policy.digest, parent.INSTRUCTIONS = previous


def process(store, campaign, request_path, buffer, receipts, deadline, ready_sha256):
    identifier = request_path.name.removesuffix('.request.json')
    policy.require(request_path.parent == campaign / QUEUE
        and re.fullmatch(r'GUIDED_SLEEP_C(?:[1-9]|10)_P[12]', identifier), 'exact_twenty_request_names')
    response_path = request_path.with_name(identifier + '.response.json')
    if store.exists(response_path):
        return
    if store.shell('mkdir ' + shlex.quote(str(request_path.with_suffix('.claim'))), check=False).returncode:
        return
    policy.require(time.time() < deadline and not any(buffer.iterdir()), 'one_bounded_parent_buffer')
    incoming = buffer / 'incoming.json'
    store.copy('NODE:' + str(request_path), incoming)
    request = transport.parent.read(incoming)
    policy.require(request['ready_sha256'] == ready_sha256 and request['id'] == identifier, 'published_request_binding')
    policy.validate_parent_payload(request['payload'])
    policy.require(identifier == f'GUIDED_SLEEP_C{request["payload"]["cycle"]}_P{request["payload"]["episode_index"]}',
        'actual_cycle_episode_binding')
    directory = buffer / identifier
    status, plan, error = 'FAILED', None, None
    try:
        with parent_context():
            plan = transport.strong.evaluate(request, directory, {}, timeout=min(120, deadline-time.time()))
        task = next(row for row in policy.tasks() if row['task_id'] == request['payload']['episodes'][0]['task_id'])
        policy.parent_lesson(plan, task)
        status = 'COMPLETE'
    except Exception as failure:
        error = dict(type=type(failure).__name__)
    directory.mkdir(exist_ok=True)
    if not (directory / 'REQUEST.json').exists():
        shutil.copyfile(incoming, directory / 'REQUEST.json')
    transport.parent.write(directory / 'TRANSPORT_RESULT.json', dict(status=status, error=error,
        request_sha256=transport.parent.sha(incoming), finished_unix=time.time(), no_retry=True))
    archive = store.archive(directory, campaign.name, identifier)
    response = dict(status=status, plan=plan, error=error, request_sha256=transport.parent.sha(incoming), archive=archive)
    local_response = buffer / 'response.json'
    transport.parent.write(local_response, response)
    store.copy(local_response, 'NODE:' + str(response_path) + '.partial')
    verified = store.shell('sha256sum ' + shlex.quote(str(response_path) + '.partial')).stdout.split()[0]
    policy.require(verified == transport.parent.sha(local_response), 'response_transfer_hash')
    store.shell('test ! -e ' + shlex.quote(str(response_path)) + ' && mv ' +
        shlex.quote(str(response_path) + '.partial') + ' ' + shlex.quote(str(response_path)))
    usage = transport.parent.read(directory / 'COMPLETE.json').get('usage') if (directory / 'COMPLETE.json').exists() else None
    if (directory / 'RAW_RESPONSE.json').exists():
        envelope = transport.parent.read(directory / 'RAW_RESPONSE.json')
        usage = envelope.get('usage', usage)
    transport.parent.write(receipts / (identifier + '.json'), dict(status=status, archive=archive,
        response_sha256=verified, request_sha256=response['request_sha256'], provider_usage=usage,
        http_attempts=1 if (directory / 'INVOCATION.json').exists() else 0,
        raw_in_repository=False, no_retry=True))
    shutil.rmtree(directory)
    incoming.unlink()
    local_response.unlink()


def serve(repository, campaign, buffer, receipts, ready_sha256, deadline):
    policy.require(os.environ.get('CUDA_VISIBLE_DEVICES') == '' and str(buffer).startswith('/tmp/'), 'cpu_bounded_buffer')
    buffer.mkdir(exist_ok=False)
    receipts.mkdir(parents=True, exist_ok=True)
    store = transport.Store(repository, campaign.parent)
    observed = store.shell('sha256sum ' + shlex.quote(str(campaign / 'READY.json'))).stdout.split()[0]
    policy.require(observed == ready_sha256 and store.exists(campaign.parent / 'PUBLICATION.json'), 'published_ready_required')
    ready = json.loads(store.shell('cat ' + shlex.quote(str(campaign / 'READY.json'))).stdout)
    while time.time() < deadline and not store.exists(campaign / 'TERMINAL.json'):
        for relative, expected in ready['parent_files'].items():
            policy.require(transport.parent.sha(repository / relative) == expected, 'pinned_provider_source')
        names = store.shell('find ' + shlex.quote(str(campaign / QUEUE)) + ' -maxdepth 1 -name "*.request.json"').stdout.splitlines()
        policy.require(len(names) <= policy.PARENT_CAP, 'twenty_total_parent_calls')
        for name in sorted(names):
            process(store, campaign, Path(name), buffer, receipts, deadline, ready_sha256)
        time.sleep(10)
    transport.parent.write(receipts / 'BROKER_TERMINAL.json', dict(finished_unix=time.time(), status='STOPPED',
        buffer_empty=not any(buffer.iterdir()), provider_retries=0))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    for name in ('repository', 'campaign', 'buffer', 'receipts'):
        parser.add_argument('--'+name, type=Path, required=True)
    parser.add_argument('--ready-sha256', required=True)
    parser.add_argument('--deadline', type=float, required=True)
    serve(**vars(parser.parse_args()))
