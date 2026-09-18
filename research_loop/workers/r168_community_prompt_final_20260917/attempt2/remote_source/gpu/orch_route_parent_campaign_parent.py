"""Tool-free, recorded existing-provider broker; no held artifacts transferred."""

import argparse
import fcntl
import json
import os
from pathlib import Path
import re
import signal
import subprocess
import time

from gpu import orch_l2_long_backend as backend
from gpu.orch_l2_shared_run import spend, write
from organism_v6 import orch_route_parent_campaign as policy


SYSTEM = ('You are a training-wheels route-learning parent, supportive and positive. '
          'Short horizon: reason only about the current provided episode, not hidden tests. '
          'Scaffold observations and ask the learner to reason; do not supply a gold route. '
          'For consolidation, help distinguish outcome evidence from failed attempts. '
          'Failures are not correct answers. Never invent observations. '
          'Return only JSON with speak (boolean), message (string, at most 90 words), '
          'rationale (string). If silent, message must be empty. No tools or filesystem access.')


def evaluate(request, directory, deadline):
    supplied = dict(request['payload'])
    cell = supplied.pop('cell')
    policy.require(cell == policy.CELL, 'fixed_first_cell')
    payload = policy.parent_payload(supplied, cell)
    directory.mkdir(parents=True, exist_ok=False)
    prompt = json.dumps(payload, sort_keys=True)
    (directory / 'prompt.txt').write_text(prompt)
    instruction = SYSTEM
    if cell != dict(style='training-wheels', horizon='short', tone='supportive-positive', provider='existing_claude_cli'):
        instruction = ('You are a route-learning parent. Parenting style: ' + cell['style'] +
            '. Tone: ' + cell['tone'] + '. Horizon: ' + cell['horizon'] +
            '. Micromanaging means concrete process checks; creative means alternate grounded strategies; '
            'training-wheels means scaffolding with fading assistance. Harsh-critical critiques the reasoning, '
            'never the learner personally. Long horizon uses the supplied own-training history only; '
            'short horizon focuses on this episode. Never invent observations or supply a gold route. '
            'Failed attempts are not correct answers. Return only JSON with speak (boolean), '
            'message (string, at most90words), rationale (string); if silent message is empty. No tools.')
    (directory / 'system.txt').write_text(instruction)
    if cell['provider'] != 'existing_claude_cli':
        from gpu import orch_route_parent_campaign_providers as providers

        policy.require(cell['provider'] in (providers.STRONG, providers.SMALLER), 'qualified_provider_only')
        selected = providers.strong if cell['provider'] == providers.STRONG else providers.smaller
        response, model, usage = selected(prompt, directory, min(time.time() + 180, deadline), instruction)
        write(directory / 'RECEIPT.json', dict(verified=True, model=model, model_usage=usage,
            request_sha256=policy.digest(request), response_sha256=policy.digest(response),
            finished_unix=time.time(), transcript_quarantined_from_ongoing_L1=True))
        return response
    command = backend.command()
    command[command.index('--system-prompt') + 1] = instruction
    cutoff = min(time.time() + 180, deadline)
    with backend.LOCK_PATH.open('a') as lock:
        while True:
            policy.require(time.time() < cutoff, 'parent_lock_deadline')
            try:
                fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
                break
            except BlockingIOError:
                time.sleep(0.25)
        policy.require(backend.available_memory() >= backend.MIN_AVAILABLE_BYTES, 'parent_memory_floor')
        write(directory / 'DISPATCH.json', dict(command=command, request_sha256=policy.digest(request),
            retries=0, max_model_components=2, started_unix=time.time(), deadline_unix=cutoff))
        child = None
        try:
            with (directory / 'stdout.json').open('x') as stdout, (directory / 'stderr.txt').open('x') as stderr:
                child = subprocess.Popen(command, cwd=directory, env=dict(os.environ, CLAUDE_CODE_MAX_OUTPUT_TOKENS='1024'),
                    stdin=subprocess.PIPE, stdout=stdout, stderr=stderr, text=True, start_new_session=True)
                child.communicate(prompt, timeout=max(0.1, cutoff - time.time()))
            policy.require(child.returncode == 0, 'provider_exit_failure')
            envelope = json.loads((directory / 'stdout.json').read_text())
            policy.require(not envelope.get('is_error') and envelope.get('type') == 'result', 'provider_failed')
            models = envelope.get('modelUsage', {})
            policy.require(0 < len(models) <= 2 and envelope.get('num_turns', 1) == 1, 'bounded_observed_provider')
            primary = [name for name, usage in models.items()
                       if 'sonnet' in str(usage.get('canonicalModel', name)).lower()]
            policy.require(len(primary) == 1, 'observed_sonnet_required_no_alias')
            raw = envelope['result']
            if raw.startswith('```json\n') and raw.endswith('\n```'):
                raw = raw[8:-4]
            response = json.loads(raw)
            policy.require(set(response) == {'speak', 'message', 'rationale'}
                and type(response['speak']) is bool and type(response['message']) is str
                and type(response['rationale']) is str
                and (response['speak'] or not response['message']), 'parent_schema')
            write(directory / 'RECEIPT.json', dict(verified=True, model=primary[0],
                model_usage=models, request_sha256=policy.digest(request),
                response_sha256=policy.digest(response), finished_unix=time.time()))
            return response
        finally:
            if child is not None and child.poll() is None:
                os.killpg(child.pid, signal.SIGTERM)
                try:
                    child.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    os.killpg(child.pid, signal.SIGKILL)
                    child.wait(timeout=5)


