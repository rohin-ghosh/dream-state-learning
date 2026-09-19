"""CPU-testable seed adapter; model creation and scoring remain caller-owned."""

import importlib.util
from pathlib import Path

from construct_candidate import CONTRACT, digest, require, sha


def load_contract(source_directory, expected_sha256):
    source = Path(source_directory) / CONTRACT
    require(not source.is_symlink() and sha(source) == expected_sha256, 'original_contract_bytes')
    spec = importlib.util.spec_from_file_location('replication_original_contract', source)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def run_cells(contract, backend, scenes, candidate, score, emit):
    epoch = candidate['sampling_epoch']
    require(digest(epoch) == candidate['sampling_epoch_sha256'], 'sampling_epoch_binding')
    require(epoch['tokens_per_cell'] == contract.BUDGET == 1024
        and epoch['decoder'] == contract.DECODER, 'unchanged_budget_and_decoder')
    require(len(scenes) == 3 and len({scene['contest_id'] for scene in scenes}) == 3,
        'three_distinct_original_scenes')
    require(all(set(scene) == {'contest_id', 'canonical_scene'} for scene in scenes),
        'scene_only_no_source_or_private_panel_context')
    seeds = epoch['sampling_seeds']
    require(len(seeds) == 2 and len(set(seeds)) == 2 and not set(seeds) & set(contract.SEEDS),
        'new_sampling_seeds_not_replay')
    results = []
    for scene in scenes:
        for seed in seeds:
            def score_cell(raw, stage, origin):
                return score(scene['contest_id'], seed, raw, stage, origin)

            def emit_cell(value):
                emit(scene['contest_id'], seed, value)

            result = contract.run_cell(backend, scene, seed, score_cell, emit_cell)
            result.update(contest_id=scene['contest_id'], seed=seed,
                diagnostic_epoch_sha256=candidate['sampling_epoch_sha256'])
            results.append(result)
            if result['status'] != 'COMPLETE_FIXED_ACTUAL_TOKEN_BUDGET':
                return dict(status='INCOMPLETE_NOT_ZERO_NO_RETRY', cells=results)
    return dict(status='COMPLETE_FIXED_ACTUAL_TOKEN_BUDGET', cells=results,
        actual_generated_tokens=sum(result['generated_tokens'] for result in results),
        diagnostic_epoch_sha256=candidate['sampling_epoch_sha256'])
