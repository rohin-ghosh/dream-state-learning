"""One R209 all-pair candidate with a measured pilot; private data stays private."""

import argparse
from collections import defaultdict
import datetime
import hashlib
import json
import math
import os
from pathlib import Path
import random
import time


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def write(path, value):
    with Path(path).open('x') as stream:
        json.dump(value, stream, indent=2, sort_keys=True, allow_nan=False)


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def partition(batch, rank, world_size=4, local_batch=16):
    require(len(batch) == world_size * local_batch and 0 <= rank < world_size, 'full_disjoint_global_batch')
    return batch[rank * local_batch:(rank + 1) * local_batch]


def measured_eta(comparisons, elapsed_seconds, now_unix, selection_seconds=None):
    require(comparisons > 0 and elapsed_seconds >= 300, 'actual_five_minute_positive_progress')
    rate = comparisons / elapsed_seconds
    remaining = (1000000 - comparisons) / rate
    result = dict(actual_pilot_comparisons=comparisons, elapsed_seconds=elapsed_seconds,
        aggregate_pairs_per_second=rate, fitting_remaining_seconds=remaining,
        predicted_fit_finish_utc=datetime.datetime.fromtimestamp(now_unix + remaining, datetime.timezone.utc).isoformat(),
        measured_at_utc=datetime.datetime.fromtimestamp(now_unix, datetime.timezone.utc).isoformat(),
        selection_additional_seconds=selection_seconds, measured_four_gpu_rate=True, completion_receipt=False)
    if selection_seconds is not None:
        require(math.isfinite(selection_seconds) and selection_seconds >= 0, 'declared_selection_cost')
        result['conservative_remaining_seconds'] = 1.25 * (remaining + selection_seconds) + 900
    return result


class PairStream:
    def __init__(self, rows, tokenizer, config):
        from gpu import ny_caption_judge as helpers
        self.schedule = random.Random(config['seed'])
        self.groups = defaultdict(list)
        for row in rows:
            if row['votes'] > 0:
                self.groups[row['contest_id']].append(row)
        self.names = sorted(name for name, group in self.groups.items() if len(group) > 1)
        require(len(self.names) == 180, 'all180_training_contests_not_widegap179')
        self.tokenizer = tokenizer
        self.canonical = helpers.canonical_input
        self.config = config
        self.cache = {}
        self.proposed = 0
        self.consumed = 0

    def eligible(self, row):
        key = (row['contest_id'], row['caption_family_sha256'])
        if key not in self.cache:
            self.cache[key] = len(self.tokenizer(self.canonical(row['scene'], row['caption']), truncation=False)['input_ids'])
        return self.cache[key] <= self.config['max_length']

    def batch(self):
        batch = []
        while len(batch) < 64:
            self.proposed += 1
            require(self.proposed <= 5000000, 'bounded_pair_proposals')
            name = self.schedule.choice(self.names)
            left, right = self.schedule.sample(self.groups[name], 2)
            target = all_pair_target(left, right, self.config['vote_cap'])
            if self.eligible(left) and self.eligible(right):
                batch.append(dict(left=left, right=right, **target))
                self.consumed += 1
        return batch


def all_pair_target(left, right, vote_cap=100):
    require(left['contest_id'] == right['contest_id'] and left['caption_family_sha256'] != right['caption_family_sha256'], 'distinct_within_contest_pair')
    require(min(left['votes'], right['votes']) > 0, 'defined_empirical_ratings')
    gap = left['mean'] - right['mean']
    return dict(winner=1.0 if gap > 0 else 0.0 if gap < 0 else 0.5,
        reliability=min(left['votes'], right['votes'], vote_cap) / vote_cap)


def weighted_loss(scores, batch, torch, distributed):
    winners = torch.tensor([pair['winner'] for pair in batch], device=scores.device, dtype=scores.dtype)
    weights = torch.tensor([pair['reliability'] for pair in batch], device=scores.device, dtype=scores.dtype)
    denominator = weights.detach().sum()
    distributed.all_reduce(denominator, op=distributed.ReduceOp.SUM)
    numerator = (torch.nn.functional.binary_cross_entropy_with_logits(scores[::2] - scores[1::2], winners, reduction='none') * weights).sum()
    return numerator * distributed.get_world_size() / denominator


