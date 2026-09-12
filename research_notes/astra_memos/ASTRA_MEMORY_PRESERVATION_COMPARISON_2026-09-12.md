# Whole-text acquisition with frozen-OFF preservation — prospective diagnostic

September12,2026,11:41UTC. After SEQ-074, retain original whole-text memory
supervision rather than another mask/LR sweep. This is a separate synthetic
oracle-material locality diagnostic, not clean ancestry, parenting, G3,
mechanism freeze or SDFT/OEL reproduction. Formal C11 custody remains deferred.

## Fixed comparison and interpretation

Two fresh base-derived LoRA fits on node3: coefficient0 onGPU0, coefficient0.1
onGPU2. Both use original source bank0/optimizer seed2, rank8/alpha16/dropout.05,
all seven native projections, AdamW1e-4, batch4, chronological three epochs,
maxlen512, no gradient checkpointing, no clipping/scheduler. Each has12,924
items,9,693steps,749,985input and711,213shifted supervised-token passes.
No coefficient1 or additional seeds are selected. Reused original A1seed2
remains an external bridge check, not a silently substituted current control.

Coefficient0 skips cache/KL entirely. It must reproduce the native CPU
loss/gradient/update ordering and is a fresh full-run bridge control. Compare
its complete1,313cue OFF/ON scores to the original; if ON differs, report that
drift and use the contemporaneous coefficient0 comparison, not a historical
control assumption. OFF/model/input drift requires diagnosis.

Coefficient0.1 adds `0.1 * KL(p_OFF || p_current)` over the full vocabulary
at the final input token of one fixed prefix per optimizer step, temperature1.
Whole-text CE coefficient remains1. Cache48detached frozen-base OFF distributions
before fitting; no teacher generation or target answers. Student preservation
forward is eval-mode with gradients and restored dropout RNG/module modes.
Accumulate CE and KL gradients, then one optimizer step. This adds measured
compute, not a compute-matched control. No stronger claim from that difference.

## Anchors and separation

48deterministic, training-only prefixes:16near-car,16far-car,16far-bicycle,
interleaved round-robin. Each family receives3,231preservation positions.
Fresh owner IDs are disjoint from the complete source and all three banks'
native evaluation owner references; no evaluation score file is read.
Near IDs derive only from exposed training owner IDs; far IDs are at least
two substitutions away from reserved IDs. Prefix construction uses existing
native templates with no color answer. Anchors are not evaluation queries.
Record exact anchor rows/hashes and actual tokenizer input IDs before use.

## Outcomes and stopping

Unchanged native1,313cue OFF/ON report, owner-bootstrap interval for I_d_frame,
correct conditional probabilities, candidate mass, dose curve and spill;
unchanged G9 and G11. Lower spill with lost acquisition remains a failure.
Native G9 requires positive interval lower bound and spill<=.03. Low training
anchor KL is not held-out locality. Full-vocabulary preservation may leave
conditional color bias unresolved. Frozen OFF already has low abstention;
this objective does not teach the unchanged G11>=.5abstention requirement.

One bank/seed is exploratory; no numeric generality claim or mechanism freeze.
If acquisition/locality both improve, decide the smallest disjoint confirmation
or semantic-binding check. If acquisition fails or spill remains broad, do not
launch more coefficients automatically; inspect whether preservation actually
held and choose a different representation/interface test. No outcome-based
anchor selection, evaluation retuning or threshold changes.

Each controller keeps its GPU through cache/fit/fresh evaluation reload gaps.
Fresh GPU process table, own CUDA reservations and queue checks before launch.
Only owned worker groups cleaned by the existing supervisor.3600seconds hard
worker cap; forecast25–40A40minutes per arm, two-GPU total<=2hours capped.
First100steps provide a timing estimate, not a learning endpoint. Abort on
nonfinite loss, incomplete dose, changed input/model bytes, or timeout; preserve
failure root and log any intervention. Both arms fit well before node3 expiry.

## Implementation and reproducibility

`organism_v6/memory_preservation.py` reuses native encoding/constants and
weighted CE; native `memory_dose.py` is unchanged at
`ab98329c433cb085cd53e1c766db350f1bb0fe2efb9181e24a3678c0d31a76e3`.
`gpu/astra_memory_preservation_diagnostic.py` prepares immutable input copies,
runs bounded stages and validates the native report. Exact committed source,
plans, launch receipts and source/model hashes accompany actual execution.

CPU19module fixtures (including full-loop order and zero-coefficient numerical
equivalence) and8launcher fixtures pass on Main's CPU environment. System
Python lacks pytest/PyTorch; unittest in the dedicated CPU-PyTorch environment
runs the gradient checks, not skipped tests. Actual node tokenizer preparation
and CPU fixtures are still required before launch. Local cache hashes are
recorded; official origin remains `UNRESOLVED_LOCAL_HASHES_ONLY`.

Preparation: `python -B -m gpu.astra_memory_preservation_diagnostic --prepare
--root NEW_RUN --original ORIGINAL_INPUT_ROOT --model LOCAL_QWEN_SNAPSHOT
--coefficient 0` (or0.1). Execution after preparation: same module with
`--root NEW_RUN --device 0 --execute` (orGPU2). Native reports live under each
root's `report/`; exact action commands are in the launch receipt. Nothing in
this prospective note itself claims a launched or completed run.
