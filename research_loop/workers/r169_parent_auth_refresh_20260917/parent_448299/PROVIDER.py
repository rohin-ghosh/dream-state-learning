"""TRAIN-only, tool-free qualification using existing provider configuration."""

import argparse
from datetime import datetime, timezone
import fcntl
import json
import os
from pathlib import Path
import signal
import subprocess
import time
import tomllib
import urllib.error
import urllib.request

from gpu import orch_l2_long_backend as backend
from gpu.orch_l2_shared_run import write
from gpu.orch_route_parent_campaign_parent import SYSTEM
from organism_v6 import orch_route_parent_campaign as policy
from organism_v6.orch_guided_bridge import file_sha256


SMALLER = 'claude-haiku-4-5-20251001'
STRONG = 'openai/openai/gpt-6-astra'


def response_schema(raw):
    if raw.startswith('```json\n') and raw.endswith('\n```'):
        raw = raw[8:-4]
    response = json.loads(raw)
    policy.require(set(response) == {'speak', 'message', 'rationale'}
        and type(response['speak']) is bool and type(response['message']) is str
        and type(response['rationale']) is str and len(response['message'].split()) <= 90
        and (response['speak'] or not response['message']), 'exact_bounded_parent_response')
    return response


def parse_strong(envelope):
    policy.require(envelope.get('model') == STRONG, 'actual_strong_model_identity')
    policy.require(envelope.get('status') == 'completed' and not envelope.get('error'), 'complete_strong_response')
    output = envelope.get('output', [])
    policy.require(all(item.get('type') in ('reasoning', 'message') for item in output), 'no_provider_tool_calls')
    texts = [part['text'] for item in output if item.get('type') == 'message'
             for part in item.get('content', []) if part.get('type') == 'output_text']
    policy.require(len(texts) == 1 and bool(envelope.get('usage')), 'one_reply_and_usage')
    return response_schema(texts[0]), envelope['model'], envelope['usage']


def parse_smaller(envelope):
    policy.require(envelope.get('type') == 'result' and not envelope.get('is_error')
                   and envelope.get('num_turns') == 1, 'complete_single_turn_smaller')
    models = envelope.get('modelUsage', {})
    policy.require(bool(models) and len(models) <= 2 and all('haiku' in name.lower() for name in models),
                   'smaller_primary_not_sonnet_auxiliary')
    primary = [name for name, usage in models.items() if name == SMALLER and usage.get('outputTokens', 0) > 0]
    policy.require(len(primary) == 1, 'exact_observed_smaller_primary')
    return response_schema(envelope['result']), primary[0], models


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise ValueError('provider_redirect_forbidden')


def strong(prompt, directory, deadline, instruction=SYSTEM, *, reasoning_effort=None):
    config_path = Path.home() / '.codex/nvidia-astra.config.toml'
    config = tomllib.loads(config_path.read_text())
    provider = config['model_providers'][config['model_provider']]
    policy.require(config['model'] == STRONG and provider['wire_api'] == 'responses'
        and provider['base_url'] == 'https://[REDACTED_HOST]/v1'
        and provider['env_key'] == 'NVIDIA_API_KEY', 'existing_exact_provider_configuration')
    key = os.environ[provider['env_key']]
    effort = config['model_reasoning_effort'] if reasoning_effort is None else reasoning_effort
    policy.require(effort in ('low', 'medium', 'high', 'xhigh'), 'explicit_supported_parent_effort')
    body = dict(model=config['model'], instructions=instruction, input=prompt,
        max_output_tokens=4096, tools=[], tool_choice='none', store=False,
        reasoning=dict(effort=effort))
    write(directory / 'API_REQUEST.json', body)
    write(directory / 'DISPATCH.json', dict(utc=datetime.now(timezone.utc).isoformat(),
        kind='existing_nvidia_responses', requested_model=config['model'], attempts=1, retries=0,
        config_sha256=file_sha256(config_path), maximum_output_tokens=4096, timeout_seconds=120,
        actual_reasoning_effort=effort,
        tool_access=False, raw_http_attempts_observable=True))
    request = urllib.request.Request(provider['base_url'] + '/responses', data=json.dumps(body).encode(),
        headers={'Authorization': '[REDACTED_SECRET]' + key, 'Content-Type': 'application/json'})
    opener = urllib.request.build_opener(NoRedirect, urllib.request.ProxyHandler({}))
    try:
        with opener.open(request, timeout=max(0.1, min(120, deadline - time.time()))) as response:
            raw = response.read().decode()
    except urllib.error.HTTPError as error:
        (directory / 'http_error_response.txt').write_text(error.read().decode(errors='replace').replace(key, '[REDACTED]'))
        raise
    (directory / 'stdout.json').write_text(raw)
    return parse_strong(json.loads(raw))


