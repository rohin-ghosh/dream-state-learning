"""Conditional cost scenarios from saved SEQ266 writer and readout receipts."""

import argparse
import hashlib
import json
import statistics
from pathlib import Path


def calculate(root):
    bindings = {}

    def load(relative, lines=False):
        raw = (root / relative).read_bytes()
        bindings[str(relative)] = hashlib.sha256(raw).hexdigest()
        return [json.loads(line) for line in raw.splitlines()] if lines else json.loads(raw)

    assert (root / 'source_commit.txt').read_text().strip() == '7f9d4251ae1ff4c5ff9138adf267d081fffa6331'
    baseline = load('baseline/RESULT.json')
    measurements = {}
    readouts = {}
    for arm in ('FULL_TARGET', 'NEW_TRAJECTORY_LOSS_OFF'):
        receipt = load(f'{arm}/train/RESULT.json')
        masks = load(f'{arm}/train/REFERENCE_MASKS.json')
        dose = load(f'{arm}/train/DOSE.json')
        losses = load(f'{arm}/train/LOSSES.jsonl', lines=True)
        after = load(f'{arm}/after/RESULT.json')
        assert receipt['status'] == after['status'] == 'COMPLETE'
        assert receipt['updates'] == len(losses) == len(dose['batches']) == 2928
        assert len(masks) == len(dose['row_presentations']) == 1674
        lengths = [len(row['input_ids']) for row in masks]
        widths = [max(lengths[index] for index in batch['row_indexes']) for batch in dose['batches']]
        assert all(len(batch['row_indexes']) == 4 for batch in dose['batches'])
        nonpadding = sum(length * count for length, count in zip(lengths, dose['row_presentations']))
        assert nonpadding == 4477997
        loop_seconds = losses[-1]['fit_elapsed_seconds']
        phase_seconds = receipt['gpu_assigned_wall_seconds']
        measurements[arm] = dict(
            updates=2928, input_rows=1674, row_presentations=sum(dose['row_presentations']),
            sequence_min=min(lengths), sequence_median=statistics.median(lengths), sequence_max=max(lengths),
            batch_width_min=min(widths), batch_width_median=statistics.median(widths),
            batch_width_mean=statistics.mean(widths), batch_width_max=max(widths),
            nonpadding_token_presentations=nonpadding, padded_token_slots=4 * sum(widths),
            loop_seconds=loop_seconds, phase_seconds=phase_seconds,
            residual_phase_seconds=phase_seconds - loop_seconds,
            loop_seconds_per_update=loop_seconds / 2928,
            effective_nonpadding_tokens_per_loop_second=nonpadding / loop_seconds,
            padding_fraction=1 - nonpadding / (4 * sum(widths)),
            width_sensitivities={str(width): dict(
                linear_proxy=width / statistics.mean(widths),
                squared_proxy=width ** 2 / statistics.mean([value ** 2 for value in widths]))
                for width in (1024, 2048)},
        )
        readouts[arm] = dict(seconds=after['gpu_assigned_wall_seconds'], calls=after['model_calls'],
                             generated_tokens=after['generated_tokens'])
    update_rate = statistics.mean(item['loop_seconds_per_update'] for item in measurements.values())
    residual = statistics.mean(item['residual_phase_seconds'] for item in measurements.values())
    after_seconds = statistics.mean(item['seconds'] for item in readouts.values())
    baseline_seconds = baseline['gpu_assigned_wall_seconds']
    scenarios = []
    for targets, presentations in ((1000, 4), (1000, 16), (1452, 4), (1452, 16), (5000, 4), (5000, 16)):
        updates = (targets + 12) * presentations // 2
        assert updates * 2 == (targets + 12) * presentations
        fit_seconds = residual + updates * update_rate
        pair_seconds = 2 * (fit_seconds + after_seconds) + baseline_seconds
        scenarios.append(dict(new_targets=targets, presentations_per_trajectory=presentations,
                              old_trajectory_rows=12, trajectory_slots_per_update=2,
                              updates=updates, nominal_fit_hours=fit_seconds / 3600,
                              nominal_pair_assigned_gpu_hours=pair_seconds / 3600,
                              nominal_three_pairs_assigned_gpu_hours=3 * pair_seconds / 3600,
                              ideal_three_gpu_pair_wall_hours=(max(fit_seconds, baseline_seconds) + after_seconds) / 3600))
    return dict(schema='SEQ266_CONDITIONAL_COST_CALIBRATION_V2', model_calls=0, fits=0,
                source_commit='7f9d4251ae1ff4c5ff9138adf267d081fffa6331',
                root=str(root), measurements=measurements, readouts=readouts,
                baseline_seconds=baseline_seconds, baseline_calls=baseline['model_calls'],
                calibration=dict(mean_loop_seconds_per_update=update_rate, mean_residual_seconds=residual,
                                 mean_after_seconds=after_seconds), scenarios=scenarios,
                assumption='Same implementation, A40 rank8 batch4, observed sequence mix and unchanged readout battery. '
                           'Not a forecast for richer sequences, A100 hardware, corpus collection, or new batch layouts.',
                file_bindings=bindings)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    options = parser.parse_args()
    result = calculate(options.root)
    with options.output.open('x') as destination:
        json.dump(result, destination, indent=2, sort_keys=True)
        destination.write('\n')
    print(json.dumps(dict(calibration=result['calibration'], scenarios=result['scenarios']), indent=2))


if __name__ == '__main__':
    main()
