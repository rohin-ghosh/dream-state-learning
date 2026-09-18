"""Read-only CPU reduction into owner-private R130 report artifacts."""

import argparse
from collections import defaultdict
from datetime import datetime, timezone
import json
import math
import os
from pathlib import Path

from gpu import orch_r130_checkpoint_scheduler as scheduler


runner = scheduler.sidecar.runner
require = scheduler.require
sha = scheduler.sha
read = scheduler.read
CONFIG_SHA256 = 'a22dfa29a16ef419de3cb2e2ad2740b673700c4669c9ecbfc76de1238dea0805'


def wilson(correct, total):
    if not total:
        return None
    require(0 <= correct <= total, 'binomial_counts')
    quantile = 1.959963984540054
    proportion = correct / total
    denominator = 1 + quantile ** 2 / total
    center = (proportion + quantile ** 2 / (2 * total)) / denominator
    radius = quantile * math.sqrt(proportion * (1 - proportion) / total
        + quantile ** 2 / (4 * total ** 2)) / denominator
    return [max(0, center - radius), min(1, center + radius)]


def mean(values):
    return sum(values) / len(values) if values else None


def paired(tasks, before, after):
    scored = [task for task in tasks if task['scoring']['type'] != 'behavior']
    deltas, brier_deltas = [], []
    gained = lost = 0
    for task in scored:
        left, right = before.get(task['task_id']), after.get(task['task_id'])
        if not all(record and record['status'] == 'COMPLETE' and record['response_valid']
                and record['score']['parse_valid'] for record in (left, right)):
            continue
        delta = int(right['score']['correct']) - int(left['score']['correct'])
        deltas.append(delta)
        gained += delta == 1
        lost += delta == -1
        if all(record['score']['brier'] is not None for record in (left, right)):
            brier_deltas.append(right['score']['brier'] - left['score']['brier'])
    return dict(expected_scored_pairs=len(scored), jointly_valid_pairs=len(deltas),
        excluded_pairs=len(scored) - len(deltas), gained=gained, lost=lost,
        accuracy_delta_on_jointly_valid=mean(deltas), confidence_pairs=len(brier_deltas),
        brier_delta_on_jointly_valid_confidence=mean(brier_deltas))


def describe(records):
    numeric = defaultdict(list)
    for record in records:
        if record['status'] != 'COMPLETE':
            continue
        for name, value in record['descriptive'].items():
            if type(value) in (int, float):
                numeric[name].append(value)
            elif name == 'scaffold_pattern_indicators':
                for indicator, count in value.items():
                    numeric['scaffold_' + indicator].append(count)
        for name in ('generation_seconds', 'elapsed_seconds'):
            numeric[name].append(record[name])
    return dict(label='descriptive_only_not_semantic_thought_units',
        means={name: mean(values) for name, values in sorted(numeric.items())})


def summarize(tasks, records):
    coverage = runner.reduce_coverage(tasks, records)
    for condition, values in coverage.items():
        values['wilson95_iid_reference_only'] = wilson(values['correct_items'], values['valid_scored_items'])
        values['descriptive'] = describe([record for record in records if record['condition'] == condition])
    return coverage


