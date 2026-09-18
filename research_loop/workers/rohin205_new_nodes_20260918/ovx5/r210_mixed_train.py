"""R210 exact-state continuation with declared TRAIN-only crossed-scene assumptions."""

import argparse
from collections import Counter
import datetime
import hashlib
import json
import math
import os
from pathlib import Path
import random
import time

from ddp_pilot import PairStream, all_pair_target, macro_spearman, partition, require, save_checkpoint, sha, weighted_loss, write


CASE_IDS = '6763a62cf349e969c1dd7ecad0637c8718fef45572eced5a07a50406e3de66ba'


class MixedPairStream(PairStream):
    def __init__(self, rows, tokenizer, config):
        super().__init__(rows, tokenizer, config)
        self.scene_groups = {}
        self.strong = {}
        for name in self.names:
            groups = {row['scene_group_sha256'] for row in self.groups[name]}
            require(len(groups) == 1, 'one_source_scene_group_per_TRAIN_contest')
            self.scene_groups[name] = next(iter(groups))
            ordered = sorted(self.groups[name], key=lambda row: (-row['mean'], -row['votes'], row['caption_family_sha256']))
            self.strong[name] = ordered[:max(1, math.ceil(len(ordered) * 0.20))]
        self.donors = {name: [other for other in self.names if self.scene_groups[other] != self.scene_groups[name]] for name in self.names}
        require(all(self.donors.values()), 'different_TRAIN_scene_group_available_for_every_recipient')

    def eligible(self, row):
        key = (row['scene'], row['caption_family_sha256'])
        if key not in self.cache:
            self.cache[key] = len(self.tokenizer(self.canonical(row['scene'], row['caption']), truncation=False)['input_ids'])
        return self.cache[key] <= self.config['max_length']

    def batch(self):
        batch = []
        while len(batch) < 64:
            self.proposed += 1
            require(self.proposed <= 5000000, 'bounded_R210_pair_proposals')
            name = self.schedule.choice(self.names)
            crossed = len(batch) % 4 == 0
            if crossed:
                left = self.schedule.choice(self.strong[name])
                donor_name = self.schedule.choice(self.donors[name])
                donor = self.schedule.choice(self.strong[donor_name])
                if left['caption_family_sha256'] == donor['caption_family_sha256']:
                    continue
                right = dict(donor, scene=left['scene'])
                require(left['scene_group_sha256'] != donor['scene_group_sha256'], 'different_original_scene_groups')
                target = dict(winner=1.0, reliability=min(left['votes'], donor['votes'], self.config['vote_cap']) / self.config['vote_cap'])
            else:
                left, right = self.schedule.sample(self.groups[name], 2)
                target = all_pair_target(left, right, self.config['vote_cap'])
            if self.eligible(left) and self.eligible(right):
                batch.append(dict(left=left, right=right, pair_type='CROSSED_SCENE_ASSUMPTION' if crossed else 'WITHIN_CONTEST_OBSERVED', **target))
                self.consumed += 1
        require(sum(pair['pair_type'] == 'CROSSED_SCENE_ASSUMPTION' for pair in batch) == 16, 'exact16cross48within_per64_draws')
        return batch


def restore_optimizer_rng(model, optimizer, schedule, payload, rank, torch):
    require(payload['global_pair_cursor'] == payload['completed_updates'] * 64, 'exact_saved_global_pair_cursor')
    optimizer.load_state_dict(payload['optimizer'])
    steps = {int(state['step'].item()) for state in optimizer.state.values() if 'step' in state}
    require(steps == {payload['completed_updates']}, 'every_restored_AdamW_step_matches_checkpoint')
    require(all(group['lr'] == 3e-5 for group in optimizer.param_groups), 'unchanged_learning_rate')
    schedule.schedule.setstate(payload['pair_rng_state'])
    schedule.consumed = payload['global_pair_cursor']
    schedule.proposed = payload['pair_proposals']
    random.setstate(payload['python_rng'])
    torch.set_rng_state(payload['torch_rng'])
    torch.cuda.set_rng_state(payload['cuda_rng'], device=rank)
    return payload['completed_updates']


