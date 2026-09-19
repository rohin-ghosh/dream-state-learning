"""Independent offline accounting of bounded public sampling receipts."""

import argparse
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path


COMPLETE = 'COMPLETE_FIXED_ACTUAL_TOKEN_BUDGET'
METRICS = ('generated_tokens', 'think_events', 'act_attempts', 'distinct_scored',
    'distinct_accepted', 'new_pixels', 'acts_without_results', 'rankless_outcomes')
IDENTITY_FIELDS = ('base_sha256', 'adapter_state_sha256', 'decoder',
    'tokenizer_backend_sha256', 'chat_template_sha256', 'library_versions',
    'all_parameters_frozen', 'optimizer_created')


class EvidenceError(ValueError):
    pass


def require(condition, message):
    if not condition:
        raise EvidenceError(message)


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False,
        separators=(',', ':'), allow_nan=False).encode()).hexdigest()


def verified(reference):
    require(reference is not None, 'missing_receipt')
    require(digest(reference['payload']) == reference['projection_sha256'], 'projection_hash_mismatch')
    return reference['payload']


def outcome_signature(outcome):
    return tuple(outcome.get(name) for name in ('rank', 'accepted', 'status', 'pixel_id'))


def cell_metrics(cell, plan):
    require(cell['budget'] == plan['tokens_per_cell'], 'wrong_cell_budget')
    require(type(cell['generated_tokens']) is int and 0 <= cell['generated_tokens'] <= cell['budget'],
        'invalid_generated_tokens')
    require(cell['status'] == COMPLETE or cell['status'].startswith('INCOMPLETE_'), 'unknown_cell_status')
    if cell['status'] == COMPLETE:
        require(cell['generated_tokens'] == cell['budget'], 'complete_cell_shortfall')
        require(cell.get('no_updates') is True and cell.get('parent_tokens') == 0
            and cell.get('learn_or_other_reply_tokens') == 0, 'not_parent_free_frozen_cell')
    counts = Counter({key: 0 for key in METRICS})
    diagnostics = Counter({name: 0 for name in ('duplicate_events', 'returned_outcomes',
        'returned_scored', 'returned_accepted', 'returned_new_pixel_statuses', 'cached_returns',
        'replayed_returns', 'duplicate_caption_returns', 'rankless_fresh_attempts')})
    error_codes = Counter()
    reasons = Counter()
    seen_events, grouped = {}, defaultdict(list)
    position = 0
    for event in cell['events']:
        origin = event['origin']
        key = digest(origin)
        event_hash = digest(event)
        if key in seen_events:
            require(seen_events[key] == event_hash, 'conflicting_duplicate_event')
            diagnostics['duplicate_events'] += 1
            continue
        seen_events[key] = event_hash
        stage = origin['stage']
        require(stage in ('ACT', 'THINK'), 'unknown_generation_stage')
        require(stage == ('THINK' if len(seen_events) % 2 else 'ACT'), 'nonalternating_stage')
        tokens = event['actual_generated_tokens']
        require(type(tokens) is int and 0 < tokens <= event['requested_max_new_tokens']
            <= min(128 if stage == 'THINK' else 256, cell['budget'] - position), 'invalid_event_token_count')
        require(origin['generated_tokens_before'] == position
            and origin['generated_tokens_after'] == position + tokens, 'token_range_gap_overlap')
        position += tokens
        score = event['score']
        require(score['judge_epoch_sha256'] == plan['judge_epoch_sha256']
            and score['diagnostic_epoch_sha256'] == plan['diagnostic_epoch_sha256'], 'mixed_score_epoch')
        counts['act_attempts' if stage == 'ACT' else 'think_events'] += 1
        counts['acts_without_results'] += int(stage == 'ACT' and not score['results'])
        for row in score['results']:
            caption = row['caption_sha256']
            require(isinstance(caption, str) and len(caption) == 64
                and all(character in '0123456789abcdef' for character in caption), 'invalid_caption_hash')
            outcome = row['result']
            for flag in ('cached', 'replayed'):
                require(type(outcome.get(flag, False)) is bool, 'invalid_cache_replay_flag')
            require(outcome.get('contest_id', cell['contest_id']) == cell['contest_id'], 'wrong_outcome_scene')
            diagnostics['returned_outcomes'] += 1
            diagnostics['returned_scored'] += int(outcome.get('rank') is not None)
            diagnostics['returned_accepted'] += int(outcome.get('accepted') is True)
            diagnostics['returned_new_pixel_statuses'] += int(outcome.get('status') == 'new_pixel')
            diagnostics['cached_returns'] += int(outcome.get('cached', False))
            diagnostics['replayed_returns'] += int(outcome.get('replayed', False))
            if outcome.get('error', {}).get('code') is not None:
                error_codes[outcome['error']['code']] += 1
            grouped[caption].append(outcome)
    require(position == cell['generated_tokens'], 'cell_event_tokens_disagree')
    counts['generated_tokens'] = position
    pixels = set()
    for outcomes in grouped.values():
        diagnostics['duplicate_caption_returns'] += len(outcomes) - 1
        fresh = [outcome for outcome in outcomes if not outcome.get('cached', False)
            and not outcome.get('replayed', False)]
        require(fresh, 'orphan_cached_or_replayed_outcome')
        ranked = [outcome for outcome in fresh if outcome.get('rank') is not None]
        diagnostics['rankless_fresh_attempts'] += len(fresh) - len(ranked)
        if ranked:
            signature = outcome_signature(ranked[0])
            require(all(outcome_signature(outcome) == signature for outcome in ranked), 'conflicting_scored_outcomes')
            require(all(outcome_signature(outcome) == signature for outcome in outcomes
                if outcome.get('cached', False) or outcome.get('replayed', False)), 'conflicting_cached_or_replayed_outcome')
            outcome = ranked[0]
            require(type(outcome['rank']) is int and 1 <= outcome['rank'] <= 65
                and type(outcome.get('accepted')) is bool, 'rank_or_acceptance_not_explicit')
            require(outcome.get('top_k', 50) == 50 and outcome.get('reference_count', 64) == 64, 'wrong_rank_contract')
            require(not outcome['accepted'] or outcome['rank'] <= 50, 'acceptance_rank_contradiction')
            counts['distinct_scored'] += 1
            counts['distinct_accepted'] += int(outcome['accepted'])
            if outcome['status'] == 'new_pixel':
                require(outcome['accepted'] and isinstance(outcome.get('pixel_id'), str), 'unbound_new_pixel')
                require(outcome['pixel_id'] not in pixels, 'new_pixel_id_reused_by_distinct_caption')
                pixels.add(outcome['pixel_id'])
                counts['new_pixels'] += 1
        else:
            require(all(outcome.get('accepted') is not True and outcome.get('status') != 'new_pixel'
                for outcome in outcomes), 'rankless_success_unknown')
            counts['rankless_outcomes'] += 1
            statuses = sorted({str(outcome.get('status', 'rankless_reason_not_recorded')) for outcome in fresh})
            reasons['|'.join(statuses)] += 1
    return dict(counts, rankless_by_status=dict(reasons),
        accept_rate=counts['distinct_accepted'] / counts['distinct_scored'] if counts['distinct_scored'] else None,
        diagnostics=dict(diagnostics), returned_error_codes=dict(error_codes))


