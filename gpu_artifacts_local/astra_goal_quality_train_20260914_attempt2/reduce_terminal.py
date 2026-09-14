import hashlib
import json
import math
import sys
from collections import Counter, defaultdict
from pathlib import Path
from types import SimpleNamespace

capsule = Path(__file__).resolve().parent.parent / 'astra_goal_quality_train_terminal_20260914_attempt2'
root = capsule / 'extracted/astra_goal_quality_train_20260914_attempt2'
sys.path.insert(0, str(root / 'source'))
from gpu import astra_goal_quality_train as driver


def read(path):
    return json.loads(path.read_text())


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify_files(directory, files):
    for name, expected in files.items():
        assert digest(directory / name) == expected, str(directory / name)


baseline = read(root / 'baseline/RESULT.json')
baseline_hash = digest(root / 'baseline/RESULT.json')
assert baseline_hash == 'c2fe5b4735ea7252fff27e7ea777093e798df882f57262ab0391ad91b6b671a2'
assert (baseline['primary']['correct'], baseline['primary']['individual']['correct']) == (2, 33)
assert (root / 'source_commit.txt').read_text().strip() == '7f9d4251ae1ff4c5ff9138adf267d081fffa6331'
assert digest(root / 'source' / driver.PROTOCOL_PATH) == driver.PROTOCOL_SHA
assert not list(root.rglob('FAILED.json'))
assert not list(root.rglob('GUARD_ABORT.txt'))
states = {}
training = {}
full_reference = read(root / 'FULL_TARGET/train/REFERENCE_MASKS.json')
full_rows = read(root / 'FULL_TARGET/train/TRAINING_ROWS.json')
assert [len(full_rows[key]) for key in driver.GROUPS] == [128, 20, 62, 12, 1452]
assert all('TRAIN' in row['master'] and 'PROBE' not in row['master'] for row in full_rows['new_trajectory_rows'])
for arm in driver.ARMS:
    directory = root / arm / 'train'
    receipt = read(directory / 'RESULT.json')
    assert receipt['status'] == 'COMPLETE' and receipt['fits'] == 1 and receipt['updates'] == 2928
    assert receipt['loaded_adapter_state_sha256'] == driver.PARENT_STATE
    assert receipt['binding'] == baseline['binding']
    assert receipt['baseline_contract_sha256'] == driver.goal.document_sha256(baseline['binding']['readout'])
    assert receipt['model_calls'] == 0 and receipt['seed'] == 0 and receipt['frozen_base_unchanged'] is True
    verify_files(directory, receipt['training_files'])
    verify_files(directory / 'adapter', receipt['adapter_files'])
    assert read(directory / 'TRAINING_ROWS.json') == full_rows
    assert read(directory / 'REFERENCE_MASKS.json') == full_reference
    recipe = read(directory / 'RECIPE.json')
    assert recipe == json.loads(json.dumps(driver.recipe(arm, 0)))
    masks = read(directory / 'MASKS.json')
    dose = read(directory / 'DOSE.json')
    logs = [json.loads(line) for line in (directory / 'LOSSES.jsonl').read_text().splitlines()]
    assert len(masks) == 1674 and len(logs) == 2928
    for index, (reference, controlled) in enumerate(zip(full_reference, masks)):
        assert reference['input_ids'] == controlled['input_ids']
        assert reference['target_ids'] == controlled['target_ids']
        expected = [-100] * len(reference['labels']) if arm == 'NEW_TRAJECTORY_LOSS_OFF' and index >= 222 else reference['labels']
        assert controlled['labels'] == expected
    presentations = Counter()
    active_total = reference_total = input_total = 0
    for offset, (batch, log) in enumerate(zip(dose['batches'], logs)):
        indexes = [offset % 128, 128 + offset % 82, 210 + (2 * offset) % 1464, 210 + (2 * offset + 1) % 1464]
        reference_count = sum(sum(token != -100 for token in full_reference[index]['labels'][1:]) for index in indexes)
        active_count = sum(sum(token != -100 for token in masks[index]['labels'][1:]) for index in indexes)
        expected = dict(update=offset + 1, row_indexes=indexes, reference_labels=reference_count,
                        active_labels=active_count, loss_scale=active_count / reference_count)
        assert batch == expected
        assert all(log[key] == value for key, value in expected.items())
        assert math.isfinite(log['loss']) and math.isclose(log['loss'], log['mean_loss'] * expected['loss_scale'], rel_tol=2e-7)
        presentations.update(indexes)
        active_total += active_count
        reference_total += reference_count
        input_total += sum(len(full_reference[index]['input_ids']) for index in indexes)
    assert all(presentations[index] == 4 for index in range(210, 1674))
    assert active_total == dose['actual_supervised_tokens'] == receipt['actual_supervised_tokens']
    assert reference_total == dose['reference_supervised_tokens'] == receipt['reference_supervised_tokens']
    assert read(directory / 'STATES.json') == dict(before=driver.PARENT_STATE, after=receipt['adapter_state_after'])
    training[arm] = dict(result_sha256=digest(directory / 'RESULT.json'), state=receipt['adapter_state_after'],
        updates=2928, active_labels=active_total, reference_labels=reference_total,
        input_token_presentations=input_total, old_memory_presentations=sum(presentations[index] for index in range(128)),
        old_behavior_presentations=sum(presentations[index] for index in range(128, 210)),
        old_trajectory_presentations=sum(presentations[index] for index in range(210, 222)),
        new_trajectory_presentations=sum(presentations[index] for index in range(222, 1674)),
        started_unix=receipt['started_unix'], finished_unix=receipt['finished_unix'],
        assigned_seconds=receipt['gpu_assigned_wall_seconds'], fit_seconds=logs[-1]['fit_elapsed_seconds'],
        adapter_files=receipt['adapter_files'])

