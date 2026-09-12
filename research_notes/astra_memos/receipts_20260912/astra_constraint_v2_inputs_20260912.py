import hashlib
import json
from pathlib import Path

old = Path('/tmp/astra_constraint_prior_ids_20260912.json')
prior = json.loads(old.read_text())
ids = set(prior['episode_ids'])
ids.update(f'rg/mini_sudoku/{seed}' for seed in range(1851000, 1851008))
fresh = {f'rg/mini_sudoku/{seed}' for seed in range(1851100, 1851108)}
assert not ids & fresh
out = Path('/tmp/astra_constraint_v2_prior_ids_20260912.json')
with out.open('x') as stream:
    json.dump(dict(schema='prior-source-ids-v1', episode_ids=sorted(ids)), stream, indent=2, sort_keys=True)
print(json.dumps(dict(count=len(ids), fresh_ids=sorted(fresh),
    prior_sha256=hashlib.sha256(old.read_bytes()).hexdigest(),
    output_sha256=hashlib.sha256(out.read_bytes()).hexdigest(),
    scope='Prior captured metadata inventory plus all eight SEQ088 IDs; not global hidden-storage coverage.')))
