"""Native CPU preparation and sealed split commitments for unlaunched F4 v4."""

import argparse
import hashlib
import json
import os
from pathlib import Path

from gpu import orch_r111_grid_prepare as previous
from organism_v6 import orch_r111_grid_v4 as policy


def write_once(path, value):
    with Path(path).open('x') as stream:
        json.dump(value, stream, sort_keys=True, indent=2)


def prepare(source_root, output):
    policy.require(os.environ.get('CUDA_VISIBLE_DEVICES') == '', 'CPU_only')
    import torch
    from gpu import astra_portable_actor_bundle as portable
    from gpu.orch_l2_rich_math_bootstrap import BUNDLE_SHA
    policy.require(not torch.cuda.is_initialized(), 'CPU_no_CUDA')
    protocol = policy.manifest(source_root)
    base = portable.verify_base_files(previous.BUNDLE, previous.MODEL, expected_manifest_sha256=BUNDLE_SHA)
    policy.require(base['expected_base_sha256'] == policy.game.BASE_SHA, 'frozen_BASE')
    tokenizer = portable.source.native.load_local_tokenizer(previous.MODEL)
    tasks = policy.cohort()
    lengths = {}
    for split, group in tasks.items():
        for task in group:
            prompt = policy.EPISODE_PROMPT if split == 'TRAIN' else policy.HELD_PROMPT
            messages = [dict(role='system', content=prompt), dict(role='user', content=json.dumps(
                policy.public_observation(task, policy.game.initial(task)), sort_keys=True))]
            tokens = tokenizer.apply_chat_template(messages, tokenize=True, add_generation_prompt=True, return_dict=False)
            policy.require(len(tokens) + 2048 <= policy.DECODER['context_limit'], 'initial_context_bound')
            lengths[task['id']] = len(tokens)
    output = Path(output)
    output.mkdir(parents=True, exist_ok=False)
    os.chmod(output, 0o700)
    for split, group in tasks.items():
        write_once(output / (split + '_PRIVATE.json'), group)
    write_once(output / 'PROTOCOL.json', protocol)
    result = dict(schema='R114_F4_NATIVE_CPU_V1', protocol_sha256=policy.digest(protocol),
        canonical_cohort_sha256=policy.digest(tasks), split_sha256=protocol['split_sha256'],
        native_private_files={split: dict(path=str(output / (split + '_PRIVATE.json')),
            sha256=hashlib.sha256((output / (split + '_PRIVATE.json')).read_bytes()).hexdigest()) for split in tasks},
        initial_prompt_tokens_min=min(lengths.values()), initial_prompt_tokens_max=max(lengths.values()),
        base=base, model_loaded=False, cuda_initialized=torch.cuda.is_initialized(),
        native_calls=0, parent_calls=0, optimizer_steps=0, gpu_launch_ready=False,
        sleep0_status='NOT_RUN', pending=protocol['pending'])
    policy.require(not result['cuda_initialized'], 'CPU_stayed_CPU')
    write_once(output / 'CPU_PREPARED.json', result)
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--source-root', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    arguments = parser.parse_args()
    print(json.dumps(prepare(arguments.source_root, arguments.output), sort_keys=True))
