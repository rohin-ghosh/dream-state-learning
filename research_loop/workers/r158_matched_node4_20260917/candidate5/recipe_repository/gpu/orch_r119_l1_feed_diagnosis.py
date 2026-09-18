"""Bounded read-only audit of current L1 captures; never author reviews or admit."""

import argparse
from collections import Counter
import hashlib
import json
import os
from pathlib import Path
import time


def read(path):
    return json.loads(Path(path).read_text())


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def classify(row, task, reference, call_sha, recomputed=None):
    reasons = []
    native_train_self = (row.get('split') == 'TRAIN' and row.get('parent_calls') == 0
                         and not row.get('teacher_or_l2', False)
                         and row.get('source_label') == 'R109_SELF_GENERATED_FUNCTIONAL')
    math_supported = row.get('family') == 'math' and task is not None
    complete = bool(row['response'].get('terminal') and not row['response'].get('truncated'))
    correct = bool(math_supported and recomputed and recomputed.get('correct') is True)
    target_sha = hashlib.sha256(row['response']['raw'].encode()).hexdigest()
    duplicate_task = row.get('source_task_id') in reference['eligible_task_ids']
    duplicate_target = target_sha in reference['eligible_target_hashes'] + reference['historical_target_hashes']
    excluded = bool(task and (task['id'] in reference['excluded_ids']
                              or task['question_sha256'] in reference['excluded_question_hashes']))
    reviewed = call_sha in reference['bound_review_call_hashes']
    expected_fields = dict(source_archive_sha256=reference['legacy_plan']['supplement_archive_sha256'],
                           original_environment_archive_sha256=reference['legacy_plan']['original_source_archive_sha256'],
                           prompt_policy_sha256=reference['legacy_plan']['policy_sha256'],
                           source_state_sha256=reference['legacy_plan']['generation_seed_unchanged'],
                           source_tasks_sha256=reference['tasks_sha256'])
    drift = [key for key, value in expected_fields.items() if row.get(key) != value]
    checks = [('not_train_self', not native_train_self), ('unsupported_family_for_existing_feed', not math_supported),
              ('nonterminal_or_truncated', not complete), ('math_outcome_not_correct', math_supported and not correct),
              ('already_admitted_source_task', duplicate_task), ('duplicate_existing_target', duplicate_target),
              ('excluded_train_identity', excluded), ('missing_bound_author_review', not reviewed),
              ('legacy_source_binding_mismatch', bool(drift))]
    reasons.extend(name for name, failed in checks if failed)
    return dict(family=row.get('family'), stage=row.get('stage'), condition=row.get('condition'),
                native_train_self=native_train_self, math_supported=math_supported,
                terminal_untruncated=complete, math_native_correct=correct,
                outcome_matches_native_recompute=(row.get('outcome', {}).get('correct') == correct) if math_supported else None,
                duplicate_task=duplicate_task, duplicate_target=duplicate_target, excluded=excluded,
                bound_review_exists=reviewed, source_binding_drift=drift,
                quality_screen_candidate=bool(native_train_self and math_supported and complete and correct
                                              and not duplicate_task and not duplicate_target and not excluded),
                descriptive_persistence=bool(row.get('descriptive_response_metrics', {}).get('persistence')),
                cap_hit=bool(row.get('descriptive_response_metrics', {}).get('cap_hit')),
                review_required=True, admitted=False, reasons=reasons,
                target_sha256=target_sha, source_task_id=row.get('source_task_id'))


def processes():
    roles = {'orch_r109_l1_feed.py': 'legacy_feed_supervisor', 'gpu.orch_r109_l1_feed': 'legacy_feed_supervisor',
             'orch_r109_l1_feed_append.py': 'append_publisher', 'gpu.orch_r109_l1_feed_append': 'append_publisher',
             'orch_r109_l1_feed_status.py': 'read_only_status', 'gpu.orch_r109_l1_feed_status': 'read_only_status',
             'orch_r119_l1_resume.py': 'fixed_cohort_continuation'}
    results = []
    for directory in Path('/proc').iterdir():
        if not directory.name.isdigit():
            continue
        try:
            if directory.stat().st_uid != os.getuid():
                continue
            raw = (directory/'cmdline').read_bytes()
            arguments = raw.decode(errors='replace').split('\0')
            matches = {roles.get(argument) or roles.get(Path(argument).name) for argument in arguments}
            matches.discard(None)
            if not matches:
                continue
            fields = (directory/'stat').read_text().rsplit(')',1)[1].split()
            results.append(dict(pid=int(directory.name), uid=directory.stat().st_uid,
                                start_ticks=fields[19], state=fields[0], roles=sorted(matches),
                                argv_sha256=hashlib.sha256(raw).hexdigest(),
                                phase=[value for value in ('supervise','train','readout','status','publish','prepare') if value in arguments]))
        except (FileNotFoundError, PermissionError, ProcessLookupError):
            continue
    return results


