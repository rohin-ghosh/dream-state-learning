"""CPU-only frozen-source validation; no admission, model, release, or launch."""

import argparse
import hashlib
import json
import os
from pathlib import Path
import sys
import time
import unittest


MODULES = (
    'tests.orch_math_feedback_uptake_r118_parallel_crash_test',
    'tests.orch_math_feedback_uptake_r118_parallel_exec_test',
    'tests.orch_math_feedback_uptake_r118_parallel_recipe_test',
    'tests.orch_math_feedback_uptake_r118_parallel_test',
    'tests.orch_math_feedback_uptake_r118_shared_test',
    'tests.orch_math_feedback_uptake_r118_final_drain_test',
    'tests.orch_math_feedback_uptake_r117_test',
)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def run(manifest_path, output):
    root = Path(__file__).resolve().parents[1]
    if os.environ.get('CUDA_VISIBLE_DEVICES') != '' or output.exists():
        raise ValueError('CPU_only_new_receipt_required')
    manifest = json.loads(manifest_path.read_text())
    for relative, digest in manifest.items():
        if Path(relative).is_absolute() or '..' in Path(relative).parts or sha(root/relative) != digest:
            raise ValueError('source_manifest_mismatch:'+relative)
    started = time.time()
    result = unittest.TextTestRunner(verbosity=1).run(unittest.defaultTestLoader.loadTestsFromNames(MODULES))
    imports = {}
    for module in tuple(sys.modules.values()):
        filename = getattr(module, '__file__', None)
        if filename:
            path = Path(filename).resolve()
            if path.is_relative_to(root) and path.suffix == '.py':
                imports[str(path.relative_to(root))] = sha(path)
    for relative, digest in imports.items():
        if manifest.get(relative) != digest:
            raise ValueError('unpinned_runtime_import:'+relative)
    if any(sha(root/relative) != digest for relative,digest in manifest.items()):
        raise ValueError('source_changed_during_CPU_tests')
    torch = sys.modules.get('torch')
    cuda = bool(torch and torch.cuda.is_initialized())
    passed = result.wasSuccessful() and not result.skipped and not cuda
    record = dict(schema='R118_MATH_FRESH_EXEC_CPU_TESTS_V1', passed=passed,
        tests=result.testsRun, failures=len(result.failures), errors=len(result.errors), skips=len(result.skipped),
        cuda_initialized=cuda, source_manifest_sha256=sha(manifest_path),
        tested_imports=imports, started_unix=started, finished_unix=time.time(),
        modules=list(MODULES), native_model_calls=0, provider_calls=0)
    with output.open('x') as stream:
        json.dump(record,stream,indent=2,sort_keys=True)
        stream.write('\n')
    if not passed:
        raise SystemExit(1)
    print(json.dumps(dict(tests=result.testsRun,passed=passed,receipt=str(output),sha256=sha(output))))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--manifest',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    arguments = parser.parse_args()
    run(arguments.manifest,arguments.output)
