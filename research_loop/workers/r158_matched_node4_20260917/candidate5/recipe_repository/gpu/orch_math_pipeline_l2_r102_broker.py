"""Versioned strong-parent broker with exact approved two-episode contexts."""

import argparse
from contextlib import contextmanager
import functools
import hashlib
import json
import os
from pathlib import Path
import shlex
import time
import tomllib

from gpu import orch_math_pipeline_l2_parent_node as transport
from gpu import orch_math_pipeline_l2_r102_policy as policy


@contextmanager
def parent_context(variant):
    old_validator = transport.parent.policy.validate_parent_payload
    old_instructions = transport.parent.INSTRUCTIONS
    descriptor = policy.VARIANTS[variant]['parenting']
    transport.parent.policy.validate_parent_payload = functools.partial(policy.validate_parent_payload, parenting=descriptor)
    if variant == 'micro5':
        transport.parent.INSTRUCTIONS = old_instructions.replace('longform learning parent', 'learning parent').replace(
            'about100-200 words per episode.', 'use compact coaching: one focused what/how prompt and one concrete check per episode; do not supply model answers.').replace(
            'Aim\nfor useful longform guidance rather than padding;', 'Aim\nfor useful compact guidance rather than padding;')
    else:
        transport.parent.INSTRUCTIONS = old_instructions + '\nCreative/long/supportive treatment: help the child compare plausible thinking strategies, explain a rejection, and carry a coherent check into its next episode; never write its answer for it.'
    try:
        yield
    finally:
        transport.parent.policy.validate_parent_payload = old_validator
        transport.parent.INSTRUCTIONS = old_instructions


def serve(repository, root, buffer, receipts, registration, deadline):
    assert os.environ.get('CUDA_VISIBLE_DEVICES') == '' and str(buffer).startswith('/tmp/')
    buffer.mkdir(parents=True, exist_ok=True)
    assert not any(buffer.iterdir()), 'previous_buffer_must_be_archived_before_takeover'
    registered = transport.parent.read(registration)
    assert registered['aggregate_native_cap'] == 1920 and registered['aggregate_parent_cap'] == 28
    assert registered['policy_sha256'] == transport.parent.sha(Path(policy.__file__))
    store = transport.Store(repository, root)
    config = tomllib.loads((Path.home() / '.codex/config.toml').read_text())
    campaigns = {item['campaign']: variant for variant, item in policy.VARIANTS.items()}
    while time.time() < deadline:
        result = store.shell('find ' + shlex.quote(str(root)) + '/campaign_*/parent_queue -maxdepth 1 -name "*.request.json"')
        for name in sorted(result.stdout.splitlines()):
            request = Path(name)
            variant = campaigns.get(request.parent.parent.name)
            if variant is None:
                transport.process_request(store, request, buffer, receipts, config, deadline)
                continue
            ready_path = request.parent.parent / 'R102_READY.json'
            text = store.shell('cat ' + shlex.quote(str(ready_path))).stdout
            assert hashlib.sha256(text.encode()).hexdigest() == registered['ready_sha256'][variant]
            ready = json.loads(text)
            assert ready['config'] == policy.VARIANTS[variant]
            assert ready['source_files']['orch_math_pipeline_l2_r102_policy.py'] == registered['policy_sha256']
            with parent_context(variant):
                transport.process_request(store, request, buffer, receipts, config, deadline)
        time.sleep(3)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--repository', type=Path, required=True)
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--buffer', type=Path, required=True)
    parser.add_argument('--receipts', type=Path, required=True)
    parser.add_argument('--registration', type=Path, required=True)
    parser.add_argument('--deadline', type=float, required=True)
    options = parser.parse_args()
    serve(options.repository, options.root, options.buffer, options.receipts, options.registration, options.deadline)
