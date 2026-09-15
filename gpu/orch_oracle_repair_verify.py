"""CPU-only terminal token/provenance replay without any new model calls."""

import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path

from gpu import astra_portable_actor_bundle as portable
from gpu.orch_math_replication_guard import verify_sources
from organism_v6 import orch_oracle_repair as policy


def check_tokens(row, tokenizer):
    result = row['call']
    actor_ids = tokenizer.apply_chat_template(result['messages'], tokenize=True,
                  add_generation_prompt=True, return_dict=False)
    prefix_ids = tokenizer.apply_chat_template(row['student_prefix'], tokenize=True,
                   add_generation_prompt=True, return_dict=False)
    target_ids = result['token_ids']
    terminal = bool(target_ids) and target_ids[-1] == tokenizer.eos_token_id
    raw = tokenizer.decode(target_ids[:-1] if terminal else target_ids,
                           skip_special_tokens=False, clean_up_tokenization_spaces=False)
    if (not 0 < len(actor_ids) <= 2048 or len(result['messages']) > 6
            or len(target_ids) > 512 or result['prompt_tokens'] != len(actor_ids)
            or result['terminal'] != terminal or raw != result['raw'] or raw != row['target']
            or row['target_sha256'] != policy.text_hash(raw)
            or prefix_ids != row['prefix_token_ids'] or row['target_token_ids'] != target_ids
            or row['labels'] != [-100] * len(prefix_ids) + target_ids or row['teacher_loss']):
        raise ValueError('exact_token_mask_or_raw_replay_failure')
    return dict(actor_prompt_tokens=len(actor_ids), neutral_prefix_tokens=len(prefix_ids),
                generated_tokens=len(target_ids) - int(terminal), generated_including_terminal=len(target_ids))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--model-dir', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    options = parser.parse_args()
    if os.environ.get('CUDA_VISIBLE_DEVICES') != '' or os.environ.get('HF_HUB_OFFLINE') != '1':
        raise ValueError('offline_cpu_only_verification_required')
    inventory = json.loads((options.root / 'SOURCE_SHA256.json').read_text())
    verify_sources(options.root / 'source', options.root / 'SOURCE_SHA256.json')
    tokenizer = portable.source.native.load_local_tokenizer(options.model_dir)
    rows = []
    own_processes = []
    for shard in range(4):
        directory = options.root / 'run' / f'shard{shard}'
        mounted = json.loads((directory / 'MOUNTED.json').read_text())
        complete = json.loads((directory / 'COMPLETE.json').read_text())
        if (mounted['actual_adapter_state'] != portable.PARENT_STATE
                or complete['adapter_state'] != portable.PARENT_STATE
                or not complete['frozen_base_unchanged']
                or len(mounted['per_named_parameter_hashes']) != 392
                or complete['driver_sha256'] != inventory['gpu/orch_oracle_repair_native.py']
                or complete['policy_sha256'] != inventory['organism_v6/orch_oracle_repair.py']):
            raise ValueError('terminal_actor_or_source_binding_failure')
        paths = sorted(directory.glob('CALL_*.json'))
        if len(paths) != complete['native_calls']:
            raise ValueError('terminal_call_count_failure')
        for path in paths:
            row = json.loads(path.read_text())
            counts = check_tokens(row, tokenizer)
            rows.append(dict(task_id=row['task_id'], branch=row['branch'], kind=row['kind'],
                             source_sha256=policy.sha256(path), **counts))
        identity = json.loads((options.root / 'run' / f'OWNED_{shard}.json').read_text())
        proc = Path('/proc') / str(identity['pid'])
        same_live_process = False
        try:
            same_live_process = (proc / 'stat').read_text().rsplit(')', 1)[1].split()[19] == identity['start_ticks']
        except FileNotFoundError:
            pass
        if same_live_process:
            raise ValueError('owned_native_process_not_released')
        own_processes.append(dict(pid=identity['pid'], start_ticks=identity['start_ticks'], released=True))
    terminal = json.loads((options.root / 'run/TERMINAL.json').read_text())
    if terminal['status'] != 'COMPLETE' or terminal['elapsed_seconds'] > 3600 or len(rows) > 96:
        raise ValueError('bounded_terminal_failure')
    policy.write(options.output, dict(created_utc=datetime.now(timezone.utc).isoformat(),
                 status='PASS', cuda_visible_devices='', new_model_calls=0, rows_checked=len(rows),
                 exact_raw_and_token_masks=True, frozen_source_verified=True,
                 actual_mounted_and_final_state=portable.PARENT_STATE,
                 owned_processes=own_processes, rows=rows, terminal=terminal))


if __name__ == '__main__':
    main()
