"""Reduce only this frozen replication's native bytes and explicit reviews."""

import argparse
import json
from pathlib import Path

from gpu import astra_portable_actor_bundle as portable
from organism_v6 import orch_math_replication as policy


def collect_native(document, tasks_path, native_roots):
    policy.validate_cohort(document)
    if len(native_roots) != 3 or len({root.resolve() for root in native_roots}) != 3:
        raise ValueError('three_distinct_frozen_shards_required')
    rows, provenance = [], []
    for shard, root in enumerate(native_roots):
        request = json.loads((root / 'REQUEST.json').read_text())
        if (request['tasks_sha256'] != policy.sha256(tasks_path)
                or request['arguments']['shard'] != shard
                or request['manifest_sha256'] != policy.MANIFEST_SHA256
                or request['driver_sha256'] != policy.sha256(Path(__file__).with_name('orch_math_replication_native.py'))
                or request['policy_sha256'] != policy.sha256(Path(policy.__file__))
                or request['fits'] != 0 or request['updates'] != 0):
            raise ValueError('native_shard_binding_mismatch')
        row_paths = sorted(root.glob('CALL_*.json'))
        expected_names = [f'CALL_{position:04d}.json' for position in range(1, len(row_paths) + 1)]
        if [path.name for path in row_paths] != expected_names:
            raise ValueError('noncontiguous_native_calls')
        shard_tasks = {task['id'] for position, task in enumerate(document['tasks']) if position % 3 == shard}
        shard_rows = [json.loads(path.read_text()) for path in row_paths]
        if any(row['task_id'] not in shard_tasks for row in shard_rows):
            raise ValueError('task_moved_across_shards')
        complete_path = root / 'COMPLETE.json'
        complete = complete_path.exists() and not (root / 'FAILED.json').exists()
        if complete:
            terminal = json.loads(complete_path.read_text())
            ready = json.loads((root / 'ACTOR_READY.json').read_text())
            if (terminal['status'] != 'COMPLETE' or terminal['model_calls'] != len(shard_rows)
                    or terminal['adapter_state'] != portable.PARENT_STATE
                    or ready['adapter_state'] != portable.PARENT_STATE
                    or any(terminal.get(key) != value or ready.get(key) != value for key, value in request.items())
                    or terminal['frozen_base_unchanged'] is not True):
                raise ValueError('terminal_provenance_mismatch')
        rows.extend(shard_rows)
        evidence = [root / 'REQUEST.json', *row_paths]
        evidence.extend(path for path in (complete_path, root / 'FAILED.json', root / 'ACTOR_READY.json') if path.exists())
        provenance.append(dict(shard=shard, complete=complete,
                               files={path.name: policy.sha256(path) for path in evidence}))
    return rows, provenance


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--tasks', type=Path, required=True)
    parser.add_argument('--native-roots', type=Path, nargs=3, required=True)
    parser.add_argument('--reviews', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    options = parser.parse_args()
    document = json.loads(options.tasks.read_text())
    rows, provenance = collect_native(document, options.tasks, options.native_roots)
    summary = policy.reduce_native(document, rows)
    task_map = {task['id']: task for task in document['tasks']}
    candidates = [row for row in rows if row['candidate']]
    review_queue = [dict(question=task_map[row['task_id']]['question'], gold=row['gold'],
                        task_id=row['task_id'], kind=row['kind'], target=row['target'],
                        target_sha256=row['target_sha256'], student_prefix=row['student_prefix'],
                        full_messages=row['call']['messages']) for row in candidates]
    decisions = json.loads(options.reviews.read_text()) if options.reviews else []
    decision_map = {(item['task_id'], item['kind']): item for item in decisions}
    candidate_keys = {(row['task_id'], row['kind']) for row in candidates}
    if len(decision_map) != len(decisions) or set(decision_map) - candidate_keys:
        raise ValueError('duplicate_or_non_candidate_review')
    reviewed = [policy.review_row(row, decision_map[(row['task_id'], row['kind'])])
                for row in candidates if (row['task_id'], row['kind']) in decision_map]
    passes = [row for row in reviewed if row['semantic_status'] == 'PASS']
    eligible = [row for row in passes if summary['families'][row['family']]['gap_eligible']]
    summary['native_provenance'] = provenance
    summary['all_shards_complete'] = all(item['complete'] for item in provenance)
    summary['semantic'] = dict(candidate_rows=len(candidates), reviewed_rows=len(reviewed),
                              pending_rows=len(candidates) - len(reviewed), pass_rows=len(passes),
                              pass_tasks=len({row['task_id'] for row in passes}),
                              eligible_pass_rows=len(eligible),
                              eligible_pass_tasks=len({row['task_id'] for row in eligible}),
                              fail_rows=sum(row['semantic_status'] == 'FAIL' for row in reviewed),
                              unresolved_rows=sum(row['semantic_status'] == 'UNRESOLVED' for row in reviewed))
    summary['strong_support'] = bool(summary['all_shards_complete'] and summary['primary']['complete']
        and summary['primary']['difference'] > 0 and summary['primary']['exact_mcnemar_two_sided'] <= 0.05
        and len(eligible) >= 8 and len({row['task_id'] for row in eligible}) >= 4
        and not summary['semantic']['pending_rows'] and not summary['semantic']['unresolved_rows']
        and not summary['unresolved_numeric_gold'])
    summary['analysis_status'] = ('INCOMPLETE_NATIVE_NOT_SCIENTIFIC_NULL' if not summary['all_shards_complete']
        else 'SEMANTIC_REVIEW_PENDING' if summary['semantic']['pending_rows'] else 'INDEPENDENT_REDUCTION_COMPLETE')
    options.output.mkdir(parents=True, exist_ok=False)
    policy.write(options.output / 'INDEPENDENT_REDUCTION.json', summary)
    policy.write(options.output / 'FULLTEXT_REVIEW_QUEUE.json', review_queue)
    policy.write(options.output / 'BOUND_SEMANTIC_REVIEWS.json', reviewed)
    policy.write(options.output / 'REDUCTION_PROVENANCE.json', dict(
        tasks_sha256=policy.sha256(options.tasks), reducer_sha256=policy.sha256(Path(__file__)),
        policy_sha256=policy.sha256(Path(policy.__file__)),
        reviews_sha256=policy.sha256(options.reviews) if options.reviews else None))
    print(json.dumps(summary, sort_keys=True))


if __name__ == '__main__':
    main()
