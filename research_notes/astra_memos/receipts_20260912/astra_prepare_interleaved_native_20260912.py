from datetime import datetime
import importlib.util
import json
from pathlib import Path

source = Path.home() / 'astra_sources/22b7e528f6f62358981ed2264d30ee7242926160'
spec = importlib.util.spec_from_file_location('interleaved_prepare', '/tmp/astra_interleaved_memory_pair_20260912.py')
driver = importlib.util.module_from_spec(spec)
spec.loader.exec_module(driver)
driver.bind(source)
original = Path.home() / 'astra_diagnostics/astra_fundamental_teaching_20260912_attempt1'
assert driver.base.digest(original / 'plan.json') == driver.memory.PINS['0'][0]
original_plan = driver.old.read_plan(original)
assert driver.base.model_hashes(original_plan['model']) == original_plan['model_files']
parent = Path.home() / 'astra_diagnostics/astra_interleaved_memory_replay_20260912_attempt1'
assert not parent.exists()
tokenizer = driver.base.native_tokenizer(original_plan['model'])
parent.mkdir()
material = parent / 'material'
root = parent / 'fits_root0_attempt1'
receipt = driver.material.prepare(material, original / 'teach.json', tokenizer)
print(json.dumps(dict(stage='MATERIAL_PREPARED', status=receipt['status'], token_totals=receipt['token_totals'])), flush=True)
deadline = datetime.fromisoformat('2026-09-12T22:30:00+00:00').timestamp()
lease_end = datetime.fromisoformat('2026-09-26T03:03:00+00:00').timestamp()
assert deadline + 300 < lease_end - 21600
prepared = driver.prepare(material, root, '1', deadline, lease_end)
print(json.dumps(prepared), flush=True)
