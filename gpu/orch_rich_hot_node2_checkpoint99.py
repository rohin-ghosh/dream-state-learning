"""Readonly FULL-checkpoint generator on node2physical0 with every-call identity."""

import argparse
import fcntl
import json
import os
from pathlib import Path
import time

from gpu import orch_rich_hot_node2_continue as base
from gpu import orch_rich_hot_node2_floor98 as floor
from organism_v6 import orch_rich_hot_node2_checkpoint99 as policy


ROOT = Path('/localhome/local-rohing/orch_rich_hot_node2_checkpoint99_20260915_attempt1')


def configure():
    base.ROOT = ROOT
    base.policy = policy
    base.reserve = reserve


def prepare():
    from safetensors.torch import load_file

    base.hot.require(os.environ.get('CUDA_VISIBLE_DEVICES') == '', 'CPU_only')
    handoff, commit = base.read(ROOT / 'SELECTED_FULL_HANDOFF.json'), base.read(ROOT / 'input/COMMIT.json')
    metadata = policy.validate_handoff(handoff, commit, base.sha(ROOT / 'input/COMMIT.json'))
    for relative, digest in commit['files'].items():
        if relative.startswith('adapter/'):
            base.hot.require(base.sha(ROOT / 'input' / relative) == digest, 'copied_checkpoint_tensor_drift')
    prior = base.read(base.ORIGINAL / 'PREPARE.json')
    floor_prepared = base.read(floor.ROOT / 'PREPARE.json')
    for name in ('TASKS.json', 'LIFETIME.json', 'gsm8k_train.jsonl'):
        base.hot.require(base.sha(ROOT / name) == base.sha(floor.ROOT / name), 'same_roster_clock_source_required')
    identity = base.bridge.AdapterIdentity.from_document(base.read(ROOT / 'INITIAL.json'))
    base.hot.require(identity.state_sha256 == handoff['adapter']['state_sha256']
                     and identity.base_sha256 == prior['identity']['base_sha256'], 'exact_FULL_fixed_base')
    identity.verify()
    tensors = load_file(str(Path(identity.path) / 'adapter_model.safetensors'), device='cpu')
    mounted = {name.replace('.lora_A.', '.lora_A.default.').replace('.lora_B.', '.lora_B.default.'): value for name, value in tensors.items()}
    base.hot.require(base.native.state_hash(mounted) == identity.state_sha256, 'saved_FULL_state_hash')
    base.portable.verify_base_files(prior['bundle'], prior['model_dir'], expected_manifest_sha256=base.BUNDLE_SHA)
    config = base.read(Path(prior['model_dir']) / 'config.json')
    base.hot.require(config['max_position_embeddings'] >= base.hot.CONTEXT, 'context_support')
    names = ('TASKS.json', 'LIFETIME.json', 'gsm8k_train.jsonl', 'INITIAL.json', 'DATA_PROVENANCE.json',
             'PROTOCOL.md', 'SERVICE_IDENTITY.json', 'SELECTED_FULL_HANDOFF.json', 'input/COMMIT.json')
    base.write(ROOT / 'PREPARE.json', dict(identity=identity.document(), model_dir=prior['model_dir'], bundle=prior['bundle'],
        original_lifetime_sha256=base.sha(base.ORIGINAL / 'LIFETIME.json'), original_prepare_sha256=base.sha(base.ORIGINAL / 'PREPARE.json'),
        source_sha256=base.sha(ROOT / 'source.tar'), source_files=base.verify_archive(ROOT / 'source.tar', ROOT / 'source'),
        files={name: base.sha(ROOT / name) for name in names}, lineage=handoff, classification=policy.CLASSIFICATION,
        comparator_root=str(floor.ROOT), comparator_physical_gpu=1, comparator_prepare_sha256=base.sha(floor.ROOT / 'PREPARE.json'),
        parent_checkpoint_update=metadata['update'], original_max_calls=6144, additional_arm_max_calls=8192,
        allocated_physical_gpu=0, inherited_other7_calls=7 * 8192, total_successor_cap=65536,
        prompt_range=floor_prepared['prompt_range'], max_new_tokens=8192, context=16384, cpu_only=True, prepared_unix=time.time()))


def reserve(root, shard, task, stage, messages, deadline):
    base.hot.require(root == ROOT and shard == 0, 'checkpoint_arm_only_physical0')
    if time.time() >= deadline or (root / 'STOP_AFTER_CALL.json').exists():
        raise base.BudgetEnd('inherited_deadline_or_stop')
    with (root / 'CALLS.jsonl').open('a+') as stream:
        fcntl.flock(stream, fcntl.LOCK_EX)
        count = len(list((root / 'reservations').glob('*.json')))
        if count >= policy.MAX_CALLS:
            raise base.BudgetEnd('checkpoint_arm8192call_cap')
        prepared = base.read(root / 'PREPARE.json')
        row = dict(index=count, shard=shard, task_id=task['id'], family=task['family'], stage=stage,
            messages=messages, max_new_tokens=8192, context=16384, condition='ORIGINAL_RICH',
            source_task_id=task['source_task_id'], repeated_train_source=task['repeated_train_source'],
            comparator_task_id=task['comparator_task_id'], comparator_root=prepared['comparator_root'], comparator_physical_gpu=1,
            generator_identity=prepared['identity'], generator_classification=policy.CLASSIFICATION,
            source_checkpoint_commit_sha256=prepared['lineage']['commit_sha256'], source_checkpoint_update=prepared['parent_checkpoint_update'],
            source_code_sha256=prepared['source_sha256'], reserved_unix=time.time(), trainingAllowed=False)
        base.write(root / 'reservations' / f'0_{task["id"]}_{stage}.json', row)
        stream.write(json.dumps({name: value for name, value in row.items() if name != 'messages'}) + '\n')
        stream.flush()
        os.fsync(stream.fileno())
        return row


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('phase', choices=('prepare', 'run'))
    options = parser.parse_args()
    configure()
    prepare() if options.phase == 'prepare' else base.run(ROOT, 0)
