"""Reproducible constructed contrasts on fitting-held DEVELOPMENT contests only."""

import argparse
from collections import defaultdict
import hashlib
import json
import math
import os
from pathlib import Path
import random
import time

from gpu import ny_caption_data as data
from gpu.ny_caption_scalar_judge import ScalarJudge


TYPES = ('word_shuffled', 'other_contest', 'scene_description', 'truncated', 'nonsense', 'mid_tier')


def pseudonym(contest):
    return hashlib.sha256(('R207_CONTEST:' + str(contest)).encode()).hexdigest()[:16]


def choose_contests(manifest, wanted, seed, eligible=None):
    data.require(type(wanted) is int and 2 <= wanted <= 100, 'bounded_contrast_contests')
    held = set(manifest['pools']['judge_dev'])
    data.require(not held.intersection(manifest['pools']['judge_train']), 'no_fitting_contest_leakage')
    if eligible is not None:
        data.require(set(eligible) <= held, 'eligible_contests_held_from_fitting')
        held.intersection_update(eligible)
    groups = [sorted(group) for group in manifest['scene_groups'] if set(group) <= held]
    random.Random(seed).shuffle(groups)
    chosen = []
    for group in groups:
        if len(chosen) + len(group) <= wanted:
            chosen.extend(group)
    data.require(len(chosen) == wanted, 'requested_whole_scene_group_count_available')
    return chosen


