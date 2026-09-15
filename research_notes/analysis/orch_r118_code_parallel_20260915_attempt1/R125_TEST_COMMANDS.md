# R125 exact pytest harness provenance — September 15, 2026

The claimed tests did **not** run with bare `python3 -m pytest`. Neither a
system installation nor installation into the model venv is required or claimed.

## Local 34 tests

Run from the repository:

```bash
uv run --offline --no-project --with pytest python -B -m pytest -q \
  tests/test_orch_r125_code_checker_recovery.py \
  tests/test_orch_r119_code_independent.py \
  tests/test_orch_r124_code_capacity.py
```

This uses uv's already-cached isolated pytest environment. Original final run:
34 passed in 2.35s. Requested revalidation: 34 passed in 2.53s.
Actual revalidation interpreter `/home/rohing/.cache/uv/builds-v0/.tmphVEIFf/bin/python`;
pytest 9.1.1 loaded from
`/data/home/rohing/.cache/uv/archive-v0/gQNbv0KfvnaJ_g5l/lib/python3.12/site-packages/pytest/__init__.py`.
The temporary uv interpreter path is evidence, not a stable command prerequisite.

## Native 17 tests: vendored pytest, not installed model-venv pytest

```bash
bash gpu/ovx3_ssh.sh \
  'env CUDA_VISIBLE_DEVICES= PYTHONDONTWRITEBYTECODE=1 /localhome/local-rohing/v2/venv/bin/python -B -' \
  2>/tmp/r125_pytest.stderr <<'PY'
import sys
sys.path[:0] = [
    '/localhome/local-rohing/orch_r118_code_parallel_source_20260915_v4_drain/source',
    '/localhome/local-rohing/orch_r111_f1_pytest_support',
]
import gpu
gpu.__path__[:0] = [
    '/localhome/local-rohing/orch_r125_code_checker_recovery_20260915_v1/gpu',
    '/localhome/local-rohing/orch_r119_code_independent_20260915_v2/gpu',
]
import pytest
raise SystemExit(pytest.main([
    '-q', '-p', 'no:cacheprovider',
    '/localhome/local-rohing/orch_r125_code_checker_recovery_20260915_v1/tests/test_orch_r125_code_checker_recovery.py',
    '/localhome/local-rohing/orch_r119_code_independent_20260915_v2/tests/test_orch_r119_code_independent.py',
]))
PY
```

The same 17 tests passed originally in 0.50s, and on requested revalidation in
0.49s. Actual pytest 9.1.1 module:
`/localhome/local-rohing/orch_r111_f1_pytest_support/pytest/__init__.py`, SHA256
`ee37885c9583f843390684dfb496907f87a0905128e7a3cf4ad227f49ff34c2d`.
This is the real pytest runner using an existing vendored dependency tree,
not a custom assertion runner. No provider/GPU calls or native actor changes.

Native immutable revalidation receipt:
`/localhome/local-rohing/orch_r125_code_checker_recovery_20260915_v1/PYTEST_HARNESS_PROVENANCE.json`.
Its `sys_path_prefix` records the path after pytest added test directories;
the **pre-import** paths are the explicit bootstrap lines above. Original
CPU_TESTS.json and original test results remain unchanged.
