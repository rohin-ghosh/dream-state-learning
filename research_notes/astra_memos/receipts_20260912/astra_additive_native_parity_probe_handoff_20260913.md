# Native parity scratch probe — EDITSTOP

September 13, 2026. Ready for Main's independent review and possible native
profiling/authorization, NOT authorization to execute. No native model,
tokenizer, GPU, network, lifecycle, score or optimizer execution occurred here.
No frozen source or endpoint was edited. Baseline drift remains unresolved.

## Owned files and CPU checks

- `gpu/astra_additive_native_parity_probe.py` SHA256
  `a331210a8f230c4ee3b5ff3cbe1fcef09a26925502fb9716c7e3ec617d914b7a`
- `tests/test_astra_additive_native_parity_probe.py` SHA256
  `0a2b398b15577231664e864e1297060a4e063ecb0f75df810b47fa7fd2891d8c`
- This handoff is the only other edited file. Its hash is in the final response.

Executed CPU-only:

```sh
python3 -B -m unittest discover -s tests -p test_astra_additive_native_parity_probe.py -v
```

23 tests PASS in 0.256 seconds. Fixtures execute mocked OLD/NEW trace seams,
not the native trainers. Coverage: first-forward/backward stop before any
step/save/second row, original OLD division versus NEW loss expression,
nested recomputation, natural RNG transitions without reseeding by observer,
operation/observer failures, existing-tracer refusal/restoration, exact anchor
drift, scalar byte hashing, input/mask/optimizer checks, finite gradients and
unchanged parameters, source/config binding, fresh preparation, strict JSON,
partial/tampered receipts and write-once comparison.

A separate stdlib-only `bind_inputs` check passed all nine actual historical
and source pins below and located both frozen AST seams. No torch/peft/
transformers import occurred. First actual occurrence is
`own-repair:seed0:EXTRA_MEMORY:000`, 169 input tokens, 24 supervised tokens,
from the complete 38-occurrence seed0 input. This was file inspection, not
native preparation or a new outcome reduction.

## Exact interception and limits

OLD calls unchanged `trainer.run_training` with original seed0 items/config,
parent, corpus SHA/name. NEW calls unchanged additive
`run_training(..., arm="MEMORY_ONLY", trainer=trainer)` with the exact paired
object, original config/parent/corpus SHA. Both use the frozen reflection
`load_native_model`; its imports use offline/local-only loading.

`sys.settrace` observes the actual frozen frames. AST locates but never
rewrites code. OLD `_run_training`: forward line 812, backward line 818.
NEW `backward_components`: forward line 214, backward line 216. Each seam
must be an unambiguous exact single-line expression in its pinned file.
After the first backward returns, the next line event raises private
`FirstBackwardCaptured(BaseException)` BEFORE the next original statement.
Separate call-event traps reject Python `torch.optim.*.step` and
`save_pretrained` before their bodies. The tracer is restored on every exit.

No extra seed setting, optimizer step, clipping, target alteration, readout,
adapter saving, forced equal RNG, or deterministic/backend override. Original
bf16/CUDA/checkpoint, rank8/alpha16/dropout.05/LR3e-5, batch1/accum1,
8epochs/max_steps0/max_len1024 settings remain unchanged. The stop is NOT a
new max_steps setting. Natural OLD `(loss / cfg.grad_accum).backward()` and
NEW `loss.backward()` remain different expressions. Model/base files and
complete original-parent inventory are checked before model loading; actual
warm initialization must match historical initialized/source/trainable
inventories. The first executed tensor IDs, labels, and 2d attention mask
must match the pinned encoding; position_ids remain absent as in both paths.

This is an instrumented comparison of the trainer paths, NOT replay of every
historical runner preamble/import or an uninstrumented historical process.
Observers hash/synchronize tensors and perturb timing/allocation. The warm
initialization boundary follows natural trainer seeding and fresh base load;
it is not a pre-base-load RNG observation. Backend flags/configuration are
not profiler proof of which kernel executes. Single-forward/backward equality
does not establish later-step, whole-fit, repeatability or scientific parity.
A difference localizes a first observed boundary, not its cause.

## API, output and failure meaning

Schema: `astra_additive_native_first_backward_20260913_v1`.

- `prepare(...)`: stdlib-only nine-file pin/AST/config check; creates fresh
  `ROOT/plan.json`, returns `plan`, `plan_sha256`, `native_authorized:false`.
- `worker(..., path="OLD"|"NEW", allow_native=True)`: one separately invoked
  OS process per path, fresh base/parent/optimizer; 300-second alarm inclusive
  of model hashing/loading and scratch completion. Requires `-B`, exact
  native interpreter/hash, current Main-supplied boot ID and one exact GPU
  UUID in `CUDA_VISIBLE_DEVICES`, offline flags and original package versions.
- `compare(...)`: two exact pinned completed receipts, same plan/probe/row,
  distinct PIDs and all six phases. Writes fresh JSON; no score or pass gate.

Each `ROOT/OLD` or `ROOT/NEW` is claimed by exclusive directory creation;
existing directories are never reused/retried. Files use exclusive creation.
Outputs: `started.json`, `environment.json`, `path.log`, six phase JSON files,
and `receipt.json` (or `probe_failure.json` on failure). Six phases are
`before_init`, `after_init`, `before_forward`, `after_forward`,
`before_backward`, `after_backward`. Each has Python, torch CPU and visible
CUDA RNG hashes plus an assertion that the observer itself consumed no RNG.
Initial trainable tensor hashes/shapes/dtypes/devices, actual input hashes,
optimizer defaults and empty state, loss/tensor hash, checkpoint/dropout/
attention/backend settings and final finite gradient hashes are recorded.
After backward: trainable parameters must remain byte-equal to their initial
state, every trainable gradient finite/present, and base gradients absent.
Environment receipt includes package/CUDA/cuDNN/device and relevant RNG/
allocator/backend environment settings; it contains no machine hostname.

