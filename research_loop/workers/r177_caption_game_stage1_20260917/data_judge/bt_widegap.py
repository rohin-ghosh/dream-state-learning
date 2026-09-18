"""R171 scalar Bradley-Terry humor ranking, with separate empirical-q calibration."""

from collections import defaultdict
import math
from pathlib import Path
import random
import time

from gpu import ny_caption_data as data
from research_loop.workers.r177_caption_game_stage1_20260917.data_judge import widegap_pairs as widegap
from research_loop.workers.r177_caption_game_stage1_20260917.data_judge import rank200_calibration_v3 as quality
from gpu import ny_caption_judge as helpers


LABEL_POLICY = widegap.LABEL_POLICY
PAIR_POLICY = widegap.PAIR_POLICY
RELIABILITY_POLICY = widegap.RELIABILITY_POLICY
MODEL_ID = 'Qwen/Qwen2.5-7B-Instruct'
MODEL_REVISION = 'a09a35458c702b33eeacc393d103063234e8bc28'


def positive_mass(row):
    counts = row['counts']
    data.require(len(counts) == 3 and all(type(value) is int and value >= 0 for value in counts)
        and sum(counts) == row['votes'] and row['votes'] > 0, 'actual_valid_vote_counts')
    return sum(counts[1:])/row['votes']


pair_target = widegap.pair_target


def bt_loss(left_scores, right_scores, winners, reliability, torch):
    signs = winners*2-1
    return (torch.nn.functional.softplus(-signs*(left_scores-right_scores))*reliability).sum()/reliability.sum()


def isotonic_calibration(scores, targets):
    data.require(scores and len(scores) == len(targets) and all(math.isfinite(value) for value in scores)
        and all(math.isfinite(value) and 0 <= value <= 1 for value in targets), 'finite_scalar_calibration_data')
    grouped = defaultdict(list)
    for score, target in zip(scores, targets):
        grouped[score].append(target)
    blocks = []
    for score in sorted(grouped):
        values = grouped[score]
        blocks.append(dict(low=score, high=score, total=sum(values), count=len(values)))
        while len(blocks) >= 2 and blocks[-2]['total']/blocks[-2]['count'] > blocks[-1]['total']/blocks[-1]['count']:
            after, before = blocks.pop(), blocks.pop()
            blocks.append(dict(low=before['low'], high=after['high'], total=before['total']+after['total'], count=before['count']+after['count']))
    return dict(method='UNWEIGHTED_NATURAL_HELD_CONTEST_ISOTONIC_POSITIVE_VOTE_MASS_V1', examples=len(scores),
        cutpoints=[(first['high']+second['low'])/2 for first, second in zip(blocks, blocks[1:])],
        values=[block['total']/block['count'] for block in blocks], human_validated=False)


def calibrated_q(calibration, score):
    data.require(math.isfinite(score), 'finite_scalar_score')
    for index, cutpoint in enumerate(calibration['cutpoints']):
        if score <= cutpoint:
            return calibration['values'][index]
    return calibration['values'][-1]


def ranking_metrics(rows, scores, top_k=5):
    data.require(rows and len(rows) == len(scores), 'joined_ranked_rows')
    groups = defaultdict(list)
    for row, score in zip(rows, scores):
        groups[row['contest_id']].append((score, positive_mass(row)))
    correlations, top_mass, base_mass = [], [], []
    concordance, comparable = 0.0, 0
    for group in groups.values():
        ranked_scores = helpers.average_ranks([item[0] for item in group])
        ranked_mass = helpers.average_ranks([item[1] for item in group])
        first = [value-sum(ranked_scores)/len(group) for value in ranked_scores]
        second = [value-sum(ranked_mass)/len(group) for value in ranked_mass]
        denominator = math.sqrt(sum(value**2 for value in first)*sum(value**2 for value in second))
        if denominator:
            correlations.append(sum(left*right for left, right in zip(first, second))/denominator)
        ordered = sorted(group, key=lambda item: item[0], reverse=True)
        top_mass.append(sum(item[1] for item in ordered[:top_k])/min(top_k, len(group)))
        base_mass.append(sum(item[1] for item in group)/len(group))
        for index, left in enumerate(group):
            for right in group[index+1:]:
                if left[1] == right[1]:
                    continue
                comparable += 1
                concordance += 0.5 if left[0] == right[0] else float((left[0]-right[0])*(left[1]-right[1]) > 0)
    return dict(examples=len(rows), contests=len(groups), defined_contests=len(correlations),
        macro_contest_spearman=sum(correlations)/len(correlations) if correlations else None,
        pairwise_concordance=concordance/comparable if comparable else None, comparable_pairs=comparable,
        sampled_top_k=top_k, sampled_macro_top_k_positive_vote_mass=sum(top_mass)/len(top_mass),
        sampled_macro_baseline_positive_vote_mass=sum(base_mass)/len(base_mass),
        minimum_sampled_rows_per_contest=min(map(len, groups.values())),
        maximum_sampled_rows_per_contest=max(map(len, groups.values())),
        literal_full_contest_top200_measured=False)


