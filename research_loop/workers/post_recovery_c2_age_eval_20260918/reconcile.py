"""Non-material, offline reporting repair; preserve both recorded metric definitions."""

from collections import Counter
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import runpy


HERE = Path(__file__).resolve().parent
RENDERER = HERE.parent / 'post_recovery_age_queue_20260918/report.py'
METRICS = ('distinct_scored', 'distinct_accepted', 'new_pixels')


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require(condition, message):
    if not condition:
        raise ValueError(message)


def summarize(cells):
    totals, seen, pixel_ids = {}, {}, {}
    for cell in cells:
        seed = str(cell['seed'])
        state = totals.setdefault(seed, dict(counts=Counter(), curve=[]))
        counts = state['counts']
        known = seen.setdefault(seed, set())
        pixels = pixel_ids.setdefault(seed, set())
        for event in cell['events']:
            counts['events'] += 1
            counts['generated_tokens'] += event['actual_generated_tokens']
            counts['event_new_pixels'] += event['score']['new_pixels']
            results = event['score']['results']
            is_act = event['origin']['stage'] == 'ACT'
            counts['act_attempts'] += int(is_act)
            counts['acts_without_scored_strings'] += int(is_act and not results)
            for scored in results:
                result = scored['result']
                key = (cell['contest_id'], scored['caption_sha256'])
                values = (result.get('rank') is not None, result.get('accepted') is True,
                    result.get('status') == 'new_pixel')
                duplicate = key in known
                replayed = result.get('replayed', False)
                counts['duplicate_rows'] += int(duplicate)
                counts['replayed_rows'] += int(replayed)
                counts['cached_rows'] += int(result.get('cached', False))
                for metric, value in zip(METRICS, values, strict=True):
                    counts['raw_' + metric] += int(value)
                    counts['replayed_' + metric] += int(value and replayed)
                    if not duplicate and not result.get('cached', False):
                        counts[metric] += int(value)
                if values[2]:
                    pixels.add((cell['contest_id'], result['pixel_id']))
                if not result.get('cached', False):
                    known.add(key)
            state['curve'].append({name: counts[name] for name in ('generated_tokens', *METRICS)})
        counts['distinct_new_pixel_ids'] = len(pixels)
    return {seed: dict(state['counts'], curve=state['curve']) for seed, state in totals.items()}


def trajectory(row):
    return [(cell['contest_id'], cell['seed'], cell['initial_context_sha256'], [
        (event['actual_generated_tokens'], event['origin']['stage'], event['origin']['text_sha256'],
            event['score']['new_pixels'], [(scored['caption_sha256'],
                {key: scored['result'].get(key) for key in
                    ('rank', 'accepted', 'status', 'cached', 'replayed', 'pixel_count')})
                for scored in event['score']['results']]) for event in cell['events']]) for cell in row['cells']]


def source_pointers(receipt):
    def bind(path):
        return dict(path=path, **receipt['files'][path])

    return {label: {row['arm']: dict(
        config=bind(row['root'] + '/CONFIG.json'),
        loaded=bind(row['output'] + '/LOADED.json'),
        complete=bind(row['output'] + '/COMPLETE.json'),
        source_manifest=bind(row['root'] + '/SOURCE_MANIFEST.json'),
        game_manifest=bind(row['root'] + '/GAME_MANIFEST.json'),
        cell_results=[bind(row['output'] + f"/{cell['contest_id']}_{cell['seed']}/RESULT.json")
            for cell in row['cells']]) for row in block['rows']} for label, block in receipt['blocks'].items()}


