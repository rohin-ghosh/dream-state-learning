"""Sanitized exact-token measurements for a separately source-bound age."""

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import subprocess
import time


def read(path):
    return json.loads(path.read_bytes())


def reference(path):
    return dict(sha256=hashlib.sha256(path.read_bytes()).hexdigest(), bytes=path.stat().st_size)


def observe(root):
    identity = read(root / 'CONDITION.json')
    output = root / 'players' / identity['condition']
    result = dict(schema='R233_BOUND_AGE_PROBE_MEASUREMENT_V1', unix=time.time(),
        condition=identity['condition'], source=read(root / 'sources/CAPTURE.json')['sources'][0],
        freshness=read(root / 'FRESHNESS_VERIFIED.json'), condition_receipt=reference(root / 'CONDITION.json'),
        source_manifest=reference(root / 'SOURCE_MANIFEST.json'), status='NOT_LOADED',
        parent_tokens=0, optimizer_updates=0, source_context_used=False, generated_tokens=0,
        actual_tokens_by_stage=dict(THINK=0, ACT=0, LEARN=0, other=0), planned_generated_tokens=6144,
        newly_scored_strings=0, accepted_new_scores=0, new_pixel_events=0, repeated_accepted_events=0,
        cached_strings=0, completed_cells=0, seed_curves={}, cells=[], process_alive=False,
        literal_caption_quality_reviewed=0, raw_acceptance_not_certified_humor=True,
        new_pixels_are_independent_seed_events_not_global_unique_ideas=True,
        whole_generation_tokens_charged_before_credit=True, not_causal_cross_lineage_age_series=True)
    for name, key in [('LOADED.json', 'loaded'), ('COMPLETE.json', 'complete')]:
        path = output / name
        if path.exists():
            value = read(path)
            result[key] = dict(receipt=reference(path), **{field: value[field] for field in
                ['unix', 'pid', 'identity', 'actual_generated_tokens', 'elapsed_seconds', 'unchanged_identity'] if field in value})
            result['status'] = 'COMPLETE' if key == 'complete' else 'LOADED'
    if 'loaded' in result:
        process = Path('/proc') / str(result['loaded']['pid']) / 'stat'
        result['process_alive'] = process.exists() and process.read_text().rsplit(')', 1)[1].split()[0] != 'Z'
    judge = root / 'JUDGE_LOADED.json'
    if judge.exists():
        loaded = read(judge)
        result['judge'] = {key: loaded[key] for key in ['pid', 'unix', 'rule_sha256', 'panel_sha256']}
    for role in ('player', 'judge'):
        path = root / (role + '_FAILED.json')
        if path.exists():
            result[role + '_failure'] = read(path)
            result['status'] = 'FAILED_PRESERVED'
    records = []
    for path in output.glob('*/*.json'):
        if path.name == 'RESULT.json':
            cell = read(path)
            result['cells'].append(dict(contest_id=cell['contest_id'], seed=cell['seed'], status=cell['status'],
                generated_tokens=cell['generated_tokens'], initial_context_sha256=cell['initial_context_sha256'],
                receipt=reference(path)))
            result['completed_cells'] += int(cell['status'] == 'COMPLETE_FIXED_ACTUAL_TOKEN_BUDGET')
        elif path.stem.isdigit():
            record = read(path)
            records.append((record['generation']['started_unix'], path, record))
    totals = {seed: Counter() for seed in (23201, 23202)}
    for started, path, record in sorted(records):
        event = record['event']
        seed = int(path.parent.name.rsplit('_', 1)[1])
        cost = event['actual_generated_tokens']
        result['generated_tokens'] += cost
        result['actual_tokens_by_stage'][event['origin']['stage']] += cost
        totals[seed]['tokens'] += cost
        for item in event['score']['results']:
            outcome = item['result']
            if outcome.get('cached'):
                result['cached_strings'] += 1
                continue
            result['newly_scored_strings'] += int(outcome.get('rank') is not None)
            accepted = outcome.get('accepted') is True
            pixel = accepted and outcome.get('status') == 'new_pixel'
            result['accepted_new_scores'] += int(accepted)
            result['new_pixel_events'] += int(pixel)
            result['repeated_accepted_events'] += int(accepted and outcome.get('status') == 'repeat')
            totals[seed]['accepted'] += int(accepted)
            totals[seed]['pixels'] += int(pixel)
        result['seed_curves'].setdefault(str(seed), []).append(dict(cumulative_generated_tokens=totals[seed]['tokens'],
            cumulative_new_pixel_events=totals[seed]['pixels'], cumulative_accepted_new_scores=totals[seed]['accepted'],
            response_receipt_sha256=reference(path)['sha256'], finished_unix=record['generation']['finished_unix']))
    result['remaining_budget_tokens'] = 6144 - result['generated_tokens']
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', required=True)
    args = parser.parse_args()
    source = Path(__file__).read_text().rsplit("if __name__ == '__main__':", 1)[0]
    code = source + '\nprint(json.dumps(observe(Path(' + repr(args.root) + '))))\n'
    process = subprocess.run(['bash', 'gpu/ovx4_ssh.sh', 'python3 -B -'], input=code,
        text=True, capture_output=True, timeout=40)
    if process.returncode:
        raise RuntimeError(process.stderr[-1400:])
    result = json.loads(process.stdout)
    root = Path(__file__).resolve().parent
    (root / (result['condition'] + '_STATUS.json')).write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({key: result[key] for key in ['unix', 'condition', 'status', 'loaded', 'process_alive',
        'generated_tokens', 'completed_cells', 'newly_scored_strings', 'accepted_new_scores', 'new_pixel_events'] if key in result}))


if __name__ == '__main__':
    main()
