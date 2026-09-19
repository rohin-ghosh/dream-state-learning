import collections
import hashlib
import json
from pathlib import Path
import re


HERE = Path(__file__).resolve().parent


def summarize(cells):
    seen = set()
    totals = collections.Counter()
    novelty_stages = collections.Counter()
    for cell in cells:
        for event in cell['events']:
            totals['generation_events'] += 1
            totals[event['stage'] + '_events'] += 1
            totals['generated_tokens'] += event['generated_tokens']
            totals['truncated_events'] += bool(event['truncated'])
            totals['CJK_characters'] += len(re.findall('[\u3400-\u4dbf\u4e00-\u9fff]', event['raw_child_output']))
            totals['events_containing_CJK'] += bool(re.search('[\u3400-\u4dbf\u4e00-\u9fff]', event['raw_child_output']))
            for outcome in event['judgments']:
                identity = (cell['seed'], cell['contest_id'], outcome['caption_sha256'])
                if identity in seen or outcome['cached']:
                    continue
                seen.add(identity)
                totals['distinct_scored_seed_local_sum'] += outcome['rank'] is not None
                totals['distinct_accepted_seed_local_sum'] += outcome['accepted'] is True
                if outcome['status'] == 'new_pixel':
                    novelty_stages[event['stage']] += 1
    return dict(totals, mean_tokens_per_generation=totals['generated_tokens'] / totals['generation_events'],
        new_pixels_seed_local_sum=sum(novelty_stages.values()),
        new_pixels_by_first_counted_stage=dict(novelty_stages))


def main():
    source = HERE / 'CHILD_OUTPUTS.json'
    raw = source.read_bytes()
    packet = json.loads(raw)
    summaries = {arm: summarize([cell for cell in packet['cells'] if cell['arm'] == arm])
        for arm in ('base', 'c2sleep51', 'c2sleep117')}
    expected = {'base': (50, 105, 81, 48), 'c2sleep51': (65, 151, 79, 57), 'c2sleep117': (152, 168, 81, 38)}
    for arm, summary in summaries.items():
        assert summary['generated_tokens'] == 6144
        assert tuple(summary[name] for name in ('generation_events', 'distinct_scored_seed_local_sum',
            'distinct_accepted_seed_local_sum', 'new_pixels_seed_local_sum')) == expected[arm]
    document = {'source_sha256': hashlib.sha256(raw).hexdigest(), 'scope': 'mechanical_counts_all18_cells_not_full_semantic_scoring',
        'arms': summaries, 'new_pixels_are_not_human_humor': True,
        'training_rows_removed': 0, 'runtime_changes': 0}
    with (HERE / 'SUMMARY.json').open('x') as stream:
        json.dump(document, stream, indent=2)
        stream.write('\n')
    print(json.dumps(summaries, indent=2))


if __name__ == '__main__':
    main()
