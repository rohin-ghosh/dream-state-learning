from collections import Counter
from datetime import datetime
import hashlib
import json
from pathlib import Path
import tarfile

archive_path = Path('/tmp/astra_fresh_behavior_terminal_20260912.tgz')
expected = '583d02e71e983169491ec8f5d2e37ae582c74b8aae0aa3c3f7091572c8ba489e'
assert hashlib.sha256(archive_path.read_bytes()).hexdigest() == expected
with tarfile.open(archive_path) as archive:
    prefix = 'astra_fresh_behavior_panel_20260912_attempt2/'
    def read(name):
        return json.load(archive.extractfile(prefix + name))
    report = read('first_act_report.json')
    release = read('main_release.json')
    known = {f'rg/mini_sudoku/{value}' for value in (1900071, 1900072, 1900073, 1900075)}
    rows, totals, off_outputs = [], Counter(), []
    for seed in report['seeds']:
        for arm, pair in seed['pairs'].items():
            for condition in ('off', 'on'):
                data = pair[condition]
                solved = [item['episode_id'] for item in data['episodes'] if item['metrics']['first_act_solved']]
                cell = f"probes/seed{seed['optimizer_seed']}_{arm}/{condition}/"
                events = [json.loads(line) for line in archive.extractfile(prefix + cell + 'generations.jsonl')]
                requests = [event for event in events if event['kind'] == 'generation_request']
                outputs = [event for event in events if event['kind'] == 'generation_output']
                assert len(requests) == len(outputs) == 32
                assert all(len(event['prompts']) == 1 for event in requests)
                assert all(len(event['outputs']) == 1 and isinstance(event['outputs'][0], str) for event in outputs)
                if condition == 'off':
                    off_outputs.append([event['outputs'] for event in outputs])
                counts = Counter('wake' if event['max_tokens'] == 400 else 'scratchpad' for event in requests)
                caps = sum(event['max_tokens'] for event in requests)
                registered = read(cell + 'results.json')
                assert registered['reserved_output_tokens'] == caps
                totals.update(counts)
                totals['request_cap_tokens'] += caps
                rows.append(dict(optimizer_seed=seed['optimizer_seed'], arm=arm, condition=condition,
                    **data['summary'], solved_ids=solved,
                    known_previously_exposed_solved_ids=sorted(set(solved) & known),
                    request_counts=dict(counts), requested_output_cap=caps))
    released = datetime.fromisoformat(release['observed_utc'])
    starts = [datetime.fromisoformat(item['started_utc']) for item in release['devices']]
    finishes = [datetime.fromisoformat(item['finished_utc']) for item in release['devices']]
    controller_seconds = sum(item['controller_seconds'] for item in release['devices'])
    full_reservation = sum((released - started).total_seconds() for started in starts)
    summary = dict(capsule_sha256=expected, status='COMPLETE_MIXED_EXPOSURE_DEVELOPMENT_ONLY',
        cells=rows, episode_ids=report['episode_ids'], known_prior_exposure_ids=sorted(known),
        prior_exposure_registry_scope='At least four selected IDs known exposed; no complete freshness claim',
        primary_endpoint='Original sixteen first-ACT solve counts per condition, no exclusions or rescue',
        difference_of_gains=report['solved_count_gain'],
        all_off_action_score_vectors_equal=report['all_off_action_score_vectors_equal'],
        all_six_off_full_output_vectors_equal=all(values == off_outputs[0] for values in off_outputs),
        totals=dict(totals), actual_native_token_counts_available=False,
        token_note='Probe retains request text and returned strings, not native token IDs. Caps are not usage.',
        summed_controller_seconds=controller_seconds, summed_controller_a40_hours=controller_seconds / 3600,
        first_launch_to_last_finish_seconds=(max(finishes) - min(starts)).total_seconds(),
        summed_full_device_reservation_seconds=full_reservation,
        reservation_note='Launch through Main full release; includes idle audit delay, not active GPU time',
        release_utc=release['observed_utc'], fits=0, independent_optimizer_seeds=3,
        independent_training_datasets=1, shared_panel_size=16, episode_cells=192,
        limitations=report['limitations'] + ['Known research-readout exposure omission; no comprehensive freshness.'])
output = Path('/tmp/astra_fresh_behavior_main_analysis_20260912.json')
with output.open('x') as target:
    json.dump(summary, target, indent=2, sort_keys=True)
print(json.dumps({key: value for key, value in summary.items() if key not in ('cells', 'limitations', 'episode_ids')}, indent=2))
