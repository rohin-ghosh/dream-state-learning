"""Post-hoc, zero-model public-cue diagnostics for the frozen SEQ266 data."""

import argparse
import base64
import hashlib
import json
from pathlib import Path


SOURCE_COMMIT = '7f9d4251ae1ff4c5ff9138adf267d081fffa6331'
RULES = (
    'display_first', 'display_last', 'lexical_low', 'lexical_high',
    'goal_first_character_parity', 'goal_last_character_parity',
    'closest_goal_port_hamming', 'farthest_goal_port_hamming',
)


def digest(value):
    encoded = json.dumps(value, sort_keys=True, ensure_ascii=True,
                         allow_nan=False, separators=(',', ':')).encode('ascii')
    return hashlib.sha256(encoded).hexdigest()


def opaque(master, prefix, index):
    payload = json.dumps(['experienced_event_microloop_DEV_v1', master, prefix, index],
                         ensure_ascii=True, separators=(',', ':')).encode('utf-8')
    suffix = base64.b32encode(hashlib.sha256(payload).digest()).decode('ascii')[:10]
    return prefix + '_' + suffix


def world_for(master):
    nodes = [opaque(master, 'N', index) for index in range(5)]
    edges = [dict(event=opaque(master, 'E', index), node=nodes[start],
                  port=opaque(master, 'P', index), outcome=nodes[end],
                  receipt=opaque(master, 'R', index))
             for index, (start, end) in enumerate(((0, 1), (0, 2), (1, 3), (2, 4)))]
    return dict(schema='DEV_EXPERIENCED_EVENT_TWO_HOP_V1', master=master,
                nodes=nodes, edges=edges)


def predict(rule, task):
    ports = task['ports']
    ranked = sorted(ports)
    if rule == 'display_first':
        return ports[0]
    if rule == 'display_last':
        return ports[-1]
    if rule == 'lexical_low':
        return ranked[0]
    if rule == 'lexical_high':
        return ranked[-1]
    if rule == 'goal_first_character_parity':
        return ranked[ord(task['goal'][2]) % 2]
    if rule == 'goal_last_character_parity':
        return ranked[ord(task['goal'][-1]) % 2]
    distances = {port: sum(first != second for first, second in
                           zip(task['goal'][2:], port[2:])) for port in ports}
    if rule == 'closest_goal_port_hamming':
        return min(ports, key=lambda port: (distances[port], port))
    if rule == 'farthest_goal_port_hamming':
        return min(ports, key=lambda port: (-distances[port], port))
    raise ValueError(rule)


def run(root):
    assert (root / 'source_commit.txt').read_text().strip() == SOURCE_COMMIT
    bindings = {}

    def load(relative):
        payload = (root / relative).read_bytes()
        bindings[str(relative)] = hashlib.sha256(payload).hexdigest()
        return json.loads(payload)

    records = []
    held_identifiers = set()
    for world_index in range(16):
        summary = load(f'baseline/PROBE_{world_index}_OWN_TEXT_SUMMARY.json')
        world = world_for(summary['master'])
        held_identifiers.update(world['nodes'])
        held_identifiers.update(value for edge in world['edges'] for value in edge.values())
        episodes = []
        for task_index in range(4):
            episode = load(f'baseline/PROBE_{world_index}_OWN_TEXT_{task_index}.json')
            assert episode['world_sha256'] == digest(world)
            task = episode['task']
            assert episode['task_sha256'] == digest(task)
            expected_ports = sorted(edge['port'] for edge in world['edges']
                                    if edge['node'] == world['nodes'][0])
            expected_events = sorted(edge['event'] for edge in world['edges'])
            if task_index % 2:
                expected_ports.reverse()
                expected_events.reverse()
            assert task == dict(node=world['nodes'][0], goal=world['nodes'][3 + task_index // 2],
                                ports=expected_ports, events=expected_events)
            intermediate = next(edge['node'] for edge in world['edges']
                                if edge['outcome'] == task['goal'])
            correct_port = next(edge['port'] for edge in world['edges']
                                if edge['node'] == task['node'] and edge['outcome'] == intermediate)
            initial = episode['messages'][1]['content']
            assert initial == (f"ROUTE TASK\nCURRENT {task['node']}\nGOAL {task['goal']}\n"
                               f"PORTS {','.join(task['ports'])}\nEVENTS {','.join(task['events'])}")
            episodes.append(dict(task=task, expected_first_port=correct_port))
        for first_index, second_index in ((0, 2), (1, 3)):
            first, second = episodes[first_index], episodes[second_index]
            assert first['expected_first_port'] != second['expected_first_port']
            assert {key: value for key, value in first['task'].items() if key != 'goal'} == {
                key: value for key, value in second['task'].items() if key != 'goal'}
        records.append(dict(master=world['master'], episodes=episodes))

    training = load('FULL_TARGET/train/TRAINING_ROWS.json')
    assert training == load('NEW_TRAJECTORY_LOSS_OFF/train/TRAINING_ROWS.json')
    overlap = {}
    for group, rows in training.items():
        present = set()
        for row in rows:
            messages = row['messages'] if 'messages' in row else row['prefix']
            assert isinstance(messages, list)
            texts = [message['content'] for message in messages]
            if 'assistant' in row:
                texts.append(row['assistant'])
            assert all(isinstance(text, str) for text in texts)
            joined = '\n'.join(texts)
            present.update(identifier for identifier in held_identifiers if identifier in joined)
        overlap[group] = dict(rows=len(rows), held_identifiers_present=sorted(present))
    assert sum(item['rows'] for item in overlap.values()) == 1674

    outcomes = {}
    for rule in RULES:
        world_outcomes = []
        for record in records:
            correct = [predict(rule, episode['task']) == episode['expected_first_port']
                       for episode in record['episodes']]
            world_outcomes.append(dict(master=record['master'], first_port_correct=correct,
                                       pair_upper_bound=sum(correct[first] and correct[second]
                                                            for first, second in ((0, 2), (1, 3)))))
        outcomes[rule] = dict(first_port_correct=sum(sum(item['first_port_correct'])
                                                   for item in world_outcomes),
                              first_port_denominator=64,
                              pair_upper_bound=sum(item['pair_upper_bound'] for item in world_outcomes),
                              pair_denominator=32, worlds=world_outcomes)
    return dict(schema='SEQ266_PUBLIC_SHORTCUT_SIDECAR_V1', source_commit=SOURCE_COMMIT,
                study_status='POST_HOC_EXPLORATORY_NOT_A_NEW_NATIVE_CONTROL',
                root=str(root), rules=list(RULES), model_calls=0, fits=0,
                held_identifier_count=len(held_identifiers), training_overlap=overlap,
                frozen_world_and_initial_task_bindings_verified=64,
                pair_gold_requires_distinct_first_ports=32, outcomes=outcomes,
                file_bindings=bindings,
                limitation='Only eight explicit public-cue rules; no claim to exclude all shortcuts. '
                           'Pair counts are optimistic first-branch upper bounds, not executed goals.')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    options = parser.parse_args()
    result = run(options.root)
    with options.output.open('x') as destination:
        json.dump(result, destination, indent=2, sort_keys=True)
        destination.write('\n')
    for name, outcome in result['outcomes'].items():
        print(name, outcome['first_port_correct'], '/64 first ports;',
              outcome['pair_upper_bound'], '/32 pair upper bound')
    print('held identifiers:', result['held_identifier_count'])
    print('training overlaps:', {name: len(item['held_identifiers_present'])
                                for name, item in result['training_overlap'].items()})


if __name__ == '__main__':
    main()