Successful receipt status is `FIRST_BACKWARD_CAPTURED_ZERO_UPDATES` with
`optimizer_steps=adapter_saves=readouts=0`. NEW's unchanged frozen cleanup
writes `scratch/failure.json` for the INTENTIONAL interruption and an empty
`scratch/steps.jsonl`; these are retained, not erased or called a completed
fit. OLD cleanup also rechecks its parent. Any other scratch output or any
nonempty step journal rejects success. Failed-phase logs remain partial;
failure is not an equality result. Comparison emits phase-wise `rng_equal`,
initial/input/settings/optimizer/environment/gradient equality, actual first
losses, and `automatic_pass:false`. Receipts refer to absolute observation
paths: compare where those paths remain available; do not edit copied receipts.

## Deployment and prospective commands — Main only, NOT executed

Deploy the probe as a standalone file (no project imports or PYTHONPATH
requirement). Make the exact nine files below available; prepare binds their
absolute deployment paths. Preserve the model and original-parent absolute
paths in the archived plans; the probe does not relocate/modify those inputs.

```sh
python3 -B "$PROBE" prepare \
  --old-root "$OLD_SEED0_ROOT" --new-root "$NEW_SEED0_ROOT" \
  --trainer "$FROZEN_TRAINER" --additive "$FROZEN_ADDITIVE" \
  --reflection "$FROZEN_REFLECTION" --out "$FRESH_ROOT" \
  --gpu-uuid "$MAIN_PLANNED_GPU_UUID" --expected-boot-id "$MAIN_CURRENT_BOOT_ID"

# Only after Main's separate review, profiling and authorization:
"$PINNED_NATIVE_PYTHON" -B "$PROBE" worker \
  --plan-path "$FRESH_ROOT/plan.json" --plan-sha256 "$PLAN_SHA256" \
  --path OLD --allow-native
"$PINNED_NATIVE_PYTHON" -B "$PROBE" worker \
  --plan-path "$FRESH_ROOT/plan.json" --plan-sha256 "$PLAN_SHA256" \
  --path NEW --allow-native

python3 -B "$PROBE" compare \
  --old-receipt "$FRESH_ROOT/OLD/receipt.json" --old-sha256 "$OLD_RECEIPT_SHA256" \
  --new-receipt "$FRESH_ROOT/NEW/receipt.json" --new-sha256 "$NEW_RECEIPT_SHA256" \
  --out "$FRESH_COMPARISON_JSON"
```

Native interpreter recorded in both plans:
`/localhome/local-rohing/v2/venv/bin/python` (binary pin also checked).
Main supplies `CUDA_VISIBLE_DEVICES` as the actual planned UUID and
`HF_HUB_OFFLINE=TRANSFORMERS_OFFLINE=1`; use `-B` to avoid frozen-source
bytecode writes. Run workers serially in separate processes, not two calls
inside one imported interpreter. There is no scheduler, launcher, collection
or GPU-query endpoint. Main must retain fresh all-process vacancy/lease checks
and an outer hard deadline with owned-process-only cleanup (e.g. 330 seconds
plus 10 seconds forced cleanup per worker). Python's 300-second alarm cannot
guarantee immediate interruption of a stuck C++/CUDA call. Runtime feasibility
is unmeasured; failure/timeout is retained, not followed by automatic retry.
Capture each command's stdout/stderr/exit in a fresh external holder log.

## Closed historical/source inventory

Local OLD root:
`/tmp/astra_own_replay_repair_native_20260913_attempt1/own_replay_repair_seed0_20260913_attempt1`

Local NEW root:
`/tmp/astra_additive_replay_native_20260913_attempt1/additive_replay_seed0_20260913_attempt1`

| Input | SHA256 |
| --- | --- |
| OLD `plan.json` | `54c27ab8043f23729d813b256b73749fc1694d552fa5cb75283dc5a0d83c3e64` |
| NEW `plan.json` | `77a7e3f39005e10c0f3085dc68aabdebc31f33f9684925125c2a261039555c45` |
| OLD `training_EXTRA_MEMORY.json` | `7c0c9c7fd452e5e311c63143944b8d8d6a60508fd109c8623f45babec9f2735a` |
| NEW `paired.json` | `769fafd87b24c276fec80f776e06cf81e66dae596760f9f026879d8fd8c8e3c9` |
| OLD `run/EXTRA_MEMORY_fit/adapter/train_manifest.json` | `56977860d3241b190c3dcaacabc40db1d23bd56846b9dcfb7c7e2d33fc2ec448` |
| NEW `run/MEMORY_ONLY_fit/adapter/train_manifest.json` | `a6ed70bc1c89e6a34b541694ee3df6ab9b167f693dee00e2f24d25a47ffcd8a7` |
| `/tmp/astra_level1_real_record_source_20260913_attempt1/organism_v6/train_adapter_v3.py` | `7bbf165fcb4b8ae3a1180328bcd19f57382c30516daddc95fd61e8a2c749fad7` |
| `/tmp/astra_additive_replay_train_20260913.py` | `3f2e73ef69b12c8db211e1d3043e4559713e036ffe09571ab8bc4c5199a426a0` |
| `/tmp/astra_reflection_fit_run_20260913.py` | `0f79efa1f4e4da6a9d1ec245c09e665f7c2b7d8bce31f7e01fe01b00f95a72fc` |

No cause inferred, no fit rerun, and no scientific acceptance/promotion claim.
EDITSTOP.
