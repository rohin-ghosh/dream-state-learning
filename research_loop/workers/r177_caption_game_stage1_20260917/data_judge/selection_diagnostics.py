"""Owner-side development-only aggregates, with no threshold or checkpoint changes."""

import argparse
import json
import math
import os
from pathlib import Path
import time

from gpu import ny_caption_data as data
from gpu import ny_caption_judge as judge


def threshold_oracle(positive_mass, minimum_mass, minimum_coverage):
    data.require(positive_mass and all(math.isfinite(value) and 0 <= value <= 1 for value in positive_mass)
        and 0 < minimum_mass < 1 and 0 < minimum_coverage <= 1, 'bounded_threshold_oracle_inputs')
    count = math.ceil(minimum_coverage*len(positive_mass))
    mean_mass = sum(sorted(positive_mass, reverse=True)[:count])/count
    return dict(examples=len(positive_mass), minimum_accepted_count=count,
        maximum_mean_positive_vote_mass_at_minimum_coverage=mean_mass,
        minimum_mean_positive_vote_mass=minimum_mass, minimum_coverage=minimum_coverage,
        quality_objective_possible_under_perfect_ranking=mean_mass >= minimum_mass,
        fit_filter_considered=False, threshold_changed=False, rows_disclosed=False)


def run(root):
    data.require(os.environ.get('CUDA_VISIBLE_DEVICES') == '', 'CPU_only_diagnostic')
    config_ref = data.file_ref(root/'TRAIN_CONFIG.json')
    config = data.bound(config_ref)
    completed = data.bound(data.file_ref(root/'COMPLETED.json'))
    trained = data.bound(completed['judge_config'])
    data.require(trained['training_config']['sha256'] == config_ref['sha256']
        and trained['locked_judge_validation_consumed'] is False, 'completed_development_only_provenance')
    for module in (data, judge):
        path = Path(module.__file__).resolve()
        data.require(data.file_ref(path)['sha256'] == trained['evaluator_source_sha256'][path.name], 'exact_frozen_v6_sources')
    plan = data.load_development_plan(config['development_plan'], config['development_source_manifest'])
    selected = plan['subsets']['threshold_selection']
    rows = judge.natural_heldout_rows(data.evaluator_rows(config['data_manifest'], 'judge_dev', contest_ids=selected),
        config['heldout_per_contest'], config['seed']+3)
    result = threshold_oracle([sum(judge.empirical_target(row['counts'])[1:]) for row in rows],
        config['threshold_minimum_mean_positive_vote_mass'], config['threshold_minimum_coverage'])
    return dict(schema='NY_THRESHOLD_FEASIBILITY_DIAGNOSTIC_V1', completed_unix=time.time(),
        config_sha256=config_ref['sha256'], completed_judge_config_sha256=completed['judge_config']['sha256'],
        development_plan_sha256=config['development_plan']['sha256'], pool='registered_judge_dev_threshold_selection',
        oracle=result, GPU_calls=0, model_calls=0, locked_validation_read=False, FINAL_read=False,
        development_reuse_provisional=True, acceptance_precision_claim=False)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', required=True)
    arguments = parser.parse_args()
    print(json.dumps(run(Path(arguments.root).resolve()), sort_keys=True))
