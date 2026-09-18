"""Aggregate actual attempt receipts by UTC hour; no captions or private scores."""

import argparse
import datetime
import json
from pathlib import Path


def hourly(document):
    buckets = {}
    def bucket_at(timestamp):
        hour = datetime.datetime.fromtimestamp(timestamp, datetime.timezone.utc).strftime('%Y-%m-%dT%H:00:00Z')
        return buckets.setdefault(hour, dict(attempts=0, opportunities_completed=0, planned_known=0,
            planned_unknown_attempts=0, parsed=0, fault_attempts=0, scored=0, accepted=0, novel=0,
            unknown=0, cached=0, ACT_generated_tokens=0, THINK_generated_tokens=0,
            salvaged_THINK_captions=0, request_ids=[]))
    for event in document['events']:
        bucket = bucket_at(event['finished_unix'])
        request = event['source']['request_id']
        if request in bucket['request_ids']:
            raise ValueError('duplicate_attempt_receipt')
        bucket['request_ids'].append(request)
        bucket['attempts'] += 1
        bucket['opportunities_completed'] += int(event['opportunity_complete'])
        bucket['planned_known'] += event['planned'] or 0
        bucket['planned_unknown_attempts'] += int(event['planned'] is None)
        bucket['fault_attempts'] += int(event['fault'])
        bucket['salvaged_THINK_captions'] += event.get('salvaged_THINK', 0)
        for name in ['parsed', 'scored', 'accepted', 'novel', 'unknown', 'cached']:
            bucket[name] += event[name]
    seen_generations = set()
    for generation in document.get('generations', []):
        if generation['request_id'] in seen_generations:
            raise ValueError('duplicate_generation_receipt')
        seen_generations.add(generation['request_id'])
        bucket_at(generation['finished_unix'])[generation['stage']+'_generated_tokens'] += generation['generated_tokens']
    return dict(condition=document['condition'], buckets=buckets,
        pending=document.get('pending'),
        total_generated_tokens_including_THINK=document['total_generated_tokens'],
        denominators=dict(planned='sum_known_declared_counts_unknown_attempts_reported_separately',
            parsed='actual_parser_recovered_captions', fault='ACT_attempts_with_format_fault',
            scored='actual_known_nonreplayed_per_caption_receipts', accepted='accepted_scored_captions',
            novel='accepted_scored_captions_with_actual_new_pixel_status'), live_GPU_claim=False)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('receipt', type=Path)
    arguments=parser.parse_args()
    print(json.dumps(hourly(json.loads(arguments.receipt.read_text())), indent=2, sort_keys=True))


if __name__ == '__main__':
    main()
