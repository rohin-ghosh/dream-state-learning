"""Own R109 cadence Astra queues; raw transcripts archived on-node, no retries."""

import argparse
from contextlib import contextmanager
import json
import os
from pathlib import Path
import re
import shlex
import shutil
import subprocess
import time

from gpu import orch_math_pipeline_l2_parent_node as transport
from organism_v6 import orch_r108_code_parent_r109 as policy


QUEUE = 'code_parent_queue'
PRINCIPLES = ''


class Store(transport.Store):
    def __init__(self, repository, root, arm):
        super().__init__(repository, root)
        self.wrapper = policy.allocation(arm)['wrapper']

    def shell(self, command, check=True):
        return subprocess.run(['bash', str(self.repository / 'gpu' / (self.wrapper + '_ssh.sh')), command],
            capture_output=True, text=True, timeout=60, check=check)

    def copy(self, source, destination, recursive=False):
        return subprocess.run(['bash', str(self.repository / 'gpu' / (self.wrapper + '_scp.sh'))] +
            (['-r'] if recursive else []) + [str(source), str(destination)],
            capture_output=True, text=True, timeout=90, check=True)


@contextmanager
def parent_context(arm):
    parent = transport.parent
    previous = parent.policy.validate_parent_payload, parent.policy.digest, parent.INSTRUCTIONS
    parent.policy.validate_parent_payload = policy.validate_parent_payload
    parent.policy.digest = policy.digest
    policy.require(bool(PRINCIPLES.strip()),'bound_shared_parenting_principles')
    parent.INSTRUCTIONS = PRINCIPLES+'\n\n'+policy.parent_instructions(arm)
    try:
        yield
    finally:
        parent.policy.validate_parent_payload, parent.policy.digest, parent.INSTRUCTIONS = previous


def process(store, campaign, request_path, buffer, receipts, deadline, ready_sha256, arm):
    identifier = request_path.name.removesuffix('.request.json')
    policy.require(request_path.parent == campaign / QUEUE
        and re.fullmatch(r'GUIDED_SLEEP_C(?:[1-9][0-9]?|100)_(?:P[12]_S[12]|P0_S[123])', identifier), 'exact_reserved_r109_request_names')
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
    policy.require(request['payload']['arm'] == arm, 'exact_broker_arm')
    policy.validate_parent_payload(request['payload'])
    policy.require(identifier == f'GUIDED_SLEEP_C{request["payload"]["cycle"]}_P{request["payload"]["episode_index"]}_S{request["payload"]["segment"]}',
        'actual_cycle_episode_binding')
    directory = buffer / identifier
    status, plan, error = 'FAILED', None, None
    try:
        with parent_context(arm):
            plan = transport.strong.evaluate(request, directory, {}, timeout=min(120, deadline-time.time()))
        task = policy.meta_task(arm,request['payload']['cycle']) if request['payload']['mode']=='META_DIALOGUE' else next(
            row for row in policy.tasks(arm) if row['task_id'] == request['payload']['episodes'][0]['task_id'])
        policy.prior.parent_lesson(plan, task)
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


def serve(repository, campaign, buffer, receipts, ready_sha256, deadline, arm, principles):
    global PRINCIPLES
    policy.require(os.environ.get('CUDA_VISIBLE_DEVICES') == '' and str(buffer).startswith('/tmp/'), 'cpu_bounded_buffer')
    buffer.mkdir(exist_ok=False)
    receipts.mkdir(parents=True, exist_ok=True)
    store = Store(repository, campaign.parent, arm)
    observed = store.shell('sha256sum ' + shlex.quote(str(campaign / 'READY.json'))).stdout.split()[0]
    policy.require(observed == ready_sha256 and store.exists(campaign.parent / 'PUBLICATION.json'), 'published_ready_required')
    ready = json.loads(store.shell('cat ' + shlex.quote(str(campaign / 'READY.json'))).stdout)
    policy.require(transport.parent.sha(principles)==ready['principles_sha256'],'same_shared_principles_hash')
    PRINCIPLES=principles.read_text()
    while time.time() < deadline and not store.exists(campaign / 'TERMINAL.json'):
        for relative, expected in ready['parent_files'].items():
            policy.require(transport.parent.sha(repository / relative) == expected, 'pinned_provider_source')
        names = store.shell('find ' + shlex.quote(str(campaign / QUEUE)) + ' -maxdepth 1 -name "*.request.json"').stdout.splitlines()
        policy.require(len(names) <= policy.allocation(arm)['parent_cap'], 'new_r109_total_parent_cap')
        for name in sorted(names):
            process(store, campaign, Path(name), buffer, receipts, deadline, ready_sha256, arm)
        time.sleep(10)
    transport.parent.write(receipts / 'BROKER_TERMINAL.json', dict(finished_unix=time.time(), status='STOPPED',
        buffer_empty=not any(buffer.iterdir()), provider_retries=0))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    for name in ('repository', 'campaign', 'buffer', 'receipts'):
        parser.add_argument('--'+name, type=Path, required=True)
    parser.add_argument('--ready-sha256', required=True)
    parser.add_argument('--deadline', type=float, required=True)
    parser.add_argument('--arm', choices=tuple(policy.ARMS), required=True)
    parser.add_argument('--principles',type=Path,required=True)
    serve(**vars(parser.parse_args()))
