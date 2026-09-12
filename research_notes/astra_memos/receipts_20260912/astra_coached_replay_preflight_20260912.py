import json
from pathlib import Path
from organism_v6 import parent_note_replay_diagnostic as replay

pair = Path.home() / 'astra_diagnostics/astra_P0_material_6101_20260912_attempt1'
sources = {arm: replay.inspect_source(pair / arm, arm) for arm in replay.ARMS}
model = sources['lesson']['config']['model_path']
assert sources['lesson']['local_pins'] == sources['sham']['local_pins']
assert replay.formation.local_files(model) == sources['lesson']['local_pins']['files']
tokenizer = replay.reader._load_tokenizer(model)
info = {arm: [replay._token_info(row, tokenizer) for row in source['sources']] for arm, source in sources.items()}
print(json.dumps(dict(status='SOURCE_AND_ACTUAL_TOKENIZER_PASS', counts={arm: len(values) for arm, values in info.items()}, maximum_prompt_tokens={arm: max(row['prompt_tokens'] for row in values) for arm, values in info.items()}, training=False, inference=False), sort_keys=True))