def train(root):
    import torch
    import torch.distributed as distributed
    from torch.nn.parallel import DistributedDataParallel
    from transformers import AutoModelForSequenceClassification, AutoTokenizer
    from peft import PeftModel
    from gpu import ny_caption_judge as helpers
    from four_gpu_admission import verify_devices
    os.umask(0o077)
    config = json.loads((root / 'PILOT_CONFIG.json').read_bytes())
    rank = int(os.environ['LOCAL_RANK'])
    require(int(os.environ['WORLD_SIZE']) == 4 and config['physical'] in ([0, 1, 2, 3], [4, 5, 6, 7]), 'four_assigned_ranks_only')
    verify_devices(config)
    torch.set_num_threads(2)
    torch.cuda.set_device(rank)
    distributed.init_process_group('nccl', timeout=datetime.timedelta(minutes=3), device_id=torch.device('cuda', rank))
    require(torch.cuda.device_count() == 4, 'exact_four_visible_devices')
    helpers.verify_runtime_device_uuid(torch.cuda.get_device_properties(rank).uuid, config['device_uuids'][rank])
    require(torch.cuda.is_bf16_supported(), 'native_BF16')
    torch.manual_seed(config['seed'])
    random.seed(config['seed'])
    packet = json.loads((root / 'PACKET.json').read_bytes())
    if rank == 0:
        for relative, reference in config['source_pin'].items():
            require(sha(root / relative) == reference, 'exact_R209_runtime_and_selection')
        for relative, reference in packet['files'].items():
            require(sha(root / relative) == reference['sha256'], 'exact_received_packet_file')
    distributed.barrier()
    tokenizer = AutoTokenizer.from_pretrained(config['model_root'], local_files_only=True, trust_remote_code=False)
    tokenizer.pad_token = tokenizer.eos_token
    tokenizer.padding_side = 'right'
    model, info = AutoModelForSequenceClassification.from_pretrained(config['model_root'], num_labels=1,
        pad_token_id=tokenizer.pad_token_id, local_files_only=True, trust_remote_code=False, use_safetensors=True,
        dtype=torch.bfloat16, device_map={'': 'cuda:' + str(rank)}, attn_implementation='sdpa', output_loading_info=True)
    require(not info.get('mismatched_keys') and not info.get('error_msgs')
        and all(name.startswith('score.') for name in info.get('missing_keys', [])), 'exact_frozen_Qwen_backbone')
    model = PeftModel.from_pretrained(model, str(root / 'warmstart'), is_trainable=True, local_files_only=True)
    trainable = [name for name, parameter in model.named_parameters() if parameter.requires_grad]
    require(trainable and all('lora_' in name or 'score.modules_to_save' in name for name in trainable), 'only_LoRA_and_scalar_head_trainable')
    model.gradient_checkpointing_enable(gradient_checkpointing_kwargs={'use_reentrant': False})
    model.enable_input_require_grads()
    model = DistributedDataParallel(model, device_ids=[rank], output_device=rank, broadcast_buffers=False)
    optimizer = torch.optim.AdamW([parameter for parameter in model.parameters() if parameter.requires_grad], lr=config['learning_rate'])
    with (root / 'TRAIN_ROWS.private.jsonl').open() as stream:
        rows = [json.loads(line) for line in stream]
    require(len(rows) == packet['training_rows'], 'exact_TRAIN_packet_rows')
    schedule = PairStream(rows, tokenizer, config)
    output = root / 'training'
    if rank == 0:
        output.mkdir(mode=0o700)
        write(output / 'LOADED.json', dict(status='ACTUAL_FOUR_GPU_DDP_LOADED', loaded_unix=time.time(),
            world_size=4, device_uuids=config['device_uuids'], warmstart_step=6250, rank=config['lora_rank'],
            packet_sha256=sha(root / 'PACKET.json'), config_sha256=sha(root / 'PILOT_CONFIG.json'),
            target_comparisons=1000000, global_batch=64, learning_rate=config['learning_rate'],
            trainable_parameter_count=sum(parameter.numel() for parameter in model.parameters() if parameter.requires_grad)))
    distributed.barrier()
    selection_rows = []
    with (root / 'SELECTION_ROWS.private.jsonl').open() as stream:
        for line in stream:
            row = json.loads(line)
            if schedule.eligible(row):
                selection_rows.append(row)
    selection_rows = helpers.natural_heldout_rows(selection_rows, 256, config['seed'] + 41)
    selection_steps = [8, 3907, 7813, 11719, 15625]
    best_score = None
    best_step = None
    selection_elapsed = 0.0
    completed = 0
    elapsed = 0
    pilot_done = False
    while completed < 15625:
        require(time.time() < config['training_end_unix'] - 180, 'bounded_training_wall')
        started = time.monotonic()
        model.train()
        batch = partition(schedule.batch(), rank)
        private_rows = [row for pair in batch for row in (pair['left'], pair['right'])]
        encoded = tokenizer([helpers.canonical_input(row['scene'], row['caption']) for row in private_rows],
            padding=True, truncation=False, return_tensors='pt')
        require(encoded['input_ids'].shape[1] <= config['max_length'], 'no_input_truncation')
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
        if rank == 0 and (completed == 1 or completed % 10 == 0):
            write(output / f'PROGRESS_{completed:06d}.json', dict(observed_unix=time.time(), completed_updates=completed,
                aggregate_comparisons=completed * 64, elapsed_seconds=elapsed,
                pairs_per_second=completed * 64 / elapsed, full_five_minute_pilot=elapsed >= 300))
        if completed in selection_steps:
            selection_started = time.monotonic()
            selected_rows = selection_rows[rank::4]
            predictions = []
            model.eval()
            with torch.no_grad():
                for offset in range(0, len(selected_rows), 16):
                    chunk = selected_rows[offset:offset + 16]
                    encoded_selection = tokenizer([helpers.canonical_input(row['scene'], row['caption']) for row in chunk], padding=True, truncation=False, return_tensors='pt')
                    values = model.module(**encoded_selection.to('cuda:' + str(rank))).logits[:, 0].float().cpu().tolist()
                    predictions.extend((row['contest_id'], row['mean'], value) for row, value in zip(chunk, values))
            gathered = [None] * 4
            distributed.all_gather_object(gathered, predictions)
            score = macro_spearman([item for part in gathered for item in part], helpers.average_ranks)
            improved = best_score is None or score > best_score
            if improved:
                best_score, best_step = score, completed
            if rank == 0:
                private = output / 'selection'
                private.mkdir(mode=0o700, exist_ok=True)
                write(private / f'STEP_{completed:06d}.private.json', dict(step=completed, macro_mean_rating_spearman=score,
                    best_step=best_step, examples=len(selection_rows), selection_rule='MAX_MACRO_WITHIN_CONTEST_SPEARMAN_EARLIEST_TIE', no_acceptance_gate=True))
                if improved:
                    model.module.save_pretrained(output / f'selected_step_{completed:06d}', safe_serialization=True)
            distributed.barrier()
            selection_elapsed += time.monotonic() - selection_started
        if elapsed >= 300 and not pilot_done:
            checkpoint = save_checkpoint(output, 'pilot_checkpoint', model, optimizer, schedule, completed, rank, torch, distributed)
            if rank == 0:
                remaining_selection = sum(step > completed for step in selection_steps) * selection_elapsed / max(1, sum(step <= completed for step in selection_steps))
                eta = measured_eta(completed * 64, elapsed, time.time(), remaining_selection)
                eta['predicted_finish_utc'] = datetime.datetime.fromtimestamp(time.time() + eta['fitting_remaining_seconds'] + remaining_selection, datetime.timezone.utc).isoformat()
                write(output / 'PILOT_COMPLETE.json', dict(status='ACTUAL_FIVE_MINUTE_PILOT_SAME_CANDIDATE_CONTINUES',
                    observed_unix=time.time(), completed_updates=completed, comparison_cursor=completed * 64,
                    remaining_comparisons=1000000 - completed * 64, checkpoint=str(checkpoint), **eta))
                write(output / 'SUSTAINED_STARTED.json', dict(started_unix=time.time(), next_update=completed + 1,
                    no_optimizer_or_rng_reset=True, predicted_finish_utc=eta['predicted_finish_utc'], hard_end_unix=config['training_end_unix']))
            distributed.barrier()
            pilot_done = True
    save_checkpoint(output, 'completed_checkpoint', model, optimizer, schedule, completed, rank, torch, distributed)
    if rank == 0:
        write(output / 'COMPLETED.json', dict(completed_unix=time.time(), optimizer_updates=completed,
            comparisons=completed * 64, selected_step=best_step, lora_rank=config['lora_rank'], full_training_completed=True))
    distributed.destroy_process_group()


