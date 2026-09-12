#!/usr/bin/env python3
"""CPU-only seed1/2 reduction/audit and three-seed descriptive summary; outputs are new files."""

import argparse
import hashlib
import json
import os
from pathlib import Path
import statistics
import subprocess
import sys


SEED0_AUDIT_SHA256 = '63447b86ee311e619f3ebd36c01a0fec9de5d47fb9d367a0956a2962823eb8a9'
SUMMARY_METRICS = (
    'first_act_solved_count', 'first_act_solved_rate',
    'first_act_native_score_mean_zero_filled', 'native_best_mean', 'n_acts_total',
)


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(path):
    return json.loads(Path(path).read_text())


def describe(values):
    return dict(per_seed_values=values, mean=statistics.mean(values),
                median=statistics.median(values), range=[min(values), max(values)])


def build_summary(capture, seed0_audit):
    paths = [seed0_audit] + [capture / f'seed{seed}_run_audit.json' for seed in (1, 2)]
    assert digest(paths[0]) == SEED0_AUDIT_SHA256
    audits = [read(path) for path in paths]
    receipt_path = capture / 'remote_adapter_rehash.json'
    receipt = read(receipt_path)
    assert {(record['training_seed'], record['arm']) for record in receipt['records']} == {
        (seed, arm) for seed in (1, 2) for arm in ('useful', 'corrupt')}
    assert len(receipt['records']) == 4
    for record in receipt['records']:
        seed, arm = record['training_seed'], record['arm']
        root = capture / f'astra_mini_sudoku_seed{seed}_20260912_attempt1'
        spec_path = root / f'logs/{arm}/probe_spec.json'
        spec = read(spec_path)
        assert record['spec_sha256'] == digest(spec_path)
        assert record['adapter_path'] == spec['adapter_path']
        assert record['actual_adapter_hashes'] == record['expected_adapter_hashes'] == spec['expected_adapter_hashes']
        assert record['expected_adapter_hashes'] == audits[seed]['arms'][arm]['expected_adapter_hashes']
    rows, comparability = [], []
    for seed, audit in enumerate(audits):
        assert audit['training_seed'] == seed and audit['status'] == 'OFFLINE_BINDINGS_VALIDATED'
        analysis = audit['analysis']
        if seed:
            assert analysis == read(capture / f'seed{seed}_reduction.json')
        pairs = analysis['pairs']
        rows.append(dict(training_seed=seed, audit_file=str(paths[seed]), audit_sha256=digest(paths[seed]),
            evidence_label=analysis['evidence_label'], audit_status=audit['status'],
            prompt_mismatch_count=audit['prompt_mismatch_count'],
            cells={f'{arm}_{condition}': dict(**pairs[arm][condition]['summary'],
                first_act_status_counts=pairs[arm][condition]['first_act_status_counts'],
                solved_ids=[entry['episode_id'] for entry in pairs[arm][condition]['episodes']
                            if entry['metrics']['first_act_solved']])
                for arm in ('useful', 'corrupt') for condition in ('off', 'on')},
            on_minus_off={arm: pairs[arm]['on_minus_off']['summary'] for arm in ('useful', 'corrupt')},
            useful_minus_corrupt={name: contrast['summary']
                                 for name, contrast in analysis['useful_minus_corrupt'].items()}))
        identities = {}
        for name in ('useful.json', 'corrupt.json', 'oracle_sources.json', 'ids.json'):
            matching = [value for path, value in audit['input_sha256'].items()
                        if path.endswith('/material/' + name)]
            assert len(matching) == 1
            identities[name] = matching[0]
        comparability.append(dict(training_seed=seed, material_sha256=identities,
            model_pins=audit['model_pins'], shared_budgets=audit['shared_budgets'],
            episode_ids=analysis['episode_ids'], paired_settings=analysis['paired_settings'],
            material_source_hashes=audit['material_source_hashes']))
    comparison_fields = ('material_sha256', 'model_pins', 'shared_budgets', 'episode_ids', 'paired_settings')
    equalities = {field: all(row[field] == comparability[0][field] for row in comparability[1:])
                  for field in comparison_fields}
    descriptive = {}
    for label, condition in (('direct_on', 'on'), ('difference_of_gains', 'on_minus_off'), ('off', 'off')):
        descriptive[label] = dict(native_contrast=condition, metrics={
            metric: describe([row['useful_minus_corrupt'][condition][metric] for row in rows])
            for metric in SUMMARY_METRICS})
    return dict(label='DESCRIPTIVE_THREE_OPTIMIZER_SEEDS_SHARED_CANARY_PANEL',
        per_seed=rows, comparability=comparability, cross_seed_exact_equalities=equalities,
        descriptive_contrasts=descriptive, range_definition='[minimum, maximum] across optimizer seeds 0,1,2',
        contrast_definitions=dict(direct_on='useful_ON - corrupt_ON',
            difference_of_gains='(useful_ON - useful_OFF) - (corrupt_ON - corrupt_OFF)',
            off='useful_OFF - corrupt_OFF'),
        remote_rehash_receipt_sha256=digest(receipt_path), summary_script_sha256=digest(__file__),
        limitations=['Seed0 had separate devices by arm; seeds1/2 use same device within each pair.',
            'Fixed useful-before-corrupt order and shared-node/time effects remain.',
            'Same 16 canary situations reused; not 48 independent heldout puzzles.',
            'Four solution grids overlap training; retain full panel and report solved IDs without post-hoc exclusion.',
            'Three optimizer seeds are descriptive, not a new significance, pass, or robustness threshold.',
            'Cross-seed byte/settings differences are reported, not normalized or silently treated as optimizer-only replication.',
            'Remote byte rehash is not local weight possession or loaded-runtime authentication.',
            'External oracle, not parenting/clean lineage; no exam exposure or C11 claim.'])


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo', required=True, type=Path)
    parser.add_argument('--capture-dir', required=True, type=Path)
    parser.add_argument('--seed0-audit', required=True, type=Path, help='Existing frozen final seed0 audit; not recomputed')
    parser.add_argument('--output-new', required=True, type=Path, help='New three-seed summary JSON')
    args = parser.parse_args(argv)
    repo = args.repo.resolve(strict=True)
    capture = args.capture_dir.resolve(strict=True)
    output = args.output_new.absolute()
    generated = [capture / f'seed{seed}_{kind}.json'
                 for seed in (1, 2) for kind in ('reduction', 'run_audit')]
    for path in [output, *generated]:
        if path.exists() or path.is_symlink():
            raise ValueError(f'output must be new; preserve existing file: {path}')
    assert output.resolve() not in {path.resolve() for path in generated}
    seed0_audit = args.seed0_audit.resolve(strict=True)
    assert digest(seed0_audit) == SEED0_AUDIT_SHA256
    environment = dict(os.environ, PYTHONDONTWRITEBYTECODE='1')
    for seed in (1, 2):
        root = capture / f'astra_mini_sudoku_seed{seed}_20260912_attempt1'
        subprocess.run([sys.executable, '-B', '-m', 'organism_v6.mini_sudoku_behavior_analysis',
            '--useful-pair', str(root / 'probes/useful'), '--corrupt-pair', str(root / 'probes/corrupt'),
            '--output-new', str(capture / f'seed{seed}_reduction.json')],
            cwd=repo, env=environment, check=True, timeout=30)
        subprocess.run([sys.executable, '-B', '-m', 'organism_v6.mini_sudoku_behavior_run_audit',
            '--run-root', str(root), '--output-new', str(capture / f'seed{seed}_run_audit.json')],
            cwd=repo, env=environment, check=True, timeout=30)
    report = build_summary(capture, seed0_audit)
    encoded = json.dumps(report, indent=2, sort_keys=True, allow_nan=False) + '\n'
    with output.open('x') as target:
        target.write(encoded)
    print('THREE_SEED_SUMMARY_WRITTEN', output, digest(output))
    print('CROSS_SEED_EXACT_EQUALITIES', report['cross_seed_exact_equalities'])


if __name__ == '__main__':
    main()
