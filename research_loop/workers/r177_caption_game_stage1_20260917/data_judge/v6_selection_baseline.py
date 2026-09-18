"""Read frozen v6 on CPU and release aggregate diagnostics, never a new judge."""

import argparse
from collections import defaultdict
import json
import math
import os
from pathlib import Path
import time

from gpu import ny_caption_data as data
from gpu import ny_caption_judge as judge


def prior_from_training(rows, config):
    groups = defaultdict(lambda: [0.0, 0.0, 0.0, 0.0])
    for row in rows:
        weight = judge.vote_weight(row['votes'], config['vote_weight_cap'])
        group = groups[row['contest_id']]
        for index, mass in enumerate(judge.soft_target(row['counts'], config['smoothing'])):
            group[index] += mass*weight
        group[3] += weight
    return [sum(group[index]/group[3] for group in groups.values())/len(groups) for index in range(3)]


def spread(rows, scores, temperature):
    groups = defaultdict(list)
    for row, logits in zip(rows, scores):
        groups[row['contest_id']].append(sum(judge.probabilities(logits, temperature)[1:]))
    values = [value for group in groups.values() for value in group]
    def deviation(group):
        mean = sum(group)/len(group)
        return math.sqrt(sum((value-mean)**2 for value in group)/len(group))
    return dict(q_mean=sum(values)/len(values), q_std=deviation(values), q_min=min(values), q_max=max(values),
        macro_contest_q_std=sum(deviation(group) for group in groups.values())/len(groups),
        macro_contest_q_range=sum(max(group)-min(group) for group in groups.values())/len(groups))


def run(root):
    started = time.time()
    data.require(os.environ.get('CUDA_VISIBLE_DEVICES') == '' and os.environ.get('HF_HUB_OFFLINE') == '1', 'CPU_only_offline_diagnostic')
    completed = data.bound(data.file_ref(root/'COMPLETED.json'))
    trained = data.bound(completed['judge_config'])
    data.require(trained['audit_mode'] == 'PREDECLARED_DISJOINT_JUDGE_DEV_AUDIT'
        and trained['locked_judge_validation_consumed'] is False, 'frozen_development_only_run')
    for module in (data, judge):
        path = Path(module.__file__).resolve()
        data.require(data.file_ref(path)['sha256'] == trained['evaluator_source_sha256'][path.name], 'exact_frozen_runtime')
    config = data.bound(trained['training_config'])
    plan = data.load_development_plan(config['development_plan'], config['development_source_manifest'])
    training = judge.balanced_training_rows(data.evaluator_rows(config['data_manifest'], 'judge_train',
        contest_ids=plan['subsets']['judge_train']), config['per_contest_per_band'], config['seed'])
    selection = judge.natural_heldout_rows(data.evaluator_rows(config['data_manifest'], 'judge_dev',
        contest_ids=plan['subsets']['model_selection']), config['heldout_per_contest'], config['seed']+1)
    data.require(len(selection) <= 2000, 'bounded_selection_CPU_examples')
    prior = prior_from_training(training, config)
    del training
    for reference in trained['checkpoint'].values():
        actual = data.file_ref(reference['path'])
        data.require(actual['sha256'] == reference['sha256'] and actual['bytes'] == reference['bytes'], 'frozen_checkpoint_bytes')
    import torch
    from transformers import AutoModelForSequenceClassification, AutoTokenizer
    from transformers.utils import logging
    logging.set_verbosity_error()
    torch.set_num_threads(2)
    data.require(not torch.cuda.is_initialized(), 'CPU_model_no_CUDA')
    selected = Path(trained['selected_checkpoint'])
    tokenizer = AutoTokenizer.from_pretrained(str(selected/'tokenizer'), local_files_only=True, trust_remote_code=False)
    model = judge.load_pretrained_classifier(AutoModelForSequenceClassification, selected/'humor', 3, 'cpu')
    model.eval()
    logits, token_count = [], 0
    with torch.no_grad():
        for start in range(0, len(selection), 16):
            data.require(time.time()-started < 240, 'finite_CPU_diagnostic_wall')
            batch = selection[start:start+16]
            encoded = tokenizer([judge.canonical_input(row['scene'], row['caption']) for row in batch],
                truncation=False, padding=True, return_tensors='pt')
            data.require(encoded['input_ids'].shape[1] <= 512, 'no_diagnostic_input_truncation')
            token_count += encoded['input_ids'].numel()
            data.require(token_count <= 1024000, 'finite_CPU_diagnostic_tokens')
            logits.extend(model(**encoded).logits.float().tolist())
    targets = [judge.empirical_target(row['counts']) for row in selection]
    prior_logits = [[math.log(value) for value in prior]]*len(selection)
    prior_metrics = judge.heldout_metrics(prior_logits, targets, 1)
    prior_metrics.update(judge.rank_metrics(selection, prior_logits, 1))
    prior_metrics.update(spread(selection, prior_logits, 1))
    result = dict(schema='NY_FROZEN_V6_SELECTION_DIAGNOSTIC_V1', completed_judge_config_sha256=completed['judge_config']['sha256'],
        model_selection_examples=len(selection), training_prior_model_selection=prior_metrics,
        selected_step=trained['selected_step'], selected_checkpoint_unchanged=True,
        selection_q_spread_before_temperature=spread(selection, logits, 1),
        selection_q_spread_after_temperature=spread(selection, logits, trained['calibration']['temperature']),
        measured_selection=judge.heldout_metrics(logits, targets, 1),
        CPU_model_examples=len(selection), CPU_model_tokens=token_count, GPU_calls=0,
        CUDA_initialized=torch.cuda.is_initialized(), elapsed_seconds=time.time()-started,
        observed_unix=time.time(), locked_validation_read=False, FINAL_read=False, threshold_changed=False,
        captions_included=False, contest_ids_included=False, development_reuse_provisional=True)
    data.require(not result['CUDA_initialized'], 'CPU_diagnostic_never_initialized_CUDA')
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', required=True)
    args = parser.parse_args()
    print(json.dumps(run(Path(args.root).resolve()), sort_keys=True))
