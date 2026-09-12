import datetime
import importlib.util
import json
from pathlib import Path


script = Path('/tmp/astra_varied_memory_pair_20260912.py')
spec = importlib.util.spec_from_file_location('varied_pair', script)
runner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runner)
source = Path.home() / 'astra_sources/dc2e9a3c11ccd9a3f10ea28513723bbfb8420247'
runner.bind(source, '/tmp/astra_memory_only_20260912.py', '/tmp/astra_fading_sentinel_20260912.py')
assert runner.base.digest(script) == 'b58f65cd482bbd2d762edc030c7967a1ecd004829cf8271c74c15d3ca54bc8c7'
root = Path.home() / 'astra_diagnostics/astra_varied_memory_replay_20260912_attempt1'
deadline = datetime.datetime.fromisoformat('2026-09-12T22:00:00+00:00').timestamp()
lease_end = datetime.datetime.fromisoformat('2026-09-26T03:03:00+00:00').timestamp()
assert deadline < lease_end - 6 * 3600
result = runner.prepare(root / 'material', root / 'fits_root0_attempt1', '1', deadline, lease_end)
runner.verify(root / 'fits_root0_attempt1')
print(json.dumps(result, sort_keys=True), flush=True)