def reconcile(receipt, original):
    require(receipt['all_files_stable'], 'stable_completed_files')
    block = receipt['blocks']['c2']
    require(block['batch'] == original['batch'], 'same_complete_batch')
    require([row['arm'] for row in block['rows']] == ['base', 'c2sleep51', 'c2sleep117'], 'exact_c2_arms')
    summaries = {}
    for row, prior in zip(block['rows'], original['rows'], strict=True):
        require(row['arm'] == prior['arm'], 'same_arm')
        expected_root = block['root'] + '/' + row['arm']
        require(row['root'] == expected_root and row['config']['root'] == expected_root, 'same_block_root')
        require(row['output'] == expected_root + '/players/' + row['config']['identity']['condition'], 'same_output')
        for field, path in dict(config_sha256=row['root'] + '/CONFIG.json',
                source_manifest_sha256=row['root'] + '/SOURCE_MANIFEST.json',
                loaded_sha256=row['output'] + '/LOADED.json',
                complete_sha256=row['output'] + '/COMPLETE.json').items():
            require(receipt['files'][path]['sha256'] == prior[field], 'same_receipt_' + field)
        require(row['source_closure_verified'], 'source_closure_verified')
        require(row['loaded']['identity'] == prior['identity'], 'same_loaded_identity')
        require(row['complete']['unchanged_identity'] == prior['unchanged_identity'], 'frozen_completion_identity')
        require(row['complete']['judge_epoch_sha256'] == prior['judge_epoch_sha256'], 'same_judge')
        require(row['config']['seeds'] == [23201, 23202] and row['config']['token_budget'] == 6144, 'same_budget')
        require(row['complete']['actual_generated_tokens'] == 6144 and len(row['cells']) == 6, 'complete_budget')
        require(row['complete']['training_updates'] == 0 and row['complete']['parent_tokens'] == 0, 'no_updates_or_parent')
        require(all(cell['generated_tokens'] == cell['budget'] == 1024 and cell['no_updates']
            and cell['parent_tokens'] == 0 for cell in row['cells']), 'six_complete_frozen_cells')
        counts = summarize(row['cells'])
        require(set(counts) == {'23201', '23202'}, 'independent_seeds')
        for seed, values in counts.items():
            require(values['generated_tokens'] == 3072, 'equal_actual_tokens')
            for name, expected in prior['per_seed'][seed].items():
                require(values[name] == expected, 'receipt_metric_' + name)
            require(values['cached_rows'] == 0 and values['duplicate_rows'] == values['replayed_rows'], 'replay_explanation')
            require(values['event_new_pixels'] == values['raw_new_pixels'], 'event_counter_definition')
            require(values['new_pixels'] == values['distinct_new_pixel_ids'], 'unique_pixel_identity_crosscheck')
            for name in METRICS:
                require(values['raw_' + name] - values['replayed_' + name] == values[name], 'exact_replay_delta')
        summaries[row['arm']] = counts
    earlier, current = receipt['blocks']['earlier']['rows'][0], block['rows'][0]
    require(earlier['source_manifest'] == current['source_manifest'], 'same_evaluator_source')
    require(earlier['loaded']['identity'] == current['loaded']['identity'], 'same_base_identity')
    require(trajectory(earlier) == trajectory(current), 'same_seed_base_trajectories')
    configs = [deepcopy(row['config']) for row in (earlier, current)]
    for config in configs:
        for key in ('root', 'epoch_root', 'deadline_unix', 'source_readiness_sha256'):
            config.pop(key, None)
        config['identity'].pop('condition')
    require(configs[0] == configs[1], 'same_base_protocol_after_operational_labels')
    return dict(same_c2_files_match_original_receipt=True, all_original_seed_counts_and_curves_reproduced=True,
        raw_minus_replayed_equals_distinct=True, same_base_protocol=True,
        same_base_generated_text_and_score_trajectories=True, independent_blocks_not_independent_replicates=True,
        original_distinct_counts_stand=True, within_block_arithmetic_comparison_stands=True,
        broad_beat_base_claim_retracted=True, raw_event_counts_are_not_distinct_new_pixels=True,
        source_pointers=source_pointers(receipt),
        per_seed={arm: {seed: {name: value for name, value in counts.items() if name != 'curve'}
            for seed, counts in seeds.items()} for arm, seeds in summaries.items()})


def main():
    receipt = json.loads((HERE / 'SAME_BLOCK_REMOTE_RECEIPT.json').read_bytes())
    original = json.loads((HERE / 'AGE_BLOCK_REFRESH.json').read_bytes())
    evidence = reconcile(receipt, original)
    markdown, svg = runpy.run_path(str(RENDERER))['render'](original)
    markdown = markdown.split('\nThe first operator-protocol failure', 1)[0]
    markdown += ('\n\n## Same-block reconciliation\n\n'
        'Read-only completed-file audit: ' + receipt['observed_utc'] + '.\n'
        'All C2 CONFIG/LOADED/COMPLETE/source-manifest hashes match AGE_BLOCK_REFRESH.json.\n'
        'The table and curves count distinct scene/caption hashes per independent seed.\n'
        'Raw event new_pixels includes replayed prior successes; it is not newly created pixels.\n'
        'Same-block raw pixels: base28/40; c2sleep51 35/31; c2sleep117 22/26 (seeds23201/23202).\n'
        'Distinct pixels: base15/24; c2sleep51 34/31; c2sleep117 19/26.\n'
        'See RESULTS.md and RECONCILIATION.json for scored/accepted counts, definitions and exact receipts.\n'
        'The original factual distinct counts and within-block arithmetic comparison stand unchanged.\n'
        'The broad beat-base claim remains retracted; no causal or certified-humor conclusion.\n'
        'Raw replay-inclusive event counts are not replacement distinct-new-pixel counts.\n'
        'The September19 00:39 UTC eval-controller lease failure was not bypassed.\n'
        'Only separately authorized node-scope metadata reads were used; no new jobs, life signals or parent deliveries.\n')
    svg = svg.replace('New embedding pixels', 'Distinct new embedding pixels')
    for name, content in (('STATUS.md', markdown), ('TOKEN_CURVES.svg', svg)):
        path = HERE / name
        previous = HERE / (path.stem + '_2212' + path.suffix)
        if not previous.exists():
            previous.write_bytes(path.read_bytes())
        path.write_text(content)
    evidence.update(original_observed_utc=original['observed_utc'], audit_observed_utc=receipt['observed_utc'],
        repair_scope='Non-material reporting clarification only; evaluator and scientific claim boundaries unchanged.',
        metric_definitions=dict(raw='All returned rank/accepted/new_pixel result rows, including replayed responses.',
            distinct='First non-cached (contest_id, caption_sha256) per seed; new pixels cross-checked by pixel_id.',
            event_new_pixels='Recorded sum; checks cached, not replayed, and therefore repeats old new_pixel status.'),
        local_sha256={name: sha(HERE / name) for name in ('AGE_BLOCK_REFRESH.json',
            'SAME_BLOCK_REMOTE_RECEIPT.json', 'REPORTER_SOURCE_RECEIPT.json', 'RECEIVING_PROVENANCE.json',
            'audit_reader.py', 'reconcile.py', 'test_report.py', 'RESULTS.md', 'STATUS.md', 'TOKEN_CURVES.svg',
            'STATUS_2212.md', 'TOKEN_CURVES_2212.svg')}, renderer_sha256=sha(RENDERER))
    (HERE / 'RECONCILIATION.json').write_text(json.dumps(evidence, sort_keys=True, indent=2) + '\n')
    print('All original counts/curves reproduced from 350 stable same-file receipts; reports rendered.')


if __name__ == '__main__':
    main()
