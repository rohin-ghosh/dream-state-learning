import hashlib
import json
from pathlib import Path
import tarfile

archive = Path('/tmp/astra_cumulative_old_inputs_20260912.tgz')
root = 'astra_A1_memory_dose_S1_F_r16k16_ts2_20260912'
prefix = root + '/adapters/bank0/F_r16k16/across/sleep4/r8/'
adapter = {}
with tarfile.open(archive, 'r:gz') as captured:
    for member in captured:
        if member.isfile() and member.name.startswith(prefix):
            adapter[member.name[len(prefix):]] = hashlib.sha256(captured.extractfile(member).read()).hexdigest()
    distractor = hashlib.sha256(captured.extractfile(root + '/distractor.json').read()).hexdigest()
assert adapter['adapter_model.safetensors'] == 'c5bc4b2d7599d7f30732bb3adb98a1415206ecca41e0f96ce6d1db89015d6516'
model = json.loads(Path('/tmp/astra_constraint_model_pins_20260912.json').read_text())
output = Path('/tmp/astra_cumulative_pins_20260912.json')
with output.open('x') as stream:
    json.dump(dict(model=model['files'], a1=adapter, distractor_sha256=distractor), stream, indent=2, sort_keys=True)
print(json.dumps(dict(output_sha256=hashlib.sha256(output.read_bytes()).hexdigest(),
    adapter=adapter, distractor_sha256=distractor), sort_keys=True))
