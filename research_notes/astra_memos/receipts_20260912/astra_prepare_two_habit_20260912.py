import json
from pathlib import Path
from organism_v6 import fundamental_two_habit_corpus as corpus

base = corpus.base
seedroot = Path.home() / 'astra_diagnostics/astra_fundamental_teaching_20260912_attempt1'
seed = base.read(seedroot / 'plan.json')
root = Path.home() / 'astra_diagnostics/astra_fundamental_two_habit_20260912_attempt1'
root.mkdir()
pins = dict(source_sha256=corpus.SOURCE_SHA256, source_code_sha256=corpus.source_hashes(),
            model_files=seed['model_files'])
with (root / 'pins.json').open('x') as output:
    json.dump(pins, output, sort_keys=True, indent=2)
result = corpus.prepare(seedroot / 'teach.json', root / 'material', pins, model=seed['model'])
print(json.dumps(result, sort_keys=True, indent=2))
