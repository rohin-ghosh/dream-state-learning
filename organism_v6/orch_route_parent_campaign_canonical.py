"""Prospective Rohin102 canonical schedule; historical cohorts stay immutable."""

from collections import Counter
from copy import deepcopy
import json

from organism_v6 import orch_route_parent_campaign as previous
from organism_v6.orch_route_parent_campaign import (
    INITIAL_STATE, INITIAL_FILE, INITIAL_BATCH, GUIDANCE, REFLECTION,
    runtime, validate_initial, reflection_prefix, target_gate, require, digest,
    shared, rich,
)


ROOT = '/tmp/orch_route_parent_campaign_20260915_canonical102'
PREFIX = 'ORCH-ROUTE-PARENT-20260915-CANONICAL102-'
ARMS = ('GUIDED', 'UNPARENTED', 'NO_LORA')
SOURCE_ARM = 'GUIDED'
BASELINE_FIRST = True
RECORD_PARENT_WAIT = True
CAPS = dict(seconds=14400, source_calls=256, child_calls_per_lane=800,
            parent_calls_per_lane=128, updates_per_sleep=112, cycles=8,
            worlds=1, context=8192, generation=512, parent_tokens=192)
CELL = dict(style='training-wheels', horizon='short', tone='supportive-positive',
            provider='openai/openai/gpt-6-astra')
CAMPAIGN_DEADLINE = 1789501022.75119


def presentations_for_cycle(cycle):
    require(type(cycle) is int and 1 <= cycle <= CAPS['cycles'], 'bounded_canonical_cycle')
    return 4 if cycle == 1 else 16


def cohort(exclusions):
    seen = set(exclusions)
    groups = {}
    for kind, count in (('TRAIN', CAPS['cycles']), ('HELD', CAPS['cycles'] + 1)):
        groups[kind.lower()] = []
        for cycle in range(count):
            master = f'{PREFIX}{kind}-C{cycle}-W0'
            world = runtime(master)['build_world'](master)
            identifiers = {value for edge in world['edges'] for value in edge.values()}
            require(not identifiers.intersection(seen), 'namespace_collision')
            seen.update(identifiers)
            tasks = shared.tasks(world)
            require(len(tasks) == 2, 'exactly_two_sequential_episodes')
            for task in tasks:
                choices = [edge for edge in world['edges'] if edge['node'] == task['node']]
                reaching = [first for first in choices if any(second['node'] == first['outcome']
                    and second['outcome'] == task['goal'] for second in world['edges'])]
                require(len(choices) == 2 and len(reaching) == 1, 'genuine_route_choice')
            groups[kind.lower()].append([world])
    return dict(groups, initial_state=INITIAL_STATE, caps=deepcopy(CAPS), cell=deepcopy(CELL),
                presentations_by_cycle=[presentations_for_cycle(cycle) for cycle in range(1, 9)],
                exclusions_sha256=digest(sorted(exclusions)), schema='CANONICAL102_V1',
                control_boundary='NEW_NO_LORA_CONTROL_NOT_HISTORICAL_FROZEN',
                schedule='TWO_SEQUENTIAL_TRAIN_EPISODES_THEN_SLEEP_REHEARSAL_THEN_FRESH_PARENT_FREE_READOUT',
                parent_curriculum='SAME_ORDERED_TRAIN_TASKS_STYLE_PROVIDER; STATE_CONDITIONAL_ADVICE',
                dose_claim='EXPLORATORY_ACROSS_CYCLE_NOT_CLEAN_CAUSAL_CURVE')


def parent_payload(payload):
    projected = previous.parent_payload(payload)
    projected['cell'] = deepcopy(CELL)
    return projected


def next_identity(initial, arm, cycle, previous_receipt=None):
    require(arm in ARMS and 1 <= cycle <= CAPS['cycles'], 'canonical_arm_cycle')
    if cycle == 1:
        require(previous_receipt is None, 'no_first_cycle_predecessor')
        return initial
    require(previous_receipt is not None and previous_receipt['status'] == 'COMPLETE'
            and previous_receipt['arm'] == arm and previous_receipt['cycle'] == cycle - 1
            and previous_receipt['phase'] == 'sleep', 'immediate_same_life_sleep_required')
    child = previous_receipt['output_adapter']
    require(child['base_sha256'] == initial['base_sha256'], 'base_drift')
    if arm == 'NO_LORA':
        require(child == initial and previous_receipt['updates'] == 0
                and previous_receipt.get('fits', 0) == 0, 'no_lora_must_not_update')
    return child


def thinking_metrics(episodes, calls, reflections):
    commands = [str(capture.get('command', '')) for episode in episodes
                for capture in episode.get('captures', [])]
    per_episode = [[str(capture.get('command', '')) for capture in episode.get('captures', [])]
                   for episode in episodes]
    responses = [call['response'] for call in calls if call.get('response') is not None]
    counts = Counter(commands)
    return dict(schema='ROUTE_THINKING_COUNTERS102_V1', episodes=len(episodes),
        calls_attempted=len(calls), calls_with_response=len(responses),
        call_errors=sum(bool(call.get('error')) for call in calls),
        prompt_tokens=sum(response.get('prompt_tokens', 0) for response in responses),
        generated_tokens_including_eos=sum(len(response.get('token_ids', [])) for response in responses),
        generation_wall_seconds=sum(call['finished_unix'] - call['started_unix'] for call in calls
                                    if 'finished_unix' in call and 'started_unix' in call),
        action_attempts=len(commands), unique_action_strings=len(counts),
        distinct_route_sequences=len({tuple(str(route) for route in episode.get('routes', [])) for episode in episodes}),
        rejected_action_attempts=sum(bool(capture.get('error')) for episode in episodes for capture in episode.get('captures', [])),
        repeated_action_strings=sum(max(0, count - 1) for sequence in per_episode for count in Counter(sequence).values()),
        adjacent_repeated_actions=sum(left == right for sequence in per_episode for left, right in zip(sequence, sequence[1:])),
        coherence_proxies=dict(complete_responses=sum(bool(response.get('terminal')) and not response.get('truncated', False) for response in responses),
            reflection_attempts=len(reflections), reflection_admissions=sum(bool(item.get('admitted')) for item in reflections)),
        interpretation='OPERATIONAL_PROXIES_NOT_LATENT_THINKING_OR_REASONING_QUALITY',
        causal_claim=False, parent_visible=False, outcome_driven_scheduling=False)


def record_thinking_metrics(output, episodes, tokenizer):
    del tokenizer
    calls = [json.loads(path.read_text()) for path in sorted(output.glob('CALL_*.json'))]
    reflections = [json.loads(path.read_text()) for path in sorted(output.glob('REFLECTION_*.json'))]
    metrics = thinking_metrics(episodes, calls, reflections)
    request = json.loads((output / 'REQUEST.json').read_text())
    wait_paths = sorted((output.parents[2] / 'parent_queue').glob(f'*_{request["arm"]}_C{request["cycle"]}.WAIT.json')) if output.name == 'experience' else []
    waits = [json.loads(path.read_text()) for path in wait_paths]
    metrics['parent_wait_calls'] = len(waits)
    metrics['parent_wait_seconds'] = sum(wait['elapsed_seconds'] for wait in waits)
    metrics['phase_started_unix'] = request['started_unix']
    with (output / 'THINKING_METRICS.json').open('x') as stream:
        json.dump(metrics, stream, indent=2)
        stream.write('\n')