def load_checkpoint(row, initial_hash):
    complete_path = Path(row['complete_path'])
    require(sha(complete_path) == row['complete_sha256'], 'complete_receipt_hash')
    complete = read(complete_path)
    require(complete['status'] == 'COMPLETE' and complete['before_after_verified'] is True
        and complete['calls'] == 60, 'complete_readonly_sixty_calls')
    require(complete['corpus_sha256'] == scheduler.sidecar.CORPUS_SHA256
        and complete['checkpoint']['commit_sha256'] == row['checkpoint_commit_sha256'], 'frozen_checkpoint_corpus')
    require(sha(row['plan_path']) == row['plan_sha256'] == complete['plan_sha256'], 'plan_hash')
    plan = read(row['plan_path'])
    require(sha(plan['corpus_path']) == scheduler.sidecar.CORPUS_SHA256, 'corpus_bytes')
    tasks = runner.validate_tasks(read(plan['corpus_path']))
    require(len(tasks) == 30, 'fixed_thirty_tasks')
    inputs = {str(complete_path): row['complete_sha256'], row['plan_path']: row['plan_sha256'],
        plan['corpus_path']: scheduler.sidecar.CORPUS_SHA256}
    records = []
    for name, expected in complete['receipts'].items():
        require(Path(name).name == name, 'receipt_basename')
        path = complete_path.parent / name
        require(sha(path) == expected, 'raw_receipt_hash')
        inputs[str(path)] = expected
        if name.startswith('CALL_') and name.count('.') == 1:
            records.append(read(path))
    task_map = {task['task_id']: task for task in tasks}
    require(len(records) == 60 and runner.reduce_coverage(tasks, records) == complete['coverage'], 'recomputed_coverage')
    for record in records:
        task = task_map[record['task_id']]
        require(record['status'] == 'COMPLETE' and record['messages'] == task['messages']
            and record['decoder'] == runner.DECODER, 'same_messages_decoder')
        require(record['score'] == runner.score_response(task, record['response']['raw']), 'objective_score_reduction')
        require(record['descriptive'] == runner.descriptive_metrics(record['response']), 'descriptive_reduction')
    commit_path = complete_path.parent / 'COMMIT.original.json'
    require(sha(commit_path) == row['checkpoint_commit_sha256'], 'original_commit_bytes')
    inputs[str(commit_path)] = row['checkpoint_commit_sha256']
    commit = read(commit_path)
    require(type(commit['optimizer_steps']) is int and commit['optimizer_steps'] >= 0, 'native_step_count')
    families = {}
    for family in sorted({task['family'] for task in tasks}):
        selected = [task for task in tasks if task['family'] == family]
        identifiers = {task['task_id'] for task in selected}
        families[family] = summarize(selected, [record for record in records if record['task_id'] in identifiers])
    result = dict(lineage_id=row['lineage_id'], label=row['label'],
        checkpoint_commit_sha256=row['checkpoint_commit_sha256'], optimizer_steps=commit['optimizer_steps'],
        checkpoint_created_unix=commit.get('created_unix'),
        is_initial=row['checkpoint_commit_sha256'] == initial_hash,
        complete_path=str(complete_path), complete_sha256=row['complete_sha256'],
        families=families, pooled_secondary_only=summarize(tasks, records))
    return result, tasks, records, inputs


def comparison(tasks, left, right):
    return {family: paired([task for task in tasks if task['family'] == family], left, right)
        for family in sorted({task['family'] for task in tasks})}


