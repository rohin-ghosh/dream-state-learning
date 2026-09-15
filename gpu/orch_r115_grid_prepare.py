"""CPU-only native preparation for the actual R115 paired grid runtime."""

import argparse
import json
import os
from pathlib import Path
import shutil
import time

from gpu import orch_r115_grid_native as run


def prepare(root, broker_config_path, launch_path):
    run.require(os.environ.get('CUDA_VISIBLE_DEVICES') == '', 'CPU_only')
    import torch
    run.require(not torch.cuda.is_initialized(), 'CPU_no_GPU')
    broker_config = run.read(broker_config_path)
    life_id = broker_config['life_id']
    lane = run.policy.LANES[life_id]
    run.require(root == Path(broker_config['remote_root']) and not root.exists(), 'new_pair_root_only')
    root.mkdir(parents=True, mode=0o700)
    data = Path('/localhome/local-rohing/orch_r111_grid_cpu_v4b/private')
    for split in ('TRAIN', 'DEV', 'FINAL'):
        shutil.copyfile(data / (split + '_PRIVATE.json'), root / (split + '.json'))
    shutil.copyfile('/localhome/local-rohing/orch_r111_route_pair_assets_20260915/LEGACY_READOUT.json', root / 'LEGACY_READOUT.json')
    shutil.copyfile('/localhome/local-rohing/orch_r109_grid_node5_7_20260915_attempt1/SERVICE_IDENTITY.json', root / 'SERVICE_IDENTITY.json')
    shutil.copyfile(broker_config_path, root / 'BROKER_CONFIG.json')
    shutil.copyfile(launch_path, root / 'BROKER_LAUNCH.json')
    tasks = {split: run.read(root / (split + '.json')) for split in ('TRAIN', 'DEV', 'FINAL')}
    run.require(run.policy.digest(tasks) == broker_config['cohort_sha256'], 'exact_previously_frozen_cohort')
    run.require(broker_config['train_tasks'] == {task['id']: task['task_sha256'] for task in tasks['TRAIN']}, 'exact_train_registry')
    run.require(set(broker_config['excluded_task_ids']) == {task['id'] for split in ('DEV', 'FINAL') for task in tasks[split]}, 'all_held_excluded')
    from gpu.orch_r111_grid_prepare import MODEL, BUNDLE
    from gpu.orch_l2_rich_math_bootstrap import BUNDLE_SHA
    base = run.original.portable.verify_base_files(BUNDLE, MODEL, expected_manifest_sha256=BUNDLE_SHA)
    run.require(base['expected_base_sha256'] == run.policy.game.BASE_SHA, 'BASE_identity')
    tokenizer = run.original.portable.source.native.load_local_tokenizer(MODEL)
    lengths = []
    for split, group in tasks.items():
        for task in group:
            messages = [dict(role='system', content=run.EPISODE if split == 'TRAIN' else run.policy.HELD_PROMPT),
                dict(role='user', content=json.dumps(run.policy.public_observation(task, run.policy.game.initial(task)), sort_keys=True))]
            count = len(tokenizer.apply_chat_template(messages, tokenize=True, add_generation_prompt=True, return_dict=False))
            run.require(count + 2048 <= 16384, 'native_context')
            lengths.append(count)
    legacy = run.read(root / 'LEGACY_READOUT.json')
    run.require(len(legacy['old_bank']) == 16 and all(any(case['kind'] == kind for case in legacy['held']['cases']) for kind in ('true', 'fault')), 'legacy16_audit2')
    from gpu import astra_goal_quality_train as legacy_source
    cases = [next(case for case in legacy['held']['cases'] if case['kind'] == kind) for kind in ('true', 'fault')]
    legacy_messages = [legacy_source.memory.memory_messages(item['event'], 0) for item in legacy['old_bank']]
    legacy_messages += [legacy_source.memory.audit._messages(case, False) for case in cases]
    for messages in legacy_messages:
        count = len(tokenizer.apply_chat_template(messages, tokenize=True, add_generation_prompt=True, return_dict=False))
        run.require(count + 512 <= 16384, 'exact_legacy_native_context')
    config = dict(schema='R115_F4_NATIVE_V1', root=str(root), life_id=life_id, physical=lane['physical'], uuid=lane['uuid'],
        parent_model=lane['parent_model'], model_dir=MODEL, base_sha256=run.policy.game.BASE_SHA, optimizer_steps=0,
        lambda_rehearsal='N/A_FROZEN_BASE_NO_SLEEP', cohort_sha256=run.policy.digest(tasks),
        split_sha256={split: run.policy.digest(group) for split, group in tasks.items()},
        inputs={name: run.sha(root / name) for name in ('TRAIN.json', 'DEV.json', 'FINAL.json', 'LEGACY_READOUT.json',
            'SERVICE_IDENTITY.json', 'BROKER_CONFIG.json', 'BROKER_LAUNCH.json')},
        source_manifest_sha256=run.sha(run.SOURCE / 'R115_SOURCE_SHA256.json'),
        prompts=dict(episode=run.EPISODE, presleep=run.policy.PRESLEEP_PROMPT, reflection=run.policy.REFLECTION_PROMPT,
            open_turn=run.policy.OPEN_PROMPT, held=run.policy.HELD_PROMPT, focused=run.policy.FOCUSED_PROMPT),
        decoder=run.policy.DECODER, max_native=run.MAX_NATIVE, max_parent=run.MAX_PARENT,
        train_end_unix=run.TRAIN_END, hard_end_unix=run.END, morning_final_unix=run.policy.FINAL_UNIX,
        final0_before_first_episode=True, reuse_TRAIN16_cyclic_pairs=True,
        context_memory='last two own TRAIN reflections; all older raw retained; no held or attached open',
        prepared_unix=time.time())
    run.write(root / 'CONFIG.json', config)
    for name in ('calls', 'readout_calls', 'sealed_readout_calls', 'parent_queue'):
        (root / name).mkdir(mode=0o700)
    run.write(root / 'CPU_READY.json', dict(base=base, initial_prompt_tokens_min=min(lengths),
        initial_prompt_tokens_max=max(lengths), model_loaded=False, CUDA_initialized=torch.cuda.is_initialized(),
        config=run.ref(root / 'CONFIG.json'), new_native_calls=0, new_parent_calls=0, optimizer_steps=0))
    run.validate(root)
    return run.ref(root / 'CPU_READY.json')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--broker-config', type=Path, required=True)
    parser.add_argument('--launch-receipt', type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(prepare(args.root, args.broker_config, args.launch_receipt), sort_keys=True))
