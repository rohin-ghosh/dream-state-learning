"""Read saved source and traces only; no generation, replay, scoring or relabeling."""

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path


ROOT = Path('gpu_artifacts_local/orch_terse_breadth_20260914_attempt1/terminal_a100')
OUTPUT = Path('research_notes/analysis/orch_terse_breadth_20260914_attempt1/FAILURE_MECHANISM.json')
STAGES = ('baseline0', 'after0', 'after1', 'after2', 'after3')
INDICES = (13, 14, 15)


def main():
    hashes = {}

    def read(relative):
        raw = (ROOT / relative).read_bytes()
        hashes[relative] = hashlib.sha256(raw).hexdigest()
        return json.loads(raw)

    sources = read('assembly/READOUT_SOURCES.json')
    source = read('collection1/shard7/COLLECTION_08.json')
    assert source == sources[7][8]
    assert source['accepted_events'] == 3 and not source['ready']
    rejected = [record for record in source['records'] if not record['accepted']]
    assert len(rejected) == 1
    missing = rejected[0]
    native = read('collection1/CALL_0329.json')
    assert missing['event']['raw'] in json.dumps(native)
    expected_port = missing['edge']['port']
    emitted_port = missing['event']['raw'].split(' DID ')[1].split(' GOT ')[0]
    assert expected_port == 'P_SQ7P2Z2RPW' and emitted_port == 'P_SQ7P2ZRPW'
    accepted = {record['edge']['event']: record for record in source['records'] if record['accepted']}
    for record in accepted.values():
        edge = record['edge']
        tokens = record['event']['raw'].rstrip('\n').split(' ')
        assert tokens == ['EVENT', edge['event'], 'AT', edge['node'], 'DID', edge['port'],
                          'GOT', edge['outcome'], 'EVIDENCE', edge['receipt']]
    worlds, commands_by_stage = [], {}
    for index in INDICES:
        shard, offset = divmod(index, 2)
        collection = sources[shard][8 + offset]
        world_report = dict(index=index, master=collection['master'],
                            source_accepted=collection['accepted_events'], source_denominator=4,
                            source_ready=collection['ready'], states={})
        for stage in STAGES:
            summary = read(f'{stage}/RESULT.json')['summary']
            panel = next(panel for panel in summary['panels'] if panel['split'] == 'PROBE'
                         and panel['condition'] == 'OWN_TEXT' and panel['master'] == collection['master'])
            episodes = []
            for task_index in range(4):
                path = f'{stage}/PROBE_{index}_OWN_TEXT_{task_index}.json'
                episode = read(path)
                commands = [trace['response']['raw'] for trace in episode['traces'] if trace['kind'] == 'actor']
                memories = [dict(address=trace['address'], response=trace['response'])
                            for trace in episode['traces'] if trace['kind'] == 'memory']
                paths = [[first['port'], second['port']] for first in collection['world']['edges']
                         for second in collection['world']['edges']
                         if first['node'] == episode['task']['node'] and second['node'] == first['outcome']
                         and second['outcome'] == episode['task']['goal']]
                assert len(paths) == 1
                assert paths[0][0] in episode['task']['ports']
                episodes.append(dict(path=path, task_index=task_index, task=episode['task'],
                                     commands=commands, memory_responses=memories,
                                     recorded_reached_goal=episode['reached_goal'],
                                     recorded_terminal=episode['terminal_reason'],
                                     recorded_routes=episode['routes'],
                                     frozen_graph_unique_two_edge_path=paths[0]))
                if index == 14:
                    assert len(commands) == 6 and len(memories) == 4
                    unavailable = [entry for entry in memories if entry['response'] == 'MEMORY UNAVAILABLE']
                    assert unavailable == [dict(address=missing['edge']['event'], response='MEMORY UNAVAILABLE')]
                    assert all(trace.get('error') is None for trace in episode['traces'])
                    assert all(not trace['response']['truncated'] for trace in episode['traces'] if trace['kind'] == 'actor')
            world_report['states'][stage] = dict(saved_pairs=panel['summary']['paired'],
                                                saved_goals=panel['summary']['individual'], episodes=episodes)
            if index == 14:
                commands_by_stage[stage] = [episode['commands'] for episode in episodes]
        worlds.append(world_report)
    assert all(commands == commands_by_stage['baseline0'] for commands in commands_by_stage.values())
    assert commands_by_stage['baseline0'][0] == commands_by_stage['baseline0'][2]
    assert commands_by_stage['baseline0'][1] == commands_by_stage['baseline0'][3]
    report = dict(utc=datetime.now(timezone.utc).isoformat(), author_analysis=True, independent_reader=False,
                  scope='Only preidentified failed world14 and immediately adjacent frozen indices13,15; five existing states',
                  new_model_calls=0, new_evaluations=0, regenerated_worlds=0, changed_labels=0,
                  source_file='collection1/shard7/COLLECTION_08.json', source_collection_sha256=source['collection_sha256'],
                  source_native_call='collection1/CALL_0329.json', source_native_receipt=native,
                  rejected_record=missing, accepted_records=list(accepted.values()),
                  identical_failed_world_command_streams_across_all_five_states=True,
                  commands_unchanged_when_only_goal_changes=True, worlds=worlds, source_file_sha256=hashes,
                  qualification='Static path existence is not a new actor rollout or counterfactual performance measurement')
    with OUTPUT.open('x') as stream:
        json.dump(report, stream, indent=2, sort_keys=True)
        stream.write('\n')
    print('READ_ONLY_MECHANISM_ASSERTIONS_PASS: 3 fixed worlds, 5 saved states, 60 existing episodes; zero new calls/evaluations')


if __name__ == '__main__':
    main()