def audit(root, destination, reference_path, count):
    import orch_r109_l1_feed as feed
    from organism_v6 import orch_rich_hot_node2 as math_source
    reference = read(reference_path)
    assert sha(feed.__file__) == reference['feed_source_sha256']
    assert sha(feed.experience.__file__) == reference['experience_source_sha256']
    config = read(root/'FORKS.json')
    origin = Path(config['origin_view'])
    assert sha(origin/'TASKS.json') == reference['tasks_sha256']
    tasks = {task['id']:task for task in read(origin/'TASKS.json')['math']['tasks']}
    paths = []
    for index in config['lanes']:
        if config['node'] == 'ovx' and index == 7:
            continue
        paths.extend((root/f'gpu{index}').glob('segment*/gpu*/CALL_[0-9]*.json'))
    selection = sorted(paths, key=lambda path: (path.stat().st_mtime_ns, str(path)), reverse=True)[:count]
    assert len(selection) == count
    results = []
    for path in selection:
        row = read(path)
        task = tasks.get(row.get('source_task_id')) if row['family'] == 'math' else None
        recomputed = math_source.outcome(task, row['response']) if task is not None else None
        result = classify(row, task, reference, sha(path), recomputed)
        try:
            feed.source_gate(dict(path=str(path)), row, task, reference['legacy_plan'], reference['tasks_sha256'])
            error = 'UNEXPECTED_PASS_WITHOUT_REVIEW'
        except (ValueError, AssertionError, KeyError) as failure:
            error = str(failure) or type(failure).__name__
        result.update(path=str(path), call_sha256=sha(path), finished_unix=row['finished_unix'],
                      diagnostic_legacy_source_gate=error, diagnostic_not_historical_rejection=True)
        results.append(result)
    destination.mkdir(exist_ok=False)
    (destination/'ROW_DIAGNOSTICS.json').write_text(json.dumps(results,sort_keys=True,indent=2))
    funnel = {}
    survivors = results
    for name, predicate in [('captured_responses', lambda row:True), ('train_self',lambda row:row['native_train_self']),
                           ('supported_math',lambda row:row['math_supported']),
                           ('terminal_untruncated',lambda row:row['terminal_untruncated']),
                           ('native_correct',lambda row:row['math_native_correct']),
                           ('not_excluded',lambda row:not row['excluded']),
                           ('new_source_task',lambda row:not row['duplicate_task']),
                           ('new_target',lambda row:not row['duplicate_target']),
                           ('bound_review_present',lambda row:row['bound_review_exists'])]:
        survivors = [row for row in survivors if predicate(row)]
        funnel[name] = len(survivors)
    compact = dict(schema='R119_L1_FEED_DIAGNOSIS_V1', node=config['node'], observed_unix=time.time(),
                   sample_count=len(results),sample_method='Newest immutable complete CALL files by filesystem mtime; fixed per-node quota, not outcome-selected; released ovx7 excluded',
                   newest_finished_unix=max(row['finished_unix'] for row in results),oldest_finished_unix=min(row['finished_unix'] for row in results),
                   funnel=funnel,reason_counts=dict(Counter(reason for row in results for reason in row['reasons'])),
                   families=dict(Counter(row['family'] for row in results)),
                   source_drift_counts=dict(Counter(field for row in results for field in row['source_binding_drift'])),
                   diagnostic_source_gate_counts=dict(Counter(row['diagnostic_legacy_source_gate'] for row in results)),
                   persistence_count=sum(row['descriptive_persistence'] for row in results),cap_hits=sum(row['cap_hit'] for row in results),
                   native_outcome_mismatches=sum(row['outcome_matches_native_recompute'] is False for row in results),
                   observed_processes=processes(),row_diagnostics_sha256=sha(destination/'ROW_DIAGNOSTICS.json'),
                   native_row_diagnostics=str(destination/'ROW_DIAGNOSTICS.json'),reference_sha256=sha(reference_path),
                   source_sha256=sha(__file__),feed_source_sha256=sha(feed.__file__),experience_source_sha256=sha(feed.experience.__file__),
                   admissions=0,training_mutations=0,author_reviews_created=0,held_or_final_content_read=False)
    (destination/'COMPACT.json').write_text(json.dumps(compact,sort_keys=True,indent=2))
    print(json.dumps(compact))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',type=Path,required=True)
    parser.add_argument('--destination',type=Path,required=True)
    parser.add_argument('--reference',type=Path,required=True)
    parser.add_argument('--count',type=int,required=True)
    options = parser.parse_args()
    assert 0 < options.count <= 100
    audit(options.root,options.destination,options.reference,options.count)