def aggregate(rows):
    totals = {key: sum(row[key] for row in rows) for key in METRICS}
    reasons = Counter()
    diagnostics = Counter()
    error_codes = Counter()
    for row in rows:
        reasons.update(row['rankless_by_status'])
        diagnostics.update(row['diagnostics'])
        error_codes.update(row['returned_error_codes'])
    return dict(totals, rankless_by_status=dict(reasons), diagnostics=dict(diagnostics), returned_error_codes=dict(error_codes),
        accept_rate=totals['distinct_accepted'] / totals['distinct_scored'] if totals['distinct_scored'] else None)


def index_unique(rows, identity):
    indexed, copies = {}, 0
    for row in rows:
        key = identity(row)
        if key in indexed:
            require(digest(indexed[key]) == digest(row), 'conflicting_duplicate_record:' + str(key))
            copies += 1
        else:
            indexed[key] = row
    return indexed, copies


def validate_block(snapshot, plan):
    require(snapshot['root'] == plan['root'], 'wrong_snapshot_root')
    docs = snapshot['documents']
    registry = verified(docs['REGISTRY.json'])
    require(docs['REGISTRY.json']['sha256'] == plan['registry_sha256'], 'predeclared_registry_changed')
    require(docs['SOURCE_FREEZE.json']['sha256'] == plan['source_freeze_sha256'], 'predeclared_freeze_changed')
    require(docs['PREREGISTRATION.md']['sha256'] == plan['preregistration_sha256'], 'preregistration_changed')
    epoch = registry['diagnostic_epoch']
    require(digest(epoch) == registry['diagnostic_epoch_sha256'] == plan['diagnostic_epoch_sha256'], 'diagnostic_epoch_mismatch')
    require(epoch['judge_epoch_sha256'] == plan['judge_epoch_sha256'], 'judge_epoch_mismatch')
    require(epoch['sampling_seeds'] == plan['seeds'] and registry['expected_scene_ids'] == plan['scenes']
        and [job['arm'] for job in registry['jobs']] == plan['arms'], 'different_cell_design')
    prepared = verified(docs['PREPARED.json'])
    require(prepared['registry_sha256'] == docs['REGISTRY.json']['sha256']
        and prepared['source_freeze_sha256'] == docs['SOURCE_FREEZE.json']['sha256'], 'prepared_hash_join')
    freeze = verified(docs['SOURCE_FREEZE.json'])
    require(set(snapshot['runtime_files']) == set(freeze['files']), 'runtime_file_set_mismatch')
    for name, checksum in freeze['files'].items():
        require(snapshot['runtime_files'][name]['sha256'] == checksum, 'runtime_changed:' + name)
    return registry, prepared


