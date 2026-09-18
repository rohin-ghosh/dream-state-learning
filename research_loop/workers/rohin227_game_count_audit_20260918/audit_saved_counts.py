"""Reconcile saved receipt counts without scoring, changing rows or reading targets."""

import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path


FIELDS = ('parsed', 'scored', 'accepted', 'new_pixels', 'cached', 'format_fault')


def summarize(rows):
    origins = [row['origin_sha256'] for row in rows]
    receipts = [row['receipt_sha256'] for row in rows]
    if len(set(origins)) != len(origins) or len(set(receipts)) != len(receipts):
        raise ValueError('duplicate_ACT_or_receipt_across_reported_phases')
    totals = {field: sum(row[field] for row in rows) for field in FIELDS}
    sources = [source for row in rows for source in row['scored_sources']]
    accepted = [source for source in sources if source['accepted']]
    if len(sources) != totals['scored'] or len(accepted) != totals['accepted']:
        raise ValueError('source_and_score_denominators_disagree')
    known = [source for source in accepted if source['exact_source_span_verified']
        and source['text_sha256'] is not None]
    timestamps = [row['unix'] for row in rows]
    return dict(ACT_attempts=len(rows), **totals,
        accept_rate=totals['accepted'] / totals['scored'] if totals['scored'] else None,
        accept_rate_denominator='newly_scored_nonreplayed_strings',
        accepted_known_source_spans=len(known),
        accepted_missing_source_spans=len(accepted) - len(known),
        accepted_distinct_known_text_hashes=len({source['text_sha256'] for source in known}),
        accepted_by_stage=dict(Counter(source['stage'] or 'unknown' for source in accepted)),
        first_receipt_utc=datetime.fromtimestamp(min(timestamps), timezone.utc).isoformat()
            if timestamps else None,
        last_receipt_utc=datetime.fromtimestamp(max(timestamps), timezone.utc).isoformat()
            if timestamps else None,
        top_k_values=sorted({value for row in rows for value in row['top_k_values']}),
        literal_caption_status='NOT_ESTABLISHED_BY_HASH_OR_AGGREGATE_COUNTER',
        distinct_semantic_ideas_status='NOT_ESTABLISHED_BY_NEW_PIXEL_COUNTER')


def report(document):
    base = document['fleet']['frozen_base']['counts']['rows']
    parented = document['fleet']['parented_C2_P3']
    p3 = [row for phase in ('legacy', 'prior', 'current') for row in parented[phase]['rows']]
    players = {'frozen_base': base, 'parented_C2_P3': p3}
    hourly = {}
    for player, rows in players.items():
        hours = {}
        for row in rows:
            hour = datetime.fromtimestamp(row['unix'], timezone.utc).strftime('%Y-%m-%dT%H:00:00Z')
            hours.setdefault(hour, []).append(row)
        hourly[player] = {hour: summarize(values) for hour, values in sorted(hours.items())}
    return dict(schema='R227_SAVED_GAME_COUNT_AUDIT_V1',
        source_cut_utc=document['published_utc'], source_since_utc=document['since_utc'],
        cumulative={player: summarize(rows) for player, rows in players.items()},
        hourly_counts_not_rates=hourly,
        base_completed_controller_opportunities=document['fleet']['frozen_base']['completed_opportunities'],
        planned_unknown_definition='ACT attempt has no machine-readable declared planned caption count; '
            'not an unknown score, missing caption, or automatic fault',
        node3='This auditor does not infer game metrics from the node3 LOAD census',
        scoring_or_training_changes=False, raw_targets_included=False,
        causal_hypothesis_conclusion=False)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', type=Path)
    parser.add_argument('output', type=Path)
    arguments = parser.parse_args()
    payload = arguments.source.read_bytes()
    output = report(json.loads(payload))
    output['source_file_name'] = arguments.source.name
    output['source_file_sha256'] = hashlib.sha256(payload).hexdigest()
    with arguments.output.open('x') as stream:
        json.dump(output, stream, indent=2, sort_keys=True, allow_nan=False)
        stream.write('\n')


if __name__ == '__main__':
    main()
