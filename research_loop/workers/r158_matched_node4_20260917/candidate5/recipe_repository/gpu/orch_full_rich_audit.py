"""Author CPU replay of immutable native captures; never loads a model."""

import argparse
import builtins
from copy import deepcopy
from pathlib import Path

from gpu import orch_full_rich as runner
from organism_v6 import orch_full_rich as screen


def replay_episode(world, task, record, calls):
    consumed = []

    def generate(messages):
        call = next(calls)
        if call['messages'] != messages:
            raise AssertionError('native_prompt_replay_drift')
        consumed.append(call)
        if call['error']:
            name = call['error']['type']
            if name not in ('ValueError', 'RuntimeError', 'TimeoutError'):
                raise AssertionError('unrecognized_native_error_requires_review')
            raise getattr(builtins, name)(call['error']['message'])
        response = deepcopy(call['response'])
        if response['generated_text_tokens'] != len(response['token_ids']) - int(response['terminal']):
            raise AssertionError('actual_generated_token_count_drift')
        return response

    replayed = screen.episode(world, task, generate, record['store'])
    original = {key: value for key, value in record['episode'].items()
                if key not in ('state', 'world_index', 'goal_index')}
    if replayed != original:
        raise AssertionError('complete_episode_replay_drift')
    return consumed


def audit(root):
    source = runner.source
    prepared = source.read(root / 'prepare/PREPARE.json')
    frozen = source.read(root / 'prepare/COHORT.json')
    for module in (screen, screen.hop, screen.readout, runner):
        path = Path(module.__file__).resolve()
        relative = '/'.join(path.parts[-2:])
        if source.file_hash(path) != prepared['helper_hashes'][relative]:
            raise AssertionError('author_replay_runtime_source_drift:' + relative)
    document = source.read(root / 'collection/SOURCE.json')
    store = screen.verify_source(frozen, document)
    collection_calls = [source.read(path) for path in sorted((root / 'collection').glob('CALL_*.json'))]
    flattened = [capture for collection in document['collections'] for capture in collection['captures']]
    if len(collection_calls) != len(flattened) or len(flattened) > screen.SOURCE_CAP:
        raise AssertionError('source_call_denominator')
    for call, capture in zip(collection_calls, flattened):
        if any(call[key] != capture[key] for key in ('messages', 'response', 'error')):
            raise AssertionError('source_capture_join_drift')
    states = {}
    for state in screen.STATES:
        calls_list = [source.read(path) for path in sorted((root / state).glob('CALL_*.json'))]
        iterator = iter(calls_list)
        consumed = []
        for world_index, world in enumerate(frozen['worlds']):
            for goal_index, task in enumerate(screen.tasks(world)):
                episode = source.read(root / state / f'EPISODE_{world_index:02d}_{goal_index}.json')
                consumed.extend(replay_episode(world, task, dict(episode=episode, store=store), iterator))
        if next(iterator, None) is not None or consumed != calls_list or len(calls_list) > screen.TRAJECTORY_CAP:
            raise AssertionError('unaccounted_trajectory_calls')
        terminal = source.read(root / state / 'RESULT.json')
        if (terminal['status'] != 'COMPLETE' or terminal['model_calls'] != sum(call['engine_invoked'] for call in calls_list)
                or not terminal['frozen_base_unchanged']):
            raise AssertionError('native_state_or_call_accounting')
        if not terminal['adapter_state_before'] == terminal['adapter_state_after'] == runner.STATES[state]:
            raise AssertionError('mounted_state_hash_mismatch')
        states[state] = dict(replayed_episodes=16, attempted_calls=len(calls_list),
                             model_calls=terminal['model_calls'], exact_capture_join=True)
    return dict(status='PASS', role='AUTHOR_CPU_AUDIT_NOT_INDEPENDENT_READER', model_calls_added=0,
                replayed_episodes=48, source_calls=len(collection_calls), states=states,
                store_sha256=screen.digest(store), source_commit=prepared['source_commit'])


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    options = parser.parse_args()
    runner.write(options.output, audit(options.root))


if __name__ == '__main__':
    main()