def validate_job(job, declaration, prepared, plan):
    config = verified(job['config'])
    prepared_rows, duplicates = index_unique(prepared['jobs'], lambda row: row['job_id'])
    require(not duplicates, 'duplicate_prepared_job')
    require(job['config']['sha256'] == prepared_rows[job['job_id']]['config_sha256'], 'config_not_prepared')
    require(job['job_id'] == declaration['job_id'] == config['job_id'] == digest(declaration['identity'])
        and config['job_identity'] == declaration['identity'], 'job_identity_mismatch')
    require(config['diagnostic_epoch_sha256'] == plan['diagnostic_epoch_sha256'], 'config_epoch_mismatch')
    require((config['judge_rank'], config['judge_step'], config['adapter_sha256'])
        == (8, 15625, plan['judge_adapter_sha256']), 'wrong_adopted_judge')
    require(config['seeds'] == plan['seeds'] and config['expected_scene_ids'] == plan['scenes']
        and config['token_budget'] == 6 * plan['tokens_per_cell'] and config['scenes'] == 3, 'config_budget_mismatch')
    require(config['parent_tokens'] == config['training_updates'] == 0
        and config['source_context_loaded'] is False, 'config_not_parent_free_frozen')
    source = declaration['identity']['checkpoint']
    require(config['source_checkpoint'] == source['source_age'], 'wrong_source_checkpoint')
    require(config['plain_base'] is (job['arm'] == 'base'), 'base_adapter_arm_mismatch')
    require((source['source_age'] is None and source['adapter_state_sha256'] is None) if job['arm'] == 'base'
        else source['source_age']['absolute_sleep'] == (51 if job['arm'] == 'c2sleep51' else 117)
        and source['source_age']['adapter_state_sha256'] == source['adapter_state_sha256']
        and source['source_age']['base_sha256'] == source['base_sha256'], 'source_age_weight_join')
    return config, source