shared_tasks = {}
shared_stores = defaultdict(dict)
taskwise = []
all_call_count = 0
after_replayed_episodes = 0
for state_name, relative in [('BASELINE', 'baseline'), ('FULL_TARGET', 'FULL_TARGET/after'),
                             ('NEW_TRAJECTORY_LOSS_OFF', 'NEW_TRAJECTORY_LOSS_OFF/after')]:
    directory = root / relative
    receipt = read(directory / 'RESULT.json')
    assert receipt['status'] == 'COMPLETE' and receipt['updates'] == receipt['fits'] == 0
    assert receipt['binding'] == baseline['binding'] and receipt['runtime'] == baseline['runtime']
    assert receipt['trainingAllowed'] is False and receipt['frozen_base_unchanged'] is True
    expected_state = driver.PARENT_STATE if state_name == 'BASELINE' else training[state_name]['state']
    assert receipt['loaded_adapter_state_sha256'] == receipt['adapter_state_after'] == expected_state
    assert read(directory / 'STATES.json') == dict(before=expected_state, after=expected_state)
    if state_name != 'BASELINE':
        assert receipt['training_result_sha256'] == training[state_name]['result_sha256']
        assert receipt['baseline_result_sha256'] == baseline_hash
    verify_files(directory, receipt['output_files'])
    assert set(receipt['output_files']) == {path.name for path in directory.glob('*.json') if path.name != 'RESULT.json'}
    calls = [read(path) for path in sorted(directory.glob('CALL_*.json'))]
    assert len(calls) == receipt['model_calls'] <= 960
    assert [call['call_index'] for call in calls] == list(range(len(calls)))
    assert all(call['error'] is None and call['response']['messages'] == call['messages'] for call in calls)
    assert sum(len(call['response']['token_ids']) for call in calls) == receipt['generated_tokens']
    all_call_count += len(calls)
    grouped = defaultdict(list)
    for call in calls:
        grouped[(call['graph'], call['master'], call['condition'], call['task_index'])].append(call)
    aggregates = {}
    world_results = []
    checked_calls = 0
    for split in ('TRAIN', 'PROBE'):
        for panel in receipt['panels'][split]:
            runtime = SimpleNamespace(**driver.goal.runtime(panel['shard']))
            world = runtime.build_world(panel['master'])
            world_index = panel['shard'] if split == 'TRAIN' else 2 * panel['shard'] + runtime.PROBE_MASTERS.index(panel['master'])
            episodes = [read(directory / f'{split}_{world_index}_{panel["condition"]}_{index}.json') for index in range(4)]
            if state_name != 'BASELINE':
                assert driver.summarize_world(dict(world=world), episodes, runtime) == panel['summary']
                after_replayed_episodes += 4
            scores = panel['summary']['scores']
            pairs = panel['summary']['pairs']
            assert panel['summary']['individual'] == dict(correct=sum(score['correct'] for score in scores), denominator=4)
            assert panel['summary']['paired'] == dict(correct=sum(pair['correct'] for pair in pairs), denominator=2)
            key = split + '_' + panel['condition']
            aggregate = aggregates.setdefault(key, dict(goals=0, pairs=0, worlds_with_pair=0, terminal=Counter(), failures=Counter(), reads=0, actor_calls=0, routes=0, unavailable_reads=0))
            aggregate['goals'] += sum(score['correct'] for score in scores)
            aggregate['pairs'] += sum(pair['correct'] for pair in pairs)
            aggregate['worlds_with_pair'] += any(pair['correct'] for pair in pairs)
            for index, (episode, task, score) in enumerate(zip(episodes, panel['tasks'], scores)):
                identity = (split, panel['master'], index)
                if identity in shared_tasks:
                    assert shared_tasks[identity] == episode['task']
                shared_tasks[identity] = episode['task']
                traces = [trace for trace in episode['traces'] if trace['kind'] == 'actor']
                native = grouped[(split, panel['master'], panel['condition'], index)]
                assert len(traces) == len(native) == episode['actor_calls']
                for trace, call in zip(traces, native):
                    assert trace['messages'] == call['messages'] and trace['response'] == call['response']
                checked_calls += len(native)
                memories = [trace for trace in episode['traces'] if trace['kind'] == 'memory']
                for trace in memories:
                    if panel['condition'] == 'UNAVAILABLE':
                        assert trace['response'] == 'MEMORY UNAVAILABLE'
                    else:
                        store = shared_stores[panel['master']]
                        if trace['address'] in store:
                            assert store[trace['address']] == trace['response']
                        store[trace['address']] = trace['response']
                aggregate['terminal'][episode['terminal_reason']] += 1
                aggregate['failures'][task['failure'] or 'correct'] += 1
                aggregate['reads'] += episode['memory_calls']
                aggregate['actor_calls'] += episode['actor_calls']
                aggregate['routes'] += len(episode['routes'])
                aggregate['unavailable_reads'] += sum(trace['response'] == 'MEMORY UNAVAILABLE' for trace in memories)
                taskwise.append(dict(state=state_name, split=split, master=panel['master'], condition=panel['condition'],
                    correct=score['correct'], **task))
            world_results.append(dict(split=split, master=panel['master'], condition=panel['condition'],
                goals=panel['summary']['individual']['correct'], pairs=panel['summary']['paired']['correct'],
                task_correct=[score['correct'] for score in scores]))
    assert aggregates['PROBE_OWN_TEXT']['pairs'] == receipt['primary']['correct']
    assert aggregates['PROBE_OWN_TEXT']['goals'] == receipt['primary']['individual']['correct']
    assert len([panel for panel in receipt['panels']['PROBE'] if panel['condition'] == 'OWN_TEXT']) == 16
    states[state_name] = dict(result_sha256=digest(directory / 'RESULT.json'), state=expected_state,
        metrics=aggregates, worlds=world_results, old_recall=receipt['old_recall'], audit=receipt['held_audit']['overall'],
        taught={key:receipt['taught_graph']['OWN_TEXT'][key] for key in ('correct', 'denominator')},
        previous_fresh={key:receipt['previous_fresh_graph']['OWN_TEXT'][key] for key in ('correct', 'denominator')},
        engineering_checks=receipt['engineering_checks'], engineering_target_met=receipt['engineering_target_met'],
        calls=len(calls), goal_native_calls_matched=checked_calls, role_calls=receipt['role_calls'],
        generated_tokens=receipt['generated_tokens'], prompt_tokens=sum(call['response']['prompt_tokens'] for call in calls),
        assigned_seconds=receipt['gpu_assigned_wall_seconds'], started_unix=receipt['started_unix'], finished_unix=receipt['finished_unix'],
        first_port_reference=dict(goals=sum(item['summary']['individual']['correct'] for item in receipt['deterministic_first_port']),
                                  pairs=sum(item['summary']['paired']['correct'] for item in receipt['deterministic_first_port'])))

