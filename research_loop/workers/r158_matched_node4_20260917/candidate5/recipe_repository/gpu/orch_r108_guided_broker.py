"""CPU R108 queue broker; no provider dispatch without a hash-bound allocation.

Allocation schema ORCH_R108_GUIDED_BROKER_ALLOCATION_V1 requires campaign,
ready_sha256, source_files, tasks_by_request, deadline_unix,
dispatch_cutoff_unix, max_parent_calls=4, attempts_per_request=1 and
max_output_tokens=4096. tasks_by_request maps all four cycleN_episodeN IDs
to exact public {id, question} TRAIN tasks. --source-pins prints the loaded
runtime inventory without contacting a node/provider. Allocation and READY
live beside PUBLICATION.json on the node; --allocation-sha256 binds the
allocation before serving. Run only from an immutable copy outside Git.

Claims survive failures/restarts. A claimed request is never retried, and a
failed episode stops the sequence. Archive/response transfer failures leave
the sole /tmp buffer intact for manual recovery, never redispatch. Raw bytes
are removed locally only after node archive AND response hashes verify.
"""

import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import re
import shlex
import shutil
import signal
import sys
import tempfile
import time
from types import FunctionType

from gpu import orch_math_pipeline_l2_parent_node as transport
from gpu import orch_route_parent_campaign_providers as provider
from organism_v6 import orch_r108_guided as policy


ALLOCATION_SCHEMA = 'ORCH_R108_GUIDED_BROKER_ALLOCATION_V1'
IDENTIFIERS = tuple(f'cycle{cycle}_episode{episode}'
    for cycle in range(1, policy.CYCLES + 1)
    for episode in range(1, policy.EPISODES + 1))
OUTPUT_CAP = 4096
ROOT = Path(__file__).resolve().parents[1]


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def source_pins():
    files = {Path(__file__).resolve()}
    for module in tuple(sys.modules.values()):
        filename = getattr(module, '__file__', None)
        if filename:
            path = Path(filename).resolve()
            if path.is_relative_to(ROOT) and path.suffix == '.py':
                if path.relative_to(ROOT).parts[0] in ('gpu', 'organism_v6'):
                    files.add(path)
    files.update(ROOT / 'gpu' / name for name in ('a100_ssh.sh', 'a100_scp.sh'))
    return {str(path.relative_to(ROOT)): sha(path) for path in sorted(files)}


LOADED_PINS = source_pins()


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        policy.require(key not in result, 'duplicate_json_key')
        result[key] = value
    return result


def loads(raw):
    def invalid_constant(value):
        raise ValueError('nonfinite_json_constant')
    return json.loads(raw, object_pairs_hook=unique_object, parse_constant=invalid_constant)


def write(path, value):
    path.write_text(json.dumps(value, sort_keys=True, indent=2, allow_nan=False) + '\n')


def validate_allocation(allocation, campaign, now):
    policy.require(set(allocation) == {'schema', 'campaign', 'ready_sha256', 'source_files',
        'tasks_by_request', 'deadline_unix', 'dispatch_cutoff_unix', 'max_parent_calls',
        'attempts_per_request', 'max_output_tokens'}, 'allocation_schema')
    policy.require(allocation['schema'] == ALLOCATION_SCHEMA
        and allocation['campaign'] == str(campaign), 'allocation_campaign')
    policy.require(campaign.is_absolute() and '..' not in campaign.parts
        and re.fullmatch(r'/[a-zA-Z0-9_./-]+', str(campaign)), 'native_campaign_path')
    for name, expected in (('max_parent_calls', 4), ('attempts_per_request', 1),
            ('max_output_tokens', OUTPUT_CAP)):
        policy.require(type(allocation[name]) is int and allocation[name] == expected, 'fixed_call_bounds')
    for name in ('deadline_unix', 'dispatch_cutoff_unix'):
        policy.require(type(allocation[name]) in (int, float)
            and math.isfinite(allocation[name]), 'finite_deadline')
    policy.require(now < allocation['dispatch_cutoff_unix']
        <= allocation['deadline_unix'] - 120, 'dispatch_deadline_margin')
    policy.require(isinstance(allocation['ready_sha256'], str)
        and re.fullmatch('[a-f0-9]{64}', allocation['ready_sha256']), 'ready_hash')
    policy.require(allocation['source_files'] == LOADED_PINS, 'loaded_source_allocation_binding')
    tasks = allocation['tasks_by_request']
    policy.require(isinstance(tasks, dict) and set(tasks) == set(IDENTIFIERS), 'four_registered_requests')
    for task in tasks.values():
        policy.require(isinstance(task, dict) and set(task) == {'id', 'question'}, 'public_task_schema')
        policy.validate_task(dict(task, split='TRAIN'))