def validate_completion(job, config, source, cells, plan):
    loaded = verified(job['loaded'])
    complete = verified(job['complete'])
    verification = verified(job['completion_verified'])
    require(verification['complete_sha256'] == job['complete']['sha256']
        and verification['loaded_sha256'] == job['loaded']['sha256']
        and verification['arm'] == job['arm'] and verification['job_id'] == job['job_id'], 'completion_receipt_join')
    states = verification['unit_states']
    require(len(states) == 2 and all(state['ExecMainStatus'] == '0' and state['Result'] == 'success'
        and state['SubState'] == 'exited' for state in states.values()), 'model_roles_not_successfully_exited')
    for record in (loaded, complete):
        require(record['diagnostic_epoch_sha256'] == plan['diagnostic_epoch_sha256']
            and record['judge_epoch_sha256'] == plan['judge_epoch_sha256'], 'loaded_complete_epoch_mismatch')
        require(record['source_age'] == source['source_age'] and record['condition'] == config['condition'], 'loaded_complete_source_mismatch')
        require(record['parent_tokens'] == 0, 'parent_assistance_present')
    require(loaded['snapshot_context_used'] is False and loaded['source_parent_text_loaded'] is False
        and complete['training_updates'] == 0, 'context_or_training_present')
    require(loaded['identity']['all_parameters_frozen'] is True
        and loaded['identity']['optimizer_created'] is False
        and complete['unchanged_identity']['all_parameters_frozen'] is True, 'parameters_not_frozen')
    for field in IDENTITY_FIELDS:
        require(loaded['identity'][field] == config['original_parameter_identity'][field], 'inference_identity_changed:' + field)
    for field in ('base_sha256', 'adapter_state_sha256'):
        require(loaded['identity'][field] == complete['unchanged_identity'][field] == source[field], 'weight_identity_changed:' + field)
    complete_cells, duplicates = index_unique(complete['cells'], lambda cell: (cell['contest_id'], cell['seed']))
    require(not duplicates and set(complete_cells) == set(cells), 'complete_cell_cross_product_mismatch')
    require(complete['actual_generated_tokens'] == 6 * plan['tokens_per_cell'], 'arm_token_shortfall')
    for key, entry in cells.items():
        require(entry['status'] == COMPLETE, 'arm_has_missing_partial_invalid_cell')
        require(complete_cells[key]['source_object_sha256'] == entry['source_object_sha256'], 'result_complete_content_mismatch')
    return dict(status='VERIFIED_RECORDED_PROVENANCE', base_sha256=source['base_sha256'],
        adapter_state_sha256=source['adapter_state_sha256'], source_age=source['source_age'],
        loaded_sha256=job['loaded']['sha256'], complete_sha256=job['complete']['sha256'])


