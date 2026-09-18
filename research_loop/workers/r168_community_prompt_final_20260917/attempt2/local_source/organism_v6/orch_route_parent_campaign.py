"""Bounded route parenting policy over the released L2 route environment."""

from copy import deepcopy
from itertools import product
from types import FunctionType

from organism_v6 import orch_l2_shared as shared
from organism_v6 import orch_full_rich as rich


INITIAL_STATE = 'd13fabd566e04926f45aa66ee0a30ff7dc88d411430ab3e1fe15dfffeb2fd27f'
INITIAL_FILE = '6f7546d334a6dd65c5a22dddeff2ee6eb42292373d79552df52a272f3aeab76f'
INITIAL_BATCH = '5aac9c13737516146b7a4ed57961beb349c8198778040b36aeaa7eb3d3ea960e'
ROOT = '/tmp/orch_route_parent_campaign_20260915_attempt1'
PREFIX = 'ORCH-ROUTE-PARENT-20260915-'
PRESENTATIONS = 4
ARMS = ('GUIDED', 'UNPARENTED', 'FROZEN')
CAPS = dict(seconds=14400, source_calls=256, child_calls_per_lane=800,
            parent_calls_per_lane=128, updates_per_sleep=64, cycles=2,
            worlds=4, context=8192, generation=512, parent_tokens=192)
CELL = dict(style='training-wheels', horizon='short', tone='supportive-positive',
            provider='existing_claude_cli')
GUIDANCE = 'Use your coach as training wheels; form your own grounded explanation.'
REFLECTION = ('Consolidate this actual experience in your own words. Distinguish '
              'observed success from failure. A failed attempt is evidence of what '
              'went wrong, NOT a correct answer. Explain an evidence-grounded '
              'strategy and uncertainty, without inventing a correct route. '
              'Do not quote the coach or give an action command.')
require = rich.hop.require
digest = rich.digest


def runtime(master):
    require(master.startswith('ORCH-ROUTE-PARENT-20260915-'), 'campaign_namespace')
    namespace = dict(shared.hop.__dict__, MASTER=master, TRANSFER_MASTER=master)
    for name, function in shared.hop.__dict__.items():
        if isinstance(function, FunctionType) and function.__globals__ is shared.hop.__dict__:
            namespace[name] = FunctionType(function.__code__, namespace, name,
                (master,) if name == 'build_world' else function.__defaults__, function.__closure__)
    return namespace


def cohort(exclusions):
    seen = set(exclusions)
    groups = {}
    for kind, count in (('TRAIN', 2), ('HELD', 3)):
        groups[kind.lower()] = []
        for cycle in range(count):
            worlds = []
            for index in range(CAPS['worlds']):
                master = f'{PREFIX}{kind}-C{cycle}-W{index}'
                world = runtime(master)['build_world'](master)
                identifiers = {value for edge in world['edges'] for value in edge.values()}
                require(not identifiers.intersection(seen), 'namespace_collision')
                seen.update(identifiers)
                worlds.append(world)
            groups[kind.lower()].append(worlds)
    if PRESENTATIONS == [4, 16]:
        for group in groups['train']:
            for world in group:
                for task in shared.tasks(world):
                    choices = [edge for edge in world['edges'] if edge['node'] == task['node']]
                    reaching = [first for first in choices if any(second['node'] == first['outcome']
                        and second['outcome'] == task['goal'] for second in world['edges'])]
                    require(len(choices) == 2 and len(reaching) == 1, 'genuine_two_way_route_choice')
    return dict(groups, initial_state=INITIAL_STATE, caps=CAPS, cell=CELL,
                presentations_by_cycle=[presentations_for_cycle(cycle) for cycle in (1, 2)],
                exclusions_sha256=digest(sorted(exclusions)))


def presentations_for_cycle(cycle):
    require(type(cycle) is int and cycle in (1, 2), 'bounded_presentation_cycle')
    return PRESENTATIONS[cycle - 1] if isinstance(PRESENTATIONS, list) else PRESENTATIONS


def validate_initial(receipt):
    require(receipt['arm'] == 'FULL_TARGET' and receipt['seed'] == 7801
            and receipt['trajectory_presentations'] == 4 and receipt['updates'] == 5760
            and receipt['fits'] == 1 and receipt['frozen_base_unchanged'] is True
            and receipt['adapter_state_after'] == INITIAL_STATE
            and receipt['adapter_files']['adapter_model.safetensors'] == INITIAL_FILE
            and receipt['batch_sha256'] == INITIAL_BATCH
            and receipt['loaded_adapter_state_sha256'] ==
                '37ec37884e4b0b679edd1dba1be1dec3474589e992649f3a33e7e3b1ec78b8c0',
            'exact_fixed_lane0_source_required')


