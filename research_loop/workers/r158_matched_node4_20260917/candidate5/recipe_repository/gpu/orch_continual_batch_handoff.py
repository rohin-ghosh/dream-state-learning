"""Truthful math_content_v2 wrappers; no review replay, relabeling or trainer reset."""

import json
from pathlib import Path
import time

from gpu import orch_continual_batch_publish as publisher
from organism_v6 import orch_continual_batch as policy


def wrap_row(row, batch_manifest_sha256):
    review = row.get('review')
    return dict(row=row, question_sha256=row['question_sha256'],
        source_archive_member=row['provenance']['raw_call_path'],
        eligibility=dict(policy='ROHIN98_BATCH_SAMPLED_AUTHOR_REVIEW_V2', eligible=True,
            admission_mode=policy.MODE, batch_manifest_sha256=batch_manifest_sha256,
            individual_reviewed=review is not None,
            individual_semantic_status=review['status'] if review else 'UNREVIEWED',
            content_axes={axis: review[axis] if review else None for axis in policy.QUALITY_AXES},
            target_sha256=row['target_sha256'], source_capture_sha256=row['provenance']['raw_call_sha256'],
            original_admitted=False, original_semantic_status=row['original_semantic_status'],
            first_person=review['first_person'] if review else None, generated_tokens=row['generated_tokens'],
            register_is_gate=False, length_is_quality_gate=False, independent_review=False,
            semantic_branching_measured=review is not None, parenting_experience=False,
            instruction_regime=row['provenance'].get('instruction_regime', 'UNKNOWN'),
            instruction_amount_tokens=row['provenance'].get('instruction_amount_tokens'),
            branch_metrics=review.get('branch_metrics') if review else dict(measurement_status='UNKNOWN',
                semantic_distinct_approaches_considered=None, semantic_distinct_approaches_pursued=None,
                repetition_failure=None),
            mechanical_branch_counts=row['provenance'].get('mechanical_branch_counts'),
            self_reported_branch_counts=row['provenance'].get('self_reported_branch_counts')),
        gold_review=dict(status=review['gold_status'], independent_answer=review['independent_answer'],
                         reason=review['gold_reason']) if review else None)


def emit(batch):
    source_manifest = publisher.read(batch / 'MANIFEST.json')
    policy.require(source_manifest['admission_mode'] == policy.MODE and source_manifest['batch_author_accepted'], 'accepted_sampled_batch_required')
    rows = publisher.read(batch / source_manifest['rows_path'])
    policy.require(publisher.sha(batch / source_manifest['rows_path']) == source_manifest['rows_sha256'], 'bound_rows_required')
    old_root = publisher.REPO / 'research_notes/analysis/orch_continual_ingest_20260915/batch_math_content_readmission473'
    old_manifest = publisher.read(old_root / 'MANIFEST.json')
    old_rows = publisher.read(old_root / old_manifest['rows_path'])
    policy.require(publisher.sha(old_root / old_manifest['rows_path']) == old_manifest['rows_sha256'], 'old473_rows_binding')
    old_hashes = {row['eligibility']['target_sha256'] for row in old_rows}
    overlap = old_hashes & {row['target_sha256'] for row in rows}
    destination = batch.with_name(batch.name + '_ingest_v2')
    destination.mkdir()
    publisher.write(destination / 'OLD473_DEDUP_CHECK.json', dict(manifest_sha256=publisher.sha(old_root / 'MANIFEST.json'),
        rows_sha256=old_manifest['rows_sha256'], overlapping_target_sha256s=sorted(overlap), old_labels_unchanged=True))
    wrappers = [wrap_row(row, publisher.sha(batch / 'MANIFEST.json')) for row in rows if row['target_sha256'] not in overlap]
    policy.require(wrappers, 'all_targets_preexisting')
    publisher.write(destination / 'ROWS.json', wrappers)
    manifest = dict(source_manifest, batch_id=source_manifest['batch_id'] + '_content_v2',
        encoding='math_content_v2', rows_path='ROWS.json', rows_sha256=publisher.sha(destination / 'ROWS.json'),
        row_count=len(wrappers), target_sha256s=[row['eligibility']['target_sha256'] for row in wrappers],
        source_purpose='L1_EXTERNAL_GENERATION', parenting_experience=False, generation_not_parenting=True,
        underlying_registered_purpose=policy.PURPOSE, original_rows_and_labels_unchanged=True,
        wrapper_policy='ROHIN98_BATCH_SAMPLED_AUTHOR_REVIEW_V2',
        individual_semantic_status='SAMPLED_PASS_UNSAMPLED_UNREVIEWED',
        source_batch_manifest_path=str(batch / 'MANIFEST.json'), source_batch_manifest_sha256=publisher.sha(batch / 'MANIFEST.json'),
        source_native_archive_path=str(batch / 'SOURCE_SNAPSHOT.tar.gz'),
        sampled_review_path=str(batch / 'SAMPLED_REVIEWS.json'), sample_registration_path=str(batch / 'SAMPLE_REGISTRATION.json'),
        exclusions_path=str(batch / 'EXCLUSIONS.json'), source_registry_path=str(batch / 'SOURCE_REGISTRY.json'),
        metrics_path=str(batch / 'METRICS.json'), provider_usage_path=str(batch / 'PROVIDER_USAGE.json'),
        old473_deduplicated=True, trainer_ingested=False,
        consumer_requirement='batch-sampled branch must preserve individually UNREVIEWED rows; do not call them per-row content-certified')
    publisher.write(destination / 'MANIFEST.json', manifest)
    return destination / 'MANIFEST.json'


def main():
    root = publisher.ROOT
    deadline = publisher.read(root / 'WATCH_LIFETIME.json')['deadline_unix']
    handoffs = []
    while time.time() < deadline:
        for batch in sorted(root.glob('batch_[0-9][0-9][0-9]')):
            destination = batch.with_name(batch.name + '_ingest_v2')
            if (batch / 'MANIFEST.json').exists() and not destination.exists():
                path = emit(batch)
                handoffs.append(dict(path=str(path), sha256=publisher.sha(path)))
                publisher.write(root / 'INGEST_HANDOFFS.json', dict(manifests=handoffs, training_ingestion_not_asserted=True))
        if (root / 'WATCH_TERMINAL.json').exists():
            break
        time.sleep(2)


if __name__ == '__main__':
    main()