def checkpoint_diagnostics(output, completed, model, tokenizer, selection_rows, cases, rank, torch, distributed):
    from gpu import ny_caption_judge as helpers
    from gpu import ny_caption_contrast as contrast
    model.eval()

    def scores(rows):
        values = []
        with torch.no_grad():
            for offset in range(0, len(rows), 16):
                chunk = rows[offset:offset + 16]
                encoded = tokenizer([helpers.canonical_input(row['scene'], row['caption']) for row in chunk],
                    padding=True, truncation=False, return_tensors='pt')
                require(encoded['input_ids'].shape[1] <= 512, 'diagnostic_no_truncation')
                values.extend(model.module(**encoded.to('cuda:' + str(rank))).logits[:, 0].float().cpu().tolist())
        return values

    local_rows = selection_rows[rank::4]
    predictions = [(row['contest_id'], row['mean'], value) for row, value in zip(local_rows, scores(local_rows))]
    gathered = [None] * 4
    distributed.all_gather_object(gathered, predictions)
    spearman = macro_spearman([item for group in gathered for item in group], helpers.average_ranks)
    local_cases = cases[rank::4]
    records, unique = [], {}
    for case in local_cases:
        tokens = [len(tokenizer(helpers.canonical_input(case['scene'], case[side]), truncation=False)['input_ids']) for side in ['good', 'contrast']]
        record = {key: case[key] for key in ['case_id', 'contest', 'kind', 'top_index']}
        record['tokens'] = tokens
        if max(tokens) > 512:
            record.update(status='SKIPPED_OVERLENGTH', good_score=None, contrast_score=None)
        elif contrast.data.normalize_caption(case['good']) == contrast.data.normalize_caption(case['contrast']):
            record.update(status='SKIPPED_IDENTICAL', good_score=None, contrast_score=None)
        else:
            record['status'] = 'PENDING'
            for side in ['good', 'contrast']:
                unique.setdefault((case['scene'], case[side]), None)
        records.append(record)
    keys = list(unique)
    unique.update(zip(keys, scores([dict(scene=scene, caption=caption) for scene, caption in keys])))
    for case, record in zip(local_cases, records):
        if record['status'] == 'PENDING':
            record.update(status='SCORED', good_score=unique[(case['scene'], case['good'])], contrast_score=unique[(case['scene'], case['contrast'])])
    gathered = [None] * 4
    distributed.all_gather_object(gathered, records)
    if rank == 0:
        by_id = {record['case_id']: record for group in gathered for record in group}
        ordered = [by_id[case['case_id']] for case in cases]
        destination = output / 'checkpoint_diagnostics' / f'step_{completed:06d}'
        destination.mkdir(parents=True, mode=0o700)
        write(destination / 'SPEARMAN.private.json', dict(step=completed, examples=len(selection_rows), macro_mean_rating_spearman=spearman))
        write(destination / 'CONTRAST.private.json', dict(step=completed, case_ids_sha256=CASE_IDS,
            cases=600, contests=20, records=ordered, **contrast.summarize(ordered)))
        write(destination / 'COMPLETE.json', dict(completed_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
            optimizer_step=completed, cases=600, contests=20, scored=sum(record['status']=='SCORED' for record in ordered),
            case_ids_sha256=CASE_IDS, same_checkpoint_contrast_and_Spearman=True,
            all_checkpoint_exports_evaluated_not_only_improvements=True, no_tau_gate=True, private_scores_only=True))
    distributed.barrier()
    return spearman


