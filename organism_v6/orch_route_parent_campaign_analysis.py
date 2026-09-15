"""Descriptive matched-route evidence reduction; never a parent input."""

from collections import Counter
import json
from pathlib import Path

from organism_v6 import orch_route_parent_campaign as policy
from organism_v6.orch_guided_bridge import file_sha256


def read(path):
    return json.loads(Path(path).read_text())


def fraction(numerator, denominator, unit):
    return dict(numerator=numerator, denominator=denominator, unit=unit)


def episode_metrics(records):
    calls = [capture for record in records for capture in record['captures']]
    responses = [capture['response'] for capture in calls if capture.get('response') is not None]
    reads = [address for record in records for address in record['reads']]
    unavailable = sum(message['role'] == 'user' and message['content'] == policy.rich.readout.UNAVAILABLE
                      for record in records for message in record['messages'])
    return dict(
        outcomes=fraction(sum(record['correct'] for record in records), len(records), 'episodes'),
        paired_both_correct=fraction(sum(records[index]['correct'] and records[index + 1]['correct']
            for index in range(0, len(records), 2)), len(records) // 2, 'worlds_with_opposite_goals'),
        actor_capture_errors=fraction(sum(capture.get('error') is not None for capture in calls), len(calls), 'actor_calls'),
        capture_error_types=dict(Counter((capture['error'].get('type', 'unknown') + ':' +
            capture['error'].get('message', 'unknown')) for capture in calls if capture.get('error') is not None)),
        missing_responses=fraction(len(calls) - len(responses), len(calls), 'actor_calls'),
        truncated_responses=fraction(sum(response.get('truncated') is True for response in responses), len(responses), 'returned_responses'),
        unterminated_responses=fraction(sum(response.get('terminal') is not True for response in responses), len(responses), 'returned_responses'),
        terminal_reasons=dict(Counter(record['terminal_reason'] for record in records)),
        reads=fraction(len(reads), len(records), 'episodes'),
        unavailable_event_reads=fraction(unavailable, len(reads), 'successful_READ_commands'),
        distinct_events_read=len(set(reads)),
        first_action_types=dict(Counter((record['captures'][0].get('command') or 'MISSING').split()[0]
                                        for record in records)),
        route_actions=fraction(sum(len(record['routes']) for record in records), len(records), 'episodes'),
        capture_calls=len(calls),
        legacy_parametric_memory_retention='NOT_MEASURED_BY_THIS_ROUTE_READOUT; external event retrieval is reported separately')


def phase(root, arm, cycle, name):
    folder = root / arm / f'cycle{cycle}' / name
    complete_path = folder / 'COMPLETE.json'
    if not complete_path.exists():
        return dict(status='PENDING', denominator=8, arm=arm, cycle=cycle, phase=name)
    complete = read(complete_path)
    policy.require(complete['status'] == 'COMPLETE' and complete['arm'] == arm
                   and complete['cycle'] == cycle and complete['phase'] == name, 'phase_identity')
    paths = sorted(folder.glob('EPISODE_*.json'))
    records = [read(path) for path in paths]
    policy.require(len(records) == complete['episodes'] == 8, 'exact_eight_episode_denominator')
    loaded = read(folder / 'LOADED.json')
    policy.require(loaded['observed'] == complete['input_adapter'] and loaded['process'] == complete['process'],
                   'actual_loaded_identity')
    if name == 'readout':
        policy.require(complete['parent_free'] is True and loaded['parent_present'] is False
                       and all(not record['parent_messages'] for record in records), 'parent_free_readout')
        if cycle:
            previous = read(root / arm / f'cycle{cycle}/sleep/COMPLETE.json')
            policy.require(previous['output_adapter'] == complete['input_adapter']
                           and previous['process'] != complete['process'], 'saved_sleep_to_fresh_process')
    return dict(status='COMPLETE', arm=arm, cycle=cycle, phase=name, metrics=episode_metrics(records),
        input_adapter=complete['input_adapter'], process=complete['process'],
        complete_sha256=file_sha256(complete_path), episode_sha256=[file_sha256(path) for path in paths],
        tasks=[record['task'] for record in records], parent_free=name == 'readout',
        completed_unix=complete['finished_unix'])


def projection(root, arm, cycle):
    folder = root / arm / f'cycle{cycle}/experience'
    reflections = [read(path) for path in sorted(folder.glob('REFLECTION_*.json'))]
    if not (folder / 'COMPLETE.json').exists():
        return dict(status='PENDING', recorded_reflections=len(reflections), intended_episode_denominator=8)
    policy.require(len(reflections) == 8, 'all_consolidation_attempts_retained')
    records = [read(path) for path in sorted(folder.glob('EPISODE_*.json'))]
    strata = {}
    for outcome in (False, True):
        selected = [reflection for reflection, record in zip(reflections, records) if record['correct'] is outcome]
        strata['successful' if outcome else 'failed'] = dict(
            offered=fraction(len(selected), sum(record['correct'] is outcome for record in records), 'experienced_episodes'),
            original_admitted=fraction(sum(item.get('admitted') is True for item in selected), len(selected), 'consolidation_attempts'))
    result = dict(status='COMPLETE', attempted=fraction(len(reflections), 8, 'experienced_episodes'), outcome_strata=strata,
        original_admitted=fraction(sum(item.get('admitted') is True for item in reflections), 8, 'consolidation_attempts'),
        original_rejections=dict(Counter(item.get('error', 'unspecified') for item in reflections if not item.get('admitted'))),
        raw_response_missing=fraction(sum(item.get('response') is None for item in reflections), 8, 'consolidation_attempts'),
        raw_response_incomplete=fraction(sum(item.get('response') is not None and
            (not item['response'].get('terminal') or item['response'].get('truncated')) for item in reflections), 8, 'consolidation_attempts'))
    sleep = root / arm / f'cycle{cycle}/sleep'
    if (sleep / 'REPLAY_REPROJECTION.json').exists():
        replay = read(sleep / 'REPLAY_REPROJECTION.json')
        result['reprojection'] = dict(candidates=fraction(replay['candidates'], len(replay['dispositions']), 'original_reflection_attempts'),
            failures=dict(Counter(item.get('error') for item in replay['dispositions'] if not item.get('candidate'))),
            model_calls=replay['model_calls'], provenance_sha256=file_sha256(sleep / 'REPLAY_REPROJECTION.json'))
    if (sleep / 'COMPLETE.json').exists():
        complete = read(sleep / 'COMPLETE.json')
        result['actual_sleep'] = dict(updates=complete['updates'], fits=complete['fits'],
            reflection_targets=complete.get('reflection_targets', 0),
            output_state=complete['output_adapter']['state_sha256'], complete_sha256=file_sha256(sleep / 'COMPLETE.json'))
    return result


def reduce(root):
    root = Path(root)
    cohort = read(root / 'COHORT.json')
    source = read(root / 'SOURCE.json')
    policy.require(source['cohort_sha256'] == policy.digest(cohort), 'frozen_cohort_source_join')
    records = [record for collection in source['collections'] for record in collection['records']]
    tests = {str(cycle): {arm: phase(root, arm, cycle, 'readout') for arm in policy.ARMS} for cycle in (0, 1, 2)}
    for cycle, arms in tests.items():
        complete = [result for result in arms.values() if result['status'] == 'COMPLETE']
        expected = [task for world in cohort['held'][int(cycle)] for task in policy.shared.tasks(world)]
        policy.require(all(result['tasks'] == expected for result in complete), 'prospective_same_held_tasks')
        policy.require(len({tuple(result['process']) for result in complete}) == len(complete), 'distinct_readout_processes')
        if cycle == '0':
            policy.require(all(result['input_adapter']['state_sha256'] == policy.INITIAL_STATE for result in complete),
                           'same_initial_child_controls')
    lineage = {}
    for arm in policy.ARMS:
        current = phase(root, arm, 2, 'experience')
        if current['status'] == 'COMPLETE':
            previous_path = root / arm / 'cycle1/sleep/COMPLETE.json'
            previous = read(previous_path)
            policy.require(current['input_adapter'] == previous['output_adapter'], 'taught_to_next_cycle_loaded_child')
            current['previous_sleep_sha256'] = file_sha256(previous_path)
            current['previous_parent_response_sha256'] = {path.name: file_sha256(path) for path in
                sorted((root / 'parent_queue').glob(f'*_{arm}_C1.response.json'))}
        lineage[arm] = current
    return dict(schema='ROUTE_PARENT_MATCHED_READOUT_DESCRIPTIVE_V1', parent_input_allowed=False,
        held_selection_or_dispatch_decisions=False, cohort_sha256=policy.digest(cohort),
        source_inventory=dict(worlds=len(source['collections']), events=fraction(sum(record['accepted'] for record in records), len(records), 'attempted_source_events'),
                              failures=fraction(sum(not record['accepted'] for record in records), len(records), 'attempted_source_events')),
        tests=tests, projections={arm: projection(root, arm, 1) for arm in policy.ARMS},
        cycle2_projections={arm: projection(root, arm, 2) for arm in policy.ARMS},
        taught_cycle1_to_actual_cycle2=lineage,
        limitations=['C0 and C1 use distinct prospectively frozen held worlds; only within-stage arms share tasks.',
            'Eight goal episodes form four paired worlds, not eight independent worlds.',
            'GUIDED/UNPARENTED C1 update counts 40/32 reflect different admitted yields; no pure-content causal claim.',
            'Original guided reflection prompts included nested private metadata; repaired neutral projections retain exact original targets without regeneration.',
            'No legacy parametric memory retention test was run; route READ retrieval failures are a separate measure.',
            'All outputs remain descriptive; no provider choice or native intervention depends on held outcomes.'])
