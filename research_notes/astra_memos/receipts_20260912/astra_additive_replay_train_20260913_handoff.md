# Additive replay trainer — candidate EDITSTOP

2026-09-13. Candidate implementation only. Main owns protocol/runner/native
preparation/launch. No direct agent-message tool; this owned handoff is the seam.

```python
load_trainer(path=TRAINER_PATH) -> frozen_trainer
prepare_pair(extra_memory_encoding, replay_encoding, *, seed, source_pins) -> paired
run_training(paired, tokenizer, base_model, cfg, out_dir, *, arm,
             init_adapter, expected_parent_files, trainer=None,
             corpus_sha=None, log=print) -> manifest
```

`arm` is MEMORY_ONLY or ADDITIVE. Inputs to prepare_pair are exact old flat
`training_EXTRA_MEMORY.json` and `training_REPLAY.json` objects, not new rows.
The old canonical file hashes, encoder self-hashes, item/epoch hashes,8orders,
moriginal+24extra placement, item kinds, lineage and audits will be checked.
All old EXTRA_MEMORY IDs/items/orders remain unchanged. Pair extra occurrence
index0..23 bijectively with replay observation index0..23 in existing frozen
source order. No balancing rotation or phase-dependent remapping.

`source_pins` must include `extra_memory_sha256` and `replay_sha256` (exact
old file SHA256); additional runner-bound provenance may be preserved. Full
original/capture/collection verification remains the separate runner's job.
The trainer checks original parent tensor pin/full expected parent inventory.

Training re-encodes the saved raw spans with the supplied tokenizer and
frozen trainer, matching every saved input/label/EOS audit before fitting.
New explicit loop: memory forward and mean-token CE backward at every slot;
ADDITIVE performs one separately normalized observation forward/backward at
extra slots; one optimizer step after both gradients. No /2 or pooled-token
normalization. Original memory slots have no observation forward. Costs and
per-step component losses distinguish the additional computation.

Reuse pinned warm-parent/init/trainability/tensor/collate/LoRA-save APIs; do not
patch/rewrite old trainer globals. Fresh exclusive outputs, parent-before/after
inventories, failure receipt/no DONE on failure, no optimizer restore/save.

Pure stdlib tests run locally. Same test file exposes `--torch-cpu --out PATH`
for Main on node2 with `CUDA_VISIBLE_DEVICES=''`: tiny randomly initialized
Qwen2/PEFT objects from local configuration (no download), frozen-trainer
MEMORY_ONLY parity, gradient sum-vs-mean with unequal target lengths, fresh
optimizer/base-frozen/parent-immutable guards. CPU-fixture training is explicitly
separate from production source-pinned inputs; no production claim from toys.
Torch/PEFT execution will remain PENDING until Main supplies its receipt.

## Locked paired object / check_fit seam

Parfit's acceptance of the original API is confirmed; no signature change.
`prepare_pair` returns an arm-neutral JSON object with:
- `schema="astra_additive_replay_pair_20260913_v1"`, `seed`, `fit_seed`,
  `protocol_sha256`, `source_pins`, `paired_sha256` (canonical hash excluding itself).
- `primary`: exact deep copy of old EXTRA_MEMORY flat encoding; `replay`:
  exact deep copy of old REPLAY flat encoding (including its original memory
  prefix, which is validated but NOT executed as replay).
- `pairs`:24 `{memory_row_id,replay_row_id}` in construction order, unchanged IDs.
- `costs`: keys MEMORY_ONLY/ADDITIVE; each contains `updates`,
  `memory_forwards`, `replay_forwards`, `memory_total_tokens`,
  `memory_supervised_tokens`, `memory_context_tokens`, `replay_total_tokens`,
  `replay_supervised_tokens`, `replay_context_tokens`, `total_forwards`,
  `total_tokens`, `supervised_tokens`, `context_tokens`, `per_kind`.

`source_pins.extra_memory_sha256`/`replay_sha256` mean actual original file
byte hashes, not a claim that arbitrary JSON serialization preserves bytes.
Runner verifies files against these pins. Trainer checks these against the six
frozen original file pins and checks semantic canonical object hashes separately
against digests independently computed from those original archived objects.
No filesystem path is required in source_pins. Additional provenance preserved.

Manifest additions for new check_fit:
- `schema="astra_additive_replay_train_20260913_v1"`, `arm`, `objective`,
  `trainer_sha256` (NEW trainer), `frozen_trainer_sha256`, `protocol_sha256`,
  `paired_sha256`, `source_pins`, `primary_encoding_sha256`,
  `primary_training_items_sha256`, `primary_epoch_order_sha256`, `pairs_sha256`.
- `costs` equals paired.costs[arm]; `component_losses`: per-step objects
  `{epoch,position,memory_row_id,replay_row_id,memory,replay,total}` (replay
  fields null for unexecuted replay). `executed_order` repeats these ID fields.