def smaller(prompt, directory, deadline, instruction=SYSTEM):
    with backend.LOCK_PATH.open('a') as lock:
        while True:
            policy.require(time.time() < deadline, 'smaller_lock_deadline')
            try:
                fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
                break
            except BlockingIOError:
                time.sleep(0.25)
        return smaller_locked(prompt, directory, deadline, instruction)


def smaller_locked(prompt, directory, deadline, instruction):
    policy.require(backend.available_memory() >= backend.MIN_AVAILABLE_BYTES, 'provider_memory_floor')
    command = backend.command() + ['--model', SMALLER]
    command[command.index('--system-prompt') + 1] = instruction
    write(directory / 'DISPATCH.json', dict(utc=datetime.now(timezone.utc).isoformat(), command=command,
        requested_model=SMALLER, cli_invocations=1, application_retries=0,
        underlying_http_attempts='NOT_OBSERVABLE_FROM_CLI', maximum_output_tokens=1024,
        timeout_seconds=180, tool_access=False))
    child = None
    try:
        with (directory / 'stdout.json').open('x') as stdout, (directory / 'stderr.txt').open('x') as stderr:
            child = subprocess.Popen(command, cwd=directory,
                env=dict(os.environ, CLAUDE_CODE_MAX_OUTPUT_TOKENS='1024'), stdin=subprocess.PIPE,
                stdout=stdout, stderr=stderr, text=True, start_new_session=True)
            child.communicate(prompt, timeout=max(0.1, min(180, deadline - time.time())))
        policy.require(child.returncode == 0, 'smaller_cli_exit')
        return parse_smaller(json.loads((directory / 'stdout.json').read_text()))
    finally:
        if child is not None and child.poll() is None:
            os.killpg(child.pid, signal.SIGTERM)
            try:
                child.wait(timeout=5)
            except subprocess.TimeoutExpired:
                os.killpg(child.pid, signal.SIGKILL)
                child.wait(timeout=5)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--kind', required=True, choices=('strong', 'smaller'))
    parser.add_argument('--request', required=True)
    parser.add_argument('--output', required=True)
    parser.add_argument('--deadline', type=float, required=True)
    args = parser.parse_args()
    directory = Path(args.output).resolve()
    directory.mkdir(parents=True, exist_ok=False)
    request = json.loads(Path(args.request).read_text())
    policy.require(request['id'] == 'READINESS_ONLY', 'training_readiness_only')
    supplied = dict(request['payload'])
    cell = supplied.pop('cell')
    prompt = json.dumps(policy.parent_payload(supplied, cell), sort_keys=True)
    (directory / 'prompt.txt').write_text(prompt)
    (directory / 'system.txt').write_text(SYSTEM)
    try:
        policy.require(time.time() < args.deadline, 'bounded_qualification_deadline')
        response, model, usage = (strong if args.kind == 'strong' else smaller)(prompt, directory, args.deadline)
        write(directory / 'RECEIPT.json', dict(verified=True, actual_primary_model=model, usage=usage,
            response=response, prompt_sha256=file_sha256(directory / 'prompt.txt'),
            envelope_sha256=file_sha256(directory / 'stdout.json'), utc=datetime.now(timezone.utc).isoformat(),
            scope='TRAIN_ONLY_READINESS_NOT_HELD', transcript_quarantined_from_ongoing_L1=True))
    except Exception as error:
        write(directory / 'FAILED.json', dict(verified=False, error_type=type(error).__name__,
            error=str(error).replace(os.environ.get('NVIDIA_API_KEY', '\x00'), '[REDACTED]'),
            utc=datetime.now(timezone.utc).isoformat(), fallback=False))
        raise SystemExit(1)


if __name__ == '__main__':
    main()
