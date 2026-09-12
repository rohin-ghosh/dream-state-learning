from datetime import datetime
import importlib.util
import json
from pathlib import Path

script = Path('/tmp/astra_interleaved_memory_replication_20260912.py')
spec = importlib.util.spec_from_file_location('replication', script)
runner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runner)
source = Path.home() / 'astra_sources/22b7e528f6f62358981ed2264d30ee7242926160'
runner.bind(source)
assert runner.base.digest(script) == 'dc92b9d18f1fc7e8b9907f304e366de34a5e12340223f8dd17506e007093065f'
root = Path.home() / 'astra_diagnostics/astra_interleaved_memory_replay_20260912_attempt1'
seed0 = root / 'fits_root0_attempt1'
review = Path('/tmp/astra_interleaved_memory_independent_review_20260912.md')
assert runner.base.digest(review) == '522633241ad3910a4d0ee1fd156d31aa3eb7756495cc5efbbe2cc3c97865f522'
gate = dict(schema='INTERLEAVED_SEED0_MAIN_GATE_V1', owner='Main', decision='ALLOW_SEEDS_1_2',
            eligible_seeds=[1, 2], criteria=runner.PROGRESSION, raw_review_verdict='PASS')
for name, path in [('seed0_plan', seed0 / 'plan.json'), ('seed0_terminal', seed0 / 'run/terminal.json'),
                   ('seed0_validation', Path('/tmp/astra_interleaved_memory_root0_terminal_20260912.tgz.validation.json')),
                   ('raw_review', review)]:
    gate[name] = dict(path=str(path), sha256=runner.base.digest(path))
gate_path = Path('/tmp/astra_interleaved_seed0_main_gate_20260912.json')
runner.old.write(gate_path, gate)
print(json.dumps(dict(stage='MAIN_GATE_SAVED', path=str(gate_path), sha256=runner.base.digest(gate_path))), flush=True)
deadline = datetime.fromisoformat('2026-09-12T23:30:00+00:00').timestamp()
lease_end = datetime.fromisoformat('2026-09-26T03:03:00+00:00').timestamp()
for seed, device in [(1, '0'), (2, '1')]:
    parent = Path.home() / 'astra_diagnostics/astra_fundamental_replications_20260912_attempt1' / f'seed{seed}'
    prepared = runner.prepare(root / 'material', root / f'fits_root{seed}_attempt1', device, deadline,
                              lease_end, seed, parent, gate_path, runner.base.digest(gate_path))
    print(json.dumps(dict(seed=seed, prepared=prepared)), flush=True)