def render(curve):
    lines = ['# Sealed R130 checkpoint report — USER / independent reader only', '',
        'Do not transmit this report, curves, metrics, prompts, outputs, or conclusions to parenting Main.',
        'Filesystem permissions restrict access to the operator account; this is not an identity-based reader ACL.',
        'The user must explicitly control any independent-reader handoff; nothing is sent automatically.', '',
        '## Design and provenance',
        f"Snapshot: {curve['created_utc']}; completed immutable checkpoints: {len(curve['checkpoints'])}.",
        f"Fixed corpus SHA256: {curve['corpus_sha256']}; runner SHA256: {curve['runner_sha256']}.",
        'Frozen Qwen2.5-7B-Instruct; one saved adapter per fresh runner process; ON/OFF within that process.',
        'Identical fixed task messages and empty per-call context; deterministic temperature 0, maximum 512 tokens.',
        'No training or optimizer-state loads. Original COMMIT metadata provides the optimizer-step x-axis.',
        'Completion, plan/corpus/receipt hashes, before/after read-only verification, scoring, and coverage are checked.',
        'Source children are not accessed. Existing scheduling and generator processes are unchanged.', '',
        '## Uncertainty, validity, and confounds',
        'Exploratory descriptive evidence only; neither consciousness nor a general learning/improvement claim is established.',
        'Thirty fixed, purposively selected prompts are not independent random population samples; families and related items may be dependent.',
        'Wilson 95% intervals are IID-binomial reference intervals on valid scored responses only, not defensible population confidence bounds.',
        'No repeated-seed inference, confirmatory p-values, multiple-testing adjustment, or causal effect of sleep is asserted.',
        'Correct/expected-scored is a coverage-aware yield, not valid-only accuracy; missing, failed, truncated, and parse-invalid items remain separate.',
        'Paired deltas use jointly valid scored items and explicitly report excluded pairs; changing valid subsets can bias conditional estimates.',
        'Confidence/Brier uses explicit scoring keys and available valid confidence values only; absent confidence is not imputed.',
        'Behavior-only items have no correctness or metacognition score. Tokens, lengths, exact repetitions and scaffold indicators are descriptive, not semantic thought units.',
        'Public BBH exposure/pretraining contamination cannot be excluded. Held custody does not establish pretraining novelty.',
        'Checkpoint trajectories confound optimizer steps, curriculum, parent interactions and elapsed history; saved snapshots are selected, not randomized treatments.',
        'LoRA OFF is a within-process base control, not an independently trained control. Cross-checkpoint OFF drift should be treated as a reproducibility warning.',
        'Timing is affected by warm-up, caching and six concurrent generation workers; it is not a clean efficiency comparison.',
        'Optimizer-step order is not an invented sleep index. Only original labels identify known initial/sleep checkpoints.',
        'Only verified completed checkpoints at snapshot time appear; pending/incomplete checkpoints are not scored as successes.', '',
        '## Per-lineage initial → saved-checkpoint curves',
        'Primary tables are separated by family; pooled values in CURVE.private.json are secondary only.', '']
    for row in curve['checkpoints']:
        lines += [f"### {row['lineage_id']} / {row['label']} / steps {row['optimizer_steps']}",
            f"COMMIT `{row['checkpoint_commit_sha256']}`; initial={row['is_initial']}.", '',
            '| Family | Condition | Correct / valid | Correct / expected scored | Parse failures | Truncated | Missing / failed | Brier (n) |',
            '|---|---|---|---|---|---|---|---|']
        for family, conditions in row['families'].items():
            for condition, value in conditions.items():
                lines.append(f"| {family} | {condition} | {value['correct_items']}/{value['valid_scored_items']} | "
                    f"{value['correct_items']}/{value['expected_scored_items']} | {value['parse_failure_items']} | "
                    f"{value['truncated_items']} | {value['missing_items']}/{value['failed_items']} | "
                    f"{value['mean_brier_on_valid_confidence']} ({value['confidence_items']}) |")
        lines += ['', 'Family-level uncertainty references and descriptive metrics:',
            '```json', json.dumps(row['families'], indent=2, sort_keys=True), '```', '']
    lines += ['## Paired ON minus OFF and saved minus initial comparisons',
        'Direction is right minus left. Signed numerical differences are observed task-set differences, not general improvement conclusions.',
        'Inspect OFF trajectories alongside ON trajectories before attributing any difference to adapter learning.',
        '```json', json.dumps(curve['paired_comparisons'], indent=2, sort_keys=True), '```', '',
        '## Reader guidance',
        'A claim beyond these observed fixed-item differences requires replicated held tasks, independent runs and matched controls.',
        'Keep scientific interpretation within the user/independent-reader boundary. Do not feed any held feedback to parents.', '']
    return '\n'.join(lines)


def write_private(path, content):
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(descriptor, 'w') as stream:
        stream.write(content)


