"""Read-only receipt accounting; never changes scoring or LEARN eligibility."""

import datetime
import hashlib
from pathlib import Path
import json


REVIEW_CLASSES = ('literal_caption_attempt', 'commentary_or_program', 'uncertain')
COUNT_FIELDS = ('scored', 'accepted', 'new_pixels', 'judge_rejected', 'cached',
                'format_fault', 'no_caption_act', 'routing_ambiguity', 'parsed',
                'source_bound_scored_strings', 'literal_caption_attempt_reviewed',
                'commentary_or_program_reviewed', 'uncertain_reviewed',
                'unreviewed_scored_strings')


def current_base_roots(phase, original, shared):
    phase, original, shared = Path(phase), Path(original), Path(shared)
    pointer = phase / 'CURRENT.json'
    if pointer.exists():
        document = json.loads(pointer.read_bytes())
        current, scorer = Path(document['root']), Path(document['scorer_root'])
        if not current.is_relative_to(phase) or not scorer.is_relative_to(phase):
            raise ValueError('current_pointer_outside_owned_phase')
        loaded = json.loads((current / 'LOADED.json').read_bytes())
        if loaded['pid'] != document['loaded']['pid']:
            raise ValueError('current_pointer_loaded_mismatch')
        return current, scorer, current / 'LOADED.json'
    if (phase / 'LOADED.json').exists():
        return phase, shared, phase / 'LOADED.json'
    return original, original / 'scorer', original / 'BASE_LOADED.json'


def scored_sources(document):
    report = document['report']
    sources = report.get('caption_sources', [])
    output = []
    for entry in report.get('feedback', []):
        result = entry.get('result', {})
        if not result.get('ok') or type(result.get('accepted')) is not bool or result.get('replayed'):
            continue
        index = entry.get('caption_source_index')
        source = sources[index] if type(index) is int and 0 <= index < len(sources) else None
        verified, text_sha256, stage = False, None, None
        if source:
            stage = source.get('stage', 'ACT')
            raw = (document.get('salvaged_THINK') or {}).get('raw', '') if stage == 'THINK' else document.get('raw_act', '')
            start, end = source.get('start'), source.get('end')
            if type(start) is int and type(end) is int and 0 <= start < end <= len(raw):
                text_sha256 = hashlib.sha256(raw[start:end].encode()).hexdigest()
                verified = text_sha256 == source.get('text_sha256')
        output.append(dict(caption_source_index=index, text_sha256=text_sha256,
            exact_source_span_verified=verified, stage=stage,
            accepted=result['accepted'], new_pixel=result['accepted'] and result.get('status') == 'new_pixel'))
    return output


def apply_review(row, reviews):
    annotations = reviews.get(row['receipt_sha256'], {})
    row['source_bound_scored_strings'] = sum(item['exact_source_span_verified'] for item in row['scored_sources'])
    for label in REVIEW_CLASSES:
        row[label + '_reviewed'] = 0
    row['unreviewed_scored_strings'] = 0
    for item in row['scored_sources']:
        annotation = annotations.get(str(item['caption_source_index']))
        if annotation is None:
            row['unreviewed_scored_strings'] += 1
            item['literal_review'] = 'unreviewed'
            continue
        label = annotation['classification']
        if label not in REVIEW_CLASSES or not item['exact_source_span_verified'] or annotation['text_sha256'] != item['text_sha256']:
            raise ValueError('literal_review_must_bind_exact_saved_source')
        item['literal_review'] = label
        row[label + '_reviewed'] += 1
    if sum(row[label + '_reviewed'] for label in REVIEW_CLASSES) + row['unreviewed_scored_strings'] != row['scored']:
        raise ValueError('scored_review_denominator_mismatch')
    return row


def hourly_rows(rows, since_unix, until_unix):
    buckets, identifiers = {}, set()
    for row in rows:
        if not since_unix <= row['unix'] <= until_unix:
            continue
        identifier = row['origin_sha256']
        if identifier in identifiers:
            raise ValueError('duplicate_ACT_origin_in_count_window')
        identifiers.add(identifier)
        hour = datetime.datetime.fromtimestamp(row['unix'], datetime.timezone.utc).replace(minute=0, second=0, microsecond=0)
        key = hour.strftime('%Y-%m-%dT%H:00:00Z')
        bucket = buckets.setdefault(key, dict(ACT_attempts=0,
            window_start_unix=max(since_unix, hour.timestamp()),
            window_end_unix=min(until_unix, hour.timestamp() + 3600),
            **{field: 0 for field in COUNT_FIELDS}))
        bucket['ACT_attempts'] += 1
        for field in COUNT_FIELDS:
            bucket[field] += row.get(field, 0)
    return buckets


def native_outcome_row(record, saved_unix):
    document = record['document']
    environment = document.get('outcome', {}).get('environment', {})
    report = environment.get('report', {})
    feedback = report.get('feedback', [])
    known = [entry['result'] for entry in feedback if entry.get('result', {}).get('ok')
             and type(entry['result'].get('accepted')) is bool and not entry['result'].get('replayed')]
    metrics = report.get('format_metrics', {})
    origin = environment.get('origin') or document.get('origin') or {}
    return dict(unix=saved_unix, timestamp_basis='actual_R184_ACT_file_mtime',
        index=record['index'], record_sha256=record['sha256'],
        origin_sha256=origin.get('record_sha256', record['sha256']),
        scorer_receipt_sha256=environment.get('receipt_sha256'), error=report.get('error'),
        transport_failure=report.get('error') in ('ORIGIN_TRANSPORT_NOT_DISPATCHED', 'SCORER_OUTCOME_UNKNOWN_NO_RETRY'),
        parsed=report.get('requested_count', 0), scored=len(known),
        accepted=sum(item['accepted'] for item in known),
        new_pixels=sum(item['accepted'] and item.get('status') == 'new_pixel' for item in known),
        judge_rejected=sum(not item['accepted'] for item in known),
        cached=sum(bool(item.get('result', {}).get('replayed')) for item in feedback),
        format_fault=bool(metrics.get('format_fault')), format_metrics_present=bool(metrics),
        no_caption_act=bool(metrics.get('no_caption_act')),
        routing_ambiguity=bool(metrics.get('ambiguous_caption_lines')))
