import hashlib
import json
from pathlib import Path


original = Path('/tmp/astra_l2_lr_specs_20260913_attempt1')
output = Path('/tmp/astra_l2_lr_specs_20260913_attempt2')
output.mkdir()
entries = []
for label in ('low', 'high'):
    specification = json.loads((original / f'seed0_{label}.json').read_text())
    target = output / f'seed0_{label}.json'
    with target.open('x') as stream:
        stream.write(json.dumps(specification, sort_keys=True) + '\n')
    entries.append(dict(name=f'seed0_{label}', spec_path=str(target),
                        spec_sha256=hashlib.sha256(target.read_bytes()).hexdigest(),
                        root=f'/localhome/local-rohing/astra_diagnostics/l2_lr_seed0_{label}_20260913_attempt2',
                        learner_seed=0, learning_rate=specification['learning_rate'],
                        gpu_index=specification['gpu_index'], gpu_uuid=specification['gpu_uuid']))
with (output / 'roster.json').open('x') as stream:
    stream.write(json.dumps(dict(status='PREPARATION_ONLY_NOT_LAUNCHED', specs=entries), sort_keys=True) + '\n')
print(json.dumps(entries, sort_keys=True))