def audit(snapshot, plan):
    registry, prepared = validate_block(snapshot, plan)
    jobs, duplicate_jobs = index_unique(snapshot['jobs'], lambda job: job['arm'])
    require(set(jobs) == set(plan['arms']), 'missing_or_extra_job')
    expected = {(scene, seed) for scene in plan['scenes'] for seed in plan['seeds']}
    arms, seed_rows, all_cells = [], [], []
    for declaration in registry['jobs']:
        arm = declaration['arm']
        job = jobs[arm]
        config, source = validate_job(job, declaration, prepared, plan)
        supplied, copies = index_unique(job['cells'], lambda cell: (cell['contest_id'], cell['seed']))
        require(set(supplied) <= expected, 'unexpected_cell')
        cells = {}
        for scene, seed in sorted(expected):
            reference = supplied.get((scene, seed), {}).get('result')
            entry = dict(arm=arm, contest_id=scene, seed=seed, status='MISSING', metrics=None,
                source_sha256=None, source_object_sha256=None, issue=None)
            if reference:
                entry.update(source_sha256=reference['sha256'], source_object_sha256=reference['source_object_sha256'])
                try:
                    payload = verified(reference)
                    require(payload['contest_id'] == scene and payload['seed'] == seed
                        and payload['diagnostic_epoch_sha256'] == plan['diagnostic_epoch_sha256'], 'result_identity_mismatch')
                    entry.update(metrics=cell_metrics(payload, plan), status=payload['status'])
                except (EvidenceError, KeyError, TypeError) as error:
                    entry.update(status='INVALID_EVIDENCE', issue=str(error))
            cells[(scene, seed)] = entry
            all_cells.append(entry)
        try:
            provenance = validate_completion(job, config, source, cells, plan)
        except (EvidenceError, KeyError, TypeError) as error:
            provenance = dict(status='UNKNOWN', reason=str(error))
        for seed in plan['seeds']:
            selected = [cells[(scene, seed)] for scene in plan['scenes']]
            completed = [row['metrics'] for row in selected if row['status'] == COMPLETE]
            all_complete = len(completed) == len(plan['scenes'])
            observed = [row['metrics'] for row in selected if row['metrics'] is not None]
            seed_rows.append(dict(arm=arm, seed=seed, cell_status='COMPLETE' if all_complete else 'INCOMPLETE',
                source_verified=provenance['status'] == 'VERIFIED_RECORDED_PROVENANCE',
                expected_cells=3, complete_cells=len(completed), missing_cells=sum(row['status'] == 'MISSING' for row in selected),
                partial_cells=sum(row['status'].startswith('INCOMPLETE_') for row in selected),
                invalid_cells=sum(row['status'] == 'INVALID_EVIDENCE' for row in selected),
                metrics=aggregate(completed) if all_complete else None,
                complete_cells_only=aggregate(completed), observed_valid_cells_only=aggregate(observed)))
        rows = [row for row in seed_rows if row['arm'] == arm]
        eligible = provenance['status'] == 'VERIFIED_RECORDED_PROVENANCE' and all(row['metrics'] is not None for row in rows)
        arms.append(dict(arm=arm, status='COMPLETE' if eligible else 'INCOMPLETE_OR_UNVERIFIED',
            duplicate_cell_copies=copies, provenance=provenance,
            metrics=aggregate([row['metrics'] for row in rows]) if eligible else None))
    indexed_seeds = {(row['arm'], row['seed']): row for row in seed_rows}
    contrasts = []
    for seed in plan['seeds']:
        for left, right in (('c2sleep51', 'base'), ('c2sleep117', 'base'), ('c2sleep51', 'c2sleep117')):
            pair = [indexed_seeds[(arm, seed)] for arm in (left, right)]
            valid = all(row['metrics'] is not None and row['source_verified'] for row in pair)
            delta = pair[0]['metrics']['new_pixels'] - pair[1]['metrics']['new_pixels'] if valid else None
            contrasts.append(dict(seed=seed, contrast=left + '_minus_' + right, delta_new_pixels=delta,
                sign='UNKNOWN' if delta is None else 'positive' if delta > 0 else 'negative' if delta < 0 else 'tie'))
    block_status = 'UNKNOWN'
    block_issue = None
    try:
        block = verified(snapshot['documents']['BLOCK_COMPLETE.json'])
        require(block['diagnostic_epoch_sha256'] == plan['diagnostic_epoch_sha256'], 'block_epoch_mismatch')
        require(block['status'] == 'COMPLETE_THREE_SOURCE_SAMPLING_DIAGNOSTIC', 'wrong_block_completion_status')
        block_jobs, copies = index_unique(block['jobs'], lambda row: row['arm'])
        require(not copies and set(block_jobs) == set(plan['arms']), 'block_job_cross_product_mismatch')
        for arm in arms:
            require(arm['status'] == 'COMPLETE', 'block_has_unverified_arm')
            require(block_jobs[arm['arm']]['job_id'] == jobs[arm['arm']]['job_id'], 'block_job_id_mismatch')
            for key in ('loaded_sha256', 'complete_sha256'):
                require(block_jobs[arm['arm']][key] == arm['provenance'][key], 'block_completion_join')
        block_status = 'COMPLETE'
    except (EvidenceError, KeyError, TypeError) as error:
        block_issue = str(error)
    reconciliation = compare_report(snapshot['runtime_report'], seed_rows, all_cells, plan)
    return dict(schema='INDEPENDENT_SAMPLING_ACCOUNTING_V1', captured_utc=snapshot['captured_utc'],
        root=plan['root'], diagnostic_epoch_sha256=plan['diagnostic_epoch_sha256'], judge_epoch_sha256=plan['judge_epoch_sha256'],
        block_status=block_status, block_issue=block_issue, expected_cells=18,
        actual_generated_tokens=sum(arm['metrics']['generated_tokens'] for arm in arms) if block_status == 'COMPLETE' else None,
        duplicate_job_copies=duplicate_jobs, arms=arms, seeds=seed_rows, cells=all_cells,
        contrasts=contrasts, runtime_reconciliation=reconciliation,
        independent_training_lineages=False, held_out_transfer=False, literal_humor_certified=False,
        cross_seed_totals_are_sums_not_union=True, analysis_deduplication_only=True,
        training_rows_changed=False)


