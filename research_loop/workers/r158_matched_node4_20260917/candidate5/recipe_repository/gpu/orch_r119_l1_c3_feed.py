"""Prospective, explicitly registered R119 self-TRAIN append; no automatic reviews."""

import argparse
from copy import deepcopy
from dataclasses import asdict
import hashlib
import json
import os
from pathlib import Path
import time

try:
    import orch_r109_l1_feed as feed
    from orch_r109_l1_feed_append import validate_extension
except ImportError:
    from gpu import orch_r109_l1_feed as feed
    from gpu.orch_r109_l1_feed_append import validate_extension

read, sha, write, require = feed.read, feed.sha, feed.write, feed.require
REGISTRATION = 'R119_SELF_GENERATED_TRAIN_FULL15460'


def source_gate(registration, review, row, task):
    root = Path(registration['root'])
    path = root / review['path']
    require(not Path(review['path']).is_absolute() and '..' not in Path(review['path']).parts
            and path.resolve().is_relative_to(root.resolve()), 'registered_capture_path')
    require(registration['source_registration_id'] == REGISTRATION
            and registration['node'] == 'ovx', 'explicit_R119_self_TRAIN_registration')
    for field, expected in registration['row_bindings'].items():
        require(row[field] == expected, 'registered_' + field)
    feed.experience.review_gate(review, row, task)
    require(not row.get('teacher_or_l2', False), 'no_silent_parented_source_mixing')


def bounded_reviews(reviews):
    require(len(reviews) <= 3, 'at_most_three_reviewed_candidates')
    require(len({row['source_task_id'] for row in reviews}) == len(reviews), 'distinct_reviewed_tasks')


def verify(root):
    manifest = read(root / 'MANIFEST.json')
    require(sha(__file__) == manifest['source_sha256'], 'frozen_C3_source')
    for path, expected in manifest['native_pins'].items():
        require(sha(path) == expected, 'native_pin:' + Path(path).name)
    require(sha(root / 'REVIEWS.json') == manifest['reviews_sha256'], 'bound_author_reviews')
    registration = read(root / 'SOURCE_REGISTRATION.json')
    require(sha(root / 'SOURCE_REGISTRATION.json') == manifest['registration_sha256'], 'bound_registration')
    from gpu import orch_r109_l1_train as trainer
    metadata = trainer.storage.verify_checkpoint(Path(registration['checkpoint']))['metadata']
    require(metadata['update'] == 15460 and metadata['adapter']['state_sha256'] ==
            registration['row_bindings']['source_state_sha256'], 'registered_seed_not_reset')
    parent = Path(manifest['parent'])
    prepared, plan = read(parent / 'PREPARED.json'), read(parent / 'PLAN.json')
    require(sha(parent / 'ENCODED.json') == prepared['encoded_sha256']
            and sha(parent / 'ELIGIBLE.json') == plan['eligible_sha256'], 'unchanged_parent_cohort')
    require(plan['seed_update'] == plan['original_schedule_seed_update'] == 9444, 'original_schedule')
    return manifest, registration, parent


