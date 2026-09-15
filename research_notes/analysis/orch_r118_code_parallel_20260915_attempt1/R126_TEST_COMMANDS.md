# R126 capacity test commands

## Local: 43 tests

```bash
uv run --offline --no-project --with pytest python -B -m pytest -q \
  tests/test_orch_r126_code_capacity.py \
  tests/test_orch_r124_code_capacity.py \
  tests/test_orch_r119_code_old_fork.py \
  tests/test_orch_r119_code_old_admission.py
```

Actual final local result: **43 passed in 4.80s**. This uses uv's cached isolated
pytest environment, not bare VM python3.

## Each native destination: 30 CPU tests

Use `gpu/ovx2_ssh.sh` for the four ovx2 slots, or replace it with
`gpu/a40r_ssh.sh` for the three a40r slots:

```bash
bash gpu/ovx2_ssh.sh \
  'env CUDA_VISIBLE_DEVICES= PYTHONDONTWRITEBYTECODE=1 /localhome/local-rohing/v2/venv/bin/python -B -' \
  2>/tmp/r126_pytest.stderr <<'PY'
import sys
sys.path[:0] = [
    '/localhome/local-rohing/orch_r119_code_old_forks_20260915_v3/source',
    '/localhome/local-rohing/orch_r108_pytest_support_0854',
]
import gpu
gpu.__path__.insert(0, '/localhome/local-rohing/orch_r126_code_capacity_20260915_v3/source/gpu')
import pytest
raise SystemExit(pytest.main([
    '-q', '-p', 'no:cacheprovider',
    '/localhome/local-rohing/orch_r126_code_capacity_20260915_v3/source/tests/test_orch_r126_code_capacity.py',
    '/localhome/local-rohing/orch_r126_code_capacity_20260915_v3/source/tests/test_orch_r124_code_capacity.py',
]))
PY
```

Actual results: **30 passed in 5.02s on ovx2; 30 passed in 5.94s on a40r**.
The real pytest runner is vendored at the explicitly added support directory;
it is not installed into the model venv. Each destination's immutable
`/localhome/local-rohing/orch_r126_code_capacity_20260915_v3/CPU_TESTS.json`
records its interpreter, pytest module/version, harness import path, arguments,
source hashes and observation time. Tests make no GPU/provider calls. The
one-cycle integration test uses a fake engine with the actual cycle policy.

Arming is distinct from these tests: the actual CPU process commands and exact
identities are in each branch's `CPU_DISPATCH.json`; actual `ARMED.json` proves
the waiting custodian started. No successor GPU launch is claimed before the
natural-C100 release, provenance validation and fresh admission.
