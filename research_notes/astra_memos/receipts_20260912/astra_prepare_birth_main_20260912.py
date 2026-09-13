import hashlib
import importlib.util
import json
from pathlib import Path
import sys


driver_path = Path('/tmp/astra_birth_conditional_run_20260913.py')
assert hashlib.sha256(driver_path.read_bytes()).hexdigest() == '072a1333c0411a73ae0fc46c6e70de9afe0bce9b49c74e01bdaae16174195daa'
spec = importlib.util.spec_from_file_location('main_prepare_birth', driver_path)
driver = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = driver
spec.loader.exec_module(driver)
source = Path.home() / 'astra_sources/31b5535ec9f73f7b32fdaf21ccfc3a2a68a948a6'
reference = Path.home() / 'astra_diagnostics/astra_rulegame_process_write_v2_20260912_attempt1/plan.json'
assert hashlib.sha256(reference.read_bytes()).hexdigest() == '67f2b89a769dd1f21e2ae3f048aa2d3743a5761f0574dcca3f47e1a8c51b0f44'
model = json.loads(reference.read_text())['model']
output = Path.home() / 'astra_diagnostics/astra_birth_conditional_fit_seed0_20260912_attempt1'
driver.main(['prepare-fit', '--source', str(source), '--module-sha256',
    '43bf074938e8c4e3a995e43d747ff24f2c6cf70252359cb35134391ff88da74b',
    '--model', model, '--out', str(output), '--device', '0',
    '--deadline', '2026-09-12T20:30:00-07:00', '--lease-end', '2026-09-25T20:03:00-07:00'])
