"""Operator-only first-current-port reference over saved L2 world bytes."""

from organism_v6 import orch_l2_guided as guided
from organism_v6 import orch_l2_shared as shared


def first_current_port(messages):
    public = next(message['content'] for message in reversed(messages)
                  if message['role'] == 'user' and 'ROUTE TASK\n' in message['content'])
    task = public.rsplit('ROUTE TASK\n', 1)[1]
    ports = next(line[6:] for line in task.splitlines() if line.startswith('PORTS '))
    if not ports:
        raise ValueError('no_current_port')
    return dict(raw='ROUTE ' + ports.split(',')[0], terminal=True, truncated=False)


def reference(frozen, document):
    store = shared.verify_source(frozen, document)
    result = dict(model_calls=0, provider_calls=0, fits=0, worlds_regenerated=False,
                  policy='IMMEDIATE_FIRST_CURRENT_LISTED_PORT_NO_READ_NO_GOAL_CONDITIONING',
                  train=[], held=[])
    for split in ('train', 'held'):
        for stage, worlds in enumerate(frozen[split]):
            panel = dict(stage=stage + 1 if split == 'train' else stage,
                         goals=0, goal_denominator=16, pairs=0, pair_denominator=8,
                         worlds=[])
            if len(worlds) != 8:
                raise ValueError('world_denominator_drift')
            for world in worlds:
                records = [guided.episode(world, task, first_current_port, store,
                                          rich_contract=False)
                           for task in shared.tasks(world)]
                for record in records:
                    if record['reads'] or record['parent_messages'] or len(record['routes']) != 2:
                        raise ValueError('firstport_transition_failed')
                    shared.readout.score(world, record['task'], record)
                first_ports = [record['routes'][0]['port'] for record in records]
                pair = all(record['correct'] for record in records) and len(set(first_ports)) == 2
                goals = sum(record['correct'] for record in records)
                panel['goals'] += goals
                panel['pairs'] += pair
                panel['worlds'].append(dict(master=world['master'], goals=goals,
                    pair_correct=pair, first_ports=first_ports, records=records))
            result[split].append(panel)
    return result
