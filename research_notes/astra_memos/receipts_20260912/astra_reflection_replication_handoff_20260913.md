# Reflection learner-seed 1/2 derivatives — September 13, 2026 UTC

**EDITSTOP. CPU-only support; no native preparation, GPU, network, Git or launch.**

Only the five assigned derivative files were created. Seed0's live root,
PID328732, driver, launcher, helper, captures and outcomes were not inspected or
modified. Main prospectively selected learner seeds1/2 before outcome inspection;
these files do not select seeds, retune the diagnostic, or add a new framework.
No WebFetch, curl or wget was used. Disposable test fixtures stay under `/tmp`.

## Frozen parents, unchanged

```text
0f79efa1f4e4da6a9d1ec245c09e665f7c2b7d8bce31f7e01fe01b00f95a72fc  /tmp/astra_reflection_fit_run_20260913.py
56fef18cf9102721548e769100e8368c3432d484fade1e564ad074743165841b  /tmp/astra_launch_reflection_fit_20260913.py
```

The runtime is a self-contained copy-derived implementation following the
accepted perception replication pattern. It does not import or wrap the live
parent runtime. The launcher is likewise self-contained. Parent hashes are
provenance constraints, not claims of clean model ancestry.

## Final derivative SHA256

```text
d1f572d094507f85245af2edd95608daffa8322a2d5dbae01ae31957e40ac6c9  /tmp/astra_reflection_fit_replication_run_20260913.py
f4ee5acfe91ca9b7a87246cb840a5be7afd810948f5fe883e51f9dba8302889c  /tmp/test_astra_reflection_fit_replication_run_20260913.py
cd0c702c6786fce3bf9c1e818254252f949f30b6daf1fd898dcce9d004e17710  /tmp/astra_launch_reflection_replication_20260913.py
20ee62c645ce18448fb28838a2d01eb6dd5fe1a29f198860bec2d3b8cd89dad2  /tmp/test_astra_launch_reflection_replication_20260913.py
```

This handoff's hash is returned separately to avoid recursive hashing.

## Exact delta and unchanged controls

- New scope: `authored_reflection_12train_24dev_learner_seed_replication_v1`.
  `prepare(..., learner_seed=...)` and CLI `--learner-seed` are required and
  accept only integer1 or2. Boolean, float, string, missing, seed0, or other
  values fail. `learner_recipe` returns a copy with only the seed changed.
- Each root pairs both cold fits at the SAME chosen learner seed. The seed
  governs the existing trainer RNG and epoch shuffle; it is not a corpus seed,
  prompt field, generation seed, or engine seed. Both latter seeds remain0.
- The only experimental changes are learner seed and its resulting epoch order.
  Scope, parent provenance and explicit seed fields are administrative changes.
  RECIPE's inherited scope note reflects the new scope. No other recipe value,
  optimizer behavior, base, precision, dependency, target, data selection, loss
  mask, model request, metric, claim boundary or timing ceiling changes.
- Seed is bound into plan/config and prepared training files; checked again at
  verify, worker and fit-manifest boundaries; attached to fit/readout identities,
  starts, launches, releases, readout closures, controller start/completion,
  scores, collection receipt and successful command results. Cross-seed receipts
  and integer-like booleans/floats are rejected. Failure handling remains the
  parent's evidence-preserving root/plan-bound behavior.
- **Actual worker epoch-order recomputation:** after re-encoding every prepared
  item using its loaded tokenizer and checking exact IDs/labels, rebuild native
  one-item packs and all four epoch orders with the bound learner seed. Reject
  disagreement with prepared `epoch_order` BEFORE calling `run_training`.
  This is an actual worker check, not merely a preparation-side assertion.
- Same12 authored TRAIN targets/order inventory in each arm, four epochs,
  rank8/alpha16/dropout0.05/LR1e-4/batch4/gradaccum1/no packing/max_len1024,
  full assistant target plus exactly one EOS, context/padding/template-tail
  masking and zero native truncation requirements. The legacy encoder's
  `overflow="truncate"` API value still grants no permission to truncate.
- Per root: two fits, six fresh matched OFF/fitWithdrawn/fitPresent ×
  withdrawn/present readouts,24 DEV calls per cell,144 total, eight fresh workers.
  Generation/engine seed0, greedy max192, matched LoRA-enabled OFF with null
  LoRARequest; exact authored restatement and strict A/B application stay separate.
- Runtime ceilings remain3600 seconds outer,600 per fit,300 per readout,
  30-second NVML,40-second included cleanup reserve,180-second separate collection.
  All captures and both completed fits precede any scoring. No automatic retry,
  source overwrite, aggregation, scientific promotion or multi-seed claim added.
- Launcher additionally requires `--learner-seed` matching plan AND trainer
  config, validates replication scope and frozen parent provenance, and includes
  seed in attempt/precheck/detachment/failure receipts. Controller command still
  obtains seed from its pinned plan, not an unbound worker CLI override.