def validate_request(request, identifier, allocation):
    policy.require(identifier in IDENTIFIERS, 'bounded_request_id')
    policy.require(isinstance(request, dict)
        and set(request) == {'id', 'payload', 'payload_sha256', 'task'}, 'request_envelope_schema')
    policy.validate_parent_payload(request['payload'])
    payload = request['payload']
    policy.require(request['id'] == identifier
        == f"cycle{payload['cycle']}_episode{payload['episode']}", 'request_cycle_episode_join')
    policy.require(request['task'] == payload['task']
        == allocation['tasks_by_request'][identifier], 'registered_train_task_join')
    policy.require(request['payload_sha256'] == policy.digest(payload), 'request_payload_hash')


def parse_response(envelope, task):
    policy.require(isinstance(envelope, dict) and envelope.get('model') == policy.STRONG,
        'actual_strong_model_identity')
    policy.require(envelope.get('status') == 'completed' and not envelope.get('error')
        and not envelope.get('incomplete_details'), 'complete_strong_response')
    output = envelope.get('output')
    policy.require(isinstance(output, list) and all(isinstance(item, dict)
        and item.get('type') in ('reasoning', 'message') for item in output), 'no_provider_tool_calls')
    texts = []
    for item in output:
        if item['type'] == 'message':
            policy.require(item.get('role') == 'assistant', 'assistant_reply_only')
            content = item.get('content')
            policy.require(isinstance(content, list) and all(isinstance(part, dict)
                and part.get('type') == 'output_text' and isinstance(part.get('text'), str)
                for part in content), 'text_reply_only')
            texts.extend(part['text'] for part in content)
    policy.require(len(texts) == 1, 'one_parent_reply')
    usage = envelope.get('usage')
    policy.require(isinstance(usage, dict) and all(type(usage.get(key)) is int
        and usage[key] >= 0 for key in ('input_tokens', 'output_tokens', 'total_tokens')),
        'actual_usage_required')
    policy.require(0 < usage['output_tokens'] <= OUTPUT_CAP, 'observed_output_cap')
    raw = texts[0]
    if raw.startswith('```json\n') and raw.endswith('\n```'):
        raw = raw[8:-4]
    plan = loads(raw)
    policy.require(isinstance(plan, dict), 'plan_object_required')
    policy.validate_plan(plan, [dict(task, split='TRAIN')])
    return plan, envelope['model'], usage


def evaluate(request, directory, deadline):
    policy.require(time.time() < deadline - 120, 'provider_dispatch_margin')
    policy.require(signal.getitimer(signal.ITIMER_REAL) == (0.0, 0.0), 'no_existing_provider_timer')
    def timeout(signum, frame):
        raise TimeoutError('provider_total_wall_timeout')
    previous_handler = signal.signal(signal.SIGALRM, timeout)
    namespace = dict(provider.strong.__globals__)
    namespace['parse_strong'] = lambda envelope: parse_response(envelope, request['task'])
    actor = FunctionType(provider.strong.__code__, namespace, provider.strong.__name__,
        provider.strong.__defaults__, provider.strong.__closure__)
    signal.setitimer(signal.ITIMER_REAL, min(120, deadline - time.time()))
    try:
        actor(json.dumps(request['payload'], sort_keys=True, allow_nan=False), directory,
            deadline, instruction=policy.PARENT_INSTRUCTION)
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, previous_handler)
        captured = directory / 'stdout.json'
        if captured.exists():
            captured.rename(directory / 'RAW_RESPONSE.json')
    return parse_response(loads((directory / 'RAW_RESPONSE.json').read_text()), request['task'])


def remote_hash(store, path):
    return store.shell('sha256sum ' + shlex.quote(str(path))).stdout.split()[0]


def native_archive(store, directory, destination):
    expected = transport.manifest(directory)
    policy.require(bool(expected), 'nonempty_archive')
    store.shell('mkdir -p ' + shlex.quote(str(destination)))
    for relative, digest in expected.items():
        policy.require('/' not in relative, 'flat_bounded_transcript')
        target = destination / relative
        if not store.exists(target):
            store.copy(directory / relative, 'NODE:' + str(target))
        policy.require(remote_hash(store, target) == digest, 'node_archive_hash_mismatch')
    return dict(remote_root=str(destination), files=expected, node_only=True, all_verified=True)


