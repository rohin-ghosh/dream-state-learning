"""Replay the two completed screen arms from original native call receipts."""

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import statistics

from organism_v6 import orch_persist_math as curriculum


def read(path):
    return json.loads(Path(path).read_text())


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def reduce_arm(root, arm):
    directory = Path(root) / arm
    result = read(directory / 'RESULT.json')
    if (directory / 'FAILED.json').exists() or result['status'] != 'COMPLETE':
        raise ValueError('completed_native_arm_required')
    if result['fits'] or result['updates'] or result['admitted_targets'] or not result['frozen_base_unchanged']:
        raise ValueError('readonly_screen_required')
    if result['adapter_state_after'] != result['loaded_adapter_state_sha256']:
        raise ValueError('adapter_state_join_failed')
    data = read(directory / 'DATA.json')
    paths = sorted(directory.glob('CALL_*.json'))
    captures = [read(path) for path in paths]
    cursor = 0

    def replay(messages, **metadata):
        nonlocal cursor
        capture = captures[cursor]
        if capture['call_index'] != cursor or capture['messages'] != messages or capture['metadata'] != metadata:
            raise ValueError('call_prefix_or_order_join_failed')
        if capture['error'] is not None or capture['response']['messages'] != messages:
            raise ValueError('actual_response_join_failed')
        cursor += 1
        return capture['response']

    replayed = curriculum.screen(replay, arm)
    if replayed != data or cursor != len(captures) or result['model_calls'] != cursor:
        raise ValueError('raw_replay_denominator_join_failed')
    expected_summary = {key: value for key, value in data.items() if key != 'episodes'}
    if result['summary'] != expected_summary:
        raise ValueError('result_summary_join_failed')
    errors = Counter()
    qualified = []
    for episode in data['episodes']:
        for turn in episode['turns']:
            verdict = turn['verdict']
            if not verdict['accepted']:
                errors[verdict['feedback'].get('error', 'parsed_but_answer_or_record_failed')] += 1
        if episode['accepted']:
            qualified.append(dict(task_id=episode['task']['task_id'], turn=len(episode['turns']) - 1,
                semantic_status='UNREVIEWED'))
    prose_counts = [capture['prose_tokens'] for capture in captures if capture.get('prose_tokens') is not None]
    return dict(**expected_summary, replayed=True, source_receipt_sha256=sha(directory / 'RESULT.json'),
        raw_data_sha256=sha(directory / 'DATA.json'),
        call_sha256={path.name: sha(path) for path in paths}, rejection_counts=dict(errors),
        joint_success_candidates=qualified,
        first_turn_joint=sum(episode['turns'][0]['verdict']['accepted'] for episode in data['episodes']),
        truncated_calls=sum(capture['response']['truncated'] for capture in captures),
        generated_tokens=sum(len(capture['response']['token_ids']) for capture in captures),
        prompt_tokens=sum(capture['response']['prompt_tokens'] for capture in captures),
        parsed_prose_token_range=[min(prose_counts), max(prose_counts)] if prose_counts else None,
        parsed_prose_token_median=statistics.median(prose_counts) if prose_counts else None,
        calls_in_150_400_prose_range=sum(150 <= count <= 400 for count in prose_counts),
        native_seconds=result['finished_unix'] - result['started_unix'],
        task_outcomes={episode['task']['task_id']: dict(answer=episode['outcome_success'],
            joint=episode['accepted']) for episode in data['episodes']})


def reduce_pair(root):
    arms = {arm: reduce_arm(root, arm) for arm in ('RICH', 'TERSE')}
    if arms['RICH']['task_outcomes'].keys() != arms['TERSE']['task_outcomes'].keys():
        raise ValueError('matched_task_set_required')
    pairings = Counter()
    for task_id in arms['RICH']['task_outcomes']:
        rich = arms['RICH']['task_outcomes'][task_id]['joint']
        terse = arms['TERSE']['task_outcomes'][task_id]['joint']
        pairings['both' if rich and terse else 'rich_only' if rich else 'terse_only' if terse else 'neither'] += 1
    return dict(arms=arms, paired_joint_counts=dict(pairings),
        fits=0, updates=0, admitted_targets=0, semantic_review='SEPARATE_TEXT_READING_REQUIRED',
        record_access='VISIBLE_IN_BOTH_ARMS', training_or_learning_slope_measured=False,
        equal_realized_compute=False)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', required=True)
    parser.add_argument('--output', required=True)
    options = parser.parse_args(argv)
    result = reduce_pair(options.root)
    with Path(options.output).open('x') as output:
        output.write(json.dumps(result, indent=2, sort_keys=True) + '\n')
    print(json.dumps({arm: {key: value[key] for key in ('tasks', 'final_outcomes', 'outcome_and_record',
        'model_calls', 'generated_tokens')} for arm, value in result['arms'].items()}, indent=2))


if __name__ == '__main__':
    main()
