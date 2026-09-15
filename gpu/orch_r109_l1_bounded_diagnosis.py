"""CPU-only bounded TRAIN capture audit; never admits rows or loads a model."""

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import re
import time


SEED = '121655d491bc55ba6bbd8eb732bc4f7a65215a07d3b6b2492f4fa623026f80f1'


def read(path):
    return json.loads(Path(path).read_text())


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def response_shape(row):
    text = row['response']['raw']
    final = re.search(r'(?im)^\s*FINAL:[^\n]*', text)
    try:
        parsed = json.loads(text.strip().splitlines()[-1])
        expression_json = isinstance(parsed, dict) and isinstance(parsed.get('expression'), str)
    except (ValueError, IndexError):
        expression_json = False
    metrics = row['descriptive_response_metrics']
    return dict(
        family=row['family'], stage=row['stage'],
        content_tokens=len(row['response']['token_ids']),
        expression_json=expression_json,
        math_pre_final_nonempty=bool(final and text[:final.start()].strip()),
        math_first_final_is_last=bool(final and not text[final.end():].strip()),
        marker_found=metrics['marker_found'],
        post_first_answer_child_tokens=metrics['post_first_answer_child_tokens'],
        persistence=metrics['persistence'], cap_hit=metrics['cap_hit'],
        alignment=metrics['native_marker_alignment_verified'],
        correct=row.get('outcome', {}).get('correct'),
        terminal=row['response']['terminal'], truncated=row['response']['truncated'],
    )


