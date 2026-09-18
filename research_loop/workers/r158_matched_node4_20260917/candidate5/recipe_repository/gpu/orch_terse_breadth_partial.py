"""Reduce completed A100 pairs without declaring the three-pair batch terminal."""

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path


def require(condition, message):
    if not condition:
        raise ValueError(message)


def summarize(result):
    require(result['status'] == 'COMPLETE', 'nonterminal_readout')
    summary = result['summary']
    conditions = {}
    for condition in ('OWN_TEXT', 'UNAVAILABLE'):
        panels = [panel for panel in summary['panels']
                  if panel['split'] == 'PROBE' and panel['condition'] == condition]
        require(len(panels) == 32 and len({panel['master'] for panel in panels}) == 32,
                'full_32_world_denominator_required')
        require(all(panel['summary']['paired']['denominator'] == 2 and
                    panel['summary']['individual']['denominator'] == 4 for panel in panels),
                'per_world_denominator_drift')
        conditions[condition] = dict(
            pairs=sum(panel['summary']['paired']['correct'] for panel in panels), pair_denominator=64,
            goals=sum(panel['summary']['individual']['correct'] for panel in panels), goal_denominator=128,
            covered_worlds=sum(panel['summary']['paired']['correct'] >= 1 for panel in panels),
            world_denominator=32,
            failed_worlds=[panel['master'] for panel in panels if not panel['summary']['paired']['correct']])
    own = conditions['OWN_TEXT']
    require(summary['primary'] == dict(correct=own['pairs'], denominator=64,
            goals=own['goals'], goal_denominator=128), 'primary_reduction_drift')
    retention = dict(w0=summary['old_recall']['0'], w8=summary['old_recall']['8'],
                     audit=summary['held_audit']['overall'])
    for output, name in (('original', 'taught_graph'), ('previous_fresh', 'previous_fresh_graph')):
        retention[output] = {key: summary[name]['OWN_TEXT'][key] for key in ('correct', 'denominator')}
    require(all(retention[key]['denominator'] == 16 for key in ('w0', 'w8', 'audit')) and
            all(retention[key]['denominator'] == 4 for key in ('original', 'previous_fresh')),
            'retention_denominator_drift')
    checks = dict(old_w0=retention['w0']['correct'] >= 15, old_w8=retention['w8']['correct'] >= 15,
                  audit=retention['audit']['correct'] >= 15, taught=retention['original']['correct'] >= 3,
                  previous_fresh=retention['previous_fresh']['correct'] >= 3,
                  pairs=own['pairs'] >= 48, every_world=own['covered_worlds'] == 32)
    require(checks == summary['checks'] and all(checks.values()) == summary['engineering_target_met'],
            'prospective_gate_reduction_drift')
    return dict(conditions=conditions, retention=retention, checks=checks,
                engineering_target_met=all(checks.values()), model_calls=result['model_calls'])


