"""Frozen100k mean-order BT pair schedule and full-clean-contest selection."""

from collections import defaultdict
import math
import random
import statistics

from gpu import ny_caption_data as data
from research_loop.workers.r177_caption_game_stage1_20260917.data_judge import rank200_calibration_v3 as quality
from research_loop.workers.r177_caption_game_stage1_20260917.data_judge import bt_ranker as old


LABEL_POLICY = 'EMPIRICAL_MEAN_THREE_CLASS_RATING_WIDE_GAP_V1'
PAIR_POLICY = 'BALANCED_ALL_CONTEST_CYCLES_TOP_BOTTOM_TERCILES_WITHOUT_REPLACEMENT_BUCKET_PASSES_V1'
RELIABILITY_POLICY = 'CAPPED_VOTES_TIMES_CLIPPED_CATEGORICAL_MEAN_STANDARDIZED_GAP_V1'
EVALUATION_STEPS = [8, 1563, 3125, 4688, 6250]
SELECTION_SAMPLE_PER_CONTEST = 256


def sampled_selection_metrics(rows, scores):
    groups = defaultdict(list)
    for row, score in zip(rows, scores):
        groups[row['contest_id']].append((row, score))
    rank = quality.full_pool_metrics(rows, scores)['macro_mean_rating_spearman']
    precision, sizes = [], []
    for group in groups.values():
        count = max(1, math.ceil(200*len(group)/group[0][0]['full_original_contest_rows']))
        ordered = sorted(group, key=lambda item: (-item[1], item[0]['caption_family_sha256']))[:count]
        precision.append(sum(row['published_rank'] <= row['full_original_contest_rows']//2 for row, score in ordered)/len(ordered))
        sizes.append(len(ordered))
    value = statistics.fmean(precision)
    data.require(rank is not None, 'defined_fixed_sample_selection_rank')
    return dict(role='FIXED_MODEL_SELECTION_SAMPLE_NOT_FULL_TOP200', examples=len(rows), contests=len(groups),
        macro_mean_rating_spearman=rank, macro_sampled_rank200_fraction_precision_in_original_top_half=value,
        sample_top_k_min=min(sizes), sample_top_k_max=max(sizes), full_contest_top200_measured=False,
        selection_composite=0.5*rank+0.5*(2*value-1))


def measured_budget(comparisons_per_second, inference_rows_per_second, remaining_pairs, inference_rows, remaining_seconds):
    data.require(all(math.isfinite(value) and value > 0 for value in
        (comparisons_per_second, inference_rows_per_second, remaining_seconds)), 'positive_measured_throughput')
    fitting = remaining_pairs/comparisons_per_second
    inference = inference_rows/inference_rows_per_second
    estimate = 1.25*(fitting+inference)+900
    return dict(fitting_seconds=fitting, inference_seconds=inference, safety_factor=1.25, fixed_close_margin_seconds=900,
        conservative_remaining_seconds=estimate, remaining_admitted_seconds=remaining_seconds,
        can_complete=estimate < remaining_seconds, inferred_ETA_not_completion_receipt=True)


def pair_target(left, right, vote_cap=100):
    data.require(left['contest_id'] == right['contest_id'] and left['scene'] == right['scene']
        and left['caption_family_sha256'] != right['caption_family_sha256'], 'clean_distinct_within_contest_pair')
    gap = left['mean']-right['mean']
    if min(left['votes'], right['votes']) < 20 or abs(gap) < 0.10:
        return None
    variance = 0.0
    for row in (left, right):
        old.positive_mass(row)
        probabilities = [(count+0.5)/(row['votes']+1.5) for count in row['counts']]
        mean = sum((index+1)*value for index, value in enumerate(probabilities))
        second = sum((index+1)**2*value for index, value in enumerate(probabilities))
        variance += max(0.0, second-mean**2)/(row['votes']+2.5)
    reliability = min(left['votes'], right['votes'], vote_cap)/vote_cap*min(1.0, abs(gap)/math.sqrt(variance))
    return dict(winner=int(gap > 0), reliability=reliability, mean_gap=abs(gap))


class PairSchedule:
    def __init__(self, rows, seed=177):
        self.generator = random.Random(seed)
        self.groups = defaultdict(list)
        for row in rows:
            if row['votes'] >= 20:
                self.groups[row['contest_id']].append(row)
        self.names = sorted(self.groups)
        data.require(self.names, 'nonempty_contest_pool')
        self.buckets, self.positions, self.bucket_passes = {}, {}, {}
        for name in self.names:
            ordered = sorted(self.groups[name], key=lambda row: (-row['mean'], row['caption_family_sha256']))
            width = len(ordered)//3
            data.require(width > 0 and ordered[0]['mean']-ordered[-1]['mean'] >= 0.10, 'contest_has_reliable_wide_gap')
            self.buckets[name] = [ordered[:width], ordered[-width:]]
            for bucket in self.buckets[name]:
                self.generator.shuffle(bucket)
            self.positions[name] = [0, 0]
            self.bucket_passes[name] = [0, 0]
        self.cursor = 0

    def draw(self):
        name = self.names[self.cursor % len(self.names)]
        self.cursor += 1
        picked = []
        for side in (0, 1):
            bucket = self.buckets[name][side]
            position = self.positions[name][side]
            if position == len(bucket):
                self.generator.shuffle(bucket)
                position = 0
                self.bucket_passes[name][side] += 1
            picked.append(bucket[position])
            self.positions[name][side] = position+1
        if self.generator.random() < 0.5:
            picked.reverse()
        return picked


def selection_key(metrics):
    rank = metrics['macro_mean_rating_spearman']
    precision = metrics['macro_precision_predicted_top200_in_original_true_top_half']
    data.require(rank is not None and precision is not None and math.isfinite(rank) and 0 <= precision <= 1,
        'defined_full_contest_selection_metrics')
    return (0.5*rank+0.5*(2*precision-1), rank, precision)


def full_metrics(rows, scores):
    result = quality.full_pool_metrics(rows, scores)
    result['selection_composite'] = selection_key(result)[0]
    result['selection_definition'] = 'HALF_MEAN_SPEARMAN_PLUS_HALF_CENTERED_TOP200_IN_TRUE_TOP_HALF_PRECISION'
    return result


def quality_audit(rows, values, threshold):
    accepted = [index for index, value in enumerate(values) if threshold is not None and value >= threshold]
    success = sum(rows[index]['published_rank'] <= 200 for index in accepted)
    coverage = len(accepted)/len(rows)
    support = len({rows[index]['contest_id'] for index in accepted})/len({row['contest_id'] for row in rows})
    lower = quality.wilson_lower(success, len(accepted))
    passed = (threshold is not None and len(accepted) >= quality.CONTRACT['minimum_accepted']
        and coverage >= quality.CONTRACT['minimum_coverage'] and support >= quality.CONTRACT['minimum_accepted_contest_fraction']
        and lower >= quality.CONTRACT['minimum_precision_wilson95_lower'])
    return dict(examples=len(rows), accepted=len(accepted), precision=success/len(accepted) if accepted else None,
        precision_wilson95_lower=lower, coverage=coverage, accepted_contest_fraction=support,
        status='PROVISIONAL_QUALITY_POINT_PASSES_SEPARATE_SCENE_AND_DUPLICATE_CHECKS_REQUIRED' if passed else 'BLOCKED_RANK200_QUALITY_POINT',
        full_judge_usable=False, reused_development_only=True)