def probability_metrics(rows, values):
    targets = [positive_mass(row) for row in rows]
    return dict(examples=len(rows), binary_vote_mass_brier=sum((score-target)**2 for score, target in zip(values, targets))/len(rows),
        binary_vote_mass_log_loss=-sum(target*math.log(max(score, 1e-12))+(1-target)*math.log(max(1-score, 1e-12))
            for score, target in zip(values, targets))/len(rows), q_mean=sum(values)/len(values),
        q_std=math.sqrt(sum((value-sum(values)/len(values))**2 for value in values)/len(values)))


def prepare(config, tokenizer):
    plan = data.load_development_plan(config['development_plan'], config['development_source_manifest'])
    training = [row for row in data.evaluator_rows(config['data_manifest'], 'judge_train', contest_ids=plan['subsets']['judge_train'])
        if len(row['caption'].split()) <= 50]
    schedule = widegap.PairSchedule(training, config['seed'])
    data.require(len(schedule.names) == 180, 'all180_fitting_contests_retained')
    cache = {}
    def eligible(row):
        identity = (row['contest_id'], row['caption_family_sha256'])
        if identity not in cache:
            cache[identity] = len(tokenizer(helpers.canonical_input(row['scene'], row['caption']), truncation=False)['input_ids'])
        return cache[identity] <= config['max_length']
    wanted = config['max_updates']*config['gradient_accumulation']*config['batch_pairs']
    data.require(wanted == 100000, 'registered_exact100k_comparisons')
    pairs, unique, accepted_contests = [], set(), defaultdict(int)
    proposed, rejected_gap, rejected_length = 0, 0, 0
    while len(pairs) < wanted:
        proposed += 1
        data.require(proposed <= 5*wanted, 'bounded_reliable_pair_preparation')
        left, right = schedule.draw()
        target = pair_target(left, right, config['vote_cap'])
        if target is None:
            rejected_gap += 1
            continue
        if not eligible(left) or not eligible(right):
            rejected_length += 1
            continue
        pairs.append(dict(left=left, right=right, **target))
        accepted_contests[left['contest_id']] += 1
        unique.update((row['contest_id'], row['caption_family_sha256']) for row in (left, right))
    held, held_missing, unscorable = {}, {}, {}
    for index, name in enumerate(('model_selection', 'probability_calibration', 'threshold_selection', 'development_audit')):
        all_rows = list(data.evaluator_rows(config['data_manifest'], 'judge_dev', contest_ids=plan['subsets'][name]))
        candidates = [row for row in all_rows if row.get('published_rank') is not None and len(row['caption'].split()) <= 50]
        held_missing[name] = len(all_rows)-len(candidates)
        if name == 'model_selection':
            full = [row for row in candidates if eligible(row)]
            unscorable[name] = len(candidates)-len(full)
            held['model_selection_full'] = full
            chosen = helpers.natural_heldout_rows(full, widegap.SELECTION_SAMPLE_PER_CONTEST, config['seed']+41)
        else:
            chosen = helpers.natural_heldout_rows(candidates, config['heldout_per_contest'], config['seed']+index+1)
            data.require(all(eligible(row) for row in chosen), 'heldout_not_truncated_or_resampled')
        data.require(chosen, 'nonempty_registered_full_contest_held_partition')
        held[name] = chosen
    panel = data.bound(config['reference_panel'])
    data.require(panel['panel_pool'] == 'judge_train' and len(panel['rows']) == 12
        and {row['contest_id'] for row in panel['rows']} <= set(schedule.names), 'fixed_hidden_fitting_panel_only')
    data.require(all(eligible(row) for row in panel['rows']), 'reference_panel_input_bound')
    data.require(len(accepted_contests) == 180, 'accepted_pairs_cover_all180_contests')
    profile = sorted(held['model_selection_full'], key=lambda row: (-cache[(row['contest_id'], row['caption_family_sha256'])], row['caption_family_sha256']))[:256]
    return dict(schema='NY_WIDEGAP100K_PRIVATE_PLAN_V1', pairs=pairs, held=held, panel=panel['rows'], inference_profile=profile,
        metadata=dict(fitting_contests=len(schedule.names), fitting_corpus_rows=len(training), comparisons=len(pairs),
            proposed_pairs=proposed, gap_or_reliability_rejected=rejected_gap, length_rejected=rejected_length,
            unique_planned_caption_rows=len(unique), whole_contest_roster_cycles=proposed//180,
            accepted_pairs_per_contest_min=min(accepted_contests.values()),
            accepted_pairs_per_contest_max=max(accepted_contests.values()),
            accepted_pairs_exact_balance_claim=False,
            actual_bucket_passes_min=min(min(values) for values in schedule.bucket_passes.values()),
            actual_bucket_passes_max=max(max(values) for values in schedule.bucket_passes.values()),
            full_corpus_or_epoch_trained_claim=False, captions_reusable_across_comparisons=True,
            maximum_planned_tokens=max(value for value in cache.values() if value <= config['max_length']),
            held_counts={name:len(rows) for name,rows in held.items()}, held_missing_rank_or_length=held_missing,
            full_selection_token_ineligible=unscorable, hidden_fitting_panel_rows=12,
            selection_is_full_clean_eligible_contest_pool=False, final_reporting_full_clean_pool=True,
            fixed_selection_sample_per_contest=widegap.SELECTION_SAMPLE_PER_CONTEST,
            full_pool_reporting_cannot_reselect_checkpoint=True, literal_all_raw_submissions_scored=False))