def publish_response(store, response, destination):
    partial = Path(str(destination) + '.partial')
    policy.require(not store.exists(destination) and not store.exists(partial), 'no_response_overwrite')
    store.copy(response, 'NODE:' + str(partial))
    policy.require(remote_hash(store, partial) == sha(response), 'response_transfer_hash')
    store.shell('test ! -e ' + shlex.quote(str(destination)) + ' && mv '
        + shlex.quote(str(partial)) + ' ' + shlex.quote(str(destination)))
    policy.require(remote_hash(store, destination) == sha(response), 'published_response_hash')


def verify_runtime(store, campaign, allocation, allocation_sha256):
    policy.require(remote_hash(store, campaign / 'PARENT_BROKER_ALLOCATION.json')
        == allocation_sha256, 'immutable_allocation_hash')
    policy.require(remote_hash(store, campaign / 'READY.json')
        == allocation['ready_sha256'], 'immutable_ready_hash')
    policy.require(store.exists(campaign / 'PUBLICATION.json'), 'published_allocation_required')
    policy.require(all(sha(ROOT / name) == digest for name, digest in LOADED_PINS.items()),
        'runtime_source_changed')


def process(store, campaign, identifier, buffer, allocation, allocation_sha256, actor=evaluate):
    policy.require(identifier in IDENTIFIERS, 'bounded_request_id')
    if time.time() >= allocation['dispatch_cutoff_unix']:
        return 'CUTOFF'
    verify_runtime(store, campaign, allocation, allocation_sha256)
    queue = campaign / 'parent_queue'
    request_path = queue / (identifier + '.request.json')
    response_path = queue / (identifier + '.response.json')
    if store.exists(response_path):
        return 'EXISTING'
    position = IDENTIFIERS.index(identifier)
    if position:
        prior_path = queue / (IDENTIFIERS[position - 1] + '.response.json')
        if not store.exists(prior_path):
            return 'WAITING'
        prior = loads(store.shell('cat ' + shlex.quote(str(prior_path))).stdout)
        policy.require(prior.get('status') == 'COMPLETE', 'previous_episode_failed_no_next_parent')
    if not store.exists(request_path):
        return 'WAITING'
    policy.require(not any(buffer.iterdir()), 'one_bounded_local_buffer')
    ledger = campaign / 'parent_broker_r108'
    claim = ledger / (identifier + '.claim')
    if store.shell('mkdir ' + shlex.quote(str(claim)), check=False).returncode:
        return 'CLAIMED_NO_RETRY'
    directory = buffer / identifier
    directory.mkdir()
    incoming = directory / 'REQUEST.json'
    policy.require(int(store.shell('stat -c %s ' + shlex.quote(str(request_path))).stdout)
        <= 1024 * 1024, 'bounded_request_packet')
    store.copy('NODE:' + str(request_path), incoming)
    policy.require(sha(incoming) == remote_hash(store, request_path), 'request_transfer_hash')
    write(directory / 'RESERVATION.json', dict(id=identifier, allocation_sha256=allocation_sha256,
        request_sha256=sha(incoming), reserved_unix=time.time(), maximum_attempts=1,
        deadline_unix=allocation['deadline_unix'], source_files=LOADED_PINS))
    native_archive(store, directory, claim)
    status, plan, actual_model, usage, error = 'FAILED', None, None, None, None
    request = None
    try:
        policy.require(incoming.stat().st_size <= 1024 * 1024, 'bounded_request_packet')
        request = loads(incoming.read_text())
        validate_request(request, identifier, allocation)
        write(directory / 'PAYLOAD.json', request['payload'])
        verify_runtime(store, campaign, allocation, allocation_sha256)
        policy.require(remote_hash(store, request_path) == sha(incoming), 'immutable_request_hash')
        policy.require(time.time() < allocation['dispatch_cutoff_unix'], 'dispatch_cutoff')
        actor(request, directory, allocation['deadline_unix'])
        plan, actual_model, usage = parse_response(
            loads((directory / 'RAW_RESPONSE.json').read_text()), request['task'])
        write(directory / 'PLAN.json', plan)
        status = 'COMPLETE'
    except Exception as failure:
        code = str(failure)
        error = dict(type=type(failure).__name__,
            code=code if re.fullmatch('[a-z0-9_]{1,100}', code) else 'captured_failure_no_retry')
    write(directory / 'TRANSPORT_RESULT.json', dict(status=status, actual_model=actual_model,
        usage=usage, error=error, completed_unix=time.time(), allocation_sha256=allocation_sha256,
        provider_dispatch_recorded=(directory / 'DISPATCH.json').exists(), retry=False))
    receipt = native_archive(store, directory, campaign / 'parent_transcripts' / identifier)
    if status == 'COMPLETE':
        receipt.update(payload_sha256=policy.digest(request['payload']), plan_sha256=policy.digest(plan))
    response = dict(id=identifier, status=status, plan=plan, actual_model=actual_model,
        transcript_receipt=receipt, error=error, allocation_sha256=allocation_sha256,
        request_sha256=sha(incoming))
    result_directory = buffer / 'result'
    result_directory.mkdir()
    local_response = result_directory / 'response.json'
    write(local_response, response)
    native_archive(store, result_directory, ledger / (identifier + '.result'))
    publish_response(store, local_response, response_path)
    shutil.rmtree(directory)
    shutil.rmtree(result_directory)
    return status