def train(root):
    import torch
    import torch.distributed as distributed
    from torch.nn.parallel import DistributedDataParallel
    from transformers import AutoModelForSequenceClassification, AutoTokenizer
    from peft import PeftModel
    from gpu import ny_caption_judge as helpers
    from gpu import ny_caption_data as data
    from four_gpu_admission import verify_devices
    os.umask(0o077)
    config = json.loads((root / 'PILOT_CONFIG.json').read_bytes())
    rank = int(os.environ['LOCAL_RANK'])
    require(int(os.environ['WORLD_SIZE']) == 4, 'four_DDP_ranks')
    verify_devices(config)
    torch.set_num_threads(2)
    torch.cuda.set_device(rank)
    distributed.init_process_group('nccl', timeout=datetime.timedelta(minutes=3), device_id=torch.device('cuda', rank))
    helpers.verify_runtime_device_uuid(torch.cuda.get_device_properties(rank).uuid, config['device_uuids'][rank])
    require(torch.cuda.device_count() == 4 and torch.cuda.is_bf16_supported(), 'four_assigned_BF16_devices')
    packet = json.loads((root / 'PACKET.json').read_bytes())
    if rank == 0:
        for name, expected in config['source_pin'].items():
            require(sha(root / name) == expected, 'exact_R210_source_and_checkpoint')
        for name, expected in packet['files'].items():
            require(sha(root / name) == expected['sha256'], 'unchanged_TRAIN_packet')
    transition = json.loads((root / 'R210_TRANSITION.json').read_bytes())
    require(transition['old_owner_stopped'] and transition['resume_step'] == config['resume_step'], 'explicit_preserved_transition')
    distributed.barrier()
    tokenizer = AutoTokenizer.from_pretrained(config['model_root'], local_files_only=True, trust_remote_code=False)
    tokenizer.pad_token = tokenizer.eos_token
    tokenizer.padding_side = 'right'
    model, info = AutoModelForSequenceClassification.from_pretrained(config['model_root'], num_labels=1,
        pad_token_id=tokenizer.pad_token_id, local_files_only=True, trust_remote_code=False, use_safetensors=True,
        dtype=torch.bfloat16, device_map={'': 'cuda:' + str(rank)}, attn_implementation='sdpa', output_loading_info=True)
    require(not info.get('mismatched_keys') and not info.get('error_msgs') and all(name.startswith('score.') for name in info.get('missing_keys', [])), 'exact_frozen_Qwen_backbone')
    model = PeftModel.from_pretrained(model, str(root / 'resume_checkpoint/adapter'), is_trainable=True, local_files_only=True)
    trainable = [name for name, parameter in model.named_parameters() if parameter.requires_grad]
    require(trainable and all('lora_' in name or 'score.modules_to_save' in name for name in trainable), 'only_existing_LoRA_and_scalar_head_trainable')
    model.gradient_checkpointing_enable(gradient_checkpointing_kwargs={'use_reentrant': False})
    model.enable_input_require_grads()
    model = DistributedDataParallel(model, device_ids=[rank], output_device=rank, broadcast_buffers=False)
    optimizer = torch.optim.AdamW([parameter for parameter in model.parameters() if parameter.requires_grad], lr=config['learning_rate'])
    with (root / 'TRAIN_ROWS.private.jsonl').open() as stream:
        rows = [json.loads(line) for line in stream]
    require(len(rows) == packet['training_rows'], 'unchanged_TRAIN_row_count')
    schedule = MixedPairStream(rows, tokenizer, config)
    with (root / 'SELECTION_ROWS.private.jsonl').open() as stream:
        eligible = [json.loads(line) for line in stream]
    selection_rows = helpers.natural_heldout_rows([row for row in eligible if schedule.eligible(row)], 256, config['seed'] + 41)
    cases = json.loads((root / 'CASES.private.json').read_bytes())
    require(len(cases) == 600 and len({case['contest'] for case in cases}) == 20
        and data.digest([case['case_id'] for case in cases]) == CASE_IDS, 'same600_held_DEVELOPMENT_contrasts')
    require(all(data.digest({key:value for key,value in case.items() if key!='case_id'}) == case['case_id'] for case in cases), 'unaltered_cases')
    payload_path = root / 'resume_checkpoint' / f'optimizer_rng_rank_{rank}.private.pt'
    payload = torch.load(payload_path, map_location='cpu', weights_only=False)
    completed = restore_optimizer_rng(model, optimizer, schedule, payload, rank, torch)
    require(completed == config['resume_step'], 'exact_per_rank_saved_step')
    output = root / 'training'
    if rank == 0:
        output.mkdir(mode=0o700)
        write(output / 'LOADED.json', dict(status='R210_EXACT_MODEL_ADAMW_RNG_LOADED', loaded_unix=time.time(),
            rank=config['lora_rank'], completed_updates=completed, optimizer_reset=False, source_checkpoint_sha256=config['checkpoint_manifest_sha256'],
            world_size=4, physical=config['physical'], transition_sha256=sha(root / 'R210_TRANSITION.json'),
            trainable_layout_sha256=hashlib.sha256(json.dumps(trainable).encode()).hexdigest()))
    distributed.barrier()
    phase_start = completed
    elapsed = 0.0
    diagnostics_elapsed = 0.0
    measurements = []
    best_score = None
    best_step = None
    first_checkpoint = phase_start + 1
    checkpoint_steps = sorted(set([first_checkpoint, 3907, 7813, 11719, 15625] + list(range(1000, 15625, 1000))))
    checkpoint_steps = [step for step in checkpoint_steps if step > phase_start]
    while completed < 15625:
        stop = torch.tensor(int((root / 'STOP_AT_SAFE_BOUNDARY').exists() or time.time() >= config['training_end_unix'] - 300), device='cuda:' + str(rank))
        distributed.broadcast(stop, src=0)
        if stop.item():
            if completed not in checkpoint_steps:
                checkpoint = save_checkpoint(output, f'checkpoint_step_{completed:06d}', model, optimizer, schedule, completed, rank, torch, distributed)
                checkpoint_diagnostics(output, completed, model, tokenizer, selection_rows, cases, rank, torch, distributed)
                if rank == 0:
                    write(checkpoint / 'COMPLETE.json', dict(optimizer_step=completed, stopped_at_safe_boundary=True))
            if rank == 0:
                write(output / 'PHASE_STOPPED.json', dict(completed_updates=completed, stopped_unix=time.time(), pending_optimizer_update=False))
            break
        started = time.monotonic()
        model.train()
        global_batch = schedule.batch()
        batch = partition(global_batch, rank)
        encoded = tokenizer([helpers.canonical_input(row['scene'], row['caption']) for pair in batch for row in [pair['left'], pair['right']]],
            padding=True, truncation=False, return_tensors='pt')
        require(encoded['input_ids'].shape[1] <= 512, 'no_training_truncation')
        optimizer.zero_grad(set_to_none=True)
        scores = model(**encoded.to('cuda:' + str(rank))).logits[:, 0].float()
        loss = weighted_loss(scores, batch, torch, distributed)
        loss.backward()
        torch.nn.utils.clip_grad_norm_([parameter for parameter in model.parameters() if parameter.requires_grad], 1.0)
        optimizer.step()
        completed += 1
        torch.cuda.synchronize()
        duration = torch.tensor(time.monotonic() - started, device='cuda:' + str(rank), dtype=torch.float64)
        distributed.all_reduce(duration, op=distributed.ReduceOp.MAX)
        elapsed += duration.item()
        phase_comparisons = (completed - phase_start) * 64
        if rank == 0:
            write(output / f'UPDATE_{completed:06d}.json', dict(observed_unix=time.time(), completed_updates=completed,
                aggregate_comparisons=completed*64, phase_comparisons=phase_comparisons,
                pair_types=dict(Counter(pair['pair_type'] for pair in global_batch)), global_batch=64,
                fitting_elapsed_seconds=elapsed, phase_pairs_per_second=phase_comparisons/elapsed))
            if completed == first_checkpoint:
                write(output / 'NEW_MIX_STARTED.json', dict(first_completed_update=completed, previous_saved_step=phase_start,
                    started_unix=time.time(), actual_first_batch_counts=dict(Counter(pair['pair_type'] for pair in global_batch)),
                    optimizer_and_RNG_restored=True, no_weight_or_optimizer_reset=True,
                    constructed_negative_assumption_not_proof=True, TRAIN_only=True))
        if completed in checkpoint_steps:
            checkpoint = save_checkpoint(output, f'checkpoint_step_{completed:06d}', model, optimizer, schedule, completed, rank, torch, distributed)
            started_diagnostics = time.monotonic()
            score = checkpoint_diagnostics(output, completed, model, tokenizer, selection_rows, cases, rank, torch, distributed)
            if best_score is None or score > best_score:
                best_score, best_step = score, completed
            measurements.append(time.monotonic()-started_diagnostics)
            diagnostics_elapsed += measurements[-1]
            if rank == 0:
                write(checkpoint / 'COMPLETE.json', dict(optimizer_step=completed, full_optimizer_RNG=True, all_diagnostics_completed=True,
                    best_R210_step=best_step, diagnostic_seconds=measurements[-1]))
        if rank == 0 and completed % 10 == 0 and phase_comparisons:
            remaining_checkpoints = sum(step > completed for step in checkpoint_steps)
            future_diagnostics = remaining_checkpoints * sum(measurements) / len(measurements) if measurements else None
            rate = phase_comparisons / elapsed
            remaining_fit = (1000000-completed*64)/rate
            write(output / f'ETA_{completed:06d}.json', dict(observed_unix=time.time(), completed_updates=completed,
                phase_pairs_per_second=rate, actual_phase_fitting_seconds=elapsed, five_minute_measurement=elapsed>=300,
                diagnostics_so_far_seconds=diagnostics_elapsed, future_diagnostics_seconds=future_diagnostics,
                predicted_finish_utc=datetime.datetime.fromtimestamp(time.time()+remaining_fit+(future_diagnostics or 0),datetime.timezone.utc).isoformat(),
                complete=False, no_tau_gate=True))
    if rank == 0 and completed == 15625:
        write(output / 'COMPLETED.json', dict(completed_unix=time.time(), comparisons=1000000, optimizer_updates=completed,
            selected_R210_step=best_step, retained_R209_updates=phase_start,
            R210_within_comparisons=(completed-phase_start)*48, R210_crossed_comparisons=(completed-phase_start)*16,
            no_claim_all_cross_captions_invalid=True))
    distributed.destroy_process_group()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', type=Path, required=True)
    train(parser.parse_args().root.resolve())
