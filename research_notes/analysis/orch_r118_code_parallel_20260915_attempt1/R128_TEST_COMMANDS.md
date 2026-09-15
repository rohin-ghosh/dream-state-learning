# R128 CODE-only queue repair — CPU provenance

No GPU/provider call is part of these tests. This is not a shared-broker edit.

## Local

```sh
uv run --offline --no-project --with pytest python -B -m pytest -q tests/test_orch_r128_code_queue_recovery.py tests/test_orch_r119_code_old_parent.py
```

Result: **19 passed in 0.51s**. Bare VM Python is not claimed to have pytest.

## Native (both ovx2 and a40r wrappers)

Interpreter: `/localhome/local-rohing/v2/venv/bin/python -B -`.
Frozen source root: `/localhome/local-rohing/orch_r128_code_queue_recovery_20260915_v1`.
The native preflight used this exact import/test bootstrap before its read-only provenance checks:

```python
import sys
from pathlib import Path
root = Path('/localhome/local-rohing/orch_r128_code_queue_recovery_20260915_v1')
sys.path[:0] = [
    '/localhome/local-rohing/orch_r108_pytest_support_0854',
    str(root / 'deps/provider'),
    '/localhome/local-rohing/orch_r119_code_old_forks_20260915_v3/source',
]
import gpu
gpu.__path__[:0] = [str(root / 'source/gpu'), str(root / 'deps/overlay/gpu')]
import pytest
assert pytest.main(['-q', '-p', 'no:cacheprovider',
    str(root / 'tests/test_orch_r128_code_queue_recovery.py')]) == 0
```

Results: **17 passed in 0.41s (ovx2), 17 passed in 0.44s (a40r)**.
Vendored pytest path/hash and native interpreter are in each `NATIVE_CPU_PROVENANCE.json`.
Native first preparation lacked `orch_r119_code_old_parent`: 15 passed / 2 import failures.
That output remains `CPU_V1_MISSING_DEPENDENCY.log` on each node. Supplying the
exact frozen old transport code dependency closure fixed packaging; no test or
production guard was removed. The code-only dependency archive stays node-local.

## Runtime binding

Frozen adapter SHA256: `87c98c00f8607939706dc7010acbb0a14ff053646beaa2d3eda0088490672ad9`.
Frozen test SHA256: `418d6c331b7eb1dabb25a052477f7046ce963727616744d9195b4bf7a3d36d8c`.
VM runtime root: `/tmp/orch_r128_code_queue_recovery_20260915_v1`.
Its `RUN.py` selects the new adapter, old frozen overlay and old frozen provider;
49 exact local code/harness pins are bound in each immutable recovery document.
Original native queues/configs/claims and RUNNER.lock remain authoritative.
Only requests created at/after the recovery cutoff can be claimed. Claimed,
responded and expired requests cannot be reissued. Historical caps and
deadlines remain unchanged. Provider contention can still yield MISSING.
