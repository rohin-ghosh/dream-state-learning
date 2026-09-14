"""Replay all four native shards and reduce the prospectively frozen Taxi screen."""

import argparse
import builtins
from collections import Counter
import json
from pathlib import Path

from gpu import orch_game_run as runner
from organism_v6 import orch_game_screen as screen


def reduce(root, bank_path):
    bank = runner.bank_from(bank_path)
    episodes, captures, files, runtimes = [], [], {}, []
    for shard in range(4):
        output = root / f'shard{shard}'
        if (output / 'exit_code.txt').read_text().strip() != '0':
            raise ValueError('all_guardians_must_exit_successfully')
        native = output / 'screen'
        result = json.loads((native / 'RESULT.json').read_text())
        if result['status'] != 'COMPLETE' or result['fits'] or result['updates'] or result['fit_ready']:
            raise ValueError('four_complete_inference_only_results_required')
        if result['adapter_before'] != result['adapter_after'] or not result['frozen_base_unchanged']:
            raise ValueError('readonly_state_required')
        loaded = json.loads((native / 'LOADED.json').read_text())
        if loaded['adapter_state'] != '37ec37884e4b0b679edd1dba1be1dec3474589e992649f3a33e7e3b1ec78b8c0':
            raise ValueError('declared_portable_actor_required')
        if runtimes and loaded['source_sha256'] != runtimes[0]['source_sha256']:
            raise ValueError('same_frozen_source_required')
        runtimes.append(loaded)
        calls = [json.loads(path.read_text()) for path in sorted(native.glob('CALL_*.json'))]
        if len(calls) != result['model_calls'] or len(calls) > 48:
            raise ValueError('native_call_count_mismatch')
        cursor = 0

        def generate(messages):
            nonlocal cursor
            call = calls[cursor]
            cursor += 1
            if call['messages'] != messages:
                raise ValueError('raw_native_prompt_join_mismatch')
            if call['error']:
                error_type = getattr(builtins, call['error']['type'])
                raise error_type(call['error']['message'])
            return call['response']

        for entry in result['episodes']:
            replayed = screen.episode(bank, entry['instance'], entry['arm'], generate,
                                      lambda turn, record: None)
            if replayed != entry:
                raise ValueError('deterministic_episode_replay_mismatch')
        if cursor != len(calls):
            raise ValueError('unaccounted_native_calls')
        episodes.extend(result['episodes'])
        captures.extend(calls)
        for path in output.rglob('*'):
            if path.is_file():
                files[str(path.relative_to(root))] = runner.file_hash(path)
    expected = [instance['id'] for instance in bank['instances'] if instance['split'] == 'mining']
    result = screen.summarize(episodes, expected)
    responses = [call['response'] for call in captures if call['response'] is not None]
    result.update(native_model_calls=len(captures), max_context_tokens=max(row['prompt_tokens'] for row in responses),
                  reducer_sha256=runner.file_hash(__file__),
                  max_generated_tokens=max(len(row['token_ids']) for row in responses),
                  source_archive_sha256=runtimes[0]['source_sha256'],
                  evidence_files_sha256=screen.digest(files), evidence_files=files,
                  node='A100', native_root='/tmp/orch_game_20260914_attempt1',
                  physical_gpu_indices=[0, 1, 2, 3], runtime_bindings=runtimes,
                  bank_sha256=runner.BANK_SHA, all_episodes_replayed=True,
                  old_facts_readout='NOT_RUN_NO_FIT', held_l1_readout='NOT_RUN_POOL_SCREEN_ONLY',
                  scope='WITHIN_TAXI_DESTINATION_SPLITS_NOT_UNSEEN_ENVIRONMENT', families={})
    for family in sorted({entry['instance']['family'] for entry in episodes}):
        selected = [entry for entry in episodes if entry['instance']['family'] == family]
        result['families'][family] = {arm: dict(episodes=8,
            successes=sum(entry['success'] for entry in selected if entry['arm'] == arm)) for arm in ('RICH', 'TERSE')}
    result['arms'] = {}
    for arm in ('RICH', 'TERSE'):
        turns = [turn for entry in episodes if entry['arm'] == arm for turn in entry['turns']]
        lengths = [len(turn['response']['token_ids']) for turn in turns if turn['response']]
        result['arms'][arm] = dict(attempted_episodes=16, attempted_turns=len(turns),
            generated_token_lengths=lengths,
            desired_150_400_count=sum(150 <= count <= 400 for count in lengths),
            format_pass=sum(turn['format_pass'] for turn in turns),
            errors=dict(Counter(turn['error']['message'] for turn in turns if turn['error'])),
            outcome_qualified_episodes=sum(entry['success'] and all(turn['format_pass'] for turn in entry['turns'])
                                           for entry in episodes if entry['arm'] == arm))
    return result, episodes


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', required=True)
    parser.add_argument('--bank', required=True)
    parser.add_argument('--output', required=True)
    parser.add_argument('--review-packets', required=True)
    options = parser.parse_args()
    result, episodes = reduce(Path(options.root), options.bank)
    runner.write(options.output, result)
    packets = [dict(instance=entry['instance'], success=entry['success'], turns=entry['turns'],
                    status='UNREVIEWED_NO_ADMISSION') for entry in episodes if entry['arm'] == 'RICH']
    runner.write(options.review_packets, packets)
    print(json.dumps({key: value for key, value in result.items()
                     if key not in ('evidence_files', 'runtime_bindings', 'arms')}, sort_keys=True))


if __name__ == '__main__':
    main()