def train(config, admission, prepared, output):
    import torch
    from transformers import AutoModelForSequenceClassification, AutoTokenizer
    from transformers.utils import logging
    from peft import PeftModel
    logging.set_verbosity_error()
    torch.set_num_threads(2)
    torch.manual_seed(config['seed'])
    data.require(torch.cuda.device_count() == 1, 'one_strictly_admitted_device')
    properties = torch.cuda.get_device_properties(0)
    helpers.verify_runtime_device_uuid(properties.uuid, admission['device_uuid'])
    data.require(torch.cuda.is_bf16_supported(), 'native_BF16_candidate_required')
    torch.cuda.set_per_process_memory_fraction(admission['max_reserved_bytes']/properties.total_memory, device=0)
    base = data.bound(config['base_model'])
    tokenizer = AutoTokenizer.from_pretrained(base['root'], local_files_only=True, trust_remote_code=False)
    tokenizer.pad_token = tokenizer.eos_token
    tokenizer.padding_side = 'right'
    guard = helpers.CapacityGuard(admission, dict(max_seconds=config['max_seconds']))
    def load_backbone():
        model, info = AutoModelForSequenceClassification.from_pretrained(base['root'], num_labels=1,
            pad_token_id=tokenizer.pad_token_id, local_files_only=True, trust_remote_code=False, use_safetensors=True,
            dtype=torch.bfloat16, device_map={'': 'cuda:0'}, attn_implementation='sdpa', output_loading_info=True)
        data.require(not info.get('mismatched_keys') and not info.get('error_msgs')
            and all(name.startswith('score.') for name in info.get('missing_keys', [])), 'exact_pretrained_Qwen_backbone')
        return model
    warm = data.bound(config['warm_start'])
    model = PeftModel.from_pretrained(load_backbone(), warm['selected_adapter_root'], is_trainable=True, local_files_only=True)
    trainable = [name for name, parameter in model.named_parameters() if parameter.requires_grad]
    data.require(trainable and all('lora_' in name or 'score.modules_to_save' in name for name in trainable), 'only_LoRA_and_scalar_head_trainable')
    model.gradient_checkpointing_enable(gradient_checkpointing_kwargs={'use_reentrant': False})
    model.enable_input_require_grads()
    output.mkdir(mode=0o700, exist_ok=False)
    started = time.time()
    data.private_write(output/'TRAINING_STARTED.json', dict(status='ACTUAL_QWEN_SCALAR_LORA_MODELS_LOADED',
        pid=__import__('os').getpid(), started_unix=started, objective='BRADLEY_TERRY_WEIGHTED_LOGISTIC',
        warm_start=config['warm_start'], optimizer_state_reset=True, objective_label=LABEL_POLICY, pretrained_revision=base['revision'], trainable_parameter_count=sum(parameter.numel() for parameter in model.parameters() if parameter.requires_grad),
        metadata=prepared['metadata'], admission=admission))
    def encode(rows):
        encoded = tokenizer([helpers.canonical_input(row['scene'], row['caption']) for row in rows],
            padding=True, truncation=False, return_tensors='pt')
        data.require(encoded['input_ids'].shape[1] <= config['max_length'], 'no_input_truncation')
        guard.charge(len(rows), encoded['input_ids'].numel())
        data.require(torch.cuda.memory_reserved(0) <= admission['max_reserved_bytes'], 'strict_admitted_memory_ceiling')
        return encoded.to('cuda:0')
    def predict(current, rows):
        current.eval()
        result = []
        with torch.no_grad():
            for start in range(0, len(rows), config['inference_batch']):
                result.extend(current(**encode(rows[start:start+config['inference_batch']])).logits[:, 0].float().cpu().tolist())
        return result
    optimizer = torch.optim.AdamW([parameter for parameter in model.parameters() if parameter.requires_grad], lr=config['learning_rate'])
    held, pairs = prepared['held'], prepared['pairs']
    best_key, best, best_metrics, best_step = None, None, None, None
    completed, consumed, pilot_fit_seconds = 0, 0, []
    for step in range(1, config['max_updates']+1):
        if step > 1 and time.time() >= admission['end_unix']-config['calibration_reserve_seconds']:
            break
        model.train()
        optimizer.zero_grad(set_to_none=True)
        fitting_started = time.time()
        losses = []
        for unused in range(config['gradient_accumulation']):
            batch = pairs[consumed:consumed+config['batch_pairs']]
            consumed += len(batch)
            rows = [row for pair in batch for row in (pair['left'], pair['right'])]
            scores = model(**encode(rows)).logits[:, 0].float()
            winners = torch.tensor([pair['winner'] for pair in batch], device='cuda:0', dtype=scores.dtype)
            weights = torch.tensor([pair['reliability'] for pair in batch], device='cuda:0', dtype=scores.dtype)
            loss = bt_loss(scores[::2], scores[1::2], winners, weights, torch)
            (loss/config['gradient_accumulation']).backward()
            losses.append(float(loss.detach().cpu()))
        torch.nn.utils.clip_grad_norm_([parameter for parameter in model.parameters() if parameter.requires_grad], 1.0)
        optimizer.step()
        if step <= 8:
            torch.cuda.synchronize()
            pilot_fit_seconds.append(time.time()-fitting_started)
        completed = step
        receipt = dict(step=step, actual_comparisons=consumed, actual_caption_draws=consumed*2,
            objective='BRADLEY_TERRY_WEIGHTED_LOGISTIC', loss=sum(losses)/len(losses), observed_unix=time.time(),
            seconds_since_model_load=time.time()-started, measured_comparisons_per_second=consumed/(time.time()-started),
            model_examples_charged=guard.examples, model_tokens_charged=guard.tokens)
        if step == 1:
            data.private_write(output/'FIRST_OPTIMIZER_STEP.json', receipt)
        if step == 1 or step % 10 == 0:
            data.private_write(output/'throughput'/f'{step:06d}.json', receipt)
        if step == 8:
            profile_started = time.time()
            predict(model, prepared['inference_profile'])
            torch.cuda.synchronize()
            profile_seconds = time.time()-profile_started
            counts = prepared['metadata']['held_counts']
            inference_rows = len(widegap.EVALUATION_STEPS)*counts['model_selection']+counts['model_selection_full']+sum(counts[name] for name in ('probability_calibration','threshold_selection','development_audit'))+counts['development_audit']+1012
            throughput = widegap.measured_budget(7*config['batch_pairs']*config['gradient_accumulation']/sum(pilot_fit_seconds[1:]),
                len(prepared['inference_profile'])/profile_seconds, 100000-consumed, inference_rows, admission['end_unix']-time.time())
            data.private_write(output/'MEASURED_BUDGET_ADMISSION.json', dict(**throughput, measured_unix=time.time(),
                fitting_pilot_updates=8, inference_profile_rows=len(prepared['inference_profile']),
                profile_policy='LONGEST_TOKEN_INPUTS_FROM_FULL_CLEAN_MODEL_SELECTION_POOL',
                actual_comparisons=consumed, actual_model_examples=guard.examples))
            data.require(throughput['can_complete'], 'measured_total100k_fit_selection_calibration_exceeds_budget')
        if step in widegap.EVALUATION_STEPS:
            selection = widegap.sampled_selection_metrics(held['model_selection'], predict(model, held['model_selection']))
            key = selection['selection_composite']
            data.private_write(output/'progress'/f'{step:06d}.json', dict(**receipt, model_selection=selection, selection_completed_unix=time.time()))
            if best_key is None or key > best_key:
                best_key, best_step, best_metrics = key, step, selection
                best = output/'checkpoints'/f'step_{step:06d}'
                model.save_pretrained(best, safe_serialization=True)
    data.require(completed > 0 and best is not None, 'actual_BT_updates_and_selected_checkpoint_required')
    del optimizer, scores, loss
    torch.cuda.empty_cache()
    model.load_adapter(str(best), adapter_name='selected', is_trainable=False)
    model.set_adapter('selected')
    model.gradient_checkpointing_disable()
    full_selection_started = time.time()
    full_selection = widegap.full_metrics(held['model_selection_full'], predict(model, held['model_selection_full']))
    full_selection.update(role='FULL_CLEAN_MODEL_SELECTION_POOL_REPORTING_ONLY_NO_RESELECTION',
        independent_from_prior_DEV_use=False, measured_inference_seconds=time.time()-full_selection_started)
    data.private_write(output/'FULL_POOL_SELECTION_REPORT.json', full_selection)
    calibration_rows = held['probability_calibration']
    calibration_scores = predict(model, calibration_rows)
    calibration = isotonic_calibration(calibration_scores, [positive_mass(row) for row in calibration_rows])
    reference_scores = predict(model, prepared['panel'])
    rank_quality = isotonic_calibration([quality.reference_win(score, reference_scores) for score in calibration_scores], [int(row['published_rank'] <= 200) for row in calibration_rows])
    rank_quality['method'] = 'NATURAL_REGISTERED_DEV_ISOTONIC_RANK200_REFERENCE_QUALITY_NOT_VOTE_Q_V1'
    threshold_rows = held['threshold_selection']
    threshold_scores = predict(model, threshold_rows)
    threshold_q = [calibrated_q(calibration, score) for score in threshold_scores]
    threshold = helpers.choose_threshold(threshold_q, [positive_mass(row) for row in threshold_rows], 0.30, 0.05)
    quality_threshold_values = [calibrated_q(rank_quality, quality.reference_win(score, reference_scores)) for score in threshold_scores]
    quality_threshold = quality.select_quality_threshold(quality_threshold_values, [int(row['published_rank'] <= 200) for row in threshold_rows], [row['contest_id'] for row in threshold_rows])
    data.private_write(output/'CALIBRATION_FIXED_BEFORE_AUDIT.json', dict(vote_q=calibration, vote_q_tau=threshold, rank200_quality=rank_quality, rank200_tau=quality_threshold, reference_scores=reference_scores, observed_unix=time.time()))
    data.private_write(output/'DEV_AUDIT_ONCE.json', dict(observed_unix=time.time(), role='REUSED_REGISTERED_DEV_AUDIT_NOT_MODEL_SELECTION', locked_test_used=False))
    audit = held['development_audit']
    audit_scores = predict(model, audit)
    audit_q = [calibrated_q(calibration, score) for score in audit_scores]
    audit_metrics = ranking_metrics(audit, audit_scores)
    audit_metrics.update(probability_metrics(audit, audit_q))
    audit_quality_values = [calibrated_q(rank_quality, quality.reference_win(score, reference_scores)) for score in audit_scores]
    quality_audit = widegap.quality_audit(audit, audit_quality_values, quality_threshold['threshold'])
    fit_config = data.bound(config['frozen_scene_fit'])
    fit_training = data.bound(fit_config['training_config'])
    fit_tokenizer = AutoTokenizer.from_pretrained(str(Path(fit_config['selected_checkpoint'])/'tokenizer'), local_files_only=True, trust_remote_code=False)
    fit = helpers.load_pretrained_classifier(AutoModelForSequenceClassification, Path(fit_config['selected_checkpoint'])/'scene_fit', 2, 'cuda:0')
    fit.eval()
    def fit_scores(rows):
        result = []
        with torch.no_grad():
            for start in range(0, len(rows), 16):
                batch = rows[start:start+16]
                encoded = fit_tokenizer([helpers.canonical_input(row['scene'], row['caption']) for row in batch], padding=True, truncation=False, return_tensors='pt')
                data.require(encoded['input_ids'].shape[1] <= fit_training['max_length'], 'no_scene_fit_truncation')
                guard.charge(len(batch), encoded['input_ids'].numel())
                result.extend(torch.softmax(fit(**encoded.to('cuda:0')).logits.float(), -1)[:, 1].cpu().tolist())
        return result
    fit_threshold = fit_config['scene_fit']['threshold']
    audit_metrics.update(helpers.acceptance_metrics(audit, audit_q, fit_scores(audit), threshold['threshold'], fit_threshold))
    stress_rows = helpers.balanced_scene_rows(audit, 40, config['seed']+6)
    cases = helpers.stress_cases(stress_rows, len(stress_rows), config['seed']+7)
    original_q = [calibrated_q(calibration, score) for score in predict(model, [case['original'] for case in cases])]
    challenged_q = [calibrated_q(calibration, score) for score in predict(model, cases)]
    challenged_fit = fit_scores(cases)
    summary = defaultdict(list)
    for case, original, challenged, fit_value in zip(cases, original_q, challenged_q, challenged_fit):
        summary[case['kind']].append((challenged-original, threshold['threshold'] is not None and challenged >= threshold['threshold'] and fit_value >= fit_threshold))
    report = dict(schema='NY_WIDEGAP100K_SAFE_PUBLIC_REPORT_V1', status='PROVISIONAL_REUSED_DEVELOPMENT_ONLY',
        objective='BRADLEY_TERRY_WEIGHTED_LOGISTIC', label_policy=LABEL_POLICY, pair_policy=PAIR_POLICY,
        reliability_policy=RELIABILITY_POLICY, model_selection=best_metrics, full_pool_selection_reporting=full_selection, selected_step=best_step,
        selected_checkpoint_comparisons=best_step*config['gradient_accumulation']*config['batch_pairs'],
        completed_updates=completed, actual_comparisons=consumed, actual_caption_draws=2*consumed,
        calibration_examples=calibration['examples'], calibrated_q_meaning='EXPECTED_SOMEWHAT_OR_FUNNY_VOTE_MASS',
        tau=threshold, rank200_quality_threshold=quality_threshold, rank200_quality_audit=quality_audit,
        required_comparisons=100000, required_pair_target_completed=(consumed == 100000),
        warm_start=config['warm_start'], optimizer_state_reset=True, development_audit=audit_metrics, fitting=prepared['metadata'],
        scene_fit_frozen_from_v6=True, scene_fit_selected_step=fit_config['selected_step'],
        stress_errors={kind: dict(examples=len(values), accepted=sum(value[1] for value in values),
            mean_q_delta=sum(value[0] for value in values)/len(values), mean_absolute_q_delta=sum(abs(value[0]) for value in values)/len(values)) for kind, values in summary.items()},
        locked_validation_used=False, FINAL_used=False, human_validated=False, second_blind_comparator_complete=False,
        captions_included=False, contest_ids_included=False, completed_unix=time.time())
    report_ref = data.private_write(output/'PUBLIC_SCORING_REPORT.json', report)
    result = dict(schema='NY_WIDEGAP100K_SCALAR_JUDGE_CONFIG_V1', base_model=config['base_model'], adapter={str(path.relative_to(best)): data.file_ref(path)
        for path in best.rglob('*') if path.is_file()}, selected_adapter_root=str(best), calibration=calibration,
        tau=threshold, rank200_quality_calibration=rank_quality, rank200_quality_threshold=quality_threshold, reference_scores=reference_scores, reference_panel=config['reference_panel'], frozen_scene_fit=config['frozen_scene_fit'], report=report_ref, config=config,
        evaluator_source_sha256=admission['source_sha256'], completed_unix=time.time(), status='PROVISIONAL',
        human_validated=False, final_release_authorized=False)
    return data.private_write(output/'judge_config.json', result)
