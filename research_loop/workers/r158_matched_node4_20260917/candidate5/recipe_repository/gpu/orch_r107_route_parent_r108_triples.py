"""Node-only, hash-bound state/intervention/behavior references; no model calls."""

import argparse
import hashlib
import json
from pathlib import Path
import time

from organism_v6 import orch_r107_route_parent_r108 as policy


def read(path):
    return json.loads(path.read_text())


def reference(path):
    return dict(path=str(path), sha256=hashlib.sha256(path.read_bytes()).hexdigest())


def evidence_table(triples, episode_count):
    return dict(completed_train_episodes=episode_count, parent_intervention_triples=len(triples),
        minimum_review_episodes=50, requested_review_range=[50, 100],
        sufficient_episode_count=episode_count >= 50,
        recurring=None, helpful=None, unhelpful=None, unaudited_triples=len(triples),
        automatic_keyword_or_outcome_qualification=False,
        status='AWAIT_AUTHOR_REVIEW' if episode_count >= 50 else 'INSUFFICIENT_EPISODES_NO_QUOTA_EXPANSION')


def collect(root):
    triples = []; episodes = 0
    for index in (2, 3, 6):
        lane = root / f'campaign_route_parent_{index}'; native = lane / 'native'
        episodes += len(list(native.glob('TRAIN_C*_E*.json')))
        calls = []
        for path in sorted(native.glob('CALL_*.json')):
            row = read(path)
            if 'response' in row and 'finished_unix' in row:
                calls.append((path, row))
        for path in sorted(lane.glob('PARENT_C*_P*.json')):
            result = read(path)
            cycle, episode = [int(value) for value in path.stem.removeprefix('PARENT_C').split('_P')]
            state = native / f'TRAIN_C{cycle}_E{episode}.json'
            task_id = read(state)['task']['task_id']
            after = [(call_path, row) for call_path, row in calls
                     if row['started_unix'] >= result['observed_unix']]
            reflections = [(call_path, row) for call_path, row in after
                           if row['purpose'] == 'reflection' and row['task_id'] == task_id]
            following = [(call_path, row) for call_path, row in after
                         if row['purpose'] in ('train_episode', 'held_episode')]
            archive = Path(result['archive']['remote_root'])
            triple = dict(index=index, lineage_policy=policy.STYLES[index] + '/R108',
                cycle=cycle, episode_index=episode, child_state=reference(state),
                parent_intervention=reference(path), actual_parent_plan=reference(archive / 'PLAN.json'),
                actual_parent_raw_envelope=reference(archive / 'RAW_RESPONSE.json'),
                own_reflection=reference(reflections[0][0]) if reflections else None,
                next_behavior=reference(following[0][0]) if following else None,
                next_behavior_context=following[0][1]['purpose'] if following else None,
                behavioral_change='UNKNOWN_PENDING_AUTHOR_AUDIT', helpfulness='UNKNOWN',
                intervention_classes='UNKNOWN_UNTIL_REVIEW_OF_PARENT_RATIONALE',
                held_behavior_never_sent_to_parent=True, no_outcome_criterion=True)
            triples.append(triple)
    return dict(observed_unix=time.time(), triples=triples, table=evidence_table(triples, episodes),
        raw_embedded=False, all_raw_remains_in_original_node_captures=True,
        model_calls=0, trainingAllowed=False, no_automatic_refill=True)


def write(path, value):
    temporary = path.with_suffix('.partial')
    temporary.write_text(json.dumps(value, sort_keys=True, indent=2) + '\n')
    temporary.replace(path)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--watch', action='store_true')
    args = parser.parse_args(); prior = None
    while True:
        snapshot = collect(args.root)
        state = json.dumps(snapshot['triples'], sort_keys=True)
        if state != prior:
            write(args.root / f'TRIPLES_{time.time_ns()}.json', snapshot)
            write(args.root / 'TRIPLES_LATEST.json', snapshot)
            prior = state
        lanes = [args.root / f'campaign_route_parent_{index}' for index in (2, 3, 6)]
        terminal = all((lane / 'TERMINAL.json').exists() for lane in lanes)
        if not args.watch or terminal or time.time() >= read(args.root / 'LIFETIME.json')['hard_deadline_unix']:
            break
        time.sleep(5)
