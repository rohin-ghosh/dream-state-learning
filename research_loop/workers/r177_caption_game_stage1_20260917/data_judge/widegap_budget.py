"""Fresh widegap100k Builder allocation without changing any machine lease."""

import math

from gpu import ny_caption_data as data


RUN_SECONDS = 20400
RESERVE_SECONDS = 1800
ALLOCATION_SECONDS = 21600
MARGIN_SECONDS = 60


def validate(budget, inventory, config, now):
    data.require(budget['schema'] == 'NY_WIDEGAP100K_EXPERIMENT_BUDGET_V1'
        and budget['machine_lease_extended'] is False
        and budget['authority'] == 'Main/Astra Builder under user standing directives', 'explicit_Builder_budget_not_lease_extension')
    data.require(budget['root'] == inventory['root'] and budget['lease'] == inventory['lease']
        and budget['device_uuid'] == 'GPU-35dcea35-12bc-f2f3-d5d2-d2eaa8bacdd8', 'exact_budget_root_lease_device')
    start, end = budget['start_unix'], budget['deadline_unix']
    data.require(all(type(value) in (int, float) and math.isfinite(value) for value in (start, end, now)), 'finite_budget_clock')
    data.require(0 < end-start <= ALLOCATION_SECONDS and start <= now
        and end == inventory['allocation_end_unix']
        and end+MARGIN_SECONDS <= inventory['lease_safe_end_unix'], 'bounded_fresh_allocation_inside_unchanged_machine_lease')
    data.require(config['max_seconds'] == RUN_SECONDS and config['calibration_reserve_seconds'] == RESERVE_SECONDS
        and budget['max_gpu_seconds'] == RUN_SECONDS and budget['calibration_reserve_seconds'] == RESERVE_SECONDS
        and now+RUN_SECONDS+MARGIN_SECONDS < end, 'complete_fit_and_calibration_must_fit_fresh_budget')
    sources = {name: reference['sha256'] for name, reference in inventory['files'].items()
        if name.endswith('.py') and not name.startswith('support/')}
    data.require(sources == budget['source_sha256'] and sources, 'budget_bound_to_exact_candidate_sources')
