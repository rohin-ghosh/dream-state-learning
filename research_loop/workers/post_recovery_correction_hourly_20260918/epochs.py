"""Per-life source windows and literal ACT exposure, never semantic uptake."""

import hashlib
import json


def source_epoch(label, binding):
    keys = ('journal_id', 'pid', 'start_ticks', 'source', 'root', 'guard_sha256',
        'loaded_index', 'loaded_sha256', 'owner_receipt_sha256', 'boot_id', 'source_manifest_sha256')
    values = dict(label=label, **{key: binding[key] for key in keys})
    return hashlib.sha256(json.dumps(values, sort_keys=True).encode()).hexdigest()


def act_exposure(evidence, audit, queue, epoch_id):
    rows = []
    for frame in audit.frames(evidence):
        if frame['stage'] != 'ACT':
            continue
        parents = [dict(event_id=event['event_id'], source_sha256=event['source_sha256'],
            body_sha256=audit.text_sha(event['text']), exact_parent_text_in_ACT=True)
            for event in frame['request']['external'] if event['actor'] == 'parent']
        rows.append(dict(source_epoch_id=epoch_id, output=queue.output_ref(frame),
            parents=parents, parent_count=len(parents), masked_request=True,
            semantic_uptake=None, retention_effect=None))
    return dict(acts=rows, actual_ACTs=len(rows), ACTs_with_exact_parent_text=sum(bool(row['parents']) for row in rows),
        exactness='Original TRAIN reader verifies whole literal parent body in user message, with exact metadata for structured render.',
        interpretation='Exposure only. Parent inputs are not automatically classified as corrections; retention is not uptake.')


def validate_cursor(cursor, epoch_id):
    if cursor.get('source_epoch_id') != epoch_id:
        raise ValueError('review_cursor_source_epoch_mismatch')


def publish_rows(rows):
    return [dict(label=row['label'], source_epoch_id=row.get('source_epoch_id'),
        status=row['status'], actual_window=row.get('current_window'),
        current_identity=row.get('current_identity'), source_horizon_utc=row.get('source_horizon_utc'),
        retention_deployed=None, retention_epoch_status='NO_AUTHORITATIVE_DEPLOYMENT_RECEIPT_BOUND',
        retention_comparison='NOT_AVAILABLE_NO_DEPLOYED_AFTER_WINDOW',
        semantic_uptake='NOT_ADJUDICATED_IN_NEW_WINDOW', ACT_parent_exposure=row.get('ACT_parent_exposure'))
        for row in rows]