- Launcher retains the corrected finish-margin rule:
  `now + 3600 + 180 + 40 + 21600 <= lease_end` (25,420 seconds), including checks
  after fresh precheck and immediately before spawn. All existing exclusive
  root/stdout, final pins, empty-CUDA precheck, PID/PGID/start-ticks and bounded
  detachment requirements remain unchanged.

## CPU validation completed

```bash
python3 -B /tmp/test_astra_reflection_fit_replication_run_20260913.py -q
REFLECTION_LEARNER_SEED=2 python3 -B /tmp/test_astra_reflection_fit_replication_run_20260913.py -q
python3 -B /tmp/test_astra_launch_reflection_replication_20260913.py -v
python3 -B /tmp/test_astra_reflection_fit_run_20260913.py -q
python3 -B /tmp/test_astra_launch_reflection_fit_20260913.py -q
```

- Derivative runtime: **46 tests pass at seed1 and46 at seed2**, final runs
  8.708 and8.948 seconds. Retains all40 parent test methods, adding six seed/delta
  checks, including tampered epoch-order rejection before optimizer execution.
- Derivative launcher: **25 tests pass**, 0.265 seconds; all21 parent test methods
  retained, plus four seed-selection/provenance/cross-seed receipt checks.
- Original CPU suites also pass unmodified: **40 runtime tests**, 7.326 seconds;
  **21 launcher tests**, 0.601 seconds. Their temporary fixtures never touch the
  live root; their native/GPU subprocess behavior is mocked.
- AST checks confirm identical ENGINE/PARAMS/base RECIPE/CLAIM definitions and
  unchanged training-item masks, corpus/API export validation, native engine,
  public binding, model loader, source freeze, cleanup and deadline helpers.
  Native generation/engine seeds are0. Seed1/2 fixture exports and model calls
  compare identically, as do training items/masks/targets; only bound seed,
  epoch-order and order-dependent batch-exposure metadata differ.
- No native tokenizer, official model load, real fit, native engine, GPU vacancy
  query or actual subprocess detachment was run. CPU fixtures are not native
  acceptance or experiment outcomes. Main owns native validation and execution.

## Main-only usage — guidance, not executed

For EACH selected seed, use a new source snapshot, root, worker-log directory,
controller stdout path and collection output. Main owns GPU1/2 assignment,
UUID/index validation and leases. Keep the accepted frozen public helper and
allocation precheck, official local Qwen files, base receipt and final source
pins; never substitute a stale helper or warm-start from seed0/perception.

Use all existing reflection prepare arguments unchanged, plus the required
selection. Run one explicit seed/root at a time; no automatic launch loop is
provided here. `$LEARNER_SEED` must be1 or2; `$PYTHON` is the exact native
interpreter that will be recorded in the new plan.

```bash
RUNTIME=/tmp/astra_reflection_fit_replication_run_20260913.py

"$PYTHON" -B "$RUNTIME" prepare \
  --learner-seed "$LEARNER_SEED" \
  --root "$ROOT" --source "$SOURCE" --model "$MODEL" \
  --probe-driver "$FROZEN_PUBLIC_HELPER" --probe-sha256 "$PUBLIC_HELPER_SHA256" \
  --binding-path "$BINDING_RECEIPT" --binding-sha256 "$BINDING_SHA256" \
  --corpus-sha256 "$HISTORICAL_CORPUS_SHA256" \
  --reflection-sha256 "$FINAL_REFLECTION_SOURCE_SHA256" \
  --source-pins-path "$SOURCE_PINS" --source-pins-sha256 "$SOURCE_PINS_SHA256" \
  --log-dir "$LOG_DIR" --gpu-index "$GPU_INDEX" --gpu-uuid "$GPU_UUID" \
  --lease-end "$LEASE_END_UNIX"

"$PYTHON" -B /tmp/astra_launch_reflection_replication_20260913.py \
  --learner-seed "$LEARNER_SEED" --root "$ROOT" --driver "$RUNTIME" \
  --driver-sha256 "$RUNTIME_SHA256" --plan-sha256 "$NEW_PLAN_SHA256" \
  --precheck "$FROZEN_ALLOCATION_PRECHECK" --precheck-sha256 "$PRECHECK_SHA256" \
  --stdout "$FRESH_CONTROLLER_STDOUT" --allow-gpu

"$PYTHON" -B "$RUNTIME" collect \
  --root "$ROOT" --plan-sha256 "$NEW_PLAN_SHA256" \
  --completion-sha256 "$NEW_COMPLETION_SHA256" --out "$NEW_COLLECTION_OUT"
```

Copy the new plan/completion hashes only from successful corresponding phases.
Collection remains separate and requires complete unscored capture closure.
Do not reuse the seed0 plan/root, auto-retry failures or change the seed mid-root.
Native helper/environment issues are Main's next work, not permission to edit
any live driver or retune these derivatives.

**EDITSTOP — five assigned files only; parent/live artifacts preserved.**
