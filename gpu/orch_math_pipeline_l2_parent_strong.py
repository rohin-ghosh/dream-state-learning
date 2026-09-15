"""Existing verified strong provider; unchanged math parent visibility contract."""

import json
import os
from pathlib import Path
import time
import tomllib
import urllib.error
import urllib.request

from gpu import orch_math_pipeline_l2_parent as parent
from gpu.orch_route_parent_campaign_providers import NoRedirect, STRONG


def parse(envelope, identifiers):
    assert envelope.get('model') == STRONG, 'actual_strong_primary_identity_required'
    assert envelope.get('status') == 'completed' and not envelope.get('error')
    assert envelope.get('usage')
    assert all(item.get('type') in ('reasoning', 'message') for item in envelope.get('output', []))
    texts = [part['text'] for item in envelope['output'] if item.get('type') == 'message'
        for part in item.get('content', []) if part.get('type') == 'output_text']
    assert len(texts) == 1
    text = texts[0]
    if text.startswith('```json\n') and text.endswith('\n```'):
        text = text[8:-4]
    plan = json.loads(text)
    assert set(plan) == {'guidance', 'order', 'episode_guidance', 'rationale'}
    assert sorted(plan['order']) == sorted(identifiers) and set(plan['episode_guidance']) == set(identifiers)
    assert isinstance(plan['guidance'], str) and isinstance(plan['rationale'], str)
    assert all(isinstance(value, str) for value in plan['episode_guidance'].values())
    return plan


def evaluate(request, directory, config, timeout=720):
    parent.policy.validate_parent_payload(request['payload'])
    assert request['payload_sha256'] == parent.policy.digest(request['payload'])
    repository = Path(__file__).resolve().parents[1]
    proof = repository / 'research_notes/analysis/orch_route_parent_campaign_20260915_monitor_v2/provider_strong/RECEIPT.json'
    qualification = parent.read(proof)
    assert qualification['verified'] and qualification['actual_primary_model'] == STRONG
    config_path = Path.home() / '.codex/nvidia-astra.config.toml'
    settings = tomllib.loads(config_path.read_text())
    provider = settings['model_providers'][settings['model_provider']]
    assert settings['model'] == STRONG and provider['wire_api'] == 'responses'
    assert provider['base_url'] == 'https://inference-api.nvidia.com/v1' and provider['env_key'] == 'NVIDIA_API_KEY'
    key = os.environ[provider['env_key']]
    identifiers = [episode['task_id'] for episode in request['payload']['episodes']]
    directory.mkdir(parents=True, exist_ok=False)
    parent.write(directory / 'REQUEST.json', request)
    parent.write(directory / 'SCHEMA.json', parent.schema(identifiers))
    prompt = parent.INSTRUCTIONS + '\n\nReturn JSON conforming to this schema:\n' + json.dumps(parent.schema(identifiers))
    prompt += '\n\nPUBLIC TRAIN DATA:\n' + json.dumps(request['payload'], ensure_ascii=False)
    (directory / 'PROMPT.txt').write_text(prompt)
    body = dict(model=STRONG, instructions=parent.INSTRUCTIONS, input=prompt,
        max_output_tokens=8192, tools=[], tool_choice='none', store=False,
        reasoning=dict(effort=settings['model_reasoning_effort']))
    parent.write(directory / 'API_REQUEST.json', body)
    parent.write(directory / 'INVOCATION.json', dict(model=STRONG, requested_model=STRONG,
        provider='EXISTING_VERIFIED_PRIMARY_RESPONSES', http_attempts=1, retries=0,
        qualification_sha256=parent.sha(proof), qualification_envelope_sha256=qualification['envelope_sha256'],
        config_sha256=parent.sha(config_path), parent_source_sha256=parent.sha(Path(parent.__file__)),
        started_unix=time.time(), max_output_tokens=8192, tool_access=False))
    api_request = urllib.request.Request(provider['base_url'] + '/responses', data=json.dumps(body).encode(),
        headers={'Authorization': 'Bearer ' + key, 'Content-Type': 'application/json'})
    opener = urllib.request.build_opener(NoRedirect, urllib.request.ProxyHandler({}))
    try:
        with opener.open(api_request, timeout=max(0.1, min(120, timeout))) as response:
            raw = response.read().decode()
    except urllib.error.HTTPError as error:
        (directory / 'HTTP_ERROR.txt').write_text(error.read().decode(errors='replace').replace(key, '[REDACTED]'))
        raise RuntimeError('strong_parent_http_error_no_retry:' + str(error.code)) from None
    (directory / 'RAW_RESPONSE.json').write_text(raw)
    envelope = json.loads(raw)
    plan = parse(envelope, identifiers)
    parent.write(directory / 'PLAN.json', plan)
    parent.write(directory / 'COMPLETE.json', dict(status='COMPLETE', actual_primary_model=envelope['model'],
        usage=envelope['usage'], http_attempts=1, retries=0, finished_unix=time.time(),
        plan_sha256=parent.sha(directory / 'PLAN.json'), raw_response_sha256=parent.sha(directory / 'RAW_RESPONSE.json'),
        public_only=True, teacher_targets_compiled=False))
    return plan