def make_cases(rows, wanted_top=5, seed=207):
    data.require(type(wanted_top) is int and 1 <= wanted_top <= 20, 'bounded_top_captions')
    groups = defaultdict(list)
    for row in rows:
        if (isinstance(row.get('published_rank'), (int, float))
                and not isinstance(row['published_rank'], bool)
                and math.isfinite(row['published_rank']) and row['published_rank'] > 0
                and isinstance(row.get('caption'), str) and 2 <= len(row['caption'].split()) <= 50):
            groups[row['contest_id']].append(row)
    data.require(len(groups) >= 2, 'two_distinct_held_contests_required')
    ordered = {}
    for contest, values in groups.items():
        values.sort(key=lambda row: (row['published_rank'], data.digest(row['caption'])))
        unique = {}
        for row in values:
            unique.setdefault(data.normalize_caption(row['caption']), row)
        ordered[contest] = list(unique.values())
        data.require(len(ordered[contest]) >= 4 * wanted_top, 'enough_real_ranked_captions_for_mid_tier')
    rng = random.Random(seed)
    names = sorted(ordered)
    cases = []
    for contest_index, contest in enumerate(names):
        ranked = ordered[contest]
        other_names = [name for name in names if ordered[name][0]['scene_group_sha256']
                       != ranked[0]['scene_group_sha256']]
        data.require(other_names, 'other_contest_not_same_scene_group')
        other = ordered[other_names[contest_index % len(other_names)]]
        for top_index, good in enumerate(ranked[:wanted_top]):
            words = good['caption'].split()
            shuffled = words[:]
            rng.shuffle(shuffled)
            if shuffled == words:
                shuffled = words[1:] + words[:1]
            try:
                description = json.loads(good['scene'])['canny']
            except (json.JSONDecodeError, KeyError, TypeError):
                description = good['scene']
            mid = ranked[len(ranked) // 2 + top_index]
            alternatives = {
                'word_shuffled': ' '.join(shuffled),
                'other_contest': other[top_index]['caption'],
                'scene_description': ' '.join(('This cartoon shows ' + description).split()[:50]),
                'truncated': ' '.join(words[:max(1, len(words) // 3)]),
                'nonsense': 'Zorp flibble twenty-seven banana sprocket.',
                'mid_tier': mid['caption'],
            }
            for kind, alternative in alternatives.items():
                case = dict(contest=pseudonym(contest), kind=kind, top_index=top_index,
                            scene=good['scene'], good=good['caption'], contrast=alternative,
                            good_published_rank=good['published_rank'],
                            contrast_published_rank=mid['published_rank'] if kind == 'mid_tier' else None)
                case['case_id'] = data.digest(case)
                cases.append(case)
    return cases


def summarize(records):
    def summary(group):
        scored = [row for row in group if row['status'] == 'SCORED']
        wins = sum(row['good_score'] > row['contrast_score'] for row in scored)
        ties = sum(row['good_score'] == row['contrast_score'] for row in scored)
        return dict(opportunities=len(group), scored=len(scored), skipped=len(group) - len(scored),
                    wins=wins, ties=ties, losses=len(scored) - wins - ties,
                    strict_accuracy=wins / len(scored) if scored else None,
                    tie_half_accuracy=(wins + ties / 2) / len(scored) if scored else None)
    by_type = {kind: summary([row for row in records if row['kind'] == kind]) for kind in TYPES}
    by_contest = {name: {kind: summary([row for row in records if row['contest'] == name
                                      and row['kind'] == kind]) for kind in TYPES}
                  for name in sorted({row['contest'] for row in records})}
    return dict(overall=summary(records), by_type=by_type, by_contest=by_contest)


def run(args):
    output = Path(args.output).resolve()
    output.mkdir(parents=True, mode=0o700, exist_ok=False)
    started = time.time()
    config_ref = data.file_ref(Path(args.judge_config).resolve())
    config = data.bound(config_ref)
    manifest_ref = config['config']['data_manifest']
    manifest = data.load_manifest(manifest_ref)
    plan = data.bound(config['config']['development_plan'])
    eligible = [contest for name, subset in plan['subsets'].items() if name != 'judge_train'
                for contest in subset]
    contests = choose_contests(manifest, args.contests, args.seed, eligible)
    cases = make_cases(list(data.evaluator_rows(manifest_ref, 'judge_dev', contest_ids=contests)),
                       args.top, args.seed)
    private_ref = data.private_write(output / 'CASES.private.json', cases)
    data.private_write(output / 'STARTED.json', dict(started_unix=started, pid=os.getpid(),
                       judge=args.name, judge_config=config_ref, cases=len(cases), contests=len(contests),
                       device=os.environ.get('CUDA_VISIBLE_DEVICES'), inference_only=True,
                       locked_validation_read=False, FINAL_read=False))
    judge = ScalarJudge(args.judge_config, batch_size=args.batch_size)
    data.private_write(output / 'LOADED.json', dict(loaded_unix=time.time(), pid=os.getpid(),
                       judge=args.name, judge_config=config_ref, selected_adapter=config['selected_adapter_root']))
    records, unique = [], {}
    for case in cases:
        tokens = [judge.token_count(case['scene'], case[side]) for side in ('good', 'contrast')]
        record = {key: case[key] for key in ('case_id', 'contest', 'kind', 'top_index')}
        record['tokens'] = tokens
        if max(tokens) > judge.max_length:
            record.update(status='SKIPPED_OVERLENGTH', good_score=None, contrast_score=None)
        elif data.normalize_caption(case['good']) == data.normalize_caption(case['contrast']):
            record.update(status='SKIPPED_IDENTICAL', good_score=None, contrast_score=None)
        else:
            record['status'] = 'PENDING'
            for side in ('good', 'contrast'):
                unique.setdefault((case['scene'], case[side]), None)
        records.append(record)
    keys = list(unique)
    for start in range(0, len(keys), args.batch_size):
        batch = keys[start:start + args.batch_size]
        values = judge.score([dict(scene=scene, caption=caption) for scene, caption in batch])
        unique.update(zip(batch, values))
        print(json.dumps(dict(judge=args.name, scored=min(start + len(batch), len(keys)),
                              total=len(keys), elapsed_seconds=round(time.time() - started, 2))), flush=True)
    for case, record in zip(cases, records):
        if record['status'] == 'PENDING':
            record.update(status='SCORED', good_score=unique[(case['scene'], case['good'])],
                          contrast_score=unique[(case['scene'], case['contrast'])])
    report = dict(schema='R207_CONSTRUCTED_CONTRAST_V1', judge=args.name, judge_config=config_ref,
                  private_cases_sha256=private_ref['sha256'], case_ids_sha256=data.digest([row['case_id'] for row in records]),
                  seed=args.seed, top_per_contest=args.top, contests=len(contests),
                  started_unix=started, completed_unix=time.time(), elapsed_seconds=time.time() - started,
                  locked_validation_read=False, FINAL_read=False, fitting_contests_excluded=True,
                  held_from_fitting_not_fresh_from_development_selection=True,
                  claim='DEVELOPMENT_DIAGNOSTIC_NOT_HUMAN_VALIDATION_OR_CALIBRATED_HUMOR',
                  score_semantics='RAW_SCALAR_BT_NOT_VOTE_PROBABILITY',
                  corpus_manifest_sha256=manifest_ref['sha256'], source_sha256={
                      name: data.file_ref(Path(name).resolve())['sha256'] for name in
                      ('gpu/ny_caption_scalar_judge.py', 'gpu/ny_caption_contrast.py')},
                  records=records, **summarize(records))
    data.private_write(output / 'REPORT.json', report)
    print(json.dumps(dict(judge=args.name, complete=True, by_type=report['by_type'])), flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--judge-config', required=True)
    parser.add_argument('--name', required=True)
    parser.add_argument('--output', required=True)
    parser.add_argument('--contests', type=int, default=20)
    parser.add_argument('--top', type=int, default=5)
    parser.add_argument('--seed', type=int, default=207)
    parser.add_argument('--batch-size', type=int, default=8)
    args = parser.parse_args()
    run(args)


if __name__ == '__main__':
    main()
