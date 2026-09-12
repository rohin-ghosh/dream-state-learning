import hashlib
import json
from pathlib import Path

prior_path = Path('/tmp/astra_constraint_v2_prior_ids_20260912.json')
prior = json.loads(prior_path.read_text())
ids = set(prior['episode_ids'])
ids.update(f'rg/mini_sudoku/{seed}' for seed in range(1851100, 1851108))
fresh = {f'rg/mini_sudoku/{seed}' for start in (1851200, 1851300) for seed in range(start, start + 8)}
assert not ids & fresh
out = Path('/tmp/astra_demonstration_prior_ids_20260912.json')
with out.open('x') as stream:
    json.dump(dict(schema='prior-source-ids-v1', episode_ids=sorted(ids)), stream, indent=2, sort_keys=True)
print(json.dumps(dict(prior_id_count=len(ids), candidate_ids=sorted(fresh),
    prior_sha256=hashlib.sha256(prior_path.read_bytes()).hexdigest(),
    output_sha256=hashlib.sha256(out.read_bytes()).hexdigest(),
    scope='Previously captured inventory plus all v2 IDs; not global hidden storage coverage.')))
