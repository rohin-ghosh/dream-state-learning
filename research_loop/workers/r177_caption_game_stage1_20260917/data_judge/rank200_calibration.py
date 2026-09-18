"""Versioned rank200 diagnostics and quality calibration; no model or GPU import."""

from collections import Counter, defaultdict
import csv
import hashlib
import io
import json
import math
from pathlib import Path
import statistics

from gpu import ny_caption_data as data
from research_loop.workers.r177_caption_game_stage1_20260917.data_judge import bt_ranker as prior


CONTRACT = dict(schema='NY_RANK200_REFERENCE_CONTRACT_V1', truth='LITERAL_RELEASED_ONE_BASED_RANK_LE_200',
    original_vote_q_preserved=True, original_threshold_unchanged=True, image_training=False,
    panel_pool='judge_train', panel_contests=4, panel_ranks=[190, 200, 210], panel_minimum_votes=20,
    calibration_field='probability_of_released_rank200_quality_NOT_vote_q', calibration_sample_per_contest=256,
    minimum_precision_wilson95_lower=0.80, minimum_coverage=0.01, minimum_accepted=20,
    minimum_accepted_contest_fraction=0.5, maximum_caption_words=50,
    maximum_read_bytes=2*1024**3, maximum_file_bytes=64*1024**2,
    locked_validation_read=False, FINAL_read=False, reused_development_only=True,
    reference_transform_improves_ordering=False, full_judge_promotion_from_rank_metric=False)


class Reader:
    def __init__(self, maximum=CONTRACT['maximum_read_bytes']):
        self.maximum, self.charged = maximum, 0

    def read(self, reference):
        path = Path(reference['path'])
        data.require(path.is_absolute() and path == path.resolve() and path.is_file(), 'canonical_bound_read')
        size = path.stat().st_size
        data.require(size <= CONTRACT['maximum_file_bytes'] and self.charged+size <= self.maximum, 'read_budget_before_IO')
        self.charged += size
        raw = path.read_bytes()
        data.require(len(raw) == size and ('bytes' not in reference or reference['bytes'] == size)
            and hashlib.sha256(raw).hexdigest() == reference['sha256'], 'exact_read_hash_and_size')
        return raw

    def json(self, reference):
        return json.loads(self.read(reference))


def q(row):
    return prior.positive_mass(row)


def summarize(values):
    values = sorted(value for value in values if value is not None)
    if not values:
        return dict(count=0, mean=None, median=None, minimum=None, maximum=None)
    return dict(count=len(values), mean=statistics.fmean(values), median=statistics.median(values),
        minimum=values[0], maximum=values[-1])


def raw_contest(raw, contest):
    all_ranks, valid, invalid = [], [], 0
    for entry in csv.DictReader(io.StringIO(raw.decode('utf-8-sig'))):
        data.require(str(entry['rank']).isdigit(), 'released_integer_rank_required')
        rank = int(entry['rank'])
        all_ranks.append(rank)
        try:
            row = data.rating_record(entry, contest)
        except (ValueError, KeyError, TypeError, OverflowError):
            invalid += 1
            continue
        valid.append(dict(row, published_rank=rank))
    data.require(sorted(all_ranks) == list(range(1, len(all_ranks)+1)), 'complete_unique_one_based_released_ranks')
    by_rank = {row['published_rank']: row for row in valid}
    count = len(all_ranks)
    boundary = by_rank.get(200)
    top = [row for row in valid if row['published_rank'] <= 200]
    oracle_count = math.ceil(0.05*len(valid))
    oracle = statistics.fmean(sorted((q(row) for row in valid), reverse=True)[:oracle_count]) if valid else None
    means = [row['mean'] for row in sorted(valid, key=lambda item: item['published_rank'])]
    summary = dict(original_rows=count, valid_rating_rows=len(valid), invalid_rating_rows=invalid,
        literal_rank200_available=boundary is not None, literal_rank200_positive_vote_mass=q(boundary) if boundary else None,
        literal_rank200_mean=boundary['mean'] if boundary else None,
        literal_rank200_coverage=200/count if count >= 200 else None,
        full_top200_positive_vote_mass=statistics.fmean(q(row) for row in top) if len(top) == 200 else None,
        top200_valid_rating_count=len(top), source_rank_mean_increases=sum(right > left+1e-6 for left, right in zip(means, means[1:])),
        boundary_mean_ties=sum(row['mean'] == boundary['mean'] for row in valid) if boundary else None,
        perfect_q_top5percent_mean_mass=oracle, perfect_q_old_point_possible=oracle is not None and oracle >= 0.30,
        rank200_meets_old_point_mass=boundary is not None and q(boundary) >= 0.30)
    families = defaultdict(list)
    for row in valid:
        families[row['caption_family_sha256']].append(row)
    unique = {family: rows[0] for family, rows in families.items() if len(rows) == 1}
    return summary, unique, by_rank


def join_clean(clean, original, original_count):
    result = []
    for row in clean:
        source = original.get(row['caption_family_sha256'])
        matched = source is not None and source['counts'] == row['counts'] and source['votes'] == row['votes']
        result.append(dict(row, published_rank=source['published_rank'] if matched else None,
            full_original_contest_rows=original_count, original_rank_join_valid=matched))
    return result