def compare_report(reference, seeds, cells, plan):
    if reference['returncode'] != 0 or reference['payload'] is None:
        return dict(status='UNKNOWN', discrepancies=['runtime_report_unavailable'])
    reported = reference['payload']
    differences = []
    for key in ('diagnostic_epoch_sha256', 'judge_epoch_sha256'):
        if reported.get(key) != plan[key]:
            differences.append(dict(location=key, independent=plan[key], runtime=reported.get(key)))
    reports, duplicates = index_unique(reported['rows'], lambda row: (row['arm'], row['seed']))
    if duplicates or set(reports) != {(row['arm'], row['seed']) for row in seeds}:
        differences.append('runtime_seed_cross_product_mismatch')
    cell_map = {(row['arm'], row['seed'], row['contest_id']): row for row in cells}
    comparisons = 0
    for row in seeds:
        runtime = reports.get((row['arm'], row['seed']))
        if runtime is None:
            continue
        pairs = [(f"{row['arm']}/{row['seed']}", row['complete_cells_only'], runtime['complete_cells_only'])]
        reported_cells, copies = index_unique(runtime['cells'], lambda cell: cell['contest_id'])
        if copies or set(reported_cells) != set(plan['scenes']):
            differences.append('runtime_scene_cross_product_mismatch:' + row['arm'] + '/' + str(row['seed']))
        for key, expected in (('missing_cells', row['missing_cells']), ('incomplete_present_cells', row['partial_cells']),
                ('actual_generated_tokens', row['metrics']['generated_tokens'] if row['metrics'] else None)):
            if runtime.get(key) != expected:
                differences.append(dict(location=f"{row['arm']}/{row['seed']}/{key}", independent=expected, runtime=runtime.get(key)))
        for candidate in runtime['cells']:
            independent = cell_map.get((row['arm'], row['seed'], candidate['contest_id']))
            if independent and candidate['status'] != ('NO_COMPLETE_CELL_RECEIPT' if independent['status'] == 'MISSING' else independent['status']):
                differences.append('runtime_cell_status_mismatch:' + row['arm'] + '/' + candidate['contest_id'])
            if independent and independent['metrics'] is not None and 'metrics' in candidate:
                if independent['source_sha256'] != candidate['sha256']:
                    differences.append('report_result_hash_mismatch:' + candidate['path'])
                pairs.append((f"{row['arm']}/{row['seed']}/{candidate['contest_id']}", independent['metrics'], candidate['metrics']))
        for label, independent, runtime_metrics in pairs:
            for key in (*METRICS, 'rankless_by_status', 'accept_rate'):
                comparisons += 1
                if independent[key] != runtime_metrics[key]:
                    differences.append(dict(location=label + '/' + key, independent=independent[key], runtime=runtime_metrics[key]))
        if row['cell_status'] != runtime['status']:
            differences.append(dict(location=f"{row['arm']}/{row['seed']}/status",
                independent=row['cell_status'], runtime=runtime['status']))
    return dict(status='MATCH' if not differences else 'DIFFERENCE', comparisons=comparisons, discrepancies=differences)


