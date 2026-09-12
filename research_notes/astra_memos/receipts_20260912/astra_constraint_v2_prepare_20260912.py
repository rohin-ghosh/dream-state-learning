import datetime
import json
from pathlib import Path

from organism_v6 import constraint_check_diagnostic as diagnostic
from gpu.astra_mini_sudoku_diagnostic import write_new

pins = diagnostic.read('/tmp/astra_constraint_model_pins_20260912.json')
prior = diagnostic.read('/tmp/astra_constraint_v2_prior_ids_20260912.json')
previous = Path.home() / 'astra_diagnostics/astra_constraint_check_preparation_20260912_attempt1'
old = diagnostic.read(previous / 'cases.json')
rows = []
for seed in diagnostic.GENERATION_SEEDS:
    root = Path.home() / f'astra_diagnostics/astra_constraint_v2_preparation_20260912_seed{seed}_attempt1'
    diagnostic.prepare(root, pins['model_path'], pins['files'], generation_seed=seed, prior_ids=prior)
    prep, digest, config, cases, check = diagnostic.validate_preparation(root)
    collisions = {key: sorted({case[key] for case in cases} & {case[key] for case in old})
                  for key in ('question_sha256', 'candidate_sha256')}
    assert not any(collisions.values()), collisions
    if rows:
        assert diagnostic.read(Path(rows[0]['root']) / 'cases.json') == cases
    rows.append(dict(root=str(root), preparation_sha256=digest, generation_seed=seed,
        status=check['status'], card_tokens=check['card_tokens'],
        collisions_with_original_preparation=collisions))
report = dict(status='NATIVE_V2_PREPARATION_AND_ORIGINAL_OVERLAP_CHECK_PASS',
    utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
    source=str(Path(diagnostic.__file__).resolve().parents[1]), pairs=rows,
    old_cases_sha256=diagnostic.formation._hash(previous / 'cases.json'),
    seed_role=diagnostic.SEED_ROLE, generation_calls=48, fits=0,
    collision_scope='Captured prior ID inventory, configured held IDs, internal uniqueness, and actual question/candidate hashes against SEQ088 only; not global hidden-storage coverage.')
write_new(Path('/tmp/astra_constraint_v2_native_preparation_20260912.json'), report)
print(json.dumps(report, sort_keys=True))