def fixed_panel(contests, seed=177):
    candidates = sorted(contests, key=lambda name: data.digest(dict(seed=seed, panel_contest=name)))
    result = []
    for name in candidates:
        rows = {row['published_rank']: row for row in contests[name] if row['published_rank'] is not None}
        if all(rank in rows and rows[rank]['votes'] >= CONTRACT['panel_minimum_votes']
                and len(rows[rank]['caption'].split()) <= CONTRACT['maximum_caption_words'] for rank in CONTRACT['panel_ranks']):
            result.extend(rows[rank] for rank in CONTRACT['panel_ranks'])
        if len(result) == CONTRACT['panel_contests']*len(CONTRACT['panel_ranks']):
            break
    data.require(len(result) == 12, 'fixed_fitting_panel_support_missing')
    return result


def reference_win(score, panel_scores):
    data.require(math.isfinite(score) and panel_scores and all(math.isfinite(value) for value in panel_scores), 'finite_reference_scores')
    def logistic(value):
        return 1/(1+math.exp(-value)) if value >= 0 else math.exp(value)/(1+math.exp(value))
    return statistics.fmean(logistic(score-reference) for reference in panel_scores)


def wilson_lower(successes, count):
    data.require(type(successes) is int and type(count) is int and 0 <= successes <= count, 'valid_binomial_counts')
    if not count:
        return 0.0
    proportion, critical = successes/count, 1.959963984540054
    return (proportion+critical**2/(2*count)-critical*math.sqrt(proportion*(1-proportion)/count+critical**2/(4*count**2)))/(1+critical**2/count)


def select_quality_threshold(probabilities, labels, contests):
    data.require(probabilities and len(probabilities) == len(labels) == len(contests)
        and all(math.isfinite(value) and 0 <= value <= 1 for value in probabilities)
        and all(type(value) is int and value in (0, 1) for value in labels), 'valid_rank200_threshold_inputs')
    candidates = []
    for threshold in sorted(set(probabilities)):
        accepted = [index for index, value in enumerate(probabilities) if value >= threshold]
        count = len(accepted)
        success = sum(labels[index] for index in accepted)
        coverage = count/len(labels)
        support = len({contests[index] for index in accepted})/len(set(contests))
        lower = wilson_lower(success, count)
        if (count >= CONTRACT['minimum_accepted'] and coverage >= CONTRACT['minimum_coverage']
                and support >= CONTRACT['minimum_accepted_contest_fraction'] and lower >= CONTRACT['minimum_precision_wilson95_lower']):
            candidates.append(dict(threshold=threshold, accepted=count, precision=success/count,
                precision_wilson95_lower=lower, coverage=coverage, accepted_contest_fraction=support))
    if not candidates:
        return dict(threshold=None, status='BLOCKED_NO_REGISTERED_RANK200_QUALITY_OPERATING_POINT')
    return dict(max(candidates, key=lambda row: (row['coverage'], row['threshold'])), status='DEVELOPMENT_THRESHOLD_ONLY_AUDIT_REQUIRED')


def full_pool_metrics(rows, scores):
    data.require(rows and len(rows) == len(scores) and all(math.isfinite(value) for value in scores), 'full_pool_score_join')
    groups = defaultdict(list)
    for row, score in zip(rows, scores):
        groups[row['contest_id']].append((row, score))
    correlations, precision, inverse = [], [], []
    missing = 0
    for group in groups.values():
        valid = [(row, score) for row, score in group if row['published_rank'] is not None]
        missing += len(group)-len(valid)
        if not valid:
            continue
        ordered = sorted(valid, key=lambda item: (-item[1], item[0]['caption_family_sha256']))
        first = prior.helpers.average_ranks([item[1] for item in valid])
        second = prior.helpers.average_ranks([item[0]['mean'] for item in valid])
        first_mean, second_mean = statistics.fmean(first), statistics.fmean(second)
        left = [value-first_mean for value in first]
        right = [value-second_mean for value in second]
        denominator = math.sqrt(sum(value**2 for value in left)*sum(value**2 for value in right))
        if denominator:
            correlations.append(sum(left_value*right_value for left_value, right_value in zip(left, right))/denominator)
        predicted = ordered[:200]
        precision.append(sum(row['published_rank'] <= row['full_original_contest_rows']//2 for row, score in predicted)/len(predicted))
        true_top = {row['caption_family_sha256'] for row, score in valid if row['published_rank'] <= 200}
        predicted_half = {row['caption_family_sha256'] for row, score in ordered[:math.ceil(len(ordered)/2)]}
        if true_top:
            inverse.append(len(true_top & predicted_half)/len(true_top))
    return dict(contests=len(groups), scored_clean_rows=len(rows), missing_original_rank_rows=missing,
        macro_mean_rating_spearman=statistics.fmean(correlations) if correlations else None,
        macro_precision_predicted_top200_in_original_true_top_half=statistics.fmean(precision) if precision else None,
        macro_recall_original_true_top200_in_predicted_clean_top_half=statistics.fmean(inverse) if inverse else None,
        all_clean_scorable_contest_rows_used=True, all_raw_submissions_scored=False,
        quarantined_rows_not_reintroduced=True, sample64_top5_used=False)
