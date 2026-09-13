import hashlib
import json
from pathlib import Path


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write(path, value):
    with path.open('x') as stream:
        stream.write(json.dumps(value, sort_keys=True) + '\n')


original = Path('/tmp/astra_level1_second_roster_20260913_attempt1_clockfix')
assert digest(original / 'roster.json') == '2bca9e4a66cc576993119fc1d5fddcac77de7cc3f93686327b962c45c2d17c69'
directory = Path('/tmp/astra_level1_a40_fallback_roster_20260913_attempt2')
directory.mkdir()
config = json.loads(Path('/tmp/astra_level1_roster_20260913_attempt1/prechecks.json').read_text())['node1']
write(directory / 'prechecks.json', {'node1': config})
entries = []
for entry in json.loads((original / 'roster.json').read_text())['entries']:
    if entry['node'] != 'a100':
        continue
    source = Path(entry['spec']['path'])
    assert digest(source) == entry['spec']['sha256']
    spec = json.loads(source.read_text())
    spec.update(gpu_uuid=config['gpus'][str(entry['gpu_index'])], lease_end=1789427640)
    specification = directory / source.name
    write(specification, spec)
    entries.append(dict(entry, node='node1', gpu_uuid=spec['gpu_uuid'],
                        root=entry['root'].removesuffix('_attempt1') + '_attempt2',
                        spec=dict(path=str(specification), sha256=digest(specification))))
assert len(entries) == 6
write(directory / 'roster.json', dict(entries=entries,
      prechecks=dict(path=str(directory / 'prechecks.json'), sha256=digest(directory / 'prechecks.json')),
      scheduling=dict(reason='A100 runtime OFF failure missing ninja; prospective A40 placement amendment',
                      parent_roster_sha256=digest(original / 'roster.json'),
                      preserve_all_original_attempts=True, node1_expiry='2026-09-14T23:14:00Z')))
print(json.dumps(dict(roster=str(directory / 'roster.json'), sha256=digest(directory / 'roster.json'))))
