# L2 public-record detached launcher handoff

Scope: CPU-only launcher support; no native preparation, GPU, network, Git, or launch operations performed. Runtime, helpers, originals, repository, and existing runs are unchanged. Only this handoff and the two named sidecar Python files are deliverables.

## Final artifacts and validation

- `/tmp/astra_launch_l2_public_record_20260913.py`: SHA256 `6b15e9ca84888aac0a00071021e829e6a829837fba621701a9d34a8dafb115da`
- `/tmp/test_astra_launch_l2_public_record_20260913.py`: SHA256 `1cb7cbb6f57b1c494ead11fa718a138f8bbb19c72895d1ac1ad8a34f691c2352`
- `python3 -B /tmp/test_astra_launch_l2_public_record_20260913.py -v`: **19 CPU tests passed** (1.486 seconds). Allocation precheck and controller subprocesses are mocked; fixtures are disposable CPU-only trees. Launcher `--help` also passed.
- The handoff's own SHA256 is reported separately, not embedded in itself.

## Frozen contract

- Runtime `gpu/astra_l2_public_record_dev.py`: `213c2a2f508815eef752c72424f5dca64b76c9edb963f7ed6f68d5522c18853e`.
- Targeted precheck: `32d366afc432d9e8dcf0c188cbf0725cdadfcc68a1a0f8e0b11532ca7629862a` (local reference `/tmp/astra_node3_targeted_prelaunch_20260913.py`; Main supplies the staged native path).
- Runtime/core schemas: `astra_l2_public_record_runtime_v1` / `l2_public_record_dev_v0`.
- Four-file source inventory: `organism_v6/__init__.py`, `organism_v6/l2_public_record_dev.py`, `organism_v6/train_adapter_v3.py`, `gpu/astra_l2_public_record_dev.py`. Actual bytes must match the final plan. Driver must be that source snapshot's runtime.
- Planned GPU index **3**, UUID **GPU-e1277146-04f2-c38f-d1ae-1a98132f907e**. Explicit `--allow-gpu` is required.
- Main reports native preparation passed for `/localhome/local-rohing/astra_diagnostics/l2_public_record_20260913_attempt1`, final plan `da6a2d651d152979afee1ab862ab9218ef571149705e4bff5ad1a4ebc0289125`, with protocol evidence logged/pushed at `e8c267f4`. These native results are Main's report, not sidecar validation.

## Bounds, preservation, and acceptance

Controller budget is **5400 seconds**, separate collection **180 seconds**, and required post-finish lease margin **21600 seconds**: `now + 27180 <= lease_end`. Cleanup is already inside the controller budget, not an additional 40 seconds. Lease and pins are rechecked after the bounded 60-second precheck and before spawn. Precheck runs with `CUDA_VISIBLE_DEVICES` empty and offline environment settings.

Only an exactly prepared root is accepted: `prepare_started.json`, `plan.json`, `calls.json`, `world.json`, `model_binding.json`. Prior-start, terminal, failure, seal, extra-file, altered-pin, or malformed-plan states are rejected. Runtime definitions perform CPU-only read validation; the launcher does not prepare or collect.

The exclusive claim is the **external sibling** `ROOT.launcher`; its existence forbids another attempt even with a different stdout. All launcher evidence (`started.json`, `precheck.json`, `detached.json` or `failure.json`) stays there, never in the sealed native root. Stdout must be a fresh external path: existing files, symlinks/symlink parents, protected-path overlap, and exclusive-writer races are rejected. Failed claims are preserved, not retried or overwritten.

Detached controller uses the pinned prepared interpreter, a new session, null stdin, and merged external stdout/stderr. The returned receipt includes exact PID, PGID, process start ticks, command, pins, budgets/ceiling, stdout, and claim directory. Controller ceiling is measured by the pinned runtime on controller entry. Unknown post-spawn identity preserves the known PID and `controller_may_be_running=true` rather than retrying or killing an unverified process. Collection remains Main's separate operation.

Tests cover final pin/schema/config rejection, opt-in, GPU binding, source/helper/prepared-file mutation and hardlinks, prior-start/terminal markers, exclusive claims and concurrent races, stdout safety, exact lease boundary and elapsed precheck time, precheck failure/timeout, root/source mutation during precheck, unknown identity, and immediate controller sealing without subsequent launcher writes inside the root.

## Main-only CLI (not executed)

Stage the frozen sidecar and precheck on the native host. Set `FINAL_TARGETED_PRECHECK` to the staged hash-matching precheck and `FRESH_EXTERNAL_CONTROLLER_STDOUT` to a nonexistent external output path with existing plain parent directories. Do not precreate `ROOT.launcher`.

```bash
ROOT=/localhome/local-rohing/astra_diagnostics/l2_public_record_20260913_attempt1
SOURCE="$(jq -r '.spec.source' "$ROOT/plan.json")"
PYTHON="$(jq -r '.python' "$ROOT/plan.json")"

CUDA_VISIBLE_DEVICES= "$PYTHON" -B /tmp/astra_launch_l2_public_record_20260913.py \
  --root "$ROOT" \
  --driver "$SOURCE/gpu/astra_l2_public_record_dev.py" \
  --driver-sha256 213c2a2f508815eef752c72424f5dca64b76c9edb963f7ed6f68d5522c18853e \
  --plan-sha256 da6a2d651d152979afee1ab862ab9218ef571149705e4bff5ad1a4ebc0289125 \
  --precheck "${FINAL_TARGETED_PRECHECK:?set staged precheck path}" \
  --precheck-sha256 32d366afc432d9e8dcf0c188cbf0725cdadfcc68a1a0f8e0b11532ca7629862a \
  --stdout "${FRESH_EXTERNAL_CONTROLLER_STDOUT:?set fresh external stdout path}" \
  --allow-gpu
```

No experiment, recipe, data, precision, dependency, or scientific-claim changes. Main owns native launch and subsequent collection. **EDITSTOP**.
