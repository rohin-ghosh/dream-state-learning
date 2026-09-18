"""Private Astra transport; one bounded VM buffer and verified node archives."""

import argparse
import json
import os
from pathlib import Path
import re
import shlex
import shutil
import time

from gpu import orch_math_feedback_uptake_r108_broker as previous
from organism_v6 import orch_math_feedback_uptake_r110 as policy


transport = previous.existing.transport
QUEUE = 'r110_parent_queue'


def process(store, campaign, path, buffer, receipts, index, deadline, ready_sha256):
    policy.require(path.parent == campaign / QUEUE, 'private_queue')
    identifier = path.name.removesuffix('.request.json')
    match = re.fullmatch(r'GUIDED_SLEEP_C(\d{3})_T(\d{3})', identifier)
    policy.require(match and 1 <= int(match[1]) <= policy.CYCLES and policy.due(index, int(match[2])), 'bounded_parent_id')
    response_path = path.with_name(identifier + '.response.json')
    if store.exists(response_path):
        return
    if store.shell('mkdir ' + shlex.quote(str(path.with_suffix('.claim'))), check=False).returncode:
        return
    policy.require(not any(buffer.iterdir()), 'single_bounded_buffer')
    incoming = buffer / 'incoming.json'
    store.copy('NODE:' + str(path), incoming)
    request = transport.parent.read(incoming)
    policy.require(request['ready_sha256'] == ready_sha256 and request['id'] == identifier, 'bound_request')
    policy.require(request['payload']['index'] == index, 'bound_lane')
    directory = buffer / identifier
    status, plan, error = 'FAILED', None, None
    validator, instructions = transport.parent.policy.validate_parent_payload, transport.parent.INSTRUCTIONS
    try:
        transport.parent.policy.validate_parent_payload = policy.validate_parent_payload
        transport.parent.INSTRUCTIONS = policy.INSTRUCTION
        plan = transport.strong.evaluate(request, directory, {}, timeout=min(120, max(1, deadline - time.time())))
        policy.validate_plan(plan, request['payload']['episodes'][0]['task_id'])
        status = 'COMPLETE'
    except Exception as failure:
        error = dict(type=type(failure).__name__, message=str(failure))
    finally:
        transport.parent.policy.validate_parent_payload, transport.parent.INSTRUCTIONS = validator, instructions
    directory.mkdir(exist_ok=True)
    if not (directory / 'REQUEST.json').exists():
        shutil.copyfile(incoming, directory / 'REQUEST.json')
    transport.parent.write(directory / 'TRANSPORT_RESULT.json', dict(status=status, error=error,
        request_sha256=transport.parent.sha(incoming), finished_unix=time.time()))
    archive = store.archive(directory, campaign.name, identifier)
    result = dict(status=status, plan=plan, error=error, request_sha256=transport.parent.sha(incoming), archive=archive)
    local = buffer / 'response.json'
    transport.parent.write(local, result)
    store.copy(local, 'NODE:' + str(response_path) + '.partial')
    observed = store.shell('sha256sum ' + shlex.quote(str(response_path) + '.partial')).stdout.split()[0]
    policy.require(observed == transport.parent.sha(local), 'response_transfer_verified')
    store.shell('test ! -e ' + shlex.quote(str(response_path)) + ' && mv ' + shlex.quote(str(response_path) + '.partial') + ' ' + shlex.quote(str(response_path)))
    transport.parent.write(receipts / f'{identifier}.json', dict(status=status, archive=archive,
        response_sha256=observed, request_sha256=result['request_sha256'], raw_in_repository=False))
    shutil.rmtree(directory)
    incoming.unlink()
    local.unlink()


def serve(repository, campaign, buffer, receipts, index, ready_sha256, deadline):
    policy.require(index in policy.DEVICES and os.environ.get('CUDA_VISIBLE_DEVICES') == ''
        and str(buffer).startswith('/tmp/'), 'cpu_broker_scope')
    buffer.mkdir(exist_ok=False)
    receipts.mkdir(parents=True, exist_ok=True)
    store = previous.Store(repository, campaign.parent)
    policy.require(store.shell('sha256sum ' + shlex.quote(str(campaign / 'READY.json'))).stdout.split()[0] == ready_sha256, 'ready_hash')
    ready = json.loads(store.shell('cat ' + shlex.quote(str(campaign / 'READY.json'))).stdout)
    policy.require(ready['index'] == index and store.exists(campaign / 'PUBLICATION.json'), 'published_lane')
    policy.bind_principles(repository / 'research_notes/PARENTING_PRINCIPLES_ROHIN_2026-09-15.md', ready['principles_sha256'])
    for name, digest in ready['provider_files'].items():
        policy.require(transport.parent.sha(repository / name) == digest, 'provider_source')
    while time.time() < deadline and not store.exists(campaign / 'TERMINAL.json'):
        names = store.shell('find ' + shlex.quote(str(campaign / QUEUE)) + ' -maxdepth 1 -name "*.request.json"').stdout.splitlines()
        for name in sorted(names):
            process(store, campaign, Path(name), buffer, receipts, index, deadline, ready_sha256)
        time.sleep(5)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    for name in ('repository', 'campaign', 'buffer', 'receipts'):
        parser.add_argument('--' + name, type=Path, required=True)
    parser.add_argument('--index', type=int, choices=(0, 1, 2), required=True)
    parser.add_argument('--ready-sha256', required=True)
    parser.add_argument('--deadline', type=float, required=True)
    args = parser.parse_args()
    serve(args.repository, args.campaign, args.buffer, args.receipts, args.index, args.ready_sha256, args.deadline)
