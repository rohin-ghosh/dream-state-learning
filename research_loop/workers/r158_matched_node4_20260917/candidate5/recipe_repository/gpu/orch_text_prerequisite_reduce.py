"""Fixed-denominator descriptive reduction; semantic judgments remain separate."""

import argparse
import json
from pathlib import Path

from organism_v6 import orch_text_prerequisite as protocol


def reduce(root, bank):
    mining = [task for task in bank['tasks'] if task['split'] == 'mining']
    if len(mining) != 8:
        raise ValueError('fixed_eight_pairs_required')
    episodes = []
    for task in mining:
        for arm in ('RICH', 'TERSE'):
            path = root / f"shard{task['shard']}/screen/{task['id']}_{arm}_EPISODE.json"
            record = json.loads(path.read_text()) if path.exists() else dict(
                task_id=task['id'], arm=arm, success=False, turns=[], error='MISSING_RETAINED_IN_DENOMINATOR')
            episodes.append(record)
    rates = protocol.eligible([item['success'] for item in episodes if item['arm'] == 'RICH'],
                              [item['success'] for item in episodes if item['arm'] == 'TERSE'])
    arms = {}
    for arm in ('RICH', 'TERSE'):
        selected = [item for item in episodes if item['arm'] == arm]
        turns = [turn for item in selected for turn in item['turns']]
        arms[arm] = dict(success=sum(item['success'] for item in selected), denominator=8,
            turns=len(turns), episode_errors=sum(bool(item['error']) for item in selected),
            format_errors=sum(bool(turn['format_error']) for turn in turns),
            truncations=sum(bool(turn['response'] and turn['response']['truncated']) for turn in turns),
            prose_tokens=[turn['prose_tokens'] for turn in turns if turn['prose_tokens'] is not None],
            generated_tokens=sum(len(turn['response']['token_ids']) for turn in turns if turn['response']),
            max_prompt_tokens=max([turn['response']['prompt_tokens'] for turn in turns if turn['response']] or [0]))
    shards = []
    for index in range(4):
        path = root / f'shard{index}/screen/RESULT.json'
        result = json.loads(path.read_text()) if path.exists() else None
        shards.append(dict(shard=index, status=result['status'] if result else 'MISSING',
            calls=result['model_calls'] if result else None,
            seconds=result['finished_unix']-result['started_unix'] if result else None))
    return dict(outcome=rates, arms=arms, shards=shards, fits=0, updates=0,
        held_L1_inference=0, semantic_review='SEPARATE_REQUIRED', pool_admitted=False,
        table=[dict(task_id=item['task_id'], arm=item['arm'], success=item['success'],
                    turns=len(item['turns']), error=item['error']) for item in episodes])


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('root', type=Path)
    parser.add_argument('bank', type=Path)
    parser.add_argument('output', type=Path)
    arguments = parser.parse_args()
    result = reduce(arguments.root, json.loads(arguments.bank.read_text()))
    arguments.output.write_text(json.dumps(result, sort_keys=True, indent=2) + '\n')
    print(json.dumps(result, sort_keys=True, indent=2))
