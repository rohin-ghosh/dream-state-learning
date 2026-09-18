"""Bounded tiny-model CPU tests against the selected candidate5 source closure."""

import ast
import hashlib
import importlib
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
assert os.environ.get('HF_HUB_OFFLINE') == '1'
assert os.environ.get('TRANSFORMERS_OFFLINE') == '1'
sys.path[:0] = [str(candidate/'source'), str(candidate/'test_support')]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def method_asts(path):
    tree = ast.parse(path.read_bytes())
    child = next(node for node in tree.body if isinstance(node, ast.ClassDef) and node.name == 'NativeChild')
    return {method.name: hashlib.sha256(ast.dump(method, include_attributes=False).encode()).hexdigest()
            for method in child.body if isinstance(method, ast.FunctionDef)}


selected = {
    'gpu/orch_r125_continual_native.py': 'bcd716db469665d6c2070ed46d4b910d619b7366b66af2891c9ed71a5e069af6',
    'gpu/astra_experienced_event_microloop.py': '8e57909a6c4f2d988a434423a33e7a663c23696ffdb2ce402c2bb03b2fccbb70',
    'gpu/orch_guided_native.py': '559d8e6ea7002f2651748ba192a57c5cf627381f6a3994d93cb02d63011a3157',
    'gpu/orch_r145_suffix_boundary.py': '632c519fd4c5a840d13b1e9503e61f512340ee9361ef95dcd43cbaf704ee0ce5',
    'gpu/orch_r145_suffix_loss.py': 'd5e69655fd30f3317d114bd4aab2025024fdfb1521664b536d54ad61069bf026',
    'organism_v6/pcfl_vertical_train.py': '9a392dc17eab4db77416b81642def0842c5b353c5ff9aca5fcdf94a04474b078',
}
for relative, expected in selected.items():
    assert sha(candidate/'source'/relative) == expected, relative

started = time.time()
import torch
import pytest
import peft
import transformers
import tokenizers
import safetensors
import gpu

assert not torch.cuda.is_initialized()
torch.set_num_threads(1)
torch.set_num_interop_threads(1)
name = 'gpu.orch_r161_native_executor'
spec = importlib.util.spec_from_file_location(name, attempt/'orch_r161_native_executor.py')
executor = importlib.util.module_from_spec(spec)
sys.modules[name] = executor
spec.loader.exec_module(executor)
setattr(gpu, 'orch_r161_native_executor', executor)
exit_code = pytest.main([str(attempt/'test_orch_r161_native_executor.py'), '-q', '-p', 'no:cacheprovider',
                         '--basetemp', str(attempt/'pytest_tmp')])
origins = {}
for name, module in sorted(sys.modules.items()):
    if name.startswith(('gpu.', 'organism_v6.')) and getattr(module, '__file__', None):
        path = Path(module.__file__).resolve()
        assert path.is_relative_to(candidate/'source') or path == attempt/'orch_r161_native_executor.py', name
        origins[name] = dict(path=str(path), sha256=sha(path))
runtime = {}
for module in (torch, peft, transformers, tokenizers, safetensors, pytest):
    path = Path(module.__file__).resolve()
    runtime[module.__name__] = dict(version=module.__version__, path=str(path), sha256=sha(path),
        distribution_version=importlib.metadata.version(module.__name__))
peft_root = Path(peft.__file__).resolve().parent
serialization_sources = {str(peft_root/relative): sha(peft_root/relative)
                        for relative in ('peft_model.py', 'config.py', 'utils/save_and_load.py')}
for relative, expected in selected.items():
    assert sha(candidate/'source'/relative) == expected, relative
receipt = dict(schema='R161_EXECUTOR_REPAIR_CPU_V1', status='PASS' if exit_code == 0 else 'FAIL',
    execution_kind='CPU_TEST_ONLY', real_7b_validated=False, legacy_pickle_constructor_forbidden=True,
    fresh_constructor_validation_allowed_pending_review=True, admitted_restore_cpu_tested=exit_code == 0,
    source_closure=str(candidate/'source'), test_support=str(candidate/'test_support'), selected_sources=selected,
    native_method_ast_sha256=method_asts(candidate/'source'/'gpu/orch_r125_continual_native.py'),
    runtime=runtime, serialization_sources=serialization_sources, origins=origins, pytest_exit_code=exit_code,
    started_unix=started, finished_unix=time.time(), cuda_visible_devices=os.environ['CUDA_VISIBLE_DEVICES'],
    cuda_initialized=torch.cuda.is_initialized(),
    files={name: sha(attempt/name) for name in ('orch_r161_native_executor.py', 'test_orch_r161_native_executor.py',
                                             'run_cpu.py')})
assert not receipt['cuda_initialized']
with (attempt/'CPU.json').open('x') as stream:
    json.dump(receipt, stream, indent=2, sort_keys=True)
    stream.write('\n')
raise SystemExit(exit_code)
