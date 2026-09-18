"""R171 scalar Bradley-Terry humor ranking, with separate empirical-q calibration."""

from collections import defaultdict
import math
from pathlib import Path
import random
import time

from gpu import ny_caption_data as data
from gpu import ny_caption_judge as helpers


LABEL_POLICY = 'EMPIRICAL_SOMEWHAT_PLUS_FUNNY_VOTE_FRACTION_NOT_MEAN_RATING_V1'
PAIR_POLICY = 'UNIFORM_CONTEST_DISTINCT_CAPTIONS_REUSABLE_COMPARISONS_V1'
RELIABILITY_POLICY = 'MIN_CAPPED_VOTES_TIMES_CLIPPED_JEFFREYS_STANDARDIZED_GAP_V1'
MODEL_ID = 'Qwen/Qwen2.5-7B-Instruct'
MODEL_REVISION = 'a09a35458c702b33eeacc393d103063234e8bc28'


def positive_mass(row):
    counts = row['counts']
    data.require(len(counts) == 3 and all(type(value) is int and value >= 0 for value in counts)
        and sum(counts) == row['votes'] and row['votes'] > 0, 'actual_valid_vote_counts')
    return sum(counts[1:])/row['votes']


def pair_target(left, right, vote_cap=100):
    data.require(left['contest_id'] == right['contest_id'] and left['scene'] == right['scene']
        and left['caption_family_sha256'] != right['caption_family_sha256'], 'within_contest_distinct_caption_pair')
    gap = positive_mass(left)-positive_mass(right)
    if gap == 0:
        return None
    variance = 0.0
    for row in (left, right):
        positive = sum(row['counts'][1:])
        posterior_mean = (positive+0.5)/(row['votes']+1)
        variance += posterior_mean*(1-posterior_mean)/(row['votes']+2)
    weight = min(left['votes'], right['votes'], vote_cap)/vote_cap*min(1.0, abs(gap)/math.sqrt(variance))
    return dict(winner=1 if gap > 0 else 0, reliability=weight)


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
    groups = defaultdict(list)
    for row in training:
        groups[row['contest_id']].append(row)
    names = sorted(groups)
    generator = random.Random(config['seed'])
    wanted = config['max_updates']*config['gradient_accumulation']*config['batch_pairs']
    pairs, rejected_length, ties, proposals = [], 0, 0, 0
    unique = set()
    cache = {}
    def eligible(row):
        identity = row['contest_id']+':'+row['caption_family_sha256']
        if identity not in cache:
            cache[identity] = len(tokenizer(helpers.canonical_input(row['scene'], row['caption']), truncation=False)['input_ids'])
        return cache[identity] <= config['max_length']
    while len(pairs) < wanted:
        proposals += 1
        data.require(proposals <= wanted*32, 'bounded_reliable_pair_proposals')
        name = generator.choice(names)
        left, right = generator.sample(groups[name], 2)
        if left['caption_family_sha256'] == right['caption_family_sha256']:
            continue
        target = pair_target(left, right, config['vote_cap'])
        if target is None:
            ties += 1
            continue
        if not eligible(left) or not eligible(right):
            rejected_length += 1
            continue
        pairs.append(dict(left=left, right=right, **target))
        unique.update((row['contest_id'], row['caption_family_sha256']) for row in (left, right))
    held = {}
    for index, name in enumerate(('model_selection', 'probability_calibration', 'threshold_selection', 'development_audit')):
        rows = data.evaluator_rows(config['data_manifest'], 'judge_dev', contest_ids=plan['subsets'][name])
        chosen = helpers.natural_heldout_rows(rows, config['heldout_per_contest'], config['seed']+index+1)
        data.require(all(eligible(row) for row in chosen), 'heldout_inputs_must_fit_without_selection_or_truncation')
        held[name] = chosen
    return dict(schema='NY_R171_PRIVATE_PAIR_PLAN_V1', pairs=pairs, held=held,
        metadata=dict(fitting_corpus_rows=len(training), fitting_contests=len(groups), comparisons=len(pairs),
            unique_planned_caption_rows=len(unique), proposed_pairs=proposals, tied_pairs_skipped=ties,
            length_ineligible_pairs_skipped=rejected_length, maximum_planned_tokens=max(value for value in cache.values() if value <= config['max_length']),
            captions_reusable_across_comparisons=True, full_corpus_or_epoch_trained_claim=False,
            held_counts={name: len(rows) for name, rows in held.items()}))


