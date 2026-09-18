"""CPU-only numerical probe tests against the immutable candidate5 closure."""

import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sys
import time


attempt = Path(__file__).resolve().parent
candidate = Path('/localhome/local-rohing/orch_r158_matched_node4_20260917_attempt5')
assert os.environ.get('CUDA_VISIBLE_DEVICES') == ''
assert os.environ.get('HF_HUB_OFFLINE') == '1'
assert os.environ.get('TRANSFORMERS_OFFLINE') == '1'
assert os.environ.get('PYTHONDONTWRITEBYTECODE') == '1'
sys.path[:0] = [str(attempt), str(candidate/'source'), str(candidate/'test_support')]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


manifest = json.loads((attempt/'INPUTS.json').read_text())
for name, expected in manifest.items():
    assert sha(attempt/name) == expected, name
native = candidate/'source/gpu/orch_r125_continual_native.py'
assert sha(native) == 'bcd716db469665d6c2070ed46d4b910d619b7366b66af2891c9ed71a5e069af6'

started = time.time()
import torch
import pytest
import gpu

assert not torch.cuda.is_initialized()
torch.set_num_threads(1)
torch.set_num_interop_threads(1)
for leaf in ('orch_r161_native_executor', 'orch_r163_executor_probe'):
    name = 'gpu.'+leaf
    spec = importlib.util.spec_from_file_location(name, attempt/(leaf+'.py'))
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    setattr(gpu, leaf, module)

status = pytest.main([str(attempt/'test_orch_r163_executor_probe.py'), '-q', '-p', 'no:cacheprovider',
    '--basetemp', str(attempt/'pytest_tmp')])
origins = {}
for name, module in sorted(sys.modules.items()):
    if name.startswith(('gpu.', 'organism_v6.')) and getattr(module, '__file__', None):
        path = Path(module.__file__).resolve()
        assert path.is_relative_to(candidate/'source') or path.parent == attempt, name
        origins[name] = dict(path=str(path), sha256=sha(path))
assert not torch.cuda.is_initialized()
for name, expected in manifest.items():
    assert sha(attempt/name) == expected, name
receipt = dict(schema='R163_PROBE_CPU_TEST_V1', status='PASS' if status == 0 else 'FAIL',
    started_unix=started, finished_unix=time.time(), files=manifest, origins=origins,
    source_closure=str(candidate/'source'), cuda_initialized=False,
    real_7b_validated=False, pytest_exit_code=status, torch_version=torch.__version__)
with (attempt/'CPU.json').open('x') as stream:
    json.dump(receipt, stream, sort_keys=True, indent=2)
    stream.write('\n')
raise SystemExit(status)
