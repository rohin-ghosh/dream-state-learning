"""Retain selected-task denominators and separate oracle/semantic judgments."""

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path

from organism_v6 import orch_code_bounded as code


def reduce(root, reviews=None):
    root = Path(root)
    document = json.loads((root / 'TASKS.json').read_text())
    reviews = reviews or {}
    rows = []
    episodes = []
    for path in sorted(root.glob('shard*/CALL_*.json')):
        row = json.loads(path.read_text())
        row['row_id'] = str(path.relative_to(root))
        assert row['target_sha256'] == code.sha(row['target'])
        assert row['target'] == row['call']['raw']
        task = next(task for task in document['tasks'] if task['id'] == row['task_id'])
        try:
            action, rationale = code.parse_action(row['target'], row['kind'] == 'record')
            replay = dict(success=True, record=True) if row['kind'] == 'record' else code.check(task, action)
        except Exception as error:
            replay = dict(success=False, error=str(error))
        assert replay == row['feedback']
        review = reviews.get(row['row_id'], {})
        if review:
            assert review['target_sha256'] == row['target_sha256']
            assert review['status'] in ('PASS', 'FAIL', 'UNRESOLVED')
            assert review['reason'] and review['evidence_spans']
            assert all(span in row['target'] for span in review['evidence_spans'])
        row['semantic_status'] = review.get('status', 'UNREVIEWED')
        row['row_eligible'] = (row['arm'] == 'rich'
                              and row['token_contract'] and row['rationale_tokens'] >= 150
                              and row['semantic_status'] == 'PASS')
        rows.append(row)
    for task in document['tasks']:
        for arm in ('rich', 'terse'):
            current = [row for row in rows if row['task_id'] == task['id'] and row['arm'] == arm]
            solution_rows = [row for row in current if row['kind'] != 'record']
            records = [row for row in current if row['kind'] == 'record']
            outcome = any(row['feedback']['success'] for row in solution_rows)
            correction = any(row['kind'] == 'correction' and row['feedback']['success'] for row in solution_rows)
            admitted = (arm == 'rich' and outcome and bool(records)
                        and all(row['feedback']['success'] for row in records)
                        and all(row['row_eligible'] for row in current))
            episodes.append(dict(task_id=task['id'], family=task['family'], arm=arm,
                                 calls=len(current), outcome=outcome, correction=correction,
                                 record_action=any(row['feedback']['success'] for row in records),
                                 admitted=admitted))
            for row in current:
                row['admitted'] = admitted
    metrics = {}
    for arm in ('rich', 'terse'):
        current = [episode for episode in episodes if episode['arm'] == arm]
        selected_rows = [row for row in rows if row['arm'] == arm]
        metrics[arm] = dict(tasks=len(current), attempted=sum(item['calls'] > 0 for item in current),
                           successes=sum(item['outcome'] for item in current),
                           corrected_tasks=sum(item['correction'] for item in current),
                           record_actions=sum(item['record_action'] for item in current),
                           admitted_episodes=sum(item['admitted'] for item in current),
                           admitted_rows=sum(row['admitted'] for row in selected_rows),
                           row_eligible=sum(row['row_eligible'] for row in selected_rows),
                           calls=len(selected_rows), generated_tokens=sum(row['generated_tokens'] for row in selected_rows),
                           families={family: dict(tasks=sum(item['family'] == family for item in current),
                                 successes=sum(item['outcome'] and item['family'] == family for item in current))
                                     for family in sorted({item['family'] for item in current})})
    complete = all((root / f'shard{index}/RESULT.json').exists() for index in range(4))
    exits = {str(index): int((root / f'shard{index}_launch/exit_code.txt').read_text())
             if (root / f'shard{index}_launch/exit_code.txt').exists() else None for index in range(4)}
    if complete:
        for index in range(4):
            result = json.loads((root / f'shard{index}/RESULT.json').read_text())
            assert result['status'] == 'COMPLETE'
            assert result['model_calls'] == sum(row['row_id'].startswith(f'shard{index}/') for row in rows)
    gate = (complete and metrics['rich']['successes'] > metrics['terse']['successes']
            and metrics['rich']['admitted_episodes'] >= 4
            and sum(item['correction'] and item['admitted'] for item in episodes) >= 2)
    summary = dict(eligibility=dict(considered=document['total'], eligible=document['eligible_count'],
                                     excluded=len(document['exclusions'])), scientific_denominator=8,
                   complete=complete, guardian_exit_codes=exits, clean_process_exit=all(value == 0 for value in exits.values()),
                   metrics=metrics, episodes=episodes, scale_gate=gate, fits=0,
                   training_rows=0, model_calls=len(rows),
                   semantic_counts=dict(Counter(row['semantic_status'] for row in rows if row['arm'] == 'rich')),
                   max_context=max((row['call']['prompt_tokens'] for row in rows), default=0),
                   max_generated=max((len(row['call']['token_ids']) for row in rows), default=0),
                   truncations=sum(row['call']['truncated'] for row in rows),
                   generated_token_distribution=[row['generated_tokens'] for row in rows],
                   task_sha256=hashlib.sha256((root / 'TASKS.json').read_bytes()).hexdigest())
    return summary, rows


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('root')
    parser.add_argument('--reviews')
    parser.add_argument('--output', required=True)
    options = parser.parse_args()
    review = json.loads(Path(options.reviews).read_text()) if options.reviews else None
    summary, rows = reduce(options.root, review)
    output = Path(options.output)
    output.mkdir(exist_ok=False)
    (output / 'SUMMARY.json').write_text(json.dumps(summary, indent=2) + '\n')
    (output / 'ROWS.json').write_text(json.dumps(rows, indent=2) + '\n')
