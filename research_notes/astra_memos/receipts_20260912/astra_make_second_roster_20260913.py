import hashlib
import json
from pathlib import Path


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write(path, value):
    with path.open('x') as stream:
        stream.write(json.dumps(value, sort_keys=True) + '\n')


directory = Path('/tmp/astra_level1_second_roster_20260913_attempt1_clockfix')
directory.mkdir()
original = Path('/tmp/astra_level1_roster_20260913_attempt1')
template = json.loads((original / 'prediction_seed0.json').read_text())
configs = json.loads((original / 'prechecks.json').read_text())
a100 = Path('/tmp/astra_a100_full_readiness_20260913T0752Z.prechecks.json')
assert digest(a100) == '256fd5ba7a98f320ae8fea7bf014c82d8a213f3bffd1a8250ba5cb311ac47cc5'
configs.update(json.loads(a100.read_text()))
configs.pop('node1')
write(directory / 'prechecks.json', configs)
source = Path('/tmp/astra_level1_second_source_20260913_attempt1')
template['source'] = str(source)
template['source_files'] = {str(path.relative_to(source)): digest(path) for path in source.rglob('*') if path.is_file()}
assert len(template['source_files']) == 5
protocol = Path('/tmp/ASTRA_LEVEL1_SECOND_ROSTER_PROTOCOL_2026-09-13.md')
assert digest(protocol) == 'c9652b1b0ad301c4a67c87597f870b8f423d95149679921bad5e5c95f3eabede'
template['protocol'] = dict(path=str(protocol), sha256=digest(protocol))
materials = {
    'node2': ('perception', 'self_reflection', '/tmp/astra_level1_perception_reflection_material_20260913.py',
              '4648f8542b1babb10f6ffda4bf023024d71b8c9834a32e2242a7f064a94a8941'),
    'a100': ('repetition', 'meta_reflection', '/tmp/astra_level1_repetition_meta_material_20260913.py',
             '498e841af8c65654b3f090a1c9f951b6d0aa0e040fd3d757d320f69cba007700')}
entries = []
for node, (first, second, path, checksum) in materials.items():
    assert digest(path) == checksum
    for position, skill in enumerate((first, second)):
        for seed in range(3):
            index = position * 3 + seed + (1 if node == 'node2' else 0)
            spec = dict(template, skill=skill, learner_seed=seed, gpu_index=index,
                        gpu_uuid=configs[node]['gpus'][str(index)],
                        lease_end=1789980180 if node == 'node2' else 1790380800,
                        material=dict(path=path, sha256=checksum))
            name = f'{skill}_seed{seed}'
            specification = directory / (name + '.json')
            write(specification, spec)
            entries.append(dict(node=node, name=name, gpu_index=index, gpu_uuid=spec['gpu_uuid'],
                                root=f'/localhome/local-rohing/astra_diagnostics/level1_{name}_20260913_attempt1',
                                spec=dict(path=str(specification), sha256=digest(specification))))
assert len({entry['root'] for entry in entries}) == 12
assert len({(entry['node'], entry['gpu_index']) for entry in entries}) == 12
write(directory / 'roster.json', dict(entries=entries,
      prechecks=dict(path=str(directory / 'prechecks.json'), sha256=digest(directory / 'prechecks.json')),
      scheduling=dict(a100_lease_end_field='conservative Sep26 00:00UTC scheduling floor; exact expiry unresolved',
                      a100_hardware='prospective first native use, not A40 parity', node2='Sep21 08:43UTC expiry')))
print(json.dumps(dict(roster=str(directory / 'roster.json'), sha256=digest(directory / 'roster.json'))))