def markdown(report):
    lines = ['# Independent selected-checkpoint sampling accounting', '',
        f"Snapshot: {report['captured_utc']}. Block: **{report['block_status']}**. "
        f"Generated tokens: {report['actual_generated_tokens']}. Expected cells: 18.", '',
        '## Per-seed results', '', '| Arm | Seed | Complete cells | Scored | Accepted | New pixels | Generated tokens | Source verified |',
        '|---|---:|---:|---:|---:|---:|---:|---|']
    for row in report['seeds']:
        metrics = row['metrics'] or {}
        values = [metrics.get(key, 'UNKNOWN') for key in ('distinct_scored', 'distinct_accepted', 'new_pixels', 'generated_tokens')]
        lines.append('| ' + ' | '.join(map(str, [row['arm'], row['seed'], row['complete_cells'], *values, row['source_verified']])) + ' |')
    lines += ['', '## All cells', '', '| Arm | Seed | Scene | Status | Scored | Accepted | New pixels | Tokens |',
        '|---|---:|---|---|---:|---:|---:|---:|']
    for row in report['cells']:
        metrics = row['metrics'] or {}
        values = [metrics.get(key, 'UNKNOWN') for key in ('distinct_scored', 'distinct_accepted', 'new_pixels', 'generated_tokens')]
        lines.append('| ' + ' | '.join(map(str, [row['arm'], row['seed'], row['contest_id'], row['status'], *values])) + ' |')
    lines += ['', '## Every matched-seed contrast', '', '| Seed | Contrast | New-pixel delta | Sign |', '|---:|---|---:|---|']
    for row in report['contrasts']:
        lines.append(f"| {row['seed']} | {row['contrast']} | {row['delta_new_pixels']} | {row['sign']} |")
    lines += ['', '## Reconciliation and limitations', '',
        f"Runtime report comparison: **{report['runtime_reconciliation']['status']}**. See JSON for every comparison discrepancy.",
        'Complete-only subtotals, partial cells, duplicate returns, rankless outcomes, and provenance issues are retained in JSON.',
        'Tokens include THINK and ACT, not prompts, training compute, or judge compute. THINK candidates are also scored.',
        'Across-seed totals are sums of independent seed-local novelty archives, not a union of distinct ideas.',
        'Acceptance is the operational adopted-judge rule, not certified literal humor.',
        'Selected-checkpoint sampling is NOT independent training replication, held-out transfer, or evidence isolating parenting/consolidation.',
        'Weight provenance is checked from source-bound pre/post receipts, not by rereading tensors. No authentic rows or training policy changed.', '']
    return '\n'.join(lines)


def source_manifest(snapshot, snapshot_path, plan_path):
    sources = {}

    def walk(value):
        if isinstance(value, dict):
            if {'path', 'bytes', 'sha256'} <= set(value):
                reference = {key: value[key] for key in ('path', 'bytes', 'sha256',
                    'source_object_sha256', 'projection_sha256') if key in value}
                require(reference['path'] not in sources or sources[reference['path']] == reference,
                    'conflicting_source_reference')
                sources[reference['path']] = reference
            for child in value.values():
                walk(child)
        elif isinstance(value, list):
            for child in value:
                walk(child)

    walk(snapshot)
    local = []
    for path in (snapshot_path, plan_path, Path(__file__), Path(__file__).with_name('export_public.py')):
        raw = path.read_bytes()
        local.append(dict(path=str(path), bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest()))
    return dict(schema='INDEPENDENT_ACCOUNTING_SOURCE_MANIFEST_V1', captured_utc=snapshot['captured_utc'],
        remote_route='bash gpu/ovx4_ssh.sh', remote_root=snapshot['root'], sources=list(sources.values()),
        local_files=local, source_bytes_not_copied_verbatim=True,
        projection_contract='export_public.py allowlist; full source-file SHA and canonical object SHA retained',
        source_scores_are_development_outcomes_only=True, private_panels_read=False,
        parameter_provenance='recorded pre/post tensor and adapter-file hashes; no independent tensor rehash')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--snapshot', type=Path, required=True)
    parser.add_argument('--plan', type=Path, default=Path(__file__).with_name('PLAN.json'))
    parser.add_argument('--markdown', action='store_true')
    parser.add_argument('--manifest', action='store_true')
    args = parser.parse_args()
    snapshot = json.loads(args.snapshot.read_text())
    if args.manifest:
        print(json.dumps(source_manifest(snapshot, args.snapshot, args.plan), indent=2, sort_keys=True))
        return
    result = audit(snapshot, json.loads(args.plan.read_text()))
    print(markdown(result) if args.markdown else json.dumps(result, indent=2, sort_keys=True, allow_nan=False))


if __name__ == '__main__':
    main()
