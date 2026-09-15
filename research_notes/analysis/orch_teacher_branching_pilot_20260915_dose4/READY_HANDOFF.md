# Teacher dose4: CPU ready, no GPU allocation or launch

Prepared 2026-09-15 06:34 UTC. Separate `TEACHER_DISTILLATION` experiment;
not own-generated replay, ongoing L1 input, or own-trajectory success.
Read `R106_RUBRIC_ADDENDUM.md` for the current prospective branching definition.

## Verified preparation

- Existing fixed16 TRAIN exemplars:8 math/8 route, all author-supported for
  arithmetic and grounding. Published main6 and remaining10 audit bytes pinned;
  no independent certification. Four math rearrangements remain explicitly weak
  method diversity; this is not a branch-eligibility failure.
- Native inventory156 files verified. Original TRAIN roster/gold reconstructed;
  exclusion checks cover32 held math IDs/32 question hashes and204 route IDs.
  Teacher steering excluded from neutral student prompts and label text.
  Target field spans bind unchanged source text; original limitations retained
  as provenance, not label text. No raw teacher files pulled to this VM.
- Local16 tests PASS (11 new pilot/interface +5 existing teacher tests).
  Native14 tests PASS before the two additional interface tests;
  actual native tokenizer and paired-batch rehearsal then PASS.
- Original37ec adapter/base/tokenizer verified; all16 targets encode without
  cropping. Supervised target+EOS lengths323–810; total sequences378–1116.
- Exact old222 encodings preserved. Each arm:56 batch4 updates;56 old-memory,
  56 old-behavior,48 old-trajectory and64 teacher-row presentations.
  Old memory/behavior visitation is the first56 of128/82 respectively, not
  uniform coverage of all legacy rows.
- Proven `orch_guided_native.training_batch` checks: FULL42207 active/reference
  labels; masked3839 active/42207 reference. Only new-row labels222–237,
  including target EOS, differ. Inputs, padding, schedule and denominator match.

## Proposed two-slot allocation — NOT granted

Candidate node1 physical4/5 only. No holds or handoff requests; preserve0/1 and3.
Main must post actual readiness, exact GPU UUIDs, ownership and lease deadline.
Both arms freshly load original37ec, never current continual adapters. One fit
per arm, LoRA only, fresh AdamW, seed8203, lr3e-5, betas(.9,.999), eps1e-8,
weight_decay.01, no gradient clipping; identical reference-normalized loss.

One shared future start, hard ceiling7200 seconds/4 GPU-hours, shortened by
lease-end minus6h; no restarts reset time/call counts. No provider/parent/source
generation calls. Held readout per arm:16 math calls +at most48 route calls
(2 worlds ×4 goals ×6 turns) +48 legacy calls =112; pair ceiling224.
Math/route max output4096, legacy160, context16384, single attempts, no forced
minimum/padding/cropping; retain truncated outputs and failures. Aggregate
output-token ceiling539648, not an expected usage estimate.

Readout cohorts are already selected by fixed order and hash-bound in native
`READOUT_COHORT.json` and `SEALED_READOUT_INPUTS.json`; held outputs never train.
The route evaluator reuses original observed source events identically for
both arms, not fabricated events or new-child autobiographical observations.
The strict route action protocol measures routing transfer, not free-form
branch richness. Math full outputs are the primary richness comparison.
Source observations are preexisting; no additional collection calls needed.
Parents and teacher never receive readout packets/results.

Planning ETA from a **future verified allocation**:5–10min load/fit;35–90min
readout, about40–100min overall with120min hard stop. This is an unmeasured
estimate, not a launch promise or an observed throughput. No fit runner has
been launched or GPU-validated. Laplace should reuse proven load/training/mask
and readout primitives with this CPU interface; final GPU wrapper/allocation
checks remain before launch. Dose16 requires separate prospective allocation.

## Native evidence

Compiler manifest:
`/localhome/local-rohing/orch_teacher_branching_pilot_20260915_dose4_compile_0630/MANIFEST.json`

SHA256 `976a0258d053f783c1cc3b5383614c7502e56d43d7e830c9782aaf9bba1fe527`.
Immutable native source tree digest:
`ac1508f9e9be6fb70adc0a96d74432fd415be8ae4596e8458dfed77aabadc8de`.

Interface receipt:
`/localhome/local-rohing/orch_teacher_branching_pilot_20260915_dose4_interface_0634/READY.json`.
Native-only readout file SHA256
`194176b99a09ad1e9bac02728332059aee666cabf8c444a1f7bc769493013062`.
Compact local reductions are `NATIVE_CPU_REDUCTION.json` and
`NATIVE_INTERFACE_REDUCTION.json`. Runtime/raw/encoded rows remain on node3.
No GPU model was loaded; the16 mock route actions were CPU fixtures, not
native model calls or learner outcomes.

## Publisher unchanged

PID3797981 observed live06:34 UTC. Published reservation snapshot4/128,
old96 unchanged; aggregate allocations<=256, deadline08:00/cutoff07:49 intact.
Latest completed accepted count remains0. LIVE_STATUS is stale after the
failed batch; do not interpret its clock as a fresh progress receipt.
Batch001 stays failed: group1 ordinal0 prefix-hash mismatch, not HTTP failure.
No failed review is retried, relabeled, or used as training material.