- Standard `steps`, `micro_batches` (optimizer batches, not constituent
  forwards), `nonfinite_batches=0`, `epochs_run`, `mean_loss_per_epoch`,
  `final_loss`, `train_tokens_seen` (COMBINED actual forward tokens),
  `tokens` (primary one-epoch legacy schema), `truncation`, `packing`,
  `config`, `base_model`, `corpus`, `versions`, `lora`, `empty=False`.
- `warm_start` preserves frozen helper receipt: its `trainer_sha256` remains
  the OLD helper hash, initial/source/final tensor inventories, original parent
  before/after inventory, optimizer class/defaults/initial-empty, parent
  unchanged, phase_steps/cumulative_steps. Top-level hash identifies new loop.
- Component forward/time counts report differing computation; no assertion of
  equal random draws, gradients, FLOPs or scientific acceptance.

Fresh `--torch-cpu --out PATH` retains receipt.json plus parent/legacy/baseline/
additive fixture outputs and gradient evidence; no temporary-directory cleanup.
No fixture relaxation in production `prepare_pair` or `run_training`.

## Final candidate pins and validation

EDITSTOP on the owned trainer and tests, September 13, 2026. No native work,
model/library downloads, Git actions, repo edits, old-helper edits or other
workers' edits. This candidate is not an execution authorization or promotion.

- `/tmp/astra_additive_replay_train_20260913.py` SHA256
  `3f2e73ef69b12c8db211e1d3043e4559713e036ffe09571ab8bc4c5199a426a0`
- `/tmp/test_astra_additive_replay_train_20260913.py` SHA256
  `49e1fc9d266f89dfc69c1ea1c0112ed61e035190fd1ad2abfb8d7867828fdce1`
- Authoritative protocol SHA256
  `724d5a6e1aea7dca4b0ae42aec6e2fd0252b98646f7c903432927263f2c391e9`
- Unchanged frozen trainer SHA256
  `7bbf165fcb4b8ae3a1180328bcd19f57382c30516daddc95fd61e8a2c749fad7`
- Unchanged old repair encoder SHA256
  `9d8777ea3bfdcf92bace3b1a459644b9249dae108db9d5d6a3e35433e0bcff93`

Final local command:

```sh
python3 -B /tmp/test_astra_additive_replay_train_20260913.py
```

19/19 stdlib tests PASS, 0.698 seconds. No Torch/PEFT/Transformers imports in
this mode (asserted). Tests read ONLY the six old training JSON members from
`gpu_artifacts_local/own_replay_repair_20260913_attempt1/evidence.tar`, without
extraction; synthetic encoding tests use the test's reversible character codec.
The initial local suite exposed a malformed-input error-type mismatch, repaired
with explicit paired-object shape validation before the final pass. Inspection
also caught the frozen helper's lexicographic nonpacked sorting; both production
validation and tiny fixture now explicitly call that exact `pack_by_group`
before `epoch_order`. Regression test19 independently matches all24 old epochs.

Coverage: all original file/object pins; raw source/target/context mutation and
repinning rejection; exact items/orders/unchanged unequal seed0 cycling; fixed
bijective replay pairing and costs; raw target roundtrip; EOS/context/tail masks;
truncation/splitting/missing audits/tokenizer drift rejection; toy-recipe rejection
at the production entry; owned versus foreign output failure/write-once behavior.

## Main-only tiny Torch/PEFT CPU command

Copy the two candidate files with their basenames unchanged to the same native
directory. Use this command with a FRESH caller-selected output path; this worker
has NOT executed it. `--frozen-trainer` may point to an exact-byte native copy.

```sh
CUDA_VISIBLE_DEVICES='' python3 -B /tmp/test_astra_additive_replay_train_20260913.py \
  --torch-cpu --out /tmp/astra_additive_replay_tiny_cpu_20260913_attempt1 \
  --frozen-trainer /tmp/astra_level1_real_record_source_20260913_attempt1/organism_v6/train_adapter_v3.py
```

The fixture forces CPU/fp32, one thread, deterministic algorithms and offline
HF/Transformers mode before importing those libraries. It constructs a random
2-layer width32 Qwen2 model with vocabulary256, writes its local configuration,
and uses rank2 LoRA/dropout0.05; no pretrained model/tokenizer download or 7B
load. Its reduced recipe invokes the same private encoded loop, NOT a production
CLI flag or a relaxation of the public source-pinned training entry.

Retained artifacts: `fixture.json`, `tiny-base-config/`, `parent_inventory.json`,
`parent/`, `legacy/`, `baseline/`, `additive/`, `baseline_parity.json`,
`gradient_algebra.json`, `gradient_vectors.pt`, `failure-loss/`,
`failure-gradient/`, and `receipt.json`. No deletion on exit. `receipt.json`
contains candidate/test/helper/protocol pins, versions, checks, elapsed time,
status/error/traceback and exact hashes of all retained prior files. On failure
it still retains the receipt and whatever artifacts were produced. Rerunning
against an existing out directory is rejected; choose a new attempt directory.

Tiny requirements encoded, NOT yet reported PASS:
1. MEMORY_ONLY final LoRA tensors and final/epoch losses exactly equal the old
   trainer, from the same tiny parent/base/recipe/legacy schedule.
