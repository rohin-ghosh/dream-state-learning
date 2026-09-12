import importlib.util
import json
from pathlib import Path
import sys

from organism_v6 import rulegame_parenting_diagnostic as diagnostic
from organism_v6 import rulegame_process_material as material

driver = Path('/tmp/astra_rulegame_process_write_20260912.py')
assert diagnostic.digest(driver) == 'a73dd6074fdd099cea19f46cfed94bf31f22b2ce02b8741ac2f224413ee514d9'
spec = importlib.util.spec_from_file_location('process_write', driver)
bridge = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = bridge
spec.loader.exec_module(bridge)
candidate = diagnostic.read('/tmp/astra_process_native_candidate_v2_20260912.json')
review = diagnostic.read('/tmp/astra_process_main_review_v2_20260912.json')
assert candidate['candidate_sha256'] == 'c54ae950ae04f469ccb8f8ce48a623592dd4cea5acfd4ae817a260475722a3f0'
model = candidate['source_binding']['identity']['backend']['model_input']
tokenizer = diagnostic.native_tokenizer(model)
pair = material.build_process_pair(candidate['source_binding']['capture_root'], review, tokenizer,
                                    fixed_candidate=candidate, protocol=material.PROTOCOL_V2)
for name, value in [('pair', pair), ('native_review_template', bridge.native_review_template(pair))]:
    path = Path(f'/tmp/astra_process_{name}_v2_20260912.json')
    bridge.write_json(path, value)
    print(json.dumps(dict(artifact=name, path=str(path), sha256=bridge.digest(path))), flush=True)
print(json.dumps(dict(status=pair['status'], totals=pair['audit']['token_totals'])), flush=True)
