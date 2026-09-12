# V3 optional weight warm start — 2026-09-12

**EDIT-STOP.** Implemented only in:

- `/data/home/rohing/dream-state/organism_v6/train_adapter_v3.py`
- `/data/home/rohing/dream-state/tests/test_train_adapter_v3.py`
- This requested handoff: `/tmp/astra_v3_warmstart_handoff_20260912.md`

No GPU, network, Git, model download, native model generation, other contributor
file change, live snapshot edit, continuation corpus creation, or launch occurred.
Main's active native `a9a7` source snapshot was not touched. Read the supplied
fading-sequence design; implemented only its bounded optional weight-loading seam,
not scheduling, new evaluation, memory diagnostics, child sleep, or claim changes.

## Interface and default compatibility

```python
run_training(items, tok, base_model, cfg, out_dir,
             corpus_sha=None, corpus_name=None, log=print,
             init_adapter=None)
```

The new argument is appended after all original arguments. `--init-adapter PATH`
is an optional CLI argument **outside TrainConfig**. `TrainConfig`, its fields,
defaults, and `asdict(cfg)` are unchanged. When unused, the public function
delegates to the original training path without warm-start metadata, stricter
output policy, or altered optimizer/save behavior. Fresh fitting remains fresh;
the original empty-corpus behavior and original default CLI config remain.

Checked against the local `06c90d1b` seed0 source archive using AST comparisons:
**TrainConfig is identical and all nine original test function bodies are
identical.** No original test was weakened or replaced.

Example invocation shape for Main's separately audited continuation, not a launch
performed or an experiment chosen by this contributor:

```bash
python -B -m organism_v6.train_adapter_v3 \
  --corpus "$AUDITED_CONTINUATION_CORPUS" --out "$FRESH_CHILD" \
  --model "$PINNED_BASE" --init-adapter "$VERIFIED_PARENT" \
  --rank 8 --alpha 16 --dropout 0.05 \
  --target-modules q_proj,k_proj,v_proj,o_proj,gate_proj,up_proj,down_proj \
  --layers all --lr "$MAIN_SELECTED_LR" --epochs "$MAIN_SELECTED_EPOCHS" \
  --seed "$MAIN_SELECTED_SEED" --batch-size 4 --grad-accum 1 --no-pack --max-len 512
```

Warm-start CLI model/tokenizer loads explicitly use `local_files_only=True`.
The API takes an already-loaded, unwrapped base, exactly as before. Never pass
the adapter as `--model` or supply a prewrapped PEFT model. Use real absolute
parent/output paths, not symlink aliases. Rank/alpha/dropout/targets/layers/bias
must match the parent; LR, phase seed, and epoch count may change. No adapter
merge, nested adapter, optimizer/RNG restoration, or parent write is performed.

## Validation and loading contract

1. Require a fresh child path, disjoint from the parent and any local base-model
   directory. Reject symlink aliases and symlink/special files in the parent.
2. Require parent `DONE`, `train_manifest.json`, `adapter_config.json`, no
   `EMPTY_CORPUS`, a completed finite V3 manifest, and exactly one weight file:
   `adapter_model.safetensors` or `adapter_model.bin`.
3. Bind the full parent-file SHA256 inventory before initialization. Validate
   base identity in the parent config/manifest, the supplied model identity and
   actual loaded model name, parent/base layer count, full parent LoRA recipe,
   and the current native PEFT LoRA configuration.
4. Reject incompatible rank/alpha/dropout/targets/layers/bias, rank/alpha patterns,
   DoRA, RS-LoRA, modules-to-save, unknown nonmetadata configuration, and other
   structural deviations from the requested standard LoRA. Reject SVD init,
   frozen-A continuation, and prewrapped/adapted base inputs.
5. Inject exactly one fresh `default` adapter, then load the complete saved
   canonical adapter state into that same adapter with native PEFT state APIs.
   This is one injection plus state loading, NOT nesting `from_pretrained` over
   another injected adapter. No fallback to random initialization exists.
6. Compare source keys exactly to the native destination adapter keys; require
   full LoRA A/B-only coverage, matching shapes, floating tensors and finite
   values. `.bin` is loaded on CPU with `weights_only=True`; safetensors also
   loads on CPU. Missing/extra/partial/corrupt/nonfinite weights are rejected.
7. Validate the full initialized state against the full source state **after
   explicit source-to-destination dtype conversion**, using per-tensor shape,
   dtype and raw-byte hashes. Record conversions; do not claim unqualified bit
   parity across precision changes. Values that overflow to nonfinite on cast
   are rejected. All non-LoRA parameters must be frozen, every expected LoRA A/B
   parameter trainable, and exactly one adapter active.
8. Construct a new optimizer normally and require its initial state dictionary
   to be empty. Record actual defaults and class. Only LoRA parameters are in
   the optimizer; base trainability is checked again before save.
9. Reject nonfinite continuation batches/final LoRA state rather than producing
   a valid `DONE`. Check parent hashes after loading, before/after child saving,
   and at function exit, including failure exit. Any failure removes `DONE`
   only from an output this invocation actually created; a creation race never
   deletes another writer's marker. Partial output remains for inspection.

Output data segmentation, native masking/encoding, packing, training loop,
step counting, and readout definitions were not redesigned.

