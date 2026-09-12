import hashlib
import json
from pathlib import Path
import re
import subprocess

source = Path('/tmp/astra_parent_correction_prepared_20260912/astra_P1_fresh_correction_preparation_20260912_attempt1/config.json')
config = json.loads(source.read_text())
search = subprocess.run(['git', 'grep', '-h', '-o', '-E', 'rg/mini_sudoku/[0-9]+', 'HEAD', '--',
                         'organism_v6', 'research_notes', 'research_loop', 'gpu', 'tests'],
                        capture_output=True, text=True, check=True)
ids = set(search.stdout.splitlines())
ids.update(re.findall(r'rg/mini_sudoku/[0-9]+', source.read_text()))
for start, stop in ((1850000, 1850032), (1850100, 1850132), (1900050, 1900076),
                    (1001000, 1001032), (1002000, 1002016), (1900020, 1900043)):
    ids.update(f'rg/mini_sudoku/{seed}' for seed in range(start, stop))
assert not ids.intersection(f'rg/mini_sudoku/{seed}' for seed in range(1851000, 1851008))
outputs = {
    '/tmp/astra_constraint_model_pins_20260912.json': dict(model_path=config['model_path'], files=config['expected_files']),
    '/tmp/astra_constraint_prior_ids_20260912.json': dict(schema='prior-source-ids-v1', episode_ids=sorted(ids)),
    '/tmp/astra_constraint_inventory_audit_20260912.json': dict(
        source_config_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
        repository_head=subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True).strip(),
        count=len(ids), scope='Tracked repository literal IDs plus captured prior correction metadata and known expanded source/evaluation ranges; not global hidden-storage coverage.',
        candidate_ids=[f'rg/mini_sudoku/{seed}' for seed in range(1851000,1851008)], collision=False)
}
for path, value in outputs.items():
    with Path(path).open('x') as stream:
        json.dump(value, stream, indent=2, sort_keys=True)
print(json.dumps(dict(prior_id_count=len(ids), status='METADATA_INVENTORY_NO_MODEL_LOAD')))
