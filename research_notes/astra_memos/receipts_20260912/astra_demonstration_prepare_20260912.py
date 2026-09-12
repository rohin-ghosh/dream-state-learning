import datetime
import json
from pathlib import Path

from organism_v6 import constraint_demonstration_diagnostic as diagnostic
from gpu.astra_mini_sudoku_diagnostic import write_new

root = Path.home() / 'astra_diagnostics/astra_demonstration_preparation_20260912_attempt1'
pins = diagnostic.read('/tmp/astra_constraint_model_pins_20260912.json')
prior = diagnostic.read('/tmp/astra_demonstration_prior_ids_20260912.json')
prior_preparations = [Path.home() / 'astra_diagnostics' / name for name in (
    'astra_constraint_check_preparation_20260912_attempt1',
    'astra_constraint_v2_preparation_20260912_seed7101_attempt1')]
diagnostic.prepare(root, pins['model_path'], pins['files'], prior_ids=prior,
                   prior_preparations=prior_preparations)
prep, digest, config, pairs, check = diagnostic.validate_preparation(root)
old_paths = [Path.home() / 'astra_diagnostics' / name / 'cases.json' for name in (
    'astra_constraint_check_preparation_20260912_attempt1',
    'astra_constraint_v2_preparation_20260912_seed7101_attempt1')]
old_cases = [case for path in old_paths for case in diagnostic.read(path)]
cases = [pair[stage] for pair in pairs for stage in ('source', 'transfer')]
collisions = {key: sorted({case[key] for case in cases} & {case[key] for case in old_cases})
              for key in ('question_sha256', 'candidate_sha256')}
assert not any(collisions.values()), collisions
assert all(pair['source_example_score']['grounded'] == pair['transfer_witness_score']['grounded'] == 1
           and pair['copied_witness_on_transfer_score']['grounded'] == 0 for pair in pairs)
report = dict(status='NATIVE_DEMONSTRATION_PREPARATION_AND_OVERLAP_PASS',
    utc=datetime.datetime.now(datetime.timezone.utc).isoformat(), root=str(root),
    source=str(Path(diagnostic.__file__).resolve().parents[1]), preparation_sha256=digest,
    generation_calls=32, fits=0, sampling_seed=7101,
    prior_cases_sha256={str(path): diagnostic.base.formation._hash(path) for path in old_paths},
    collisions=collisions, source_group_counts={group: diagnostic.GROUPS.count(group) for group in set(diagnostic.GROUPS)},
    explanation_tokens={mode: [row['tokens'] for row in check['explanations'][mode]] for mode in diagnostic.MODES},
    explanation_tokens_equal=check['explanation_tokens_equal'],
    source_prompt_tokens_equal=check['source_prompt_tokens_equal'],
    boundary=diagnostic.BOUNDARY,
    collision_scope='Supplied prior ID inventory, configured held IDs, all16 internal question/candidate hashes, actual v1/v2 question/candidate overlap only; not global hidden storage coverage.')
write_new(Path('/tmp/astra_demonstration_native_preparation_20260912.json'), report)
print(json.dumps(report, sort_keys=True))