def schedule(providers):
    require(all(provider.get('verified') and provider.get('model') for provider in providers),
            'verified_providers_only')
    return [dict(style=style, horizon=horizon, tone=tone, provider=provider)
            for style, horizon, tone, provider in product(
                ('training-wheels', 'micromanaging', 'creative'), ('short', 'long'),
                ('supportive-positive', 'harsh-critical'), providers)]


def parent_payload(payload, cell=None):
    if cell is None:
        cell = CELL
    require(set(payload) == {'kind', 'turn', 'task', 'public_messages',
                            'prior_parent_messages', 'learner'}, 'parent_allowlist')
    require(payload['kind'] == 'coach', 'coach_only')
    text = str(payload)
    require('HELD' not in text and '/tmp/' not in text and 'sealed_score' not in text,
            'no_held_or_paths_to_parent')
    return dict(deepcopy(payload), cell=deepcopy(cell))


def reflection_prefix(record):
    require(type(record['correct']) is bool and record['captures'], 'actual_episode_required')
    evidence = dict(task=record['task'], messages=record['messages'], reads=record['reads'],
        routes=record['routes'], terminal_reason=record['terminal_reason'],
        outcome='SUCCESS' if record['correct'] else 'FAILURE_NOT_CORRECT_ANSWER',
        attempted_actions_are_not_gold=True,
        attempts=[dict(response={key: capture['response'][key] for key in
                  ('raw', 'terminal', 'truncated', 'token_ids') if key in capture['response']}
                  if capture['response'] else None, error=capture['error'])
                  for capture in record['captures']])
    import json

    return [dict(role='system', content=REFLECTION),
            dict(role='user', content=json.dumps(evidence, sort_keys=True))]


def target_gate(raw, private):
    require(isinstance(raw, str) and bool(raw.strip()), 'nonempty_child_reflection')
    for lesson in private:
        require(lesson not in raw, 'teacher_bytes_in_target')
        words = lesson.split()
        require(not any(' '.join(words[start:start + 8]) in ' '.join(raw.split())
                        for start in range(max(0, len(words) - 7))), 'teacher_span_in_target')
    require(not any(line.startswith(('ROUTE ', 'READ EVENT ')) for line in raw.splitlines()),
            'reflection_not_answer_action_replay')
    return True


def next_identity(initial, arm, cycle, previous=None):
    require(arm in ARMS and 1 <= cycle <= CAPS['cycles'], 'arm_cycle')
    if cycle == 1:
        require(previous is None, 'initial_cycle_no_predecessor')
        return initial
    require(previous is not None and previous['status'] == 'COMPLETE'
            and previous['arm'] == arm and previous['cycle'] == cycle - 1
            and previous['phase'] == 'sleep', 'immediate_own_sleep_required')
    result = previous['output_adapter']
    require(result['base_sha256'] == initial['base_sha256'], 'base_drift')
    if arm == 'FROZEN':
        require(result == initial and previous['updates'] == 0, 'frozen_changed')
    return result


def activate(config):
    global ROOT, PREFIX, PRESENTATIONS, CELL, CAPS

    require(set(config) == {'segment', 'root', 'cell', 'presentations', 'initial_state'}, 'exact_segment_config')
    require(config['segment'] in (2, 3, 4) and config['root'] ==
            f'/tmp/orch_route_parent_campaign_20260915_segment{config["segment"]}', 'bounded_segment_root')
    require(config['initial_state'] == INITIAL_STATE, 'same_fixed_route_child_no_score_selection')
    require(config['presentations'] == 16 or (config['segment'] == 3
            and config['presentations'] == [4, 16]), 'declared_next_segment_dose')
    require(set(config['cell']) == set(CELL)
            and config['cell']['style'] in ('training-wheels', 'micromanaging', 'creative')
            and config['cell']['horizon'] in ('short', 'long')
            and config['cell']['tone'] in ('harsh-critical', 'supportive-positive')
            and config['cell']['provider'] in ('existing_claude_cli',
                'claude-haiku-4-5-20251001', 'openai/openai/gpt-6-astra'), 'verified_parent_axes')
    ROOT, PREFIX = config['root'], f'ORCH-ROUTE-PARENT-20260915-SEG{config["segment"]}-'
    PRESENTATIONS, CELL = deepcopy(config['presentations']), deepcopy(config['cell'])
    CAPS = dict(CAPS, updates_per_sleep=256)