def serve(repository, campaign, allocation_sha256, buffer_parent=Path('/tmp')):
    policy.require(repository.resolve() == ROOT and os.environ.get('CUDA_VISIBLE_DEVICES') == '',
        'cpu_pinned_repository_required')
    policy.require(not (ROOT / '.git').exists(), 'immutable_runtime_outside_worktree_required')
    for name, module in tuple(sys.modules.items()):
        filename = getattr(module, '__file__', None)
        if filename and name.startswith(('gpu.', 'organism_v6.')):
            policy.require(Path(filename).resolve().is_relative_to(ROOT), 'no_external_source_imports')
    policy.require(buffer_parent.resolve().is_relative_to(Path('/tmp')),
        'temporary_transport_outside_repository')
    policy.require(re.fullmatch('[a-f0-9]{64}', allocation_sha256), 'allocation_hash_required')
    store = transport.Store(repository, campaign.parent)
    raw = store.shell('cat ' + shlex.quote(str(campaign / 'PARENT_BROKER_ALLOCATION.json'))).stdout
    policy.require(hashlib.sha256(raw.encode()).hexdigest() == allocation_sha256, 'allocation_bytes_hash')
    allocation = loads(raw)
    validate_allocation(allocation, campaign, time.time())
    verify_runtime(store, campaign, allocation, allocation_sha256)
    ledger = campaign / 'parent_broker_r108'
    store.shell('mkdir -p ' + shlex.quote(str(ledger)))
    lock = ledger / 'RUNNER.lock'
    policy.require(store.shell('mkdir ' + shlex.quote(str(lock)), check=False).returncode == 0,
        'single_native_broker_lock')
    buffer = Path(tempfile.mkdtemp(prefix='orch_r108_guided_broker_', dir=buffer_parent))
    try:
        while time.time() < allocation['dispatch_cutoff_unix']:
            if store.exists(campaign / 'TERMINAL.json'):
                break
            states = []
            for identifier in IDENTIFIERS:
                state = process(store, campaign, identifier, buffer, allocation, allocation_sha256)
                states.append(state)
                if state in ('FAILED', 'CLAIMED_NO_RETRY', 'CUTOFF'):
                    break
            if 'FAILED' in states or all(state == 'EXISTING' for state in states):
                break
            if 'CLAIMED_NO_RETRY' in states:
                raise ValueError('existing_claim_requires_manual_receipt_recovery_no_redispatch')
            time.sleep(2)
    finally:
        if not any(buffer.iterdir()):
            buffer.rmdir()
        store.shell('rmdir ' + shlex.quote(str(lock)))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source-pins', action='store_true')
    parser.add_argument('--repository', type=Path, default=ROOT)
    parser.add_argument('--campaign', type=Path)
    parser.add_argument('--allocation-sha256')
    parser.add_argument('--buffer-parent', type=Path, default=Path('/tmp'))
    options = parser.parse_args()
    if options.source_pins:
        print(json.dumps(LOADED_PINS, sort_keys=True, indent=2))
    else:
        if not options.campaign or not options.allocation_sha256:
            parser.error('--campaign and --allocation-sha256 are required to serve')
        serve(options.repository, options.campaign, options.allocation_sha256, options.buffer_parent)
