import json
from pathlib import Path
from organism_v6 import fresh_behavior_panel as diagnostic

root = diagnostic.ROOTS[0]
records = json.loads((root / 'material/oracle_sources.json').read_text())['records']
gym = diagnostic.native.ReasoningGymGym(require_package=True, strict_verifier=True)
solutions = diagnostic._solutions()
differences = []
for old in records:
    actual = diagnostic._entry(gym, old['episode_id'], solutions)
    for name in ('entry', 'puzzle', 'solution'):
        if actual[name] != old[name]:
            normalized = json.loads(json.dumps(actual[name]))
            differences.append(dict(episode_id=old['episode_id'], field=name,
                json_normalized_equal=normalized == old[name], actual=actual[name], saved=old[name],
                metadata_types={key:type(value).__name__ for key,value in actual['entry']['metadata'].items()}))
print(json.dumps(dict(differences=differences, count=len(differences),
                     only_json_roundtrip=all(row['json_normalized_equal'] for row in differences)), sort_keys=True))
