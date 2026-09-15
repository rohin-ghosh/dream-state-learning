"""Offline R106 composition; semantic annotations stay separate from proxies."""

import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
from statistics import mean


CATEGORIES = ('direct_computation', 'restated_givens', 'checks_verification',
              'judgments_asides', 'meta_comments', 'final_answer')


def digest(data):
    return hashlib.sha256(data).hexdigest()


def segments(text):
    boundaries = {0, len(text)}
    for match in re.finditer(r'(?<=[.!?])\s+(?=[A-Z\\])|\n+|(?=\bFINAL:)', text):
        boundaries.add(match.start())
        boundaries.add(match.end())
    ordered = sorted(boundaries)
    pieces = [(start, end) for start, end in zip(ordered, ordered[1:])
              if text[start:end].strip()]
    if not pieces:
        raise ValueError('empty output')
    return [(0 if index == 0 else start,
             pieces[index + 1][0] if index + 1 < len(pieces) else len(text))
            for index, (start, end) in enumerate(pieces)]


def proxy_label(text):
    lowered = text.strip().lower()
    if re.search(r'\bfinal:|\\boxed\{', lowered):
        return 'final_answer'
    if re.search(r'\b(my reasoning|my thinking|my approach|rethink|thought process)\b', lowered):
        return 'meta_comments'
    if re.search(r'\b(check|verify|verification|double-check|sanity|what if)\b', lowered):
        return 'checks_verification'
    if re.search(r'\b(notice|interestingly|reasonable|unreasonable|alternatively|however)\b', lowered):
        return 'judgments_asides'
    if re.match(r'(given\b|each\b|the first\b|the quilt\b|since\b)', lowered) and not re.search(
            r'=|\b(calculate|divide|multiply|so|therefore|find|gives|will|can)\b', lowered):
        return 'restated_givens'
    return 'direct_computation'


def validate_annotation(annotation, text, spans):
    if annotation['text_sha256'] != digest(text.encode()):
        raise ValueError('annotation hash mismatch')
    labels = annotation['labels']
    if len(labels) != len(spans) or any(label not in CATEGORIES for label in labels):
        raise ValueError('annotation must label every segment once')
    methods = annotation['worked_methods']
    if type(methods) is not int or methods < 0:
        raise ValueError('invalid method count')
    for branch in annotation['departures_and_returns']:
        main, departure, resume = (branch[key] for key in ('main', 'departure', 'return'))
        if not all(type(index) is int for index in (main, departure, resume)):
            raise ValueError('branch indices must be integers')
        if not 0 <= main < departure < resume < len(spans):
            raise ValueError('branch needs ordered main, departure and return')
        if not branch.get('reason') or not branch.get('kind'):
            raise ValueError('branch requires evidence interpretation')
        expected_phase = 'terminal_check_or_aside' if labels[resume] == 'final_answer' else 'mid_solution'
        if branch.get('return_phase') != expected_phase:
            raise ValueError('branch return phase must match annotated resumption')
    return labels


def count_tokens(offsets, spans, labels):
    counts = Counter({category: 0 for category in CATEGORIES})
    for start, end in offsets:
        if end <= start:
            raise ValueError('unexpected empty content token offset')
        overlaps = [max(0, min(end, span_end) - max(start, span_start))
                    for span_start, span_end in spans]
        if not max(overlaps):
            raise ValueError('token outside labelled text')
        counts[labels[overlaps.index(max(overlaps))]] += 1
    return dict(counts)


def summarize(records, field, sample=None):
    selected = [record for record in records if record.get(field) is not None
                and (sample is None or record.get('author_sample') == sample)]
    counts = {category: sum(record[field][category] for record in selected)
              for category in CATEGORIES}
    total = sum(counts.values())
    return dict(outputs=len(selected), content_tokens=total, token_counts=counts,
                token_shares={category: count / total if total else None
                              for category, count in counts.items()})


