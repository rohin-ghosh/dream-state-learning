"""F2 broker entrypoint: shared Claude transport and identical-policy Astra calls."""

import argparse
import fcntl
import json
import os
from pathlib import Path
import time
import tomllib
import urllib.request
import urllib.error

from gpu import orch_r110_claude_broker as shared
from gpu.orch_route_parent_campaign_providers import NoRedirect, STRONG


def astra_evaluate(request, directory, deadline, *, config, launch, prompt_root, principles_path):
    shared.validate_config(config)
    shared.validate_launch(config, launch, time.time())
    directory = Path(directory)
    shared.require(directory.resolve().is_relative_to(Path('/tmp')), 'bounded_tmp_only')
    directory.mkdir(parents=True, exist_ok=False)
    shared.write(directory / 'REQUEST.json', request)
    dispatched, binding = False, None
    lock = None
    try:
        transcript = shared.validate_request(request, config)
        cutoff = min(deadline, request['lane_deadline_unix']-30)
        shared.require(time.time() < cutoff, 'lane_cutoff_before_dispatch')
        lock = Path(shared.backend.LOCK_PATH).open('a')
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        floor = config.get('min_available_bytes', shared.backend.MIN_AVAILABLE_BYTES)
        available = shared.backend.available_memory()
        shared.write(directory / 'MEMORY.json', dict(available_bytes=available, floor_bytes=floor, serialized_lock=True))
        shared.require(available >= floor, 'vm_memory_floor')
        system, prompt, binding = shared.build_system(transcript, config, prompt_root, principles_path)
        (directory / 'PARENT_PROMPT.md').write_bytes(prompt)
        (directory / 'SYSTEM.txt').write_text(system)
        shared.write(directory / 'PROMPT_BINDING.json', binding)
        settings_path = Path.home() / '.codex/nvidia-astra.config.toml'
        settings = tomllib.loads(settings_path.read_text())
        provider = settings['model_providers'][settings['model_provider']]
        shared.require(settings['model'] == STRONG and provider['wire_api'] == 'responses'
            and provider['base_url'] == 'https://inference-api.nvidia.com/v1'
            and provider['env_key'] == 'NVIDIA_API_KEY', 'existing_verified_primary_only')
        secret = os.environ[provider['env_key']]
        body = dict(model=STRONG, instructions=system,
            input='Respond to the supplied TRAIN transcript using the transport contract.',
            max_output_tokens=config['max_output_tokens'], tools=[], tool_choice='none', store=False,
            reasoning=dict(effort=settings['model_reasoning_effort']))
        shared.write(directory / 'API_REQUEST.json', body)
        shared.write(directory / 'INVOCATION.json', dict(actual_requested_model=STRONG,
            config_sha256=shared.sha(settings_path), http_attempts=1, retries=0, started_unix=time.time()))
        invocation = urllib.request.Request(provider['base_url']+'/responses', data=json.dumps(body).encode(),
            headers={'Authorization': 'Bearer '+secret, 'Content-Type': 'application/json'})
        opener = urllib.request.build_opener(NoRedirect, urllib.request.ProxyHandler({}))
        dispatched = True
        try:
            with opener.open(invocation, timeout=max(.1, cutoff-time.time())) as response:
                raw = response.read(shared.STDOUT_CAP+1)
        except urllib.error.HTTPError as error:
            raw_error = error.read(shared.STDOUT_CAP).decode(errors='replace').replace(secret, '[REDACTED]')
            (directory / 'HTTP_ERROR.txt').write_text(raw_error)
            raise
        shared.require(len(raw) <= shared.STDOUT_CAP, 'provider_output_bytes_limit')
        (directory / 'RAW_RESPONSE.json').write_bytes(raw)
        envelope = json.loads(raw)
        shared.require(envelope.get('model') == STRONG and envelope.get('status') == 'completed'
            and not envelope.get('error') and envelope.get('usage'), 'actual_strong_model_verified')
        texts = [part['text'] for item in envelope.get('output', []) if item.get('type') == 'message'
            for part in item.get('content', []) if part.get('type') == 'output_text']
        shared.require(len(texts) == 1 and time.time() < cutoff, 'one_on_time_parent_response')
        text = texts[0].strip()
        if text.startswith('```json\n') and text.endswith('\n```'):
            text = text[8:-4]
        decoded = '[SILENT]' if text == '[SILENT]' else shared.loads(text)
        plan, metadata = shared.adapt_plan(decoded, config['family'], transcript['task_id'])
        result = dict(status='SILENT' if plan is None else 'COMPLETE', plan=plan,
            parent_metadata=metadata, actual_model=STRONG, usage=envelope['usage'])
    except Exception as error:
        result = dict(status='MISSING', plan=None, parent_metadata=None, actual_model=None,
            error=dict(type=type(error).__name__, code='captured_astra_failure_no_retry'))
    finally:
        if lock is not None:
            lock.close()
    result.update(id=request['id'], request_sha256=shared.digest(request), payload_sha256=request['payload_sha256'],
        lane_deadline_unix=request['lane_deadline_unix'], prompt_binding=binding,
        provider_dispatched=dispatched, retry=False, finished_unix=time.time())
    shared.write(directory / 'RESULT.json', result)
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--member', choices=('FABLE', 'ASTRA'), required=True)
    parser.add_argument('--config', type=Path, required=True)
    parser.add_argument('--launch-receipt', type=Path, required=True)
    parser.add_argument('--prompt-root', type=Path, required=True)
    parser.add_argument('--principles', type=Path, required=True)
    args = parser.parse_args()
    if args.member == 'ASTRA':
        shared.evaluate = astra_evaluate
    shared.serve(args.config, args.launch_receipt, args.prompt_root, args.principles)
