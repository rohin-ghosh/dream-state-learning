import json
from pathlib import Path
import time

from transformers import AutoTokenizer
from organism_v6 import sequential_memory_corpus as material

source = Path('/localhome/local-rohing/astra_sources/5a1f300fed4b7f1ef54524869c2bf11509e965ca')
assert Path.cwd() == source
assert Path(material.__file__).parent.parent == source
model = '/localhome/local-rohing/.cache/huggingface/hub/models--Qwen--Qwen2.5-7B-Instruct/snapshots/a09a35458c702b33eeacc393d103063234e8bc28'
teach = Path('/localhome/local-rohing/astra_diagnostics/astra_fundamental_teaching_20260912_attempt1/teach.json')
output = Path('/localhome/local-rohing/astra_diagnostics/astra_sequential_memory_20260912_attempt1/material')
started = time.monotonic()
tokenizer = AutoTokenizer.from_pretrained(model, local_files_only=True, trust_remote_code=False)
manifest = material.prepare(output, teach, tokenizer)
audit = json.loads((output / 'token_audit.json').read_text())
print(json.dumps(dict(status=manifest['status'], output=str(output), manifest_sha256=material.digest((output / 'manifest.json').read_bytes()),
    elapsed_seconds=time.monotonic()-started, total_planned_updates=audit['total_planned_updates'],
    total_target_exposure=audit['total_target_exposure'], paired=audit['paired'],
    fits={cycle: {arm: details['ten_epochs'] for arm, details in arms.items()} for cycle, arms in audit['fits'].items()},
    native_identity_authenticated=False, parent_validated=False), sort_keys=True), flush=True)