def reduce_arm(directory, tokenizer, annotations):
    loaded = json.loads((directory / 'LOADED.json').read_text())
    if loaded.get('parent_present') is not False:
        raise ValueError('requires parent-free readout')
    records = []
    for path in sorted(directory.glob('CALL_*.json')):
        call = json.loads(path.read_text())
        if call['metadata']['purpose'] not in ('math', 'math_held'):
            continue
        if call['status'] != 'COMPLETE':
            raise ValueError('incomplete call')
        text = call['response']['raw']
        encoded = tokenizer(text, add_special_tokens=False, return_offsets_mapping=True)
        native_ids = call['response']['token_ids']
        content_ids = list(native_ids)
        while content_ids and content_ids[-1] in tokenizer.all_special_ids:
            content_ids.pop()
        if encoded['input_ids'] != content_ids:
            raise ValueError('retokenized text differs from native IDs: ' + str(path))
        spans = segments(text)
        labels = [proxy_label(text[start:end]) for start, end in spans]
        annotation = annotations.get(digest(text.encode()))
        author_counts = None
        if annotation is not None:
            author_labels = validate_annotation(annotation, text, spans)
            author_counts = count_tokens(encoded['offset_mapping'], spans, author_labels)
        records.append(dict(position=call['position'], task_id=call['metadata']['task_id'],
            call_sha256=digest(path.read_bytes()), text_sha256=digest(text.encode()),
            generated_tokens=len(native_ids), content_tokens=len(content_ids),
            excluded_terminal_tokens=len(native_ids) - len(content_ids),
            segment_boundaries=spans,
            lexical_proxy_counts=count_tokens(encoded['offset_mapping'], spans, labels),
            author_counts=author_counts,
            author_sample=annotation.get('sample') if annotation else None,
            worked_methods=annotation['worked_methods'] if annotation else None,
            departures_and_returns=annotation['departures_and_returns'] if annotation else None))
    if len(records) != 64:
        raise ValueError('expected matched 64-task cohort')
    return dict(native_readout=str(directory), loaded_sha256=digest((directory / 'LOADED.json').read_bytes()),
        outputs=len(records), mean_generated_tokens=mean(row['generated_tokens'] for row in records),
        lexical_proxy=summarize(records, 'lexical_proxy_counts'),
        author_review=summarize(records, 'author_counts', 'fixed_first4'),
        marker_selected_review=summarize(records, 'author_counts', 'marker_selected'),
        confirmed_branch_outputs_lower_bound=sum(bool(row['departures_and_returns']) for row in records),
        confirmed_mid_solution_outputs_lower_bound=sum(any(branch['return_phase'] == 'mid_solution'
            for branch in (row['departures_and_returns'] or [])) for row in records),
        confirmed_terminal_check_outputs_lower_bound=sum(any(branch['return_phase'] == 'terminal_check_or_aside'
            for branch in (row['departures_and_returns'] or [])) for row in records),
        semantic_unreviewed=sum(row['departures_and_returns'] is None for row in records), records=records)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--tokenizer', required=True)
    parser.add_argument('--annotations', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    options = parser.parse_args()
    from transformers import AutoTokenizer
    tokenizer = AutoTokenizer.from_pretrained(options.tokenizer, local_files_only=True, use_fast=True)
    annotations = json.loads(options.annotations.read_text()) if options.annotations else {}
    report = dict(schema='R106_COMPOSITION_V1', native_calls=0, parent_calls=0,
        measured_utc=datetime.now(timezone.utc).isoformat(),
        fits=0, raw_text_included=False, visibility='SEALED_ANALYST_ONLY_NOT_TRAIN_OR_PARENT',
        semantic_population_branching=None,
        lexical_proxy_warning='Rule-based segment labels with direct-computation fallback; not semantic verdicts.',
        author_sample='Fixed first4/arm; nonrandom, not population estimate',
        source_sha256=digest(Path(__file__).read_bytes()),
        annotations_sha256=digest(options.annotations.read_bytes()) if options.annotations else None,
        arms={arm: reduce_arm(options.root / arm / 'readout', tokenizer, annotations)
              for arm in ('FULL', 'OFF', 'BASE')})
    groups = [{(row['position'], row['task_id']) for row in result['records']}
              for result in report['arms'].values()]
    if any(group != groups[0] for group in groups):
        raise ValueError('unmatched task cohorts')
    with options.output.open('x') as destination:
        json.dump(report, destination, indent=2, sort_keys=True)
        destination.write('\n')
    print(json.dumps({arm: {key: value for key, value in result.items() if key != 'records'}
                      for arm, result in report['arms'].items()}, indent=2))


if __name__ == '__main__':
    main()