def prepare(root):
    require(os.environ.get('CUDA_VISIBLE_DEVICES') == '', 'CPU_only_prepare')
    manifest, registration, parent = verify(root)
    from gpu import orch_r109_l1_train as trainer
    from gpu.orch_combined_l1_continual_content import encode_rows
    from organism_v6 import orch_rich_hot_node2 as math_source
    from organism_v6 import orch_r107_capability as capability
    origin = Path(manifest['origin'])
    document = read(registration['tasks_path'])
    tasks = {task['id']: task for task in document['math']['tasks']}
    excluded_ids = set(document['math']['excluded_ids'])
    excluded_questions = set(document['math']['excluded_question_hashes'])
    prepared, plan = read(parent / 'PREPARED.json'), read(parent / 'PLAN.json')
    held = read(parent / 'input/prior/LEGACY_READOUT.json')['held']
    require(feed.digest(held) == prepared['held_behavior_sha256'] and
            capability.digest(capability.tasks()) == prepared['fixed32_suite_sha256'], 'unchanged_sealed_suites')
    previous_rows = read(parent / 'ELIGIBLE.json')['rows']
    previous_encoded = read(parent / 'ENCODED.json')
    require(len(previous_rows) == 19, 'exact_old19')
    eligible, encoded = deepcopy(previous_rows), deepcopy(previous_encoded)
    seen_tasks = {row['source_task_id'] for row in eligible}
    seen_targets = {row['target_sha256'] for row in eligible}
    historical = {row.get('target_sha256') for row in read(origin / 'input/prior/CORPORA/000013.json')['rows']}
    reviews = read(root / 'REVIEWS.json')['reviews']
    bounded_reviews(reviews)
    tokenizer = trainer.native.source.native.load_local_tokenizer(plan['model_dir'])
    decisions, additions = [], []
    for review in reviews:
        path = Path(registration['root']) / review['path']
        try:
            require(sha(path) == review['call_sha256'], 'immutable_capture_hash')
            row = read(path)
            task = tasks[row['source_task_id']]
            source_gate(registration, review, row, task)
            require(math_source.outcome(task, row['response'])['correct'] is True, 'native_oracle_recomputed')
            require(task['id'] not in excluded_ids and task['question_sha256'] not in excluded_questions,
                    'held_task_and_question_excluded')
            text = json.dumps(row['messages'], ensure_ascii=False) + row['response']['raw']
            require(all(item['id'] not in text and item['prompt'] not in text for item in capability.tasks())
                    and all(item['event'] not in text for item in held['events']), 'sealed_content_excluded')
            target = row['response']['raw']
            target_sha = hashlib.sha256(target.encode()).hexdigest()
            require(task['id'] not in seen_tasks and target_sha not in seen_targets | historical,
                    'new_distinct_reviewed_target')
            item = encode_rows([dict(student_prefix=row['messages'], target=target)], tokenizer)[0]
            require(tuple(row['response']['token_ids']) == tuple(item.target_ids)
                    and len(item.input_ids) <= 2048, 'exact_native_tokens_untruncated_student_prefix')
            admitted = dict(source_label=feed.experience.SOURCE_LABEL, split='TRAIN', task_id=row['task_id'],
                contamination_family=task['question_sha256'], functional_verdict='PASS', grounding_verdict='PASS',
                source_archive_sha256=row['source_archive_sha256'], source_call_sha256=sha(path),
                annotation_sha256=feed.digest(review), target_actor='CHILD', parent_text_masked=True,
                target=target, target_sha256=target_sha, native_token_ids=row['response']['token_ids'],
                student_prefix=row['messages'], prefix_sha256=feed.digest(row['messages']),
                source_task_id=task['id'], native_source_path=str(path), source_state_sha256=row['source_state_sha256'],
                review=review, original_capture_unchanged=True, teacher_or_l2=False,
                source_registration_id=REGISTRATION, source_registration_sha256=sha(root / 'SOURCE_REGISTRATION.json'))
            trainer.policy.validate_eligible(admitted, excluded_ids, excluded_questions)
            eligible.append(admitted)
            encoded['eligible'].append(asdict(item))
            seen_tasks.add(task['id'])
            seen_targets.add(target_sha)
            additions.append(dict(source_task_id=task['id'], target_sha256=target_sha,
                call_sha256=sha(path), native_tokens=len(item.target_ids), property=review['property']))
            decisions.append(dict(path=review['path'], call_sha256=sha(path), status='ADMITTED',
                reason='AUTHOR_REVIEWED_TASK_CONSTRAINT_USED', admitted_unix=time.time()))
        except (AssertionError, ValueError, KeyError) as error:
            decisions.append(dict(path=review['path'], call_sha256=review['call_sha256'], status='REJECTED', reason=str(error)))
    write(root / 'ADMISSION_DECISIONS.json', dict(decisions=decisions, newly_admitted=len(additions),
        observed_unix=time.time(), consumer_adopted=False, persistence_claim=False, source_registration_id=REGISTRATION))
    if not additions:
        print(json.dumps(dict(status='NO_ELIGIBLE_APPEND_KEEP_OLD_COHORT',newly_admitted=0)))
        return
    validate_extension(previous_rows, eligible, previous_encoded, encoded)
    folder = root / 'cohort'
    folder.mkdir(exist_ok=False)
    write(folder / 'ELIGIBLE.json', dict(rows=eligible, newly_admitted=additions,
        source_registration_id=REGISTRATION, previous_eligible_sha256=sha(parent / 'ELIGIBLE.json')))
    write(folder / 'ENCODED.json', encoded)
    (folder / 'input/prior').mkdir(parents=True)
    (folder / 'input/prior/LEGACY_READOUT.json').symlink_to(parent / 'input/prior/LEGACY_READOUT.json')
    write(folder / 'PLAN.json', dict(plan, cohort_id='R119_EXPERIENCE_C3_B003',
        eligible_sha256=sha(folder / 'ELIGIBLE.json'), previous_cohort_plan_sha256=sha(parent / 'PLAN.json'),
        cohort_source_sha256=sha(__file__), cohort_archive_sha256=sha(root / 'MANIFEST.json'),
        reviews_sha256=sha(root / 'REVIEWS.json'), registration_sha256=sha(root / 'SOURCE_REGISTRATION.json'),
        batch_number=3, reset=False, published_at_segment_boundary_only=True))
    write(folder / 'PREPARED.json', dict(prepared, plan_sha256=sha(folder / 'PLAN.json'),
        encoded_sha256=sha(folder / 'ENCODED.json'), eligible_sha256=sha(folder / 'ELIGIBLE.json'),
        counts={name:len(rows) for name,rows in encoded.items()}, newly_admitted=len(additions),
        eligible_unique_tasks=len(seen_tasks), all_prefix_masked=True))
    write(root / 'PUBLISHED.json', dict(status='IMMUTABLE_COHORT_PUBLISHED_NOT_ADOPTED',
        observed_unix=time.time(), new_rows=len(additions), total_rows=len(eligible),
        cohort=str(folder), prepared_sha256=sha(folder / 'PREPARED.json'),
        source_registration_sha256=sha(root / 'SOURCE_REGISTRATION.json'), consumer_adopted=False,
        old19_digest=feed.digest(previous_rows), old19_encoded_digest=feed.digest(previous_encoded['eligible']),
        unchanged_bucket_digests={key:feed.digest(value) for key,value in previous_encoded.items() if key!='eligible'},
        additions=additions, raw_node_only=True))
    print(json.dumps(read(root / 'PUBLISHED.json')))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, required=True)
    options = parser.parse_args()
    prepare(options.root)