def train(config, admission, prepared, output):
    import torch
    from transformers import AutoModelForSequenceClassification, AutoTokenizer
    from transformers.utils import logging
    from peft import LoraConfig, TaskType, get_peft_model
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
    model = get_peft_model(load_backbone(), LoraConfig(task_type=TaskType.SEQ_CLS, r=8, lora_alpha=16,
        lora_dropout=0.05, target_modules=['q_proj', 'v_proj'], modules_to_save=['score'], bias='none'))
    trainable = [name for name, parameter in model.named_parameters() if parameter.requires_grad]
    data.require(trainable and all('lora_' in name or 'score.modules_to_save' in name for name in trainable), 'only_LoRA_and_scalar_head_trainable')
    model.gradient_checkpointing_enable(gradient_checkpointing_kwargs={'use_reentrant': False})
    model.enable_input_require_grads()
    output.mkdir(mode=0o700, exist_ok=False)
    started = time.time()
    data.private_write(output/'TRAINING_STARTED.json', dict(status='ACTUAL_QWEN_SCALAR_LORA_MODELS_LOADED',
        pid=__import__('os').getpid(), started_unix=started, objective='BRADLEY_TERRY_WEIGHTED_LOGISTIC',
        pretrained_revision=base['revision'], trainable_parameter_count=sum(parameter.numel() for parameter in model.parameters() if parameter.requires_grad),
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
    completed, consumed = 0, 0
    for step in range(1, config['max_updates']+1):
        if step > 1 and time.time() >= admission['end_unix']-config['calibration_reserve_seconds']:
            break
        model.train()
        optimizer.zero_grad(set_to_none=True)
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
        completed = step
        receipt = dict(step=step, actual_comparisons=consumed, actual_caption_draws=consumed*2,
            objective='BRADLEY_TERRY_WEIGHTED_LOGISTIC', loss=sum(losses)/len(losses), observed_unix=time.time(),
            seconds_since_model_load=time.time()-started, measured_comparisons_per_second=consumed/(time.time()-started),
            model_examples_charged=guard.examples, model_tokens_charged=guard.tokens)
        if step == 1:
            data.private_write(output/'FIRST_OPTIMIZER_STEP.json', receipt)
        if step == 1 or step % 10 == 0:
            data.private_write(output/'throughput'/f'{step:06d}.json', receipt)
        if step == 1 or step % config['evaluation_interval'] == 0 or step == config['max_updates']:
            selection = ranking_metrics(held['model_selection'], predict(model, held['model_selection']))
            correlation = selection['macro_contest_spearman']
            key = (float('-inf') if correlation is None else correlation, selection['pairwise_concordance'] or 0)
            data.private_write(output/'progress'/f'{step:06d}.json', dict(**receipt, model_selection=selection))
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
    calibration_rows = held['probability_calibration']
    calibration = isotonic_calibration(predict(model, calibration_rows), [positive_mass(row) for row in calibration_rows])
    threshold_rows = held['threshold_selection']
    threshold_q = [calibrated_q(calibration, score) for score in predict(model, threshold_rows)]
    threshold = helpers.choose_threshold(threshold_q, [positive_mass(row) for row in threshold_rows], 0.30, 0.05)
    data.private_write(output/'DEV_AUDIT_ONCE.json', dict(observed_unix=time.time(), role='REUSED_REGISTERED_DEV_AUDIT_NOT_MODEL_SELECTION', locked_test_used=False))
    audit = held['development_audit']
    audit_scores = predict(model, audit)
    audit_q = [calibrated_q(calibration, score) for score in audit_scores]
    audit_metrics = ranking_metrics(audit, audit_scores)
    audit_metrics.update(probability_metrics(audit, audit_q))
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
    report = dict(schema='NY_R171_SAFE_PUBLIC_SCALAR_REPORT_V1', status='PROVISIONAL_REUSED_DEVELOPMENT_ONLY',
        objective='BRADLEY_TERRY_WEIGHTED_LOGISTIC', label_policy=LABEL_POLICY, pair_policy=PAIR_POLICY,
        reliability_policy=RELIABILITY_POLICY, model_selection=best_metrics, selected_step=best_step,
        selected_checkpoint_comparisons=best_step*config['gradient_accumulation']*config['batch_pairs'],
        completed_updates=completed, actual_comparisons=consumed, actual_caption_draws=2*consumed,
        calibration_examples=calibration['examples'], calibrated_q_meaning='EXPECTED_SOMEWHAT_OR_FUNNY_VOTE_MASS',
        tau=threshold, development_audit=audit_metrics, fitting=prepared['metadata'],
        scene_fit_frozen_from_v6=True, scene_fit_selected_step=fit_config['selected_step'],
        stress_errors={kind: dict(examples=len(values), accepted=sum(value[1] for value in values),
            mean_q_delta=sum(value[0] for value in values)/len(values), mean_absolute_q_delta=sum(abs(value[0]) for value in values)/len(values)) for kind, values in summary.items()},
        locked_validation_used=False, FINAL_used=False, human_validated=False, second_blind_comparator_complete=False,
        captions_included=False, contest_ids_included=False, completed_unix=time.time())
    report_ref = data.private_write(output/'PUBLIC_SCORING_REPORT.json', report)
    result = dict(schema='NY_BT_SCALAR_JUDGE_CONFIG_V1', base_model=config['base_model'], adapter={str(path.relative_to(best)): data.file_ref(path)
        for path in best.rglob('*') if path.is_file()}, selected_adapter_root=str(best), calibration=calibration,
        tau=threshold, frozen_scene_fit=config['frozen_scene_fit'], report=report_ref, config=config,
        evaluator_source_sha256=admission['source_sha256'], completed_unix=time.time(), status='PROVISIONAL',
        human_validated=False, final_release_authorized=False)
    return data.private_write(output/'judge_config.json', result)