def macro_spearman(predictions, average_ranks):
    groups = defaultdict(list)
    for contest, mean, score in predictions:
        groups[contest].append((mean, score))
    correlations = []
    for group in groups.values():
        target = average_ranks([item[0] for item in group])
        predicted = average_ranks([item[1] for item in group])
        target = [value - sum(target) / len(target) for value in target]
        predicted = [value - sum(predicted) / len(predicted) for value in predicted]
        denominator = math.sqrt(sum(value * value for value in target) * sum(value * value for value in predicted))
        if denominator:
            correlations.append(sum(left * right for left, right in zip(target, predicted)) / denominator)
    require(correlations, 'defined_checkpoint_selection_Spearman')
    return sum(correlations) / len(correlations)


def save_checkpoint(output, name, model, optimizer, schedule, completed, rank, torch, distributed):
    checkpoint = output / name
    if rank == 0:
        checkpoint.mkdir(mode=0o700)
        model.module.save_pretrained(checkpoint / 'adapter', safe_serialization=True)
    distributed.barrier()
    torch.save(dict(optimizer=optimizer.state_dict(), torch_rng=torch.get_rng_state(), cuda_rng=torch.cuda.get_rng_state(),
        python_rng=random.getstate(), global_pair_cursor=schedule.consumed, pair_proposals=schedule.proposed,
        pair_rng_state=schedule.schedule.getstate(), completed_updates=completed), checkpoint / f'optimizer_rng_rank_{rank}.private.pt')
    write(checkpoint / f'RANK_{rank}.json', dict(rank=rank, pid=os.getpid(), optimizer_updates=completed,
        comparisons=completed * 16, max_memory_allocated=torch.cuda.max_memory_allocated(),
        max_memory_reserved=torch.cuda.max_memory_reserved(), optimizer_sha256=sha(checkpoint / f'optimizer_rng_rank_{rank}.private.pt')))
    distributed.barrier()
    return checkpoint


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', type=Path, required=True)
    arguments = parser.parse_args()
    train(arguments.root.resolve())
