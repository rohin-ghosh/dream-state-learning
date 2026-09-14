"""Hash-bound all-candidate author adjudication of the fixed diagnostic."""

import argparse
import hashlib
import json
from pathlib import Path

from organism_v6 import orch_base_contract as policy


def main():
    parser = argparse.ArgumentParser()
    for name in ('freeze', 'raw', 'reviews', 'output'):
        parser.add_argument('--' + name, required=True)
    options = parser.parse_args()
    entries = json.loads(Path(options.freeze).read_text())['entries']
    reviews = json.loads(Path(options.reviews).read_text())
    rows = []
    runs = []
    expected_freeze = hashlib.sha256(Path(options.freeze).read_bytes()).hexdigest()
    for shard in range(4):
        directory = Path(options.raw) / f'shard{shard}'
        result = json.loads((directory / 'RESULT.json').read_text())
        assert result['status'] == 'COMPLETE' and result['base_and_adapter_unchanged']
        assert result['freeze_sha256'] == expected_freeze
        calls = sorted(directory.glob('CALL_*.json'))
        assert len(calls) == result['model_calls'] <= 8
        runs.append(result)
        for path in calls:
            row = json.loads(path.read_text())
            row['raw_file'] = str(path.relative_to(Path(options.raw)))
            row['raw_file_sha256'] = hashlib.sha256(path.read_bytes()).hexdigest()
            key = row['raw_file']
            assert row['target_sha256'] == policy.sha(row['target'])
            assert row['call']['raw'] == row['target']
            entry = entries[row['position']]
            assert entry['task']['id'] == row['task_id'] and row['position'] % 4 == shard
            if row['kind'] == 'solution':
                assert row['call']['messages'] == entry['initial_messages']
            assert row['call']['prompt_tokens'] == len(row['serialization']['input_token_ids']) <= 2048
            assert len(row['call']['token_ids']) <= 512
            review = reviews[key]
            row['admitted'] = policy.admission(row, review)
            row['semantic_status'] = review['status']
            row['review'] = review
            row['legacy_code_rationale_pass'] = row['domain'] != 'CODE' or row['rationale_tokens'] >= 150
            rows.append(row)
    assert len(reviews) == len(rows) <= 32
    assert sum(row['kind'] == 'solution' for row in rows) == 16
    summary = policy.reduce(entries, rows)
    summary.update(full_texts_reviewed=len(rows), independent_review=False,
                   clean_paired_provenance=not any(run.get('historical_post_mounted_hash_missing') for run in runs),
                   historical_post_mounted_hash_missing=sum(run.get('imported_model_calls', 0) for run in runs),
                   author='BASE-CONTRACT', native_gpu_hours=sum(run['finished_unix'] - run['started_unix'] for run in runs) / 3600,
                   original_replay=[dict(task_id=entry['task']['id'], exact=next(row for row in rows
                       if row['task_id'] == entry['task']['id'] and row['state'] == 'ORIGINAL' and row['kind'] == 'solution')['target_sha256']
                       == entry['original_target_sha256']) for entry in entries],
                   by_domain={domain: {state: dict(denominator=4,
                       admitted_tasks=sum(pair[state] for pair in summary['pairs'] if pair['domain'] == domain),
                       initial_success=sum(row['outcome_pass'] for row in rows if row['state'] == state and row['domain'] == domain and row['kind'] == 'solution'))
                       for state in policy.STATES} for domain in ('CODE', 'MATH')})
    output = Path(options.output)
    output.mkdir(exist_ok=True)
    for name, value in [('ROWS.json', rows), ('REDUCTION.json', summary)]:
        with (output / name).open('x') as stream:
            stream.write(json.dumps(value, sort_keys=True, indent=2, ensure_ascii=False) + '\n')
    print(json.dumps(summary, indent=2))


if __name__ == '__main__':
    main()
