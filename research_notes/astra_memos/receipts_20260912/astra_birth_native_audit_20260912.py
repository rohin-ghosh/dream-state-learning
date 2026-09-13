import hashlib
import json
import os
from pathlib import Path
import time

from organism_v6 import birth_conditional_corpus as birth


source = Path.home() / 'astra_sources/31b5535ec9f73f7b32fdaf21ccfc3a2a68a948a6'
assert Path(birth.__file__).resolve() == source / 'organism_v6/birth_conditional_corpus.py'
assert hashlib.sha256(Path(birth.__file__).read_bytes()).hexdigest() == '43bf074938e8c4e3a995e43d747ff24f2c6cf70252359cb35134391ff88da74b'
assert not os.environ.get('CUDA_VISIBLE_DEVICES')
reference = Path.home() / 'astra_diagnostics/astra_rulegame_process_write_v2_20260912_attempt1/plan.json'
assert hashlib.sha256(reference.read_bytes()).hexdigest() == '67f2b89a769dd1f21e2ae3f048aa2d3743a5761f0574dcca3f47e1a8c51b0f44'
plan = json.loads(reference.read_text())
model = Path(plan['model'])
required = {'config.json', 'tokenizer.json', 'tokenizer_config.json'}
optional = {'vocab.json', 'merges.txt', 'special_tokens_map.json', 'added_tokens.json', 'chat_template.jinja', 'chat_template.json'}
pins = {name: hashlib.sha256((model / name).read_bytes()).hexdigest()
        for name in sorted(required | {name for name in optional if (model / name).exists()})}
for name, checksum in pins.items():
    assert checksum == plan['model_files'][name]
output = Path('/tmp/astra_birth_native_audit_20260912_attempt1.json')
assert not output.exists()
started = time.monotonic()
candidate = birth.build_candidate()
recipe = birth.training_recipe(learning_rate=1e-4, seed=0, epochs=4)
audit = birth.audit_native(candidate, model, pins, recipe=recipe)
with output.open('x') as stream:
    json.dump(audit, stream, sort_keys=True, allow_nan=False)
    stream.write('\n')
print(json.dumps(dict(status=audit['status'], seconds=time.monotonic()-started,
    output=str(output), output_sha256=hashlib.sha256(output.read_bytes()).hexdigest(),
    config_counts=audit['config_counts'], input_tokens_per_epoch=audit['input_tokens_per_epoch'],
    target_tokens_per_epoch=audit['target_tokens_per_epoch'],
    padded_input_per_fit=sum(row['padded_input_tokens'] for row in audit['group_costs']['0']),
    source_commit=source.name, model_origin='UNRESOLVED_LOCAL_HASHES_ONLY'), sort_keys=True))