2. Frozen model `.loss` equals explicit shifted masked mean CE. Unequal labels
   (3 memory versus20 replay, EOS included) produce paired gradients equal to
   the SUM of independent means, distinct from both half-sum and pooled-token
   mean. Gradient vectors and errors retained. Algebra runs in eval mode for
   an identical function; actual baseline parity uses training dropout0.05.
3. Original parent/source/initial tensors equal across arms; one LoRA, fresh
   optimizer/defaults/no restored state; base parameters remain frozen and
   bitwise unchanged; same primary schedule, four optimizer steps per toy arm,
   zero versus two replay forwards.
4. Nonfinite loss and finite-loss/nonfinite-gradient fixtures fail without DONE;
   failure receipts retain parent inventory evidence. Existing output and parent
   inventories remain unchanged after rejection.

## Actual fixed training-artifact accounting

| Seed | Updates/arm | Memory forward tokens | Memory supervised tokens | ADDITIVE extra replay tokens | ADDITIVE total tokens |
|---|---:|---:|---:|---:|---:|
| 0 | 304 | 52888 | 8776 | 66184 | 119072 |
| 1 | 256 | 43552 | 6368 | 66184 | 109736 |
| 2 | 256 | 44928 | 7744 | 66184 | 111112 |

Replay has5688 supervised and60496 context tokens per ADDITIVE arm,192extra
forwards each. MEMORY_ONLY has zero executed replay. Both retain eight memory
presentations per occurrence; seed0's original source records appear3times per
epoch for10sources and2times for4sources. No balancing or rotation introduced.
The primary legacy token fields in `paired.primary` remain unchanged.

All six original member-byte hashes were directly checked; independently
canonicalizing their parsed objects happened to yield the SAME hashes because
these particular originals already use sorted compact JSON plus a newline:

| Seed | EXTRA_MEMORY original file SHA256 | REPLAY original file SHA256 |
|---|---|---|
| 0 | 7c0c9c7fd452e5e311c63143944b8d8d6a60508fd109c8623f45babec9f2735a | 8441052b34d6cb358d38c1933a6e4ddf3e6fedae760bb32fe830e99105727fb5 |
| 1 | b0cd8384f6dd39a64782b1336a20a50a4f0ada3f40584a2b985546449bf2aab5 | 15f137d918402009b1298713253b9cee95fd17714dcf980c76e0d36c5af2f66d |
| 2 | fed12bf11cdd50dcaebb9974cbb63117eac736fd7855c876435e7c97b1625e93 | 83e8c224d3b90183bea1729b54498f1f0defeedd16b5cf53772c433603afc5c9 |

With source_pins containing ONLY the two byte hashes above, paired object hashes:
- seed0 `26e8b4d5ccf6a55ef71780e4664f9e27a7ede1f7e1fc4222fb5d9684b3a8e291`
- seed1 `b989c9955b934065f9fb75ed8b57c0a8b7998f6ea9a4a40df985281eec379e9a`
- seed2 `e6646114f205b30516993cee0844c142db69254054b5ebb3d770c3b585871384`

These object pins are not file-format generalizations. Runner checks actual
byte hashes, full immutable original/capture/history/parent provenance and
native preparation; trainer checks its exact frozen data/object seam, original
expected parent inventory, native re-encoding and frozen warm/config APIs.
No repeated source/custody audit or scientific-score reduction was performed.

## Implementation / limits / Parfit agreement

The explicit new loop uses the same model(labels=...).loss interface as the old
trainer (whose masked-mean semantics are tested against explicit CE in the tiny
suite). Each component calls backward once; memory backward then replay backward
when applicable, one AdamW step and zero_grad after BOTH. No loss division,
concatenation, global mutation, AST rewrite or old-trainer monkeypatch. Grads,
losses and updated adapter parameters must be finite; DONE is written last.
`steps.jsonl` preserves completed update identities/losses even on later failure.
Warm receipt retains the OLD trainer hash; top-level trainer hash names this loop.

Additional manifest fields: `adapter_update_l2`, `optimizer_steps`,
`memory_forwards`, `replay_forwards`, `component_seconds`, `executed_order_sha256`,
`peak_cuda_memory_allocated_bytes`, and timing/memory scope strings. CUDA host
intervals are not synchronized kernel profiling; allocator peak is a process
high-water mark, not an isolated phase delta. More RNG draws are expected but
not counted; no matched-RNG/compute/gradient-trajectory claim.

Read Parfit's in-progress runner's `paired`/`expected_costs`/`check_fit`/`fit_arm`
and core prepared seam after publication: signatures and consumed fields agree
with this implementation. Did not edit or execute those modules; their final
pins and integration tests belong to Parfit/Main. No blocked API contract found.

PENDING Main receipt: all Torch/PEFT execution, native tokenizer/source checks
and any actual fit/readout. Pure tests do not establish numerical parity or
GPU feasibility. Candidate flags are descriptive only, not launch/adoption
triggers. No outcome, retention, memory-floor or H1/H2 claim is made.