for master, store in shared_stores.items():
    assert len(store) == 4
assert sum(value == 'MEMORY UNAVAILABLE' for store in shared_stores.values() for value in store.values()) == 1
release = {str(index): read(capsule / f'release_gpu{index}.json') for index in (0, 1)}
assert all(report['clear'] and not report['owners'] and not report['unresolved'] and not report['compute_apps'] for report in release.values())
reduction = dict(schema='QUALITY_ATTEMPT2_TERMINAL_REDUCTION_V1', source_commit=(root/'source_commit.txt').read_text().strip(),
    protocol_sha256=driver.PROTOCOL_SHA, archive_sha256=read(capsule/'preservation.json')['archive_sha256'],
    baseline_sha256=baseline_hash, baseline_warning='SELECTED_944_CALL_BASELINE_33_OF_64_GOALS_2_OF_32_PAIRS_NOT_LEGACY_0_OF_4',
    training=training, states=states, taskwise=taskwise, shared_read_stores=shared_stores,
    checks=dict(all_receipt_inventory_hashes=True, matched_rows_reference_inputs_schedule=True,
                only_new_labels_masked=True, common_reference_denominator=True, saved_state_joins=True,
                frozen_base_receipt_attestations=True, same_readout_bindings_and_runtime=True,
                after_episodes_replayed=after_replayed_episodes, native_goal_trace_matches=True,
                all_call_files_verified=all_call_count, baseline_replayed_again=False,
                tokenizer_or_model_loaded=False, physical_and_cvd_release=True),
    incremental_primary_observed=states['FULL_TARGET']['metrics']['PROBE_OWN_TEXT']['pairs'] > max(
        states[name]['metrics']['PROBE_OWN_TEXT']['pairs'] for name in ('BASELINE','NEW_TRAJECTORY_LOSS_OFF')),
    engineering_target_met=states['FULL_TARGET']['engineering_target_met'], release=release)
with (capsule/'REDUCTION.json').open('x') as stream:
    json.dump(reduction,stream,indent=2,sort_keys=True)
print(json.dumps({key:value for key,value in reduction.items() if key not in ('taskwise','shared_read_stores','release','states')},indent=2))
for state_name,state in states.items():
    print(state_name,json.dumps({key:state[key] for key in ('metrics','old_recall','audit','taught','previous_fresh','engineering_checks','calls','generated_tokens','prompt_tokens','assigned_seconds','first_port_reference')},sort_keys=True))