## Manifest additions — ONLY when warm start is used

`train_manifest.json["config"]` remains the original TrainConfig dictionary.
The new `warm_start` object contains:

```text
mode: WEIGHT_WARM_START_FRESH_OPTIMIZER
optimizer_initialization: fresh_per_write
optimizer_state_restored: false
optimizer_state_saved: false
optimizer_class: actual fully qualified class name
optimizer_defaults: actual defaults, including phase LR
optimizer_initial_state_entries: 0
parent_path: resolved parent directory
parent_files: complete pre-write relative-file SHA256 inventory
parent_files_after: identical post-save inventory
parent_unchanged: true
source_state: tensor name -> {shape, dtype, raw-byte sha256}
initialized_state: tensor name -> {shape, dtype, raw-byte sha256}
initialized_loaded_state_check: true
equality_scope: exact after explicit dtype conversion, before any update
dtype_conversions: only changed tensor dtypes, source and initialized
final_state: finite post-update tensor inventory
trainable_names: exact LoRA A/B parameter names
base_frozen: true
adapter_count: 1
phase_seed: current cfg.seed
parent_cumulative_steps: previous cumulative steps, or original parent steps
phase_steps: current completed optimizer-step count
cumulative_steps: parent cumulative + phase steps
trainer_sha256: current trainer source hash
```

Original `train_meta.json`, `DONE`, and adapter weight/config artifacts remain in
their original layouts. New warm-start manifests can be parents of later writes,
but every separate call again initializes a fresh optimizer. This is explicitly
**not true optimizer resume**: the original trainer never saved AdamW moments,
RNG state, or a data cursor. It is authored post-training, **not child sleep**.

## Tests and exact local counts

Used the existing offline CPU PyTorch interpreter:

```bash
PYTHONDONTWRITEBYTECODE=1 HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 OMP_NUM_THREADS=1 \
  /tmp/astra_preservation_cpu_20260912/bin/python -B tests/test_train_adapter_v3.py
python3 -B -m organism_v6.train_adapter_v3 --help
```

**21 test functions, zero failures; direct runner prints `21/21 passed` with
7 skip notices. Do not interpret that as 21 native passes.** Precisely:

- Original nine tests are unchanged. Six run completely; the parser test runs
  its assertions but skips its optional PEFT `lora_config` branch; two original
  native tiny-model tests skip entirely because native packages are unavailable.
- Twelve new tests: eight run completely (six dependency-light tests plus two
  actual CPU-PyTorch tensor/trainability tests); four actual PEFT/Transformers
  tiny-model tests are implemented but skip entirely on this VM.
- Thus **14 fully exercised functions, one partially exercised function, six
  wholly skipped functions**, and seven skip notices counting the parser branch.
- Available: PyTorch 2.8.0+cpu. Missing locally: PEFT, Transformers, safetensors,
  pytest, and NumPy. No dependencies were installed/downloaded. Tensor hash checks
  use raw-byte chunks without requiring NumPy; its optional PyTorch warning does
  not affect the passing CPU tensor tests.

New runnable tests cover default config/delegation identity; LR changes without
structural changes; parent completeness/hashes; stale/overlap/symlink paths;
missing/ambiguous artifacts; parent mutation and output-creation races; strict
saved LoRA configuration; exact tensor keys/shapes/finiteness/dtypes; and one-
adapter/LoRA-only trainability.

The four new native tiny-model tests, ready for Main's native **CPU** environment,
cover full loaded weights BEFORE updates, zero-epoch child equality, finite update
at changed LR, a zero-LR later phase, fresh optimizer state on each phase, parent
immutability, unchanged frozen base tensors, cumulative steps, no nesting, wrong
base/rank/alpha/dropout/targets/layers/bias, advanced-structure rejection,
missing/partial/extra/wrong-shape/nonfinite/integer/corrupt weights, and empty writes.

## Required Main validation and limitations

Run the same direct test file with Main's native interpreter against a **fresh
source copy containing these changes**, offline and CPU-only. Require **21/21
with no skip notices** before using the warm-start path for a GPU write. The
installed PEFT integration and the original nine native test paths could not be
executed by this contributor; this is the main outstanding validation limitation.
Do not silently count skipped native tests as evidence of successful loading.

The parent checkpoint is bound by full file hashes, but original V3 manifests do
not contain authenticated full base-file inventories. Compatibility here checks
parent/loaded base identity, layer count and exact adapter structure, not original
base byte provenance. Main must retain its existing external model/source pins
and supply the unmodified base. No base-origin or clean-lineage claim is added.

Use a nonempty target-bearing corpus for zero-update checkpoint tests:
`epochs=0` means zero updates; `max_steps=0` still means no step cap, as before.
`lr=0` with positive epochs counts optimizer steps while leaving weights unchanged.
Warm empty/no-target writes fail rather than creating a checkpoint. General
trainer corpus semantics are not narrowed to a specific continuation schedule.

The corrected birth-material figures are 4,517 input / 912 target tokens **per
epoch**, 18,068 / 3,648 **total across four epochs**, not repeated per-epoch totals.
No new continuation dataset or token accounting claim was produced here.

**EDIT-STOP. Main owns native CPU validation, source publication, supervision,
budget, checkpoint selection, and any future continuation launch.**