def build(config_path, output):
    require(sha(config_path) == CONFIG_SHA256, 'pinned_scheduler_config')
    config = read(config_path)
    root = Path(config['operator_root'])
    require(output.parent == root and output.name.startswith('sealed_scientific_report_')
        and not output.exists() and not root.is_symlink(), 'new_sealed_operator_output')
    require(sha(config['registry_path']) == scheduler.REGISTRY_SHA256, 'pinned_six_checkpoint_registry')
    require(sha(config['lineages_path']) == config['lineages_sha256'], 'lineage_registry_hash')
    require(sha(Path(config['source_root']) / 'gpu/orch_r130_checkpoint_benchmark.py')
        == scheduler.sidecar.RUNNER_SHA256, 'runner_source_hash')
    lineages = scheduler.enrolled_lineages(read(config['lineages_path']))
    seeds = scheduler.seed_completed(config, lineages)
    scheduler.ledger_state(config, seeds, lineages)
    rows = []
    inputs = {str(config_path): CONFIG_SHA256, config['registry_path']: scheduler.REGISTRY_SHA256,
        config['lineages_path']: config['lineages_sha256']}
    for row in read(config['registry_path'])['checkpoints']:
        rows.append(dict(row, lineage_id=scheduler.SEED_LABELS[row['label']]))
    for terminal_path in sorted(Path(config['ledger_root']).glob('*.COMPLETE.json')):
        terminal = read(terminal_path)
        claim_path = terminal_path.with_name(terminal_path.name.replace('.COMPLETE.json', '.RESERVED.json'))
        claim = read(claim_path)
        require(terminal['status'] == 'COMPLETE' and terminal['claim_sha256'] == sha(claim_path)
            and terminal['key'] == scheduler.key_for(claim['lineage_id'], claim['commit_sha256']), 'completion_claim')
        inputs[str(terminal_path)] = sha(terminal_path)
        inputs[str(claim_path)] = sha(claim_path)
        rows.append(dict(lineage_id=claim['lineage_id'], label='saved_' + claim['commit_sha256'][:12],
            checkpoint_commit_sha256=claim['commit_sha256'], complete_path=terminal['native_complete_path'],
            complete_sha256=terminal['native_complete_sha256'], plan_path=claim['plan_path'], plan_sha256=claim['plan_sha256']))
    require(len({(row['lineage_id'], row['checkpoint_commit_sha256']) for row in rows}) == len(rows), 'no_duplicate_checkpoints')
    curve_rows, calls, comparisons = [], {}, []
    for row in rows:
        reduced, tasks, records, evidence = load_checkpoint(row, lineages[row['lineage_id']]['initial_commit_sha256'])
        curve_rows.append(reduced)
        inputs.update(evidence)
        calls[row['checkpoint_commit_sha256']] = {condition: {record['task_id']: record for record in records
            if record['condition'] == condition} for condition in runner.CONDITIONS}
    curve_rows.sort(key=lambda row: (row['lineage_id'], not row['is_initial'], row['optimizer_steps'], row['checkpoint_commit_sha256']))
    for row in curve_rows:
        current = calls[row['checkpoint_commit_sha256']]
        comparisons.append(dict(kind='ON_minus_OFF', lineage_id=row['lineage_id'], label=row['label'],
            families=comparison(tasks, current['LORA_OFF'], current['LORA_ON'])))
        if not row['is_initial']:
            baseline = calls[lineages[row['lineage_id']]['initial_commit_sha256']]
            for condition in runner.CONDITIONS:
                comparisons.append(dict(kind='saved_minus_initial', lineage_id=row['lineage_id'], label=row['label'],
                    condition=condition, families=comparison(tasks, baseline[condition], current[condition])))
    curve = dict(schema='R130_SEALED_SCIENTIFIC_REPORT_V1', created_utc=datetime.now(timezone.utc).isoformat(),
        audience='USER_AND_INDEPENDENT_READER_ONLY_NOT_PARENTING_MAIN', corpus_sha256=scheduler.sidecar.CORPUS_SHA256,
        runner_sha256=scheduler.sidecar.RUNNER_SHA256, checkpoints=curve_rows, paired_comparisons=comparisons)
    report = render(curve)
    for path, expected in inputs.items():
        require(sha(path) == expected, 'input_unchanged_after_reduction')
    output.mkdir(mode=0o700)
    write_private(output / 'CURVE.private.json', json.dumps(curve, indent=2, sort_keys=True) + '\n')
    write_private(output / 'REPORT.private.md', report)
    write_private(output / 'EVIDENCE.private.json', json.dumps(dict(inputs=inputs,
        generator_sha256=sha(__file__), readonly_reduction=True), indent=2, sort_keys=True) + '\n')
    artifacts = {name: sha(output / name) for name in ('REPORT.private.md', 'CURVE.private.json', 'EVIDENCE.private.json')}
    receipt = dict(status='SEALED_REPORT_CREATED', report_root=str(output), artifacts=artifacts,
        completed_checkpoint_count=len(curve_rows), future_completed_checkpoints=len(curve_rows) - 6,
        completed_call_count=60 * len(curve_rows), lineage_count=len({row['lineage_id'] for row in curve_rows}),
        no_parent_visible_metrics=True)
    write_private(output / 'PARENT_SAFE_RECEIPT.json', json.dumps(receipt, indent=2, sort_keys=True) + '\n')
    return dict(receipt, receipt_sha256=sha(output / 'PARENT_SAFE_RECEIPT.json'))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--config', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    try:
        print(json.dumps(build(args.config, args.output), sort_keys=True))
    except Exception as error:
        print(json.dumps(dict(status='REPORT_FAILED_NO_RESULTS_DISCLOSED', error_type=type(error).__name__)))
        raise SystemExit(1)


if __name__ == '__main__':
    main()
