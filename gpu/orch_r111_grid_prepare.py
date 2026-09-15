"""Native CPU-only F4 cohort/tokenizer preparation; never authorizes dispatch."""

import hashlib
import json
import os
from pathlib import Path

from organism_v6 import orch_r111_grid as policy


MODEL = '/localhome/local-rohing/.cache/huggingface/hub/models--Qwen--Qwen2.5-7B-Instruct/snapshots/a09a35458c702b33eeacc393d103063234e8bc28'
BUNDLE = '/tmp/astra_portable_37ec_20260914_attempt1'


def prepare(source_root, output):
    policy.require(os.environ.get('CUDA_VISIBLE_DEVICES') == '', 'CPU_only')
    output = Path(output)
    policy.require(not (output/'CPU_PREPARED.json').exists(), 'immutable_CPU_receipt')
    import torch
    from gpu import astra_portable_actor_bundle as portable
    from gpu.orch_l2_rich_math_bootstrap import BUNDLE_SHA
    policy.require(not torch.cuda.is_initialized(), 'no_GPU_initialization')
    protocol = policy.manifest(source_root)
    base = portable.verify_base_files(BUNDLE,MODEL,expected_manifest_sha256=BUNDLE_SHA)
    policy.require(base['expected_base_sha256'] == policy.game.BASE_SHA, 'frozen_base')
    tokenizer = portable.source.native.load_local_tokenizer(MODEL)
    corpus = policy.cohort()
    lengths = {}
    for split, tasks in corpus.items():
        for task in tasks:
            prompt = policy.HELD_PROMPT if split == 'HELD' else policy.EPISODE_PROMPT
            messages = [dict(role='system',content=prompt),dict(role='user',content=json.dumps(
                policy.public_observation(task,policy.game.initial(task)),sort_keys=True))]
            tokens = tokenizer.apply_chat_template(messages,tokenize=True,add_generation_prompt=True,return_dict=False)
            cap = policy.DECODER['held_max_new_tokens'] if split == 'HELD' else policy.DECODER['segment_max_new_tokens']
            policy.require(len(tokens)+cap <= policy.DECODER['context_limit'], 'initial_native_context_bound')
            lengths[task['id']] = len(tokens)
    output.mkdir(parents=True,exist_ok=True)
    with (output/'COHORT_PRIVATE.json').open('x') as stream:
        json.dump(corpus,stream,indent=2,sort_keys=True)
    result = dict(schema='R111_F4_NATIVE_CPU_PREPARED_V1',protocol_sha256=policy.digest(protocol),
        canonical_cohort_sha256=policy.digest(corpus),native_private_cohort=dict(path=str(output/'COHORT_PRIVATE.json'),
            sha256=hashlib.sha256((output/'COHORT_PRIVATE.json').read_bytes()).hexdigest()),
        initial_prompt_tokens=lengths,base=base,model_loaded=False,cuda_initialized=torch.cuda.is_initialized(),
        native_calls=0,parent_calls=0,sleep_count=0,sleep0_status='NOT_RUN',
        gpu_launch_ready=False,Fable_gate='CLOSED_UNTIL_EXPLICIT_WATCHER_GO',
        pending=protocol['pending'],note='Initial context check only; full accumulated-dialogue driver still requires native tests')
    policy.require(result['cuda_initialized'] is False, 'CPU_stayed_CPU')
    with (output/'CPU_PREPARED.json').open('x') as stream:
        json.dump(result,stream,indent=2,sort_keys=True)
    return result