def transfer_response(host, remote, path):
    destination = remote + '/parent_queue/' + path.name
    subprocess.run(['scp', '-q', str(path), host + ':' + destination + '.partial'], check=True, timeout=30)
    subprocess.run(['ssh', '-o', 'BatchMode=yes', host, 'mv ' + destination + '.partial ' + destination],
                   check=True, timeout=20)


def serve(host, remote, local, deadline):
    policy.require(remote == policy.ROOT, 'own_remote_only')
    local.mkdir(parents=True, exist_ok=True)
    while time.time() < deadline:
        listing = subprocess.run(['ssh', '-o', 'BatchMode=yes', host,
            f'find {remote}/parent_queue -maxdepth 1 -name "*.request.json" -printf "%f\\n"'],
            capture_output=True, text=True, timeout=20)
        for name in sorted(listing.stdout.splitlines()):
            if not re.fullmatch(r'\d{4}_(GUIDED|FROZEN)_C[12]\.request\.json', name):
                continue
            identity = name.removesuffix('.request.json')
            response_path = local / (identity + '.response.json')
            delivered = local / (identity + '.delivered.json')
            if delivered.exists():
                continue
            if not response_path.exists():
                subprocess.run(['scp', '-q', host + ':' + remote + '/parent_queue/' + name, str(local / name)],
                               check=True, timeout=30)
                request = json.loads((local / name).read_text())
                arm = identity.split('_')[1]
                spend(local, 'PROVIDER_' + arm, policy.CAPS['parent_calls_per_lane'],
                      dict(id=identity, reserved_components=2, retries=0))
                try:
                    response = evaluate(request, local / identity, deadline)
                except Exception as error:
                    response = dict(error=str(error), speak=False, message='', rationale='NO_SUBSTITUTE')
                write(response_path, dict(id=identity, request_sha256=policy.digest(request), result=response))
            transfer_response(host, remote, response_path)
            write(delivered, dict(time_unix=time.time()))
            write(local / 'STATUS.json', dict(last=identity, time_unix=time.time()))
        time.sleep(2)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--host')
    parser.add_argument('--local-root', required=True)
    parser.add_argument('--deadline', type=float, required=True)
    parser.add_argument('--probe', action='store_true')
    parser.add_argument('--config')
    args = parser.parse_args()
    if args.config:
        policy.activate(json.loads(Path(args.config).read_text()))
    if args.probe:
        local = Path(args.local_root).resolve()
        local.mkdir(parents=True, exist_ok=True)
        world = policy.cohort(set())['train'][0][0]
        task = policy.shared.tasks(world)[0]
        payload = dict(kind='coach', turn=0, task=task,
            public_messages=[dict(role='user', content=policy.rich.readout.display(task['node'], task, task['ports']))],
            prior_parent_messages=[], learner=dict(purpose='availability_probe_no_child_call'))
        request = dict(id='READINESS_ONLY', payload=policy.parent_payload(payload))
        write(local / 'REQUEST.json', request)
        evaluate(request, local / 'probe', args.deadline)
        write(local / 'PROVIDER.json', json.loads((local / 'probe/RECEIPT.json').read_text()))
        return
    policy.require(bool(args.host), 'host_required')
    serve(args.host, policy.ROOT, Path(args.local_root), args.deadline)


if __name__ == '__main__':
    main()
