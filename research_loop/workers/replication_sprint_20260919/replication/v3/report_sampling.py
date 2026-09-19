"""Read-only public accounting; never export caption text or private panels."""

import argparse
from collections import Counter
from pathlib import Path

import execution as common
from construct_candidate import require


def summarize(cells):
    seen = set()
    reasons = Counter()
    totals = dict(generated_tokens=0, think_events=0, act_attempts=0, distinct_scored=0,
        distinct_accepted=0, new_pixels=0, acts_without_results=0, rankless_outcomes=0)
    for cell in cells:
        totals['generated_tokens'] += cell['generated_tokens']
        for event in cell['events']:
            is_act = event['origin']['stage'] == 'ACT'
            totals['act_attempts'] += int(is_act)
            totals['think_events'] += int(event['origin']['stage'] == 'THINK')
            results = event['score']['results']
            totals['acts_without_results'] += int(is_act and not results)
            for row in results:
                key = (cell['contest_id'], row['caption_sha256'])
                outcome = row['result']
                if key in seen or outcome.get('cached', False):
                    continue
                seen.add(key)
                scored = outcome.get('rank') is not None
                totals['distinct_scored'] += int(scored)
                totals['distinct_accepted'] += int(outcome.get('accepted') is True)
                totals['new_pixels'] += int(outcome.get('status') == 'new_pixel')
                totals['rankless_outcomes'] += int(not scored)
                if not scored:
                    reasons[str(outcome.get('status', 'rankless_reason_not_recorded'))] += 1
    return dict(totals, rankless_by_status=dict(reasons), accept_rate=(
        totals['distinct_accepted'] / totals['distinct_scored'] if totals['distinct_scored'] else None))


def report(root):
    document = common.read(root / 'REGISTRY.json')
    common.validate_registry(document)
    prepared = common.read(root / 'PREPARED.json')
    common.regular(root / 'REGISTRY.json', prepared['registry_sha256'])
    rows = []
    for job in document['jobs']:
        config = common.read(Path(job['root']) / 'CONFIG.json')
        prepared_job = next(row for row in prepared['jobs'] if row['job_id'] == job['job_id'])
        common.regular(Path(job['root']) / 'CONFIG.json', prepared_job['config_sha256'])
        for seed in common.SEEDS:
            cells, entries = [], []
            for scene in common.SCENE_IDS:
                path = Path(config['root']) / 'players' / config['condition'] / f'{scene}_{seed}/RESULT.json'
                entry = dict(contest_id=scene, seed=seed, path=str(path), status='NO_COMPLETE_CELL_RECEIPT')
                if path.exists():
                    cell = common.read(path)
                    require(cell['diagnostic_epoch_sha256'] == document['diagnostic_epoch_sha256']
                        and cell['contest_id'] == scene and cell['seed'] == seed, 'same_sampling_cell')
                    require(type(cell['generated_tokens']) is int and 0 <= cell['generated_tokens'] <= 1024,
                        'bounded_recorded_cell_tokens')
                    if cell['status'] == 'COMPLETE_FIXED_ACTUAL_TOKEN_BUDGET':
                        require(cell['generated_tokens'] == 1024, 'completed_original_cell_budget')
                        cells.append(cell)
                    else:
                        require(cell['status'].startswith('INCOMPLETE_'), 'known_incomplete_cell_status')
                    entry.update(status=cell['status'], sha256=common.sha(path), metrics=summarize([cell]),
                        observed_generated_tokens=cell['generated_tokens'])
                entries.append(entry)
            metrics = summarize(cells)
            rows.append(dict(arm=job['arm'], seed=seed, status='COMPLETE' if len(cells) == 3 else 'INCOMPLETE',
                actual_generated_tokens=metrics['generated_tokens'] if len(cells) == 3 else None,
                expected_generated_tokens=3072, complete_cells_only=metrics, cells=entries,
                missing_cells=sum(entry['status'] == 'NO_COMPLETE_CELL_RECEIPT' for entry in entries),
                incomplete_present_cells=sum(entry['status'].startswith('INCOMPLETE_') for entry in entries)))
    return dict(schema='C2_SAMPLING_PUBLIC_ACCOUNTING_V1',
        diagnostic_epoch_sha256=document['diagnostic_epoch_sha256'],
        judge_epoch_sha256=document['diagnostic_epoch']['judge_epoch_sha256'],
        preregistration=document['preregistration'], independent_training_lineages=False,
        rows=rows, missing_cells_are_not_zero=True, private_payloads_exported=False)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, required=True)
    args = parser.parse_args()
    print(common.json.dumps(report(args.root), indent=2, sort_keys=True, allow_nan=False))


if __name__ == '__main__':
    main()
