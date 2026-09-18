"""Read-only candidate3 probe semantics, tiny CPU models, isolated diagnostic receipts."""

import hashlib
import importlib.metadata
import importlib.util
import json
import os
from pathlib import Path
import sys
import time


attempt = Path(__file__).resolve().parent
candidate = Path('/localhome/local-rohing/orch_r158_matched_node4_20260917_attempt5')
assert os.environ.get('CUDA_VISIBLE_DEVICES') == ''
assert os.environ.get('PYTHONDONTWRITEBYTECODE') == '1'
assert os.environ.get('HF_HUB_OFFLINE') == os.environ.get('TRANSFORMERS_OFFLINE') == '1'
sys.path[:0] = [str(candidate/'source'), str(candidate/'test_support')]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


expected = {
    'orch_r161_native_executor.py': 'b033fbe4f1e8db5fa071e6c47678706f6e2b054d54a505947d8e4161075bea15',
    'orch_r163_executor_probe.py': '99c114f4cd68dbff86afb16ec39544460cacb68fdbff60a513b59eb801227422',
}
assert sha(candidate/'source'/'gpu/orch_r125_continual_native.py') == 'bcd716db469665d6c2070ed46d4b910d619b7366b66af2891c9ed71a5e069af6'
for filename, expected_sha in expected.items():
    assert sha(attempt/filename) == expected_sha
files_before = {filename: sha(attempt/filename) for filename in (*expected, 'test_orch_r163_probe_qwen_cpu.py', 'run_cpu.py')}
started = time.time()
import torch
import peft
import transformers
import pytest
import gpu

torch.set_num_threads(1)
torch.set_num_interop_threads(1)
assert not torch.cuda.is_initialized()
for filename in expected:
    name = 'gpu.'+Path(filename).stem
    spec = importlib.util.spec_from_file_location(name, attempt/filename)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    setattr(gpu, Path(filename).stem, module)
exit_code = pytest.main([str(attempt/'test_orch_r163_probe_qwen_cpu.py'), '-q', '-s', '-p', 'no:cacheprovider',
                         '--basetemp', str(attempt/'pytest_tmp')])
diagnostics = []
for path in sorted((attempt/'pytest_tmp').glob('*/DIAGNOSTIC.json')):
    if path.parent.is_symlink():
        continue
    document = json.loads(path.read_bytes())
    diagnostics.append(dict(path=str(path), sha256=sha(path), dtype=document['dtype'],
        checkpointing=document['checkpointing'], dropout=document['lora_dropout'], nonzero_B=document['nonzero_lora_B'],
        state_restored=document['state_restored'], comparisons={name: {key: value for key, value in comparison.items()
            if key not in ('gradients', 'adapter')} | {
                'gradients': {key: value for key, value in comparison['gradients'].items() if key != 'parameters'},
                'adapter': {key: value for key, value in comparison['adapter'].items() if key != 'parameters'}}
            for name, comparison in document['comparisons'].items()}))
origins = {}
for name, module in sorted(sys.modules.items()):
    if name.startswith(('gpu.', 'organism_v6.')) and getattr(module, '__file__', None):
        path = Path(module.__file__).resolve()
        assert path.is_relative_to(candidate/'source') or path.parent == attempt, name
        origins[name] = dict(path=str(path), sha256=sha(path))
assert files_before == {filename: sha(attempt/filename) for filename in files_before}
receipt = dict(schema='R163_GRADIENT_CPU_DIAGNOSIS_V1', execution_kind='CPU_TEST_ONLY',
    status='PASS' if exit_code == 0 else 'DIAGNOSTIC_MISMATCH_OR_ERROR', pytest_exit_code=exit_code,
    started_unix=started, finished_unix=time.time(), real_7b_validated=False,
    cuda_initialized=torch.cuda.is_initialized(), cuda_visible_devices=os.environ['CUDA_VISIBLE_DEVICES'],
    files=files_before, origins=origins, diagnostics=diagnostics,
    runtime={module.__name__: dict(version=module.__version__, distribution_version=importlib.metadata.version(module.__name__),
        path=module.__file__) for module in (torch, transformers, peft, pytest)},
    cpu_capability=torch.backends.cpu.get_cpu_capability(), mkldnn_enabled=torch.backends.mkldnn.enabled)
assert receipt['cuda_initialized'] is False
with (attempt/'CPU.json').open('x') as stream:
    json.dump(receipt, stream, indent=2, sort_keys=True)
    stream.write('\n')
raise SystemExit(exit_code)