def audit(origin, node, output, window=96):
    if not 1 <= window <= 128 or node not in ('node1', 'node2'):
        raise ValueError('bounded_node_window')
    if output.exists() or output.resolve().is_relative_to(origin.resolve()):
        raise ValueError('new_external_audit_directory_required')
    generation = origin / 'generation_v3'
    plan = read(generation / 'PLAN.json')
    if plan['node'] != node or plan['generation_seed_unchanged'] != SEED:
        raise ValueError('exact_node_seed')
    tasks_sha = sha(origin / 'TASKS.json')
    lanes, examples, row_refs = [], [], []
    sample_keys = set()
    for index in plan['lanes']:
        directory = generation / f'gpu{index}'
        loaded = read(directory / 'LOADED.json')
        progress_bytes = (directory / 'PROGRESS.json').read_bytes()
        progress = json.loads(progress_bytes)
        if loaded['adapter']['state_sha256'] != SEED:
            raise ValueError('actual_LOADED_seed_mismatch')
        records = []
        for number in range(max(progress['inherited_calls'] + 1, progress['calls'] - window + 1), progress['calls'] + 1):
            path = directory / f'CALL_{number:06d}.json'
            row = read(path)
            if not (row['split'] == 'TRAIN' and row['parent_calls'] == 0
                    and row['source_state_sha256'] == SEED
                    and row['source_archive_sha256'] == plan['supplement_archive_sha256']
                    and row['original_environment_archive_sha256'] == plan['original_source_archive_sha256']
                    and row['prompt_policy_sha256'] == plan['policy_sha256']
                    and row['source_tasks_sha256'] == tasks_sha):
                raise ValueError('native_TRAIN_source_binding')
            shape = response_shape(row)
            ref = dict(path=str(path), sha256=sha(path), task_id=row['task_id'],
                       source_task_id=row['source_task_id'], condition=row['condition'],
                       verifier_error=row.get('outcome', {}).get('verifier', {}).get('error'),
                       prefix_plus_target_tokens=row['response']['prompt_tokens'] + len(row['response']['token_ids']),
                       **shape)
            row_refs.append(ref)
            records.append((row, ref))
            key = (row['family'], row['stage'])
            if key not in sample_keys and len(examples) < 8:
                examples.append(dict(reference=ref, messages=row['messages'], response=row['response']['raw']))
                sample_keys.add(key)
        drafts = {row['task_id']: row for row, ref in records if row['stage'] == 'draft'}
        pairs = []
        for row, ref in records:
            draft = drafts.get(row['task_id'])
            if row['stage'] != 'optional_opportunity' or draft is None:
                continue
            pairs.append(dict(task_id=row['task_id'], family=row['family'],
                              draft_correct=draft.get('outcome', {}).get('correct'),
                              continuation_correct=row.get('outcome', {}).get('correct'),
                              identical_text=draft['response']['raw'] == row['response']['raw']))
        lane = dict(index=index, condition=loaded['condition'], loaded_sha256=sha(directory / 'LOADED.json'),
                    seed=loaded['adapter']['state_sha256'], base=loaded['adapter']['base_sha256'],
                    progress_sha256=hashlib.sha256(progress_bytes).hexdigest(), sampled_end_call=progress['calls'],
                    sampled_rows=len(records), unique_source_ids=len({row['source_task_id'] for row, ref in records}),
                    family_stage=dict(Counter(row['family'] + ':' + row['stage'] for row, ref in records)),
                    metrics={key:sum(bool(ref[key]) for row, ref in records) for key in
                             ('expression_json', 'math_pre_final_nonempty', 'math_first_final_is_last',
                              'marker_found', 'persistence', 'cap_hit', 'alignment', 'terminal', 'truncated')},
                    maximum_post_tokens=max(ref['post_first_answer_child_tokens'] for row, ref in records),
                    code_errors=dict(Counter(ref['verifier_error'] or 'no_verifier_error_recorded'
                                     for row, ref in records if row['family'] == 'code')),
                    over_C2_2048=sum(ref['prefix_plus_target_tokens'] > 2048 for row, ref in records),
                    pair_count=len(pairs), pairs=pairs)
        lanes.append(lane)
    output.mkdir(parents=True)
    sample_path = output / 'NATIVE_TRAIN_SAMPLES.json'
    sample_path.write_text(json.dumps(examples, indent=2) + '\n')
    references_path = output / 'CAPTURE_REFERENCES.json'
    references_path.write_text(json.dumps(row_refs, indent=2) + '\n')
    feed = None
    if node == 'node2':
        eligible_path = origin / 'experience_feed_v1/versions/002/ELIGIBLE.json'
        eligible = read(eligible_path)['rows']
        seen = {row['source_task_id'] for row in eligible}
        sampled_math = [row for row in row_refs if row['family'] == 'math']
        feed = dict(eligible_sha256=sha(eligible_path), eligible_rows=len(eligible),
                    eligible_unique_tasks=len(seen), sampled_math_calls=len(sampled_math),
                    sampled_math_unique_tasks=len({row['source_task_id'] for row in sampled_math}),
                    sampled_math_already_eligible=sum(row['source_task_id'] in seen for row in sampled_math),
                    exact_native_sources={name:sha(origin / 'experience_feed_v1/source' / name)
                        for name in ('orch_r109_l1_feed.py', 'orch_r109_l1_experience.py')})
    summary = dict(schema='R109_BOUNDED_TRAIN_DIAGNOSIS_V1', node=node, observed_unix=time.time(),
                   window_per_lane=window, sampling='last completed calls at frozen per-lane PROGRESS counter; not population estimate',
                   origin=str(origin), generation_plan_sha256=sha(generation / 'PLAN.json'),
                   tasks_sha256=tasks_sha, original_archive_sha256=plan['original_source_archive_sha256'],
                   supplement_archive_sha256=plan['supplement_archive_sha256'],
                   runner_sha256=plan['runner_sha256'], policy_sha256=plan['policy_sha256'],
                   audit_source_sha256=sha(__file__), lanes=lanes, feed=feed,
                   sample_count=len(examples), native_samples=dict(path=str(sample_path), sha256=sha(sample_path)),
                   references=dict(path=str(references_path), sha256=sha(references_path)),
                   GPU_launched=False, live_files_changed=False, rows_admitted=0, FINAL_read=False)
    (output / 'COMPACT.json').write_text(json.dumps(summary, indent=2) + '\n')
    print(json.dumps(summary, sort_keys=True))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--origin', type=Path, required=True)
    parser.add_argument('--node', choices=('node1', 'node2'), required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--window', type=int, default=96)
    options = parser.parse_args()
    audit(options.origin, options.node, options.output, options.window)