def reduce_a100(root):
    records, hashes = {}, {}
    for stage in ('baseline0', 'train0', 'after0', 'train1', 'after1', 'train2', 'after2', 'train3', 'after3'):
        path = root / stage / 'RESULT.json'
        raw = path.read_bytes()
        hashes[str(path.relative_to(root))] = hashlib.sha256(raw).hexdigest()
        records[stage] = json.loads(raw)
        require(records[stage]['status'] == 'COMPLETE', 'incomplete_stage:' + stage)
        require(not (root / stage / 'FAILED.json').exists(), 'contradictory_failure:' + stage)
    for lane in range(4):
        require((root / f'chain{lane}.done').exists(), 'chain_not_terminal')
        for phase in ('train', 'after'):
            require((root / f'chain{lane}_{phase}_exit.txt').read_text().strip() == '0', 'nonzero_chain_exit')
    baseline = records['baseline0']
    batch_sha = hashlib.sha256((root / 'assembly/BATCH.json').read_bytes()).hexdigest()
    require(all(record['batch_sha256'] == batch_sha and record['frozen_base_unchanged']
                for record in records.values()), 'batch_or_base_drift')
    for key in ('manifest_sha256', 'source_sha256'):
        require(len({record[key] for record in records.values()}) == 1, key + '_drift')
    baseline_summary = summarize(baseline)
    pairs = []
    for full_lane, off_lane, seed in ((0, 1, 7801), (2, 3, 7802)):
        full, off = (records[f'after{lane}'] for lane in (full_lane, off_lane))
        train_full, train_off = (records[f'train{lane}'] for lane in (full_lane, off_lane))
        require(full['arm'] == train_full['arm'] == 'FULL_TARGET' and
                off['arm'] == train_off['arm'] == 'NEW_TRAJECTORY_LOSS_OFF', 'control_arm_drift')
        require(all(record['seed'] == seed and record['trajectory_presentations'] == 4
                    for record in (full, off, train_full, train_off)), 'seed_or_dose_drift')
        require(train_full['row_presentations'] == train_off['row_presentations'] and
                train_full['reference_supervised_tokens'] == train_off['reference_supervised_tokens'],
                'matched_schedule_or_reference_denominator_drift')
        for readout, train in ((full, train_full), (off, train_off)):
            require(readout['loaded_adapter_state_sha256'] == train['adapter_state_after'] and
                    readout['pid'] != train['pid'], 'fresh_process_saved_state_mismatch')
            require(train['updates'] == 5760, 'update_count_drift')
            signature = [(panel['master'], panel['condition'], panel['collection_sha256'],
                          panel['shared_text_sha256']) for panel in readout['summary']['panels']]
            expected = [(panel['master'], panel['condition'], panel['collection_sha256'],
                         panel['shared_text_sha256']) for panel in baseline['summary']['panels']]
            require(signature == expected, 'cohort_or_readout_source_drift')
        full_summary, off_summary = summarize(full), summarize(off)
        reference = full['summary']['deterministic_first_port']
        require(reference == off['summary']['deterministic_first_port'] ==
                baseline['summary']['deterministic_first_port'] and len(reference) == 32,
                'deterministic_reference_drift')
        reference_score = sum(entry['summary']['paired']['correct'] for entry in reference)
        full_score = full_summary['conditions']['OWN_TEXT']['pairs']
        off_score = off_summary['conditions']['OWN_TEXT']['pairs']
        comparator_win = full_score > max(off_score, baseline_summary['conditions']['OWN_TEXT']['pairs'], reference_score)
        pairs.append(dict(seed=seed, dose=4, full=full_summary, loss_off=off_summary,
                          paired_difference=full_score-off_score, deterministic_pairs=reference_score,
                          comparator_win=comparator_win,
                          conjunction_survived=full_summary['engineering_target_met'] and comparator_win,
                          full_state=train_full['adapter_state_after'], control_state=train_off['adapter_state_after']))
    return dict(utc=datetime.now(timezone.utc).isoformat(), status='PARTIAL_BATCH_A100_TERMINAL',
                pairs=pairs, baseline=baseline_summary, batch_sha256=batch_sha, source_result_hashes=hashes,
                pending_pair=dict(seed=7801, dose=16, lanes=[4, 5], status='RUNNING_NOT_REDUCED'),
                two_seed_four_dose_conjunction_survived=all(pair['conjunction_survived'] for pair in pairs),
                reader_verified=False, promotion=False, old266_gate='FAIL_UNCHANGED',
                claim='AUTHOR_ONLY_SAME_COHORT_TWO_SEED_FOUR_DOSE_NOT_THREE_PAIR_TERMINAL')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('root', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    report = reduce_a100(args.root)
    with args.output.open('x') as stream:
        json.dump(report, stream, indent=2, sort_keys=True)
        stream.write('\n')


if __name__ == '__main__':
    main()
