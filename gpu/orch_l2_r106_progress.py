"""Bounded offline late-cycle audit; no inference, training or parent inputs."""

import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
from pathlib import Path
import re
from statistics import mean


LANES = ('campaign_03_r102_micro5', 'campaign_04_r102_creative7',
         'campaign_05_r104_training4')


def load_helper(name):
    specification = importlib.util.spec_from_file_location(name, Path(__file__).with_name(name + '.py'))
    helper = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(helper)
    return helper


def read(path):
    return json.loads(path.read_text())


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def call_metrics(path):
    call = read(path)
    response = call.get('response')
    result = dict(path=str(path), sha256=sha(path), task_id=call['task_id'],
                  purpose=call['purpose'], response_available=response is not None)
    if response is None:
        return result
    words = re.findall(r'\w+', response['raw'].lower())
    grams = [tuple(words[index:index + 4]) for index in range(max(0, len(words) - 3))]
    repeats = sum(count - 1 for count in Counter(grams).values())
    result.update(generated_tokens=len(response['token_ids']), includes_terminal_eos=True,
        truncated=response['truncated'], lexical_repeated_fourgram_rate=repeats / len(grams) if grams else 0,
        system_prompt_sha256=hashlib.sha256(call['messages'][0]['content'].encode()).hexdigest(),
        prompt_requests_check=bool(re.search(r'\bcheck\b', call['messages'][1]['content'], re.I)),
        generation_seconds=call['finished_unix'] - call['started_unix'])
    return result


def summarize(root):
    evidence = load_helper('orch_math_pipeline_l2_evidence')
    measure = load_helper('orch_math_pipeline_l2_measure')
    emitted = measure.observe(root, set(LANES))
    report = dict(measured_utc=datetime.now(timezone.utc).isoformat(), native_calls=0,
        parent_calls=0, raw_text_included=False, parent_may_read=False,
        source_sha256=sha(Path(__file__)),
        helper_hashes={name: sha(Path(__file__).with_name(name + '.py'))
                      for name in ('orch_math_pipeline_l2_evidence', 'orch_math_pipeline_l2_measure')},
        newly_emitted_joins=[dict(path=path, sha256=sha(Path(path))) for path in emitted], lanes={})
    for name in LANES:
        campaign = root / name
        cycles = []
        for number in range(1, 9):
            cycle = campaign / 'GUIDED_SLEEP' / f'cycle{number}'
            experience = cycle / 'experience'
            readout = cycle / 'readout'
            if not (readout / 'COMPLETE.json').exists():
                continue
            terminal = read(readout / 'COMPLETE.json')
            learned = read(experience / 'COMPLETE.json')
            loaded = read(readout / 'LOADED.json')
            after = read(readout / 'AFTER.json')
            assert terminal['status'] == learned['status'] == 'COMPLETE'
            assert terminal['parent_present'] is False and terminal['updates'] == 0
            assert terminal['input_adapter']['state_sha256'] == learned['output_adapter']['state_sha256']
            assert terminal['output_adapter']['state_sha256'] == terminal['input_adapter']['state_sha256']
            assert terminal['process'] != learned['process']
            assert loaded['process'] == after['process'] == terminal['process']
            assert loaded['observed']['state_sha256'] == terminal['input_adapter']['state_sha256']
            assert after['output_adapter']['state_sha256'] == terminal['input_adapter']['state_sha256']
            assert after['actual_mounted_identity_verified'] and after['frozen_base_verified']
            calls = [call_metrics(path) for path in sorted(readout.glob('CALL_*.json'))]
            held = [call for call in calls if call['purpose'] == 'held' and call['response_available']]
            assert terminal['denominator'] == 8
            previous = evidence.join_transition(campaign, 'GUIDED_SLEEP', number) if number >= 2 else None
            experience_calls = [call_metrics(path) for path in sorted(experience.glob('CALL_*.json'))]
            cycles.append(dict(cycle=number, saved_updates=learned['updates'],
                source_coverage=learned.get('coverage'), cumulative_prior_rows=learned.get('cumulative_prior_rows'),
                experience_complete_sha256=sha(experience / 'COMPLETE.json'),
                readout_complete_sha256=sha(readout / 'COMPLETE.json'),
                readout_loaded_sha256=sha(readout / 'LOADED.json'),
                readout_after_sha256=sha(readout / 'AFTER.json'),
                readout_input_adapter=terminal['input_adapter']['state_sha256'],
                fresh_process_readout=True, parent_free=True,
                full_cycle_seconds=terminal['finished_unix'] - learned['started_unix'],
                experience_sleep_seconds=learned['finished_unix'] - learned['started_unix'],
                readout_seconds=terminal['finished_unix'] - terminal['started_unix'],
                held_responses=len(held), held_denominator=8,
                mean_held_tokens=mean(call['generated_tokens'] for call in held) if held else None,
                held_truncations=sum(call['truncated'] for call in held),
                mean_held_lexical_repetition=mean(call['lexical_repeated_fourgram_rate'] for call in held) if held else None,
                accuracy_secondary=dict(correct=terminal['successes'], denominator=8),
                previous_sleep_to_original_attempts=previous,
                held_calls=held, experience_calls=experience_calls))
        report['lanes'][name] = dict(completed_cycles=len(cycles), cycles=cycles)
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    options = parser.parse_args()
    report = summarize(options.root)
    with options.output.open('x') as destination:
        json.dump(report, destination, indent=2, sort_keys=True)
        destination.write('\n')
    print(json.dumps({name: [{key: value for key, value in cycle.items()
                            if key not in ('held_calls', 'experience_calls', 'previous_sleep_to_original_attempts')}
                            for cycle in lane['cycles']] for name, lane in report['lanes'].items()}))
