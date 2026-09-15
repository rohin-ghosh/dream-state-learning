"""CPU preparation on node2 only; source/raw archives never copied to the VM."""

import json
import os
from pathlib import Path
import shutil
import socket
import tarfile
import time

from gpu import orch_rich_hot_node2_exhaustion_v3 as run


base, ROOT, policy = run.base, run.ROOT, run.policy


def prepare():
    base.hot.require(socket.gethostname() == base.HOST and os.environ.get('CUDA_VISIBLE_DEVICES') == '', 'node2_CPU_only')
    prior = base.read(base.ORIGINAL / 'PREPARE.json')
    checkpoint = base.read(run.DERIVED / 'PREPARE.json')
    for name in ('TASKS.json', 'LIFETIME.json', 'SERVICE_IDENTITY.json'):
        shutil.copyfile(run.FLOOR / name, ROOT / name)
    base.hot.require(base.read(ROOT / 'LIFETIME.json') == base.read(base.ORIGINAL / 'LIFETIME.json'), 'unchanged_lifetime')
    base.portable.verify_base_files(prior['bundle'], prior['model_dir'], expected_manifest_sha256=base.BUNDLE_SHA)
    config_path = Path(prior['model_dir']) / 'config.json'
    config = base.read(config_path)
    base.hot.require(config['max_position_embeddings'] >= policy.CONTEXT, 'native_context_32768_supported')
    identities = {str(shard): checkpoint['identity'] if shard == 0 else prior['identity'] for shard in range(8)}
    from safetensors.torch import load_file
    for document in (prior['identity'], checkpoint['identity']):
        identity = base.bridge.AdapterIdentity.from_document(document)
        identity.verify()
        tensors = load_file(str(Path(identity.path) / 'adapter_model.safetensors'), device='cpu')
        mounted = {name.replace('.lora_A.', '.lora_A.default.').replace('.lora_B.', '.lora_B.default.'): value for name, value in tensors.items()}
        base.hot.require(base.native.state_hash(mounted) == identity.state_sha256, 'saved_state_hash')
    tokenizer = base.native.source.native.load_local_tokenizer(prior['model_dir'])
    document = base.read(ROOT / 'TASKS.json')
    lengths = []
    for shard in range(8):
        for position in range(shard % 2, policy.prior.TASKS_PER_BATCH, 2):
            task = policy.task_at(document, 0, position, shard)
            if task['family'] != 'route':
                tokens = tokenizer.apply_chat_template(policy.messages(task, shard), tokenize=True, add_generation_prompt=True, return_dict=False)
                base.hot.require(policy.effective_budget(len(tokens)) == policy.TARGET, 'initial_budget_fits')
                lengths.append(len(tokens))
    for position in range(0, policy.prior.TASKS_PER_BATCH, 2):
        left, right = policy.task_at(document, 0, position, 0), policy.task_at(document, 0, position + 1, 1)
        base.hot.require(left == right and policy.guidance(0) == policy.guidance(1), 'matched_V3_pair')
    with tarfile.open(ROOT / 'source.tar', 'w') as archive:
        for path in sorted((ROOT / 'source').rglob('*.py')):
            archive.add(path, arcname=str(path.relative_to(ROOT / 'source')), recursive=False)
    paths = [ROOT / name for name in ('TASKS.json', 'LIFETIME.json', 'SERVICE_IDENTITY.json', 'PROTOCOL.md')]
    paths += [config_path, base.ORIGINAL / 'PREPARE.json', run.FLOOR / 'PREPARE.json', run.DERIVED / 'PREPARE.json',
              run.DERIVED / 'input/COMMIT.json', run.DERIVED / 'SELECTED_FULL_HANDOFF.json']
    prepared = dict(source_sha256=base.sha(ROOT / 'source.tar'), source_files=base.verify_archive(ROOT / 'source.tar', ROOT / 'source'),
        files={str(path): base.sha(path) for path in paths}, identities=identities, identity=identities['1'],
        checkpoint_commit_sha256=checkpoint['lineage']['commit_sha256'], model_dir=prior['model_dir'], bundle=prior['bundle'],
        model_max_position_embeddings=config['max_position_embeddings'], model_config_sha256=base.sha(config_path),
        rope_configuration_unchanged=True, prompt_token_range=[min(lengths), max(lengths)],
        target_max_new_tokens=policy.TARGET, context=policy.CONTEXT, total_successor_cap=policy.MAX_CALLS,
        per_slot_including_prior=policy.PER_SLOT, original_cap=6144, cpu_only=True, prepared_unix=time.time())
    base.write(ROOT / 'PREPARE.json', prepared)
    (ROOT / 'reservations').mkdir()
    print(json.dumps(dict(prepare_sha256=base.sha(ROOT / 'PREPARE.json'), source_sha256=prepared['source_sha256'],
        model_config_sha256=prepared['model_config_sha256'], context=policy.CONTEXT, target=policy.TARGET,
        prompt_token_range=prepared['prompt_token_range'], tasks_sha256=base.sha(ROOT / 'TASKS.json'),
        identities={key: value['state_sha256'] for key, value in identities.items()}, native_root=str(ROOT))))


if __name__ == '__main__':
    prepare()
